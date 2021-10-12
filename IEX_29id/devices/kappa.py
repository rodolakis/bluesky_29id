from epics import caget, caput
from time import sleep
from IEX_29id.utils.exp import CheckBranch, BL_ioc
from IEX_29id.devices.motors import Move_Motor_vs_Branch, ARPES_PVmotor, Kappa_PVmotor, Move_ARPES_Motor
from IEX_29id.scans.setup import Scan_Go, Scan_FillIn, Scan_Kappa_Motor_Go, Scan_Progress, Scan_FillIn_Pos2
from math import *
from IEX_29id.devices.motors import UMove_Motor_vs_Branch
from IEX_29id.devices.kappa import cts
### all the function that move/scan the diffractometer:
### tth, th, phi, chi, x, y, z



def mvtth(val):
    """ Moves tth motor in the in the Kappa chamber
    """
    name="tth"
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        print("   tth motor does not exit")
    #elif branch == "d":
    elif mybranch == "d":
        Move_Motor_vs_Branch(name,val)



def Sync_PI_Motor():
    '''Syncronize VAL with RBV'''
    for i in [7,8,9]:
        VAL='29idKappa:m'+str(i)+'.VAL'
        RBV='29idKappa:m'+str(i)+'.RBV'
        current_RBV=caget(RBV)
        caput(VAL,current_RBV)
    print('PI motors VAL synced to RBV')



def Sync_Euler_Motor():
    ''' Sychronize 4C pseudo motor with real motors' positions'''
    caput('29idKappa:Kappa_sync.PROC',1)
    sleep(1)
    caput('29idKappa:Kappa_sync.PROC',1)
    print('Euler motors VAL/RBV synced to physical motors')



def Home_SmarAct_Motor():
    '''Home the piezo (x,y,z). Home position is middle of travel.'''
    for i in [2,3,4]:
        VAL='29idKappa:m'+str(i)+'.HOMF'
        caput(VAL,1)
        sleep(10)
    print('SamrAct motors VAL homed')

def input_d(question):
    """
    ask a question (e.g 'Are you sure you want to reset tth0 (Y or N)? >')
    return the answer
    """
    try:
        print(question)
        foo = input()
        return foo
    except KeyboardInterrupt as e:
        raise e
    except:
        return


def tth0_set():
    current_det=caget('29idKappa:userStringSeq6.STR1',as_string=True)
    if current_det != 'd4':
        print('tth0 can only be redefined with d4')
    else:
        foo=input_d('Are you sure you want to reset tth0 (Y or N)? >')
        if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
            caput('29idKappa:m9.SET','Set')
            sleep(0.5)
            caput('29idKappa:m9.VAL',0)
            sleep(0.5)
            caput('29idKappa:m9.SET','Use')
            print("tth position reset to 0")
        else:
            print("That's ok, everybody can get cold feet in tough situation...")

def Scan_ARPES_Go(scanIOC='ARPES',scanDIM=1,**kwargs):
    """Starts the N dimension scan in the ARPES chamber (N=ScanDIM)
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs) 
    
def ARPES_scanDIM():
    """
    sets the default scanDIM for ARPES (not 1 due to sweeps)
    """
    scanDIM=1
    return scanDIM


def Scan_ARPES_Motor_Go(name,start,stop,step,mode="absolute",**kwargs):
    """
    Fills in the Scan Record and the presses the go button
    if scanIOC=None then uses BL_ioc()
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details      
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())

    Scan_ARPES_Motor(name,start,stop,step,mode,**kwargs)
    Scan_ARPES_Go(kwargs["scanIOC"],kwargs["scanDIM"])

def Scan_ARPES_Motor(name,start,stop,step,mode="absolute",**kwargs):  # FR added **kwargs in the args 06/14/21
    """
    Fills in the Scan Record does NOT press Go
    if scanIOC=None then uses BL_ioc()
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())
    kwargs.setdefault("settling_time",0.1)
    
    m_RBV=ARPES_PVmotor(name)[0]
    m_VAL=ARPES_PVmotor(name)[1]
    if mode == "relative":
        current_value=caget(m_RBV)
        abs_start=round(current_value+start,3)
        abs_stop =round(current_value+stop,3)
        print("start, stop, step = "+str(abs_start)+", "+str(abs_stop)+", "+str(step))
    else:
        abs_start=start
        abs_stop =stop
    caput("29id"+kwargs["scanIOC"]+":scan1.PDLY",kwargs["settling_time"])
    Scan_FillIn(m_VAL,m_RBV,kwargs["scanIOC"],kwargs["scanDIM"],abs_start,abs_stop,step)
    

def scanz(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        Scan_ARPES_Motor_Go("z",start,stop,step,mode=mode,**kwargs)
    elif mybranch == "d":
        Scan_Kappa_Motor_Go("z",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    #elif mybranch == "e":
    #    Scan_RSoXS_Motor_Go("z",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        

def dscanz(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanz'''
    scanz(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)
def scanx(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        Scan_ARPES_Motor_Go("x",start,stop,step,mode=mode,**kwargs)
    elif mybranch == "d":
        Scan_Kappa_Motor_Go("x",start,stop,step,mode=mode,**kwargs)
    #elif mybranch == "e":
    #    Scan_RSoXS_Motor_Go("x",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
def dscanx(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanx'''
    scanx(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)


def scanth(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        Scan_ARPES_Motor_Go("th",start,stop,step,mode=mode,**kwargs)        
    elif mybranch == "d":
        print("Scanning pseudo motor 29idKappa:Euler_Theta")
        Scan_Kappa_Motor_Go("th",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs) 
    #elif mybranch == "e":
    #    Scan_RSoXS_Motor_Go("th",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        

def dscanth(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanth'''
    scanth(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def scany(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        Scan_ARPES_Motor_Go("y",start,stop,step,mode=mode,**kwargs)
    elif mybranch == "d":
        Scan_Kappa_Motor_Go("y",start,stop,step,mode=mode,**kwargs)
    #elif mybranch == "e":
    #    Scan_RSoXS_Motor_Go("y",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)

def dscany(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scany'''
    scany(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def scanchi(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        print("chi motor scan not implemented")
    elif mybranch == "d":
        Scan_Kappa_Motor_Go("chi",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    elif mybranch =="e":
        print("chi motor scan not implemented")

def dscanchi(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanchi'''
    scanchi(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def scanphi(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        print("phi motor scan not implemented")
    elif mybranch == "d":
        Scan_Kappa_Motor_Go("phi",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    elif mybranch =="e":
        print("phi motor scan not implemented")
          
def dscanphi(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanphi'''
    scanphi(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)
 
def mvz(val):
    """ Moves z motor in the endstation specified by CheckBranch()
    """
    name="z"
    Move_Motor_vs_Branch(name,val)
def mvy(val):
    """ Moves y motor in the endstation specified by CheckBranch()
    """
    name="y"
    Move_Motor_vs_Branch(name,val)


def mvth(val):
    """ Moves phi motor in the endstation specified by CheckBranch()
    Kappa th is a four-circle pseudomotor, kth is an actual motor
    """
    name="th"
#    mybranch=CheckBranch()
#    if mybranch == "d":
#        print("   th motor does not exit")
    #elif branch == "d":
#    else:
    Move_Motor_vs_Branch(name,val)

def uan(tth,th):
    """ Moves tth and th motors simultaneously in the in the Kappa chamber
    """
    caput(Kappa_PVmotor("tth")[1],tth)
    caput(Kappa_PVmotor("th")[1],th)
    while True:
        MotorBusy=caget("29idKappa:alldone.VAL",as_string=True)
        if MotorBusy!='done':
    #        print "No beam current, please wait..."+dateandtime()
            sleep(0.1)
        else:
            print('tth='+str(tth)+' th='+str(th))
            break

def mvrchi(val):
    """
    Relative move
    """
    name="chi"
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        print("   chi motor not implemented")
    #elif branch == "d":
    else :
        UMove_Motor_vs_Branch(name,val)

def mvrchi(val):
    """
    Relative move
    """
    name="chi"
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        print("   chi motor not implemented")
    #elif branch == "d":
    else :
        UMove_Motor_vs_Branch(name,val)

def mvrphi(val):
    """
    Relative move
    """
    name="phi"
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        print("   phi motor not implemented")
    #elif branch == "d":
    else :
        UMove_Motor_vs_Branch(name,val)
def mvkrth(val):
    """
    Relative move
    """
    name="kth"
    mybranch=CheckBranch()
    if mybranch == "d":
        UMove_Motor_vs_Branch(name,val)
    else:
        print("   kth motor does not exit")

def mvrx(val):
    """
    Relative move
    """
    name="x"
    UMove_Motor_vs_Branch(name,val)
def mvry(val):
    """
    Relative move
    """
    name="y"
    UMove_Motor_vs_Branch(name,val)
def mvrz(val):
    """
    Relative move
    """
    name="z"
    UMove_Motor_vs_Branch(name,val)

def mvrkphi(val):
    """
    Relative move
    """
    name="kphi"
    mybranch=CheckBranch()
    if mybranch == "d":
        UMove_Motor_vs_Branch(name,val)
    else:
        print("   kphi motor does not exit")

def scankap(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "d":
        Scan_Kappa_Motor_Go("kap",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    else:
        print("kap motor does not exit")


def sample(ListPosition):
    """
    ARPES: ListPosition = ["Sample Name", x, y, z, th, chi, phi]
    Kappa: ListPosition = ["Sample Name", x, y, z, tth, kth, kap, kphi]; tth does not move
    RSoXS: ListPosition=["Sample Name",x,y,z,chi,phi,th,tth]
    """
    mybranch=CheckBranch()
    if mybranch == "c":
        Move_ARPES_Sample(ListPosition)
    elif mybranch == "d":
        Move_Kappa_Sample(ListPosition)
        print("tth is kept fixed.")
    elif mybranch =="e":
        Move_RSoXS_Sample(ListPosition)

def Move_ARPES_Sample(ListPosition):
    """ListPosition = ["Sample Name", x, y, z, th, chi, phi]"""
    if not isinstance(ListPosition[0],str):
        ListPosition.insert(0,"")
    name,x,y,z,th,chi,phi=ListPosition
    print("\nx="+str(x), " y="+str(y)," z="+str(z), " theta="+str(th)," chi="+str(chi)," phi="+str(phi),"\n")
    Move_ARPES_Motor("x",x)
    Move_ARPES_Motor("y",y)
    Move_ARPES_Motor("z",z)
    Move_ARPES_Motor("th",th)
    Move_ARPES_Motor("chi",chi)
    Move_ARPES_Motor("phi",phi)
    #print "Sample now @:",name

def Move_Kappa_Sample(ListPosition):
    """ListPosition = ["Sample Name", x, y, z, tth, kth, kap, kphi]
    keeps tth fixes
     """
    if not isinstance(ListPosition[0],str):
        ListPosition.insert(0,"")
    #tth=round(caget("29idHydra:m1.RBV"),2)
    name,x,y,z,tth,kth,kap,kphi=ListPosition
    print("\nx="+str(x), " y="+str(y)," z="+str(z), " tth="+str(tth), " kth="+str(kth), " kap="+str(kap), " kphi="+str(kphi),"\n")
    caput("29idKappa:m2.VAL",x,wait=True,timeout=18000)
    caput("29idKappa:m3.VAL",y,wait=True,timeout=18000)
    caput("29idKappa:m4.VAL",z,wait=True,timeout=18000)
    caput("29idKappa:m8.VAL",kth,wait=True,timeout=18000)
    caput("29idKappa:m7.VAL",kap,wait=True,timeout=18000)
    caput("29idKappa:m1.VAL",kphi,wait=True,timeout=18000)
    print("Sample now @:",name)

def Move_RSoXS_Sample(ListPosition):
    """
    ListPosition=["Sample Name",x,y,z,chi,phi,th,tth]
    """
    if not isinstance(ListPosition[0],str):
        ListPosition.insert(0,"")
    name,x,y,z,chi,phi,th,tth=ListPosition
    print("\nx="+str(x), " y="+str(y)," z="+str(z), " chi="+str(chi), " phi="+str(phi), " th="+str(th), " tth="+str(tth),"\n")
    #Moving x/y to center of travel move tth then th
    caput("29idRSoXS:m1.VAL",0,wait=True,timeout=18000)
    caput("29idRSoXS:m2.VAL",10,wait=True,timeout=18000)
    caput("29idRSoXS:m8.VAL",tth,wait=True,timeout=18000)
    caput("29idRSoXS:m7.VAL",th,wait=True,timeout=18000)
    #Moving the rest
    caput("29idRSoXS:m3.VAL",z,wait=True,timeout=18000)
    caput("29idRSoXS:m4.VAL",chi,wait=True,timeout=18000)
    caput("29idRSoXS:m5.VAL",phi,wait=True,timeout=18000)
    caput("29idRSoXS:m1.VAL",x,wait=True,timeout=18000)
    caput("29idRSoXS:m2.VAL",y,wait=True,timeout=18000)

def scanth2th(tth_start,tth_stop,tth_step,th_offset,ct,**kwargs):
    """
    Used for a linear (not table) scan where th =  tth /2 + th_offset
    **kwargs
        run = True (default) starts the scan; false just fills in the scanRecord
        scanIOC = BL_ioc (default)
        scanDIM = 1 (default)
        settling_time = 0.1 (default)
    """
    
    #scanIOC=BL_ioc()
    kwargs.setdefault('run',True)
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    kwargs.setdefault("settling_time",0.1)
    
    scanIOC=kwargs['scanIOC']
    scanDIM=kwargs['scanDIM']
    settling_time=kwargs['settling_time']
    
    th_start=(tth_start)/2+th_offset
    th_stop=(tth_stop)/2+th_offset
    
    print('tth: '+str(tth_start)+"/"+str(tth_stop)+"/"+str(tth_step))
    print('th: '+str(th_start)+"/"+str(th_stop)+"/"+str(tth_step/2.0))
    
    #write to the scanRecord
    scanPV="29id"+scanIOC+":scan"+str(scanDIM)
    caput(scanPV+".PDLY",settling_time)
    Scan_FillIn(Kappa_PVmotor("tth")[1],Kappa_PVmotor("tth")[0],scanIOC,scanDIM,tth_start,tth_stop,tth_step)
    Scan_FillIn_Pos2(Kappa_PVmotor("th")[1],Kappa_PVmotor("th")[0],scanIOC,scanDIM,th_start,th_stop)
    
  
    if kwargs['run']==True:
        cts(ct)
        Scan_Go(scanIOC,scanDIM)
        
        #Setting everything back
        caput(scanPV+".PDLY",0.1)

        # Need to clear positionner!
        Clear_Scan_Positioners(scanIOC)


def Clear_Scan_Positioners(scanIOC,scanDIM=1):
    """Clear all extra scan positioners"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    for i in range (1,5):
        caput(pv+".R"+str(i)+"PV","")
        caput(pv+".P"+str(i)+"PV","")
    print("\nAll extra positionners cleared")
