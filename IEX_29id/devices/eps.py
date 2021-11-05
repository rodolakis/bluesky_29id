from time import sleep
from epics import caget, caput, PV
from IEX_29id.utils.exp import CheckBranch, CheckBranch_Name
from IEX_29id.utils.misc import dateandtime
from IEX_29id.devices.mirror import M3R_Table, Move_M3R
from IEX_29id.scans.setup import Reset_Scan
from IEX_29id.devices.diagnostics import all_diag_out
from IEX_29id.devices.detectors import MPA_HV_OFF
from IEX_29id.utils.misc import WaitForPermission
from IEX_29id.devices.undulator import ID_Start

##########################

def Open_MainShutter():
    caput("PC:29ID:FES_OPEN_REQUEST.VAL",1, wait=True,timeout=180000)
    print("Opening Main Shutter...")


def Close_MainShutter():
    caput("PC:29ID:FES_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing Main Shutter...")

def Open_DShutter():
    branch="D"
    caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Opening "+branch+"-Shutter...")   

def Close_DShutter():
    branch="D"
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")

def Close_CShutter():
    branch="C"
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")



##########################


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



def Open_BranchShutter():
    "Opens current branch shutter (based on deflecting mirror position)"
    branch=CheckBranch().upper()
    status=caget("PA:29ID:S"+branch+"S_BLOCKING_BEAM.VAL")
    if status == "ON":
        caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
        print("Opening "+branch+"-Shutter...")
    elif status == "OFF":
        print(branch+"-Shutter already open...")

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



def BL_Shutdown():
    BL_CloseAllShutters()
    BL_Valve_All(state="CLOSE")
    all_diag_out()
    #EA.zeroSupplies()
    caput("29iddau1:dau1:011:DAC_Set",0)    #RSXS HV = "OFF"

def BL_CloseAllShutters():
    Close_MainShutter()
    Close_CShutter()
    Close_DShutter()

def BL_Valve_All(state="CLOSE"):
    ValveList=["V1A","V2A","V3B","V4B","V5B","V6B","V7C","V8C","V9C","V10C","V7D","V8D","V9D","V10D"]
    for Vname in ValveList:
        pv=BL_Valve2pv(Vname)+state+".VAL"
        caput(pv,1)

def BL_Valve(Vname,state="CLOSE"):
    pv=BL_Valve2pv(Vname)+state+".VAL"
    caput(pv,1)

def BL_Valve2pv(Vname):
    Valve={
        "V1A":"GV01","V2A":"GV02",                #A-Hutch
        "V3B":"GV03","V4B":"GV04","V5B":"GV05","V6B":"GV15",    #B-Branch
        "V7C":"GV06","V8C":"GV08","V9C":"GV09","V10C":"GV10",    #C-Branch
        "C-Turbo":"GV16",                    #ARPES
        "V7D":"GV11","V8D":"GV12","V9D":"GV13","V10D":"GV14",    #D-Branch
        "D-Turbo":"GV17","D-TES":"GV18"                #RSXS
    }
    pv="29id:BLEPS:"+Valve[Vname]+":"
    return pv
