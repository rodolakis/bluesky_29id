









#--------------------------------------------------------
# support functions for units conversion

def convert(value, egu, to_egu):
    return pint.Quantity(value, egu).to(to_egu).magnitude

def eV2keV(value):
    return convert(value, "eV", "keV")

def keV2eV(value):
    return convert(value, "keV", "eV")

#--------------------------------------------------------
# define the structures to be used

class UndulatorEnergy(PVPositioner):  # in keV
    setpoint = Component(EpicsSignal, "EnergyScanSet")
    readback = Component(EpicsSignalRO, "Energy")
    done = Component(Signal,kind='omitted',value = True)
    done_value = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent.feedback.subscribe(self.done_callback)
        self.parent.busy_record.subscribe(self.done_callback)
        
    def done_callback(self,*args,**kwargs):
        self.done.put(self.parent.ready)
    
#     def cb_put(self, *args, **kwargs):
#         # TODO: confirm this works as expected
#         # TODO: consider the calibration dictionary for commanded vs actual energy



class MyUndulator(Device):   # in keV
    """29ID has a special undulator, not APS Undulator A."""
    energy = Component(UndulatorEnergy, "")
    actual_mode = Component(EpicsSignal, "ActualMode", write_pv='DesiredMode', string=True, kind='config') 
    quasi_ratio_raw = Component(EpicsSignal, "QuasiRatio.RVAL", write_pv='QuasiRatioIn.C', kind='config')
    main_on_off = Component(EpicsSignal, 'Main_on_off', string=True, kind='config')
    feedback = Component(EpicsSignalRO, 'feedback', string=True, kind='omitted')
    busy_record = Component(EpicsSignalRO, 'BusyRecord', string=True, kind='omitted')

    
    @property
    def ready(self):
        status=(self.feedback.get() == "Ready") and (self.busy_record.get() != 1)
        #print(f"ready? {status = },  {self.feedback.get() = },  {self.busy_record.get() = }")
        return status

    
    def wait_until_ready(self):
        while not self.ready:
            yield from bps.sleep(0.1)   # bps = bluesky plan stub

        self.readback.name = self.name

class MonoEnergy(PVPositioner):  # in keV
    setpoint = Component(EpicsSignal, "ENERGY_SP")
    readback = Component(EpicsSignalRO, "ENERGY_MON")
    done = Component(EpicsSignalRO,'ERDY_STS',kind='omitted',string=True)
    done_value = 'Ready'      
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readback.name = self.name


class Monochromator(Device):
    energy = Component(MonoEnergy, "29idmono:")
    mirror_pitch = Component(EpicsMotor, "29idmonoMIR:P")
    grating_pitch = Component(EpicsMotor, "29idmonoGRT:P")
    grating_density = Component(EpicsSignal, "29idmono:GRT_DENSITY")
    mirror_status = Component(EpicsSignalRO, "29idmonoMIR:P_AXIS_STS")
    grating_status = Component(EpicsSignalRO, "29idmonoGRT:P_AXIS_STS")
    
    @property
    def status(self): #test.get(as_string=True) in ("Moving", "Positioned")
        return self.mirror_status.get(as_string=True) in  ("Moving", "Positioned") and self.grating_status.get(as_string=True) in  ("Moving", "Positioned")
        

aps = apstools.devices.ApsMachineParametersDevice(name="aps")
undulator = MyUndulator("ID29:", name="undulator") #, egu="keV"?


mono = Monochromator("", name="mono")




if mono.grating_density.get() == 1200:
    GRT="MEG"
elif mono.grating_density.get() == 2400:
    GRT="HEG"
branch = EpicsSignal("29id:CurrentBranch", name="branch")











############################################################################################################

from time import sleep
from epics import caget, caput
from IEX_29id.utils.exp import CheckBranch
from IEX_29id.devices.undulator import ID_Range, SetID
from IEX_29id.devices.slits import SetSlit_BL
from IEX_29id.devices.mirror import align_m3r
from IEX_29id.devices.mono import Check_Grating


def SetRange(hv):
    Mode=caget("ID29:ActualMode")
    hv_min=ID_Range()[1]
    hv_max=ID_Range()[2]
    sleep(0.1)
    hv_SP=min(round(max(hv,hv_min)*1.0,3),hv_max)*1.0
    sleep(0.1)
#    if round(hv,1) != hv_SP:
    if hv < hv_min or hv > hv_max:
        print("\nWARNING: Set point out of BL energy range:")
    return hv_SP

def SetMono(eV):
    GRT=Check_Grating()
    if GRT == "HEG":
        min_limit=120
        max_limit=2200
    elif GRT == "MEG":
        min_limit=120
        max_limit=3000
    eV = max(min_limit,eV)
    eV = min(max_limit,eV)
    caput("29idmono:ENERGY_SP",eV,wait=True,timeout=60)
    sleep(2.5)
    STS=Mono_Status()
    if STS >1:
            print("Mono error - resetting motor")
            caput("29idmonoMIR:P.STOP",1)
            caput("29idmonoGRT:P.STOP",1)
            sleep(1)
            caput("29idmono:ENERGY_SP",eV,wait=True,timeout=18000)
            sleep(2.5)
            caput("29idmono:ENERGY_SP",eV,wait=True,timeout=18000)
    print("Mono set to",str(eV),"eV")

def Mono_Status():
    MIR_Status=caget("29idmonoMIR:P_AXIS_STS")
    GRT_Status=caget("29idmonoGRT:P_AXIS_STS")
    Status=MIR_Status*GRT_Status
    return Status


def SetBL(hv,c=1):
    caput("29id:BeamlineEnergyAllow",'Disable',wait=True,timeout=18000)
    caput("29id:BeamlineEnergySet",hv,wait=True,timeout=18000)
    hv_SP=round(SetRange(hv),3)
    if hv_SP == round(hv,3):
        #if (hv>2250):
            #ActualMode=caget("ID29:ActualMode")
            #if(ActualMode<2):         #circular
                #print("Setting ID to second harmonic.")
        SetID(hv)
        SetMono(hv)
        SetSlit_BL(c2B=c,q='q')
        print("\n")
#        caput("29id:BeamlineEnergyAllow",'Enable',wait=True,timeout=18000)
    else:
        print("Please select a different energy.")






def energy(val,c=1,m3r=True):
    """
    Sets the beamline energy: insertion device + mono + apertures.
    Use c < 1 to kill flux density.
    """
    SetBL(val,c)
    SetMono(val)
    if m3r == True:
        if CheckBranch() == 'd':
            print('\nalign_m3r()')
            try:
                align_m3r()
                sleep(1)
                if caget('29id_m3r:RY_POS_SP') == -16.52:
                    align_m3r(debug=True)
            except:
                print('Unable to align; check camera settings.')



def Energy_Range(grating,IDmode):
    BL_range={}    #   Slit:PE
    BL_range["HEG"]  = { "H":(250,2000), "V":(440,2000), "RCP":(400,2000), "LCP":(400,2000)  }
    BL_range["MEG"]  = { "H":(250,2500), "V":(440,2500), "RCP":(400,2500), "LCP":(400,2500) }
    energy_min, energy_max = BL_range[grating][IDmode]
    return energy_min, energy_max

