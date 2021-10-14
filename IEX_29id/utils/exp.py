
from epics import caput, caget
from IEX_29id.utils.folders import *
from IEX_29id.utils.strings import ClearCalcOut
import datetime
from math import *
from IEX_29id.utils.misc import dateandtime
from time import sleep
from IEX_29id.scans.setup import Reset_Scan
from epics import PV
from IEX_29id.devices.energy import Switch_IDMode, energy, Open_MainShutter, ID_Start
from IEX_29id.devices.slits import SetExitSlit
from IEX_29id.devices.diagnostics import diodeC_plan, diodeD_plan, all_diag_out
from IEX_29id.devices.detectors import MPA_HV_OFF
import numpy as np
from IEX_29id.devices.mirror import Move_M3R, M3R_Table

def light(ON_OFF):
    if ON_OFF in ['On','on','ON']:
        light=0
    elif ON_OFF in ['Off','off','OFF']:
        light=1
    caput('29idd:Unidig1Bo0',light)
    print(("Turning light "+ON_OFF+"."))

def Check_run():
    todays_date = datetime.today()
    
    date1 = ( 1, 1)   # start date run_1
    date2 = ( 5, 1)   # start date run_2
    date3 = (10, 1)   # start date run_3
    
    datex = (todays_date.month,todays_date.day)
    
    if date1 <= datex < date2:
        run=str(todays_date.year)+'_1'
    elif date2 <= datex < date3:
        run=str(todays_date.year)+'_2'
    else:
        run=str(todays_date.year)+'_3'
    print('Current run:', run)
    return(run)




def CheckBranch():
    BL_mode=BL_Mode_Read()[0]
    BranchPV=caget("29id:CurrentBranch.VAL")
    if BL_mode==2:
        branch="c"
    elif BL_mode==3:
        branch="e"
    else:
        if (BranchPV == 0):
            branch = "c"        # PV = 0 => ARPES
        else:
            branch = "d"        # PV = 1 => RSXS
    return branch

def CheckBranch_Name():
    BL_mode=BL_Mode_Read()[0]
    BranchPV=caget("29id:CurrentBranch.VAL")
    if BL_mode==2:
        branchname= "He Lamp"
    else:
        if (BranchPV == 0):
            branchname = "ARPES"
        else:
            branchname = "RSXS"
    return branchname


## BeamLine mode functions
def BL_Mode_Set(which):
    """
    which = "Staff", "User", "He" (Helium Lamp), "RSoXS"; if which is not specified then i=4
    """
    n=5
    ClearCalcOut("b",n)
    pvstr="29idb:userCalcOut"+str(n)
    caput(pvstr+".DESC","BL_Mode")
    if which == "Staff":
        i=1        # Staff
    elif which == "He":
        i=2        # Helium
    elif which == "User":
        i=0        # User
    elif which == "RSoXS":
        i=3
    else:
        i=4
    caput(pvstr+".A",i)

def BL_Mode_Read():
    caput("29idb:userCalcOut5.PROC",1)            # After reboot value return to 0 even if A=1
    BL_mode=caget("29idb:userCalcOut5.VAL")        # User = 0, Staff = 1, He = 2, Other = 3
    if BL_mode == 1:
        which="Staff"
    elif BL_mode == 2:
        which="He Lamp"
    elif BL_mode == 0:
        which="User"
    elif BL_mode == 3:
        which="RSoXS"
    elif BL_mode == 4:
        which="Other"
    return BL_mode,which


def BL_ioc():
    BL_mode=BL_Mode_Read()[0]            # User = 0, Staff = 1, He = 2
    if BL_mode == 0 or BL_mode == 1:         # User + Staff
        branch=CheckBranch()            # TO BE REMOVED ONCE WE HAVE IT AS A GLOBAL VARIABLE
        if branch == "c":
            scanIOC='ARPES'
        if branch == "d":
            scanIOC='Kappa'
    elif  BL_mode == 2:                    # Helium
        scanIOC='ARPES'
    elif  BL_mode ==3:                    # RSoXS chamber
        scanIOC='RSoXS'
    return scanIOC





# def Close_CBranch(**kwargs):
#     """
#     EA.off()
#     Close_CShutter()
#     Close_CValve()
#     **kwargs
#         EA="off"; turns off EA (None = doesn't check)
#     """
#     kwargs.setdefault("EA","off")
#     if kwargs["EA"] == "off":
#         EA.off()
#     shutter=caget('PA:29ID:SCS_BLOCKING_BEAM.VAL',as_string=True)
#     if shutter == 'OFF':  #OFF = beam not blocked = shutter open
#         Close_CShutter()
#     i=0
#     while True:
#         valve=caget('29id:BLEPS:GV10:OPENED:STS',as_string=True)
#         if (valve=='GOOD'):
#             sleep(10)
#             Close_CValve()
#             i+=1
#             if i == 3:
#                 print("Can't close valve; check status")
#                 break
#         elif (valve == 'BAD'):
#             print('ARPES chamber valve now closed')
#             break

