from epics import caput,caget,PV
from time import sleep
from .utils.exp import BL_ioc, CheckBranch, BL_Mode_Read
from .utils.log import scanlog
from .utils.misc import dateandtime


def Reset_Scan(scanIOC,scanDIM=1,**kwargs):
    """
    Reset scan record; the current IOC is defined by BL_ioc() (i.e. mirror position).
    kwargs:
        scaler='y', for Kappa IOC only, ARPES ignors this keyword
        detTrig=2, for ARPES/Kappa IOC, used to clear SES/MPA trigger
        
    """

    kwargs.setdefault("scaler",'y')
    scaler=kwargs['scaler']
    
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    print("\nResetting "+pv)
    #Clear Scan Settings
    Reset_Scan_Settings(scanIOC,scanDIM)    # Reset scan settings to default: ABSOLUTE, STAY, 0.05/0.1 positioner/detector settling time
    #Setting Detectors
    Detector_Default(scanIOC,scanDIM)
    #Clearing the Detector Triggers
    Clear_Scan_Triggers(scanIOC,scanDIM)
    
    if scanIOC == 'ARPES':
        caput(pv+".T1PV",Detector_Triggers_StrSeq(scanIOC))
        print("\nDetector triggered:", Detector_List(scanIOC))
        
    if scanIOC == 'Kappa':
        caput('29idKappa:UBmatrix',[0,0,0,0,0,0,0,0,0])
        caput('29idKappa:UBsample','')
        caput('29idKappa:UBlattice',[0,0,0,0,0,0])
        caput('29idKappa:UBenergy',0)
        caput('29idKappa:UBlambda',0)
        if scaler == 'y':
            caput(pv+".T1PV",'29idMZ0:scaler1.CNT')
            caput('29idMZ0:scaler1.TP',0.1)
            print('Kappa scalers are triggered. Counting time set to 0.1s')
            #Reset_CA_all(); Reset_MonoMPA_ROI_Trigger()
        else:
            caput(pv+".T1PV",Detector_Triggers_StrSeq(scanIOC))
            print('Kappa scalers are NOT triggered. Using Current Amplifiers (CA)')
            print("\nDetector triggered:", Detector_List(scanIOC))
#     if scanIOC=='Kappa' and scaler is not None:
#         print('\nDo you want to use the scalers as detector trigger? (Note to self: to be modified  (FR))>')
#         foo = input()
#         if foo in ['yes','y','Y','YES']:
#             caput(pv+".T1PV",'29idMZ0:scaler1.CNT')
#             caput('29idMZ0:scaler1.TP',0.1)
#             print('Scalers added as trigger 2')
#             print('Counting time set to 0.1s')
#     else:
#         print('\nScalers not triggered. To trigger use: \n\n       Reset_Scan(\'Kappa\',scaler=\'y\')')
    caput(pv+".BSPV",BeforeScan_StrSeq(scanIOC))
    caput(pv+".ASPV",AfterScan_StrSeq(scanIOC,scanDIM))
    caput(pv+".BSCD",1)
    caput(pv+".BSWAIT","Wait")
    caput(pv+".ASCD",1)
    caput(pv+".ASWAIT","Wait")
    #SaveData
    caput("29id"+scanIOC+":saveData_realTime1D",1)
    #Check that detector and positioner PVs are good
    sleep(10)
    Scan_Check(scanIOC,scanDIM)

### Reset detectors in scan record:
def Scan_Check(scanIOC,scanDIM=1):
    """
    Check if any of the detectors or positions are not connected
    """
    print('Checking if all detectors & positioners are connected...')
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    #Detectors
    for i in range(1,71):
        num=(str(i).zfill(2))
        pvd=caget(pv+".D"+num+"PV")
        if pvd !='': 
            det=PV(pvd); sleep(0.1) #smallest sleep to allow for PV traffic
            if not det.connected:
                print("Detector "+num+" has a bad PV:  "+det.pvname+" not connected")
    #Positioners
    for i in range(1,5):
        num=str(i)
        pvp=caget(pv+".P"+num+"PV")
        if pvp != '': 
            pos=PV(pvp)
            if not pos.connected:
                print("Positioner "+num+" has a BAD PV:  "+pos.pvname+" not connected")


        
def scantth(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "c":
        print("tth motor does not exit")
    elif mybranch == "d":
        Scan_Kappa_Motor_Go("tth",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    #elif mybranch =="e":
    #    Scan_RSoXS_Motor_Go("tth",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)     


def Scan_Kappa_Motor_Go(name,start,stop,step,mode="absolute",settling_time=0.1,scanIOC=None,scanDIM=1,**kwargs):
    """
    Fills in the Scan Record and presses the go button
    if scanIOC=None then uses BL_ioc()
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details      
    default: scanDIM=1  

    """
    if scanIOC is None:
        scanIOC="Kappa"
    Scan_Kappa_Motor(name,start,stop,step,mode,settling_time)
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)

def Scan_Kappa_Motor(name,start,stop,step,mode="absolute",settling_time=0.1,scanIOC=None,scanDIM=1):
    """
    Fills in the Scan Record does NOT press Go
    if scanIOC=None then uses BL_ioc()
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    m_RBV=Kappa_PVmotor(name)[0]
    m_VAL=Kappa_PVmotor(name)[1]
    if mode == "relative":
        current_value=caget(m_RBV)
        abs_start=round(current_value+start,3)
        abs_stop =round(current_value+stop,3)
    else:
        abs_start=start
        abs_stop =stop
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)
    Scan_FillIn(m_VAL,m_RBV,scanIOC,scanDIM,abs_start,abs_stop,step)


### Start Scan:
def Scan_Go(scanIOC,scanDIM=1,**kwargs):
    """Starts a scan for a given IOC scanIOC=("ARPES","Kappa","RSoXS") and diension scanDIM
    by default: scanDIM=1  
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
#    try:
    Scan_Progress(scanIOC,scanDIM)
    BL_mode=BL_Mode_Read()[0]
    if not(BL_mode==2 or BL_mode==4):
        Check_MainShutter()
    Before_After_Scan(scanIOC,scanDIM)
    for i in range(1,scanDIM+1):
        drive = caget("29id"+scanIOC+":scan"+str(i)+".P1PV")
        start = caget("29id"+scanIOC+":scan"+str(i)+".P1SP")
        stop  = caget("29id"+scanIOC+":scan"+str(i)+".P1EP")
        step  = caget("29id"+scanIOC+":scan"+str(i)+".P1SI")
        print('Scan'+str(i)+': '+drive+'= '+str(start)+' / '+str(stop)+' / '+str(step))
    FileName = caget("29id"+scanIOC+":saveData_baseName",as_string=True)
    FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")
    print(FileName+str(FileNum)+" started at ", dateandtime())
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".EXSC",1,wait=True,timeout=900000)  #pushes scan button
    print(FileName+str(FileNum)+" finished at ", dateandtime())
    print('\n')
    scanlog(**kwargs)

### Fill Scan Record - 1st positionner:
def Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step,point=None):
    Scan_Progress(scanIOC,scanDIM)
    #print "Scan {:d} - {:s} : {:0.3f} / {:0.3f} / {:0.3f}".format(scanDIM,VAL,start,stop,step)
    #print "Scan "+str(scanDIM),VAL+" : "+str(start)+"/"+str(stop)+"/"+str(step)+"\n"
    start=start*1.0
    stop=stop*1.0
    step=step*1.0
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    caput(pv+".P1SM","LINEAR") 
    caput(pv+".P1PV",VAL)
    caput(pv+".R1PV",RBV)
    caput(pv+".P1SP",start)
    caput(pv+".P1EP",stop)
    if point is None:
        caput(pv+".P1SI",step)
    else:
        caput(pv+".NPTS",step)

### Check & Wait while scan is in progress:
def Scan_Progress(scanIOC,scanDIM=1,q=None):
    """Checks if a scan is in progress, and sleeps until it is done"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    check=caget(pv+".FAZE")
    while (check!=0):
        if q == None:
            print(pv+" in progress - please wait...")
        sleep(30)
        check=caget(pv+".FAZE")