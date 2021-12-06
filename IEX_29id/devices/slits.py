
__all__ = """
    slits
""".split()


import logging
from ophyd import EpicsSignal, PVPositionerPC, EpicsSignalRO    
from ophyd import Component, Device
from apstools.devices import EpicsDescriptionMixin


# see 4ID-D: https://github.com/APS-4ID-POLAR/ipython-polar/blob/master/profile_bluesky/startup/instrument/devices/slits.py

class _SoftSlitSize(PVPositionerPC):
    setpoint = Component(EpicsSignal, "size.VAL")           # 29idb:Slit1Hsize.VAL   => setpoint
    readback = Component(EpicsSignalRO, "t2.C")             # 29idb:Slit1t2.C        => readback  
    sync = Component(EpicsSignal,"sync.PROC",kind='omitted')# RO means ReadOnly, those are PV that we cannot write to 
    done_value = 1                                          # done_value = 1 (Done) or 0 (moving)
    done = Component(EpicsSignalRO,'DMOV',kind='omitted')   # slits done = 29idb:Slit1VDMOV


class _SoftSlitCenter(PVPositionerPC):
    setpoint = Component(EpicsSignal, "center.VAL")         # 29idb:Slit1Hsize.VAL   => setpoint
    readback = Component(EpicsSignalRO, "t2.D")             # 29idb:Slit1t2.C        => readback  
    sync = Component(EpicsSignal,"sync.PROC",kind='omitted')               # RO means ReadOnly, those are PV that we cannot write to 
    done_value = 1                                          # done_value = 1 (Done) or 0 (moving)
    done = Component(EpicsSignalRO,'DMOV',kind='omitted')                 # slits done = 29idb:Slit1VDMOV

#class _SoftSlit3(PVPositionerPC):
#    setpoint = Component(EpicsSignal, "Fit.A")               # 29idb:Slit3CFit.A     => setpoint
#    readback = Component(EpicsSignalRO, "3CRBV")             # 29idb:Slit3CRBV       => readback  

class _My4Slits(Device):
    H1size = Component(_SoftSlitSize, "1H")    
    V1size = Component(_SoftSlitSize, "1V")  
    H1center = Component(_SoftSlitCenter, "1H")    
    V1center = Component(_SoftSlitCenter, "1V")  
    H2size = Component(_SoftSlitSize, "2H")    
    V2size = Component(_SoftSlitSize, "2V")  
    H2center = Component(_SoftSlitCenter, "2H")    
    V2center = Component(_SoftSlitCenter, "2V") 
    V4center = Component(_SoftSlitCenter, "4V") 
    V4size = Component(_SoftSlitSize, "4V") 
    #V3size= Component(_SoftSlit3, "3V") 
    
## Instantiate pseudo motors
slits = _My4Slits("29idb:Slit",name="motors")


