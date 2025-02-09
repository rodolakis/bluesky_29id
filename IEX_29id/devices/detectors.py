__all__ = """
    set_detector_plan
    srs
    scaler
    TEY
    D3
    D4
    MCP
    meshD
    scaler
    timebase
    TEYcalc
    D3calc
    D4calc
    MCPcalc
    HV
    select_detector
    """.split()

from ophyd import EpicsSignal, EpicsSignalRO
from ophyd.scaler import ScalerCH
from ophyd import Component, Device
from apstools.devices import SRS570_PreAmplifier
from bluesky import plan_stubs as bps

class PreAmplifier(Device):
    A1 = Component(SRS570_PreAmplifier, "1")
    A2 = Component(SRS570_PreAmplifier, "2")
    A3 = Component(SRS570_PreAmplifier, "3")
    A4 = Component(SRS570_PreAmplifier, "4")

srs = PreAmplifier("29idd:A", name = "srs")


scaler = ScalerCH("29idMZ0:scaler1", name="scaler", labels=["scalers", "detectors"])
scaler.wait_for_connection()
scaler.select_channels() 

timebase = scaler.channels.chan01.s
TEY = scaler.channels.chan02.s
D3 = scaler.channels.chan03.s
D4 = scaler.channels.chan04.s
MCP = scaler.channels.chan05.s
meshD = scaler.channels.chan14.s
TEYcalc = EpicsSignalRO('29idMZ0:scaler1_calc1.B',name='TEYcalc')
D3calc = EpicsSignalRO('29idMZ0:scaler1_calc1.C',name='D3calc')
D4calc = EpicsSignalRO('29idMZ0:scaler1_calc1.D',name='D4calc')
MCPcalc = EpicsSignalRO('29idMZ0:scaler1_calc1.E',name='MCPcalc')


select_detector=EpicsSignal('29idKappa:det:set', name='select_detector', string=True)

def set_detector_plan(desired_detector):
    yield from bps.mv(select_detector,desired_detector)

HV = EpicsSignal("29idKappa:userCalcOut10.OVAL", name="HV")
#TODO: move HV


#TODO: to be tested - compare with script from run_20211205.ipbn 
def gain_set_plan(gain_value,gain_unit,n=4): 
    v={1:0,2:1,5:2,10:3,20:4,50:5,100:6,200:7,500:8}[gain_value] 
    u={'pA':0,'nA':1,'uA':2,'mA':4}[gain_unit] 
    srsN = getattr(globals, f"srs{n}")
    yield from bps.mv(
        srsN.sensitivity_unit, u,
        srsN.sensitivity_value, v,
    )
    yield from bps.sleep(1)
    u = srsN.sensitivity_unit.get()
    v = srsN.sensitivity_value.get()
    logger.info('SRS%s : %s %s', n, v, u)







# def set_detector(detector):   
#     """
#     detector = d3, d4, mcp, apd, yag
#     Reset tth for a given detector.
#     """
#     caput('29idKappa:det:set',detector)
#     return detector
    

# def setgain(det,gain,unit):
#     """
#     det  = 'SRS1', 'SRS2', 'SRS3', 'SRS4','mesh','tey','d3','d4'
#     gain = 1,2,5,10,20,50,100,200,500
#     unit = 'pA, 'nA', 'uA', 'mA'
#     """

# def cts(time):
#     """
#     Sets the integration time for the scalers
#     """
#     ScalerInt(time)

# def ScalerInt(time):
#     """
#     Sets the integration time for the scalers
#     """
#     pv="29idMZ0:scaler1.TP"
#     caput(pv,time)
# #     if time>=1:
# #         caput('29iddMPA:Proc1:NumFilter',floor(time))
# #     else:
# #         caput('29iddMPA:Proc1:NumFilter',1)
#     caput('29iddMPA:Proc1:NumFilter',floor(time))
#     print("Integration time set to:", str(time))


    
    









