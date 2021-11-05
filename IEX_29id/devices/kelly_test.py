
from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor, EpicsSignal, PVPositionerPC, EpicsSignalRO
from ophyd import Component, Device
#from hkl.geometries import E4CV

#logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)














# Functions to convert:

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