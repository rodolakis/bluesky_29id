__all__ = """
    all_diag_in
    meshW_plan
    diodeC_plan
    diodeD_plan
    meshD_plan
""".split()


from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor
from ophyd import Component, Device


logger = logging.getLogger(__name__)


class _DiagnosticMotors(Device):
    m1  = Component(EpicsMotor, "1")
    m2  = Component(EpicsMotor, "2")
    m3  = Component(EpicsMotor, "3")
    m4  = Component(EpicsMotor, "4")
    m5  = Component(EpicsMotor, "5")
    m6  = Component(EpicsMotor, "6")
    m7  = Component(EpicsMotor, "7")
    m17 = Component(EpicsMotor, "17")
    m20 = Component(EpicsMotor, "20")
    m25 = Component(EpicsMotor, "25")
    m28 = Component(EpicsMotor, "28")

diagnostic_motors = _DiagnosticMotors("29idb:m", name="motors")


# now I can import diagnostic motors if needed: from diagnostic import diagnostic_motors
# diagnostic_motors.m5
# diagnostic_motors.m20
# diagnostic_motors.m28


def _pick_motor(number):
    return getattr(diagnostic_motors, f"m{number}")


def _diagnostic_dictionary():
    """
    Dictionary of diagnostic name, out positions and in position by motor number
    WARNING: When updating motor position values, also update the following screens:
        - 29id_BL_Layout.ui       (for MeshD and DiodeC)
        - 29id_Diagnostic.ui
        - 29idd_graphic
    """
    diag = {}
    #  motor_number: [name, out_position, in_position]
    diag = {  1:['H-wire',  -4, -4],
              2:['V-wire',  -10,-10],
              3:['H-Diagon',-4, -4],
              4:['V-Diagon',-4, -4],
              5:['W-mesh',  -20,-55],
              6:['D2B',     -20,-46],
              7:['D3B',     -20,-20],
             17:['D4C',     -20,-56],
             20:['D5C-diode',-21,-30],
             25:['D4D',     -20,-56],
             28:[['D5D-mesh','D5D-diode'],-20,[-57,-71.25]]}    ## 1st position = mesh, 2nd position = diode (?)

    return diag


def _diagnostic_plan(insert,motor_number,n=None):
    """
    Inserts/retracts diagnostic

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    diag  = _diagnostic_dictionary()  
    motor = _pick_motor(motor_number)  # motors.m#
    placement = {False: [1,"Out"], True: [2,"In"]}[insert][1]
    setpoint  = {False: [1,"Out"], True: [2,"In"]}[insert][0]
    if n is None:
        position=diag[motor_number][setpoint]
        desc  = diag[motor_number][0]
    else:
        position=diag[motor_number][setpoint][n]
        desc  = diag[motor_number][0][n]
    yield from bps.mv(motor, position)
    logger.info("%s: %s", desc, placement)


def all_diag_in():
    "Inserts all diagnostic (meshes and diodes) for pinhole scans"
    diag=_diagnostic_dictionary()
    insert=True
    for motor_number in list(diag.keys()):
        if motor_number == 28: n = 0
        else: n = None
        yield from _diagnostic_plan(insert,motor_number,n)
    logger.info("All diagnostics in (meshes and diodes) for pinhole scans")


def all_diag_out(keep_diode_in=False, keep_mesh_in=False):
    """
    Retracts all diagnostics.
    If keep_diode_in or keep_mesh_in = True then leaves it inserted.
    """
    diag=_diagnostic_dictionary()
    diag_list=list(diag.keys())
    insert=False
    text='.'
    if keep_diode_in:
        diag_list = diag_list.remove(20)
        text=' except diode ARPES'
    if keep_mesh_in:
        diag_list = diag_list.remove(28)
        text=' except mesh RSXS'
    for motor_number in diag_list:
        yield from _diagnostic_plan(insert,motor_number)
    logger.info("All diagnostics out"+text)


def meshW_plan(insert):
    """
    Inserts/retracts W mesh (post-M0M1)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,5)


def diodeC_plan(insert):
    """
    Inserts/retracts gas cell diode (post ARPES slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,20)


def meshD_plan(insert):
    """
    Inserts/retracts RSXS diode (RSXS-slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,28,n=0) # n=0 mesh position


def diodeD_plan(insert):
    """
    Inserts/retracts RSXS diode (post-slit)

    insert bool: ``True`` if should insert, ``False`` to retract 
    """
    yield from _diagnostic_plan(insert,28,n=1)  # n=1 diode position

