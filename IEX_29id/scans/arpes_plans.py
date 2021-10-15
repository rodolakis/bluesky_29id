
from epics import caget, caput
from IEX_29id.scans.setup import Scan_Go, Scan_FillIn
from IEX_29id.utils.exp import BL_ioc
from IEX_29id.devices.arpes_motors import ARPES_PVmotor

def Scan_ARPES_Go(scanIOC='ARPES',scanDIM=1,**kwargs):
    """Starts the N dimension scan in the ARPES chamber (N=ScanDIM)
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs) 
    
def ARPES_scanDIM():
    """
    sets the default scanDIM for ARPES (not 1 due to sweeps)
    """
    scanDIM=1
    return scanDIM


def Scan_ARPES_Motor_Go(name,start,stop,step,mode="absolute",**kwargs):
    """
    Fills in the Scan Record and the presses the go button
    if scanIOC=None then uses BL_ioc()
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details      
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())

    Scan_ARPES_Motor(name,start,stop,step,mode,**kwargs)
    Scan_ARPES_Go(kwargs["scanIOC"],kwargs["scanDIM"])

def Scan_ARPES_Motor(name,start,stop,step,mode="absolute",**kwargs):  # FR added **kwargs in the args 06/14/21
    """
    Fills in the Scan Record does NOT press Go
    if scanIOC=None then uses BL_ioc()
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())
    kwargs.setdefault("settling_time",0.1)
    
    m_RBV=ARPES_PVmotor(name)[0]
    m_VAL=ARPES_PVmotor(name)[1]
    if mode == "relative":
        current_value=caget(m_RBV)
        abs_start=round(current_value+start,3)
        abs_stop =round(current_value+stop,3)
        print("start, stop, step = "+str(abs_start)+", "+str(abs_stop)+", "+str(step))
    else:
        abs_start=start
        abs_stop =stop
    caput("29id"+kwargs["scanIOC"]+":scan1.PDLY",kwargs["settling_time"])
    Scan_FillIn(m_VAL,m_RBV,kwargs["scanIOC"],kwargs["scanDIM"],abs_start,abs_stop,step)
    