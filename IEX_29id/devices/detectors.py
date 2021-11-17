__all__ = """
    set_detector_plan
    """.split()

from ophyd import EpicsSignal
from bluesky import plan_stubs as bps

new_detector=EpicsSignal('29idKappa:det:set', name='new_detector', string=True)

def set_detector_plan(detector):
    yield from bps.mv(new_detector,detector)




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


    
    









