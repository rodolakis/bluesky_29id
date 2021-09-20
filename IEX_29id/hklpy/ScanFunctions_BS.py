
"""
29id_example.py: setup for scan h k l with bluesky
"""

__all__ = """
    aps
    bec
    bp
    bps
    cat
    kappa
    logger
    mono
    peaks
    RE
    sd
    undulator
    scaler1
    timebase
    TEY
    D3
    D4
    MCP
    meshD
""".split()

# required steps, before first import from hkl package
import gi
gi.require_version('Hkl', '5.0')

import apstools.devices
from bluesky import plan_stubs as bps  # steps for use inside a plan
from bluesky import plans as bp  # standard scan plans
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.magics import BlueskyMagics
from bluesky.utils import PersistentDict
from bluesky.utils import ProgressBarManager
from hkl.geometries import E4CV
from IPython import get_ipython
from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import PseudoSingle
from ophyd import PVPositioner
from ophyd import PVPositionerPC
from ophyd import Signal
from ophyd.signal import AttributeSignal
from ophyd.signal import EpicsSignalBase
import bluesky
import databroker
import hkl.user
import logging
import os
import pint
import stdlogpj
from ophyd.scaler import ScalerCH

BLUESKY_MONGO_CATALOG_NAME = "29idd" 

# I prefer logging to printing
BYTE = 1
kB = 1024 * BYTE
MB = 1024 * kB
# logger = stdlogpj.standard_logging_setup(
#     "bluesky-session", "ipython_logger", maxBytes=1 * MB, backupCount=9
# )
# logger.setLevel(logging.DEBUG)
# logger.info("#" * 60 + " startup")
# logger.info("logging started")
# logger.info(f"logging level = {logger.level}")

#--------------------------------------------------------
# setup the Bluesky framework first

# connect with the data
cat = databroker.catalog[BLUESKY_MONGO_CATALOG_NAME]

# prepare the RunEngine
RE = bluesky.RunEngine({})
RE.subscribe(cat.v1.insert)  # send run data to databroker

# To remember "scan_id" and other such metadata (md), need
# to save config to disk.  That's the role of PersistentDict.
# Here, we define a directory to be used.  And create it if
# it does not exist already.
home_dir = os.environ["HOME"]
md_dir_name = "Bluesky_RunEngine_md"
persistent_md_dir = os.path.join(home_dir, ".config", md_dir_name)
if not os.path.exists(persistent_md_dir):
    logger.info(
        "New directory to store RE.md between sessions: %s",
        persistent_md_dir
    )
    os.makedirs(persistent_md_dir)
RE.md = PersistentDict(persistent_md_dir)  # synchronizes RE.md with persistent_md_dir

# supplemental data: baselines, monitors
sd = bluesky.SupplementalData()
RE.preprocessors.append(sd)

# LiveTable and LivePlot during scan
bec = BestEffortCallback()
RE.subscribe(bec)
peaks = bec.peaks  # just as alias for less typing

# Register bluesky IPython magics.
get_ipython().register_magics(BlueskyMagics)

# Add a progress bar.
# RE.waiting_hook = ProgressBarManager()

# MUST be called BEFORE any EpicsSignal objects are created.
# Set default timeout for all EpicsSignal connections & communications.
try:
    EpicsSignalBase.set_defaults(
        auto_monitor=True, timeout=60, write_timeout=60, connection_timeout=60,
    )
except RuntimeError:
    pass

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
    
#     @property
#     def ready(self):
#         print('ready?')
#         status=(self.feedback.get() == "Ready") and (self.busy_record.get() != 1)
#         print(f"{status = }")
#         return status
    
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
        

class SoftRealMotor(PVPositionerPC):
    setpoint = Component(EpicsSignal, "")
    readback = Component(EpicsSignalRO, "RBV")

class My4Circle(E4CV):
    h = Component(PseudoSingle, "")
    k = Component(PseudoSingle, "")
    l = Component(PseudoSingle, "")

    omega = Component(SoftRealMotor, "29idKappa:Euler_Theta")
    chi = Component(SoftRealMotor, "29idKappa:Euler_Chi")
    phi = Component(SoftRealMotor, "29idKappa:Euler_Phi")
    tth = Component(EpicsMotor, "29idKappa:m9")
    _real = ["omega", "chi", "phi", "tth"]
    # now, the extra motors
    kth = Component(EpicsMotor, "29idKappa:m8")
    kap = Component(EpicsMotor, "29idKappa:m7")
    kphi = Component(EpicsMotor, "29idKappa:m1")

#--------------------------------------------------------
# define (and configure) the ophyd objects

aps = apstools.devices.ApsMachineParametersDevice(name="aps")
undulator = MyUndulator("ID29:", name="undulator") #, egu="keV"?
# TODO: shutters?
# TODO: slits?
# TODO: mirrors?
# TODO: baseline stream (extra PVs)
# TODO: Futur plans => secondary stream
# TODO: scan mono+ID
# TODO: calibration ID


mono = Monochromator("", name="mono")

scaler1 = ScalerCH("29idMZ0:scaler1", name="scaler1", labels=["scalers", "detectors"])
scaler1.stage_sigs['preset_time']=1
scaler1.wait_for_connection()
scaler1.select_channels()  # choose just the channels with EPICS names
# make shortcuts to specific channels assigned in EPICS
timebase = scaler1.channels.chan01.s
TEY = scaler1.channels.chan02.s
D3 = scaler1.channels.chan03.s
D4 = scaler1.channels.chan04.s
MCP = scaler1.channels.chan05.s
meshD = scaler1.channels.chan14.s
TEYcalc = EpicsSignalRO('29idMZ0:scaler1_calc1.B',name='TEYcalc')
D3calc = EpicsSignalRO('29idMZ0:scaler1_calc1.C',name='D3calc')
D4calc = EpicsSignalRO('29idMZ0:scaler1_calc1.D',name='D4calc')
MCPcalc = EpicsSignalRO('29idMZ0:scaler1_calc1.E',name='MCPcalc')

kappa = My4Circle("", name="kappa")
hkl.user.select_diffractometer(kappa)


# choose WHICH detector based on the PV (sets tth 0 position)
det_selected = EpicsSignal("29idKappa:userStringSeq6.STR1", name="det_selected", string=True)
HV = EpicsSignal("29idKappa:userCalcOut10.OVAL", name="HV")
centroidM3R = EpicsSignal("29id_ps6:Stats1:CentroidX_RBV", name="centroidM3R")

if mono.grating_density.get() == 1200:
    GRT="MEG"
elif mono.grating_density.get() == 2400:
    GRT="HEG"
branch = EpicsSignal("29id:CurrentBranch", name="branch")



#--------------------------------------------------------
# Future plans  (yield from something)
#
# TODO:
#
# def change_energy_BL(): 
#    """ID + mono + apertures 1A & 2B"""
#
# def set_ID():
#   """ Make sure RBV is within 5% of SP; restart ID if not"""
#
#



#--------------------------------------------------------
# TODO:

# the first block was what I use to create my logging csv file that takes a screenshot of the beamline at the end of each scan (equivalent/redundant with the extra PVs from the scan records). the second (longer) block is the detectors I record at each scan

    # if branch == "d":
    #     x   = caget("29idKappa:m2.VAL")
    #     y   = caget("29idKappa:m3.VAL")
    #     z   = caget("29idKappa:m4.VAL")
    #     tth  = caget("29idKappa:m9.VAL")
    #     kth = caget("29idKappa:m8.RBV")
    #     kap  = caget("29idKappa:m7.VAL")
    #     kphi = caget("29idKappa:m1.RBV")
    #     slit=caget("29idb:Slit4Vt2.C")
    #     TA   = caget("29idd:LS331:TC1:Control")
    #     TB   = caget("29idd:LS331:TC1:SampleB")

    # detector channels of the sscan record, to save at every point of a scan
    # If they update at their own rate, they can be recorded as "monitors"
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D19PV","29idd:ca2:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D20PV","29idd:ca3:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D21PV","29idd:ca4:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D22PV","29idd:ca5:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D23PV","29idd:LS331:TC1:SampleA")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D24PV","29idd:LS331:TC1:SampleB")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D25PV","29id_ps6:Stats1:CentroidX_RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D26PV","29id_ps6:Stats1:SigmaX_RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D27PV","29id_ps6:Stats1:CentroidTotal_RBV")
    #         # D28  free
    #         # D29  free
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D30PV","29iddMPA:det1:TotalRate_RBV") # MPA software count rate?
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D31PV","29idMZ0:scaler1.S14") #-mesh D
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D32PV","29idMZ0:scaler1.S2") # TEY
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D33PV","29idMZ0:scaler1.S3") # D3
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D34PV","29idMZ0:scaler1.S4") # D4
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D35PV","29idMZ0:scaler1.S5") # MCP
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D36PV","29idMZ0:scaler1_calc1.B") #TEY/mesh
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D37PV","29idMZ0:scaler1_calc1.C") #D3/mesh
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D38PV","29idMZ0:scaler1_calc1.D") #D4/mesh
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D39PV","29idMZ0:scaler1_calc1.E") #MCP/mesh
    #         # D40 free
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D41PV","29iddMPA:Stats1:Total_RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D42PV","29iddMPA:Stats2:Total_RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D43PV","29iddMPA:Stats3:Total_RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D44PV","29iddMPA:Stats4:Total_RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D45PV","29iddMPA:Stats5:Total_RBV")
    #         # D46  <H>
    #         # D47  <K>
    #         # D48  <L>
    #         # D49  free
    #         # D50  free
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D51PV","29idKappa:m8.RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D52PV","29idKappa:m7.RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D53PV","29idKappa:m1.RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D54PV","29idKappa:m9.RBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D55PV","29idKappa:Euler_ThetaRBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D56PV","29idKappa:Euler_ChiRBV")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D57PV","29idKappa:Euler_PhiRBV")

    #                 caput("29id"+scanIOC+":scan"+str(scanDIM)+".D01PV","S:SRcurrentAI.VAL")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D02PV","EPS:29:ID:SS1:POSITION")
    #         #Setting Detectors -- Beamline Energy
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D03PV","29idmono:ENERGY_MON")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D04PV","ID29:EnergySet.VAL")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D05PV","ID29:Energy.VAL")
    #         #Setting Detectors -- Keithleys
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D06PV","29idb:ca1:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D07PV","29idb:ca2:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D08PV","29idb:ca3:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D09PV","29idb:ca4:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D10PV","29idb:ca5:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D11PV","29idb:ca9:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D11PV","29idb:ca10:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D12PV","29idb:ca12:read")
    #         caput("29id"+scanIOC+":scan"+str(scanDIM)+".D13PV","29idb:ca13:read")


    # #Setting Detectors -- Slits & Apertures
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D58PV","29idb:Slit1Ht2.C")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D59PV","29idb:Slit1Ht2.D")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D60PV","29idb:Slit1Vt2.C")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D61PV","29idb:Slit1Vt2.D")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D62PV","29idb:Slit2Ht2.C")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D63PV","29idb:Slit2Ht2.D")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D64PV","29idb:Slit2Vt2.C")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D65PV","29idb:Slit2Vt2.D")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D66PV","29idb:Slit3CRBV")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D67PV","29idb:Slit4Vt2.C")
    # #Setting Detectors -- Mono details
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D68PV","29idmono:ENERGY_SP")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D69PV","29idmonoMIR:P.RBV")
    # caput("29id"+scanIOC+":scan"+str(scanDIM)+".D70PV","29idmonoGRT:P.RBV")
