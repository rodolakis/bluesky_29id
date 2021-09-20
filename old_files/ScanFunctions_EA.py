#############################################################
###################### Imports ##############################
#############################################################
from epics import *
import numpy as np
from os.path import join, isfile, exists
from os.path import dirname
from operator import itemgetter
from scipy.interpolate import interp1d
import time

#from EA_29idcEA import*
from EA_29idcScienta import*

from ScanFunctions_IEX import *

#############################################################################
pv=PV("29idcScienta:HV:KineticEnergy.VAL") 
sleep(0.1) #need sleep  to use .connected without python moves too fast
global EA
if pv.connected:
    EA=Scienta()
else:
    print("\n\n NOTE: Scienta IOC is not running - start IOC and %run Macros_29id/ScanFunctions_EA.py\n\n")
#############################################################################
def _29idcScientaIOC_init(**kwargs):
    """
    run after restarting the 29idcScienta IOC
    kwargs:
        Close_CShutter="Close" default, if something else then it doesn't close the shutter
    """
    kwargs.setdefault("Close_CShutter",True)
    if kwargs['Close_CShutter']:
        Close_CShutter()
    #Addding HDF5 atttributes
    filepath='/xorApps/epics/synApps_6_1/ioc/29idcScienta/iocBoot/ioc29idcScienta/HDF5Attributes.xml'
    EA._updateAttributes(filepath)
    #Enabling User CalcOut, needed for BE 
    caput("29idcScienta:userCalcOutEnable.VAL","Enable")
    #clipping and other processing
    caput("29idcScienta:Proc1:EnableLowClip","Enable")
    caput("29idcScienta:Proc1:LowClip",1)
    caput("29idcScienta:Proc1:EnableHighClip",'Disable')

    caput("29idcScienta:Proc1:Scale",100)
    caput("29idcScienta:Proc1:Offset",-1)
    ### Add here
    #Setting ExpFrames
    caput("29idcScienta:ExpFrames.VAL",1)
    #setting save default lens values
    EA._AcquisitionMode('Spectra')
    sleep(0.25)
    KE=getE()
    EA.put(KE, PE=50, LensMode="Angular")
    caput(EA.PHV+"KineticEnergy:TWV.VAL",1)
    caput(EA._Pcam+"Acquire","Acquire")
    
    print("C-Shutter is closed for initialization ")

def getSESslit():
    SES=caget("29idc:m8.RBV")
    return SES

def Folder_EA(userPath,filePrefix="EA",**kwargs):
    """
    For Staff: folder='b', userName='Staff'
    For ARPES: folder ='c'

    setFolders = True; creates the data folder and sets scanRecords/AreaDetectors 
               = False: only creates the data folders; does NOT set 
    """
    kwargs.setdefault('create_only',False)
    
    ADplugin=EA._savePlugin 
    dtype=EA.dtype  
    if dtype == "nc":
        df="netCDF"
    else:
        df=EA.dtype  

    fpath=join(userPath,df)
    print("\nFolder: " + fpath)

    if exists(fpath):
        print("exists")
        fileNumber=getNextFileNumber(fpath,filePrefix, debug=False)
    else:
        print("making")
        mkdir(fpath)
        fileNumber=1
    
    if kwargs['create_only']==False:
        caput(ADplugin+"FilePath",fpath)
        caput(ADplugin+"FileName",filePrefix)
        caput(ADplugin+"FileNumber",fileNumber)

        #setup AD
        caput(ADplugin+"FileTemplate","%s%s_%4.4d."+dtype)
        caput(ADplugin+"AutoIncrement","Yes")
        caput(ADplugin+"AutoSave","Yes")
        
    print("EA path: "+fpath)    
    print("Next "+filePrefix+" file: "+str(fileNumber))  
    
    
def log_EA(**kwargs):
    """
        Writes CSV file for the MDA scans with the following default parameters:
        
    FilePath='/home/beams/29IDUSER/Documents/User_Folders/UserName/'
    Filename is set by logname_set(FileName=None), default:YYYYMMDD_log.txt, where YYYYMMDD is when folders were set
        (FileName=None,FileSuffix=None) is they are specified then it will use those values instead
    scanIOC=None -> uses BL_ioc to determine the IOC for scanning
    comment="Additional comments, (e.g. 'XPS survey')"
 
    Update SaveFile_Header version number when changing the structure of the file (indexing). 
    previously EA_log()
    """
    #default parameters
    kwargs.setdefault('comment',"")
    kwargs.setdefault('FileSuffix','log')
    kwargs.setdefault('FileName',None)
    kwargs.setdefault('FilePath',"/home/beams/29IDUSER/Documents/User_Folders/")
    kwargs.setdefault('scanIOC',BL_ioc())
    kwargs.setdefault('debug',False)

    #assigning variable the dictionary values (there has to be a more concise way to do this, but moving on)
    comment=kwargs['comment']
    FileSuffix=kwargs['FileSuffix']
    FileName=kwargs['FileName']
    FilePath=kwargs['FilePath']
    scanIOC=kwargs['scanIOC']

    if FileSuffix != None: 
        ScanInfo={}
        try:
            ScanInfo.update({'ScanName':[caget(EA._savePlugin+"FileName_RBV",as_string=True),"s"]})
            ScanInfo.update({'t ': [time.strftime("%D-%H:%M:%S"),"s"]})
            if BL_Mode_Read()[0]<2: #xray
                ScanInfo.update({'ID_Mode':[ID_State2Mode("State",caget("ID29:ActualMode")),"s"]})
                ScanInfo.update({'ID_QP':[caget("ID29:QuasiRatio.RVAL"),".2f"]})
                ScanInfo.update({'ID_SP':[round(caget("ID29:EnergySet.VAL"),4)*1000,".2f"]})
                ScanInfo.update({'ID_RBV':[round(caget("ID29:Energy.VAL"),4)*1000,".2f"]})
                ScanInfo.update({'hv':[caget("29idmono:ENERGY_SP"),".2f"]})
            else:
                ScanInfo.update({'ID_Mode':["","s"]})
                ScanInfo.update({'ID_QP':[0,".2f"]})
                ScanInfo.update({'ID_SP':[0,".2f"]})
                ScanInfo.update({'ID_RBV':[0,".2f"]})
                ScanInfo.update({'hv':[22,".2f"]})
            ScanInfo.update({'slit':[caget("29idb:Slit3CRBV"),".2f"]})
            c=caget("29idmono:GRT_DENSITY")
            if c==1200:
                ScanInfo.update({'GRT':["MEG","s"]})
            elif c== 2400:
                ScanInfo.update({'GRT':["HEG","s"]})
            for key in ['x','y','z','th','chi','phi']:
                ScanInfo.update({key:[caget(ARPES_PVmotor(key)[1]),".2f"]})
            for key in ['SES_slit','TA','TB']:
                ScanInfo.update({key:[caget(ARPES_PVextras(key)),".2f"]})
            for key in ['tey1','tey2']:
                ScanInfo.update({key:[caget(ARPES_PVextras(key)),"1.2e"]})
            ScanInfo.update({'PassEnergy':[EA.PassEnergy,".0f"]})
            ScanInfo.update({'LensMode':[EA.LensMode,"s"]})
            scan_mode,KE=EA._spectraInfo()
            ScanInfo.update({"scan_mode":[scan_mode,"s"]})
            ScanInfo.update({"KE":[str(KE),"s"]})
            ScanInfo.update({"Sweeps":[EA.Sweeps,".0f"]})
            ScanInfo.update({"Frames":[EA.ExpFrames,".0f"]})
            if kwargs['debug']:
                print(ScanInfo)
        except:
            print("Couldn't read one of the PV; check for missing soft IOC.")
        try:
            ListOfEntry=[]
            ListOfPv=[]
            ListOfFormat=[]
            for key in ScanInfo:
                ListOfEntry.append(key)
                ListOfPv.append(ScanInfo[key][0])
                ListOfFormat.append(ScanInfo[key][1])
            if kwargs['debug']:
                for i,j,k in zip(ListOfEntry,ListOfPv,ListOfFormat):
                    print(i,j,k)
                    print(logname(scanIOC,FileName,FileSuffix))
            FileNameWithSubFolder=logname(scanIOC,FileName,FileSuffix)
            if kwargs['debug']:
                print(FileNameWithSubFolder)
            SaveFile(FilePath,FileNameWithSubFolder,ListOfEntry,ListOfPv,ListOfFormat)
        except:
            print("EAlog did not write to file, check for errors.")

def log_headerEA(**kwargs):##JM - need to update so that we get the keys from log_EA
    s="\nscan    x   y   z   th   chi   phi   T   scan_mode   E1   E2   step   i   f   PE   lens_mode   SES slit #    ID_mode   hv   exit_slit   GRT   TEY1   TEY2   time\n"
    kwargs={'comment': s}
    logprint(**kwargs)

def _EAspectraTime():
    """
    estimates the time for spectra with the current analyzer settings
    """
    time_seconds=0
    overhead=0.25 #emperically determined
    if caget(EA.PHV+"ScientaMode") == 2: #Fixed
        numFrames=caget(EA.P+"ExpFrames.VAL")
        time_seconds=numFrames*(1/17)+overhead 
    elif caget(EA.PHV+"ScientaMode") > 2: #Baby-Sweep and Sweep
        HVscanDIM=2
        numPoints=caget(EA.PHV+"SCAN:steps.VAL")
        numFrames=caget("29idcScienta:"+"ExpFrames.VAL")
        PDLY=caget(EA.PHV+"scan"+str(HVscanDIM)+".PDLY")
        DDLY=caget(EA.PHV+"scan"+str(HVscanDIM)+".PDLY")
        time_seconds=numPoints*(1/17+PDLY+DDLY+overhead)     
    return str(datetime.timedelta(seconds=time_seconds))    

def EAsweptTime_estimate(EAlist):
    """
    estimates the time for spectra with the current analyzer settings
    """
    E=1392#image width
    HVscanDIM=2
    
    C=EAlist[1]# Estart
    D=EAlist[2]# Estop
    A=EAlist[3]# Estep
    B=EAlist[4]*0.000078# PixelEnergy=PassEnergy*0.000078

    numPnts=ceil((D-C)/ceil(A/B)/B)+E/min(floor(ceil(A/B)+0.001),E)-(E/min(floor(ceil(A/B)+0.001),E))%2+1
                                                 
    PDLY=caget(EA.PHV+"scan"+str(HVscanDIM)+".PDLY")
    DDLY=caget(EA.PHV+"scan"+str(HVscanDIM)+".PDLY")
    time_seconds=numPnts*(1/17+PDLY+DDLY+overhead)   

def _scanEATrigger(EAlist,before_after,**kwargs):
    """
    before_after="before" sets up scanIOC scanRecord for EA scan and sets prefix to "MDAscan0000"
    before_after="after" clears up scanIOC scanRecord of EA scan and resets prefix to "EA"
        Trigger EA
        Det20 = EA scanNum

        set the EA._savePlugin Prefix to be 'MDAscan0045_'
        **kwargs:
            scanIOC = BL_ioc()
            scanDIM=1
            detTrig=2
    """ 
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    kwargs.setdefault("detTrig",2)
    kwargs.setdefault("dtype",EA.dtype)
    kwargs.setdefault("detNum",20)
    kwargs.setdefault("prefix","EA")# if not None then over rides the auto
    kwargs.setdefault("debug",False)

    scanPV="29id"+kwargs["scanIOC"]+":scan"+str(kwargs["scanDIM"])
    triggerPV=scanPV+".T"+str(kwargs["detTrig"])+"PV"
    
    if kwargs["debug"]:
        print("scanPV: "+scanPV)
        print("before_after: "+before_after)
        
    #setting EA._savePlugin FilePath, FileName,FileNumber
    if before_after == "before":
        _scanEAPrefix("mda",**kwargs)
        scanType,HVscanPV, KElist =EA._spectraSetup(EAlist)
        caput(triggerPV,HVscanPV)
        
    if before_after == "after":
        _scanEAPrefix(kwargs["prefix"],**kwargs)
        caput(triggerPV,"")
        
    if kwargs["debug"]:
        print(triggerPV,caget(triggerPV, as_string=True))
    return
 

def _scanEAPrefix(ptype,**kwargs):
    """
    sets the EA file prefix based on 
    ptype = "mda" -> for "MDAscan"+current MDA file
        else prefix = ptype
    kwargs:
        debug = False (default)
        prefix
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("debug",False)
    kwargs.setdefault("nzeros",4)
    kwargs.setdefault("debug",False)
    
    prefix=""
    if kwargs["debug"]:
        print(ptype)

    if ptype == "mda":
        fpath=dirname(MDA_CurrentDirectory(kwargs["scanIOC"]))[0:-3]+EA.dtype
        nextMDA = caget("29id"+kwargs["scanIOC"]+":saveData_scanNumber")
        prefix="MDAscan"+str.zfill(str(nextMDA),kwargs["nzeros"])
    else:
        prefix = ptype
    
    if kwargs["debug"]==kwargs["debug"]:
        print("_scanEAPrefix prefix: ",prefix)

    
    #setting the file path for the EA saving
    fpath=caget(EA._savePlugin +"FilePath",as_string=True)
    caput(EA._savePlugin+"FileName",prefix)
    nextNum=getNextFileNumber(fpath,prefix,**kwargs)
    caput(EA._savePlugin+"FileNumber",nextNum)
    sleep(.5)
    if kwargs["debug"]:
        print("FilePath: ",caget(EA._savePlugin +"FilePath", as_string=True))
        print("FileName: ",caget(EA._savePlugin +"FileName", as_string=True))
        print("FileNumber: ",caget(EA._savePlugin +"FileNumber", as_string=True))

def _BE2KE_setupCalc(BE,DESC,CalcOutNum,OutputPV):
    """
    used by scanEA for talking in BE
    """
    pvCalcOut="29idcScienta:userCalcOut"+str(CalcOutNum)
    caput(pvCalcOut+".DESC", DESC)
    caput(pvCalcOut+".A",BE)
    caput(pvCalcOut+".INPB","29idmono:ENERGY_MON")
    caput(pvCalcOut+".INPC","29idcScienta:HV:WorkFunction")
    caput(pvCalcOut+".CALC$","B-A-C")
    caput(pvCalcOut+".OUT",OutputPV+" PP")
    return pvCalcOut+".PROC"
    
def scanEA_reset(**kwargs):
    """resets the IOC after a forced stop
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    _scanEATrigger([],"after",**kwargs)
    Clear_Scan_Positioners(kwargs["scanIOC"],kwargs["scanDIM"])
    
def scanEA(EAlist,**kwargs):
    """
    Uses the scanRecord (mda) to take multiple Scienta spectra
    EAlist=
        Fixed Mode:["KE"/"BE",CenterEnergy,PassEnergy,Frames,Sweeps] (5)
        Swept Mode:["KE"/"BE",StartEnergy,StopEnergy,StepEnergy,PassEnergy,Frames,Sweeps] (7)
        Baby Sweep (dither):["KE"/"BE",CenterEnergy,PassEnergy,Frames,Sweeps,"BS"] (6)

            (+) BE is positive below Ef
            (-) BE is negative above Ef
            
    **kwargs
        scanIOC=BL_ioc()
        scanDIM=1
        run=True
        debug=False
        
    """

    kwargs.setdefault('scanIOC',BL_ioc())
    kwargs.setdefault('scanDIM',1)
    kwargs.setdefault("run",True)
    kwargs.setdefault("debug",False)
    
    if EAlist[0]=="KE" or EAlist[0]=="BE":
        pass
    else:
        print("need to specify BE or KE")

    if EAlist[-1]=='BS':
        sweeps=EAlist[-2]
    else:
        sweeps=EAlist[-1]
        
    if kwargs['debug']:
        print("sweeps: "+str(sweeps))

    #set up name and add HV trigger and FileNum as det scan1 (sweeps)
    _scanEATrigger(EAlist,"before",**kwargs)

    #Fill in Sweeps scan
    Clear_Scan_Positioners(kwargs["scanIOC"],kwargs["scanDIM"])
    VAL=""
    RBV=""
    Scan_FillIn(VAL,RBV,kwargs["scanIOC"],kwargs["scanDIM"],0,sweeps,1,point=Scan_FillIn)
    if kwargs['debug']:
        scanPV="29id"+kwargs["scanIOC"]+":scan"+str(kwargs["scanDIM"])
        print("scanPV: "+scanPV)
        
    #Writing EA parameters
    EAscanType,EAscanPV, KElist =EA._spectraSetup(EAlist)
    #this part is eventually go into the Scienta IOC
    if EAlist[0]=="BE":
        if EAscanType == "Fixed":
            pvCalcOut1=_BE2KE_setupCalc(EAlist[1],"BE_center",10,"29idcScienta:HV:fixedEnergy.VAL")
            KE_arrayp1=np.full((sweeps), 1)
            Scan_FillIn_Table(pvCalcOut1,"",kwargs["scanIOC"],kwargs["scanDIM"],np.full((sweeps), 1),1)
        elif EAscanType == "Baby-Sweep":
            pvCalcOut1=_BE2KE_setupCalc(EAlist[1],"BE_center",10,"29idcScienta:HV:babySweepCenter.VAL")
            KE_arrayp1=np.full((sweeps), KElist[0])
            Scan_FillIn_Table(pvCalcOut1,"",kwargs["scanIOC"],kwargs["scanDIM"],np.full((sweeps), 1),1)
        elif EAscanType == "Sweep":
            pvCalcOut1=_BE2KE_setupCalc(EAlist[1],"BE_start",9,"29idcScienta:HV:sweepStartEnergy.VAL")
            pvCalcOut2=_BE2KE_setupCalc(EAlist[2],"BE_stop",10,"29idcScienta:HV:sweepStopEnergy.VAL")
            KE_arrayp1=np.full((sweeps), KElist[0])
            KE_arrayp2=np.full((sweeps), KElist[1])
            Scan_FillIn_Table(pvCalcOut1,"",kwargs["scanIOC"],kwargs["scanDIM"],np.full((sweeps), 1),1)
            Scan_FillIn_Table(pvCalcOut2,"",kwargs["scanIOC"],kwargs["scanDIM"],np.full((sweeps), 1),2)
            
    if kwargs['debug']:
        print("EA._spectraSetup: ")
        print(EAscanType,EAscanPV, KElist)

    print(EA._spectraMessage(EAscanType, EAscanPV, KElist))
    print(_EAspectraTime())
    
    #executing the scan
    if kwargs["run"]==True:
        Scan_Go(kwargs["scanIOC"],kwargs["scanDIM"])
        log_EA(**kwargs)
        #kwargs.update({"prefix":"EA"})
        #scanEA_reset(**kwargs)


        
def scanFM(RoughPositions,thList,EAlist,**kwargs):
    """
    New FermiMap using ScanRecord table scans to move motors
    RoughPositions is a List rough positions from which to interpolate (use RoughPositions_Find())
    thList=[th_start,th_stop,th_step]
    EAlist  to be finish only one scan at the moment[can be a single list if you are only taking a single scan or a list of lists to take multiple scans]
        **kwargs
            scanIOC = BL_ioc()
            scanDIM = 1
        
            logfile(**kwargs)
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("debug",False)
    kwargs.setdefault("run",True)
    
    scanIOC=kwargs['scanIOC']
    scanDIM=2 #hard coded
    
    if kwargs['debug']:
        print(scanIOC,scanDIM)
    
    # Making Tables and Filling positioners
    x,y,z,th,chi,phi=interpRoughPositions(RoughPositions,thList[0],thList[1],thList[2])
    if kwargs['debug']:
        print(x,y,z,th,chi,phi)
    
    Scan_FillIn_Table(ARPES_PVmotor("th")[1],ARPES_PVmotor("th")[0],scanIOC,scanDIM,th,posNum=1)
    Scan_FillIn_Table(ARPES_PVmotor("x")[1],ARPES_PVmotor("x")[0],scanIOC,scanDIM,x,posNum=2)
    Scan_FillIn_Table(ARPES_PVmotor("y")[1],ARPES_PVmotor("y")[0],scanIOC,scanDIM,y,posNum=3)
    Scan_FillIn_Table(ARPES_PVmotor("z")[1],ARPES_PVmotor("z")[0],scanIOC,scanDIM,z,posNum=4)

    #setting up EA
    run=kwargs['run']
    kwargs['run']=False
    kwargs['scanDIM']=1
    scanEA(EAlist,**kwargs)
    kwargs['run']=run
    
    #executing the scan
    if kwargs["run"]==True:
        Scan_Go(kwargs["scanIOC"],2)
        log_EA(**kwargs)
        scanEA_reset(**kwargs)


def interpRoughPositions(RoughPositions,thStart,thStop,thStep,**kwargs):
    """
    Interpolate sample position as a function of theta, based on RoughPosition, 
    a list of motor position lists and returns x,y,z,th,chi,phi

    **kwargs:
        kind="cubic" by default, interpolation type ("linear","cubic","quadratic")

    Usage:  
        x,y,z,th,chi,phi=interpRoughPositions(RoughPositions,3,-8,0.5) 

    (direction to minimize backlash)
        RoughPositions=[
                    [x,y,z,th,chi,phi],
                    [x,y,z,th,chi,phi]
                    ]
    """
    kwargs.setdefault('kind','cubic')
    kwargs.setdefault('debug',False)

    #Puts Rough Position in increasing theta order
    RoughPositions=sorted(RoughPositions, key=itemgetter(3))[::-1] 
    RoughPositions=np.array(RoughPositions)
    if kwargs['debug']:
        print('RoughPositions: ',RoughPositions)

    #thlist
    if kwargs['debug']:
        print('ths: ',thStart,thStop,thStep)
    th=np.arange(np.max([thStart,thStop]),np.min([thStart,thStop])-1.0*abs(thStep),-1.0*abs(thStep),dtype=float)
    if kwargs['debug']:
        print('th: ',th)
        
    #interpolating
    def func(th,th_col,m_col,**kwargs):
        f=interp1d(th_col,m_col)
        m=f(th)
        return m
    x=func(th,RoughPositions[:,3], RoughPositions[:,0])
    y=func(th,RoughPositions[:,3], RoughPositions[:,1])
    z=func(th,RoughPositions[:,3], RoughPositions[:,2])
    chi=func(th,RoughPositions[:,3], RoughPositions[:,4])
    phi=func(th,RoughPositions[:,3], RoughPositions[:,5])

    return x,y,z,th,chi,phi

def mv_interp(RoughPositions, thVal,**kwargs):
    """
    Moves to the interpolated position for a give theta and RoughPosition list
    uses interpRoughPositions
    """
    x,y,z,th,chi,phi=interpRoughPositions(RoughPositions,thVal,thVal-.1,1,kwargs)
    Pos=[x,y,z,th,chi,phi]
    sample(Pos)

def scanEA_hv(*hvs,EAlist,**kwargs):    
    """
    hv (not kz!!!) map with fixed energy steps; uses scanXAS in scanDIM2.
    WARNING: To be used only with \"BE\" mode in EAlist.
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    scanXAS(hv,StartStopStepLists,settling_time=0.2,average=None,scanIOC=None,scanDIM=1,**kwargs)
    scanDIM=2 (hard coded)
    
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("average",None)
    kwargs.setdefault("run",True)
    kwargs.setdefault("debug",False)

    #setting up EA
    run=kwargs['run']
    kwargs['run']=False
    kwargs['scanDIM']=1
    scanEA(EAlist,**kwargs)
    kwargs['run']=run

    
    #Setting up the ScanRecord for Mono and ID in Table mode
    scanDIM=2 #hard coded
    kwargs["scanDIM"]=scanDIM
    mono_array,ID_array=Tables_BLenergy(*hvs,**kwargs)
    ScanFillIn_BLenergy(*hvs, **kwargs)
    
    
    if kwargs["run"]==True:
        #Setting the beamline energy to the first point, and EA at first KE
        energy(mono_array[0])
        KE=mono_array[0]-EAlist[1]
        EA.put(KE=KE)
        #Scanning                      
        Scan_Go(kwargs["scanIOC"],scanDIM)
        log_EA(**kwargs)
        #After scan
        scanEA_reset(**kwargs)
        Scan_Reset_AfterTable(kwargs['scanIOC'],scanDIM)

        
def scanEA_kz(n_start,n_stop,n_step,lattice,V0, EAlist,**kwargs):
    """
    kz map; uses scanXAS in scanDIM2.
    WARNING: To be used only with \"BE\" mode in EAlist.
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    scanXAS(hv,StartStopStepLists,settling_time=0.2,average=None,scanIOC=None,scanDIM=1,**kwargs)
    """
    #calculation hvs
    nList=np.arrange(n_start,n_stop,n_step,dtype=float)
    hvList=kz2hv(lattice,V0,nList)
    
    ScanFillIn_BLenergy(hvList, **kwargs)
    
    #setting up EA
    scanEA(EAlist,run=False)
    
    if kwargs["run"]==True:
        #Setting the beamline energy to the first point
        energy(mono_array[0])
        #Scanning                      
        print(EA._spectraMessage(EAscanType, EAscanPV, KElist))
        Scan_Go(kwargs["scanIOC"],kwargs["scanDIM"])
        log_EA(**kwargs)
        #After scan
        scanEA_reset(**kwargs)
        Scan_Reset_AfterTable(kwargs['scanDIM'],kwargs['scanDIM'])

    
def hv2kz(lattice,V0,hv):
    """
    Converts a hv value for the nth zone had returns corresponding kz values 
    [0]for zone  boundary and [1] for zone center in inverse angstroms
    lattice = c; assuming kz orthoganal to a-b plane (i.e. 2pi/c = GZ distance)
    and at zone center (kx,ky)=0 /cos(th=0)=1
    V0 = the inner potential
    """
    work_fct=EA.wk
    Ek=hv-work_fct
    k_z=0.5124*sqrt(Ek+V0)    # Kz at (kx,ky)=0 i.e. cos(th)=1
    c_star=2*pi/lattice    # 2pi/c = GZ distance
    GZ_n=round((k_z/c_star*2),2)
    G_n=round((k_z/c_star),2)
    print("  kz = "+str(round(k_z,2))+" A^(-1) = " +str(GZ_n)+" * pi/c = " +str(G_n)+" * 2pi/c")
    return GZ_n,G_n
    
def kz2hv(lattice,V0,n):
    """
    Converts a kz value for the nth zone had returns corresponding hv
    lattice = c; assuming kz orthoganal to a-b plane (i.e. 2pi/c = GZ distance)
    and at zone center (kx,ky)=0 /cos(th=0)=1
    V0 = the inner potential
    """
    work_fct=EA.wk
    c_star=2*pi/lattice        # 2pi/c = GZ distance
    Ek=(n*c_star/0.5124)**2-V0    # Ek at (kx,ky)=0 i.e. cos(th)=1
    hv=Ek+work_fct
    mono=round(hv,1)
    print("\n")
    print("  hv = Ek + Phi = "+str(round(hv,2))+" eV")
    print("  kz = n*2pi/c   with  n = "+str(n))
    return mono


def Print_Gamma_n(lattice,V0,n1,n2):
    work_fct=EA.wk
    c_star=2*pi/lattice                # 2pi/c = GZ distance
    for n in RangeUp(n1,n2,1):
        Ek_Gn=(n*c_star/0.5124)**2-V0        # Ek at G
        Ek_Zn=((n+0.5)*c_star/0.5124)**2-V0    # Ek at Z
        hv_Gn=round(Ek_Gn+work_fct,2)
        hv_Zn=round(Ek_Zn+work_fct,2)
        print("\n G["+str(n)+"]:  hv = Ek + Phi = "+str(round(hv_Gn,2))+" eV ")
        print(" Z["+str(n)+"]:  hv = Ek + Phi = "+str(round(hv_Zn,2))+" eV")

def Print_Gamma_hv(lattice,V0,hv1,hv2):
    work_fct=EA.wk
    c_star=2*pi/lattice                # 2pi/c = GZ distance
    Ek1=hv1-work_fct
    Ek2=hv2-work_fct
    k_z1=0.5124*sqrt(Ek1+V0)    # Kz at (kx,ky)=0 i.e. cos(th)=1
    k_z2=0.5124*sqrt(Ek2+V0)    # Kz at (kx,ky)=0 i.e. cos(th)=1
    GZ_n1=round((k_z1/c_star*2),1)
    G_n1=round((k_z1/c_star),1)
    GZ_n2=round((k_z2/c_star*2),1)
    G_n2=round((k_z2/c_star),1)
    if modf(G_n1)[0]>=0.5:
        n1=modf(G_n1)[1]+1,0
    else:
        n1=modf(G_n1)[1]
    n2=modf(G_n2)[1]
    print("\n hv1 = "+str(hv1)+" eV:  " +str(GZ_n1)+" * pi/c = " +str(G_n1)+" * 2pi/c")
    if type(n1) == tuple: n1 = n1[0]
    if type(n2) == tuple: n2 = n2[0]
    Print_Gamma_n(lattice,V0,n1,n2)
    print("\n hv2 = "+str(hv2)+" eV:  " +str(GZ_n2)+" * pi/c = " +str(G_n2)+" * 2pi/c")
    return n1,n2

def kx2deg(lattice,hv):
    a=pi/lattice
    b=0.5124*sqrt(hv)
    c=a/b
    theta_rad=asin(c)
    theta_deg=rad2deg(theta_rad)
    print(" 1/2-BZ (GX) = "+str(round(theta_deg,1))+" deg")
    
def Resolution_EA(PE,slit_SES):    # updated 10/30/17: straight slits scaled to slit width not area
    SES_Table={}
    SES_Table[2]   = {1: 1.6, 2:2,   3:2,   4:4,   5:4,   6:6,    7:12,   8:20,   9:32}
    SES_Table[5]   = {1: 2.7, 2:4,   3:4,   4:7,   5:7,   6:11,   7:20,   8:34,   9:54}
    SES_Table[10]  = {1: 5.7, 2:9,   3:9,   4:14,  5:14,  6:23,   7:43,   8:71,   9:114}
    SES_Table[20]  = {1:10.8, 2:16,  3:16,  4:27,  5:27,  6:43,   7:81,   8:135,  9:216}
    SES_Table[50]  = {1:34.6, 2:52,  3:52,  4:87,  5:87,  6:138,  7:260,  8:433,  9:692}
    SES_Table[100] = {1:49.5, 2:74,  3:74,  4:124, 5:124, 6:198,  7:371,  8:619,  9:990}
    SES_Table[200] = {1:88.9, 2:133, 3:133, 4:222, 5:222, 6:356,  7:667,  8:1111, 9:1778}
    SES_Table[500] = {1:250,  2:375, 3:375, 4:625, 5:625, 6:1000, 7:1875, 8:3125, 9:5000}
    try:
        SES=SES_Table[PE][slit_SES]
    except KeyError:
        print("WARNING: Not a valid PE/Slit combination")
        SES=0
    return SES
