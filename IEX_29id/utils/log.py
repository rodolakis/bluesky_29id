from epics import caput, caget 
from .exp import BL_ioc, CheckBranch
from .misc import today 
import time
import os

def logname_PV(scanIOC=None):
    """
    Dictionary to get the PV in which the FileName for logging is stored
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    PV_Dict={
        'Test':'29idb:userStringSeq10.STR1',
        'ARPES':'29idb:userStringSeq10.STR2',
        'Kappa':'29idb:userStringSeq10.STR3',
        'RSoXS':'29idb:userStringSeq10.STR4',
        }
    if scanIOC in PV_Dict.keys():
        PV=PV_Dict[scanIOC]
    else:
        PV='29idb:userStringSeq10.STR10'
    return PV

def logname_set(FileName=None,scanIOC=None):
    """
    Sets the string used for the FileName in scanlog and EAlog
    uses logname_PV to reference PV associated with a particular ioc
    if FileName=None it sets the filename to YYYYMMDD_log.txt
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    if FileName is None:
        FileName=today()+'_log.txt'
    try:
        PV=logname_PV(scanIOC)
        caput(PV,FileName)
        print("\nLog FileName = \'"+FileName+"\' @ "+PV)
        print('To change FileName, use logname_set("newname")')
    except:
        print("Error: was not able to set the FileName, check that 29idb IOC is running")

        
def logname_get(scanIOC=None):
    """
    Gets the string used for the FileName in scanlog and EAlog for the given scanIOC.
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    return caget(logname_PV(scanIOC))
       
def logname_generate(FileName=None,FileSuffix="log"):
    """
    Generates the filename based on the MDA_CurrentUser and the data
    """    
    UserName=MDA_CurrentUser()
    if FileName != None:
        if FileName[0] == '/':
            FileName=FileName[1:] 
        if FileName.find('.txt')== -1:
            FileName= FileName+'.txt'
        if FileName.find('/') == -1:
            FileNameWithSubFolder=UserName+'/'+FileName
        else:
            FileNameWithSubFolder=FileName
    else:
        
        FileNameWithSubFolder=UserName+'/'+today()+'_'+FileSuffix+'.txt'
    return FileNameWithSubFolder

def logname(scanIOC=None,FileName=None,FileSuffix='log'):
    """
    returns FileNameWithSubFolder using logname_PV is exist, else UserName/YYYYMMDD_log.txt
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    try: 
        PV=logname_PV(scanIOC)
        FileName=caget(PV)
        UserName=MDA_CurrentUser()
        FileNameWithSubFolder=UserName+'/'+FileName
    except:
        FileNameWithSubFolder=logname_generate(FileName,FileSuffix)
    return FileNameWithSubFolder

def logprint(comment,**kwargs):
    """
    Writes comments to the logfile on a new line
    comment is a string of what you want to add to the file e.g. "-------Starting Fermi Map--------"
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    #default parameters
    logargs = {
        'comment':comment,
        'FileSuffix':'log',
        'FileName':None,
        'FilePath':"/home/beams/29IDUSER/Documents/User_Folders/",
        'scanIOC': None  ,      
    }
    #updating to replace default values with those specified in kwargs 
    logargs.update(kwargs) 
    #assigning variable the dictionary values (there has to be a more concise way to do this, but moving on
    #print(logargs)
    FileSuffix=logargs['FileSuffix']
    FileName=logargs['FileName']
    FilePath=logargs['FilePath']   
    scanIOC=logargs['scanIOC']
    if scanIOC is None: 
        scanIOC=BL_ioc()
        print(comment) 
    try:
        FileNameWithSubFolder=logname(scanIOC,FileName,FileSuffix) 
        #print(FileNameWithSubFolder)
        if not os.path.isfile(os.path.join(FilePath, FileNameWithSubFolder)):
            SaveFile_Header(FilePath,FileNameWithSubFolder)
        with open(os.path.join(FilePath, FileNameWithSubFolder),'a') as myfile:
            myfile.write(comment)
            myfile.write('\n')
        #print(comment,FileNameWithSubFolder)
    except:
        print("Logprint failed")


def log_headerMDA(**kwargs):
    branch=CheckBranch()
    if branch == "c":
        s="\nscan   motor   start   stop   step   x   y   z   th   chi   phi   T   hv   exit_slit   GRT   ID_Mode   TEY     time   comment\n"
    if branch == "d":
        s="\nscan,motor,start,stop,step,x,y,z,tth,kth,kap,kphi,TA,TB,hv,exit_slit,GRT,ID_SP,ID_RBV,ID_Mode,ID_QP,TEY,mesh,det,HV,centroid,time,comment\n"
    kwargs.update({'comment': s})        
    logprint(**kwargs)

    
def scanlog(**kwargs):
    """
    Writes CSV file for the MDA scans with the following default parameters:
    FilePath='/home/beams/29IDUSER/Documents/User_Folders/UserName/'
    Filename is set by logname_set(FileName=None), default:YYYYMMDD_log.txt, where YYYYMMDD is when folders were set
        (FileName=None,FileSuffix=None) is they are specified then it will use those values instead
    scanIOC=None -> uses BL_ioc to determine the IOC for scanning
    comment="Additional comments"

    Update SaveFile_Header version number when changing the structure of the file (indexing).
    """
    #default parameters
    logargs={
        'comment':"",
        'FileSuffix':'log',
        'FileName' : None,
        'FilePath' : "/home/beams/29IDUSER/Documents/User_Folders/",
        'scanIOC':None
    }
    #updating to replace default values with those specified in kwargs 
    logargs.update(kwargs) 
    #assigning variable the dictionary values (there has to be a more concise way to do this, but moving on)
    comment=logargs['comment']
    FileSuffix=logargs['FileSuffix']
    FileName=logargs['FileName']
    FilePath=logargs['FilePath']
    scanIOC=logargs['scanIOC']
    
    if FileSuffix != None:
        #try:
        if scanIOC is None:
            scanIOC=BL_ioc()
        ScanName = caget("29id"+scanIOC+":saveData_baseName",as_string=True)
        ScanNum  = caget("29id"+scanIOC+":saveData_scanNumber")-1
        ScanName = ScanName+str(ScanNum)

        drive = caget("29id"+scanIOC+":scan1.P1PV")
        start = caget("29id"+scanIOC+":scan1.P1SP")
        stop  = caget("29id"+scanIOC+":scan1.P1EP")
        step  = caget("29id"+scanIOC+":scan1.P1SI")

        t = time.strftime("%D-%H:%M:%S")
        ID_Mode=ID_State2Mode("State",caget("ID29:ActualMode"))
        ID_QP =caget("ID29:QuasiRatio.RVAL")
        ID_SP =round(caget("ID29:EnergySet.VAL"),4)*1000
        ID_RBV=round(caget("ID29:Energy.VAL"),4)*1000
        hv=caget("29idmono:ENERGY_SP")
        c=caget("29idmono:GRT_DENSITY")
        if c==1200:
            GRT="MEG"
        elif c== 2400:
            GRT="HEG"
        branch=CheckBranch()
        if branch == "c":
            x   = caget(ARPES_PVmotor('x')[1])
            y   = caget(ARPES_PVmotor('y')[1])
            z   = caget(ARPES_PVmotor('z')[1])
            th  = caget(ARPES_PVmotor('th')[1])
            chi  = caget(ARPES_PVmotor('chi')[1])
            phi  = caget(ARPES_PVmotor('phi')[1])
            slit=caget("29idb:Slit3CRBV")
            T   =caget("29idARPES:LS335:TC1:IN1") 
            tey1=caget("29idc:ca1:read")
            tey2=caget("29idc:ca2:read")
            ListOfEntry=        ["scan", "motor","start","stop","step","x",  "y",  "z",  "th", "chi","phi", "T", "hv",  "exit_slit", "GRT", "ID_SP", "ID_RBV", "ID_Mode", "ID_QP", "TEY_1", "TEY_2", "time", "comment"]
            ListOfPv =        [ScanName,drive,  start,  stop , step , x    ,y    ,z    ,th   ,chi  ,phi,   T   ,hv   , slit ,      GRT,  ID_SP,  ID_RBV,  ID_Mode,  ID_QP,  tey1 , tey2  ,  t,   comment]
            ListOfFormat =    ["s" ,"s"  ,".3f",   ".3f", ".3f",".2f",".2f",".2f",".2f", ".2f",".2f",".1f",".2f",  ".0f",       "s",".1f",".1f",  "s", ".0f", "1.2e","1.2e","s",   "s"]
        elif branch == "d":
            x   = caget("29idKappa:m2.VAL")
            y   = caget("29idKappa:m3.VAL")
            z   = caget("29idKappa:m4.VAL")
            tth  = caget("29idKappa:m9.VAL")
            kth = caget("29idKappa:m8.RBV")
            kap  = caget("29idKappa:m7.VAL")
            kphi = caget("29idKappa:m1.RBV")
            slit=caget("29idb:Slit4Vt2.C")
            TA   = caget("29idd:LS331:TC1:Control")
            TB   = caget("29idd:LS331:TC1:SampleB")
            tey=str(caget("29idMZ0:scaler1.S2"))+' (x'+caget('29idd:A2sens_num.VAL',as_string=True)+' '+caget('29idd:A2sens_unit.VAL',as_string=True)+')'
            mesh = str(caget("29idMZ0:scaler1.S14"))+' (x'+caget('29idd:A1sens_num.VAL',as_string=True)+' '+caget('29idd:A1sens_unit.VAL',as_string=True)+')'
            det = caget('29idKappa:userStringSeq6.STR1')
            HV = caget('29idKappa:userCalcOut10.OVAL')
            centroid = caget('29id_ps6:Stats1:CentroidX_RBV')
            ListOfEntry=    ["scan","motor","start","stop","step","x","y","z","tth","kth","kap","kphi","TA","TB","hv","exit_slit","GRT", "ID_SP", "ID_RBV", "ID_Mode", "ID_QP","TEY","mesh","det","HV","centroid","time","comment"]
            ListOfPv =         [ScanName,drive,start,stop ,step ,x    ,y    ,z    ,tth   ,kth  ,kap, kphi,TA,TB    ,hv   ,slit ,GRT,  ID_SP,  ID_RBV,  ID_Mode,  ID_QP, tey  ,mesh,det, HV, centroid,t,comment]
            ListOfFormat =  ["s" ,"s"  ,".3f",".3f",".3f",".2f",".2f",".2f",".2f",".2f",".2f",".2f",".1f",".1f",".2f",".0f","s",".1f",".1f",  "s", ".0f","s","s","s",".0f",".2f","s","s"]
        #except:
        #    print("Couldn't read one of the PV; check for missing soft IOC.")
        try:
            FileNameWithSubFolder=logname(scanIOC,FileName,FileSuffix)
            SaveFile(FilePath,FileNameWithSubFolder,ListOfEntry,ListOfPv,ListOfFormat)
        except:
            print("scanlog did not write to file, check for errors.")
            