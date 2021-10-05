
from epics import caput, caget
from IEX_29id.utils.folders import *
from IEX_29id.utils.strings import ClearCalcOut
import datetime
from math import *
from IEX_29id.utils.misc import dateandtime
from time import sleep
from IEX_29id.scans.setup import Reset_Scan

from epics import PV

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
def Close_DShutter():
    branch="D"
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")

def Close_CShutter():
    branch="C"
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")

def M3R_Table(branch,motor):   # WARNING: branch_pv uses: D => (Tx <= 0) and (Ry < 0) - Make sure this remains true or change it
    M3R_Table={}
    M3R_Table["C"] = {'scanIOC':'ARPES',  "TX":10,     "TY":0, "TZ":0, "RX":0,      "RY":0,       "RZ":0}
    M3R_Table["D"] = {'scanIOC':'Kappa',  "TX":-2.5,"TY":0, "TZ":0, "RX":-13.955,"RY":-16.450, "RZ":-6} # Optimized for MEG @ 500 eV on 2/29/def start
    M3R_Table["E"] = {'scanIOC':'RSoXS',  "TX":-2.000,"TY":0, "TZ":0, "RX":-13.960,"RY":-16.614, "RZ":-7.500}     #2018_3-- JM changed for RSoXS alignment max diode current
    try:
        position=M3R_Table[branch][motor]
    except KeyError:
        print("WARNING: Not a valid MIR position - check spelling!")
        position=0
    return position

############# WARNING: when changing table, make sure the string sequence below is still relevant:

def Move_M3R(which,Position,q=None):    #motor = "TX","TY","TZ","RX","RY","RZ"
    """
        \"TX\" = lateral                 \"RX\" = Yaw
        \"TY\" = vertical                \"RY\" = Pitch
        \"TZ\" = longitudinal            \"RZ\" = Roll
    """
    motor_pv="29id_m3r:"+which+"_POS_SP"
    caput(motor_pv,Position)
    sleep(2)
    caput("29id_m3r:MOVE_CMD.PROC",1)
    sleep(2)
    while caget("29id_m3r:SYSTEM_STS")==0:
        sleep(.5)
    if q is not None:
        m3=caget('29id_m3r:'+which+'_MON')
        print('\nM3R:{} = {:.4f}'.format(which,m3))

def Check_BranchShutter():
    "Checks current branch shutter is open, if not opens it (based on deflecting mirror position)"
    branch=CheckBranch().upper()
    pvA="PA:29ID:S"+branch+"S_BLOCKING_BEAM.VAL"
    pvB="PB:29ID:S"+branch+"S_BLOCKING_BEAM.VAL"
    while True:
        SSA=caget(pvA)
        SSB=caget(pvB)
        if (SSA == 1) or (SSB == 1):
            print(branch, "SHUTTER CLOSED !!!" , dateandtime())
            sleep(30)
            shutter="PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL"
            caput(shutter,1)
            sleep(30)
        else:
            break


def Switch_Branch(which, forced=False, noshutter=False,noreset=False,nocam=False):
    """Switch beam into which = \"c\" or \"d\" branch (by retracting/inserting deflecting mirror)
        Optionnal keyword argument:
            forced = True      (default=False) => forces change branch even if the beamline think it is already there
            noshutter = True   (default=False) => does not open/close shutters
            noreset   = True   (default=False) => does not reset stuff
            nocam = True   (default=False) => does not turn on/off cameras
    """
    which=which.upper()
    if which in ["C","D","E"]:

    # Check current branch:
        Current_Branch=CheckBranch().upper()
        if Current_Branch == which and forced:
                Tx=round(caget("29id_m3r:TX_MON"),2)
                Ty=round(caget("29id_m3r:TY_MON"),2)
                Tz=round(caget("29id_m3r:TZ_MON"),2)
                Rx=round(caget("29id_m3r:RX_MON"),2)
                Ry=round(caget("29id_m3r:RY_MON"),2)
                Rz=round(caget("29id_m3r:RZ_MON"),2)
                print("    M3R @ "+"%.2f" % Tx, "/","%.2f" % Ty, "/","%.2f" % Tz, "/","%.2f" % Rx, "/","%.2f" % Ry, "/","%.2f" % Rz)
                if Tx == 0 and Ty+Tz+Rx+Ry+Rz == 0:
                    print("\nMirror homed...")
                    print("...Try again using: Switch_Branch(which, forced=True)")
                else:
                    print("\nWell, looks like the beam is already in this branch...")
                    print("...if you want to force the mirror motion, use the argument: forced=True")
        else:

        # Close both shutters:
            print("\n")
            print("Switching branch, please wait...")
            if not noshutter:
                Close_DShutter()
                Close_CShutter()
        # Move M3R:
            motors=["TX","TY","TZ","RX","RY","RZ"]
            for m in motors:
                motor_pv="29id_m3r:"+m+"_POS_SP"
                caput(motor_pv,M3R_Table(which,m))
            sleep(2)
            caput("29id_m3r:MOVE_CMD.PROC",1)
            sleep(2)
            while caget("29id_m3r:SYSTEM_STS")==0:
                sleep(.5)
        # Relax bellows by doing large Z translation:
            Move_M3R("TY",5)
            Move_M3R("TY",0)
            #if which in ["D"]:
                #Move_M3R("TX",-1)        # FR added on 2/2/2017 after adjusting GRT roll
        # Print current positions:
            print(dateandtime()," -  In "+which+"-Branch")
            sleep(2)
            Tx=caget("29id_m3r:TX_MON")
            Ty=caget("29id_m3r:TY_MON")
            Tz=caget("29id_m3r:TZ_MON")
            Rx=caget("29id_m3r:RX_MON")
            Ry=caget("29id_m3r:RY_MON")
            Rz=caget("29id_m3r:RZ_MON")
            print("\nM3R @ "+"%.2f" % Tx, "/","%.2f" % Ty, "/","%.2f" % Tz, "/","%.2f" % Rx, "/","%.2f" % Ry, "/","%.2f" % Rz)
        # Open branch shutters:
            if not noshutter:
                shutter="PC:29ID:S"+which+"S_OPEN_REQUEST.VAL"
                caput(shutter,1)
                sleep(10)
                print("Opening "+which+"-Shutter...")
                Check_BranchShutter()
            if not noreset:
                scanIOC=M3R_Table(which,'scanIOC')
                Reset_Scan(scanIOC)
                Current_Branch=CheckBranch_Name()
            if not nocam:
                pvcam1=PV("29id_ps1:cam1:Acquire")
                pvcam2=PV("29id_ps2:cam1:Acquire")
                pvcam3=PV("29id_ps3:cam1:Acquire")
                pvcam4=PV("29id_ps4:cam1:Acquire")
                pvcam6=PV("29id_ps6:cam1:Acquire")
                pvcam7=PV("29id_ps7:cam1:Acquire")
                cam_list=[pvcam1,pvcam2,pvcam3,pvcam4,pvcam6,pvcam7]
                cam_dict={'C':[0,1,2],'D':[3,4,6]}  # index of cam_list 
                for pvcam in cam_list:                  # turn OFF all cam
                    try:
                        if pvcam.connected:  pvcam.put(0)
                    except:
                        pass
                for i in cam_dict[which]:                 # turn ON relevant cam
                    try:
                        if cam_list[i].connected: cam_list[i].put(1)
                        else: print(cam_list[i].pvname+' not connected')
                    except:
                        pass
    else:
        print("\nWARNING: Not a valid branch name, please select one of the following:")
        print(" \"c\" for ARPES, \"d\" for Kappa ")

