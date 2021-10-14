from epics import caput,caget,PV, EA
from time import sleep
from IEX_29id.utils.exp import BL_ioc, CheckBranch, BL_Mode_Read, Check_MainShutter
from IEX_29id.utils.log import scanlog
from IEX_29id.utils.misc import dateandtime
from IEX_29id.devices.detectors import Detector_List
from IEX_29id.utils.strings import ClearStringSeq
from IEX_29id.devices.motors import Kappa_PVmotor
from math import *
import numpy as np
import numpy.polynomial.polynomial as poly




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

def Reset_Scan_Settings(scanIOC,scanDIM=1):
    """
    Reset scan settings to default: ABSOLUTE, STAY, 0.05/0.1 positioner/detector settling time
    """
    Cam_ScanClear(scanIOC,scanDIM)
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    innerScan="29id"+scanIOC+":scan"+str(scanDIM-1)+".EXSC"
    caput(pv+".CMND",3)        # Clear all Positionners
    caput(pv+".P1AR",0)        # Absolute position
    caput(pv+".PASM","PRIOR POS")    # After scan: prior position
    caput(pv+".PDLY",0.05)     # Positioner Settling time
    caput(pv+".DDLY",0.1)         # Detector Settling time
    if scanDIM > 1:    #Resets the higher dimensional scans to trigger the inner scan
        caput(pv+".T1PV",innerScan)
    print("Scan record reset to default.")



### Reset detectors in scan record:
def Detector_Triggers_StrSeq(scanIOC,scalerOnly=None):    # do we need to add 29idb:ca5 ???
    n=8
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    ClearStringSeq(scanIOC,n)
    caput(pvstr+".DESC","Triggers_"+scanIOC)
    branch=CheckBranch()
    n=len(Detector_List(scanIOC))
    for (i,list) in enumerate(Detector_List(scanIOC)):
        pvCA='29id'+list[0]+':ca'+str(list[1])+':read.PROC CA NMS'
        caput(pvstr+".LNK" +str(i+1),pvCA)
        caput(pvstr+".WAIT"+str(i+1),"After"+str(n))
    return pvstr+".PROC"


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

def Detector_Default(scanIOC,scanDIM=1,BL_mode=None):
    """
    Sets the ScanRecord detectors
    """
    Note_endstation = "Detectors are set for "+scanIOC+","
    Note_xrays="with X-rays"
    if BL_mode==None:
        BL_mode=BL_Mode_Read()[0]        # possible to overwrite (e.g. set up time scan to monitor all PVs)
    #Endstation parameters
    if scanIOC == "ARPES":
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D17PV","29idARPES:LS335:TC1:IN1")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D18PV","29idARPES:LS335:TC1:IN2")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D14PV","29idc:ca2:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D16PV","29idc:ca1:read")
        if caget(EA._statsPlugin+"Total_RBV") != None:
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D17PV",EA._statsPlugin+"Total_RBV")
        else:
            print(EA.PHV+" is not running")
        
    elif scanIOC == "Kappa":
        # D14  D5D - mesh
        # D15  D5C - gas cell
        # D16  free        
        # D17  free
        # D18  free        
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D19PV","29idd:ca2:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D20PV","29idd:ca3:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D21PV","29idd:ca4:read")
        #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D22PV","29idd:ca5:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D23PV","29idd:LS331:TC1:SampleA")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D24PV","29idd:LS331:TC1:SampleB")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D25PV","29id_ps6:Stats1:CentroidX_RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D26PV","29id_ps6:Stats1:SigmaX_RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D27PV","29id_ps6:Stats1:CentroidTotal_RBV")
        # D28  free
        # D29  free
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D30PV","29iddMPA:det1:TotalRate_RBV") # MPA software count rate?
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D31PV","29idMZ0:scaler1.S14") #-mesh D
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D32PV","29idMZ0:scaler1.S2") # TEY
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D33PV","29idMZ0:scaler1.S3") # D3
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D34PV","29idMZ0:scaler1.S4") # D4
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D35PV","29idMZ0:scaler1.S5") # MCP
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D36PV","29idMZ0:scaler1_calc1.B") #TEY/mesh
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D37PV","29idMZ0:scaler1_calc1.C") #D3/mesh
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D38PV","29idMZ0:scaler1_calc1.D") #D4/mesh
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D39PV","29idMZ0:scaler1_calc1.E") #MCP/mesh
        # D40 free
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D41PV","29iddMPA:Stats1:Total_RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D42PV","29iddMPA:Stats2:Total_RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D43PV","29iddMPA:Stats3:Total_RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D44PV","29iddMPA:Stats4:Total_RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D45PV","29iddMPA:Stats5:Total_RBV")
        # D46  <H>
        # D47  <K>        
        # D48  <L>        
        # D49  free
        # D50  free            
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D51PV","29idKappa:m8.RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D52PV","29idKappa:m7.RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D53PV","29idKappa:m1.RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D54PV","29idKappa:m9.RBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D55PV","29idKappa:Euler_ThetaRBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D56PV","29idKappa:Euler_ChiRBV")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D57PV","29idKappa:Euler_PhiRBV")
    elif scanIOC == "RSoXS":#JM need to get another keithly for RSoXS -BS+Diode
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D19PV","29idd:ca2:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D20PV","29idd:ca3:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D21PV","29idd:ca4:read")
        #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D22PV","29idd:ca5:read")
    #Beamline parameters
    if BL_mode < 2:     # (User or staff) + Xrays"
        #Setting Detectors -- main shutter & ring current
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D01PV","S:SRcurrentAI.VAL")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D02PV","EPS:29:ID:SS1:POSITION")
        #Setting Detectors -- Beamline Energy
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D03PV","29idmono:ENERGY_MON")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D04PV","ID29:EnergySet.VAL")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D05PV","ID29:Energy.VAL")
        #Setting Detectors -- Keithleys
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D06PV","29idb:ca1:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D07PV","29idb:ca2:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D08PV","29idb:ca3:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D09PV","29idb:ca4:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D10PV","29idb:ca5:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D11PV","29idb:ca9:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D11PV","29idb:ca10:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D12PV","29idb:ca12:read")
        caput("29id"+scanIOC+":scan"+str(scanDIM)+".D13PV","29idb:ca13:read")
        #Setting Detectors -- Meshes/Diodes
        if scanIOC == "ARPES":
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D15PV","29idb:ca15:read")
        elif scanIOC == "Kappa":
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D14PV","29idb:ca14:read")
        elif scanIOC == "RSoXS":
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D14PV","29idb:ca14:read")
        Note_user="and in Users mode"
        if BL_mode==1: # "Staff + Xrays"
            # C/D diodes:
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D14PV","29idb:ca14:read")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D15PV","29idb:ca15:read")
            #Setting Detectors -- beamline vacuum and shutters
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D61PV","29idb:VS1A.VAL")   
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D62PV","29idb:VS2A.VAL")
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D63PV","29idb:VS3AB.VAL")
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D64PV","29idb:VS4B.VAL")
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D65PV","29idb:IP4B.VAL")
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D66PV","PA:29ID:SCS_BLOCKING_BEAM.VAL")
            #caput("29id"+scanIOC+":scan"+str(scanDIM)+".D67PV","PA:29ID:SDS_BLOCKING_BEAM.VAL")
            #Setting Detectors -- Slits & Apertures
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D58PV","29idb:Slit1Ht2.C")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D59PV","29idb:Slit1Ht2.D")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D60PV","29idb:Slit1Vt2.C")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D61PV","29idb:Slit1Vt2.D")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D62PV","29idb:Slit2Ht2.C")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D63PV","29idb:Slit2Ht2.D")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D64PV","29idb:Slit2Vt2.C")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D65PV","29idb:Slit2Vt2.D")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D66PV","29idb:Slit3CRBV")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D67PV","29idb:Slit4Vt2.C")
            #Setting Detectors -- Mono details
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D68PV","29idmono:ENERGY_SP")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D69PV","29idmonoMIR:P.RBV")
            caput("29id"+scanIOC+":scan"+str(scanDIM)+".D70PV","29idmonoGRT:P.RBV")

            Note_user=" and in Staff mode"
    else:
        Note_user=""
        Note_xrays="no Xrays"
    print("\nWARNING: %s %s %s" % (Note_endstation, Note_xrays, Note_user))


def Clear_Scan_Triggers(scanIOC,scanDIM=1):
    """Clear all scan detectors triggers"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    for i in range(1,5):
        caput(pv+'.T'+str(i)+'PV',"")

def Scan_FillIn_Pos3(VAL,RBV,scanIOC,scanDIM,start,stop):
    Scan_Progress(scanIOC,scanDIM)
    start=start*1.0
    stop=stop*1.0
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    caput(pv+".P1SM","LINEAR")     
    caput(pv+".P3PV",VAL)
    caput(pv+".R3PV",RBV)
    caput(pv+".P3SP",start)
    caput(pv+".P3EP",stop)

def Scan_FillIn_Table(VAL,RBV,scanIOC,scanDIM,myarray,posNum=1):
    """
    Fills in the scan record for table scans given positioner=posNum
    myarray can be generated by myarray=Scan_MakeTable(StartStopStepLists)
    """
    Scan_Progress(scanIOC,scanDIM)
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    #positioner detting
    caput(pv+".P"+str(posNum)+"SM","TABLE") 
    caput(pv+".P"+str(posNum)+"PV",VAL)         #Drive
    caput(pv+".R"+str(posNum)+"PV",RBV)         #Read
    #caput(pv+".P"+str(posNum)+"SP",myarray[0])  #Start
    #caput(pv+".P"+str(posNum)+"EP",myarray[-1]) #Stop    
    #caput(pv+".P"+str(posNum)+"SI",0)           #Step     
    caput(pv+".P"+str(posNum)+"PA",myarray)
    caput(pv+'.NPTS',len(myarray))    
    
def Scan_FillIn_Pos2(VAL,RBV,scanIOC,scanDIM,start,stop):
    Scan_Progress(scanIOC,scanDIM)
    start=start*1.0
    stop=stop*1.0
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    caput(pv+".P1SM","LINEAR")     
    caput(pv+".P2PV",VAL)
    caput(pv+".R2PV",RBV)
    caput(pv+".P2SP",start)
    caput(pv+".P2EP",stop)



def BeforeScan_StrSeq(scanIOC):        # Put All relevant (triggered) CA in passive mode
    n=9
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    ClearStringSeq(scanIOC,n)
    caput(pvstr+".DESC","BeforeScan_"+scanIOC)
    for (i,list) in enumerate(Detector_List(scanIOC)):
        pvCA='29id'+list[0]+':ca'+str(list[1])+':read.SCAN PP NMS'
        caput(pvstr+".LNK" +str(i+1),pvCA)
        caput(pvstr+".STR" +str(i+1),"Passive")
    return pvstr+".PROC"


def AfterScan_StrSeq(scanIOC,scanDIM=1,Snake=None):
    n=10
    pvstr ="29id"+scanIOC+":userStringSeq"+str(n)
    pvscan="29id"+scanIOC+":scan"+str(scanDIM)
    
    SnakePV="29id"+scanIOC+":userCalcOut"+str(1) #Snake UserCal
        
    ClearStringSeq(scanIOC,n)
    caput(pvstr+".DESC","AfterScan_"+scanIOC)
    ## Put All relevant CA back in live mode29idARPES:userStringSeq10.LNK8
    caput(pvstr+".LNK1",CA_Live_StrSeq(scanIOC)+" PP NMS")
    caput(pvstr+".DO1",1)
    ## Put scan record back in absolute mode
    caput(pvstr+".LNK2",pvscan+".P1AR")
    caput(pvstr+".STR2","ABSOLUTE")
    ## Put Positionner Settling time to 0.1s
    caput(pvstr+".LNK3",pvscan+".PDLY NPP NMS")
    caput(pvstr+".DO3",0.1)
    ## Clear DetTriggers 2 to 4:
    #caput(pvstr+".LNK4",pvscan+".T2PV NPP NMS")    # FR is testing - why remove all trigger after scan?
    caput(pvstr+".LNK5",pvscan+".T3PV NPP NMS")
    caput(pvstr+".LNK6",pvscan+".T4PV NPP NMS")
    if scanIOC == 'Kappa':
        caput(pvstr+".STR4","")
    #    caput(pvstr+".STR4","29idMZ0:scaler1.CNT")   # to be fixed FR 2020/10/27
    else:
        caput(pvstr+".STR4","")
    caput(pvstr+".STR5","")
    caput(pvstr+".STR6","")
    caput(pvstr+".LNK7",pvscan+".PASM")
    caput(pvstr+".STR7","PRIOR POS")
    #if Snake is not None:
    #    ## Put scan record back in 'STAY POS'

#        caput(pvstr+".LNK8",SnakePV+".PROC")
#        caput(pvstr+".D8",1)
#    #caput(pvstr+"")JM was here
#    else:
#        ## Put scan record back in 'PRIOR POS'
#        caput(pvstr+".LNK7",SnakePV+".PROC PP NMS")
#        caput(pvstr+".DO1",1)
    return pvstr+".PROC"






def Before_After_Scan(scanIOC,scanDIM):
    """
    Clear all Before/After scan (1,2,3,4).
    Proc Before/AfterScan StrSeq  for the most outer loop:
        - before scan puts all relevant detectors in passive
        - after scan puts back all relevant detector in Live and reset scan1 to default settings.
    """
    All_Scans=[1,2,3,4]
    All_Scans.remove(scanDIM)
    #Clearing all Before/Afters
    for i in All_Scans:
        caput("29id"+scanIOC+":scan"+str(i)+".BSPV","")
        caput("29id"+scanIOC+":scan"+str(i)+".ASPV","")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".BSPV",BeforeScan_StrSeq(scanIOC))
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".BSCD",1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".BSWAIT","Wait")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".ASPV",AfterScan_StrSeq(scanIOC))
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".ASCD",1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".ASWAIT","Wait")



def Clear_Scan_Positioners(scanIOC,scanDIM=1):
    """Clear all extra scan positioners"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    for i in range (1,5):
        caput(pv+".R"+str(i)+"PV","")
        caput(pv+".P"+str(i)+"PV","")
    print("\nAll extra positionners cleared")


