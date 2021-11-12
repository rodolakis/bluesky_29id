from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor, EpicsSignal, PVPositionerPC, EpicsSignalRO
from ophyd import Component, Device
#from hkl.geometries import E4CV

#logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)


class _SlitsMotors(Device):
    m9   = Component(EpicsMotor, "9")     ## top1
    m10  = Component(EpicsMotor, "10")    ## in1
    m11  = Component(EpicsMotor, "11")    ## out1
    m12  = Component(EpicsMotor, "12")    ## bot1
    m13  = Component(EpicsMotor, "13")    ## top2
    m14  = Component(EpicsMotor, "14")    ## in2
    m15  = Component(EpicsMotor, "15")    ## out2
    m16  = Component(EpicsMotor, "16")    ## bot2

slits_motors = _SlitsMotors("29idb:m", name="motors")

class _SoftSize(PVPositionerPC):
    setpoint = Component(EpicsSignal, "size.VAL")  
    readback = Component(EpicsSignalRO, "t2.C")  
    sync = Component(EpicsSignal, "sync.PROC")
class _SoftCenter(PVPositionerPC):
    setpoint = Component(EpicsSignal, "center.VAL")  
    readback = Component(EpicsSignalRO, "t2.D")  
    sync = Component(EpicsSignal, "sync.PROC")

class _FourMotors(Device):
    size_1H = Component(_SoftSize, "1H")  
    size_1V = Component(_SoftSize, "1V")  
    size_2H = Component(_SoftSize, "2H")  
    size_2V = Component(_SoftSize, "2V")  
    center_2H = Component(_SoftCenter, "2H")      
    center_2V = Component(_SoftCenter, "2V")
    center_1H = Component(_SoftCenter, "1H")      
    center_1V = Component(_SoftCenter, "1V")

slits = _FourMotors("29idb:Slit",name="motors")

# 29idb:Slit1Vsize.VAL
# 29idb:Slit1Vt2.C
# 29idb:Slit1Vsync.PROC
# 29idb:Slit1Hsize.VAL
# 29idb:Slit1Ht2.C
# 29idb:Slit1Hsync.PROC
# 29idb:Slit2Vsize.VAL
# 29idb:Slit2Vt2.C
# 29idb:Slit2Vsync.PROC

## defined objects

def sync_motors():
    sync_1H = slits.center_1H.sync
    yield from bps.abs_set(sync_1H,1)
    sync_2H = slits.center_2H.sync
    yield from bps.abs_set(sync_2H,1)
    sync_1V = slits.center_1V.sync
    yield from bps.abs_set(sync_1V,1)
    sync_2V = slits.center_2V.sync
    yield from bps.abs_set(sync_2V,1)


def SetSlit1(Hsize,Vsize,Hcenter,Vcenter):
    sync_1H = slits.center_1H.sync
    yield from bps.abs_set(sync_1H,1)
    sync_1V = slits.center_1V.sync
    yield from bps.abs_set(sync_1V,1)
    Hsize_motor = slits.size_1H.setpoint
    Vsize_motor = slits.size_1V.setpoint
    Hcenter_motor = slits.center_1H.setpoint
    Vcenter_motor = slits.center_1V.setpoint
    yield from bps.mv(Hsize_motor, Hsize, Vsize_motor, Vsize, Hcenter_motor, Hcenter, Vcenter_motor, Vcenter)
   

def SetSlit2(Hsize,Vsize,Hcenter,Vcenter):
    sync_2H = slits.center_2H.sync
    yield from bps.abs_set(sync_2H,1)
    sync_2V = slits.center_2V.sync
    yield from bps.abs_set(sync_2V,1)
    Hsize_motor = slits.size_2H.setpoint
    Vsize_motor = slits.size_2V.setpoint
    Hcenter_motor = slits.center_2H.setpoint
    Vcenter_motor = slits.center_2V.setpoint
    yield from bps.mv(Hsize_motor, Hsize, Vsize_motor, Vsize, Hcenter_motor, Hcenter, Vcenter_motor, Vcenter)
   
