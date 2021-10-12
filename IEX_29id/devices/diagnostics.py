from epics import caget, caput
from time import sleep
from IEX_29id.utils.exp import AllDiag_dict

# ----------------------------------
__all__ = ["m5", "MeshW_plan"]

from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor
from ophyd import Component, Device

logger = logging.getLogger(__name__)

# from diagnostics import *

# https://blueskyproject.io/ophyd/reference/builtin-devices.html#epics-motor
# https://blueskyproject.io/bluesky/plans.html#stub-plans

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



