from IEX_29id.utils.exp import CheckBranch, BL_ioc, Switch_Branch, CheckFlux
from IEX_29id.devices.diagnostics import DiodeC, DiodeD, AllDiagIn
from IEX_29id.scans.setup import Scan_FillIn, Scan_Go
from IEX_29id.devices.mono import Switch_Grating
from epics import caget, caput
from time import sleep

def WireScan(which,scanIOC=None,diag='In',**kwargs):
    """
    Scans the wires located just downstream of M0/M1, 
         which = 'H' for the horizontal, typically CA2
         which = 'V' for the vertical, typically CA3
    diag ='In' -> AllDiagIn(), otherwise you have to put any diagnostics in by hand
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details    
    """
    
    if scanIOC is None:
        scanIOC=BL_ioc()
    if diag == 'In':
        AllDiagIn()
    if which=='H':
        print("\n================== H wire scan (29idb:ca3):")
        Scan_FillIn("29idb:m1.VAL","29idb:m1.RBV",scanIOC,1,-13,-27,-0.25)

    elif which=='V':
        print("\n================== V wire scan (29idb:ca2):")
        Scan_FillIn("29idb:m2.VAL","29idb:m2.RBV",scanIOC,1,-17,-30,-0.25)
    Scan_Go(scanIOC,scanDIM=1,**kwargs)

def CheckM0M1(scanIOC='ARPES',hv=500,stay=None,wire=None,**kwargs): #JM added energy parameter
    """
    Prints Flux in C-branch
    stay = 'yes' => Leaves diagnostics in the beam
    wire ='yes'=> Does wire scans to determine M0M1 alignment
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Switch_Branch('c')
    Switch_Grating('HEG')
    print("\nFlux at hv=500 as off Feb 2019:  ~3.3e-06 A = ~1.5e+11 ph/s")
    Open_BranchShutter()
    CheckFlux(hv=hv,stay=stay)
    if wire is not None:
        WireScan('H',scanIOC,**kwargs)
        WireScan('V',scanIOC,**kwargs)

def Open_BranchShutter():
    "Opens current branch shutter (based on deflecting mirror position)"
    branch=CheckBranch().upper()
    status=caget("PA:29ID:S"+branch+"S_BLOCKING_BEAM.VAL")
    if status == "ON":
        caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
        print("Opening "+branch+"-Shutter...")
    elif status == "OFF":
        print(branch+"-Shutter already open...")

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


def M0M1_SP(Run,Mirror,Go='no'):
    """
    put values from a given run as defined by M0M1_Table as the set points
     you will need to push the Move button
    """
    MirrorPos=M0M1_Table(Run,Mirror).split('/')
    Motor=['TX','TY','TZ','RX','RY','RZ']
    for i in range(len(Motor)):
        PV="29id_m"+str(Mirror)+":"+Motor[i]+"_POS_SP"
        Val=MirrorPos[i]#float(MirrorPos[i])
        print(PV+" = "+Val)
        caput(PV,Val)
    sleep(0.5)
    if Go == 'yes':
        caput('29id_m'+str(Mirror)+':MOVE_CMD.PROC',0,wait=True,timeout=18000)
    else:
        print(" caput(\'29id_m"+str(Mirror)+":MOVE_CMD.PROC\',0)")


def M0M1_Table(Run,Mirror):
    """
    Prints the positions TX / TY / TZ / RX / RY / RZ for either Mirror = 0 or 1 (M0 or M1) for the specified Run
    Run='default' give a reasonable starting position after homing
    M0M1_SP() will put those values as the set points, you will need to push the Move button
    """
    M0M1_Pos={}
    M0M1_Pos['default']={0:'-0.400/-22.5/0/0/0.000/0.0000',1:'0.400/-21.5/0/0/8.400/2.800'}
    M0M1_Pos['2019_1']= {0:'0.3010/-22.5/0/0/-0.151/0.0393',1:'1.449/-21.5/0/0/8.339/2.700'}
    M0M1_Pos['2019_2']= {0:'-0.400/-22.5/0/0/ 0.000/0.000',1:'0.400 /-21.5/0/0/8.436/3.000'}
    return M0M1_Pos[Run][Mirror]
