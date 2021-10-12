from epics import caget, caput
from time import sleep
from IEX_29id.utils.exp import AllDiag_dict

# ----------------------------------
__all__ = """
    motors
    MeshW_plan
""".split()

"""markdown
# Bluesky documentation reference tables

## The most common ophyd imports

class | import | description | URL
--- | --- | --- | ---
`EpicsSignal` | `from ophyd import EpicsSignal` | connect with ONE PV | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device
`EpicsSignalRO` | `from ophyd import EpicsSignalRO` | connect with ONE read-only PV | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device
`EpicsSignalWithRBV` | `from ophyd import EpicsSignalWithRBV` | connect with TWO PVs (one for read AND one for write) | https://blueskyproject.io/ophyd/generated/ophyd.areadetector.base.EpicsSignalWithRBV.html#ophyd.areadetector.base.EpicsSignalWithRBV
`EpicsMotor` | `from ophyd import EpicsMotor` | connect with ONE EPICS motor record | https://blueskyproject.io/ophyd/generated/ophyd.epics_motor.EpicsMotor.html#ophyd.epics_motor.EpicsMotor
`ScalerCH` | `from ophyd.scaler import ScalerCH` | connect with one EPICS scaler record | https://blueskyproject.io/ophyd/generated/ophyd.scaler.ScalerCH.html#ophyd.scaler.ScalerCH
`Signal` | `from ophyd import Signal` | fundamental single piece of information, non-EPICS, in Python memory only
`Device` | `from ophyd import Device` | make a group of Signal(s) and/or Device(s) | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device
`Component` | `from ophyd import Component` | Used in a Device to define one attribute | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device

other: EPICS Area Detector, MCA

## The most common bluesky imports
description | import | URL
--- | --- | ---
Pre-assembled Plans | `from bluesky import plans as bp` | https://blueskyproject.io/bluesky/plans.html
Stub Plans (used in plans) | `from bluesky import plan_stubs as bps` | https://blueskyproject.io/bluesky/plans.html#stub-plans

Other: databroker, metadata, baseline, monitor
"""

from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor
from ophyd import Component, Device

logger = logging.getLogger(__name__)

# from diagnostics import *


# m5 = EpicsMotor("29idb:m5", name="m5")
# m20 = EpicsMotor("29idb:m20", name="m20")
# m28 = EpicsMotor("29idb:m28", name="m28")

class MyMotors(Device):
    m5 = Component(EpicsMotor, "5")
    m20 = Component(EpicsMotor, "20")
    m28 = Component(EpicsMotor, "28")

motors = MyMotors("29idb:m", name="motors")
# motors.m5
# motors.m20
# motors.m28

def pick_motor(number):
    return getattr(motors, f"m{number}")

def MeshW_plan(insert):
    """
    Inserts/retracts RSXS mesh (post-slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    diag = AllDiag_dict()
    motor_number = 5
    motor = pick_motor(motor_number)  # motors.m5
    placement = {True: "In", False: "Out"}
    position = diag[placement][motor_number]
    yield from bps.mv(motor, position)
    logger.info("D1A W-Mesh: %s", placement)
# ----------------------------------


def MeshW(In_Out):
    "Inserts/retracts RSXS mesh (post-slit); arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=5; position=diag[In_Out][motor]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nD1A W-Mesh: "+ In_Out)

def AllDiagIn():
    "Inserts all diagnostic (meshes and diodes) for pinhole scans"
    diag=AllDiag_dict()
    for motor in list(diag["In"].keys()):
        position=diag["In"][motor]
        if isinstance(position, list):  #  type(position) == list:
            position=position[0]
        caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
        print('m'+str(motor)+' = '+str(position))
    print("All diagnostics in (meshes and diodes) for pinhole scans")


def AllMeshIn():
    "Inserts all diagnostic (meshes and gas-cell is out) for wire scans"
    diag=AllDiag_dict()
    for motor in list(diag["In"].keys()):
        position=diag["In"][motor]
        if type(position) == list:
            position=position[0]
        caput("29idb:m"+str(motor)+".VAL",position,timeout=18000)
        print('m'+str(motor)+' = '+str(position))
    print("All diagnostics in (meshes and diodes) for pinhole scans")

def DiodeC(In_Out):
    "Inserts/retracts ARPES (gas-cell) diode; arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=20; position=diag[In_Out][motor]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nARPES Diode: "+ In_Out)

def DiodeD(In_Out):
    "Inserts/retracts RSXS diode; arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=28; position=position=diag[In_Out][motor]
    if type(position) == list:
        position=position[1]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nRSXS Diode: "+ In_Out)
    
def Diagnostic(which,In_Out):
    "Inserts/retracts a diagnostic(motor number or name) either = \"In\" or \"Out\""
    diag=AllDiag_dict()
    if type(which) is int:
        motor=which
        name=diag['name'][motor]
    else:
        name=which
        motor=diag["motor"][name]
    position=diag[In_Out][motor]

    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\n"+name+": "+ In_Out)



