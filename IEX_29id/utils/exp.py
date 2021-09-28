
from epics import caput, caget
from IEX_29id.utils.folders import *
from IEX_29id.utils.strings import ClearCalcOut
from os import system
import datetime
import time


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

