
from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor, EpicsSignal, PVPositionerPC, EpicsSignalRO
from ophyd import Component, Device
#from hkl.geometries import E4CV

#logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class MyEpicsMotor(EpicsMotor):
    sync = Component(EpicsSignal, "sync.PROC")
    desc = Component(EpicsSignalRO,".DESC")
    homf = Component(EpicsSignal,".HOMF")
    dval = Component(EpicsSignal,".DVAL")

class _SlitsMotors(Device):
    m1  = Component(MyEpicsMotor, "1")    ## 1H  
    m2  = Component(MyEpicsMotor, "2")    ## 1V
    m3  = Component(MyEpicsMotor, "3")    ## 2H
    m4  = Component(MyEpicsMotor, "4")    ## 2V

slits_motors = _SlitsMotors("29idb:m", name="motors")

class _SoftMotor(PVPositionerPC):
    setpoint = Component(EpicsSignal, "")
    readback = Component(EpicsSignalRO, ".RBV")   
    desc = Component(EpicsSignalRO,".DESC")

class _FourMotors(Device):
    Slit1H = Component(_SoftMotor, "29idb:Slit1H")   
    Slit1V = Component(_SoftMotor, "29idb:Slit1V")    
    Slit2H = Component(_SoftMotor, "29idb:Slit2H")      
    Slit2V = Component(_SoftMotor, "29idb:Slit2V")

four_motors = _FourMotors("",name="motors")
 
def sync_PI_motors():
    """
    Synchronize VAL with RBV for 1H, 1V, 2H, 2V
    """
    Slit1H_motor = slits_motors.m1
    Slit1V_motor = slits_motors.m2
    Slit2H_motor = slits_motors.m3
    Slit2V_motor = slits_motors.m4
    yield from bps.abs_set(Slit1H_motor.sync,1)
    yield from bps.abs_set(Slit1V_motor.sync,1)
    yield from bps.abs_set(Slit2H_motor.sync,1)
    yield from bps.abs_set(Slit2V_motor.sync,1)

class _Status(Device):
    st1  = Component(EpicsSignal, "1")        
    st2  = Component(EpicsSignal, "2")    
    st3  = Component(EpicsSignal, "3")     
    st4  = Component(EpicsSignal, "4")    

## Instantiate status
status  = _Status("29idb:gp:text",name="status")  



def SetSlit1A(Hsize,Vsize,Hcenter,Vcenter):   
    """move slits 1A: Hsize x Vsize centered at (Hcenter,Vcenter)"""
    caput("29idb:Slit1Hsync.PROC",1)    # make sure slits are in sink with real motors
    caput("29idb:Slit1Vsync.PROC",1)
    caput("29idb:Slit1Hsize.VAL", Hsize)
    caput("29idb:Slit1Vsize.VAL", Vsize)
    caput("29idb:Slit1Hcenter.VAL",Hcenter)
    caput("29idb:Slit1Vcenter.VAL",Vcenter)
    print("Slit-1A = ("+str(round(Hsize,3))+"x"+str(round(Vsize,3))+") @ ("+str(Hcenter)+","+str(Vcenter)+")")   # use status strings

def SetSlit2B(Hsize,Vsize,Hcenter,Vcenter):
    caput("29idb:Slit2Hsync.PROC",1)
    caput("29idb:Slit2Vsync.PROC",1)
    caput("29idb:Slit2Hsize.VAL", Hsize)
    caput("29idb:Slit2Vsize.VAL", Vsize)
    caput("29idb:Slit2Hcenter.VAL",Hcenter)
    caput("29idb:Slit2Vcenter.VAL",Vcenter)
    print("Slit-2B = ("+str(Hsize)+"x"+str(Vsize)+") @ ("+str(Hcenter)+","+str(Vcenter)+")")