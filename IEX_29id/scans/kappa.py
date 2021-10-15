from time import sleep
from epics import caget, caput

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
        
def scankap(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "d":
        Scan_Kappa_Motor_Go("kap",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    else:
        print("kap motor does not exit")

def dscanphi(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanphi'''
    scanphi(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

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


def kth0_set(value):
    foo=prompt('Are you sure you want to reset kth0 (Y or N)? >')
    if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
        foo=prompt('Are you aligning at theta 0 or 180 (0 or 180)? >')
        if foo == '180':
            new_value=round(value-180,3)-56.06
            print(str(value)+' - 180 = '+str(new_value))
        elif foo == '0':
            new_value=value
        else:
            print('Not a valid answer')
        caput('29idKappa:userCalcOut1.G',new_value)
        print("\nkth0 position set to",new_value)
        print('which now corresponds to theta=0 @ chi=90')
    else:
        print("That's ok, keep going, you are doing great!")