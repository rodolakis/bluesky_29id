from epics import caput,caget
from time import sleep
from IEX_29id.utils.strings import ClearCalcOut

           
# def Kappa_Detector_Offset(detector):
#     """
#     detector = d3, d4, mcp, apd, yag
#     """
#     #det={'d4': 0.0,'d3': 7.684, 'mcp': 18.275, 'apd': 29.753, 'yag': 33.269, }   # up to 2020_3
#     det={'d4': 0.0,'d3': -29.123, 'mcp': -18.6416-0.2+0.11, 'apd': 0.0, 'yag': 4.036 }    # 2021_1
#     angle=det[detector]
#     return angle


def set_detector(detector):
    """
    detector = d3, d4, mcp, apd, yag
    Reset tth for a given detector.
    """
    caput('29idKappa:det:set',detector)
    return
    
def MPA_Interlock():
    ioc="Kappa"
    n=7
    pvioc="29id"+ioc+":userCalcOut"+str(n)
    ClearCalcOut(ioc,n)
    LLM=-16
    HLM=-6
    caput(pvioc+".DESC","MPA Interlock")
    caput(pvioc+".INPA","29idKappa:m9.DRBV CP NMS")
    caput(pvioc+".B",1)
    caput(pvioc+".CALC$","ABS((("+str(LLM)+"<A && A<"+str(HLM)+") && (B>0))-1)")
    caput(pvioc+".OCAL$",'A')
    caput(pvioc+".OOPT",2)    # When zero
    caput(pvioc+".DOPT",0)    # Use CALC
    caput(pvioc+".IVOA",0)    # Continue Normally
    caput(pvioc+".OUT","29iddMPA:C0O PP NMS")