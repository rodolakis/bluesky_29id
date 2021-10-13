__all__ = """
    meshW_plan
    diodeC_plan
    diodeD_plan
    meshD_plan
""".split()

from epics import caget, caput
#from time import sleep
#from IEX_29id.utils.exp import AllDiag_dict
from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor
from ophyd import Component, Device

logger = logging.getLogger(__name__)


class _DiagnosticMotors(Device):
    m5 = Component(EpicsMotor, "5")
    m20 = Component(EpicsMotor, "20")
    m28 = Component(EpicsMotor, "28")

diagnostic_motors = _DiagnosticMotors("29idb:m", name="motors")
# now I can import diagnostic motors if needed: from diagnostic import diagnostic_motors
# diagnostic_motors.m5
# diagnostic_motors.m20
# diagnostic_motors.m28

def _pick_motor(number):
    return getattr(diagnostic_motors, f"m{number}")

def _diagnostic_plan(insert,motor_number,desc,n=None):
    """
    Inserts/retracts diagnostic

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    diag = AllDiag_dict()
    motor = _pick_motor(motor_number)  # motors.m#
    placement = {True: "In", False: "Out"}[insert]
    if n is None:
        position=diag[placement][motor_number]
    else:
        position=diag[placement][motor_number][n]
    yield from bps.mv(motor, position)
    logger.info("%s: %s", desc, placement)

def meshW_plan(insert):
    """
    Inserts/retracts W mesh (post-M0M1)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,5,'W-mesh')

def diodeC_plan(insert):
    """
    Inserts/retracts gas cell diode (post ARPES slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,20,'Diode ARPES')

def diodeD_plan(insert):
    """
    Inserts/retracts RSXS diode (post-slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,28,'Diode  RSXS',n=1)  # n=1 diode position

def meshD_plan(insert):
    """
    Inserts/retracts RSXS diode (RSXS-slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,28,'Diode  RSXS',n=0) # n=0 mesh position

# ----------------------------------


def MeshW(In_Out):
    "Inserts/retracts RSXS mesh (post-slit); arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=5; position=diag[In_Out][motor]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nD1A W-Mesh: "+ In_Out)

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





def AllDiag_dict():
    """
    Dictionary of Diagnostic positions In and Out by either motor number or name
    WARNING: When updating motor values, also update the following screens:
        - 29id_BL_Layout.ui               (for MeshD and DiodeC)
        - 29id_Diagnostic.ui
        - 29idd_graphic
    usage:       
        AllDiag_dict()['name'] returns dictionary motor:name
        AllDiag_dict()['motor'] returns dictionary name:motor   
        AllDiag_dict()['In'] returns dictionary motor:In position  (where val can be a list for multiple position)  
        AllDiag_dict()['Out'] returns dictionary motor:In position  
                motor=AllDiag_dict()['motor']['gas-cell']
                pos_in=AllDiag_dict()['In'][motor]
    """
    diag={}
    diag["In"]  = {1:-4, 2:-10, 3:-4, 4:-4, 5:-55, 6:-46, 7:-20, 17:-56, 20:-30, 25:-56, 28:[-57,-71.25]}                                                                          
    diag["Out"] = {1:-4, 2:-10, 3:-4, 4:-4, 5:-20, 6:-20, 7:-20, 17:-20, 20:-21, 25:-20, 28:-20}    
    diag["name"]= {1:"H-wire", 2:"V-wire", 3:"H-Diagon", 4:"V-Diagon", 5:"W-mesh",
     6:"D2B", 7:"D3B", 17:"D4C/pre-slit", 20:"gas-cell", 25:"D4D/pre-slit", 28:"D5D/pre-RSXS"}
    diag["motor"]= {"H-wire":1, "V-wire":2, "H-Diagon":3, "V-Diagon":4,"W-mesh":5,
     "D2B":6, "D3B":7, "D4C":17, "gas-cell":20,"D4D":25,"D5D":28}
    return diag
