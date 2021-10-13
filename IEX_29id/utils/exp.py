
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
from IEX_29id.devices.diagnostics import DiodeC, DiodeD
from IEX_29id.devices.detectors import MPA_HV_OFF
import numpy as np
from IEX_29id.devices.mirror import Move_M3R, M3R_Table



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

def CheckFlux(hv=500,mode='RCP',stay=None):
    Switch_IDMode(mode)
    energy(hv)
    branch=CheckBranch()
    SR=round(caget("S:SRcurrentAI.VAL"),2)
    if branch == "c":
        current_slit=caget('29idb:Slit3CFit.A')
        DiodeC('In')
        diode=caget('29idb:ca15:read')
    elif branch == "d":
        current_slit=caget('29idb:Slit4Vsize.VAL')
        DiodeD("In")
        diode=caget('29idb:ca14:read')
    SetExitSlit(50)
    flux=ca2flux(diode)
    print("\n----- Current on diode   : %.3e" % diode, "A")
    print("----- Corresponding flux: %.3e" % flux, "ph/s \n")
    print("----- Storage ring current: %.2f" % SR, "mA")
    if stay is None:
        AllDiagOut()
    SetExitSlit(current_slit)


def AllDiagOut(DiodeStayIn=None):
    """Retracts all diagnostic
    if DiodeStayIn = something then it leaves the diode in for the current branch
    """
    diag=AllDiag_dict()
    text=""
    #which motor is Diode of interest
    if DiodeStayIn != None:
        DiodeStayIn=CheckBranch()
    if DiodeStayIn == 'c':
        diode_motor=diag["motor"]["gas-cell"]
    elif DiodeStayIn == 'd':
        diode_motor=diag["motor"]["D5D"]
    else:
        diode_motor=None
    #Taking out the diagnostic
    for motor in list(diag["Out"].keys()):
        if motor is diode_motor:
            text=' except Diode-'+DiodeStayIn
            #putting Diode In if not already in -JM
            position=diag["In"][motor]
            caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
        else:
            position=diag["Out"][motor]
            caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    text="All diagnostics out"+text
    print("\n",text)

def ca2flux(ca,hv=None,p=1):
    curve=LoadResponsivityCurve()
    responsivity=curve[:,0]
    energy=curve[:,1]
    charge = 1.602e-19
    if hv is None:
        hv=caget('29idmono:ENERGY_SP')
        print("\nCalculating flux for:")
        print("   hv = %.1f eV" % hv)
        print("   ca = %.3e Amp" % ca)
    eff=np.interp(hv,energy,responsivity)
    flux = ca/(eff*hv*charge)
    if p is not None:
        print("Flux = %.3e ph/s\n" % flux)
    return flux


def LoadResponsivityCurve():
    FilePath='/home/beams/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/'
    FileName="DiodeResponsivityCurve"
    data = np.loadtxt(FilePath+FileName, delimiter=' ', skiprows=1)
    return data

def WaitForPermission():
    """
    Monitors the ID permissions and waits for the ID to be in User Mode and then breaks
    Checks the status every 30 seconds
    """
    while True:
        ID_Access=caget("ID29:AccessSecurity.VAL")
        if (ID_Access!=0):
            print("Checking ID permission, please wait..."+dateandtime())
            sleep(30)
        else:
            print("ID now in user mode -"+dateandtime())
            break
def WaitForBeam():
    """
    Monitors the storage ring current and breaks when the ring current is above 60 mA
    Checks the status every 30 seconds
    """
    while True:
        SR=caget("S:SRcurrentAI.VAL")
        if (SR<60):
    #        print "No beam current, please wait..."+dateandtime()
            sleep(30)
        else:
            print("Beam is back -"+dateandtime())
            break

def Get_MainShutter():
    "Checks main shutter is open, does not opens it"
    SS1=caget("EPS:29:ID:SS1:POSITION")
    SS2=caget("EPS:29:ID:SS2:POSITION")
    PS2=caget("EPS:29:ID:PS2:POSITION")
    check=SS1*SS2*PS2
    if (check!=8):
        return False
    else:
        return True

def Check_MainShutter():
    "Checks main shutter is open, if not opens it"
    while True:
        SS1=caget("EPS:29:ID:SS1:POSITION")
        SS2=caget("EPS:29:ID:SS2:POSITION")
        PS2=caget("EPS:29:ID:PS2:POSITION")
        check=SS1*SS2*PS2
        if (check!=8):
            print("MAIN SHUTTER CLOSED !!!" , dateandtime())
            WaitForPermission()
            Open_MainShutter()
            sleep(10)
        else:
            break
    ID_off=caget("ID29:Main_on_off.VAL")
    if ID_off == 1:
        ID_Start("RCP")
        sleep(30)


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

def Close_DBranch():
    try:
        MPA_HV_OFF()
    except:
        shutter=caget('PA:29ID:SDS_BLOCKING_BEAM.VAL',as_string=True)
        if shutter == 'OFF':  #OFF = beam not blocked = shutter open
            Close_DShutter()
        i=0
        while True:
            valve=caget('29id:BLEPS:GV14:OPENED:STS',as_string=True)
            if (valve=='GOOD'):
                sleep(10)
                Close_DValve()
                i+=1
                if i == 3:
                    print("Can't close valve; check status")
                    break
            elif (valve == 'BAD'):
                print('RSXS chamber valve now closed')
                break


def Close_CValve():
    branch="C"
    caput("29id:BLEPS:GV10:CLOSE.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Valve...")

def Close_DValve():
    branch="D"
    caput("29id:BLEPS:GV14:CLOSE.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Valve...")

def light(ON_OFF):
    if ON_OFF in ['On','on','ON']:
        light=0
    elif ON_OFF in ['Off','off','OFF']:
        light=1
    caput('29idd:Unidig1Bo0',light)
    print(("Turning light "+ON_OFF+"."))
