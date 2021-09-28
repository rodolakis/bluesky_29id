from math import *
import time
import datetime
import subprocess
import argparse
import re
import csv
import ast
import socket
import numpy as np
import numpy.polynomial.polynomial as poly
#import pandas as pd
from datetime import date
from os import listdir,mkdir,chown,system,chmod
from os.path import join, isfile, exists, dirname



def Folder_ARPES(UserName,**kwargs):
    """
    Create and sets (if create_only=False) all the folders the current run and ARPES user 
        Mode = "User" or "He"; automatically set to "Staff" if UserName is "Staff" 
    Sets the FileName for logging to be "UserName/YYYYMMDD_log.txt using logname_Set()"
    
    **kwargs:
        create_only = False; creates the data folder and sets scanRecords/AreaDetectors 
                    = True: only creates the data folders; does NOT set scanRecords/AreaDetectors 
        mdaOnly =True only creates/sets the mda folder (EA is unchanged)
        run = uses Check_run() to get current run based on the current date
        scanIOC = 'ARPES'
        Mode = 'User'; sets BL_Mode_Set(Mode) Mode: 'Staff'/'User'/'He'
        ftp = False; does not set up ftp
            = True; else creates the ftps folders
    """
    kwargs.setdefault('create_only',False)
    kwargs.setdefault('mdaOnly',False)
    kwargs.setdefault('run',Check_run())
    kwargs.setdefault('scanIOC','ARPES')
    kwargs.setdefault('Mode','User')
    kwargs.setdefault('ftp',False)
    kwargs.setdefault('debug',False)
    
    run=kwargs["run"]
    scanIOC=kwargs['scanIOC']
    ftp=kwargs['ftp']

    if UserName == 'Staff':
        folder='b'
        BL_Mode_Set('Staff')
    else:
        folder='c'
        BL_Mode_Set(kwargs["Mode"])
        
    if kwargs['debug']:
        print("run,folder,UserName,scanIOC,ftp: ",run,folder,UserName,scanIOC,ftp)
    # Create User Folder:
    Make_DataFolder(run,folder,UserName,scanIOC,ftp)
    sleep(5)
    if kwargs["create_only"] == False:
        # Set up MDA folder:
        Folder_mda(run,folder,UserName,scanIOC)
        print("\nScanIOC set to:", scanIOC)
        sleep(5)
        SaveStatus=caget('29id'+scanIOC+':saveData_status',as_string=True)
        SaveMessage=caget('29id'+scanIOC+':saveData_message',as_string=True)
        print("\nSave Status "+scanIOC+": "+SaveStatus+" - "+SaveMessage)
        logname_set(scanIOC=scanIOC)
        print("\nREMINDER: Reset_Scan('"+scanIOC+"'); Reset_CA_all(); Reset_Mono_Limits(); Reset_Lakeshore()")
        
    #Set up Scienta folders:
    if kwargs['mdaOnly'] == False:
        if caget(EA._statsPlugin+"Total_RBV",timeout=0.1) != None:
            Folder_EA(_userDataFolder(UserName,scanIOC),**kwargs)
        else:
            print(EA.PHV+" is not running")



def Folder_RSoXS(run,UserName,scanIOC="RSoXS",ftp=None):        # FR: scanIOC argument added for new Kappa soft IOC  - 9/27/2018
    """ Sets (and creates if needed) all the folders a given run="201X_Y" and RSoXS user """
    folder="d"
    BL_Mode_Set("User")
    # Create User Folder:
    Make_DataFolder(run,folder,UserName,scanIOC,ftp)
    sleep(5)
    # Set up MDA folder:
    Folder_mda(run,folder,UserName,scanIOC)
    print('\nScanIOC set to:', scanIOC)
    sleep(5)
    SaveStatus=caget('29id'+scanIOC+':saveData_status',as_string=True)
    SaveMessage=caget('29id'+scanIOC+':saveData_message',as_string=True)
    print("\nSave Status "+scanIOC+": "+SaveStatus+" - "+SaveMessage)
    logname_set(scanIOC=scanIOC)
    print('\nREMINDER: Reset_Scan("'+scanIOC+'"); Reset_CA_all(); Reset_Mono_Limits()')

def mdaPath(userName,scanIOC,**kwargs):
    """
    Returns the path to a user mda folder
            dataFolder='/net/s29data/export/data_29id'+folder+'/'+run+'/'+userName
    kwargs:
        run: Check_run(); unless specified
        BLmode:  Staff / User; based on userName unless specified
            
        folder: determined by UserName and scanIOC
            folder = b (Staff)
            folder = c (User and ARPES)
            folder = d (User and Kappa)
    """
    return join(_userDataFolder(userName,scanIOC,**kwargs),"mda")


def Folder_MPA(run,folder,UserName,FilePrefix="mpa"):
    if folder == "b":
        windowsIOC = "X"
        UserName = ""
        windowsPath = windowsIOC+':\\'+run+"\\mpa"
    else:
        windowsIOC = "Z"
        UserName = UserName+"/"
        windowsPath=windowsIOC+':\\'+run+"\\"+UserName[:-1]+"\\mpa"
    MyPath="/net/s29data/export/data_29id"+folder+"/"+run+"/"+UserName+"mpa"
    print("\nMPA folder: " + MyPath)
    if not (exists(MyPath)):
        mkdir(MyPath)
        FileNumber=1
    else:
        FileNumber=getNextFileNumber(MyPath,FilePrefix)
    caput("29iddMPA:det1:MPAFilename",windowsIOC+":/"+run+"/"+UserName+"mpa/mpa_")
    caput("29iddMPA:TIFF1:FilePath",windowsPath)
#    caput("29iddMPA:TIFF1:FilePath",windowsIOC+':/'+run+"/"+UserName+"/mpa")
    print("\nMPA folder on Crabby: "+windowsPath)
    caput("29iddMPA:TIFF1:FileName",FilePrefix)
    caput("29iddMPA:TIFF1:FileNumber",FileNumber)


def SaveFile_Header(FilePath,FileName,ListOfEntry=None):   
    version = '1.2'
    FilePathC  = MDA_CurrentDirectory('ARPES')
    FilePathD  = MDA_CurrentDirectory('Kappa')
    ListOfEntry_EA   ="scan,x,y,z,th,chi,phi,T,scan_mode,E1,E2,step,i,f,PE,lens_mode,SES slit #,hv,exit_slit,GRT,ID_SP,ID_RBV,ID_Mode,ID_QP,TEY1,TEY2,time,comment"           
    ListOfEntry_ARPES="scan,motor,start,stop,step,x,y,z,th,chi,phi,T,hv,exit_slit,GRT,ID_SP,ID_RBV,ID_Mode,ID_QP,TEY_1,TEY_2,time,comment"            
    ListOfEntry_Kappa="scan,motor,start,stop,step,x,y,z,tth,kth,kap,kphi,TA,TB,hv,exit_slit,GRT,ID_SP,ID_RBV,ID_Mode,ID_QP,TEY,mesh,det,HV,centroid,time,comment"
    if FileName[0] == '/':
        FileName=FileName[1:] 
    with open(join(FilePath, FileName), "w+") as f:
        f.write('@Log version: '+ version+'\n\n')
        f.write('FilePath ARPES:  '+ FilePathC+'\n')
        f.write('FilePath Kappa:  '+ FilePathD+'\n\n')
        f.write('EA Header:  '+ ListOfEntry_EA+'\n\n')
        f.write('ARPES Header:\n'+ ListOfEntry_ARPES+'\n\n')
        f.write('Kappa Header: \n'+ ListOfEntry_Kappa+'\n\n')
        
        
#        if ListOfEntry != None:
#            FileHeader = "    ".join(ListOfEntry)+"\n"
#            f.write(FileHeader+'\n')


   
def SaveFile(FilePath,FileName,ListOfEntry,ListOfPv,ListOfFormat):
    """ To be used for scanlog and scanEA functions.
        Update SaveFile_Header version number when changing the structure of the file (indexing).
    """
    
    if FileName[0] == '/':
        FileName=FileName[1:] 
    
    if not isfile(join(FilePath, FileName)):
        SaveFile_Header(FilePath,FileName,ListOfEntry)
    with open(join(FilePath, FileName), "a+") as f:
        for i in RangeUp(0,len(ListOfFormat)-2,1):
            PvFormat="{0:"+ListOfFormat[i]+"},"
            f.write(PvFormat.format(ListOfPv[i]))
        LastEntry=len(ListOfFormat)-1
        PvFormat="{0:"+ListOfFormat[LastEntry]+"}\n"
        f.write(PvFormat.format(ListOfPv[LastEntry]))





##############################################################################################################
################################             Tables             ##############################
##############################################################################################################

def TestMe():
    print("YEAH!")

def TestShell():
    subprocess.call("start_cryocon")






def Mono_Optics():
    """
    returns current mono variables [[Mirror],[Grating],[VLS]]
        Mirror=[MIR,MIR_Offset,MIR_Tx]
        Grating=[GRT,GRT_Offset,GRT_Tx,GRT_LD,GRT_b2]
        VLS=[CFF,TUN0,TUN1,TUN2,TUN3,ARM]]
    """
    num1=caget("29idmonoMIR_TYPE_MON")
    num2=caget("29idmonoGRT_TYPE_MON")
    Mono_Optics={}
    Mono_Optics["MIR"] = {1:("Au_1000", "C"), 2:("Silicon", "D"), 3:("Carbon","E"), 4:("Au_500","F"), 5:("not used","G"), 6:("not used","H"), 7:("not used","I"), 8:("not used","J"), 9:("not used","K"), 10:("not used","L")}
    Mono_Optics["GRT"] = {1:("MEG_1000","C"), 2:("HEG_1000","D"), 3:("Dummy" ,"E"), 4:("Dummy" ,"F"), 5:("MEG_500" ,"G"), 6:("HEG_500" ,"H"), 7:("not used","I"), 8:("not used","J"), 9:("not used","K"), 10:("not used","L")}
    try:
        MIR,MIR_pv=Mono_Optics["MIR"][num1]
        GRT,GRT_pv=Mono_Optics["GRT"][num2]
        GRT_Offset=caget("29idmonoGRT:P_OFFSETS."+GRT_pv)
        GRT_b2=caget("29idmonoGRT:B2_CALC."+GRT_pv)
        GRT_Tx=caget("29idmonoGRT:X_DEF_POS."+GRT_pv)
        GRT_LD=caget("29idmonoGRT:TYPE_CALC."+GRT_pv)
        MIR_Offset=caget("29idmonoMIR:P_OFFSETS."+MIR_pv)
        MIR_Tx=caget("29idmonoMIR:X_DEF_POS."+MIR_pv)
        CFF=caget("29idmono:CC_MON")
        TUN0=caget("29idmonoGRT:TUN0_CALC."+GRT_pv)
        TUN1=caget("29idmonoGRT:TUN1_CALC."+GRT_pv)
        TUN2=caget("29idmonoGRT:TUN2_CALC."+GRT_pv)
        TUN3=caget("29idmonoGRT:TUN3_CALC."+GRT_pv)
        ARM=caget("29idmono:PARAMETER.G")
    except KeyError:
        print("WARNING: Not a valid MIR and/or GRT position - check for mono error!")
        GRT=""
        MIR=""
        CFF=0
        TUN0=0
        TUN1=0
        TUN2=0
        TUN3=0
        GRT_Offset=0
        GRT_b2=0
        GRT_Tx=0
        GRT_LD=0
        MIR_Offset=0
        MIR_Tx=0
        ARM=0
    return [[MIR,MIR_Offset,MIR_Tx],[GRT,GRT_Offset,GRT_Tx,GRT_LD,GRT_b2],[CFF,TUN0,TUN1,TUN2,TUN3,ARM]]

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

    
def centroid(t=None,q=1): 
    '''
    Return position of centroid, sigma, m3r:RY (mirror pitch)
    Optional argument t to set camera intergration time.
    '''
    if t is not None:
        caput('29id_ps6:cam1:AcquireTime',t)
    else:
        t=caget('29id_ps6:cam1:AcquireTime')
    position=  round(caget('29id_ps6:Stats1:CentroidX_RBV'),2)
    sigma=round(caget('29id_ps6:Stats1:SigmaX_RBV'),2)
    intensity=round(caget('29id_ps6:Stats1:CentroidTotal_RBV'),2)
    m3rRY=round(caget("29id_m3r:RY_MON"),4)
    if q != None:
        print('(position, sigma, total intensity, integration time (s), mirror pitch):')
    return position,sigma,intensity,t,m3rRY



def align_m3r(p=118,debug=False):
    
    def mvm3r_pitch_FR(x):
        if -16.53<x<-16.38:
            motor_pv="29id_m3r:RY_POS_SP"
            #print('... moving to '+str(x))
            caput(motor_pv,x)
            sleep(0.5)
            caput("29id_m3r:MOVE_CMD.PROC",1)
            sleep(1)
            #print('Positioned')
        else:
            print('Out of range')

    shutter=caget('PA:29ID:SDS_BLOCKING_BEAM.VAL')
    camera=caget('29id_ps6:cam1:Acquire',as_string=True)
    hv=caget('29idmono:ENERGY_SP')
    if shutter == 'ON':
        foo=input_d('Shutter D is closed, do you want to open it (Y or N)? >')
        if foo == 'Y'.lower() or foo == 'y' or foo == 'yes'.lower():
            Open_DShutter()
        else:
            print('Aborting...')
            return
    if camera == 'Done':
        caput('29id_ps6:cam1:Acquire','Acquire') 
     
    if hv < 2190:
        caput('29id_ps6:cam1:AcquireTime',0.001)
        caput('29id_ps6:Stats1:CentroidThreshold',7)
    else:
        caput('29id_ps6:cam1:AcquireTime',0.03)
        caput('29id_ps6:Stats1:CentroidThreshold',7)
    sleep(1)    
    intensity=caget('29id_ps6:Stats1:CentroidTotal_RBV')
    if intensity < 10000:
        print('Count too low. Please adjust camera settings')
    else:   
        print('Starting...')
        mvm3r_pitch_FR(-16.52)
        position = centroid(q=None)[0]
        max_pitch=-16.39
        #print('position = '+str(position))
        while position < p:
            position = centroid(q=None)[0]
            if position < p-10:
                pitch = caget('29id_m3r:RY_POS_SP')
                mvm3r_pitch_FR(min(pitch + 0.005,max_pitch))
                #print(centroid(q=None)[4])
                position = centroid(q=None)[0]
                #print('position = '+str(position))
            elif  p-10<= position:
                pitch = caget('29id_m3r:RY_POS_SP')
                mvm3r_pitch_FR(min(pitch + 0.001,max_pitch))
                #print(centroid(q=None)[4])
                position = centroid(q=None)[0]
                #print('position = '+str(position))
        print('Done')
        print(centroid())
        print('\n')

    
def GoToSlit1AScribe():
    """Moves to Scribe Marks
    """
    Close_MainShutter()
    for m in range(9,13):
        caput('29idb:m'+str(m)+'.DVAL',0)


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

    
    
"""def ID_SP(hv):
    coefs=np.array([-1.03236075e+00,9.35232601e-1,4.35940038e-5])
    IDsp=coefs[0]*hv**0+coefs[1]*hv**1+coefs[2]*hv**2
    return IDsp

"""

def read_dict(FileName,FilePath="/home/beams22/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/"):
    with open(join(FilePath, FileName)) as f:
        for c,line in enumerate(f.readlines()):
            if line[0] == '=':
                lastdate=line[8:16]
            lastline=line
        mydict=ast.literal_eval(lastline)
    return mydict



def ID_Coef(grt,mode,hv):    # Mode = state (0=RCP,1=LCP,2=V,3=H); 
    
    """Return the ID coeff for a given polarization mode and energy;
    with Mode = 0 (RCP),1 (LCP), 2 (V), 3 (H).
    Current coefficient dictionary:
        /home/beams22/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/Dict_IDCal.txt
    """

    
    def ListRange(grt,mode,IDdict):  # extract the list of break pts for a given mode/grt 
        tmp_list=[]
        for item in (IDdict[grt][mode]):
            tmp_list.append(item[0])  
        return tmp_list


    def FindRange(hv,range_list):         # returns the index for the corresponding range
        B = [x - hv for x in range_list]
        index = [i for (i, x) in enumerate(B) if x > 0]
        return(index[0])
    
    try:
        #FRPath = '/Users/fannysimoes/Box/6-Python/MyPython/Macros_29id/'   #   FR hardcoded
        ID_function=read_dict(FileName='Dict_IDCal.txt')
    
    except KeyError:
        print("Unable to read dictionary") 
        
    try:   
        Lrange = ListRange(grt,mode,ID_function)
        Erange = FindRange(hv,Lrange)
        K = ID_function[grt][mode][Erange][1]
        
    except KeyError:
        print("WARNING: PLease select one of the following:")
        print("        mode 0 = RCP")
        print("        mode 1 = LCP")
        print("        mode 2 = V")
        print("        mode 3 = H")
        
    return K



def ID_Calc(grt,mode,hv):    # Mode = state (0=RCP,1=LCP,2=V,3=H)
    """Calculate the ID SP for a given polarization mode and energy;
    with Mode = 0 (RCP),1 (LCP), 2 (V), 3 (H)"""
    if type(mode)== str:
        mode={'RCP':0,'LCP':1,'V':2,'H':3}[mode]
    try:
        K=ID_Coef(grt,mode,hv)
        #ID = K[0] + K[1]*hv**1 + K[2]*hv**2 + K[3]*hv**3 + K[4]*hv**4 + K[5]*hv**5
        ID=poly.polyval(hv,K)
    except KeyError:
        print("WARNING: PLease select one of the following:")
        print("        mode 0 = RCP")
        print("        mode 1 = LCP")
        print("        mode 2 = V")
        print("        mode 3 = H")
        ID=caget("ID29:EnergySeteV")
    return round(ID,1)




def ID_Range():      # mode = state (0=RCP,1=LCP,2=V,3=H)
    Mode=caget("ID29:ActualMode")
    GRT=caget("29idmono:GRT_DENSITY")
    ID_min=[400,400,440,250,250]
    ID_max=3800
    hv_min=[390,390,430,245,245]
    if GRT == 2400:
        hv_max=2000
    elif GRT == 1200:
        hv_max=3000
    return ID_min[Mode],hv_min[Mode],hv_max,ID_max


def Energy_Range(grating,IDmode):
    BL_range={}    #   Slit:PE
    BL_range["HEG"]  = { "H":(250,2000), "V":(440,2000), "RCP":(400,2000), "LCP":(400,2000)  }
    BL_range["MEG"]  = { "H":(250,2500), "V":(440,2500), "RCP":(400,2500), "LCP":(400,2500) }
    energy_min, energy_max = BL_range[grating][IDmode]
    return energy_min, energy_max





def Slit_Coef(n):
    if n == 1:
        pv='29id:k_slit1A'
        #Redshifted x (H):
        H0=2.3325
        H1=-.000936
        H2=2.4e-7
         #Redshifted z (V):
        V0=2.3935
        V1=-.0013442
        V2=3.18e-7
    if n == 2:
        pv='29id:k_slit2B'
        #Redshifted x (H):
        H0=3.61
        H1=-0.00186
        H2=5.2e-7
        #Redshifted z (V):
        V0=6.8075
        V1=-0.003929
        V2=9.5e-7
    K=H0,H1,H2,V0,V1,V2
    return pv,K







##############################################################################################################
################################             ID scripts             ##############################
##############################################################################################################




###### ID status / start / restart :


def Monitor_Beam(which='user'):
    """
    which = 'user' or 'staff'
    Edit bin/pvMailUser (user) or bin/pvMailSomething (staff) to have you right address (google "mycarrier sms email")

    """
    if which == 'staff':n='6'
    elif which == 'user':n='7'
    caput('29idb:userCalcOut'+n+'.DESC',"BEAM DUMP!!!")
    caput('29idb:userCalcOut'+n+'.A',0) #resetting
    while True:
        SR=caget("S:SRcurrentAI.VAL")
        if SR > 60:
            sleep(30)
        else:
            print("Beam lost")
            break
    caput('29idb:userCalcOut'+n+'.A',1) #triggering
    print('Sending text/email')
    sleep(5)
    caput('29idb:userCalcOut'+n+'.A',0) #resetting

    print('Sending text/email')


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


def ID_Ready(q=None):
    while True:
        checkready=caget("ID29:feedback.VAL")
        checkbusy=caget("ID29:BusyRecord")
        if (checkready!="Ready")|(checkbusy==1):
            sleep(2)
        else:
            break
    if q is None:
        print("ID Ready")

def ID_Stop():
    WaitForPermission()
    caput("ID29:Main_on_off.VAL",1,wait=True,timeout=18000)


def ID_Start(Mode):
    "Starts ID with a specific polarization; Mode = \"H\", \"V\", \"RCP\" or \"LCP\""
    WaitForPermission()
    print("Starting ID  -  "+dateandtime())
    caput("ID29:EnergySet.VAL",3.8)
    caput("ID29:Main_on_off.VAL",0,wait=True,timeout=18000)
    ID_Ready()
    Switch_IDMode(Mode)
    while True:
        SS1=caget("EPS:29:ID:SS1:POSITION")
        SS2=caget("EPS:29:ID:SS2:POSITION")
        PS2=caget("EPS:29:ID:PS2:POSITION")
        check=SS1*SS2*PS2
        if (check!=8):
            print("MAIN SHUTTER CLOSED !!!" , dateandtime())
            Open_MainShutter()
            sleep(60)
        else:
            print("Shutter is now open" , dateandtime())
            break


def ID_Restart():
    Mode=caget("ID29:ActualMode")
    print("Restarting ID", dateandtime())
    caput("ID29:Main_on_off.VAL",1,wait=True,timeout=18000)
    sleep(10)
    while True:
        RBV=caget("ID29:Energy.VAL")
        checkready=caget("ID29:feedback.VAL")
        checkbusy=caget("ID29:BusyRecord")
        if (checkready!="Ready") or (RBV < 3.7):
            sleep(2)
        elif ((checkready=="Ready") and (RBV > 3.7)) and (checkbusy=="Busy"):
            caput("ID29:Busy.VAL",0)
        else:
            break
    sleep(10)
    caput("ID29:EnergySet.VAL",3.8)
    caput("ID29:Main_on_off.VAL",0,wait=True,timeout=18000)
    ID_Ready()
    caput("ID29:DesiredMode.VAL",Mode,wait=True,timeout=18000)
    sleep(10)

    print("ID is back ON", dateandtime())




###### ID modes & quasiperiodicity :

def Check_IDMode(which):
    if which in ["RCP","LCP","V","H"]:
        Mode=ID_State2Mode("Mode",which)
        Check_MainShutter()
        ActualMode=caget("ID29:ActualMode")
        if Mode != ActualMode:
            print("Switching ID mode, please wait...")
            caput("ID29:DesiredMode.VAL",Mode,wait=True,timeout=18000)     # RCP
            ID_Ready()
    else:
        print("WARNING: Not a valid polarization mode, please select one of the following:")
        print(" \"RCP\", \"LCP\", \"H\", \"V\" ")


def Switch_IDMode(which):
    "Change ID polarization; which = \"H\", \"V\", \"RCP\" or \"LCP\""
    GRT=caget("29idmono:GRT_DENSITY")
    if which in ["RCP","LCP","V","H"]:
        Mode=ID_State2Mode("Mode",which)
        Check_MainShutter()
        ActualMode=caget("ID29:ActualMode")
        if Mode != ActualMode:
            print("Turning ID off...")
            ID_Stop()
            
            sleep(10)
            caput("ID29:EnergySet.VAL",3.8)
            caput("ID29:Main_on_off.VAL",0,wait=True,timeout=18000)
            print("Switching ID mode, please wait...")
            caput("ID29:DesiredMode.VAL",Mode,wait=True,timeout=18000)     # RCP
            ID_Ready()
        print("ID Mode:",which)
    else:
        print("WARNING: Not a valid polarization mode, please select one of the following:")
        print(" \"RCP\", \"LCP\", \"H\", \"V\" ")



def Switch_IDQP(energy,mode,QP):
    QP=max(70,QP)
    ID_Stop()
    caput("ID29:QuasiRatioIn.C",QP)
    ID_Start(mode)
    sleep(15)
    SetID_Raw(energy)
    Byq=caget("ID29:ByqRdbk")
    Vcoil=caget("ID29:ByRdbk.VAL")
    ratio=Byq/Vcoil
    ratio_RBV=caget("ID29:QuasiRatio.RVAL")
    print("QP ratio =", round(ratio,3)*100,"%")
    print("QP RBV   =", ratio_RBV,"%")
    sleep(15)


##### ID energy :

def SetID(hv):
    "Sets optimum ID set point for hv(eV) (max intensity)"
    Check_MainShutter()
    GRT=Check_Grating()
    hv_SP=round(SetRange(hv),3)
    ID_min=ID_Range()[0]
    if hv_SP == round(hv,2) and hv_SP < 3001:
        Mode=caget("ID29:ActualMode")
        ID_SP=max(ID_Calc(GRT,Mode,hv_SP),ID_min)
        ID_SP_RBV=round(caget("ID29:EnergySet.VAL"),4)*1000
        if ID_SP == ID_SP_RBV:                    # compare ID (eV)SP to the (keV)SP energy
            ID_RBV=caget("ID29:EnergyRBV")
            print("\nID SET : "+"%.1f" % ID_SP, "eV")
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            print(caget('ID29:TableDirection',as_string=True))
        else:
            caput("ID29:EnergyScanSeteV",ID_SP,wait=True,timeout=18000)
            sleep(1)
            caput("ID29:EnergyScanSeteV",ID_SP+0.001,wait=True,timeout=18000)

            ID_Ready()
            print("\nID SET : "+"%.1f" % ID_SP, "eV")
            sleep(5)
            ID_RBV=caget("ID29:EnergyRBV")
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            ID_DIF=abs(ID_RBV-ID_SP)
            ID_BW=ID_SP*0.095
            if ID_DIF>ID_BW:
                sleep(20)
                ID_RBV=caget("ID29:EnergyRBV")
                print("ID RBV : "+"%.1f" % ID_RBV, "eV")
                ID_DIF=abs(ID_RBV-ID_SP)
                if ID_DIF>ID_BW:
                    ID_Restart()
                    SetID_keV_pV(hv_SP)
            print(caget('ID29:TableDirection',as_string=True))
#    elif  2450 < hv_SP < 3000:
#        print("Not calibrated above 2450 eV. ID set point needs to be determined manually.")
    else:
        print("Please select a different energy.")

def SetID_keV_pV(hv_eV):
    "Sets optimum ID set point for hv(eV) (max intensity) using KeV PVs"
    Check_MainShutter()
    hv_SP=SetRange(hv_eV)                # check hv range
    GRT=Check_Grating()
    if hv_SP == hv_eV:
        Mode=caget("ID29:ActualMode")
        ID_SP=ID_Calc(GRT,Mode,hv_SP)/1000.0        # ID_SP in keV
        ID_SP_RBV=round(caget("ID29:EnergySet.VAL"),3)    # ID_SP_RBV in keV
        if ID_SP == ID_SP_RBV:                # checks if ID is already at the SP energy
            ID_RBV=caget("ID29:Energy.VAL")
            print("\nID SET : "+"%.3f" % ID_SP, "keV")
            print("ID RBV : "+"%.3f" % ID_RBV, "keV")
            print(caget('ID29:TableDirection',as_string=True))
        else:
            caput("ID29:EnergyScanSet",ID_SP,wait=True,timeout=18000)
            sleep(1)
            caput("ID29:EnergyScanSet",ID_SP+0.0001,wait=True,timeout=18000)
        
            ID_Ready()
            print("\nID SET : "+"%.3f" % ID_SP, "keV")
            sleep(5)
            ID_RBV=caget("ID29:Energy.VAL")
            print("ID RBV : "+"%.3f" % ID_RBV, "keV")
            ID_DIF=abs(ID_RBV-ID_SP)
            ID_BW=ID_SP*0.095
            if ID_DIF > ID_BW:
                sleep(20)
                ID_RBV=caget("ID29:Energy.VAL")
                print("\nID RBV : "+"%.3f" % ID_RBV, "keV")
                ID_DIF=abs(ID_RBV-ID_SP)
                if ID_DIF > ID_BW:
                    ID_Restart()
                    SetID_keV_pV(hv_eV)
            print(caget('ID29:TableDirection',as_string=True))
    else:
        print("Please select a different energy.")


def SetID_Raw(hv):
    "Sets the ID set point to a specific value (hv(eV)) which will not likely be optimum"
    Check_MainShutter()
    Mode=caget("ID29:ActualMode")
    Mode_RBV=("state",Mode)
    ID_min=ID_Range()[0]
    ID_max=ID_Range()[3]
    ID_SP=min(max(hv,ID_min),ID_max)*1.0
    if hv < ID_min or hv > ID_max:
        print("\nWARNING:Set point out of BL energy range !!!")
        print("Please select a different energy.")
    else:
        ID_SP_RBV=round(caget("ID29:EnergySet.VAL"),3)*1000
        if ID_SP == ID_SP_RBV:                # checks if ID is already at the SP energy
            ID_RBV=caget("ID29:EnergyRBV")
            print("ID SET : "+"%.1f" % ID_SP, "eV")
            #print "\nID SET : "+"%.1f" % ID_SP, "eV"
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            print(caget('ID29:TableDirection',as_string=True))
        else:
            caput("ID29:EnergyScanSet.VAL",ID_SP/1000,wait=True,timeout=18000)
            sleep(1)
            caput("ID29:EnergyScanSet.VAL",(ID_SP+0.001)/1000,wait=True,timeout=18000)
            caput('ID29:StartRamp.VAL',1)
            #caput("ID29:EnergyScanSeteV",ID_SP,wait=True,timeout=18000)
            ID_Ready(q='q')
            print("\nID SET : "+"%.1f" % ID_SP, "eV")
            sleep(5)
            ID_RBV=caget("ID29:EnergyRBV")
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            ID_DIF=abs(ID_RBV-ID_SP)
            ID_BW=ID_SP*0.095
            if ID_DIF>ID_BW:
                sleep(20)
                ID_RBV=caget("ID29:EnergyRBV")
                print("\nID RBV : "+"%.1f" % ID_RBV, "eV")
                ID_DIF=abs(ID_RBV-ID_SP)
                if ID_DIF>ID_BW:
                    ID_Restart()
                    SetID_Raw(hv)
            print(caget('ID29:TableDirection',as_string=True))








##############################################################################################################
################################             BL scripts             ##############################
##############################################################################################################



###### Shutters & branches:


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


def light(ON_OFF):
    if ON_OFF in ['On','on','ON']:
        light=0
    elif ON_OFF in ['Off','off','OFF']:
        light=1
    caput('29idd:Unidig1Bo0',light)
    print(("Turning light "+ON_OFF+"."))

def Close_MainShutter():
    caput("PC:29ID:FES_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing Main Shutter...")

def Close_BranchShutter():
    "Closes current branch shutter (based on deflecting mirror position)"
    branch=CheckBranch().upper()
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")

def Close_CShutter():
    branch="C"
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")

def Close_DShutter():
    branch="D"
    caput("PC:29ID:S"+branch+"S_CLOSE_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Shutter...")

def Close_CValve():
    branch="C"
    caput("29id:BLEPS:GV10:CLOSE.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Valve...")

def Close_DValve():
    branch="D"
    caput("29id:BLEPS:GV14:CLOSE.VAL",1,wait=True,timeout=18000)
    print("Closing "+branch+"-Valve...")


def Close_CBranch(**kwargs):
    """
    EA.off()
    Close_CShutter()
    Close_CValve()
    **kwargs
        EA="off"; turns off EA (None = doesn't check)
    """
    kwargs.setdefault("EA","off")
    if kwargs["EA"] == "off":
        EA.off()
    shutter=caget('PA:29ID:SCS_BLOCKING_BEAM.VAL',as_string=True)
    if shutter == 'OFF':  #OFF = beam not blocked = shutter open
        Close_CShutter()
    i=0
    while True:
        valve=caget('29id:BLEPS:GV10:OPENED:STS',as_string=True)
        if (valve=='GOOD'):
            sleep(10)
            Close_CValve()
            i+=1
            if i == 3:
                print("Can't close valve; check status")
                break
        elif (valve == 'BAD'):
            print('ARPES chamber valve now closed')
            break

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

def Close_RSoXS():
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
            print('V10D valve now closed -- REMEMBER TO CLOSE V12D BY UNPLUGGING!!!!')
            break

def Open_MainShutter():
    caput("PC:29ID:FES_OPEN_REQUEST.VAL",1, wait=True,timeout=180000)
    print("Opening Main Shutter...")

def Open_BranchShutter():
    "Opens current branch shutter (based on deflecting mirror position)"
    branch=CheckBranch().upper()
    status=caget("PA:29ID:S"+branch+"S_BLOCKING_BEAM.VAL")
    if status == "ON":
        caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
        print("Opening "+branch+"-Shutter...")
    elif status == "OFF":
        print(branch+"-Shutter already open...")

def Open_CShutter():
    branch="C"
    caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Opening "+branch+"-Shutter...")

def Open_DShutter():
    branch="D"
    caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Opening "+branch+"-Shutter...")

def Open_CValve():
    branch="C"
    shutter=caget('PA:29ID:SCS_BLOCKING_BEAM.VAL')
    if shutter == 'OFF':  #OFF = beam not blocked = shutter open
        print("Can't open valve with the shutter open.")
        print("Close the shutter and try again.")
    else:
        caput("29id:BLEPS:GV10:OPEN.VAL",1,wait=True,timeout=18000)
        print("Opening "+branch+"-Valve...")

def Open_DValve():
    branch="D"
    shutter=caget('PA:29ID:SDS_BLOCKING_BEAM.VAL')
    if shutter == 'OFF':  #OFF = beam not blocked = shutter open
        print("Can't open valve with the shutter open.")
        print("Close the shutter and try again.")
    else:
        caput("29id:BLEPS:GV14:OPEN.VAL",1,wait=True,timeout=18000)
        print("Opening "+branch+"-Valve...")

def Open_CBranch():
    shutter=caget('PA:29ID:SCS_BLOCKING_BEAM.VAL')
    if shutter == 'OFF':  #OFF = beam not blocked = shutter open
        Close_CShutter()
    i=0
    while True:
        valve=caget('29id:BLEPS:GV10:OPENED:STS')
        if (valve=='BAD'):
            sleep(10)
            Open_CValve()
            i+=1
            if i == 3:
                print("Can't open valve; check EPS screen")
                break
        elif (valve == 'GOOD'):
            print('ARPES chamber valve now opened')
            Open_CShutter
            break


def Open_DBranch():
    shutter=caget('PA:29ID:SDS_BLOCKING_BEAM.VAL')
    if shutter == 'OFF':  #OFF = beam not blocked = shutter open
        Close_DShutter()
    i=0
    while True:
        valve=caget('29id:BLEPS:GV14:OPENED:STS')
        if (valve=='BAD'):
            sleep(10)
            Open_DValve()
            i+=1
            if i == 3:
                print("Can't open valve; check EPS screen")
                break
        elif (valve == 'GOOD'):
            print('RSXS chamber valve now opened')
            Open_DShutter
            break





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



def Tweak_M3R(Motor_Name,val):
    """
        \"TX\" = lateral                 \"RX\" = Yaw
        \"TY\" = vertical                \"RY\" = Pitch
        \"TZ\" = longitudinal            \"RZ\" = Roll
    """
    motor_rbv="29id_m3r:"+Motor_Name+"_MON"
    motor_pv="29id_m3r:"+Motor_Name+"_POS_SP"
    old=round(caget(motor_rbv),3)
    print("Old pitch position:",old)
    caput(motor_pv,old+val)
    sleep(2)
    caput("29id_m3r:MOVE_CMD.PROC",1,wait=True,timeout=18000)
    sleep(2)
    while caget("29id_m3r:SYSTEM_STS")==0:
        sleep(.5)
    new=round(caget(motor_rbv),3)
    print("New pitch position:",new)

def Tweak_M3R_Pitch(sign):
    Motor_Name="RY"
    val=0.005
    if sign == "+":
        Tweak_M3R(Motor_Name,val)
    elif sign == "-":
        Tweak_M3R(Motor_Name,-val)

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




###### Diagnostics:

def AllDiag_dict():
    """
    Dictionary of Diagnostic positions In and Out by either motor number or name
    WARNING: When updating motor values, also update the following screens:
        - 29id_BL_Layout.ui               (for MeshD and DiodeC)
        - 29id_Diagnostic.ui
        - 29idd_graphic
    useage:       
        AllDiag_dict()['name'] returns dictionary motor:name
        AllDiag_dict()['motor'] returns dictionary name:motor   
        AllDiag_dict()['In'] returns dictionary motor:In position  (where val can be a list for multiple position)  
        AllDiag_dict()['Out'] returns dictionary motor:In position  
                motor=AllDiag_dict()['motor']['gas-cell']
                pos_in=AllDiag_dict()['In'][motor]
    """
    diag={}
    diag["In"]  = {                5:-55, 6:-46,          17:-56, 20:-30, 25:-56, 28:[-57,-71.25]}
                                                                                    
    diag["Out"] = {1:-4, 2:-10, 3:-4, 4:-4, 5:-20, 6:-20, 7:-20, 17:-20, 20:-21, 25:-20, 28:-20}    
    diag["name"]= {1:"H-wire", 2:"V-wire", 3:"H-Diagon", 4:"V-Diagon", 5:"W-mesh",
     6:"D2B", 7:"D3B", 17:"D4C/pre-slit", 20:"gas-cell", 25:"D4D/pre-slit", 28:"D5D/pre-RSXS"}
    diag["motor"]= {"H-wire":1, "V-wire":2, "H-Diagon":3, "V-Diagon":4,"W-mesh":5,
     "D2B":6, "D3B":7, "D4C":17, "gas-cell":20,"D4D":25,"D5D":28}
    return diag


def Diagnostic(which,In_Out):
    "Inserts/retracts a diagnostic(motor number or name) either = \"In\" or \"Out\""
    diag=AllDiag_dict()
    if type(which) is int:
        motor=which
        name=diag['name'][motor]
    else:
        name=which
        motor=diag["motor"][name]
    position=diag[In_Out][motor]

    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\n"+name+": "+ In_Out)

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

def AllDiagIn():
    "Inserts all diagnostic (meshes and diodes) for pinhole scans"
    diag=AllDiag_dict()
    for motor in list(diag["In"].keys()):
        position=diag["In"][motor]
        if type(position) == list:
            position=position[0]
        caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
        print('m'+str(motor)+' = '+str(position))
    print("All diagnostics in (meshes and diodes) for pinhole scans")

def AllMeshIn():
    "Inserts all diagnostic (meshes and gas-cell is out) for wire scans"
    diag=AllDiag_dict()
    for motor in list(diag["In"].keys()):
        position=diag["In"][motor]
        if type(position) == list:
            position=position[0]
        caput("29idb:m"+str(motor)+".VAL",position,timeout=18000)
        print('m'+str(motor)+' = '+str(position))
    print("All diagnostics in (meshes and diodes) for pinhole scans")

def MeshW(In_Out):
    "Inserts/retracts RSXS mesh (post-slit); arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=5; position=diag[In_Out][motor]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nD1A W-Mesh: "+ In_Out)


def DiodeC(In_Out):
    "Inserts/retracts ARPES (gas-cell) diode; arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=20; position=diag[In_Out][motor]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nARPES Diode: "+ In_Out)

def DiodeD(In_Out):
    "Inserts/retracts RSXS diode; arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=28; position=position=diag[In_Out][motor]
    if type(position) == list:
        position=position[1]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nRSXS Diode: "+ In_Out)


def MeshC(In_Out,which="postSlit"):
    "Inserts/retracts ARPES mesh (preSlit or postSlit); arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    if which == "postSlit":
        motor=20; position=-31
    elif which == "preSlit":
        motor=17; position=diag[In_Out][motor]

    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nD4C Au-Mesh: "+ In_Out)

def MeshD(In_Out):
    "Inserts/retracts RSXS mesh (post-slit); arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=28; position=position=diag[In_Out][motor]
    if type(position) == list:
        position=position[0]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nD5D Au-Mesh: "+ In_Out)



###### Energy & Gratings:


def SetRange(hv):
    Mode=caget("ID29:ActualMode")
    hv_min=ID_Range()[1]
    hv_max=ID_Range()[2]
    sleep(0.1)
    hv_SP=min(round(max(hv,hv_min)*1.0,3),hv_max)*1.0
    sleep(0.1)
#    if round(hv,1) != hv_SP:
    if hv < hv_min or hv > hv_max:
        print("\nWARNING: Set point out of BL energy range:")
    return hv_SP


def SetBL(hv,c=1):
    caput("29id:BeamlineEnergyAllow",'Disable',wait=True,timeout=18000)
    caput("29id:BeamlineEnergySet",hv,wait=True,timeout=18000)
    hv_SP=round(SetRange(hv),3)
    if hv_SP == round(hv,3):
        #if (hv>2250):
            #ActualMode=caget("ID29:ActualMode")
            #if(ActualMode<2):         #circular
                #print("Setting ID to second harmonic.")
        SetID(hv)
        SetMono(hv)
        SetSlit_BL(c2B=c,q='q')
        print("\n")
#        caput("29id:BeamlineEnergyAllow",'Enable',wait=True,timeout=18000)
    else:
        print("Please select a different energy.")


def SetMono(eV):
    GRT=Check_Grating()
    if GRT == "HEG":
        min_limit=120
        max_limit=2200
    elif GRT == "MEG":
        min_limit=120
        max_limit=3000
    eV = max(min_limit,eV)
    eV = min(max_limit,eV)
    caput("29idmono:ENERGY_SP",eV,wait=True,timeout=60)
    sleep(2.5)
    STS=Mono_Status()
    if STS >1:
            print("Mono error - resetting motor")
            caput("29idmonoMIR:P.STOP",1)
            caput("29idmonoGRT:P.STOP",1)
            sleep(1)
            caput("29idmono:ENERGY_SP",eV,wait=True,timeout=18000)
            sleep(2.5)
            caput("29idmono:ENERGY_SP",eV,wait=True,timeout=18000)
    print("Mono set to",str(eV),"eV")



def Mono_Status():
    MIR_Status=caget("29idmonoMIR:P_AXIS_STS")
    GRT_Status=caget("29idmonoGRT:P_AXIS_STS")
    Status=MIR_Status*GRT_Status
    return Status


def Check_Grating():
    GRTd=caget("29idmono:GRT_DENSITY")
    if GRTd == 1200:
        GRT = "MEG"
    elif GRTd == 2400:
        GRT = "HEG"
    return GRT


def Move_GRT(which):
    MonoeV=round(caget("29idmono:ENERGY_MON"),1)
    Current_Shutter=caget("EPS:29:ID:SS2:POSITION")
    if Current_Shutter!=1:
        Close_MainShutter()
        while caget("EPS:29:ID:SS2:POSITION")!=1:
               sleep(0.5)
    if which == "Imp_MEG":
           caput("29idmonoGRT_TYPE_SP",1,wait=True,timeout=18000)          # MEG Imp
           caput("29idmonoGRT:X_DCPL_CALC.PROC",1,wait=True,timeout=18000)
           while caget("29idmonoGRT:X.RBV")!=3.872:
               sleep(0.5)
    elif which == "HEG":
           caput("29idmonoGRT_TYPE_SP",2,wait=True,timeout=18000)          # HEG
           caput("29idmonoGRT:X_DCPL_CALC.PROC",1,wait=True,timeout=18000)
           while caget("29idmonoGRT:X.RBV")!=68.000:
               sleep(0.5)
    elif which == "MEG":
           caput("29idmonoGRT_TYPE_SP",3,wait=True,timeout=18000)          # MEG
           caput("29idmonoGRT:X_DCPL_CALC.PROC",1,wait=True,timeout=18000)
           while caget("29idmonoGRT:X.RBV")!=130.624:
               sleep(0.5)
    SetMono(MonoeV)
    if Current_Shutter!=1:
        Open_MainShutter()
        while caget("EPS:29:ID:PS2:POSITION")!=2:
               sleep(0.5)
    print("Mono Grating:",which)


def Switch_Grating(which):
    if which in ["HEG","MEG","Imp_MEG"]:
        print("\n")
        Actual_GRT=caget('29idmonoGRT_TYPE_MON')
        if which == "HEG":
            if Actual_GRT != 2:
                print("Switching grating, please wait...")
                caput("29idmonoGRT_TYPE_SP",2,wait=True,timeout=18000)         # HEG
                caput("29idb:gr:move",1,wait=True,timeout=18000)
                sleep(20)
                Current_GRT=caget('29idmonoGRT_TYPE_MON')
                if (Current_GRT!=2):
                    print("Failed - Switching grating again...")
                    Move_GRT(which)
                    SetSlit_BL()
                else:
                    print(dateandtime()," -  Current mono grating: HEG")
            else:
                print(dateandtime()," -  Current mono grating: HEG")
        elif which == "Imp_MEG":
#            print "Old MEG."
            if Actual_GRT != 1:
                print("Switching grating, please wait...")
                caput("29idmonoGRT_TYPE_SP",1,wait=True,timeout=18000)         # MEG
                caput("29idb:gr:move",1,wait=True,timeout=18000)
                sleep(2)
                Current_GRT=caget('29idmonoGRT_TYPE_MON')
                if (Current_GRT!=1):
                    print("Failed - Switching grating again...")
                    Move_GRT(which)
                    SetSlit_BL()
                else:
                    print(dateandtime()," -  Current mono grating: MEG Imp")
            else:
                print(dateandtime()," -  Current mono grating: MEG Imp")
        elif which == "MEG":  #JY MEG
#            print "JY MEG"
            if Actual_GRT != 3:
                print("Switching grating, please wait...")
                Move_GRT(which)
                #caput("29idb:gr:move",1,wait=True,timeout=18000)     missing the 3rd slot
                sleep(2)
                Current_GRT=caget('29idmonoGRT_TYPE_MON')
                if (Current_GRT!=3):
                    print("Failed - Switching grating again...")
                    Move_GRT(which)
                    SetSlit_BL()
                else:
                    print(dateandtime()," -  Current mono grating: MEG")
                Open_MainShutter()
            else:
                print(dateandtime()," -  Current mono grating: MEG")
        SetSlit_BL()
    else:
        print("WARNING: Not a valid grating name, please select one of the following:")
        print(" \"HEG\" for high resolution, \"MEG_JY\" for high flux \"MEG\" is soon to be obsolete ")



def Kill_Mono():
    caput("29idmonoMIR:P_KILL_CMD.PROC",1)
    caput("29idmonoGRT:P_KILL_CMD.PROC",1)
#    caput("29idmonoGRT:X_KILL_CMD.PROC",1)
    sleep(5)
    caput("29idmono:STOP_CMD.PROC",1)
#    caput("29idmonoGRT:X_HOME_CMD.PROC",1)


def Stop_Mono():
    caput("29idmono:STOP_CMD.PROC",1)
    sleep(5)

def Enable_Mono():
    caput("29idmonoGRT:X_ENA_CMD.PROC",1)
    caput("29idmonoGRT:P_ENA_CMD.PROC",1)
    caput("29idmonoMIR:X_ENA_CMD.PROC",1)
    caput("29idmonoMIR:P_ENA_CMD.PROC",1)




##############################################################################################################
###########################                      Scan Set-Up                  ######################
##############################################################################################################

def Print_Beeper(scanDIM=1):
    """Prints pv to copy/paste into the beeper"""
    branch=CheckBranch()
    if branch == "c":
        print("29idcEA:det1:Acquire")
    scanIOC=BL_ioc()
    pv="29id"+scanIOC+":scan"+str(scanDIM)+".FAZE"
    print(pv)
    print("ID29:BusyRecord")



### Abort Scan
def Scan_Abort(scanIOC,scanDIM):
    pv="29id"+scanIOC+":"
    caput("29id"+scanIOC+":AbortScans.PROC",0)
    





##JM says that the Scan_Kappa_Go and the Scan_Kappa_Motor_Go should be the same scanIOC=BL_ioc() or hard coded? xxxxx
def Scan_Kappa_Go(scanIOC='Kappa',scanDIM=1,**kwargs):
    """Starts the N dimension scan in the Kappa chamber (N=ScanDIM)
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)
    
def Scan_ARPES_Go(scanIOC='ARPES',scanDIM=1,**kwargs):
    """Starts the N dimension scan in the ARPES chamber (N=ScanDIM)
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs) 

def Scan_RSoXS_Go(scanIOC='RSoXS',scanDIM=1,**kwargs):
    """Starts the N dimension scan in the RSoXS chamber using the Kappa IOC (N=ScanDIM)
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)


def TEY():
    """
    Returns TEY from the branch specified by CheckBranch()
    """
    mybranch=CheckBranch()
    if mybranch == "c":
        tey=caget("29idc:ca1:read")   # changed for ca2
    elif mybranch == "d":
        tey=caget('29idMZ0:scaler1.S2')
    #tey=format(tey,'1.3e')
    return tey

def D3():
    d3=caget('29idMZ0:scaler1.S3')
    #d3=format(d3,'1.3e')
    return d3


def D4():
    d4=caget('29idMZ0:scaler1.S4')
    #d4=format(d4,'1.3e')
    return d4


def APD():
    apd=caget('29idMZ0:scaler1.S2')
    #apd=format(apd,'1.3e')
    return apd

def MCP():
    apd=caget('29idMZ0:scaler1.S5')
    #apd=format(apd,'1.3e')
    return apd


def CA14():    #JM added
    mesh=caget('29idb:ca14:read')
    #mesh=format(mesh,'1.3e')
    return mesh

def CA15():
    diode=caget('29idb:ca15:read')
    #diode=format(diode,'1.3e')
    return diode


def Clear_Scan_Positioners(scanIOC,scanDIM=1):
    """Clear all extra scan positioners"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    for i in range (1,5):
        caput(pv+".R"+str(i)+"PV","")
        caput(pv+".P"+str(i)+"PV","")
    print("\nAll extra positionners cleared")

def Clear_Scan_Detectors(scanIOC,scanDIM=1):
    """Clear all scan detectors"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    for i in range(1,10):
        caput(pv+".D0"+str(i)+"PV","")
    for i in range(10,71):
        caput(pv+".D"+str(i)+"PV","")
    print("\nAll detectors cleared")

def Clear_Scan_Triggers(scanIOC,scanDIM=1):
    """Clear all scan detectors triggers"""
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    for i in range(1,5):
        caput(pv+'.T'+str(i)+'PV',"")

def Scan_Empty_Go():#HERE need to not hard code
    scanIOC=BL_ioc()
    scanDim=1   
    Scan_FillIn("","",scanIOC,scanDim,0,1,1)     
    Scan_Go(scanIOC,scanDim=scanDim)
    caput("29id"+scanIOC+":saveData_subDir","2016_3/mda")





def Scan_Time_Go(duration_min,step_sec,scanIOC,scanDIM=1):
    stop=duration_min*60.0/step_sec
    
    Scan_FillIn("","time",scanIOC,scanDIM,1,stop,1)
    Detector_Default(scanIOC,scanDIM=1,BL_mode=1)
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    caput(pv+".DDLY",step_sec)
    caput(pv+ '.BSPV','')
    caput(pv+'.ASPV','')
    caput(pv+'.T1PV','29idb:ca5:read')
    print("Time scan - Settling time : "+str(step_sec))
    FileName = caget("29id"+scanIOC+":saveData_baseName",as_string=True)
    FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")
    print(FileName+str(FileNum)+" started at ", dateandtime())
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".EXSC",1)  #pushes scan button
    Scan_Progress('Kappa',scanDIM=scanDIM,q='quiet')
    print(FileName+str(FileNum)+" finished at ", dateandtime())
    Reset_Scan(scanIOC)




### Reset detectors in scan record:
def Reset_ScanAll(scanIOC, **kwargs):
    """
    Resets all the scanRecords (scanDIM=1,2,3,4) for a given IOC 
        uses Reset_Scan()
    **kwargs
        scaler='y', only for Kappa ioc
    """
    kwargs.setdefault("scaler",'y')
    for scanIOC in [1,2,3,4]:
        Reset_Scan(scanIOC,scaler=kwargs['scaler'],scanDIM=scanDIM)
    
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



### Fill Scan Record - 2nd positionner:
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

### Fill Scan Record - 3rd positionner:
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

def Scan_FillIn_Pos4(VAL,RBV,scanIOC,scanDIM,start,stop):
    Scan_Progress(scanIOC,scanDIM)
    start=start*1.0
    stop=stop*1.0
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    caput(pv+".P1SM","LINEAR")     
    caput(pv+".P4PV",VAL)
    caput(pv+".R4PV",RBV)
    caput(pv+".P4SP",start)
    caput(pv+".P4EP",stop)
    
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
    
def Scan_Reset_AfterTable(scanIOC,scanDIM):
    """
    resets positioner settling time 0.1
    sets all positionitonser to linear
    clears positioners
    """
    #Setting everything back
    scanPV="29id"+scanIOC+":scan"+str(scanDIM)
    caput(scanPV+".PDLY",0.1)
    for i in range(1,5):
        caput(scanPV+".P"+str(i)+"SM","LINEAR") 
    Clear_Scan_Positioners(scanIOC,scanDIM)
    
def Scan_MakeTable(StartStopStepLists):
    """
    Creates and returns a np.array with values based on StartStopStepList
    StartStopStepList is a list of lists defining regions for a table array
              StartStopStepList[[start1,stop1,step1],[start1,stop1,step1],...]
    Automatically removes duplicates and sorts into ascending order
    if you want descending
               myarray=XAS_Table(StartStopStepLists)[::-1]
    """
    table_array=np.array([])
    if type(StartStopStepLists) is not list:
        start=StartStopStepLists[0]
        stop=StartStopStepLists[1]
        step=StartStopStepLists[2]
        j=start
        while j<=stop:
            table_array=np.append(table_array, j)
            j+=step
    else:
        for i in range(0,len(StartStopStepLists)):
            start=StartStopStepLists[i][0]
            stop=StartStopStepLists[i][1]
            step=StartStopStepLists[i][2]
            j=start
            while j<=stop:
                table_array=np.append(table_array, j)
                j+=step
    table_array=np.unique(table_array)#removing duplicate
    table_array=np.sort(table_array) #sort into ascending order    
    return table_array



def CA_Autoscale(ca_ioc,ca_num,On_Off='On',gain=7):
    """
    On_Off= 'On' => Turns On the Autoscale; gain is irrelevant.
    On_Off= 'Off' => Turns Off the Autoscale with gain below:
            0 = 2nA
            1 = 20nA
            2 = 200nA
            3 = 2uA
            4 = 20uA
            5 = 200uA
            6 = 2mA
            7 = 20mA
    """
    pv="29id"+ca_ioc+":ca"+str(ca_num)
    caput(pv+":rangeAutoSet",On_Off)
    sleep(0.5)
    caput(pv+":rangeSet",gain)
    print(pv,"Autoscale",On_Off)
    if On_Off == 'Off':
            sleep(1)
            print("Gain set to:",caget(pv+":range",as_string=True))

def Reset_CA_all(rate="Slow"):
    for i in [1,2,3,4,5,9,10,12,13,14,15]:
        Reset_CA("b",i,rate)
    for i in [1,2]:
        Reset_CA("c",i,rate)
    #for i in [1,2,3,4,5]:
    for i in [2,3,4]:
        Reset_CA("d",i,rate)
    caput("29idb:ca5:read.SCAN","Passive")    # CA5 in passive
    print("\nAll the current amplifiers have been reset; ca5 set to passive.")



def CA_Name(ca_ioc,ca_num):    #{motor,position}
    ca={}
    ca["b"] = {4:'Slit1A',13:'Slit3C',14:'MeshD',15:'DiodeC'}
    ca["c"] = {1:'TEY'   ,2:'Diode'}
    ca["d"] = {1:'APD'   ,2:'TEY',  3:'D-3',  4:'D-4',5:'RSoXS Diode'}
    try:
        name=ca[ca_ioc][ca_num]
    except:
        name=""
    return name


def CA_Filter(ca_ioc,ca_num,avg_pts,rate,quiet=None,scanDIM=1):
    scanIOC=BL_ioc()
    pv="29id"+ca_ioc+":ca"+str(ca_num)
    pvscan="29id"+scanIOC+":scan"+str(scanDIM)
    name=CA_Name(ca_ioc,ca_num)
    t=0.1
    if rate == "Slow":
        t=6/60.0
    elif rate == "Medium":
        t=1/60.0
    elif rate == "Fast":
        t=0.1/60.0
    settling=round(max(0.15,avg_pts*t+0.1),2)
    if avg_pts  <= 1:
        Reset_CA(ca_ioc,ca_num,rate)    # change for Reset_CA(ca_ioc,ca_num) if we want to
        caput(pvscan+".DDLY",0.15)    # reset to default reset speed ie slow
        if not quiet:
            print("Average disabled: "+name+" - "+pv)
            print("Detector settling time ("+pvscan+") set to: 0.15s")
    else:
        caput(pv+":read.SCAN","Passive",wait=True,timeout=500)
        caput(pv+":rateSet",rate)
        sleep(1)
        caput(pv+":digitalFilterCountSet",avg_pts,wait=True,timeout=500)
        caput(pv+":digitalFilterControlSet","Repeat",wait=True,timeout=500)
        caput(pv+":digitalFilterSet","On",wait=True,timeout=500)
        caput(pvscan+".DDLY",settling)
        caput(pv+":read.SCAN","Passive",wait=True,timeout=500)
        if not quiet:
            print("Average enabled: "+name+" - "+pv)
            print("Detector settling time ("+pvscan+") set to: "+str(settling)+"s")




def CA_Average(avg_pts,quiet='q',rate="Slow",scanDIM=1):
    """
    Average reading of the relevant current amplifiers for the current scanIOC/branch.
    By default it is chatty (i.e. quiet argument not specified).
    To make it quiet, specify quiet=''.
    """
    print("\nAverage set to:   "+str(max(avg_pts,1)))
    CA_list=Detector_List(BL_ioc())
    n=len(CA_list)-1
    for i in RangeUp(0,n,1):
        ca_ioc=CA_list[i][0]
        ca_num=CA_list[i][1]
        CA_Filter(ca_ioc,ca_num,avg_pts,rate,quiet,scanDIM)



def CA_Passive():        # Put All commonly used (triggered) CA in passive mode - legacy
    caput("29idc:ca1:read.SCAN","Passive")
    caput("29idd:ca2:read.SCAN","Passive")
    caput("29idd:ca3:read.SCAN","Passive")
    caput("29idd:ca4:read.SCAN","Passive")
    #caput("29idd:ca5:read.SCAN","Passive")
    caput("29idb:ca14:read.SCAN","Passive")
    caput("29idb:ca15:read.SCAN","Passive")
    caput("29idd:ca4:read.SCAN","Passive")
    caput("29idb:ca5:read.SCAN","Passive")
    caput("29idc:ca2:read.SCAN","Passive")

def ScalerInt(time):
    """
    Sets the integration time for the scalers
    """
    pv="29idMZ0:scaler1.TP"
    caput(pv,time)
#     if time>=1:
#         caput('29iddMPA:Proc1:NumFilter',floor(time))
#     else:
#         caput('29iddMPA:Proc1:NumFilter',1)
    caput('29iddMPA:Proc1:NumFilter',floor(time))
    print("Integration time set to:", str(time))


def cts(time):
    """
    Sets the integration time for the scalers
    """
    ScalerInt(time)



def Reset_Lakeshore():
    caput("29idARPES:LS335:TC1:read.SCAN",".5 second")
    caput("29idARPES:LS335:TC1:OUT1:Cntrl","A")
    caput("29idARPES:LS335:TC1:OUT2:Cntrl","B")
    caput("29idARPES:LS335:TC1:OUT1:Mode","Closed Loop")
    print("Lakeshore parameters have been reset.")





def Detector_List(scanIOC):
    """
    Define the detector used for:
        CA_Live_StrSeq()
        Detector_Triggers_StrSeq()
        BeforeScan_StrSeq() => puts everybody in passive
        CA_Average()
    WARNING: can't have more than 5 otherwise CA_Live_StrSeq gets angry.
    """

    BL_mode=BL_Mode_Read()[0]
    if scanIOC == "ARPES":
        CA_list=[["c",1],["b",15],["b",4],["b",13]]
    elif scanIOC == "Kappa":
        CA_list=[["d",2],["d",3],["d",4],["b",14]]
    elif scanIOC == "RSoXS":
        CA_list=[["d",3],["d",4],["d",5],["b",14],]
    else:
        CA_list=[]
#    if BL_mode == 1:
#        CA_list=[["b",1],["b",2],["b",3],["b",4],["b",5]] #JM was here
#        CA_list=[["b",15],["d",2],["d",3],["d",4],["b",14]]
    return CA_list





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








def UserAvg(average_pts):
    scanIOC=BL_ioc()
    for n in RangeUp(1,10,1):
        avg_pv="29id"+scanIOC+":userAve"+str(n)
        det_pv="29id"+scanIOC+":scan1.D"+str(60+n)+"PV"
        if average_pts > 0:
            caput("29id"+scanIOC+":scan1.T2PV","29id"+scanIOC+":userStringSeq8.PROC")     #set all Avg as Det
            caput(avg_pv+".A",average_pts)
            caput(det_pv,avg_pv+".VAL")
        elif average_pts == 0:
            caput("29id"+scanIOC+":scan1.T2PV","")
            caput(det_pv,"")
    if average_pts > 0:
        print("User Average enabled")
    elif average_pts == 0:
        print("User Average disabled")


def UserAvg_Setup(pv,average_num,average_pts,name,mode="ONE-SHOT"):
    scanIOC=BL_ioc()
    avg_pv="29id"+scanIOC+":userAve"+str(average_num)
    UserAvg_Trigger_StrSeq(scanIOC,average_num)
    # Fill User Average:
    UserAvg_PV(pv,average_num,10,name,mode)
    print(avg_pv+":",pv)

##############################################################################################################
###########################                    Basic scans                  ######################
##############################################################################################################


### BL Energy (ID+mono):

def Scan_SetTime(sec):
    scanIOC=BL_ioc()
    caput("29id"+scanIOC+":scan1.PDLY",sec)

def Scan_ID(scanDIM,start,stop,step):
    scanIOC=BL_ioc()
    VAL="ID29:EnergyScanSeteV"
    RBV="ID29:EnergySetRBV"
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)

def Scan_Mono(scanDIM,start,stop,step,settling_time=0.2):
    """Sets (but does NOT starts) a mono scan for a given scan dimension"""
    scanIOC=BL_ioc()
    VAL="29idmono:ENERGY_SP"
    RBV="29idmono:ENERGY_MON"
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)

def Scan_Mono_Go(scanDIM,start,stop,step,settling_time=0.2,**kwargs):
    """Starts a mono scan for a given scan dimension
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details       
    """
    scanIOC=BL_ioc()
    current_energy=caget('29idmono:ENERGY_SP')
    Scan_Mono(scanDIM,start,stop,step,settling_time)  
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)    
    SetMono(current_energy)


def Scan_BL(scanDIM,start,stop,step,settling_time=1):
    scanIOC=BL_ioc()
    caput("29id:BeamlineEnergyAllow",1)
    SetBL(start)
    sleep(10)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)    # positionner Settling time = 2s
    Scan_FillIn("29id:BeamlineEnergySet","",scanIOC,scanDIM,start,stop,step)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    print("WARNING: The ID is sloooow, Settling time set to "+str(settling_time)+" seconds")


def Scan_Energy_Go(scanDIM,start,stop,step,ID_offset=0,ID_parked=None,coef=1,settling_time=0.2,mesh='y',**kwargs):    # ID fixed at center energy
    """ Starts energy scan with fixed ID:
        => if ID_parked is NOT None, the ID will stay were it is.
        => if ID_parked IS None, the ID will move to:
                ID @ (stop-start)/2 + ID_offset
        => mesh='y': drops in the mesh for normalization (D branch only); retracts it at the end.
        => mesh='stay': to leave the mesh in after the scan is finished
        => mesh='n': no mesh.
    """
    current_energy=caget('29idmono:ENERGY_SP')
    print('ID_offset = '+str(ID_offset))
    scanIOC=BL_ioc()
    Branch=CheckBranch()
    if Branch=="d" and mesh=='y' or mesh== 'stay':
        MeshD("In")
        #print "error in MeshDIn()"
    center=(start+stop)/2.0+ID_offset
    if ID_parked is None:
        SetBL(center,coef)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)    # positionner Settling time = 0.2s
    print("WARNING: Settling time set to "+str(settling_time)+" seconds")
    Scan_Mono(scanDIM,start,stop,step,settling_time)   
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs) 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",0.1)    # positionner Settling time = 0.1s
    print("WARNING: Settling time back to 0.1 seconds")
    SetMono(current_energy)
    if Branch==("d"or "e") and mesh=='y':
        MeshD("Out")



##############################################################################################################
##############################             ARPES Motor Scan Set Up        ##############################
##############################################################################################################

##JM says that the Scan_Kappa_Go and the Scan_Kappa_Motor_Go should be the same scanIOC=BL_ioc() or hard coded? xxxxx

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


def Scan_ARPES_2D(InnerMotorList,OuterMotorList,**kwargs):
    """
    Fills in a the Scan Record for a 2D scan (Mesh),
    InnerMotorList=[name1,start1,stop1,step1] #scanDIM=2
    OuterMotorList=[name2,start2,stop2,step2] #scanDIM=3
        name = 'x'/'y'/'z'/'th'...    
    
    **kwargs
        mode="absolute"
        settling_time=0.1
        Snake; coming soon
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())
    kwargs.setdefault("mode","absolute")
    kwargs.setdefault("settling_time",0.1)
            
    if "Snake" in kwargs.keys():
        #SnakeScanSetup(scanIOC,1,Snake)
        print("Snake Coming Soon")
        
    name1,start1,stop1,step1=InnerMotorList
    name2,start2,stop2,step2= OuterMotorList  
    m1_RBV=ARPES_PVmotor(name1)[0]
    m1_VAL=ARPES_PVmotor(name1)[1]
    m2_RBV=ARPES_PVmotor(name2)[0]
    m2_VAL=ARPES_PVmotor(name2)[1]
    if kwargs["mode"] == "relative":
        current_value1=caget(m1_RBV)
        abs_start1=round(current_value1+start1,3)
        abs_stop1 =round(current_value1+stop1,3)
        current_value2=caget(m2_RBV)
        abs_start2=round(current_value2+start2,3)
        abs_stop2 =round(current_value2+stop2,3)
    else:
        abs_start1=start1
        abs_stop1 =stop1
        abs_start2=start2
        abs_stop2 =stop2
        print("start, stop, step = "+str(abs_start1)+", "+str(abs_stop1)+", "+str(step1)+", "+str(abs_start2)+", "+str(abs_stop2)+", "+str(step2))
    caput("29id"+kwargs["scanIOC"]+":scan1.PDLY",kwargs["settling_time"])
    Scan_FillIn(m1_VAL,m1_RBV,kwargs["scanIOC"],kwargs["scanDIM"],abs_start1,abs_stop1,step1)
    Scan_FillIn(m2_VAL,m2_RBV,kwargs["scanIOC"],kwargs["scanDIM"]+1,abs_start2,abs_stop2,step2)



def Scan_ARPES_2D_Go(InnerMotorList,OuterMotorList,**kwargs):
    """
    Fills in a the Scan Record for a 2D scan (mesh scan) and presses the scan go button
    InnerMotorList=[name1,start1,stop1,step1]
    OuterMotorList=[name2,start2,stop2,step2]
        name = 'x'/'y'/'z'/'th'...  
    
    **kwargs
        mode="absolute"
        settling_time=0.1
        scanIOC='ARPES'
        Snake=None,
    
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details      
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())
        
    Scan_ARPES_2D(InnerMotorList,OuterMotorList,**kwargs)   
    Scan_Go(kwargs["scanIOC"],kwargs["scanDIM"]+1)

def ARPES_PVextras(name):
    """
    used to get the PV associated with a given pnuemonic
    used with ARPES_PVmotor only have to change PVs in a single place
    name = "SES_slit", "TA", "TB", tey1", "tey2" 
    """
    dict={
        "SES_slit":"29idc:m8.RBV",
        "TA":"29idARPES:LS335:TC1:IN1", 
        "TB":"29idARPES:LS335:TC1:IN2",
        "tey1":"29idc:ca1:read",
        "tey2":"29idc:ca2:read",
    }
    return dict[name]


def ARPES_scanDIM():
    """
    sets the default scanDIM for ARPES (not 1 due to sweeps)
    """
    scanDIM=1
    return scanDIM



def Reset_Motor_ARPES(name):
    ''' Reset motor for the ARPES manipulator:
            name = 'x','y' 'z','th','chi','phi'
    '''
    pv=ARPES_PVmotor(name)[2]
    caput(pv,'Stop')
    sleep(1)
    caput(pv,'Go')

def Move_ARPES_focus(val):
    """ Moves APPES x and compensates y motor so that the beam stays in the same sample position 
    """
    xval=val    
    yval=val*tan(55/180*pi)+caget(ARPES_PVmotor('y')[0])
    Move_ARPES_Motor("x",xval)
    Move_ARPES_Motor("y",yval)
    return xval,yval

def Scan_ARPES_Focus(x_start,x_stop,x_step,mode='absolute',**kwargs):
    """Scans APPES x and compensates y motor so that the beam stays in the same sample position
    y=x*tan(55)
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details          
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",ARPES_scanDIM())
    scanIOC=kwargs['scanIOC']
    scanDIM=kwargs['scanDIM']

    x_VAL=ARPES_PVmotor('x')[1]
    x_RBV=ARPES_PVmotor('x')[0]
    y_VAL=ARPES_PVmotor('y')[1]
    y_RBV=ARPES_PVmotor('y')[0]
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    Scan_Progress(scanIOC,scanDIM)
    x_current=caget(x_RBV)
    if mode == 'relative':
        x_start=x_current+x_start*1.0
        x_stop=x_current+x_stop*1.0
    x_step=x_step*1.0
    y_start=x_start*tan(55/180*pi)
    y_stop=x_stop*tan(55/180*pi)
    print("\nx start/stop/step = ",x_start,x_stop,x_step)
    print("y start/stop/step = ",y_start,y_stop)
    print("\nDon't forget to clear extra positionners at the end of the scan if you were to abort the script using the function:")
    print(" Clear_Scan_Positioners(\'"+scanIOC+"\',"+str(scanDIM)+")")
    Scan_FillIn(x_VAL,x_RBV,kwargs["scanIOC"],kwargs["scanDIM"],x_start,x_stop,x_step)
    Scan_FillIn_Pos2(y_VAL,y_RBV,kwargs["scanIOC"],kwargs["scanDIM"],y_start,y_stop)  
    Scan_Go(kwargs["scanIOC"],kwargs["scanDIM"])
    Clear_Scan_Positioners(kwargs["scanIOC"],kwargs["scanDIM"])
    
    
    
def ARPES_Scan_Clear_StringSeq():
    n=6
    scanIOC="ARPES"
    ClearStringSeq(scanIOC,n)
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    caput(pvstr+".DESC","ARPES_Scan_Clear")
    caput(pvstr+".LNK1","29idARPES:scan1.T2PV PP")
    caput(pvstr+".STR1","")
    caput(pvstr+".LNK2","29idARPES:userStringSeq7.PROC PP")
    caput(pvstr+".STR2","1")
    caput(pvstr+".LNK3","29idARPES:scan1.CMND PP")
    caput(pvstr+".STR3","6")
    caput(pvstr+".LNK4","29idARPES:scan2.CMND PP")
    caput(pvstr+".STR4","6")
    caput(pvstr+".LNK5","29idARPES:scan3.CMND PP")
    caput(pvstr+".STR5","6")
    caput(pvstr+".LNK6","29idARPES:scan4.CMND PP")
    caput(pvstr+".STR6","6")
    
def ARPES_EA_Trigger_StringCalc():
    n=1
    scanIOC="ARPES"
    ClearStringSeq(scanIOC,n)
    pvstr="29id"+scanIOC+":userStringCalc"+str(n)
    caput(pvstr+".DESC","ARPRES_EATriggerCalc")
    caput(pvstr+".INAA","29idARPES:scan1.T2PV PP")
    caput(pvstr+".CALC$",'AA="29idcScienta:HV:ScanTrigger"')

##############################################################################################################
##############################             Kappa - Motor Scan Setting        ##############################
##############################################################################################################

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




def scanth2th_table(start,stop,step,th0,settling_time=0.2,ct=1,scanIOC='Kappa',scanDIM=1,**kwargs):
    """
    Create a table for tth, e.g.:
        mytable_tth=[]
        for q in range(2,41,1):
            mytable_tth.append(q)
        print(mytable_tth)
        
    th0 = th value at grazing incidence
    cts = counting time (default is 1s)
    
    Logging is automatic    
        **kwargs are the optional logging arguments see scanlog() for details
    """
    #caput('29idKappa:Kappa_sync.PROC',1)

    ScalerInt(ct)
    table_tth=np.asarray(table_tth)
    table_th=table_tth/2.0+th0

    #Using pyhkl to make motor table: 
    Scan_FillIn_Table('29idKappa:m9.VAL'     ,"29idKappa:m9.RBV"        ,scanIOC, scanDIM, table_tth,   posNum=1)
    Scan_FillIn_Table('29idKappa:Euler_Theta',"29idKappa:Euler_ThetaRBV",scanIOC, scanDIM, table_th, posNum=2)

    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)

    #Scanning
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)    

    #Setting everything back
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",0.1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P1SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P2SM","LINEAR") 

    # Need to clear positionner!
    Clear_Scan_Positioners(scanIOC)







def Scan_Kappa_2D_Go(InnerMotorList,OuterMotorList,**kwargs):
    """
    Fills in a the Scan Record for a 2D scan (mesh scan) and presses the scan go button
    InnerMotorList=[name1,start1,stop1,step1]
    OuterMotorList=[name2,start2,stop2,step2]
        name = 'x'/'y'/'z'/'th'...  
        
    **kwargs
        mode="absolute"
        settling_time=0.1
        scanIOC='ARPES'
        Snake=None,
    
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details      
    """
    if "scanIOC" in kwargs.keys():
        scanIOC = kwargs["scanIOC"]
    else:
        scanIOC=BL_ioc()
        
    Scan_Kappa_2D(InnerMotorList,OuterMotorList,scanIOC,**kwargs)
    Scan_Go(scanIOC,2,**kwargs)

def Scan_Kappa_2D(InnerMotorList,OuterMotorList,scanIOC,**kwargs):
    """
    Fills in a the Scan Record for a 2D scan (Mesh),
    InnerMotorList=[name1,start1,stop1,step1] #scanDIM=1
    OuterMotorList=[name2,start2,stop2,step2] #scanDIM=2
        name = 'x'/'y'/'z'/'th'...    
    
    **kwargs
        mode="absolute"
        settling_time=0.1
        Snake; coming soon
    """
    kwargs.setdefault("mode","absolute")
    kwargs.setdefault("settling_time",0.1)
            
    if "Snake" in kwargs.keys():
        #SnakeScanSetup(scanIOC,1,Snake)
        print("Snake Coming Soon")
    mode=kwargs["mode"]
    name1,start1,stop1,step1=InnerMotorList
    name2,start2,stop2,step2=OuterMotorList
    m1_RBV=Kappa_PVmotor(name1)[0]
    m1_VAL=Kappa_PVmotor(name1)[1]
    m2_RBV=Kappa_PVmotor(name2)[0]
    m2_VAL=Kappa_PVmotor(name2)[1]
    if mode == "relative":
        current_value1=caget(m1_RBV)
        abs_start1=round(current_value1+start1,3)
        abs_stop1 =round(current_value1+stop1,3)
        current_value2=caget(m2_RBV)
        abs_start2=round(current_value2+start2,3)
        abs_stop2 =round(current_value2+stop2,3)
    else:
        abs_start1=start1
        abs_stop1 =stop1
        abs_start2=start2
        abs_stop2 =stop2
    settling_time=kwargs["settling_time"]
    caput("29id"+scanIOC+":scan1.PDLY",settling_time)
    Scan_FillIn(m1_VAL,m1_RBV,scanIOC,1,abs_start1,abs_stop1,step1)
    Scan_FillIn(m2_VAL,m2_RBV,scanIOC,2,abs_start2,abs_stop2,step2)



def Move_Kappa_Motor(name,val):
    m_RBV=Kappa_PVmotor(name)[0]
    m_VAL=Kappa_PVmotor(name)[1]
    caput(m_VAL,val,wait=True,timeout=18000)




##############################################################################################################
##############################     General Area Detector            ##############################
##############################################################################################################
def AD_CurrentDirectory(ADplugin):
    """
    returns the current directory for area detector SavePlugin
    handles both Winodws and linux IOCs
    ADplugin = "29idc_ps1:TIFF1:"; $(P)$(SavePlugin)
    """
    SubDir=caget(ADplugin+"FilePath",as_string=True)
    if SubDir[0] == 'X':
        Dir='/net/s29data/export/data_29idb/'
        SubDir=SubDir.split('\\')[1:]
    elif SubDir[0] == 'Y':
        Dir='/net/s29data/export/data_29idc/'
        SubDir=SubDir.split('\\')[1:]
    elif SubDir[0] == 'Z':
        Dir='/net/s29data/export/data_29idd/'    
        SubDir=SubDir.split('\\')[1:]
    else: 
        Dir = SubDir
        SubDir=[]
    FilePath=join(Dir,*SubDir,'')
    return FilePath 

def AD_prefix(ADplugin):
    """
    returns the prefix for AreaDetector plugin based on ADplugin 
    """
    prefix = caget(ADplugin+"FileName_RBV",as_string=True)
    return prefix

def AD_EnableStats(ADplugin):
    """
    Enabling the statistics in an AreaDector
    ADplugin = "29idc_ps1:Stats1:"; (ADplugin=$(P)$(StatsPlugin))
    """
    caput(ADplugin+"EnableCallbacks","Enable")
    caput(ADplugin+"ComputeStatistics","Yes")
    caput(ADplugin+"ComputeCentroid","Yes")
    
    
    

def AD_SaveFileSetup(ADplugin,**kwargs):
    """    
    ADplugin = "29idc_ps1:TIFF1:" which IOC and which filesaving plugin
            (ADplugin=$(P)$(SavePlugin))
    uses to get the current MDA directory and then set the path to one up + /dtype
    MDA_CurrentDirectory(scanIOC=None)
    
    **kwargs (defaults)
        scanIOC = BL_ioc()
        userpath = extracted from ScanRecord unless specified
        subfolder = taken from ADplugin unless specified
            filepath = userpath/subfolder
        
        prefix = default same as subfolder
        ext = file extension is extracted for ADplugin unless specified
            (TIFF -> tif, HDF -> h5, ...)
        FileTemplate="%s%s_%4.4d."+ext; format for filename first %s = filepath, second %s = prefix
        
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("userpath",dirname(dirname(MDA_CurrentDirectory(BL_ioc()))))
    kwargs.setdefault("subfolder",ADplugin.split(":")[-2][:-1])

    kwargs.setdefault("prefix",ADplugin.split(":")[-2][:-1])
    extDict={"TIFF":".tif","HDF":"h5"}
    kwargs.setdefault("ext",ADplugin.split(":")[-2][:-1])
    kwargs.setdefault("FileTemplate","%s%s_%4.4d."+kwargs["ext"])
    
    kwargs.setdefault("debug",False)
    
    if kwargs['debug']:
        print("kwargs: ",kwargs)

    fpath=join(kwargs['userpath'],kwargs['subfolder'],'')
    print("\nFolder: " + fpath)
    if not (exists(fpath)):
        fileNumber=1
    else:
        fileNumber=getNextFileNumber(fpath,kwargs["prefix"])
    print("NextFile: "+str(fileNumber))
        
    caput(ADplugin+"FilePath",fpath)
    caput(ADplugin+"FileName",kwargs["prefix"])
    caput(ADplugin+"FileNumber",fileNumber)
    
    #setup AD
    caput(ADplugin+"FileTemplate",kwargs["FileTemplate"])
    caput(ADplugin+"AutoIncrement","Yes")
    caput(ADplugin+"AutoSave","Yes")
    
    
def AD_CurrentDirectory(ADplugin):
    """
    returns the current directory for area detector SavePlugin
    handles both Winodws and linux IOCs
    ADplugin = "29idc_ps1:TIFF1:"; $(P)$(SavePlugin)
    """
    SubDir=caget(ADplugin+"FilePath",as_string=True)
    if SubDir[0] == 'X':
        Dir='/net/s29data/export/data_29idb/'
        SubDir=SubDir.split('\\')[1:]
    elif SubDir[0] == 'Y':
        Dir='/net/s29data/export/data_29idc/'
        SubDir=SubDir.split('\\')[1:]
    elif SubDir[0] == 'Z':
        Dir='/net/s29data/export/data_29idd/'    
        SubDir=SubDir.split('\\')[1:]
    else: 
        Dir = SubDir
        SubDir=[]
    FilePath=join(Dir,*SubDir,'')
    return FilePath  

def AD_CurrentPrefix(ADplugin):
    """
    returns the prefix (without _) for area detector SavePlugin
    ADplugin = "29id_ps1:TIFF1:"; $(P)$(SavePlugin)
    """
    Prefix=caget(ADplugin+'FileName',as_string=True)
    return Prefix
   
def AD_CurrentRun(ADplugin):
    """
    returns the curent run specified in the filepath for area detector SavePlugin
    ADplugin = "29id_ps1:TIFF1:"; $(P)$(SavePlugin)
    """
    fpath=caget(ADplugin+"FilePath",as_string=True)
    current_run=re.findall("\d\d\d\d_\d", fpath)[0]
    return current_run
   
def AD_CurrentUser(ADplugin):
    """
    returns the curent user specified in the filepath for area detector SavePlugin
    ADplugin = "29id_ps1:TIFF1:"; $(P)$(SavePlugin)
    """
    SubDir=caget(ADplugin+":FilePath",as_string=True)
    if SubDir[0] == 'X':
        current_user='Staff'
    elif SubDir[0] == 'Y':
        m=SubDir.find(EA_CurrentRun())
        n=SubDir.find('/netCDF')
        current_user=SubDir[m+7:n]
    else: current_user=None
    return current_user

def AD_ScanTrigger(ADplugin,**kwargs):
    """
    Add Triggering of AreaDetector to scanIOC
    ADplugin = "29idc_ps1:TIFF1:" (ADplugin=$(P)$(SavePlugin))
    
    **kwargs
        scanIOC = "29id"+BL_ioc() if not specified
        scanDIM = 1
        P=first part of ADplugin if not specified
        R="cam1:"; other AD have "det1"
        detTrig = 2; detectorTrigger number
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    kwargs.setdefault("P",ADplugin.split(":")[0]+":")
    kwargs.setdefault("R","cam1:")
    kwargs.setdefault("detTrig",2)
    
    scanPV="29id"+kwargs["scanIOC"]+":scan"+str(kwargs["scanDIM"])    
    trigger=".T"+str(kwargs["detTrig"])+"PV"
    caput(scanPV+trigger,kwargs["P"]+kwargs["R"]+"Acquire")
    
def ADplugin_Scan(ADplugin, **kwargs):
    """
    stop the acquisition, puts in ImageMode=Single
    enables saving
    add to detector trigger
    Does not press go
    
    ADplugin = "29idc_ps1:TIFF1:"; (ADplugin=$(P)$(SavePlugin))
    **kwargs from 
    **kwargs
        # AD_ScanTrigger
        scanIOC = "29id"+BL_ioc() if not specified
        scanDIM = 1
        P=first part of ADplugin if not specified
        R="cam1:"; other AD have "det1:"
        detTrig = 2; detectorTrigger number
        
        # AD_SaveFileSetup
        filepath=userpath (from BL_ioc scanRecord)+"/dtype"
         (e.g. filepath="/net/s29data/export/data_29id"+folder+"/"+run+"/"+userName+"/"+df)
        dtype = taken from ADplugin
        FileTemplate="%s%s_%4.4d."+dtype; format for filename first %s = filepath, second %s = prefix
        prefix = dtype by default
    
    """
    #from AD_ScanTrigger
    kwargs.setdefault("P",ADplugin.split(":")[0]+":")
    kwargs.setdefault("R","cam1:")

    caput(kwargs["P"]+kwargs["R"]+"Acquire","Done")
    caput(kwargs["P"]+kwargs["R"]+"ImageMode","Single")
    AD_SaveFileSetup(ADplugin,**kwargs)
    AD_ScanTrigger(ADplugin, **kwargs)



def Cam_ScanSetup(scanDIM,camNUM):        #individual files saving
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    pvIOC="29id"+scanIOC+":"
    #beforscan
    Cam_SaveStrSeq(camNUM)
    caput(pvIOC+"scan"+str(scanDIM)+".BSPV",pvIOC+"userStringSeq2.PROC")
    #scan record (filename and trigger)
    nextfile=str(caget(pvIOC+"saveData_baseName"))+str(caget(pvIOC+"saveData_scanNumber"))
    filepath=caget(pvIOC+"saveData_fileSystem")
    filepath="/net"+filepath[1:len(filepath)]+"/tif"
    caput(pvCam+"TIFF1:FilePath",filepath)
    caput(pvCam+"TIFF1:FileName",nextfile)
    caput(pvCam+"TIFF1:FileWriteMode","Single")
    caput("29id"+scanIOC+":scan1.T2PV",pvCam+"cam1:Acquire")
    #afterscan
    Cam_FreeStrSeq(camNUM)
    caput(pvIOC+"scan"+str(scanDIM)+".ASPV",pvIOC+"userStringSeq1.PROC")
    caput(pvIOC+"scan1.ASCD",1)
    print("DON'T FORGET TO CLEAR SCAN RECORD AT THE END OF THE SCRIPT!!!!! ")
    print("Use Script: Cam_ScanClear(scanIOC,scanDIM)")



def Cam_FreeRun(camNUM):
    camNUM=str(camNUM)
    pv="29id_ps"+camNUM+":"
    caput(pv+"TIFF1:AutoSave",0)
    caput(pv+"TIFF1:EnableCallbacks",0)
    sleep(0.5)
    caput(pv+"cam1:ImageMode",2)
    caput(pv+"cam1:Acquire",1)
    caput(pv+"cam1:AcquireTime",0.015)
    caput(pv+"cam1:AcquirePeriod",0.030)
    print("Cam"+str(camNUM)+": Free run mode")





def Cam_SaveMode(camNUM):
    camNUM=str(camNUM)
    pv="29id_ps"+camNUM+":"
    caput(pv+"cam1:Acquire",0)
    sleep(0.5)
    caput(pv+"cam1:ImageMode",0)
    caput(pv+"TIFF1:AutoSave",1)
    caput(pv+"TIFF1:EnableCallbacks",1)
    caput(pv+"TIFF1:FileNumber",1)
    caput(pv+"cam1:AcquireTime",0.015)
    caput(pv+"cam1:AcquirePeriod",0.030)
    print("Cam"+str(camNUM)+": Saving mode")

def Cam_Start(camNUM):
    Cam_FreeRun(camNUM)

def Cam_Stop(camNUM):
    camNUM=str(camNUM)
    pv="29id_ps"+camNUM+":"
    caput(pv+"cam1:Acquire",0)



def Cam_ROI_SetUp(xstart,ystart,xsize,ysize,camNUM,roiNUM=1,binX=1,binY=1):
    pv="29id_ps"+str(camNUM)+":ROI"+str(roiNUM)+':'
    caput(pv+'MinX',xstart)
    caput(pv+'MinY',ystart)
    caput(pv+'SizeX',xsize)
    caput(pv+'SizeY',ysize)
    caput(pv+'BinX',binX)
    caput(pv+'BinY',binY)
    caput(pv+'EnableCallbacks','Enable')
    print(('ROI'+str(roiNUM)+' - '+caget(pv+'EnableCallbacks_RBV',as_string=True)))

def Cam_ROI_Stats(xstart,ystart,xsize,ysize,camNUM,roiNUM=1,binX=1,binY=1):
    pv="29id_ps"+str(camNUM)+":Stats1:"
    Cam_ROI_SetUp(xstart,ystart,xsize,ysize,camNUM,roiNUM,binX,binY)
    caput(pv+'EnableCallbacks','Enable')
    roi=caget(pv+'NDArrayPort_RBV',as_string=True)
    print((roi+' Stats => '+pv+'Total_RBV'))
    print('To set-up as detector use:')
    print('Cam_ROI_Det(detNUM,scanIOC,camNUM='+str(camNUM)+',roiNUM='+str(roiNUM)+')')
    
def Cam_ROI_Det(detNUM,scanIOC,camNUM,roiNUM,scanDIM=1):
    pvdet='29id'+scanIOC+':scan'+str(scanDIM)+'.D'+str(detNUM)+'PV'
    pvroi="29id_ps"+str(camNUM)+":Stats1:Total_RBV"
    caput(pvdet,pvroi)
    print('ROI stats set up as detector D'+str(detNUM)+' in '+scanIOC+' scan'+str(scanDIM))

### Scan Record Set-Up:

def Scan_Cam_Go(VAL,RBV,scanDIM,start,stop,step,camNUM):
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_Progress(scanIOC,scanDIM)
    Cam_ScanSetup(scanDIM,camNUM)

    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")

    # Scan_Go() without Before_After_Scan()
    BL_mode=BL_Mode_Read()[0]
    if BL_mode != 2:
        Check_MainShutter()
    FileName = caget("29id"+scanIOC+":saveData_baseName",as_string=True)
    FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")
    print(FileName+": #"+str(FileNum)+" started at ", dateandtime())
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".EXSC",1,wait=True,timeout=900000)  #pushes scan button
    print(FileName+": #"+str(FileNum)+" finished at ", dateandtime())

    Cam_ScanClear(scanIOC,scanDIM)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","PRIOR POS")

def Scan_Cam_Pos2_Go(VAL1,RBV1,VAL2,RBV2,scanDIM,start1,stop1,step1,start2,stop2,camNUM):
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    Cam_ScanSetup(scanDIM,camNUM)
    Scan_FillIn(VAL1,RBV1,scanIOC,scanDIM,start1,stop1,step1)
    Scan_FillIn_Pos2(VAL2,RBV2,scanIOC,scanDIM,start2,stop2)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    Scan_Go(scanIOC,scanDIM=1 )
    Cam_ScanClear(scanIOC,scanDIM)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","PRIOR POS")

def Cam_ScanClear(scanIOC,scanDIM):
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".BSPV","")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".ASPV","")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".T2PV","")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".DDLY",0.5)
    #print "Scan Record cleared from Camera Settings"



### Image Acquisition:

def TakeImageSetFolder(camNUM,NewFolder=""):
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    pvIOC="29id"+scanIOC+":"
    #beforscan
    Cam_SaveMode(camNUM)
    #FilePath
    filepath=caget(pvIOC+"saveData_fileSystem")+"/tif"
    filepath="/net"+filepath[1:len(filepath)]+"/"+NewFolder
    caput(pvCam+"TIFF1:FilePath",filepath)
    print("WARNING: Make sure NewFolder exists !!!")

def TakeImageSetFileNum(camNUM,n):
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    pvIOC="29id"+scanIOC+":"
    #beforscan
#    Cam_SaveMode(camNUM)
    #Filename
    if n<10:
        nextfile="29id"+scanIOC+"_000"+str(n)
    elif n<100:
        nextfile="29id"+scanIOC+"_00"+str(n)
    elif n<1000:
        nextfile="29id"+scanIOC+"_0"+str(n)
    elif n<10000:
        nextfile="29id"+scanIOC+"_"+str(n)
    caput(pvCam+"TIFF1:FileName",nextfile)
    caput(pvCam+"TIFF1:AutoIncrement",1)
    caput(pvCam+"TIFF1:FileNumber",2)

def TakeImageSetup(camNUM):
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    pvIOC="29id"+scanIOC+":"
    #beforscan
    Cam_SaveMode(camNUM)
    #Filename
    nextfile=str(caget(pvIOC+"saveData_baseName"))+str(caget(pvIOC+"saveData_scanNumber")-1)
    filepath=caget(pvIOC+"saveData_fileSystem")+"/tif"
    if scanIOC == "Test":
        filepath="/"+filepath[1:len(filepath)]        # for 29idTest
    else:
        filepath="/net"+filepath[1:len(filepath)]    # for 29idb/c/d

    caput(pvCam+"TIFF1:FilePath",filepath)
    caput(pvCam+"TIFF1:FileName",nextfile)
    #afterscan

def TakeImage(camNUM,AcqTime):
    AcqPeriode=AcqTime+0.040
    pvCam="29id_ps"+str(camNUM)+":"
    caput(pvCam+"cam1:AcquireTime",AcqTime)
    caput(pvCam+"cam1:AcquirePeriod",AcqPeriode)
    sleep(1)
    caput(pvCam+"cam1:Acquire",1,wait=True,timeout=500)
    sleep(1)
    TiffNum =caget(pvCam+"TIFF1:FileNumber_RBV")-1
    FileName= caget(pvCam+"TIFF1:FileName_RBV",as_string=True)
    print("\n"+FileName+": #"+str(TiffNum)+" started at ", dateandtime())
    print("\n================================================\n")






##############################################################################################################
##############################             Resolution              ##############################
#############################################################################################################



def Calc_BL_Resolution(GRT,hv,exitslit):
    res_function={}
    res_function[10]  = {"MEG":(-0.000800494,2.56761e-05,1.83724e-08,-1.69223e-12,0),          "HEG":(-0.000414482,1.07456e-05,8.79034e-09,-8.42361e-13,0)}
    res_function[20]  = {"MEG":(-0.00156643, 3.16894e-05,2.72121e-08,-2.63642e-12,0),          "HEG":(-0.00054591, 1.35647e-05,2.01775e-08,-4.30789e-12,5.70112e-16)}
    res_function[50]  = {"MEG":(-0.00251543, 4.89022e-05,7.70055e-08,-1.66358e-11,2.21272e-15),"HEG":(-0.00173081, 2.97625e-05,4.90646e-08,-1.0706e-11, 1.43011e-15)}
    res_function[100] = {"MEG":(-0.00545563, 9.14928e-05,1.51335e-07,-3.30332e-11,4.41314e-15),"HEG":(-0.00360316, 5.83265e-05,9.76881e-08,-2.13767e-11,2.85877e-15)}
    res_function[200] = {"MEG":(-0.0111658,  0.000179785,3.01277e-07,-6.59309e-11,8.81755e-15),"HEG":(-0.00728107, 0.000116055,1.95149e-07,-4.27331e-11,5.71638e-15)}
    try:
        a,b,c,d,e = res_function[exitslit][GRT]
        resolution=a+b*hv+c*hv**2+d*hv**3+e*hv**4
    except KeyError:
        print("WARNING: Slit size not listed, please choose one of the following:")
        print("        10, 20, 50, 100, 200 um.")
        resolution=0

    return resolution*1000


def Resolution_Mono(GRT,hv):
    if GRT == "MEG":
        K0=-2.3836
        K1=0.02083
        K2=7.8886e-06
    if GRT == "HEG":
        K0=-2.0984
        K1=0.011938
        K2=3.6397e-06
    Noise=K0+K1*hv+K2*hv**2
    return Noise


def Resolution_BL(grating,hv,slit_3C):
    M=Resolution_Mono(grating,hv)
    BL=Calc_BL_Resolution(grating,hv,slit_3C)
    resolution=sqrt(BL**2+M**2)
    print("BL   : "+"%.0f" % BL, "meV")
    print("Mono : "+"%.0f" % M, "meV")
    print("Total: "+"%.0f" % resolution, "meV")

def Resolution_ARPES(grating,hv,slit_3C,PE,slit_SES,T):
    M=Resolution_Mono(grating,hv)
    KbT=T*25/300
    BL=Calc_BL_Resolution(grating,hv,slit_3C)
    SES=Resolution_EA(PE,slit_SES)
    resolution=sqrt(BL**2+SES**2+KbT**2+M**2)
    print("BL   : "+"%.0f" % BL, "meV")
    print("Mono : "+"%.0f" % M, "meV")
    print("SES  : "+"%.0f" % SES, "meV")
    print("KbT  : "+"%.0f" % KbT, "meV")
    print("Total: "+"%.0f" % resolution, "meV")

def Resolution_BL_eff(grating,hv,slit_3C,PE,slit_SES,T,Ef):
    M=Resolution_Mono(grating,hv)
    KbT=T*25/300
    BL=Calc_BL_Resolution(grating,hv,slit_3C)
    SES=Resolution_EA(PE,slit_SES)
    resolution=sqrt(BL**2+SES**2+KbT**2+M**2)
    effective=sqrt(Ef**2-SES**2-KbT**2-M**2)
    print("BL_th : "+"%.0f" % BL, "meV            SES   : "+"%.0f" % SES, "meV")
    print("Mono  : "+"%.0f" % M, "meV            KbT   : "+"%.0f" % KbT, "meV")
    print("Total : "+"%.0f" % resolution, "meV            Fermi : "+"%.0f" % Ef, "meV")
    print("BL_eff: "+"%.0f" % effective, "meV")


def Resolution_BL_eff2(grating,hv,slit_3C,PE,slit_SES,T,Ef,Dirty_Au):
    M=Resolution_Mono(grating,hv)
    KbT=T*25/300
    BL=Calc_BL_Resolution(grating,hv,slit_3C)
    SES=Resolution_EA(PE,slit_SES)
    resolution=sqrt(BL**2+SES**2+KbT**2+M**2+Dirty_Au**2)
    effective=sqrt(Ef**2-SES**2-KbT**2-M**2-Dirty_Au**2)
    print("BL_th : "+"%.0f" % BL, "meV            SES   : "+"%.0f" % SES, "meV")
    print("Mono  : "+"%.0f" % M, "meV            KbT   : "+"%.0f" % KbT, "meV")
    print("Total : "+"%.0f" % resolution, "meV            Fermi : "+"%.0f" % Ef, "meV")
    print("BL_eff: "+"%.0f" % effective, "meV            Sample : "+"%.0f" % Dirty_Au, "meV")


##############################################################################################################
##############################             Slits Set-Up            ##############################
##############################################################################################################


def SyncAllSlits():
    caput("29idb:Slit1Hsync.PROC",1)
    caput("29idb:Slit1Vsync.PROC",1)
    caput("29idb:Slit2Hsync.PROC",1)
    caput("29idb:Slit2Vsync.PROC",1)
    caput("29idb:Slit4Vsync.PROC",1)
    caput("29idd:Slit4Hsync.PROC",1)
    caput("29idd:Slit4Vsync.PROC",1)
    caput("29idd:Slit5Hsync.PROC",1)
    caput("29idd:Slit5Vsync.PROC",1)




# SetSlits:
    
def SetSlit(n,Hsize=None,Vsize=None,Hcenter=0,Vcenter=0,q=None):
    
    if n == 1:
        if Hsize in [inf,nan,None]: Hsize=4.5
        if Vsize in [inf,nan,None]: Vsize=4.5
        SetSlit1A(Hsize,Vsize,Hcenter,Vcenter,q=None)
    elif n == 2:
        if Hsize in [inf,nan,None]: Hsize=6
        if Vsize in [inf,nan,None]: Vsize=8
        SetSlit2B(Hsize,Vsize,Hcenter,Vcenter,q=None)
    else:
        print('Not a valid slit number')
    
def SetSlit1A(Hsize,Vsize,Hcenter,Vcenter,q=None):
    caput("29idb:Slit1Hsync.PROC",1)
    caput("29idb:Slit1Vsync.PROC",1)
    caput("29idb:Slit1Hsize.VAL", Hsize)
    caput("29idb:Slit1Vsize.VAL", Vsize, wait=True,timeout=18000)
    caput("29idb:Slit1Hcenter.VAL",Hcenter)
    caput("29idb:Slit1Vcenter.VAL",Vcenter, wait=True,timeout=18000)
    if not q:
        print("Slit-1A = ("+str(round(Hsize,3))+"x"+str(round(Vsize,3))+") @ ("+str(Hcenter)+","+str(Vcenter)+")")

def SetSlit2B(Hsize,Vsize,Hcenter,Vcenter,q=None):
    caput("29idb:Slit2Hsync.PROC",1)
    caput("29idb:Slit2Vsync.PROC",1)
    caput("29idb:Slit2Hsize.VAL", Hsize)
    caput("29idb:Slit2Vsize.VAL", Vsize, wait=True,timeout=18000)
    caput("29idb:Slit2Hcenter.VAL",Hcenter)
    caput("29idb:Slit2Vcenter.VAL",Vcenter, wait=True,timeout=18000)
    if not q:
        print("Slit-2B = ("+str(Hsize)+"x"+str(Vsize)+") @ ("+str(Hcenter)+","+str(Vcenter)+")")



def SetSlit2B_Small(Hsize,Vsize,Hcenter,Vcenter,coef):
    caput("29idb:Slit2Hsync.PROC",1)
    caput("29idb:Slit2Vsync.PROC",1)
    #Hsize=caget("29idb:Slit2Ht2.C")
    #Vsize=caget("29idb:Slit2Vt2.C")
    #Hcenter=caget("29idb:Slit2Ht2.D")
    #Vcenter=caget("29idb:Slit2Vt2.D")
    caput("29idb:Slit2Hsize.VAL", Hsize*coef)
    caput("29idb:Slit2Vsize.VAL", Vsize*coef, wait=True,timeout=18000)
    caput("29idb:Slit2Hcenter.VAL",Hcenter)
    caput("29idb:Slit2Vcenter.VAL",Vcenter, wait=True,timeout=18000)
    print("\n\n !!! WARNING: closing Slit-2B down by a factor of", coef, "!!!")
    print("Slit-2B = ("+str(round(Hsize*coef,3))+"x"+str(round(Vsize*coef,3))+") @ ("+str(round(abs(Hcenter),0))+","+str(round(abs(Vcenter),0))+")")


# Slits Fits:

def Aperture_Fit(hv,n):
    K=Slit_Coef(n)[1]
    sizeH=K[0]+K[1]*hv+K[2]*hv*hv
    sizeV=K[3]+K[4]*hv+K[5]*hv*hv
    return [round(sizeH,3),round(sizeV,3)]


def Slit3C_Fit(size):
    K0=-36.383
    K1=0.16473
    K2=-0.00070276
    K3=8.4346e-06
    K4=-5.6215e-08
    K5=1.8223e-10
    K6=-2.2635e-13
    motor=K0+K1*size+K2*size**2+K3*size**3+K4*size**4+K5*size**5+K6*size**6
    return motor

def Slit3C_RBV():
    position=caget("29idb:m24.RBV")
    K0=299.66
    K1=16.404
    K2=1.5572
    K3=0.14102
    K4=0.0064767
    K5=0.00014501
    K6=1.2617e-06
    size=round(K0+K1*position+K2*position**2+K3*position**3+K4*position**4+K5*position**5+K6*position**6,0)
    return size


def SetSlit3C(size):
    position=round(Slit3C_Fit(size),1)
    caput("29idb:Slit3CFit.A",size,wait=True,timeout=18000)
    print("Slit-3C =",size,"um  -  ( m24 =",position,")")

def SetSlit3D(size,position=None):
    if position == None:
        position=round(caget('29idb:Slit4Vt2.D'),2)
    caput("29idb:Slit4Vcenter.VAL",position,wait=True,timeout=18000)
    caput("29idb:Slit4Vsize.VAL",size,wait=True,timeout=18000)
    print("Slit-3D =",size,"um")

def SetExitSlit(size):
    branch=CheckBranch()
    if branch == "c":
        SetSlit3C(size)
    elif branch == "d":
        SetSlit3D(size)

def Scan_Slit3D_center(start,stop,step,size=50,**kwargs):
    SetSlit3D(size)
    VAL="29idb:Slit4Vcenter.VAL"
    RBV="29idb:Slit4Vt2.D"
    Scan_FillIn(VAL,RBV,'Kappa',1,start,stop,step)
    Scan_Kappa_Go(**kwargs)

def Scan_Slit3D_size(start,stop,step,center=0,**kwargs):
    SetSlit3D(100,center)
    VAL="29idb:Slit4Vsize.VAL"
    RBV="29idb:Slit4Vt2.C"
    Scan_FillIn(VAL,RBV,'Kappa',1,start,stop,step)
    Scan_Kappa_Go(**kwargs)    
    

def Scan_D5D(start=-62.5,stop=-42.5,step=0.5,**kwargs):
    VAL="29idb:m28.VAL"
    RBV="29idb:m28.RBV"
    Scan_FillIn(VAL,RBV,'Kappa',1,start,stop,step)
    Scan_Kappa_Go(**kwargs)    




def SetSlit_BL(c2B=1,c1A=1,q=None):

    RBV=caget("29idmono:ENERGY_MON")
    GRT=caget("29idmono:GRT_DENSITY")
    hv=max(RBV,500)
    hv=min(RBV,2000)
    c=4.2/2.2

    if GRT==1200:
        GRT='MEG'
        V=0.65        #  set to 65% of RR calculation for both grt => cf 2016_2_summary
    elif GRT==2400:
        GRT='HEG'
        V=0.65*c        #  set to 65% of RR calculation (no longer 80%) => cf 2016_2_summary

    try:
        slit_position=read_dict(FileName='Dict_Slit.txt')
    except KeyError:
        print("Unable to read dictionary")
        return

    V2center= slit_position[GRT]['S2V']
    H2center= slit_position[GRT]['S2H']
    V1center= slit_position[GRT]['S1V']
    H1center= slit_position[GRT]['S1H']

    Size1A=( Aperture_Fit(hv,1)[0]*c1A,       Aperture_Fit(hv,1)[1]*c1A )
    Size2B=( Aperture_Fit(hv,2)[0]*c2B, round(Aperture_Fit(hv,2)[1]*c2B*V,3))
    SetSlit1A(Size1A[0],Size1A[1],H1center,V1center,q)    # standard operating
    SetSlit2B(Size2B[0],Size2B[1],H2center,V2center,q)




##############################################################################################################
####################################             Aborting scans              ##################################
##############################################################################################################


import signal
TIMEOUT = 5


def interrupted_b(signum, frame):
    "called when read times out"
    print('\nIs anybody out there???? (b)')
    #raise ValueError
signal.signal(signal.SIGALRM, interrupted_b)


def input_b(which):
    """ which = 'EA' or 'MDA' """
    try:
        print('\n\nWARNING: '+which+'Scan() stopped by operator.')
        print('Do you want to abort the scan (Y or N)? >')
        foo = input()
        return foo
    except KeyboardInterrupt as e:
        raise e
    except:
        # timeoutdef Get_SnapShot(which=None):
        return

def getUserInput_b(which):
    signal.alarm(TIMEOUT)
    try:
        s = input_b(which)
    except ValueError:
        print("\nInput has timed out!!!!!")
    except KeyboardInterrupt as e:
        print("\nUser wants to abort (b)!")
        s = False
        raise e
    finally:
        signal.alarm(0)              # if times out: reply_c == None    => True
    return s



###############################################################################################
####################################### FLUX CONVERSION #######################################
###############################################################################################




def LoadResponsivityCurve():
    FilePath='/home/beams/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/'
    FileName="DiodeResponsivityCurve"
    data = np.loadtxt(FilePath+FileName, delimiter=' ', skiprows=1)
    return data



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


def flux2ca(flux,hv=None,p=1):
    curve=LoadResponsivityCurve()
    responsivity=curve[:,0]
    energy=curve[:,1]
    charge = 1.602e-19
    if hv is None:
        hv=caget('29idmono:ENERGY_SP')
        print("\nCalculating current for:")
        print("   hv = %.1f eV" % hv)
        print("   flux = %.3e ph/s" % flux)
    eff=np.interp(hv,energy,responsivity)

    ca = flux*(eff*hv*charge)
    if p is not None:
        print("CA = %.3e Amp/n" % ca)
    return ca



##############################################################################################################
##############################     Resetting Motor Dial Position                    ##########################
##############################################################################################################


def Reset_Motor_Dial(m,motorIOC,value):
    pv='29id'+motorIOC+':m'+str(m)
    UL=caget(pv+'.DHLM')
    LL=caget(pv+'.DLLM')
    CV=caget(pv+'.DVAL')
    caput(pv+'.FOFF','Frozen')
    caput(pv+'.SET','Set')
    sleep(1)
    caput(pv+'.DVAL',value)
    sleep(1)
    caput(pv+'.SET','Use')
    caput(pv+'.FOFF','Variable')
    caput(pv+'.DHLM',UL-(CV-value))
    caput(pv+'.DLLM',LL-(CV-value))
    print('Don\'t forget to sync at the end!')


def Reset_Motor_User(m,motorIOC,value):
    pv='29id'+motorIOC+':m'+str(m)
    caput(pv+'.FOFF','Variable')
    caput(pv+'.SET','Set')
    sleep(1)
    caput(pv+'.VAL',value)
    sleep(1)
    caput(pv+'.SET','Use')
    print('Don\'t forget to sync at the end!')


##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################


######         ScanFunctions_BL.py:
#    - Start of the Run : Slit Calibration & Beam Steering
#    - Beam caracteristics curves (BL paper)
#    - Beam Profile (Mono vs Slits)
#     - Mono Calibration
#    - 4f vs Slits maps
#    - Pinholes
#    - ID calibration
#    - Beam Motion
#    - FMB / Mono Scripts: zero order, pink beam, alpha/beta
#    - Scan Bakeout
######    



##############################################################################################################
############################################          Shut down      #################################################
##############################################################################################################

def BL_Shutdown():
    BL_CloseAllShutters()
    BL_Valve_All(state="CLOSE")
    AllDiagOut()
    EA.zeroSupplies()
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


##############################################################################################################
##################             Slit Calibration & Beam Steering scripts                 ##################
##############################################################################################################


def Notes_from_20191212():
    print(""" looking at diode 3 in scattering chamber, open 3D all the way (2000)
        WARNING: 10% energy detune is enough to see the 2 lobes with 2B but not for 1A => 20% 
        Red shifted  (485eV) = edges give center of the grating
        Blue shifted (510eV) = gaussian center gives center of the beam
        => we want the slit centered on the grating center and the beam centered on the slits/grating
        => 5 urad down = 1 mm negative motion on 2B-V with HEG""")


def Procedure_Alignment_M1():
    print("""\n-Start with a very red shifted line cut to localize the edges of the grating:
                Set_IDraw(510)
                mono(485)
                Scan_NarrowSlit('2V',[0.25,-8,8,0.5])
                Scan_NarrowSlit('2H',[0.25,-4,4,0.5])
    => Verticaly: The edges/center of the grating define the center of 2V 
    => Horizontaly: The edges are defined by the aperture upstream. 
        As long as the beam makes it through the pipe to the next mirror, we are good. 
        Each M1 pitch will have its own slit-2H zero
        It can be a good idea to check that GRT or M2 translation does not change anything.
\n-Once the slits are centered on the grating, center resonant beam on the grating (zero slit):
                Get_Mirror(1)   # to get current values
                for roll in RangeUp(3,4,0.2):
                    print('\\n')
                    Move_M1('RZ',roll)
                    sleep(5)
                    Scan_MonoVsSlit('2V',[0.25,-0.5,0.5,0.25],[490,530,2])
                for pitch in RangeUp(8.5,8.7,0.05):
                    print('\\nMove_M1('RY',pitch)')
                    Move_M1('RY',pitch)
                    sleep(5)
                    Scan_MonoVsSlit('2H',[0.25,-0.5,0.5,0.25],[490,530,2])
    => The resonant beam is the slit value for the most blue shifted curve.
    
    WARNING: It is more accurate (and easier) to compare the leading edge of the ID peak 
    than trying to look at the perpendicular direction (slit line cut) because of the 
    asymetry in the beam intensity (uneven carbon strip along the grating?)
""")


    # 2017_3 - HEG after opitmization:  mba_b_0241-0244
    # 2018_1 - HEG before opitmization: mba_b_0005-0008

def StartOfTheWeek(GRT,branch,wait,**kwargs):
    """
    This should be run every at the start of every week; 50 min total.
    Switch to C-branch,.
    If wait='yes', wait for next day a 8:05.
    
    kwargs defaults:
        run = None: used today's date to set run appropriatetly 
        repeat = False: sets everything: switches branch, sets BL_Mode to Staff, resets scan/CAs/mono
        scanType = ['slit1','wire','flux','monoVslit']
        sound = False; no sounds
              = True => plays sound after Slit1A scans and when script is complete
    }
    steering out => move beam more positive (10 urad ~ 0.25 mm)
    steering up  => move beam more positive (10 urad ~ 0.25 mm)
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault('repeat',False)
    kwargs.setdefault('run',Check_run())
    kwargs.setdefault('scanType',['slit1','wire','flux','monoVslit'])
    kwargs.setdefault('sound',False)
    
    for scan in kwargs['scanType']: 
        if scan not in ['slit1','wire','flux','monoVslit']:
            print(scan+" is not a valid scan scanType=['slit1','wire','flux','monoVslit']")
            return
    
    scanIOC=kwargs['scanIOC']
    run=kwargs['run']
    
    if branch == 'c': 
        scanIOC='ARPES'
        CA_Autoscale('b',15,'Off',7) #turn off autoscaling on CA15
    elif branch == 'd': 
        scanIOC='Kappa'
        
    print("\n\n================== Sets Directory:")
    Check_Staff_Directory(**kwargs)
    FileName='StartOfTheWeek_log.txt'
    logname_set(FileName,scanIOC)
    FirstScan=None
    

    #Stuff that doesn't need beam & does not need to be run if repeating SoTW:

    print("\n\n================== Sets Beamline & Scans:")
    Switch_Grating(GRT)
    if not kwargs['repeat']:    
        Switch_Branch(branch)
        BL_Mode_Set('Staff')
        Reset_Scan(BL_ioc()); Reset_CA_all(); Reset_Mono_Limits()
        Get_All()
    
    shutter=caget('PA:29ID:S'+branch.upper()+'S_BLOCKING_BEAM.VAL')
    if shutter == 'ON':
        foo=input_d('Shutter '+branch.upper()+' is closed, do you want to open it (Y or N)? >')
        if foo == 'Y'.lower() or foo == 'y' or foo == 'yes'.lower():
            Open_BranchShutter()
        else:
            print('Aborting...')
            return

    
    AllDiagOut(DiodeStayIn=branch)

    if wait =='Y' or wait == 'y' or wait == 'yes'or wait == 'YES' or wait == True:
        t = datetime.datetime.today()
        if 0 <= t.hour <= 8:
            WaitForIt(0,8,5)
        else:    
            WaitForIt(1,8,5)

    print("\n\n================== Start ID:")
    ID_OnOff=caget('ID29:Main_on_off.VAL')
    if ID_OnOff==1:  # 0 = On, 1 = Off
        ID_Start('RCP')
    else:
        polarization('RCP')



    if not kwargs['repeat']:    
        logprint("\n\n================== Start Of The Week @ "+today('slash')+':\n',FileName=FileName)

    ###### Scan front-end slit center:
    
    if 'slit1' in kwargs['scanType']:
        print("\n\n================== Slit 1A scans:")
        SetID_Raw(2000)
        Scan_SlitCenter('1H',-3,3,0.1,comment='Slit center - 1H')
        FirstScan=MDA_GetLastFileNum()
        Scan_SlitCenter('1V',-3,3,0.1,comment='Slit center - 1V')
        SetSlit1A(4.5,4.5,0,0)
        if kwargs['sound']:
            playsound()

    ###### Wire scans: 
    if 'wire' in kwargs['scanType']:
        SetID_Raw(2000)
        SetSlit1A(4.5,4.5,0,0)
        WireScan('H',comment='Wire scan - H')     # by default puts all meshes in + DiodeC
        WireScan('V',comment='Wire scan - V')

    ###### Mono/slit scans: 
    if 'monoVslit' in kwargs['scanType']:
        if GRT=="HEG":
            slit(300)
        else:
            slit(200)
        print("\n\n================== Mono/slit scans:")
        mono(500)
        SetSlit_BL()
        AllDiagOut(DiodeStayIn=branch)
        SetID_Raw(500)
        Scan_MonoVsSlit('2V',[0.25,-2,2,0.5],[475,515,2],comment='Mono/Slit - 2V')    #10min
        Scan_MonoVsSlit('2H',[0.25,-2,2,0.5],[475,515,2],comment='Mono/Slit - 2H')    #10min
        Scan_MonoVsSlit('1V',[0.5,-0.75,0.75,0.25],[475,515,2],comment='Mono/Slit - 1V')    #10min
        Scan_MonoVsSlit('1H',[0.5,-0.75,0.75,0.25],[475,515,2],comment='Mono/Slit - 1H')    #10min
    
    ###### Check flux: 
    if 'flux' in kwargs['scanType']:
        print("\n\n================== Check Flux:")
        CheckFlux(stay='y')
        slit(50)
        energy(500)
        scanhv(475,525,1,comment='Mono Scan @ 500eV')
        AllDiagOut()

    print("\n\n================== All done:")
    print("\nDon't forget to put back the user folder !!!!")
    
    ###### Plotting instructions and return first scan number 
    if FirstScan is not None:
        logprint(comment="\nFirstScan = "+str(FirstScan))
        print('plot_StartOfTheWeek("'+branch+'",'+str(FirstScan)+')' )
    print('\nREMEMBER to update slit center using:     update_slit_dict()')
    
    if kwargs['sound']:
        playsound()
        
    return FirstScan
    

    

#####################################################################################
### Slit-1A Procedures
#####################################################################################

def Check_Slit1A(scanIOC=None,step=0.1):
    """
    Checks that Slit1A is centered on the fixed aperature/theoretical optic axis
        top='m9' -> CA5
        inboard='m10' -> CA4
        
    Scans the top blade - CA4 sees an step function
           top_center = midpoint of motor position for zero current and when current saturates
    Scans the inner blade - CA4 sees box fuction convoluted with gaussian beam position 
           inner_center - midpoint bewteen box edges
           
    SetSlit1A(0,0,inner_center,top_center)
    for m in range(9,13):
        Reset_Motor_User(m,'b',0)
    SyncAllSlits()  
    
    If data makes no sense then Reset_Slit1A_Procedure()
 
    """
    if scanIOC == None:
        scanIOC=BL_ioc()
   #scanning top-blade

    SetSlit1A(8,8,0,0)         # aperture wide open
    caput('29idb:m10.VAL',0)   # Inboard blade centered-ish in the beam
    m=9
    VAL='29idb:m'+str(m)+'.VAL'
    RBV='29idb:m'+str(m)+'.RBV'
    Scan_FillIn(VAL,RBV,'ARPES',1,-4,4.0,step)
    Scan_ARPES_Go()
    FileNum1  = caget("29id"+scanIOC+":saveData_scanNumber")-1

    #scanning inboard-blade
    SetSlit1A(8,8,0,0)         # aperture wide open
    caput('29idb:m9.VAL',0)    # top blade centered-ish  in the beam
    m=10
    VAL='29idb:m'+str(m)+'.VAL'
    RBV='29idb:m'+str(m)+'.RBV' 
    Scan_FillIn(VAL,RBV,'ARPES',1,-4,4.0,step)
    Scan_ARPES_Go()
    FileNum2  = caget("29id"+scanIOC+":saveData_scanNumber")-1
    return FileNum1, FileNum2


def Procedure_Reset_Slit1A():
    """
    Prints the procedure for Resetting Slit1A
    """
    print("\n#------- Checking and Resetting the Dial -------")
    print("    GoToSlit1AScribe()")
    print("# if not on the scribe marks tweek the position until the scribe marks are aligned")
    print("    for m in [9,10,11,12]: Reset_Motor_Dial(m,\'b\',0);SyncAllSlits()")
    print("\n#------- Resetting the User -------")
    print("# SetSlit1A by hand such that you have some beam coming through")
    print("    Scan_SlitSize(\"1H\",start,stop,step) #looking at CA4")
    print("    Scan_SlitSize(\"1V\",start,stop,step) #looking at CA4")
    print("# Then SetSlit1A(1Hsize,1Vsize,0,0); where 1Hsize and 1Vsize are the size where CA4 = 0")
    print("    for m in [9,10,11,12]: Reset_Motor_User(m,'b',0);SyncAllSlits()")
    

def Scan_SlitCenter(slit,start,stop,step,setslit=None,scanIOC=None,scanDIM=1,**kwargs):
    """
    Scans the slit center: 
    slit='1H','1V','2H' or '2V'
    Slit 1A is set to (0.25,0.25,0,0) unless setslit= not None
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    default: scanDIM=1  
    """
    if setslit is None:
        SetSlit1A(0.25,0.25,0,0)
        #SetSlit1A(4.5,4.5,0,0,'q')
        #SetSlit2B(6.0,8.0,0,0,'q')
    if scanIOC is None:
        scanIOC = BL_ioc()
    VAL='29idb:Slit'+slit+'center.VAL'
    RBV='29idb:Slit'+slit+'t2.D'   
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step) 
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)


def Scan_SlitSize(slit,start,stop,step,setslit=None,scanIOC=None,scanDIM=1,**kwargs):
    """
    Scans the slit center: 
    slit='1H','1V','2H' or '2V'
    Slit 1A is set to (1.75,1.75,0,0) unless setslit= not None
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    default: scanDIM=1  
    """
    if setslit is None:
        SetSlit1A(1.75,1.75,0,0)         #why is that?
        #SetSlit1A(4.5,4.5,0,0,'q')        # would open all the way?
        #SetSlit2B(6.0,8.0,0,0,'q')
    if scanIOC is None:
        scanIOC = BL_ioc()
    VAL='29idb:Slit'+slit+'size.VAL'
    RBV='29idb:Slit'+slit+'t2.C'   
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step) 
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)




    
def Check_ID_steering(hv=2000):
    """
    Scans Slit1A center (set to a (0.25,0.25) pinhole) while looking at the back blade:
        - slit center vs fixed aperture: given by the position of the edges
        - beam center vs fixed aperture: given by the position of the bump in the middle
    """
    SetSlit1A(0.25,0.25,0,0)
    SetID_Raw(hv)
    Scan_SlitCenter('1H',-3,3,0.1)
    Scan_SlitCenter('1V',-3,3,0.1)
        
        
#####################################################################################
# Checking the beam steering uses the gas-cell to see if the beam is centered on the grating
# and that the slits are centered
#####################################################################################

def BeamProfile(GRT,SlitList,c_slit=1,c_energy=1,scanIOC=None,**kwargs):
    """
        Makes a nice 2D image of the energy distribution of the beam across the grating at ID=500
        Does NOT put the diagnostics into the beam you need to run the following if you haven't already (AllDiagOut(); DiodeCIn())
        SlitList=["2H","2V","1H","1V"]
        c_slit  = scaling of step size (c=1   Slit-1: step = 0.25. Slit-2: step = 0.5)
        c_energy = scaling of mono step size ( c=1   eV step = 2)
        with c_slit=1 and c_energy = 1   Each slit ~ 1:10 min
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    Switch_Grating(GRT)
    GRT=caget("29idmono:GRT_DENSITY")
    c=GRT/1200
    ID=500
    eVstart,eVstop,eVstep=460,540,4
    for slit in SlitList:
        if slit=="1H":
            #Hsize,Vsize,Hstart,Hstop,Hstep = 0.50,2,-2,2,0.25*c_slit      # => 35 min
            #MonoVsSlit1AH_Go(ID,eVstart,eVstop,eVstep*c_energy,Hstart,Hstop,Hstep,Hsize,Vsize,scanIOC,**kwargs)
            Scan_MonoVsSlit('1H',[0.5,-2,2,0.25*c_slit],[eVstart,eVstop,eVstep],comment='Mono/Slit - 1H')
        elif slit == "1V":
            #Hsize,Vsize,Vstart,Vstop,Vstep = 2,0.50,-2,2,0.25*c_slit
            #MonoVsSlit1AV_Go(ID,eVstart,eVstop,eVstep*c_energy,Vstart,Vstop,Vstep,Hsize,Vsize,scanIOC,**kwargs)
            Scan_MonoVsSlit('1V',[0.5,-2,2,0.25*c_slit],[eVstart,eVstop,eVstep],comment='Mono/Slit - 1V')
        elif slit =="2H":
            #Hsize,Vsize,Hstart,Hstop,Hstep = 0.50,8,-3,3,0.5*c_slit
            #MonoVsSlit2BH_Go(ID,eVstart,eVstop,eVstep*c_energy,Hstart,Hstop,Hstep,Hsize,Vsize,scanIOC,**kwargs)
            Scan_MonoVsSlit('2H',[0.5,-3,3,0.5*c_slit],[eVstart,eVstop,eVstep],comment='Mono/Slit - 2H')
        elif slit =="2V":
            #Hsize,Vsize,Vstart,Vstop,Vstep = 6,0.25*c,-4*c,4*c,0.5*c_slit
            #MonoVsSlit2BV_Go(ID,eVstart,eVstop,eVstep*c_energy,Vstart,Vstop,Vstep,Hsize,Vsize,scanIOC,**kwargs)
            Scan_MonoVsSlit('2V',[0.5,-4,4,0.5*c_slit],[eVstart,eVstop,eVstep],comment='Mono/Slit - 2V')


def CheckAllSlits_long(hvList=[500],SlitList=["1H","1V","2H","2V"],scanIOC=None,**kwargs):
    """
    For each photon energy in hvList, takes 3 slit curves @ mono below / resonance / above
    For given SlitList
    For both gratings
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    for GRT in ["HEG","MEG"]:    # One full loop for a given grating and 3 energies takes 5h for average 20
        Switch_Grating(GRT)
        for hv in hvList:
            SetBL(hv)
            step=hv/100.0
            start=hv-step
            stop=hv+step
            for slit in SlitList:
                for hv in RangeUp(start,stop,step):
                    print("\r")
                    SetMono(hv)
                    CheckBeamPosition(slit,scanIOC,**kwargs)


def CheckSlitCalibration(slit_list,BL=500,hvList=[485,510],scanIOC=None,**kwargs):
    """
    Slit scan for red shifted and blue shifted mono values
    used to determine in the beam is centered on the grating (gaussian)
    and if the slits are centered on the grating (humped)
                 hv=500; hvList=[485,510]
                 hv=1500;hvList=[hv*0.97,hv*1.01]
    Note: sets the exit slit to 50
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    SetExitSlit(50)
    SetBL(BL)
    for hv in hvList:
        SetMono(hv)
        for slit in slit_list:
            CheckBeamPosition(slit,scanIOC=scanIOC,**kwargs)
        print("\n")

def CheckBeamPosition(slit,scanIOC=None,**kwargs):            # instead of the full 2D map, you get 3 vertical cuts which
    if scanIOC is None:
        scanIOC=BL_ioc()
    GRT=caget("29idmono:GRT_DENSITY")    # can be plotted directly on dview using the buffer. That should
    c=GRT/1200                # be fairly quick and not require any data loading/analysis
    SetSlit1A(3.5,3.5,0,0,'q')
    #SetSlit1A(4.5,4.5,0,0,'q')
    SetSlit2B(6.0,8.0,0,0,'q')        # Open up all the slits to make sure we scan the full beam
    if slit == "1H":
#        size,start,stop,step = 0.50,-2.5,2.5,0.1
        size,start,stop,step = 0.50,-4.5,4.5,0.2
    elif slit == "1V":
#        size,start,stop,step = 0.50,-2.5,2.5,0.1
        size,start,stop,step = 0.50,-4.5,4.5,0.2
    elif slit == "2H":
#        size,start,stop,step = 0.25,-3.0,3.0,0.1
        size,start,stop,step = 0.25,-8.0,8.0,0.2
    elif slit == "2V":
#        size,start,stop,step = 0.25,-3.5*c,3.5*c,0.1*c
        size,start,stop,step = 0.25*c,-4*c,4*c,0.2*c
    VAL ="29idb:Slit"+slit+"center.VAL"
    RBV ="29idb:Slit"+slit+"t2.D"
    caput("29idb:Slit"+slit+"size.VAL",size)
    print("\nScan "+slit+":")
    scanIOC = BL_ioc()
    scanDIM=1 
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)
    Scan_Go(scanIOC,scanDIM,**kwargs)
    SetSlit_BL(q='q')




def Reset_Slit2B_Encoders(Hcenter,Vcenter):
    """
    Resetting Slit 2B encoders to 0 for a given position (Hcenter,Vcenter).
    Slit size need to be set to 0.
    """
    SetSlit2B(0,0,Hcenter,Vcenter)
    print('\nCurrent Position:')
    print(('e13 = '+str(caget('29idMini1:e13Pos'))))
    print(('e14 = '+str(caget('29idMini1:e14Pos'))))
    print(('e15 = '+str(caget('29idMini1:e15Pos'))))
    print(('e16 = '+str(caget('29idMini1:e16Pos'))))
    print('\nSetting all Offsets to 0:')
    caput('29idMini1:e13Pos.EOFF',0)
    caput('29idMini1:e14Pos.EOFF',0)
    caput('29idMini1:e15Pos.EOFF',0)
    caput('29idMini1:e16Pos.EOFF',0)
    print('\nCurrent Position:')
    print(('e13 = '+str(caget('29idMini1:e13Pos'))))
    print(('e14 = '+str(caget('29idMini1:e14Pos'))))
    print(('e15 = '+str(caget('29idMini1:e15Pos'))))
    print(('e16 = '+str(caget('29idMini1:e16Pos'))))
    print('\nSetting back Offsets:')
    caput('29idMini1:e13Pos.EOFF',-caget('29idMini1:e13Pos'))
    caput('29idMini1:e14Pos.EOFF',-caget('29idMini1:e14Pos'))
    caput('29idMini1:e15Pos.EOFF',-caget('29idMini1:e15Pos'))
    caput('29idMini1:e16Pos.EOFF',-caget('29idMini1:e16Pos'))
    print('\nCurrent Position:')
    print(('e13 = '+str(caget('29idMini1:e13Pos'))))
    print(('e14 = '+str(caget('29idMini1:e14Pos'))))
    print(('e15 = '+str(caget('29idMini1:e15Pos'))))
    print(('e16 = '+str(caget('29idMini1:e16Pos'))))
    Sync_Encoder_RBV('b')
    SyncAllSlits()

def Reset_Slit3D_Encoders(center):
    """
    Resetting Slit 3D encoders to 0 for a given position (Hcenter,Vcenter).
    Slit size need to be set to 0.
    """
    caput('29idb:Slit4Vsize.VAL',0)
    caput('29idb:Slit4Vcenter.VAL',center)

    print('\nCurrent Position:')
    print(('e26 = '+str(caget('29idMini2:e26Pos'))))
    print(('e27 = '+str(caget('29idMini2:e27Pos'))))
    print('\nSetting all Offsets to 0:')
    caput('29idMini2:e26Pos.EOFF',0)
    caput('29idMini2:e27Pos.EOFF',0)
    print('\nCurrent Position:')
    print(('e26 = '+str(caget('29idMini2:e26Pos'))))
    print(('e27 = '+str(caget('29idMini2:e27Pos'))))
    print('\nSetting back Offsets:')
    caput('29idMini2:e26Pos.EOFF',-caget('29idMini2:e26Pos'))
    caput('29idMini2:e27Pos.EOFF',-caget('29idMini2:e27Pos'))
    print('\nCurrent Position:')
    print(('e26 = '+str(caget('29idMini2:e26Pos'))))
    print(('e27 = '+str(caget('29idMini2:e27Pos'))))
    Sync_Encoder_RBV('b')
    SyncAllSlits()



##############################################################################################################
##################                 Commissioning paper curves                     ##################
##############################################################################################################



def FermiEdges(Energy,Slit):
    EF_Table={}
    EF_Table[500]  = {10:20,  20:20,  50:20,  100:20,  200:20}
    EF_Table[1000] = {10:50,  20:50,  50:50,  100:50,  200:50}
    EF_Table[1500] = {10:100, 20:100, 50:100, 100:100, 200:100}
    PE = EF_Table[Energy][Slit]
    return PE




def QP_Curves(hv,list_mode,start,stop,step):
    SetExitSlit(200)
    #Switch_Grating("MEG")
    #print "\r"
    #print "****************  QP OFF  ****************"
    #for mode in list_mode:
    #    Switch_IDMode(mode)
    #    SetID_Raw(hv)
    #    SetSlit_BL()
    #    SetMono(250)
    #    Scan_Mono(1,start,stop,step)
    #    Scan_Go("b",1)
    #print "\r"
    #print "****************  QP ON  ****************"
    #Switch_IDQP("on")
    for mode in list_mode:
        Switch_IDMode(mode)
        SetID_Raw(hv)
        SetSlit_BL()
        SetMono(250)
        Scan_Mono(1,start,stop,step)
        Scan_Go("b",scanDIM=1)
    #Switch_IDQP("off")
    #Switch_Grating("HEG")
    #Switch_IDMode("RCP")



##############################################################################################################
###########################                    Beam Profile               ######################
##############################################################################################################



def Scan_NarrowSlit(which='2V',slit_parameters=[0.25,-2,2,0.5],scanDIM=1,scanIOC=None):
    """
        which='1V','1H','2V','2H'
        slit_parameters = [SlitSize,start,stop,step]
  
    Typical slit sizes/start/stop/step are (for full range): 
        1H/1V : [0.50, -4.5, 4.5, 0.2]
        2H    : [0.25, -3.0, 3.0, 0.2]
        2V-MEG: [0.25, -4.0, 4.0, 0.2]    
        2V-HEG: [0.50, -8.0, 8.0, 0.2]    
    """
    if scanIOC == None:
        scanIOC=BL_ioc()
    size,start,stop,step = slit_parameters
    
    SlitDict={"V":(inf,size),"H":(size,inf),'1':'2','2':'1'}     ## very complicated stuff to make a narrow slit along the direction perpendicular to the scan, and open the other slit all the way
    Hsize=SlitDict[which[1]][0]
    Vsize=SlitDict[which[1]][1]
    scanslit=int(which[0])
    otherslit=int(SlitDict[which[0]])

    SetSlit(scanslit,Hsize,Vsize)
    SetSlit(otherslit) 
    if which in ['2V','2H']:
        SetSlit1A(3,3,0,0)   # SetSlit_BL FR added on 9/24/2020
    VAL="29idb:Slit"+which+"center.VAL"
    RBV="29idb:Slit"+which+"t2.D"
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)


def Scan_NarrowSlit_Go(which='2V',slit_parameters=[0.25,-2,2,0.5],scanDIM=1,scanIOC='ARPES'):
    """
        which='1V','1H','2V','2H'
        slit_parameters = [SlitSize,start,stop,step]
    Typical slit sizes/start/stop/step are (for full range): 
        1H/1V : [0.50, -4.5, 4.5, 0.2]
        2H    : [0.25, -3.0, 3.0, 0.2]
        2V-MEG: [0.25, -4.0, 4.0, 0.2]    
        2V-HEG: [0.50, -8.0, 8.0, 0.2]    
    """
    Scan_NarrowSlit(which,slit_parameters,scanDIM,scanIOC)
    Scan_Go(scanIOC,scanDIM=scanDIM)


def Scan_MonoVsSlit(which='2V',slit_parameters=[0.25,-2,2,0.5],energy_parameters=[470,530,2],**kwargs):
    """
    This can be used to find the center of the resonant beam i.e. the slit value for the most blue shifted curve: 
        which='1V','1H','2V','2H'
        slit_parameters = [SlitSize,start,stop,step]
        energy_parameters = [eVstart,eVstop,eVstep]= [470,530,2]
        
    Typical slit sizes/start/stop/step are (for full range): 
        1H/1V : [0.50, -4.5, 4.5, 0.2]
        2H    : [0.25, -3.0, 3.0, 0.2]
        2V-MEG: [0.25, -4.0, 4.0, 0.2]    
        2V-HEG: [0.50, -8.0, 8.0, 0.2] 
        
    """
    scanIOC=BL_ioc()
    eVstart,eVstop,eVstep=energy_parameters  
    # Filling Scans:
    Scan_Mono(1,eVstart,eVstop,eVstep) 
    caput("29id"+scanIOC+":scan1.PASM","STAY")
    Scan_NarrowSlit(which,slit_parameters,2)  
    Scan_Go(scanIOC,2,**kwargs)
    # Resetting everybody to normal:
    caput("29id"+scanIOC+":scan1.PASM","PRIOR POS")
    SetMono((eVstart+eVstop)/2.0)
    SetSlit_BL()

##############################################################################################################
#######################                     Mono Calibration                    #######################
##############################################################################################################

def Mono_Parameters_Get():
    """
    Gets the mono parameters and prints them for the History
    """
    date=time.strftime("%Y%m%d",time.localtime())
    pvList=['C','D','E']
    #MIR
    mirList=["Au","Si","Carbon"]
    txt="MonoParm[\'"+date+"\']= {\n\t"
    for i in range(0,len(mirList)):
        mir=mirList[i]
        offset=caget("29idmonoMIR:P_OFFSETS."+pvList[i])
        position=caget("29idmonoMIR:X_DEF_POS."+pvList[i])
        txt+="\'"+mir+"\':["+str(offset)+","+str(position)+"],"
    #GRT
    txt+="\n\t"
    grtList=["MEG_Imp", "HEG_JY", "MEG_JY"]
    for i in range(0,len(grtList)):
        grt=grtList[i]
        offset=caget("29idmonoGRT:P_OFFSETS."+pvList[i])
        position=caget("29idmonoGRT:X_DEF_POS."+pvList[i])
        spacing=caget("29idmonoGRT:TYPE_CALC."+pvList[i])
        b2=caget("29idmonoGRT:B2_CALC."+pvList[i])
        txt+="\'"+grt+"\':["+str(offset)+","+str(position)+","+str(spacing)+","+str(b2)+"],"

    txt+="}"
    print(txt)


def Mono_Parameters_History(date):
    """
    Dictionary of Mono parameters used in Mono_Parameters(date) which sets the parameters
    #MonoParm['date']={'Au':[],Si:[],'Carbon':[],'MEG_Imp':[],'HEG_JY':[],'MEG_JY':[]}
    Mono_Parameters_Set(date) writes the parameters from the Dictionary
    """
    MonoParm={}
    #MonoParm['date']={'Au':[],Si:[],'Carbon':[],'MEG_Imp':[],'HEG_JY':[],'MEG_JY':[]}
    MonoParm["20160822"]={
        'Au':[0.3237,-12.04],'Si':[0.3237,-2.04],'Carbon':[0.3237,7.96],
        'MEG_Imp':[0.7290,4.872,1200.0,-7.34e-05],'HEG_JY':[0.7302,69.0,2400.0,-5.58e-05],'MEG_JY':[0.8,131.624,1200.0,0.0]}
    MonoParm["20190719_4"]={
        'Au':[0.3266,-12.04],'Si':[0.3237,-2.04],'Carbon':[0.3237,7.96],
        'MEG_Imp':[0.7306,4.872,1200.0,-7.15e-05],'HEG_JY':[0.7278,69.0,2400.0,-5.535e-05],'MEG_JY':[0.8,131.624,1200.0,0.0]}
    MonoParm['20191018']= {
        'Au':[0.3203,-12.04],'Si':[0.3237,-2.04],'Carbon':[0.3237,7.96],
        'MEG_Imp':[0.7306,4.872,1200.0,-7.15e-05],'HEG_JY':[0.7123,69.0,2400.0,-5.535e-05],'MEG_JY':[0.7306,131.624,1200.0,0.0],}
    return MonoParm[date]

def Mono_Parameters_Set(date):
    hvSP=caget("29idmono:ENERGY_SP")
    MonoParm=Mono_Parameters_History(date)
    pvList=['C','D','E']
    mirList=["Au","Si","Carbon"]
    for i in range(0,len(mirList)):
        mir=mirList[i]
        caput("29idmonoMIR:P_OFFSETS."+pvList[i],MonoParm[mir][0])
        caput("29idmonoMIR:X_DEF_POS."+pvList[i],MonoParm[mir][1])
    grtList=["MEG_Imp", "HEG_JY", "MEG_JY"]
    for i in range(0,len(grtList)):
        grt=grtList[i]
        caput("29idmonoGRT:P_OFFSETS."+pvList[i],MonoParm[grt][0])
        caput("29idmonoGRT:X_DEF_POS."+pvList[i],MonoParm[grt][1])
        caput("29idmonoGRT:TYPE_CALC."+pvList[i],MonoParm[grt][2])
        caput("29idmonoGRT:B2_CALC."+pvList[i],MonoParm[grt][3])
    sleep (1)
    SetMono(hvSP)

def Mono_Suffixes():
    """
    returns the FMB index for the current (MIR,GRT)
    """
    mirList=["Au","Si","Carbon"]
    grtList=["MEG_Imp", "HEG_JY", "MEG_JY"]
    pvList=['C','D','E']

    MIRindex=caget("29idmonoMIR_TYPE_MON")
    MIR_suf=pvList[MIRindex-1]
    GRTindex=caget("29idmonoGRT_TYPE_MON")
    GRT_suf=pvList[GRTindex-1]
    return MIR_suf,GRT_suf

def Mono_angle(alpha,beta): #JM modified to monitor the ready, moving sequentialy ended up in crash sometimes
    """
    Sets the mirror pitch (alpha) and grating pitch (beta) angles
    """
    alpha=alpha*1.0
    beta=beta*1.0
    #Putting Setpoints Go
    caput("29idmonoGRT:P_SP",alpha)
    caput("29idmonoMIR:P_SP",beta)
    ready=0
    while ready != 1:
        sleep(0.1)
        ready=caget('29idmono:ERDY_STS')
    print("Mono set to zero order: MIR_pitch = "+str(alpha)+", GRT_pitch = "+str(beta))



def Mono_Set_b2(b2):
    """
    Changes the b2 value for the current grating
    """
    hvSP=caget("29idmono:ENERGY_SP")
    suffix=Mono_Suffixes()[1]
    caput("29idmonoGRT:B2_CALC."+suffix,b2)
    sleep (1)
    SetMono(hvSP)
    Get_Mono()
    
def Mono_Set_cff(order,cff):
    """
    Changes the cff value for the current grating
    """
    which=caget("29idmonoGRT_TYPE_MON")
    hvSP=caget("29idmono:ENERGY_SP")
    MIR_Pitch=caget("29idmonoMIR:P.RBV")
    GRT_Pitch=caget("29idmonoGRT:P.RBV")
    hv=caget("29idmono:ENERGY_MON")
    print('MIR & GRT Pitch:',MIR_Pitch,GRT_Pitch)
    suffix=Mono_Suffixes()[1]
    caput("29idmonoGRT:TUN"+str(order)+"_CALC."+suffix,cff)
    sleep (1)
    SetMono(hvSP)
    new_MIR_Pitch=caget("29idmonoMIR:P.RBV")
    new_GRT_Pitch=caget("29idmonoGRT:P.RBV")
    dif_MIR_Pitch=new_MIR_Pitch-MIR_Pitch
    dif_GRT_Pitch=new_GRT_Pitch-GRT_Pitch
    new_hv=caget("29idmono:ENERGY_MON")
    print('MIR & GRT Pitch:',new_MIR_Pitch,new_GRT_Pitch)
    print('Differences    :',dif_MIR_Pitch,dif_GRT_Pitch)
#    Get_CFF()


def Mono_Set_GRT0(newGRT0):
    """
    Sets ONLY the GRT_offset for the current Grating
    Paralellism is NOT maintained
    """
    which='GRT'
    suffix=Mono_Suffixes()[1]                   # Mono_Suffixes() returns suffixes for current MIR [0] and GRT [1]
    GRT_pv='29idmono'+which+':P_OFFSETS.'+suffix
    hvSP=caget("29idmono:ENERGY_SP")
    caput(GRT_pv,newGRT0)

    #Putting the energy back and printing mono parameters
    sleep (1)
    caput("29idmono:ENERGY_SP",hvSP)
    Get_Mono()


def Mono_Set_MIR0(newMIR0):
    """
    Sets ONLY the MIR0 for the current Grating
    Paralellism is NOT maintained
    """
    which='MIR'
    suffix=Mono_Suffixes()[0]                   # Mono_Suffixes() returns suffixes for current MIR [0] and GRT [1]
    GRT_pv='29idmono'+which+':P_OFFSETS.'+suffix
    hvSP=caget("29idmono:ENERGY_SP")
    caput(GRT_pv,newMIR0)
    #Putting the energy back and printing mono parameters
    sleep (1)
    caput("29idmono:ENERGY_SP",hvSP)
    Get_Mono()



def Mono_Set_MIR0_GRT0(newMIR0):
    """
    Sets both the MIR0 and the GRT0 for the current Mirror and Grating
    so that paralellism is maintained
    """
    MIR_suffix=Mono_Suffixes()[0]                # Mono_Suffixes() returns suffixes for current MIR [0] and GRT [1]
    GRT_suffix=Mono_Suffixes()[1]
    MIR_pv='29idmonoMIR:P_OFFSETS.'+MIR_suffix
    GRT_pv='29idmonoGRT:P_OFFSETS.'+GRT_suffix
    # Getting current values and current delta between GRT0 and MIR0
    hvSP=caget("29idmono:ENERGY_SP")
    oldMIR0=caget(MIR_pv)
    oldGRT0=caget(GRT_pv)
    delta=oldGRT0-oldMIR0
    # Setting new values while maintaining delta
    caput(MIR_pv,newMIR0)
    caput(GRT_pv,newMIR0+delta)
    #Putting the energy back and printing mono parameters
    sleep (1)
    caput("29idmono:ENERGY_SP",hvSP)
    Get_Mono()


def Mono_Set_MIR0_GRT0_all(newMIR0):
    """
    Sets both the MIR0 for the current mirror and the GRT0 for all grating
    so that paralellism is maintained =>     Equivalent to moveing ExitSlit_Vcenter
    """
    hvSP=caget("29idmono:ENERGY_SP")
    MIR_suffix=Mono_Suffixes()[0]               # Mono_Suffixes() returns suffixes for current MIR [0] and GRT [1]
    MIR_pv ='29idmonoMIR:P_OFFSETS.'+MIR_suffix
    GRT_pv1='29idmonoGRT:P_OFFSETS.C'
    GRT_pv2='29idmonoGRT:P_OFFSETS.D'
    GRT_pv3='29idmonoGRT:P_OFFSETS.E'
    #Getting current values:
    oldMIR0  =caget(MIR_pv)
    oldGRT0_1=caget(GRT_pv1)
    oldGRT0_2=caget(GRT_pv2)
    oldGRT0_3=caget(GRT_pv3)
    print("MIR0   : ",oldMIR0)
    print("GRT0s  : ",oldGRT0_1,oldGRT0_2,oldGRT0_3)
    #Calculating the deltas between GRT0s and MIR0
    delta1=oldGRT0_1-oldMIR0
    delta2=oldGRT0_2-oldMIR0
    delta3=oldGRT0_3-oldMIR0
    print("GRT0(1)-MIR0", delta1)
    print("GRT0(2)-MIR0", delta2)
    print("GRT0(3)-MIR0", delta3)
    # Setting new values while maintaining delta
    caput(MIR_pv ,newMIR0)
    caput(GRT_pv1,newMIR0+delta1)
    caput(GRT_pv2,newMIR0+delta2)
    caput(GRT_pv3,newMIR0+delta3)
    #Putting the energy back and printing mono parameters
    sleep (1)
    caput("29idmono:ENERGY_SP",hvSP)
    Get_Mono()



def Mono_Set_ExitArm(distance_mm):
    """
    Changes the exit arm value in mm (distance between grating and exit slit, theoritically 20000)
    """
    hvSP=caget("29idmono:ENERGY_SP")
    MIR_Pitch=caget("29idmonoMIR:P.RBV")
    GRT_Pitch=caget("29idmonoGRT:P.RBV")
    hv=caget("29idmono:ENERGY_MON")
    print('MIR & GRT Pitch:',MIR_Pitch,GRT_Pitch)
    caput("29idmono:PARAMETER.G",distance_mm)
    sleep (1)
    SetMono(hvSP)
    new_MIR_Pitch=caget("29idmonoMIR:P.RBV")
    new_GRT_Pitch=caget("29idmonoGRT:P.RBV")
    dif_MIR_Pitch=new_MIR_Pitch-MIR_Pitch
    dif_GRT_Pitch=new_GRT_Pitch-GRT_Pitch
    new_hv=caget("29idmono:ENERGY_MON")
    print('MIR & GRT Pitch:',new_MIR_Pitch,new_GRT_Pitch)
    print('Differences    :',dif_MIR_Pitch,dif_GRT_Pitch)
#    Get_CFF()


def Mono_Set_Slitvshv(hv,c=3):
    '''
    Adjust slit size to keep reasonable count vs hv
          c=3 for nominal Slit2B size
          c=10 for apertured slit2B (e.g 0.25 or 0.5)
    '''
    slit(hv/100.0*c)


def Mono_Scan_Slit2BV(hv,peakBE=84,pts=11,r=0.75,i=1,**kwargs):
    """
    Takes a Slit-2V map for a range of photon energies 
        peakBE=84; fixed mode
        pts = number of pts in slit positions, default: 11
        r = % of range in slit size,  default: 0.75
        i = scanEA time in minute (default:1 for MEG, 2 for HEG?)
        Takes 2.5h with default parameters (i=1)
    """
  
    print("\n--------------- Starting core level vs Slit-2B(V) map ---------------")
    GRT=caget("29idmono:GRT_DENSITY")
    c=GRT/1200                # c = 1 for MEG, 2 for HEG
    # Getting EA parameters vs hv:
    PE=200
    #Getting Slit-2B parameters
    Vsize=0.25*c
    n=(4.5-hv/500)
    Vstart=-((floor((2*n)/Vsize/2)+1)*Vsize*c)*r
    Vstep=-round(Vstart*2/pts,2)
    #Setting energy:
    energy(hv)
    Mono_Set_Slitvshv(hv,c=10)
    #Aperturing slit 2V
    caput("29idb:Slit2Vsize.VAL",Vsize)
    VVAL ="29idb:Slit2Vcenter.VAL"
    #Take XPS for each Slit-2V position
    for V in RangeUp(Vstart,-Vstart,Vstep):
        caput(VVAL,V,wait=True,timeout=18000)
        kwargs.update({'comment': "2-V center ="+str(V)[0:6]})
        EAlist=["BE",peakBE,PE,17*60*i,1]
        scanEA(EAlist,**kwargs)
    SetSlit_BL()



def Mono_Scan_hv_drift(start,stop,step,peakBE=84,EF=None,**kwargs):
    '''
    Measure core level (by default Au 4f) in fixed mode vs energy while maintaining resonable count rate
    If EF='y' (by default None) takes the Fermi edge as well.
    kwargs:
        c=3 is the default slit2B size
    
    Used for grating calibration (changing grating_offset and b2 effects this - use grating_offset since b2 was measured)
    '''
    kwargs.setdefault('c','3')

    for hv in RangeUp(start,stop,step):
        energy(hv)
        c=int(kwargs['c'])
        Mono_Set_Slitvshv(hv,c)
        kwargs.update({'comment': "Core level @ hv = "+str(hv)})      
        scanEA(["BE",peakBE,200,17*60*1,1],**kwargs) 
        if EF is not None:
            kwargs.update({'comment': "EF @ hv = "+str(hv)})                
            scanEA(["BE",0,200,17*60*10,1],**kwargs) 


    
##############################################################################################################
###########################                    Pinhole Scripts               ######################
##############################################################################################################


def FullPinhole():
    """
    Does a pinhole with .1 mm step with AllDiagIn and then with only DiodeCIn()
    """
    AllDiagIn()
    Scan_Pinhole_Go(-3, 3, .5, .1, -3, 3, .5, .1)
    AllDiagOut()
    DiodeC('In')
    Scan_Pinhole_Go(-3, 3, .5, .1, -3, 3, .5, .1)


def Scan_Pinhole_Go(Hstart, Hstop, Hsize, Hstep,Vstart, Vstop, Vsize, Vstep,HscanDim=1,VscanDim=2,scanIOC="BL_ioc"):
    """
        Sets up the pinhole scan in the specified scanIOC (    BL_ioc => BL_ioc(), else scanIOC="Kappa","ARPES","RSXS"...)
        Make sure that you have the appropriate Diagnostics in can use AllDiagIn()
        Scan_Pinhole_Start(-3, 3, 0.5, 0.5, -3, 3, 0.5, 0.5)
    """
    Scan_Pinhole(Hstart, Hstop, Hsize, Hstep, Vstart, Vstop, Vsize, Vstep,HscanDim,VscanDim,scanIOC)
    print("\r")
    print("Pinhole ("+str(HscanDim)+","+str(VscanDim)+"): "+str(Hstart)+"/"+str(Hstop)+"/"+str(Hsize)+"/"+str(Hstep)+"/"+str(Vstart)+"/"+str(Vstop)+"/"+str(Vsize)+"/"+str(Vstep))
    if scanIOC == "BL_ioc":
        scanIOC = BL_ioc()      
    Scan_Go(scanIOC,scanDIM=VscanDim)
    print("\r")
    print("Now setting the slits back to:")
    SetSlit_BL()
    print("\r")
    print("WARNING: Don't forget to pull all of the diagnostics out.")

def Scan_Pinhole(Hstart, Hstop, Hsize, Hstep,Vstart, Vstop, Vsize, Vstep,HscanDim=1,VscanDim=2,scanIOC="BL_ioc"):
    """
        Sets up the pinhole scan in the specified scanIOC (    BL_ioc => BL_ioc(), else scanIOC="Kappa","ARPES","RSXS"...)
        Make sure that you have the appropriate Diagnostics in can use AllDiagIn()
        Does not press Go
    """
    if scanIOC == "BL_ioc":
        scanIOC = BL_ioc()
        
    #Synching slits
    caput("29idb:Slit1Hsync.PROC",1)
    caput("29idb:Slit1Vsync.PROC",1)
    #Getting initial slit size
    Hsize0=caget("29idb:Slit1Ht2.C")
    Vsize0=caget("29idb:Slit1Vt2.C")
    Hcenter0=caget("29idb:Slit1Ht2.D")
    Vcenter0=caget("29idb:Slit1Vt2.D")
    #Filling in the ScanRecord
    HVAL="29idb:Slit1Hcenter.VAL"
    HRBV="29idb:Slit1Ht2.D"
    Hstart=1.0*Hstart
    Hstop=1.0*Hstop
    Hstep=1.0*Hstep
    VVAL="29idb:Slit1Vcenter.VAL"
    VRBV="29idb:Slit1Vt2.D"
    Vstart=1.0*Vstart
    Vstop=1.0*Vstop
    Vstep=1.0*Vstep
    Scan_FillIn(HVAL,HRBV,scanIOC,HscanDim,Hstart,Hstop,Hstep)
    Scan_FillIn(VVAL,VRBV,scanIOC,VscanDim,Vstart,Vstop,Vstep)
    SetSlit1A(Hsize,Vsize,0,0,q=None)
    print("WARNING: The slits are now set to", str(Hsize),"x",str(Vsize))



##############################################################################################################
################################          ID calibration scripts        ##############################
##############################################################################################################

######  Energy range follows ID ########

def IDCalibration_Scan(start,stop,step,bandwidth=10,QP=None,Harm=1,scanIOC=None):
    """
    Sets the ID_SP and scans the mono:
        start,stop,step are for ID
    if QP is not None adjusts the mono range to offset accordingly
    !!! DOES NOT CHANGE QP VALUE !!!!
    !!! Doesn't put diodes in !!!
    """
    
    print("""
             !!! DOES NOT CHANGE QP VALUE !!!!
             !!! Doesn't put diodes in !!!""")
    
    if scanIOC is None:
        scanIOC=BL_ioc()
    scanDIM=1
    #Setting up scan record to go to peak position at the end of the scan
    PV='29id'+scanIOC+':scan'+str(scanDIM)
    VAL="29idmono:ENERGY_SP"
    RBV="29idmono:ENERGY_MON"
    caput(PV+'.PDLY',0.2)        #Detector settling time
    caput(PV+'.PASM','STAY')

    #Getting mono max range based on grating
    GRT=caget("29idmono:GRT_DENSITY")
    c=GRT/1200            # c = 1 for MEG, 2 for HEG
    if c == 1: maxhv = 3000
    elif c == 2: maxhv = 2000
    kwargs={'comment': "====== Starting Mono Scan vs ID"}
    kwargs.update({'FileSuffix': "IDCalibration"})    
    logprint(**kwargs)
    for ID in RangeUp(start,stop,step):
        print("\n------------------  ID-SP @ "+str(ID)+"   ------------------")
        SetMono(ID)
        SetID_Raw(ID)
        SetSlit_BL()
        if QP is None:
            start_hv=min(ID-ID/(bandwidth*1.0)*Harm,maxhv)  # FR update range 11/20/2019
            stop_hv=min(ID+ID/(bandwidth*2.0)*Harm,maxhv)
            step_hv=round(ID/300.0,1)
#            start_hv=min(ID-ID/(bandwidth*2.0)*Harm,maxhv)  # shift the window by doing -BW*2/+BW*1 instead of -BW*1'/'+BW*2
#            stop_hv=min(ID+ID/(bandwidth*1.0)*Harm,maxhv)
#            step_hv=round(ID/500.0,1)
        else:
            start_hv=min(ID-ID/(bandwidth*2.5)*Harm,maxhv)
            stop_hv=min(ID+ID/(bandwidth*0.7)*Harm,maxhv)
            step_hv=round(ID/300.0,1)
        Scan_FillIn(VAL,RBV,scanIOC,1,start_hv,stop_hv,step_hv)
        Scan_Go(scanIOC,scanDIM=scanDIM,FileSuffix='IDCalibration',comment="ID-SP @ "+str(ID))
        sleep(1)
        FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")-1
        if ID == start:
            FirstFileNum=FileNum     # Record First Scan Number
    LastFileNum=FileNum              # Record Last Scan Number

    print("Use:  update_id_dict("+str(FirstFileNum)+","+str(LastFileNum)+",update_file,path=None,prefix='ARPES',q=True)")




def IDCalibration_Mode(which,start=None,stop=None,step=25,Harm=1):
    '''
    Runs full calibration with a 25 eV step (by default) for a given mode:
            which = 'RCP','LCP', 'V','H'
    Better to run each mode in a separated cell (print statement at the end helps with calibration) 
    '''
    branch=CheckBranch()
    AllDiagOut(DiodeStayIn=branch)
    DiodeC('In')
    polarization(which)
    GRT=caget("29idmono:GRT_DENSITY")
    if GRT==2400: GRT='HEG'
    if GRT==1200: GRT='MEG'
    QP_ratio=caget("ID29:QuasiRatioIn.C")
    if start == None:
        start=Energy_Range(GRT,which)[0]
    if stop == None:
        stop=Energy_Range(GRT,which)[1]-50
    if QP_ratio <100:
        stop=min(stop,1500)
        QP_ratio=1
    else: QP_ratio=None
    IDCalibration_Scan(start,stop,step,bandwidth=10,QP=QP_ratio,Harm=Harm,scanIOC=None)


##############################################################################################################
##############################             Beam Motion            ##############################
##############################################################################################################


def Pixel_Calibration(motorName,start,stop,step,camNUM,AcqTime):
    """   
    """    
    scanIOC=BL_ioc()
    scanDIM=1

    branch=CheckBranch()
    if branch == "c":
        m_RBV,m_VAL=ARPES_PVmotor(motorName)
    elif branch == "d":
        m_RBV,m_VAL=Kappa_PVmotor(motorName)
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_FillIn("","",scanIOC,scanDIM,1,1,1)
    Scan_Go(scanIOC,scanDIM=scanDIM)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)
    for value in RangeUp(start,stop,step):
        caput(m_VAL,value)
        sleep(2)
        print(motorName+" = "+str(value))
        TakeImage(camNUM,AcqTime)
    Cam_FreeRun(camNUM)



def BeamMotion_Vs_BL_Go(start,stop,step,camNUM,AcqTime,scanDIM=1):
    """
    default: scanDIM=1  
    """
    scanIOC=BL_ioc()
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_FillIn("","",scanIOC,scanDIM,1,1,1)
    Scan_Go(scanIOC,scanDIM=scanDIM)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)
    for eV in RangeUp(start,stop,step):
        SetBL(eV)
    #    if mode == 0 or mode == 1:
    #        if eV>=600 or eV<=1600:
    #            AcqTime=AcqTime/2.0         #JM commented out
        if eV > 2200:
            AcqTime=AcqTime*10
        TakeImage(camNUM,AcqTime)
    Cam_FreeRun(camNUM)

def BeamMotion_Vs_hv_Go(ioc,scannum,ID,hv,AcqTime):
    ioc="b"
    scannum=1
    camNUM=4
    pvCam="29id_ps"+str(camNUM)+":"
    SetID(ID)
    SetMono(hv)
    Scan_FillIn("","",ioc,scannum,1,1,1)
    Scan_Go(ioc,scanDIM=1)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)
    sleep(3)
    TakeImage(camNUM,AcqTime)
    Cam_FreeRun(camNUM)

def BeamMotion_Vs_MonoZero_Go(ioc,scannum,start,stop,step,camNUM,iteration,AcqTime):
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_FillIn("","",ioc,scannum,1,1,1)
    Scan_Go(ioc,scanDIM=1)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)
    i=1
    while i<=iteration:
        n=start*1.0
        while n<=stop:
            Mono_zero(n)
            TakeImage(camNUM,AcqTime)
            n+=step
        i+=1
    Cam_FreeRun(camNUM)

def BeamMotion_Vs_MirPitch_Go(ioc,scannum,angle1,angle2,camNUM,iteration,AcqTime):
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_FillIn("","",ioc,scannum,1,1,1)
    Scan_Go(ioc,scanDIM=1)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)
    i=1
    while i<=iteration:
        Mono_angle(angle1,angle1)
        sleep(5)
        TakeImage(camNUM,AcqTime)
        Mono_angle(angle2,angle1)
        i+=1
#    Cam_FreeRun(camNUM)

def BeamMotion_Vs_GrtPitch_Go(ioc,scannum,angle1,angle2,camNUM,iteration,AcqTime):
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_FillIn("","",ioc,scannum,1,1,1)
    Scan_Go(ioc,scanDIM=1)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)
    i=1
    while i<=iteration:
        Mono_angle(angle1,angle1)
        sleep(5)
        TakeImage(camNUM,AcqTime)
        Mono_angle(angle1,angle2)
        i+=1
#    Cam_FreeRun(camNUM)

def BeamMotion_Vs_GrtTx_Go(ioc,scannum,camNUM,iteration,AcqTime):
    pvCam="29id_ps"+str(camNUM)+":"
    Scan_FillIn("","",ioc,scannum,1,1,1)
    Scan_Go(ioc,scanDIM=1)
    TakeImageSetup(camNUM)
    caput(pvCam+"TIFF1:FileNumber",1)

    i=1
    while i<=iteration:
        grating("HEG")
        Mono_zero(2)
        sleep(10)
        TakeImage(camNUM,AcqTime)
        grating("MEG")
        Mono_zero(2)
        sleep(10)
        TakeImage(camNUM,AcqTime)
        i+=1
#    Cam_FreeRun(camNUM)




##############################################################################################################
###########################                    FMB / Mono Scripts               ######################
##############################################################################################################



def Scan_M0M1(mirror,start,stop,step,scanIOC=None,scanDIM=1):
    """
    e.g. Scan_FMBMirror("m1:TX",-5,5,.25)
    """
    if scanIOC is None:
        scanIOC=BL_ioc()
    # database sets .PREC==0.  We want more digits than that.
    caput("29id_"+mirror+"_SP.PREC",3)
    VAL="29id_"+mirror+"_SP"
    RBV="29id_"+mirror+"_MON"
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)

def Scan_M3R(which,start,stop,step,scanIOC=None,scanDIM=1):
    """
        TX = lateral                 RX = Yaw
        TY = vertical                RY = Pitch
        TZ = longitudinal            RZ = Roll
    """
    PV="29id_m3r:"
    if scanIOC is None:
        scanIOC=BL_ioc()
    # database sets .PREC==0.  We want more digits than that.
    caput(PV+which+"_SP.PREC",3)
    caput('29id'+scanIOC+':scan1.DDLY',1)
    VAL=PV+which+"_SP"
    RBV=PV+which+"_MON"
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)


def Move_M0(which,val):
    """
        TX = lateral                 RX = Yaw
        TY = vertical                RY = Pitch
        TZ = longitudinal            RZ = Roll
    """
    n=0
    Move_M0M1(n,which,val)


def Move_M1(which,val):
    """
        TX = lateral                 RX = Yaw
        TY = vertical                RY = Pitch
        TZ = longitudinal            RZ = Roll
    """
    n=1
    Move_M0M1(n,which,val)

def Move_M0M1(n,which,val):
    """
    n = 0,1
    and which:
        TX = lateral                 RX = Roll
        TY = vertical                RY = Pitch
        TZ = longitudinal            RZ = Yaw
    """
    PV="29id_m"+str(n)+":"
    caput(PV+which+"_SP.PREC",3)
    caput(PV+which+"_SP",val)
    sleep(1)
    while True:
        status=caget(PV+'SYSTEM_STS')
        if status != 1:    # Moving
            sleep(0.5)
        if status == 1:    # Positioned
            current=round(caget(PV+which+'_SP'),3)
            if current!= round(val,3):
                caput(PV+'MOVE_CMD.PROC',1)
            else:
                break
    print(PV+which+" = "+str(current))

def Move_FMBMono(motor,value):
    """
        for pitch motor => MIR:P or GRT:P
        for translation motor => MIR:X or GRT:X
    """
    caput("29idmono"+motor+"_SP.PREC",3)
    PV="29idmono"+motor+"_SP"
    caput(PV,value,wait=True,timeout=18000)

def Scan_FMBMono(scanDIM,motor,start,stop,step):
    """
        for pitch motor => MIR:P or GRT:P
        for translation motor => MIR:X or GRT:X
    """
    scanIOC=BL_ioc()
    # database sets .PREC==0.  We want more digits than that.
    caput("29idmono"+motor+"_SP.PREC",3)
    VAL="29idmono"+motor+"_SP"
    RBV="29idmono"+motor+"_MON"
    Scan_FillIn(VAL,RBV,scanIOC,scanDIM,start,stop,step)

### Mono controls:

def Mono_pinkbeam(): ##used move grating in mirror out of beam
    caput("29idmonoMIR:P_POS_SP",0,0)
    caput("29idmonoMIR:P_MOVE_CMD.PROC",0)
    sleep(3)
    caput("29idmonoGRT:P_POS_SP",0.0)
    caput("29idmonoGRT:P_MOVE_CMD.PROC",0)
    sleep(3)
    caput("29idmonoMIR:X_POS_SP",-52)
    caput("29idmonoMIR:X_MOVE_CMD.PROC",0)
    sleep(3)
    caput("29idmonoGRT:X_POS_SP",210)
    caput("29idmonoGRT:X_MOVE_CMD.PROC",0,wait=True,timeout=18000)

def Mono_CC(): ##used for commissioning
    caput("29idmonoMIR_TYPE_SP",3)
    caput("29idmonoMIR:X_DCPL_CALC.PROC",0)
    caput("29idmonoGRT_TYPE_SP", 10)
    caput("29idmonoGRT:X_DCPL_CALC.PROC",0)
    ev=caget("29idmono:ENERGY_SP")
    caput("29idmono:ENERGY_SP", 440)

def Mono_zero(angle):
    angle=angle*1.0
    caput("29idmonoMIR:P_POS_SP",angle,wait=True,timeout=18000)
    caput("29idmonoMIR:P_MOVE_CMD.PROC",1,wait=True,timeout=18000)
    caput("29idmonoGRT:P_POS_SP",angle,wait=True,timeout=18000)
    caput("29idmonoGRT:P_MOVE_CMD.PROC",1,wait=True,timeout=18000)
    print("Mono set to zero order: MIR_pitch = "+str(angle)+", GRT_pitch = "+str(angle))



##############################################################################################################
##############################             Scan Bakeout            ##############################
##############################################################################################################




#Scan_Bakeout
def Scan_Bakeout(scanIOC,scanDIM,which):        # which = "Mono" / "Beamline" / "ARPES" / "RSXS" / "Stinger"
    run=Check_run()
    folder='/net/s29data/export/data_29idb/Bakeout/'
    subfolder='/'+which+'/'+run
    prefix='mda_'
    
    caput('29id'+scanIOC+':saveData_fileSystem',folder)
    caput('29id'+scanIOC+':saveData_subDir',subfolder)
    caput('29id'+scanIOC+':saveData_baseName',prefix)

    MyPath="/net/s29data/export/data_29idb/Bakeout/"+which+"/"+run
    print("\nBakeout folder: " + MyPath)
    if not (exists(MyPath)):
        mkdir(MyPath)
        FileNumber=1
    else:
        FileNumber=getNextFileNumber(MyPath,prefix[:-1])
    caput('29id'+scanIOC+':saveData_scanNumber',FileNumber)
    
    sleep(5)
    SaveStatus=caget('29id'+scanIOC+':saveData_status',as_string=True)
    SaveMessage=caget('29id'+scanIOC+':saveData_message',as_string=True)
    print("\nSave Status "+scanIOC+": "+SaveStatus+" - "+SaveMessage)
    
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    Reset_Scan_Settings(scanIOC,scanDIM)
    i=1
    
    while i<=9:
        caput(pv+".D0"+str(i)+"PV","")
        i+=1
    while i<=70:
        caput(pv+".D"+str(i)+"PV","")
        i+=1
    Scan_FillIn("","time",scanIOC,scanDIM,1,1,1)        # scan vs time
    caput(pv+".NPTS",99999)                # max number of point
    caput(pv+".T1PV","29idb:ca1:read")
    caput("29idb:ca1:read.SCAN",0)            # CA5 in passive
    caput(pv+".DDLY",60)                # record point every minute
    # Thermocouples:
    caput(pv+".D01PV","29iddau1:dau1:001:ADC")
    caput(pv+".D02PV","29iddau1:dau1:002:ADC")
    caput(pv+".D03PV","29iddau1:dau1:003:ADC")
    caput(pv+".D04PV","29iddau1:dau1:004:ADC")
#    caput(pv+".D05PV","29iddau1:dau1:005:ADC")
    caput(pv+".D06PV","29iddau1:dau1:006:ADC")
    caput(pv+".D07PV","29iddau1:dau1:007:ADC")
    caput(pv+".D08PV","29iddau1:dau1:008:ADC")
    caput(pv+".D09PV","29iddau1:dau1:009:ADC")
    caput(pv+".D10PV","29iddau1:dau1:010:ADC")
    # Ion Gauges:
    caput(pv+".D21PV","29idb:VS1A.VAL")
    caput(pv+".D22PV","29idb:VS2A.VAL")
    caput(pv+".D23PV","29idb:VS3AB.VAL")
    caput(pv+".D24PV","29idb:VS4B.VAL")
    caput(pv+".D25PV","29idb:VS5B.VAL")
    caput(pv+".D26PV","29idb:VS6B.VAL")
    caput(pv+".D27PV","29idb:VS7B.VAL")
    caput(pv+".D28PV","29idb:VS8C.VAL")
    caput(pv+".D29PV","29idb:VS8CSP.VAL")
    caput(pv+".D30PV","29idb:VS9C.VAL")
    caput(pv+".D31PV","29idb:VS10C.VAL")
    caput(pv+".D32PV","29idb:VS8D.VAL")
    caput(pv+".D33PV","29idb:VS9D.VAL")
    caput(pv+".D34PV","29idb:VS10D.VAL")
    # Ion Pumps:
    caput(pv+".D41PV","29idb:IP1A.VAL")
    caput(pv+".D42PV","29idb:IP2A.VAL")
    caput(pv+".D43PV","29idb:IP3A.VAL")
    caput(pv+".D44PV","29idb:IP3B.VAL")
    caput(pv+".D45PV","29idb:IP4B.VAL")
    caput(pv+".D46PV","29idb:IP5B.VAL")
    caput(pv+".D47PV","29idb:IP6B.VAL")
    caput(pv+".D48PV","29idb:IP7B.VAL")
    caput(pv+".D49PV","29idb:IP7C.VAL")
    caput(pv+".D51PV","29idb:IP8C1.VAL")
    caput(pv+".D52PV","29idb:IP8C2.VAL")
    caput(pv+".D53PV","29idb:IP9C.VAL")
    caput(pv+".D54PV","29idb:IP10C1.VAL")
    caput(pv+".D55PV","29idb:IP10C2.VAL")
    caput(pv+".D56PV","29idb:IP7D.VAL")
    caput(pv+".D57PV","29idb:IP8D1.VAL")
    caput(pv+".D58PV","29idb:IP8D2.VAL")
    caput(pv+".D59PV","29idb:IP9D.VAL")
    caput(pv+".D60PV","29idb:IP10D1.VAL")
    caput(pv+".D61PV","29idb:IP10D2.VAL")

    if which.upper() == "Beamline".upper():
        print("ScanRecord ready")
    if which.upper() == "Mono".upper():
        print('Setting up Mono temperatures')
        caput(pv+".D11PV","29idmono:TC1_MON")
        caput(pv+".D12PV","29idmono:TC2_MON")
        caput(pv+".D13PV","29idmono:TC3_MON")
        caput(pv+".D14PV","29idmono:TC4_MON")
        caput(pv+".D15PV","29idmono:TC5_MON")
        caput(pv+".D16PV","29idmono:TC6_MON")
    if which.upper() == "ARPES".upper():
        print('Setting up ARPES temperatures')
        caput(pv+".D11PV","29idc:VS11C.VAL")
        caput(pv+".D12PV","29idc:VSCUBE.VAL")
        caput(pv+".D13PV","29idc:IP11C1.VAL")
        caput(pv+".D14PV","29idc:IP11C2.VAL")
        caput(pv+".D15PV","29idc:IPCUBE.VAL")
        caput(pv+".D16PV","29idARPES:LS335:TC1:IN1")
        caput(pv+".D17PV","29idARPES:LS335:TC1:IN2")
    if which.upper() == "RSXS".upper():
        print('Setting up RSXS temperatures')
        caput(pv+".D11PV","29idb:VS11D.VAL")
        caput(pv+".D12PV","29idb:VS12D.VAL")
        caput(pv+".D13PV","29idd:LS331:TC1:SampleA")
        caput(pv+".D14PV","29idd:LS331:TC1:SampleB")
    if which.upper() == "Stinger".upper():
        print('Setting up Stinger temperatures')
        caput(pv+".D01PV","29idARPES:LS335:TC1:IN1")
        caput(pv+".D02PV","29idARPES:LS335:TC1:IN2")
        caput(pv+".D03PV","29idd:LS331:TC1:SampleA")
        caput(pv+".D04PV","29idd:LS331:TC1:SampleB")
        caput(pv+".D05PV","29idc:LS340:TC2:Control")
        caput(pv+".D06PV","29idc:LS340:TC2:Sample")
        caput(pv+".D07PV","29idc:VS11C.VAL")
        caput(pv+".D08PV","29idb:VS11D.VAL")
        
        

##############################################################################################################
########################        Endstation Testing            ##############################
##############################################################################################################


def Kappa_ScanTempPres(scanIOC,scanDIM):
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    #Clear all scan pvs
    caput(pv+".CMND",6)
    #Set detectors
    caput(pv+".D01PV","29idd:tc1:getVal_A.VAL")
    caput(pv+".D02PV","29idd:tc1:getVal_B.VAL")
    caput(pv+".D03PV","29idb:VS11D.VAL")
    #Scan_Time_Go(duration_min,step_sec,scanIOC,scanDIM=1)
    Scan_Time_Go(9999,60,scanIOC,scanDIM)





def MIR_GRT_Offset(GRT,Slit_list):    
    """ "Find MIR-GRT offset by scanning 0 order through exit slit"""
    Switch_Grating(GRT)
    SetExitSlit(50)
    scanIOC="Test"
    DiodeC('In')
    SetSlit2B(2,0.5,0,0)
    VAL="29idmonoGRT:P_SP"
    for ang in RangeUp(1.5,5,0.5):
        print("\r")
        Mono_angle(ang,ang)
        print("\r")
        for x in Slit_list:
            SetExitSlit(x)
            print("\r")
            caput("29idTest:scan1.PASM",3)        # go to peak position
            caput("29idTest:scan1.REFD",44)
            start,stop,step = ang-0.0005*x, ang+0.0005*x ,0.00002*x
            Scan_FillIn(VAL,"",scanIOC,1,start,stop,step)
            Scan_Go(scanIOC,scanDIM=1)
            sleep(1)
            print("\r")
            ang=caget("29idmonoGRT:P_SP")
            print("Peak: ",ang)
            print("\r")
            print("-------------------------")
    caput("29idTest:scan1.PASM",2)
    caput("29idTest:scan1.REFD",1)






def Change_Mono_Offsets(x):
    """
    change MIR OFFSET TO X
    change GRT OFFSETS accordingly to maintain parallelism
    After determining parallelism (zero order a=b)
    Get the correct take-off angle delta, equivalent to scan ExitSlit_Vcenter
    """

    hvSP=caget("29idmono:ENERGY_SP")
    PV_MIR_Offset="29idmonoMIR:P_OFFSETS.C"
    MIR_Offset=caget(PV_MIR_Offset)

    GRT_OffsetList=[]
    for suf in ['C','D','E']:
        GRT_OffsetList.append(caget("29idmonoGRT:P_OFFSETS."+suf))
    MIR_GRT_Offset=MIR_Offset-np.array(GRT_OffsetList)    # list of MIR-GRT for all 3 gratings

    caput(PV_MIR_Offset,x)
    caput("29idmonoGRT:P_OFFSETS.C",x-MIR_GRT_Offset[0])
    caput("29idmonoGRT:P_OFFSETS.D",x-MIR_GRT_Offset[1])
    caput("29idmonoGRT:P_OFFSETS.E",x-MIR_GRT_Offset[2])
    sleep (1)
    SetMono(hvSP)
    Get_Mono()


##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################


######         ScanFunctions_EA.py:
#    - General EA Functions
#    - General EA SetUp
#    - EA Scan Scripts
######    


##########################################################################################
####################            General EA Functions          ##############################
##########################################################################################

def SES_slit(val):
    """
    Set the Scienta Slit
    val    w_mm    l_mm    Shape
    1    0.2        25    Curved
    2    0.3        30    Straight
    3    0.3        25    Curved
    4    0.5        30    Straight
    5    0.5        25    Curved
    6    0.8        25    Curved
    7    1.5        30    Straight
    8    2.5        30    Straight
    8.5            open apperture
    9    4.0        30    Straight    
    """
    caput("29idc:m8.VAL",val,wait=True,timeout=18000)


def BE2KE(BE):
    wk=EA.wk
    hv=Get_energy()[4]
    KE=hv-BE-wk
    return KE






##############################################################################################################
##############################             TimeOut                  ##############################
##############################################################################################################


import signal
TIMEOUT = 5


def interrupted_c(signum, frame):
    "called when read times out"
    print('\nIs anybody out there????')
    print('I am reducing count rate and repeating the scan!')
    raise ValueError
signal.signal(signal.SIGALRM, interrupted_c)

def input_c():
    try:
        print('\n\nWARNING: Scan stopped by operator OR interlock triggered, reduce count rate...')
        print('Press ENTER (CTRL+C) within the next 30s to CONTINUE (ABORT) >')
        foo = input()
        return foo
    except KeyboardInterrupt as e:
        raise e
    except:
        # timeout
        return



def getUserInput_c():
    signal.alarm(TIMEOUT)                # reply_c = getUserInput_c()
    try:
        s = input_c()                # if asnwer prompt: isinstance(reply_c, basestring) => True
    except ValueError:                # i.e. reply_c is a string ('' if press Return key)
        print("\nInput has timed out!!!!!")
    except KeyboardInterrupt as e:
        print("\nUser wants to abort!")
        s = False                # if CTRL+C   : reply_c == False    => True
        raise e
    finally:
        signal.alarm(0)              # if times out: reply_c == None    => True
    return s



def Test_Prompt():
    print("\nDo something")
    reply_c=getUserInput_c()
    if reply_c == None:
        print("\nRepeat that thing")
    sleep(1)
    print("\nDo something else")


    reply_c = getUserInput_c()

#



##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################



"""
####### How to use the new built-in logging feature:
#
# 1.) Create a text file in the "User_Folders/MyName/" directory every time you make a new sample
# 2.) Everytime you restart ipython, type 'logfile="Kawasaki/<logfile>.txt"' -
#    the example for the a given sample log would be: 'logfile="Kawasaki/date_sample_logfile.txt"'
# 3.) When calling a function with logging "activated", just pass the arguement of 'logfile'
#      i.) Functions with 'log=None' have logging activated. NOTE: If you do not pass an arguement for the
#      'log=None' field, there will NOT be an error, it just simply thinks you do not want to log the data
#     ii.) An example of a call is: scanEA(["KE",512,516.5,0.05,100,7,5,"Angular",1],logfile)
#    iii.) If you pass a function 'logfile' without defining the variable (i.e. right after opening/restarting ipython) #       it'll error out saying that the variable logfile is undetermined

# Other assorted notes:
#    I've noticed that when running Fanny's new fermi map function that if I cancel it midway through the script
#    ipython will start acting up.
#    Basically if you try to go back to an older function call it won't let you scroll the cursor backwards past
#    a certain point in the terminal
#    The solution I've found that works well enough is to just type 'exit' to exit the ipython session and restart
#    it (don't forget to re-define the logfile variable and rerun macro file)
"""

##############################################################################################################
##############################             ARPES function         ##############################
##############################################################################################################
##############################################################################################################
##############################             SES Work Function          ##############################
##############################################################################################################

def WorkFunction_Measure(PE,KE=409,**kwargs):
    '''
    Takes data with 1st and 2nd order light of core level with KE at @ hv=500eV
    **kwargs
    
    '''
    frames=round(17*60*200/PE,0)
    energy(500)
    
    #Fermi Level
    slit(150)
    kwargs.update({'comment': 'EF1'}) 
    EAlist=['KE',495,PE,frames,1]
    scanEA(EAlist,**kwargs)
    
    #Core level first order
    slit(50)
    kwargs.update({'comment': 'KE1'})     
    EAlist=['KE',KE,PE,frames/10,1]
    scanEA(EAlist,**kwargs)
    
    #Core level second order
    slit(150)
    kwargs.update({'comment': 'KE2'}) 
    EAlist=['KE',KE+500,PE,frames*10,1]
    scanEA(EAlist,**kwargs)
    print("""Fit the data :
          - EF1 = EF in first order light (scan #1)
          - KE1 = Au_3/2 in first order light (scan #2)
          - KE2 = Au_3/2 for 2nd order light (scan #3)
          => wk = KE2-2*KE1-(EF1-KE1)`
    Details of the math is page 16 of commissionning book IV
    Now if you know what you are doing you can: 
          caput('29idcEA:det1:ENERGY_OFFSET',new_wk_value)""")
    
def WorkFunction_Calc(EF1,KE1,KE2):
    """Fit the data :
          - EF1 = EF in first order light (scan #1)
          - KE1 = Au_3/2 in first order light (scan #2)
          - KE2 = Au_3/2 for 2nd order light (scan #3)
          => wk = KE2-2*KE1-(EF1-KE1)`
    Details of the math is page 16 of commissionning book IV"""
    wk = KE2-2*KE1-(EF1-KE1)
    print("wk = KE2-2*KE1-(EF1-KE1) = ",wk)
    print("Now if you know what you are doing you can:") 
    print("EA._setwk("+str(round(wk,2))+")")

def WorkFunction(KE1,KE2,Ef):
    Phi=round(KE2-2*KE1-(Ef-KE1),3)
    print(('Phi = '+str(Phi)+' eV'))
    return Phi

def Map_ARPES_Sample(step_y=0.5,step_z=0.5):
    print("Scan_ARPES_2Dmotor(\"y\",0,4,"+str(step_y)+",\"z\",12,16,"+str(step_z)+")")
    Scan_ARPES_2D_Go(["y",0,4,step_y],["z",12,16,step_z])

def RoughPositions_Find(th_start,th_stop, th_step,**kwargs):
    """automatically scans and creates the RoughPosition list used in FermiMap for 
    relatively uniform samples by:
        1) scanx(-0.5,0.5,.05,mode='relative')
        2) does a gaussian fits the mda EAV intesnity to determine center of the fit x_center
        3) mv(x_center)
        4) mprint() and appends current position to list
        5) moves to the next theta value and repeats
        
    Note: before starting move to the first theta position and adjust the focus leaving the EA is Live Mode
    
    **kwargs
        scanDet=17
    """
    kwargs.setdefault("scanDet",17)
    if caget("29idcEA:det1:Acquire") !=1:
        print("Turn on the EA!!! EALive(PE,KE,Lens=\'Transmission\')")
    else:
        RefinedPositions=[]
        for th in RangeDown(th_start,th_stop+th_step,th_step):
            mvth(th)
            scanx(-0.5,0.5,.05,mode='relative')
            scanNum=caget("29idARPES:saveData_scanNumber")-1
            x,y,x_name,y_name=mda_1D(scanNum,kwargs["scanDet"])
            results=fit_gauss(np.array(x),np.array(y))
            mvx(results[2][1])  
            RefinedPositions.append(mprint())
        print("RefinedPositions=",RefinedPositions) 




####################################################################################################
################    ARPES Positions (LEED,transfer, measure)    #####################################
#####################################################################################################
def ARPES_DefaultPosition(destination):
    """
    Default ARPES positions in DIAL units
    """
    DefaultPosition={
    'measure':(0.0,0.0,-13.5,0.0,0.0,0.0),
    'LEED':(-0.0, 0.0, -141.5, 89.5, 0.0, 0.0),
    'transfer':(-0,0.0,-141.5,180.0,0.0,0.0),
    }
    if destination in DefaultPosition:
        pos=DefaultPosition[destination]
    else:
        pos=(None,None,None,None,None,None)
    return pos

def ARPES_MoveSequence(destination):
    """
    Moves the ARPES manipulator x,y,z,th to a given destination (does not change chi or phi)
    Resets the limits to help protect from crashes 
        such as: phi/chi motor body into the strong back, manipulator into the LEED, manipulator into the wobble stick
        
    DO NOT MAKE BIG MOVE WITH OUT WATCHING THE MANIPULATOR!!!! 
        if the theta encoder stops reading the manipulator will CRASH!!!!
    """
    (x,y,z,th,chi,phi)=ARPES_DefaultPosition(destination)
    if x is None:
        print("Not a valid destination")
    else:
        #reset limits to default values
        ARPES_LimitsSet(None)
        #print destination
        print(("Moving to "+destination+": "+str(round(x,1))+","+str(round(y,1))+","+str(round(z,1))+","+str(round(th,1)))+'     Time:'+time.strftime("%H:%M"))
        # move x and y to zero for all moves (helps protect the motors from crashing into the strong back)
        caput(ARPES_PVmotor('x')[3]+".DVAL",0,wait=True,timeout=18000)
        caput(ARPES_PVmotor('y')[3]+".DVAL",0,wait=True,timeout=18000)
        # moves z and th simultaneously and monitors the .DMOV
        caput(ARPES_PVmotor('z')[3]+".DVAL",z,wait=False,timeout=18000)
        caput(ARPES_PVmotor('th')[3]+".DVAL",th,wait=False,timeout=18000)
        while True:
            Test=caget(ARPES_PVmotor('z')[3]+".DMOV")*caget(ARPES_PVmotor('th')[3]+".DMOV")
            if(Test==1):
                break
        # move x and y to final position
        caput(ARPES_PVmotor('x')[3]+".DVAL",x,wait=True,timeout=18000)
        caput(ARPES_PVmotor('y')[3]+".DVAL",y,wait=True,timeout=18000)
        print(("Arrived at "+destination+": "+str(round(x,1))+","+str(round(y,1))+","+str(round(z,1))+","+str(round(th,1)))+'     Time:'+time.strftime("%H:%M"))
        #set the limits for this position
        ARPES_LimitsSet(destination)

def ARPES_LimitsSet(destination):
    """
    Resets the ARPES motor limits in Dial cooridinates(remember that z is negative)
        destination: 'measures' or 'LEED',
        else: sets to the full range
    ARPES_MoveSequence(destination) minimizes that chance of a crash and sets limits
    """
    if destination == 'measure':
        (x,y,z,th,chi,phi)=ARPES_DefaultPosition("measure")
        limits={'x':[5.5,-7],'y':[7,-5],'z':[-6,-310],'th':[th+35,th-25],'chi':[45,-15],'phi':[120,-120]}
    elif destination == 'LEED':
        (x,y,z,th,chi,phi)=ARPES_DefaultPosition("LEED")
        limits={'x':[5.5,-7],'y':[6,-1],'z':[z-5,z+5],'th':[th+2,th-2],'chi':[45,-15],'phi':[120,-120]}
    else:
        limits={'x':[5.5,-7],'y':[7,-5],'z':[-6,-310],'th':[240,-70],'chi':[45,-15],'phi':[120,-120]}
    #setting the limits for each motor in Dial
    for m in limits:
        caput(ARPES_PVmotor(m)[3]+'.DHLM',limits[m][0])
        caput(ARPES_PVmotor(m)[3]+'.DLLM',limits[m][1])
    if destination is not None:
        print("Limits have been reset for "+destination+" position")
    else:
        print("Limits have been reset for full range")
####################################################################################################
def ARPES_transfer(chi=0,phi=0,**kwargs):
    """
    Moves the ARPES manipulator to the default transfer position
    kwargs:
        EA_HV_Off=True; Turns off the EA HV
        Close_CBranch=True;  closes the C-shutter and the C-valve (main chamber to BL)
    """
    ARPESgo2("transfer",**kwargs)

def ARPES_measure(**kwargs):
    """
    Moves to ARPES motors x,y,z,th to the default measurement position
    kwargs
        chi=None # specify a value to move chi
        phi=None # specifiy a value to move phi
    """
    ARPESgo2("measure",**kwargs)

def ARPES_LEED(**kwargs):
    """
    Moves to ARPES motors x,y,z,th to the default LEED position
    kwargs:
        EA_HV_Off=True; Turns off the EA HV
        Close_CBranch=True;  closes the C-shutter and the C-valve (main chamber to BL)
        
        chi=None # specify a value to move chi
        phi=None # specifiy a value to move phi
    """
    ARPESgo2("LEED",**kwargs)    
####################################################################################################
def ARPESgo2(destination,**kwargs):
    """
    Moves the ARPES manipulator to the default position: 
    destination: "transfer", "measure", "LEED"

    kwargs:
        EA_HV_Off=True; Turns off the EA HV
        Close_CBranch=True;  closes the C-shutter and the C-valve (main chamber to BL)
        
        chi=None => doesn't move, otherwise specify a value to move chi
        phi=None => doesn't move, otherwise specifiy a value to move phi 

    """
    kwargs.setdefault("EA_HV_Off",True)
    kwargs.setdefault("Close_CBranch",True)
    kwargs.setdefault("chi",None)
    kwargs.setdefault("phi",None)


    #safety checks (default is not None)
    if kwargs['EA_HV_Off']:
        EA.off()
    if kwargs['Close_CBranch']:
        Close_CShutter()
        Close_CValve()

    #Move x,y,z,th
    ARPES_MoveSequence(destination)
    #Move chi and phi back to 0
    if kwargs["chi"] is not None:
        caput(ARPES_PVmotor('chi')[1],kwargs["chi"])
    if kwargs["phi"] is not None:
        caput(ARPES_PVmotor('phi')[1],kwargs["phi"])


##############################################################################################################
##############################            conversions         ##############################
##############################################################################################################


def deg2rad(angle_deg):
    angle_rad=angle_deg*pi/180
    return angle_rad

def rad2deg(angle_rad):
    angle_deg=angle_rad*180/pi
    return angle_deg



##############################################################################################################
##############################             Lakeshore 335 Diode Curves        ##############################
##############################################################################################################
#---Settings as of 12/04/2018---
#DiodeCurve_Write(22,"SI435")
#DiodeCurve_SetInput("A",22,400)
#DiodeCurve_Write(23,"SI410")
#DiodeCurve_SetInput("B",23,450)



# =============================================================================
# def DiodeCurves(DiodeModel):
#      DiodeCalibration={}
#      DiodeCalibration["SI435"]=[0.00000,1.66751,1.64531,1.61210,1.57373,1.53247,1.49094,1.45196,1.41723,1.38705,1.36089,1.33785,1.31699,1.29756,1.27912,1.26154,1.24489,1.22917,1.21406,1.19855,1.18193,1.16246,1.13841,1.12425,1.11828,1.11480,1.11217,1.10996,1.10828,1.10643,1.10465,1.10295,1.10124,1.09952,1.09791,1.09629,1.09468,1.09306,1.09145,1.08983,1.08821,1.08659,1.08497,1.08334,1.08171,1.08008,1.07844,1.07681,1.07517,1.07353,1.07188,1.07023,1.06858,1.06693,1.06528,1.06362,1.06196,1.06029,1.05863,1.05696,1.05528,1.05360,1.05192,1.05024,1.04856,1.04687,1.04518,1.04349,1.04179,1.04010,1.03839,1.03669,1.03498,1.03327,1.03156,1.02985,1.02814,1.02642,1.02471,1.02299,1.02127,1.01957,1.01785,1.01612,1.01439,1.01267,1.01093,1.00918,1.00744,1.00569,1.00393,1.00218,1.00042,0.99865,0.99687,0.99510,0.99332,0.99153,0.98975,0.98795,0.98615,0.98434,0.98254,0.98073,0.97891,0.97710,0.97527,0.97344,0.97161,0.96978,0.96794,0.96609,0.96424,0.96239,0.96053,0.95867,0.95680,0.95492,0.95304,0.95116,0.94927,0.94738,0.94549,0.94358,0.94167,0.93976,0.93785,0.93592,0.93398,0.93203,0.93008,0.92812,0.92616,0.92418,0.92221,0.92022,0.91823,0.91623,0.91423,0.91222,0.91021,0.90819,0.90617,0.90414,0.90212,0.90008,0.89805,0.89601,0.89397,0.89293,0.88988,0.88783,0.88578,0.88372,0.88166,0.87959,0.87752,0.87545,0.87337,0.87129,0.86921,0.86712,0.86503,0.86294,0.86084,0.85874,0.85664,0.85453,0.85242,0.85030,0.84818,0.84606,0.84393,0.84180,0.83967,0.83754,0.83540,0.83325,0.83111,0.82896,0.82680,0.82465,0.82249,0.82032,0.81816,0.81599,0.81381,0.81163,0.80945,0.80727,0.80508,0.80290,0.80071,0.79851,0.79632,0.79412,0.79192,0.78972,0.78752,0.78532,0.78311,0.78090,0.77869,0.77648,0.77426,0.77205,0.76983,0.76761,0.76539,0.76317,0.76094,0.75871,0.75648,0.75425,0.75202,0.74978,0.74755,0.74532,0.74308,0.74085,0.73861,0.73638,0.73414,0.73191,0.72967,0.72743,0.72520,0.72296,0.72072,0.71848,0.71624,0.71400,0.71176,0.70951,0.70727,0.70503,0.70278,0.70054,0.69829,0.69604,0.69379,0.69154,0.68929,0.68704,0.68479,0.68253,0.68028,0.67802,0.67576,0.67351,0.67124,0.66898,0.66672,0.66445,0.66219,0.65992,0.65765,0.65538,0.65310,0.65083,0.64855,0.64628,0.64400,0.64172,0.63944,0.63716,0.63487,0.63259,0.63030,0.62802,0.62573,0.62344,0.62115,0.61885,0.61656,0.61427,0.61197,0.60968,0.60738,0.60509,0.60279,0.60050,0.59820,0.59590,0.59360,0.59131,0.58901,0.58671,0.58441,0.58211,0.57980,0.57750,0.57520,0.57289,0.57059,0.56828,0.56598,0.56367,0.56136,0.55905,0.55674,0.55443,0.55211,0.54980,0.54748,0.54516,0.54285,0.54053,0.53820,0.53588,0.53356,0.53123,0.52891,0.52658,0.52425,0.52192,0.51958,0.51725,0.51492,0.51258,0.51024,0.50790,0.50556,0.50322,0.50088,0.49854,0.49620,0.49385,0.49151,0.48916,0.48681,0.48446,0.48212,0.47977,0.47741,0.47506,0.47271,0.47036,0.46801,0.46565,0.46330,0.46095,0.45860,0.45624,0.45389,0.45154,0.44918,0.44683,0.44447,0.44212,0.43976,0.43741,0.43505,0.43270,0.43034,0.42799,0.42563,0.42327,0.42092,0.41856,0.41620,0.41384,0.41149,0.40913,0.40677,0.40442,0.40206,0.39970,0.39735,0.39499,0.39263,0.39027,0.38792,0.38556,0.38320,0.38085,0.37849,0.37613,0.37378,0.37142,0.36906,0.36670,0.36435,0.36199,0.35963,0.35728,0.35492,0.35256,0.35021,0.34785,0.34549,0.34313,0.34078,0.33842,0.33606,0.33371,0.33135,0.32899,0.32667,0.32428,0.32192]
#      DiodeCalibration["SI410"]=[0.0000,1.7191,1.7086,1.6852,1.6530,1.6124,1.5659,1.5179,1.4723,1.4309,1.3956,1.3656,1.3385,1.3142,1.2918,1.2712,1.2517,1.2333,1.2151,1.1963,1.1759,1.1524,1.1293,1.1192,1.1146,1.1114,1.1090,1.1069,1.1049,1.1031,1.1014,1.0997,1.0980,1.0964,1.0949,1.0933,1.0917,1.0902,1.0886,1.0871,1.0855,1.0839,1.0824,1.0808,1.0792,1.0776,1.0760,1.0744,1.0728,1.0712,1.0696,1.0679,1.0663,1.0646,1.0630,1.0613,1.0597,1.0580,1.0563,1.0547,1.0530,1.0513,1.0497,1.0480,1.0463,1.0446,1.0429,1.0412,1.0395,1.0378,1.0361,1.0344,1.0327,1.0310,1.0293,1.0276,1.0259,1.0242,1.0224,1.0207,1.0190,1.0172,1.0155,1.0137,1.0120,1.0102,1.0085,1.0067,1.0049,1.0032,1.0014,0.9996,0.9978,0.9960,0.9942,0.9924,0.9905,0.9887,0.9869,0.9851,0.9832,0.9814,0.9795,0.9777,0.9758,0.9740,0.9721,0.9703,0.9684,0.9665,0.9646,0.9628,0.9609,0.9590,0.9571,0.9552,0.9533,0.9514,0.9495,0.9476,0.9457,0.9437,0.9418,0.9398,0.9379,0.9359,0.9340,0.9320,0.9300,0.9281,0.9261,0.9241,0.9222,0.9202,0.9182,0.9162,0.9142,0.9122,0.9102,0.9082,0.9062,0.9042,0.9022,0.9002,0.8982,0.8962,0.8942,0.8921,0.8901,0.8881,0.8860,0.8840,0.8820,0.8799,0.8779,0.8758,0.8738,0.8717,0.8696,0.8676,0.8655,0.8634,0.8613,0.8593,0.8572,0.8551,0.8530,0.8509,0.8488,0.8467,0.8446,0.8425,0.8404,0.8383,0.8362,0.8341,0.8320,0.8299,0.8278,0.8257,0.8235,0.8214,0.8193,0.8171,0.8150,0.8129,0.8107,0.8086,0.8064,0.8043,0.8021,0.8000,0.7979,0.7957,0.7935,0.7914,0.7892,0.7871,0.7849,0.7828,0.7806,0.7784,0.7763,0.7741,0.7719,0.7698,0.7676,0.7654,0.7632,0.7610,0.7589,0.7567,0.7545,0.7523,0.7501,0.7479,0.7457,0.7435,0.7413,0.7391,0.7369,0.7347,0.7325,0.7303,0.7281,0.7259,0.7237,0.7215,0.7193,0.7170,0.7148,0.7126,0.7104,0.7082,0.7060,0.7037,0.7015,0.6993,0.6971,0.6948,0.6926,0.6904,0.6881,0.6859,0.6837,0.6814,0.6792,0.6770,0.6747,0.6725,0.6702,0.6680,0.6657,0.6635,0.6612,0.6590,0.6567,0.6545,0.6522,0.6500,0.6477,0.6455,0.6432,0.6410,0.6387,0.6365,0.6342,0.6319,0.6297,0.6274,0.6251,0.6229,0.6206,0.6183,0.6161,0.6138,0.6115,0.6092,0.6070,0.6047,0.6024,0.6001,0.5979,0.5956,0.5933,0.5910,0.5887,0.5865,0.5842,0.5819,0.5796,0.5773,0.5750,0.5727,0.5705,0.5682,0.5659,0.5636,0.5613,0.5590,0.5567,0.5544,0.5521,0.5498,0.5475,0.5452,0.5429,0.5406,0.5383,0.5360,0.5337,0.5314,0.5291,0.5268,0.5245,0.5222,0.5199,0.5176,0.5153,0.5130,0.5107,0.5084,0.5061,0.5038,0.5015,0.4992,0.4968,0.4945,0.4922,0.4899,0.4876,0.4853,0.4830,0.4806,0.4783,0.4760,0.4737,0.4714,0.4690,0.4667,0.4644,0.4621,0.4597,0.4574,0.4551,0.4528,0.4504,0.4481,0.4458,0.4435,0.4411,0.4388,0.4365,0.4341,0.4318,0.4295,0.4271,0.4248,0.4225,0.4201,0.4178,0.4154,0.4131,0.4108,0.4084,0.4061,0.4037,0.4014,0.3991,0.3967,0.3944,0.4154,0.4131,0.4108,0.4084,0.4061,0.4037,0.4014,0.3991,0.3967,0.3709,0.3685,0.3662,0.3638,0.3615,0.3591,0.3567,0.3544,0.3520,0.3497,0.3473,0.3449,0.3426,0.3402,0.3379,0.3355,0.3331,0.3308,0.3284,0.3260,0.3237,0.3213,0.3189,0.3165,0.3142,0.3118,0.3094,0.3071,0.3047,0.3023,0.2999,0.2976,0.2952,0.2928,0.2904,0.2880,0.2857,0.2833,0.2809,0.2785,0.2761,0.2738,0.2714,0.2690,0.2666,0.2642,0.2618,0.2594,0.2570,0.2547,0.2523,0.2499,0.2475,0.2451,0.2427,0.2403,0.2379,0.2355,0.2331,0.2307,0.2283,0.2259,0.2235,0.2211,0.2187,0.2163,0.2139,0.2115,0.2091,0.2067,0.2043]
#      return DiodeModel,DiodeCalibration[DiodeModel]
# =============================================================================

def DiodeCurve_Write_backup(CRVNum,DiodeModel):
    """
    Writes a Diode curve to the Lakeshore 335 temperature controller
    Diode curves are saved in the fname=Dict_TempDiode.txt
    usage:  DiodeCurve_Write(22,"SI435") to write to curve 22 the dictionary entry "SI435"
            DiodeCurve_SetInput("A",22,400)
    """
    fname="Dict_TempDiode.txt"
    PV="29idARPES:LS335:TC1:serial.AOUT"

    t=1
    index=1
    #Curve Header
    DiodeDict=read_dict(fname)
    CRVHDR,CRVList=DiodeModel,DiodeDict[DiodeModel]
    
    cmd="CRVHDR "+str(CRVNum)+","+CRVHDR+",SN,2,"+str(len(CRVList)-1)+",1"
    print(cmd)
    caput(PV,cmd,wait=True,timeout=1800)
    while t <len(CRVList):
        if(t>=0 and t<30):
            countby=1
        elif(t>=30 and t<230):
            countby=2
        elif(t>=230):
            countby=5
        cmd="CRVPT "+str(CRVNum)+","+str(index)+","+str(CRVList[t])+","+str(t)
        #print cmd
        caput(PV,cmd,wait=True,timeout=1800)
        #sleep(1)
        t=t+countby
        index+=1
    #write 0,0 to indicate list is done
    cmd="CRVPT "+str(CRVNum)+","+str(index)+","+str(CRVList[0])+","+str(0)
    caput(PV,cmd,wait=True,timeout=1800)
    print("last point = "+str(index))

def DiodeCurve_Write(CRVNum,DiodeModel,run=True): #reversing order since it seems that the curve needs to go from high to low based on the built-in
    """
    Writes a Diode curve to the Lakeshore 335 temperature controller
    Diode curves are saved in the fname=Dict_TempDiode.txt

    run=True to write to the Lakeshoe
    run=False to print only

    usage:  DiodeCurve_Write(22,"SI435") to write to curve 22 the dictionary entry "SI435"
            DiodeCurve_SetInput("A",22,400)
    """
    fname="Dict_TempDiode.txt"
    PV="29idARPES:LS335:TC1:serial.AOUT"


    #Curve Header
    CRVList=read_dict(fname)[DiodeModel]
    cmd="CRVHDR "+str(CRVNum)+","+DiodeModel+",SN,2,"+str(len(CRVList)-1)+",1"
    if run == True:
        caput(PV,cmd,wait=True,timeout=1800)
    else:    
        print(cmd)
    
    #Writing the individual terms (model 335 only supports index:1-200)
    T1=50
    T2=230
    T3=len(CRVList)

    T=np.arange(0,T1,1)
    V=np.array(CRVList[0:T1])
    
    T=np.append(T,np.arange(T1,T2,2))
    V=np.append(V,np.array(CRVList[T1:T2:2]))

    T=np.append(T,np.arange(T2,T3,5))
    V=np.append(V,np.array(CRVList[T2:T3:5]))
    
    #reverse order
    T=T[::-1]
    V=V[::-1]
    
    for i,t in enumerate(T):
        cmd="CRVPT "+str(CRVNum)+","+str(i+1)+","+str(V[i])+","+str(t)
        #cmd="index,v,t"+str(i+1)#+","+str(V[i])+","+str(t)
        if run == True:
            caput(PV,cmd,wait=True,timeout=1800)
        else:    
            print(cmd)

def DiodeCurve_SetInput(Channel,Curve,Tmax):
    """
    Sets the diode curve for a given channel on the Lakeshore 335 temperature controller
        DiodeCurve_SetInput("A",22,400)
        Channel: A or B
        Curve: set by DiodeCurve_Write(22,"SI435")
        Tmax: max temperature for that diode
    (pg 118 of manual)
    """
    
    PV="29idARPES:LS335:TC1:serial.AOUT"
    #Set curve info
    cmd="INTYPE "+Channel+","+"1,0,0,0,1"
    caput(PV,cmd,wait=True,timeout=1800)
    #Select curve
    cmd="INCRV "+Channel+","+str(Curve)
    caput(PV,cmd,wait=True,timeout=1800)
    #Set temperature Limit
    cmd="TLIMIT "+Channel+","+str(Tmax)
    caput(PV,cmd,wait=True,timeout=1800)

##############################################################################################################
##############################             PID Settings            ##############################
##############################################################################################################


#Setting the PID
#    Set P=10, I=0, D=0; Set T and range,
#        if T oscilate above setpoint, P/=2
#        if T doesn't reach setpoint, P*=2
#        if T swings above setpoint but then settle below use this P
#    Set I=10; smaller I, more reactive (approximately time(sec) for one full oscillation period
#    Set D=I/4
#Lakeshore 355 I = time in seconds for one oscilation / 1000; D=50-100 for starters


def PID_dict(which,T): #Dictionary of PID setting to try for the ARPES chamber
    """Dictionary for common PID setting for the ARPES system.
    Since the PID is dependent on the cooling power, this will change with the cryogen and the flow rate:
        - Flow = "LHe,LN" =>  LHe = needle valve = "on" and flow = 70
    """
    PID={}
#    PID[which,T]=[P,I,D,Range]    Range=HIGH,MEDIUM,LOW,OFF
    PID['RT', 378.0]=[200.0,0.0,0.0,'MEDIUM']
    PID['RT', 375.0]=[200.0,0.0,0.0,'MEDIUM']
    PID['RT', 338.0]=[100.0,0.0,0.0,'MEDIUM']
    PID['RT', 298.0]=[20.0,0.0,0.0,'LOW']
    PID['GHe', 378.0]=[210.0,0.0,0.0,'MEDIUM']
    PID['GHe', 375.0]=[210.0,0.0,0.0,'MEDIUM']
    PID['GHe', 338.0]=[130.0,0.0,0.0,'MEDIUM']
    PID['GHe', 298.0]=[60.0,0.0,0.0,'MEDIUM']
    PID['GHe', 250.0]=[10.0,0.0,0.0,'LOW']
    PID['LHe',298.0]=[20.0,5.0,1.0,'HIGH']     # +/- 1.1 deg, over 10 min, heater power 53%
    PID['LHe',200.0]=[10.0,5.0,1.0,'HIGH']     # +/- 1.1 deg, over 10 min, heater power 53%
    PID['LHe',150.0]=[200.0,0.1,0,'HIGH']     # Stablized at 153, heater power 43%
    PID['LHe',180.0]=[200.0,0.1,0,'HIGH']
    PID['LHe',230.0]=[200.0,0.1,0,'HIGH']
    PID['LHe',300.0]=[200.0,0.1,0,'HIGH']
    PID['LHe',40.0]=[200.0,0.1,0,'HIGH']     #
    PID['LN2',230]=[10.0,0.6,100,'HIGH']        #stable 237.83, needle valve=ON; flow 6 half turns from max)
    PID['LN2',180]=[50.0,4,100,'MEDIUM']
    return PID[which,T]

def PID_set(which,T,heater='ON'):
    """
    Uses preset PID settings as defined in PID_dict()
    To cool down: heater='OFF'

    """
    P,I,D,Range=PID_dict(which,T)
    caput("29idARPES:LS335:TC1:P1",P)
    caput("29idARPES:LS335:TC1:I1",I)
    caput("29idARPES:LS335:TC1:D1",D)
    if heater == 'ON':
        caput("29idARPES:LS335:TC1:HTR1:Range",Range)
    elif heater == 'OFF':
        caput("29idARPES:LS335:TC1:HTR1:Range",'OFF')
    print('\nP = ',PID_dict(which,T)[0])
    print('I = ',PID_dict(which,T)[1])
    print('D = ',PID_dict(which,T)[2])
    print('Range = ',PID_dict(which,T)[3])


def SetT_Sample(which,T,precision=5,minutes=15,offset=6):
    """
    Sets PID settings for a given set point as defined in PID_dict().
    Available set points:
        which = 'RT' : T = 298, 338, 375
        which = 'LHe': T = 150, 200
        which = 'GHe': T = 250, 298, 338, 370
        which = 'LN2': T = 230, 180
        precision is temperature in K
    """
    current_T=caget("29idARPES:LS335:TC1:IN1")
    print('\nSet T to '+ str(T)+' K   @ '+ dateandtime())
    if T>current_T:
        PID_set(which,T,'ON')
        Range=PID_dict(which,T)[3]
        SetT_Up(T,offset,Range,precision,minutes)
    else:
        PID_set(which,T,'OFF')
        Range=PID_dict(which,T)[3]
        SetT_Down(T,offset,Range,precision,minutes)
    caput("29idARPES:LS335:TC1:OUT1:SP",T)


def SetT_Up(T,offset,Range,precision=5,minutes=15):
    if Range=='LOW':    Range=1
    if Range=='MEDIUM': Range=2
    if Range=='HIGH':   Range=3
    t=15
    u=0
    caput('29idARPES:LS335:TC1:OUT1:SP',T)                # set the set point to T
    while True:                            # while TA < T
        TA=caget('29idARPES:LS335:TC1:IN1')                # get current temperature at the sample
        TB=caget('29idARPES:LS335:TC1:IN2')                # get current temperature (B=cold finger)
        if TA<T-precision:                                  # if it hasn't reach SP
            caput("29idARPES:LS335:TC1:HTR1:Range",min(Range,3))            # increase heater range to Range +1
            while True:                                # while TB < T+offset:
                TB=caget('29idARPES:LS335:TC1:IN2')                    # get current temperature at the cold finger
                if (t%120)==0:
                    print('\nTA = ',TA,'  TB = ',TB, '  @  ',dateandtime())
                if TB<(T+offset) and t<=minutes*60:                            #if it hasn't reach the SP+offser
                    sleep(15)
                    t+=15
                    #print t, TA, TB
                elif TB<(T+offset) and t>minutes*60:
                        heater_power=caget('29idARPES:LS335:TC1:HTR1')
                        heater_range=caget('29idARPES:LS335:TC1:HTR1:Range')
                        if heater_power > 90:
                            caput("29idARPES:LS335:TC1:HTR1:Range",min(heater_range+1,3))
                            print('Change Range to',caget('29idARPES:LS335:TC1:HTR1:Range'),'  @  ',dateandtime())
                        elif heater_range==3 or heater_power<=90:
                            P=caget("29idARPES:LS335:TC1:P1")
                            caput("29idARPES:LS335:TC1:P1",P*1.5)
                            print('Change P to',caget("29idARPES:LS335:TC1:P1"),'  @  ',dateandtime())
                        t=0
    
                else:                                    #else
                    break                                    # break
            caput("29idARPES:LS335:TC1:HTR1:Range",'OFF')                # turn off the heater
        elif TA>T-precision:                            # if it has reach the set point
            break                                    # break
    print('TA = ',TA,'  TB = ',TB, '  @  ',dateandtime())        # print temperatures
    caput("29idARPES:LS335:TC1:HTR1:Range",Range)            # set the heater range to preset value






def SetT_Down(T,offset,Range,precision=5,minutes=15):
    t=0
    caput('29idARPES:LS335:TC1:OUT1:SP',T)                # set the set point to T
    while True:                            # while TA < T
        TA=caget('29idARPES:LS335:TC1:IN1')
        TB=caget('29idARPES:LS335:TC1:IN2')
        if (t%120)==0:
            print('\nTA = ',TA,'  TB = ',TB, '  @  ',dateandtime())
        if TA>T+precision:
            sleep(15)
            t+=15
        elif t>minutes*60:
                P=caget("29idARPES:LS335:TC1:P1")
                caput("29idARPES:LS335:TC1:P1",P/1.5)
                t=0
        else:
            break
    caput("29idARPES:LS335:TC1:HTR1:Range",Range)
    print('TA = ',TA,'  TB = ',TB, '  @  ',dateandtime())


# def Get_PID(which='LHe'):
#     T=caget("29idARPES:LS335:TC1:IN1")
#     SP=caget("29idARPES:LS335:TC1:OUT1:SP")
#     P=caget("29idARPES:LS335:TC1:P1")
#     I=caget("29idARPES:LS335:TC1:I1")
#     D=caget("29idARPES:LS335:TC1:D1")
#     Range=caget("29idARPES:LS335:TC1:HTR1:Range",as_string=True)
# #    print SP,P,I,D,Range
#     print("Current T:", T,'K')
#     print("PID[\'"+which+"\',"+str(SP)+"]=["+str(P)+","+str(I)+","+str(D)+",\'"+Range+"\']")






##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################


######         ScanFunctions_RSXS.py:
#    - RSXS Utilities
#    - SI9700 control
#    - MCP Scan Setting
#    - Preset Positions
#    - Kappa to Euler Conversion
######    

##############################################################################################################
##############################             RSXS Utilities         ##############################
##############################################################################################################
def Reset_MPA_HV():
    """
    resetting the SRS which controls the MPA HV
    Model: SRS PS350
    ip = "164.54.118.57"
    """
    ip = "164.54.118.57"
    # Open TCP connect to poet 1234 of GPIB-ETHERNET
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    sock.settimeout(0.1)
    sock.connect((ip, 1234))

    # Set mode as CONTROLLER
    sock.send(b'++mode 1\n')

    # specify GPIB address of device being controlled
    addr = "14"
    str1="++addr"+addr+'\n'
    sock.send(bytes(str1,'utf-8'))

    # reset SRS PS350
    #sock.send("*RST\n")

    # turn the high voltage on, clearing any current or voltage trips
    sock.send(b"HVON\n")

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


def gain_dict(x):
    gain_state={}
    gain_state={1:0, 2:1, 5:2, 10:3, 20:4, 50:5, 100:6, 200:7, 500:8}
    try:
        x=gain_state[x]
    except KeyError:
        print("WARNING: Not a valid gain!")
    return x

def unit_dict(x):
    unit_state={}
    unit_state={'pA':0, 'nA':1, 'uA':2, 'mA':3}
    try:
        u=unit_state[x]
    except KeyError:
        print("WARNING: Not a valid unit!")
    return u


def setgain(det,gain,unit):
    """
    det  = 'SRS1', 'SRS2', 'SRS3', 'SRS4','mesh','tey','d3','d4'
    gain = 1,2,5,10,20,50,100,200,500
    unit = 'pA, 'nA', 'uA', 'mA'
    """
    def SRS_dict(x):
        SRS_det={}
        SRS_det={'SRS1':1, 'SRS2':2, 'SRS3':3, 'SRS4':4,'mesh':1, 'tey':2, 'd3':3, 'd4':4}
        try:
            n=SRS_det[x]
        except KeyError:
            print("WARNING: Not a valid gain!")
        return n
    n=SRS_dict(det)
    g=gain_dict(gain)
    u=unit_dict(unit)
    pvg='29idd:A'+str(n)+'sens_num.VAL'
    pvu='29idd:A'+str(n)+'sens_unit.VAL'
    caput(pvu,u)
    caput(pvg,g)

def Get_SRS(n,short=True):
    invert=caget('29idd:A'+str(n)+'invert_on.VAL',as_string=True)
    currentUnit=caget('29idd:A'+str(n)+'sens_unit.VAL',as_string=True)
    currentValue=caget('29idd:A'+str(n)+'sens_num.VAL',as_string=True)
    offsetValue=caget("29idd:A"+str(n)+"offset_num.VAL",as_string=True)
    offsetUnit=caget("29idd:A"+str(n)+"offset_unit.VAL",as_string=True)
    offsetSign=caget("29idd:A"+str(n)+"offset_sign.VAL",as_string=True)
    offsetFactor=caget("29idd:A"+str(n)+"off_u_put.VAL",as_string=True)
    print('Gain: '+currentValue+' '+currentUnit+'  (invert '+invert+')')
    print('Baseline: '+offsetSign+' '+offsetFactor+' x '+offsetValue+" "+offsetUnit)
    if short == False:
        filterType=caget('29idd:A'+str(n)+'filter_type.VAL',as_string=True)
        filterLow=caget('29idd:A'+str(n)+'low_freq.VAL',as_string=True)
        filterHigh=caget('29idd:A'+str(n)+'high_freq.VAL',as_string=True)
        blank=caget('29idd:A'+str(n)+'blank_on.VAL',as_string=True)
        biasOnOff=caget('29idd:A'+str(n)+'bias_on.VAL',as_string=True)
        biasValue=caget('29idd:A'+str(n)+'bias_put.VAL',as_string=True)
        print('Filter: '+filterType+' - Low/High: '+filterLow+'  -'+filterHigh)
        print('Bias: '+biasOnOff+'- '+biasValue)
        print('Blank: '+blank)
        
           


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

def kth0_set(value):
    foo=input_d('Are you sure you want to reset kth0 (Y or N)? >')
    if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
        foo=input_d('Are you aligning at theta 0 or 180 (0 or 180)? >')
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




##############################################################################################################
##############################             SI9700 Kludge         ##############################

##############################################################################################################
def ResetPID():
    caput('29idd:tc1:SetPID_1.INPA','')
    caput('29idd:tc1:SetPID_1.INPB','')
    caput('29idd:tc1:SetPID_1.INPC','')

def GetCurrentPID():
    T=caget('29idd:tc1:getVal_A.VAL')
    P=caget('29idd:tc1:SetPID_1.A')
    I=caget('29idd:tc1:SetPID_1.B')
    D=caget('29idd:tc1:SetPID_1.C')
    return T,P,I,D

def SetTempSetting(T,P,I,D):
    #Change the sample temperature T with the specified PID values
    caput('29idd:tc1:getVal_A.VAL',T)
    caput('29idd:tc1:SetPID_1.A',P)
    caput('29idd:tc1:SetPID_1.B',I)
    caput('29idd:tc1:SetPID_1.C',D)

# GetCurrentPID => (60.0121, 8.0, 50.0, 12.0) ## Temperature overshoots no more than 5.5 degrees
#it takes about 3 min to stablize at any temp
#cooling is about 10 degrees/min
##############################################################################################################
##############################             MCP scan Setting          ##############################
##############################################################################################################


def eV2Lambda(eV):
    """ Converts energy (eV) into wavelenght (Angstrom)"""
    h=4.135667516e-15
    c=299792458
    E=h*c/eV*1e9*10
    return E

def Lambda2eV(E):
    """ Converts wavelenght (Angstrom) into energy (eV)"""
    h=4.135667516e-15
    c=299792458
    eV=h*c/E*1e9*10
    return eV



def Scan_th2th_sensitivity(th_table,gainN_table,gainU_table,srs_num=2,settling_time=0.1,**kwargs):
    """
    Scans th2th with variable gain on SRS# (srs_num).
    Gain is specified for a given th2th range by building tables as follow:

    th_table = np.array([])
    gn_table = np.array([])
    gu_table = np.array([])
    for i in RangeUp(10,20,0.5):
        th_table = np.append(th_table, i)
        gn_table = np.append(gn_table, gain_dict(2))
        gu_table = np.append(gu_table, unit_dict('mA'))
    for i in RangeUp(20.5,40,0.5):
        th_table = np.append(th_table, i)
        gn_table = np.append(gn_table, gain_dict(1))
        gu_table = np.append(gu_table, unit_dict('uA'))
    for i in RangeUp(40.5,60,0.5):
        th_table = np.append(th_table, i)
        gn_table = np.append(gn_table, gain_dict(10))
        gu_table = np.append(gu_table, unit_dict('pA'))
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
       
    """
    scanIOC='Kappa'
    scanDIM=1
    pv='29id'+scanIOC+':scan'+str(scanDIM)

    kth_offset=caget("29idKappa:userCalcOut1.G")

    kth_VAL="29idKappa:m8.VAL"
    kth_RBV="29idKappa:m8.RBV"
    tth_VAL="29idKappa:m9.VAL"
    tth_RBV="29idKappa:m9.RBV"
    gn_VAL="29idd:A"+str(srs_num)+"sens_num.VAL"
    gu_VAL="29idd:A"+str(srs_num)+"sens_unit.VAL"

    Scan_Progress(scanIOC,scanDIM)

    kth_table=th_table+kth_offset
    tth_table=th_table*2

    print("\nDon't forget to clear extra positionners at the end of the scan if you were to abort the script using the function:")
    print("                Clear_Scan_Positioners('Kappa',1)")

    caput(pv+".PDLY",settling_time)
    Scan_FillIn(kth_VAL,kth_RBV,scanIOC,scanDIM,0,0,0)
    Scan_FillIn_Pos2(tth_VAL,tth_RBV,scanIOC,scanDIM,0,0)
    Scan_FillIn_Pos3(gn_VAL,"",scanIOC,scanDIM,0,0)
    Scan_FillIn_Pos4(gu_VAL,"",scanIOC,scanDIM,0,0)
    caput(pv+'.P1SM','TABLE')
    caput(pv+'.P1PA',kth_table)
    caput(pv+'.P2SM','TABLE')
    caput(pv+'.P2PA',tth_table)
    caput(pv+'.P3SM','TABLE')
    caput(pv+'.P3PA',gainN_table)
    caput(pv+'.P4SM','TABLE')
    caput(pv+'.P4PA',gainU_table)
    caput(pv+'.NPTS',len(kth_table))
 
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)
    Clear_Scan_Positinners(scanIOC,scanDIM)
    caput(pv+'.P1SM','LINEAR')
    caput(pv+'.P2SM','LINEAR')
    caput(pv+'.P3SM','LINEAR')
    caput(pv+'.P4SM','LINEAR')





##############################################################################################################
##############################             Preset Positions        ##############################
##############################################################################################################


## FR: I want people to look and think when they move!


def Kappa_ResetPreset():
    KappaGrazing_StrSeq()
    KappaTransfer_StrSeq()


def kphiReset(ang):
    caput("29idKappa:m1.SET",1)    # 1 = Set
    sleep(0.5)
    caput("29idKappa:m1.VAL",ang)
    sleep(0.5)
    caput("29idKappa:m1.SET",0)    # 0 = Use
    print(("\nkphi has been reset to",ang))


def SmarAct_Enable():
    caput('29idKappa:m1.SPMG',3)  # 3=Go
    caput('29idKappa:m2.SPMG',3)
    caput('29idKappa:m3.SPMG',3)
    caput('29idKappa:m4.SPMG',3)

def SmarAct_Disable():
    caput('29idKappa:m1.SPMG',0)  # 1=Stop
    caput('29idKappa:m2.SPMG',0)
    caput('29idKappa:m3.SPMG',0)
    caput('29idKappa:m4.SPMG',0)



##############################################################################################################
##############################             Kappa to Euler Conversion        ##############################
##############################################################################################################




def Kappa2Fourc(ang1,ang2,ang3,conversion,k_arm=50):

    a,b,c=0,0,0
    if conversion=='Kappa':
        a,b,c=EtoK(ang1,ang2,ang3,k_arm)
        print(("\n"+"th  = "+str(ang1)))
        print(("chi = "+str(ang2)))
        print(("phi = "+str(ang3)))
        print("~~~~~~~~")
        print(("kth  = "+str(a)))
        print(("kap  = "+str(b)))
        print(("kphi = "+str(c)+"\n"))
    elif    conversion=='fourc':
        a,b,c=KtoE(ang1,ang2,ang3,k_arm)
        print(("\n"+"kth  = "+str(ang1)))
        print(("kap  = "+str(ang2)))
        print(("kphi = "+str(ang3)))
        print("~~~~~~~~")
        print(("th  = "+str(a)))
        print(("chi = "+str(b)))
        print(("phi = "+str(c)+"\n"))
    else:
        print('2nd argument invalid; please choose one of the following:')
        print('"Kappa" or  "fourc"')
    return a,b,c



def EtoK(e_theta,e_chi,e_phi,k_arm=50):
    conv = pi/180.0
    kth_offset=caget('29idKappa:userCalcOut1.G')
    if(abs(e_chi)> 2.0*k_arm):
        print("Chi should be no more than twice the Kappa arm offset angle.")
        kth,kap,kphi=0,0,0
    else:
        print(("Calculating Kappa angles using kth0 = "+str(kth_offset)))
        k_ang = k_arm*conv
        delta = asin( - tan(e_chi*conv/2.0) / tan(k_ang) )
        k_theta = e_theta*conv - delta
        k_kappa = 2.0 * asin( sin(e_chi*conv/2.0) / sin(k_ang))
        k_phi   = e_phi*conv - delta
        #print k_theta, k_kappa,k_phi
        kth = rounder(k_theta)-(57.045-kth_offset)
        kap = rounder(k_kappa)
        kphi  = rounder(k_phi)
        #print delta
    return (kth,kap,kphi)




def KtoE(k_theta,k_kappa,k_phi,k_arm=50):
    conv = pi/180.0
    kth_offset=caget('29idKappa:userCalcOut1.G')
    print(("Calculating Euler angles using kth0 = "+str(kth_offset)))
    k_ang = k_arm*conv
    delta = atan( tan(k_kappa*conv/2.0) * cos(k_ang) )
    e_theta = k_theta*conv - delta
    e_chi   = 2.0 * asin( sin(k_kappa*conv/2.0) * sin(k_ang) )
    e_phi   = k_phi*conv - delta
    #print round(e_theta,1),round(e_phi,1),round(e_chi,1)
    theta = rounder(e_theta)+(57.045-kth_offset)
    chi   = rounder(e_chi)        # convert from rad to deg
    phi   = rounder(e_phi)
    #print round(delta,1)
    return (theta,chi,phi)


def rounder(val):        # convert from rad to deg
    conv = pi/180.0
    roundVal=round(1000.0*val/conv)/1000.0
    return roundVal


def mv4C(th,chi,phi):
    caput('29idKappa:Euler_Theta',th,wait=True,timeout=18000)
    caput('29idKappa:Euler_Chi',chi,wait=True,timeout=18000)
    caput('29idKappa:Euler_Phi',phi,wait=True,timeout=18000)
    new_th=caget('29idKappa:Euler_ThetaRBV')
    new_chi=caget('29idKappa:Euler_ChiRBV')
    new_phi=caget('29idKappa:Euler_PhiRBV')
    print('th = {:.3f}\tchi = {:.3f}\tphi = {:.3f}'.format(new_th,new_chi,new_phi))






##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################


######         ScanFunctions_MPA.py:
#    - HV Control
#    - MCP Scripts
######    


##############################################################################################################
##############################                HV Control              ##############################
##############################################################################################################


def MPA_HV_Set(volt):
    volt=min(volt,2990)
    caput("29idKappa:userCalcOut9.A",volt,wait=True,timeout=18000)
    sleep(1)
    RBV=caget("29idKappa:userCalcOut10.OVAL")
    print("HV = "+str(RBV)+" V")


def MPA_HV_ON():
    n=1
    tth = caget('29idKappa:m9.DRBV')
    if -16<= tth <=-6:
        print('MPA OFF: detector in direct beam (-5 < mcp < 5); move away before turning HV ON.')
    else:
        caput('29iddMPA:C1O',1,wait=True,timeout=18000)
        caput('29iddMPA:C1O',0,wait=True,timeout=18000)
        caput("29iddMPA:C0O",n,wait=True,timeout=18000)
        print("MPA - HV On")

def MPA_HV_OFF():
    n=0
    caput("29iddMPA:C0O",n,wait=True,timeout=18000)
    print("MPA - HV Off")


def MPA_HV_Reset():
    caput('29iddMPA:C1O',1)
    print("MPA - Reset")
    
    
def MPA_HV_scan(start=2400,stop=2990,step=10):
    cts(1)
    VAL='29idKappa:userCalcOut9.A'
    RBV='29idKappa:userCalcOut10.OVAL'
    Scan_FillIn(VAL,RBV,'Kappa',1,start,stop,step)
    caput('29idKappa:scan1.PDLY',1) # positionner settling time
    Scan_Go('Kappa')

##############################################################################################################
##############################                MCP Scripts              ##############################
##############################################################################################################




def AD_ROI_SetUp(AD,ROInum,xcenter=500,ycenter=500,xsize=50,ysize=50,binX=1,binY=1):  
    """
    AD = "29id_ps4"
    AD = "29iddMPA"
    """
    # roiNUM=1  MPA_ROI_SetUp(535,539,50,50)  center of MCP
    
    ADplugin=AD+':ROI'+str(ROInum)+':'
    xstart=xcenter-xsize/2.0
    ystart=ycenter-ysize/2.0
    caput(ADplugin+'MinX',xstart)
    caput(ADplugin+'MinY',ystart)
    caput(ADplugin+'SizeX',xsize)
    caput(ADplugin+'SizeY',ysize)
    caput(ADplugin+'BinX',binX)
    caput(ADplugin+'BinY',binY)
    caput(ADplugin+'EnableCallbacks','Enable')
    print(ADplugin+' - '+caget(ADplugin+'EnableCallbacks_RBV',as_string=True))
    #MPA_ROI_Stats(roiNUM)
    
def AD_OVER_SetUp(AD,ROInum,OVERnum,linewidth=5,shape='Rectangle'):
    """
    AD = "29id_ps4"
    AD = "29iddMPA"
    shape= 'Cross', 'Rectangle', 'Ellipse','Text'
    """
    OVER1=AD+":Over1:"+str(OVERnum)+":"
    ROI=AD+":ROI"+str(ROInum)+":"
    
    caput(ROI+'EnableCallbacks','Enable')
    caput(OVER1+"Name","ROI"+str(ROInum))
    caput(OVER1+"Shape",shape)
    caput(OVER1+"Red",0)
    caput(OVER1+"Green",255)
    caput(OVER1+"Blue",0)
    caput(OVER1+'WidthX',linewidth)
    caput(OVER1+'WidthY',linewidth)
    
    caput(OVER1+"PositionXLink.DOL",ROI+"MinX_RBV CP")
    caput(OVER1+"SizeXLink.DOL",ROI+"SizeX_RBV CP")
    caput(OVER1+"PositionYLink.DOL",ROI+"MinY_RBV CP")
    caput(OVER1+"SizeYLink.DOL",ROI+"SizeY_RBV CP")
   
    caput(OVER1+"Use","Yes")
    
    

def MPA_ROI_SetUp(roiNUM=1,xcenter=535,ycenter=539,xsize=50,ysize=50,binX=1,binY=1):  
    # roiNUM=1  MPA_ROI_SetUp(535,539,50,50)  center of MCP
    AD_ROI_SetUp('29iddMPA',roiNUM,xcenter,ycenter,xsize,ysize,binX,binY)
    pv="29iddMPA:ROI"+str(roiNUM)+':'
    MPA_ROI_Stats(roiNUM)
    
def MPA_ROI_SetAll(xcenter=535,ycenter=539):
    MPA_ROI_SetUp(1,xcenter,ycenter,xsize=50,ysize=50)
    MPA_ROI_SetUp(2,xcenter,ycenter,xsize=100,ysize=100)
    MPA_ROI_SetUp(3,xcenter,ycenter,xsize=150,ysize=150)
    MPA_ROI_SetUp(4,xcenter,ycenter,xsize=200,ysize=200)
    
    
def MPA_ROI_Stats(roiNUM):
    pvROI="29iddMPA:ROI"+str(roiNUM)+':'
    pvSTATS="29iddMPA:Stats"+str(roiNUM)+':'
    caput(pvSTATS+'NDArrayPort','ROI'+str(roiNUM))
    caput(pvSTATS+'EnableCallbacks','Enable')
    caput(pvSTATS+'ArrayCallbacks','Enable')
    caput(pvSTATS+'ComputeStatistics','Yes')
    caput(pvSTATS+'ComputeCentroid','Yes')
    caput(pvSTATS+'ComputeProfiles','Yes')

def _MPA_Trigger_Callback(BeforeAfter,saveImg=False,**kwargs):
    """
    used for triggering the MPA in the scanRecord, reset Proc1 and waits for finish
    
    BeforeAfter = before, sets up and puts trigger in detTrigNum
                = after, clear detTrigNum amd resets to defaults
    
    saveImg = False used for appropriate trigger of ROIs
            = True also saves an image based on ADplugin type
    
    by default ADplugin = 29iddMPA:TIFF1: 
        can use 29iddMPA:HDF1:
    """

    kwargs.setdefault("ADplugin","29iddMPA:TIFF1:")

    ADplugin=kwargs["ADplugin"]
    Proc1="29iddMPA:Proc1:"
    
    #All this should moved into the MPA IOC 
    Busy="29idcScienta:mybusy2"
    PVstr1="29idTest:userStringSeq1"
    PVstr2="29idTest:userStringSeq2"
    PVcalcOut9="29idTest:userCalcOut9"
    PVcalcOut10="29idTest:userCalcOut10"
    if BeforeAfter=="makeStringSeqCalcCout":
        #userCalcOut9 - MPA-busy
        caput(PVcalcOut9+".DESC","MPA busy")
        caput(PVcalcOut9+".INPA",Busy+" CP")
        caput(PVcalcOut9+".OOPT",'Transition to non-zero')
        caput(PVcalcOut9+".OUT",PVstr1+".PROC PP")
        #Enable CalcOut10 if enable exists
        #userStringSeq1 - MPA-start
        caput(PVstr1+".DESC","MPA start")
        caput(PVstr1+".LNK1", Proc1+"ResetFilter PP")
        caput(PVstr1+".STR1","Yes")
        #userCalcOut9 - MPA-Proc1waiting
        caput(PVcalcOut10+".DESC","MPA Proc1waitng")
        caput(PVcalcOut10+".INPA",Proc1+"NumFilter_RBV")
        caput(PVcalcOut10+".INPB",Proc1+"NumFiltered_RBV")
        caput(PVcalcOut10+".OOPT",'Transition to non-zero')
        caput(PVcalcOut10+".OUT",PVstr2+".PROC PP")
        #userStringSeq1 - MPA-writeDone
        caput(PVstr2+".DESC","MPA writeDone")
        caput(PVstr2+".LNK1", ADplugin+"WriteFile PP")
        caput(PVstr2+".STR1","Write")
        caput(PVstr2+".LNK1", Busy+" PP")
        caput(PVstr2+".STR1","Done")
        
    detTrigNum=kwargs["detTrigNum"]
    
    if BeforeAfter=="before":
        caput(ADplugin+"AutoResetFilter","Yes")
        if saveImg:
            caput(ADplugin+"AutoSave", "No")
            caput(ADplugin+"EnableCallbacks", "Enable")
        

    if BeforeAfter=="after":
        caput(ADplugin+"AutoResetFilter","No")
        if saveImg:
            caput(ADplugin+"EnableCallbacks", "Disable")
            caput(ADplugin+"AutoSave", "Yes")

    trigger=Busy
    return Busy

def _MPA_Prefix(**kwargs):
    """
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("debug",False)
    
    scanIOC=kwargs['scanIOC']
    fpath=join(dirname(dirname(MDA_CurrentDirectory(scanIOC))),"mpa",'')
    nextMDA = caget("29id"+scanIOC+":saveData_scanNumber")
    prefix="mda"+str.zfill(str(nextMDA),4)+"_mpa"

def MPA_Trigger(BeforeAfter, saveImg, **kwargs):
    """
    Sets up the ScanRecord to trigger the MPA 
        
    saveImg = False used for appropriate trigger of ROIs
            = True also saves an image based on ADplugin type  
    
 
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    kwargs.setdefault("detTrigNum",2)
    
    cnt=floor(caget("29idMZ0:scaler1.TP"))
    caput("29iddMPA:Proc1:NumFilter",cnt)
    
    Busy=_MPA_Trigger_Callback(BeforeAfter,saveImg=saveImg,**kwargs)
    scanPV="29id"+kwargs["scanIOC"]+":scan"+str(kwargs["scanDIM"])
                         
    #adding the MPA to the scanRecord trigger
    if BeforeAfter == "before":
        _MPA_Prefix(**kwargs)
        caput(scanPV+".T"+str(kwargs["detTrigNum"])+"PV", Busy)
    
    else:
        caput(scanPV+".T"+str(kwargs["detTrigNum"])+"PV", "")
        
        






##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################


######         ScanFunctions_cmd.py:
#    - Utilities
#    - BL Commands
#    - ARPES & Kappa move
#    - ARPES & Kappa scan
#    - Move Sample
######    


##############################################################################################################
############################ Attempt to define branch as global variable #####################################
##############################################################################################################


#global mybranch
#print("ScanFunctions_cmd.py loaded.")
#
#def input_29id():
#    try:
#        print('\n\n Which branch are you working on?')
#        print(' Please type: c (ARPES) or d (Kappa)  or e (RSoXS)> ')
#        foo = input()
#        return foo
#    except:
#        return 0
#
#
#
#def Prompt_29id():
#    reply_29id=input_29id()
#    if reply_29id not in ['c','d']:
#        print("\n WARNING: Invalid answer!")
#        mybranch=None
#    elif reply_29id is 'c':
#        print('\n ARPES it is... Thank you!')
#        mybranch=reply_29id
#    elif reply_29id is 'd':
#        print('\n Kappa it is... Thank you!')
#        mybranch=reply_29id
#    elif reply_29id is 'e':
#        print('\n RSoXS it is... Thank you!')
#        mybranch=reply_29id
#    return mybranch
#
#
#def Test_MyBranch():
#    global mybranch
#    print('Does mybranch exist?', mybranch)

##############################################################################################################
##############################                       Utilities                        ##############################
##############################################################################################################


def SendText(msg,which='user'):
    """
    
    which = 'user' or 'staff'
    
    Edit the following file with the correct email/phone number:
        [sleepy /home/beams22/29ID/bin] pvMailSomething        # for staff
        [sleepy /home/beams22/29IDUSER/bin] pvMailUser        # for user
        
    Use the following website to figure out carriers email:
        https://20somethingfinance.com/how-to-send-text-messages-sms-via-email-for-free/
    
    In a terminal, run the screen session:
        pvMailUser (or pvMailSomething)
        
    To kill the screen session:
        screen -ls                         #show list of screen session
        screen -r screen#              #reattached to a given screen session
        screen -XS screen# kill         #kill a given screen session
        

    """
    if which == 'staff':n='6'
    elif which == 'user':n='7'
    caput('29idb:userCalcOut'+n+'.DESC',msg)
    caput('29idb:userCalcOut'+n+'.A',0)
    sleep(1)
    caput('29idb:userCalcOut'+n+'.A',1)
    print('Sending text/email')


def AbortScript():
    """
    Example:
        while True:
                try:
                print 'do something'
                sleep(5)
                except KeyboardInterrupt:
                if AbortScript() == 'y':
                        break
    """
    try:
        print('\n\nWARNING: Do you want to abort?')
        print('Type y to ABORT, anything else to CONTINUE >')
        foo = input()
        return foo
    except KeyboardInterrupt as e:
        raise e


##############################################################################################################
##############################               BL commands            ##############################
##############################################################################################################

def energy(val,c=1,m3r=True):
    """
    Sets the beamline energy: insertion device + mono + apertures.
    Use c < 1 to kill flux density.
    """
    SetBL(val,c)
    SetMono(val)
    if m3r == True:
        if CheckBranch() == 'd':
            print('\nalign_m3r()')
            try:
                align_m3r()
                sleep(1)
                if caget('29id_m3r:RY_POS_SP') == -16.52:
                    align_m3r(debug=True)
            except:
                print('Unable to align; check camera settings.')
        


def mono(val):
    """
    Sets the mono energy (insertion device & apertures stay fixed).
    """
    SetMono(val)
    
    
def mvid(val):
    """
    Sets the ID absolute set point (not optimized , mono & apertures stay fixed).
    """
    SetID_Raw(val)

def getE():
    """ 
    Returns current mono set point.
    """
    E=Get_energy()[4]
    return E

def slit(val):
    """
    Sets the exit slits:
        ARPES = 0 < x < 300  um
        Kappa  = 0 < x < 1000 um
    """
    SetExitSlit(val)


def grating(which):
    """
    Change mono grating: which = \"HEG\", \"MEG\"
        HEG = high resolution, low flux
        MEG = medium resolution, high flux
    """
    Switch_Grating(which)


def polarization(which):
    """
    Change beam polarization: which = \"H\", \"V\", \"RCP\" or \"LCP\"
    """
    Switch_IDMode(which)


def resolution():
    """
    Calculate the theoretical resolution for the current beamline settings:
        ARPES: total resolution i.e. sqrt(kbT^2 + analyzer^2 + BL^2); default SES slit = 5.
        Kappa:  beamline contribution only
    """


    mybranch=CheckBranch()
    GRT=caget("29idmono:GRT_DENSITY")
    if GRT == 2400:
        grating="HEG"
    elif GRT == 1200:
        grating="MEG"
    hv=caget("29idmono:ENERGY_SP")
    #if branch == "c":
    if mybranch == "c":
        slit_SES=getSESslit()
        slit=TakeClosest([10,20,50,100,200],round(caget("29idb:Slit3CRBV"),0))
        PE=int(EA.PassEnergy)
        T=round(caget("29idARPES:LS335:TC1:IN1"),0)
        print("\nCalculating the current resolution with the following arguments:")
        print("        grating, hv, slit, PE, SES_slit, T(K)")
        print("\nResolution_ARPES(\""+grating+"\","+str(hv)+","+str(slit)+","+str(PE)+","+str(slit_SES)+","+str(T)+")")
        Resolution_ARPES(grating,hv,slit,PE,slit_SES,T)
    #elif branch == "d":
    elif mybranch == "d" or mybranch == "e":
        slit=TakeClosest([10,20,50,100,200],round(caget("29idb:Slit4Vt2.C")*1000,0))
        print("\nCalculating the current resolution with the following arguments:")
        print("        grating, hv, slit")
        print("\nResolution_BL(\""+grating+"\","+str(hv)+","+str(slit)+")")
        Resolution_BL(grating,hv,slit)


def avg(n,quiet=''):
    """Average reading of the relevant current amplifiers for the current branch.
    To make it chatty, specify quiet=None."""
    CA_Average(n, quiet, rate='Slow')





##############################################################################################################
##############################               ARPES & Kappa move            ##############################
##############################################################################################################



def mvx(val):
    """ Moves x motor in the endstation specified by CheckBranch()
    """
    name="x"
    Move_Motor_vs_Branch(name,val)

def mvy(val):
    """ Moves y motor in the endstation specified by CheckBranch()
    """
    name="y"
    Move_Motor_vs_Branch(name,val)

def mvz(val):
    """ Moves z motor in the endstation specified by CheckBranch()
    """
    name="z"
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


def mvchi(val):
    """ Moves phi motor in the endstation specified by CheckBranch()
    Kappa: chi is a four-circle pseudomotor
    """
    name="chi"
#    mybranch=CheckBranch()
#    if mybranch == "d":
#        print("   chi motor does not exit")
#    #elif branch == "d":
#    elif mybranch == "c":
    Move_Motor_vs_Branch(name,val)

def mvphi(val):
    """ Moves phi motor in the endstation specified by CheckBranch()
    Kappa: phi is a four-circle pseudomotor, kphi is an actual motor
    """
    name="phi"
#    mybranch=CheckBranch()
#    if mybranch == "d":
#        print("   phi motor does not exit")
    #elif branch == "d":
#    elif mybranch == "c":
    Move_Motor_vs_Branch(name,val)

def mvkth(val):
    """ Moves kth motor in the in the Kappa chamber
    """
    name="kth"
    Move_Motor_vs_Branch(name,val)

def mvkap(val):
    """ Moves kap motor in the in the Kappa chamber
    """
    name="kap"
    Move_Motor_vs_Branch(name,val)

def mvkphi(val):
    """ Moves kphi motor in the in the Kappa chamber
    """
    name="kphi"
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

def mvDetV(val):
    """ Moves the vetector vertically motor in the in the RSoXS chamber
    """
    name="Det_V"
    Move_Motor_vs_Branch(name,val)

def mvsample(mylist):
    """
    gets endstation from CheckBranch() and moves to the sample position specified in mylist
    ARPES: mylist=['string',x,y,z,th,chi,phi]
    Kappa: mylist=['string',x, y, z, tth, kth, kap, kphi]
    """
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        Move_ARPES_Sample(mylist)
    #elif branch == "d":
    elif mybranch == "d":
        Move_Kappa_Sample(mylist)
    elif mybranch == "e":
        Move_RSoXS_Sample(mylist)


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
def mvrth(val):
    """
    Relative move
    """
    name="th"
    UMove_Motor_vs_Branch(name,val)
def mvrtth(val):
    """
    Relative move
    """
    name="tth"
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        print("   tth motor does not exit")
    #elif branch == "d":
    else:
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

def mvrkap(val):
    """
    Relative move
    """
    name="kap"
    mybranch=CheckBranch()
    if mybranch == "d":
        UMove_Motor_vs_Branch(name,val)
    else:
        print("   kap motor does not exit")
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


def LastMDA():
    """
    returns the last mda file number in the ioc defined by BL_ioc
    """
    scanIOC=BL_ioc()
    n=caget('29id'+scanIOC+':saveData_scanNumber')-1
    return n

##### Kappa Optimization scans #####
def Opt_d4(iteration,moveZ,graph='y',srs=None,start=-0.5,stop=0.5,step=0.04):
    tth_w=0.1
    if srs==None: det=21
    else: det=34
    z=caget('29idKappa:m4.RBV')
    current_det=caget('29idKappa:userStringSeq6.STR1',as_string=True)
    if current_det != 'd4':
        print('Switching detector to d4')
        setdet('d4')
    mvtth(0)
    if moveZ is not None:
        mvz(z-1000)
    for i in range(iteration):
        scantth(start,stop,step,'relative')
        scannum=LastMDA()
        tth0=fit_mda(scannum,det,tth_w,'gauss',graph=graph)
        mvtth(tth0)
    mvz(z)
    return tth0,scannum

def Opt_z0(iteration,movetth,movekth,det='d4',srs=None,graph='y'):
    z_w=400
    current_det=caget('29idKappa:userStringSeq6.STR1',as_string=True)
    if current_det != det:
        print('Switching detector to '+det)
        setdet(det)
    if det=='d3' and srs==None: det=20
    if det=='d3' and srs!=None: det=33
    if det=='d4' and srs==None: det=21
    if det=='d4' and srs!=None: det=34
    if movetth is not None:
        mvtth(movetth)  
    if movekth is not None:
        mvkth(movekth)
    if iteration>1:
        scanz(-2000,2000,250,'relative')
        scannum=LastMDA()
        z0=fit_mda(scannum,det,z_w,'erf',graph=graph)
        mvz(z0)
    scanz(-700,700,50,'relative')
    scannum=LastMDA()
    z0=fit_mda(scannum,det,z_w,'erf',graph=graph)
    mvz(z0)
    return z0,scannum

def Opt_kth(kth_0,theta,det='d4',srs=None,graph='y'):
    current_det=caget('29idKappa:userStringSeq6.STR1',as_string=True)
    if current_det != det:
        print('Switching detector to '+det)
        setdet(det)
    if det == 'd4': 
        if srs==None: det=21
        else: det=34
        i=1
    elif det == 'd3': 
        if srs==None: det=20
        else: det=33
        i=5
    mvtth(theta*2)
    mvkth(kth_0+theta)
    scankth(-0.5*i,0.5*i,0.05*i,'relative')
    new_kth=fit_mda(LastMDA(),det,0.1,'gauss',graph=graph)
    mvkth(new_kth)
    scankth(-0.2*i,0.2*i,0.02*i,'relative')
    new_kth=fit_mda(LastMDA(),det,0.1,'gauss',graph=graph)
    mvkth(new_kth)
    scannum=LastMDA()
    kth0=round(new_kth-theta,3)
    print('\nkth0 = ',kth0)
    print('To plot use:') 
    print('     fit_mda('+str(scannum)+',21,0.2,"gauss",mytitle=\'theta ='+str(theta)+'\')')
    print('If you are happy with that, you can set this value as kth0 using:')
    print('     kth0_set('+str(kth0)+')')

    return kth0,scannum

def plot_opt(opt_scan_list,energy_list,det,mytitle=''):
    fig,(ax1)=plt.subplots(1,1)
    fig.set_size_inches(5,4)

    for i,j in zip(opt_scan_list,energy_list):
        x,y,x_name,y_name=mda_1D(i,det,1,0)
        xdata = np.array(x)
        ydata = np.array(y)
        Imax=np.max(ydata)    
        ax1.plot(x,y/Imax,label=str(j)+" eV")
    ax1.set(ylabel='Intensity')
    ax1.set(xlabel=x_name)
    ax1.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    ax1.grid(color='lightgray', linestyle='-', linewidth=0.5)
    ax1.legend(bbox_to_anchor=[1.2, 1],ncol=2,shadow=True, title=mytitle, fancybox=True)    





##############################################################################################################
##############################               ARPES & Kappa scan            ##############################
##############################################################################################################

#JM added scanIOC and scanDIM to the scan functions
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

        
def scankth(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "d":
        Scan_Kappa_Motor_Go("kth",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    else:
        print("kth motor does not exit")

def scankap(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "d":
        Scan_Kappa_Motor_Go("kap",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    else:
        print("kap motor does not exit")

def scankphi(start,stop,step,mode="absolute",scanIOC=None,scanDIM=1,**kwargs):
    mybranch=CheckBranch()
    if scanIOC is None:
        scanIOC=BL_ioc()
    if mybranch == "d":
        Scan_Kappa_Motor_Go("kphi",start,stop,step,mode=mode,scanIOC=scanIOC,scanDIM=scanDIM,**kwargs)        
    else:
        print("kphi motor does not exit")

def scanFocus(start,stop,step,mode="relative",**kwargs):
    """
    scans the ARPES focus relative to the current x value, y=xtan55
    kwargs: 
        scanIOC = BL_ioc()
        scanDIM = 1
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    
    mybranch=CheckBranch()

    if mybranch == "c":
        Scan_ARPES_Focus(start,stop,step,mode,**kwargs)
    else:
        print("Used only in the ARPES chamber")
   
        
def dscanx(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanx'''
    scanx(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscany(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scany'''
    scany(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscanz(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanz'''
    scanz(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscantth(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scantth'''
    scantth(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscanth(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanth'''
    scanth(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscanchi(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanchi'''
    scanchi(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscanphi(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scanphi'''
    scanphi(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscankth(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scankth'''
    scankth(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscankap(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scankap'''
    scankap(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)

def dscankphi(start,stop,step,scanIOC=None,scanDIM=1,**kwargs):
    '''RELATIVE scankphi'''
    scankphi(start,stop,step,"relative",scanIOC,scanDIM,**kwargs)





def scanMesh(InnerMotorList,OuterMotorList,**kwargs):
    """
        InnerMotorList=[startH,stopH,stepH](x in the plot)
        OuterMotorList=[startV,stopV,stepV](y in the plot)
    
    Raster/maps the sample with outer/inner loop being the vertical/horizontal direction:
        - yz scan for ARPES
        - yx scan for Kappa (sample is assumed to be normal to the beam i.e kth/ksap/kphi = 147/134.7/57)
    
    **kwargs defaults
        mode='Absolute'
        settling_time=0.1,
        scanIOC=BL_ioc
        Snake; coming soon
    """
    mybranch=CheckBranch()
    settling_time=0.1
    startH,stopH,stepH=InnerMotorList
    startV,stopV,stepV=OuterMotorList
    if mybranch == "c":
        Scan_ARPES_2D_Go(["y",startH,stopH,stepH],["z",startV,stopV,stepV],**kwargs)
    elif mybranch == "d":
        Scan_Kappa_2D_Go(["y",startH,stopH,stepH],["x",startV,stopV,stepV],**kwargs)
    else:
        print("Not yet implemented")


def scan2D(InnerMotorList,OuterMotorList,mode="absolute",settling_time=0.1,**kwargs):
    """ Scans two motors.using the motor name (e.g. x,y,z,th).
        InnerMotorList=[name1,start1,stop1,step1](x in the plot)
        OuterMotorList=[name2,start2,stop2,step2](y in the plot)
        name = 'x'/'y'/'z'/'th'...  
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details      
        """
    mybranch=CheckBranch()
    if mybranch == "c":
        Scan_ARPES_2D_Go(InnerMotorList,OuterMotorList,**kwargs)
    elif mybranch == "d":
        Scan_Kappa_2D_Go(InnerMotorList,OuterMotorList,**kwargs)
    else:
        print("Not yet implemented")

def scan3D(list1,list2,list3,mode="absolute",settling_time=0.1,**kwargs):
    """ Scans two motors.using the motor name (e.g. x,y,z,th).
        listn=[name,start,stop,step]
        list1 is for the inner loop -> fast (x in the plot)
        list2 is for the middle loop -> slow (y in the plot)
        list3 is for the outer loop -> slow (y in the plot)
        """
    scanIOC=BL_ioc()
    mybranch=CheckBranch()
    if mybranch == "c":
        m1_RBV=ARPES_PVmotor(list1[0])[0]
        m1_VAL=ARPES_PVmotor(list1[0])[1]
        m2_RBV=ARPES_PVmotor(list2[0])[0]
        m2_VAL=ARPES_PVmotor(list2[0])[1]
        m3_RBV=ARPES_PVmotor(list3[0])[0]
        m3_VAL=ARPES_PVmotor(list3[0])[1]
    elif mybranch == "d":
        m1_RBV=Kappa_PVmotor(list1[0])[0]
        m1_VAL=Kappa_PVmotor(list1[0])[1]
        m2_RBV=Kappa_PVmotor(list2[0])[0]
        m2_VAL=Kappa_PVmotor(list2[0])[1]
        m3_RBV=Kappa_PVmotor(list3[0])[0]
        m3_VAL=Kappa_PVmotor(list3[0])[1]
    else:
        print("Not yet implemented")
    if mode == "relative":
        current_value1=caget(m1_RBV)
        abs_start1=round(current_value1+list1[1],3)
        abs_stop1 =round(current_value1+list1[2],3)
        current_value2=caget(m2_RBV)
        abs_start2=round(current_value2+list2[1],3)
        abs_stop2 =round(current_value2+list2[2],3)
        current_value3=caget(m3_RBV)
        abs_start3=round(current_value3+list3[1],3)
        abs_stop3 =round(current_value3+list3[2],3)
    else:
        abs_start1=list1[1]
        abs_stop1 =list1[2]
        abs_start2=list2[1]
        abs_stop2 =list2[2]
        abs_start3=list3[1]
        abs_stop3 =list3[2]
    step1=list1[3]
    step2=list2[3]
    step3=list3[3]
    Scan_FillIn(m1_VAL, m1_RBV, scanIOC, 1, abs_start1, abs_stop1, step1, point=None)
    Scan_FillIn(m2_VAL, m2_RBV, scanIOC, 2, abs_start2, abs_stop2, step2, point=None)
    Scan_FillIn(m3_VAL, m3_RBV, scanIOC, 3, abs_start3, abs_stop3, step3, point=None)

    Scan_Go(scanIOC,scanDIM=3,**kwargs)


def scanE(start,stop,step,average=None,ID_offset=0,ID_parked=None,coef=1,mesh='stay',**kwargs):
    """ Starts energy scan with fixed ID:
        => if ID_parked is NOT None, the ID will stay were it is.
        => if ID_parked IS None, the ID will move to:
                ID @ (stop-start)/2 + ID_offset
        => mesh='y': drops in the mesh for normalization (D branch only); retracts it at the end.
        => mesh='stay': to leave the mesh in after the scan is finished
        => mesh='n': no mesh.
    """
    scanDIM=1
    settling_time=0.2
    if average:
        CA_Average(average)
    Scan_Energy_Go(scanDIM,start,stop,step,ID_offset,ID_parked,coef,settling_time,mesh,**kwargs)
    if average:
        CA_Average(0)


def scanhv(start,stop,step,average=None,settling_time=0.2,**kwargs):
    """
    scans the mono at the current ID value
    """
    scanDIM=1
    if average:
        CA_Average(average)
    Scan_Mono_Go(scanDIM,start,stop,step,settling_time,**kwargs)
    if average:
        CA_Average(0)

def scanXAS(hv,StartStopStepLists,settling_time=0.2,**kwargs):
    """
    Sets the beamline to hv and then scans the mono for XAS scans
    
    StartStopStepLists is a list of lists for the different scan ranges
        StartStopStepList[[start1,stop1,step1],[start1,stop1,step1],...]
        Note duplicates are review and the resulting array is sorted in ascending order
    
    Normalization:2575
        - If in the D-branch the Mesh is put in but is not removed
        - If in the C-branch we use the slit blades for normalization (ca13)
        
    Logging is automatic ; kwargs:  
        mcp = True
        m3r = True
        average = None
        scanIOC = BL_ioc
        scanDIM = 1
        run = True; False doesn't push Scan_Go
    """

    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    kwargs.setdefault("average",None)
    kwargs.setdefault("run",True)
    kwargs.setdefault("debug",False)
    kwargs.setdefault("m3r",True)
    kwargs.setdefault("mcp",True)       


    posNum=1 #positionioner 1
    scanIOC=kwargs['scanIOC']
    scanDIM=kwargs['scanDIM']
    
    #Setting up the ScanRecord for Mono in Table mode
    VAL="29idmono:ENERGY_SP"
    RBV="29idmono:ENERGY_MON"
    myarray=Scan_MakeTable(StartStopStepLists)
    Scan_FillIn_Table(VAL,RBV,scanIOC,scanDIM,myarray, posNum=posNum)
    #mono needs to stay and have a longer settling time
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)
    
    #Averaging and Normalization
    if kwargs["average"]:
        CA_Average(kwargs["average"])
    Branch=CheckBranch()
    if Branch=="d":
        MeshD("In")
     
    #Setting the beamline energy
    energy(hv,m3r=kwargs["m3r"])
    if Branch=="d" and kwargs["mcp"]:
        MPA_HV_ON()
        
    #Scanning
    Scan_Go(scanIOC,scanDIM)
    Scan_Reset_AfterTable(scanIOC,scanDIM)

    
    #Setting everything back
    SetMono(hv)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",0.1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P1SM","LINEAR") 
    if Branch=="d":
        if kwargs["mcp"]: MPA_HV_OFF()
        print("WARNING: Mesh"+Branch+" is still in")        

def Tables_BLenergy(StartStopStepLists,**kwargs):
    """
    returns mono_array and ID_array for BL energy scans
    *energies:
        start,stop,step
        ListofLists, e.g.{[400,420,1],[420,425,0.25]...}
    """
    kwargs.setdefault("settling_time",0.2)

    mono_array=Scan_MakeTable(StartStopStepLists)
    ID_array=np.array([])
    ID_Mode,ID_QP,ID_SP,ID_RBV,hv,grt=Get_energy()
    for n in mono_array:
        ID_array=np.append(ID_array,ID_Calc(grt,ID_Mode,n))
    return mono_array,ID_array

def ScanFillIn_BLenergy(*hvs, **kwargs):
    kwargs.setdefault('scanIOC',BL_ioc())
    kwargs.setdefault('scanDIM',1)
    kwargs.setdefault("run",True)
    kwargs.setdefault("debug",False)
    kwargs.setdefault("settling_time",0.2)

    mono_array,ID_array=Tables_BLenergy(*hvs)
    if kwargs["debug"]:
        print("mono_array: ",mono_array)
        print("ID_array: ",ID_array)
        
    #Setting up the ScanRecord for Mono and ID in Table mode: mono Pos1 and ID Pos2
    VAL1="29idmono:ENERGY_SP"
    RBV1="29idmono:ENERGY_MON"
    VAL2="ID29:EnergyScanSeteV"
    RBV2=""

    Scan_FillIn_Table(VAL1,RBV1,kwargs["scanIOC"],kwargs["scanDIM"],mono_array, posNum=1)
    Scan_FillIn_Table(VAL2,RBV2,kwargs["scanIOC"],kwargs["scanDIM"],ID_array, posNum=2)
    
    #mono needs to stay and have a longer settling time
    scanPV="29id"+kwargs["scanIOC"]+":scan"+str(kwargs["scanDIM"])
    caput(scanPV+".PASM","STAY")
    caput(scanPV+".PDLY",kwargs["settling_time"])
    
    return


def scanXAS_BL(StartStopStepLists,settling_time=1,**kwargs):
    """
    Sets the beamline to hv and then scans the mono & ID for XAS scans
    StartStopStepLists: the photon energies to scan 
        start,stop,step => for a monotonic scan
        [[start1,stop1,step1],[start2,stop2,step2],...]
        Note duplicates are removed and the resulting array is sorted in ascending order
    
    Normalization:
        - If in the D-branch the Mesh is put in but is not removed
        - If in the C-branch we use the slit blades for normalization (ca13)
        
    **kwargs are the optional logging arguments see scanlog() for details
    Defaults:
        mcp = True
        m3r = True
        average = None
        scanIOC = BL_ioc
        scanDIM = 1
        run = True; False doesn't push Scan_Go
    """

    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("scanDIM",1)
    kwargs.setdefault("average",None)
    kwargs.setdefault("run",True)
    kwargs.setdefault("debug",False)
    kwargs.setdefault("m3r",True)
    kwargs.setdefault("mcp",True)
        
    #Setting up the ScanRecord for Mono and ID in Table mode
    mono_array,ID_array=Tables_BLenergy(StartStopStepLists)
    ScanFillIn_BLenergy(StartStopStepLists, **kwargs)
    
    #Averaging and Normalization
    if kwargs["average"]:
        CA_Average(kwargs["average"])
    Branch=CheckBranch()
    if Branch=="d":
        MeshD("In")

    if kwargs["run"]==True:
        #Setting the beamline energy to the first point
        energy(mono_array[0]-2,m3r=False)
        energy(mono_array[0]-1,m3r=kwargs["m3r"])
        if Branch=="d" and kwargs["mcp"]:
            MPA_HV_ON()
        #Scanning
        Scan_Go(kwargs['scanIOC'],kwargs['scanDIM'])
        Scan_Reset_AfterTable(kwargs['scanIOC'],kwargs['scanDIM'])
        
        if Branch=="d":
            if kwargs["mcp"]: MPA_HV_OFF()
            print("WARNING: Mesh"+Branch+" is still in")     
            
# def mprint():
#     """
#     Print motor position in current branch as defined by Check_Branch()
#     """
#     return Print_Motor()

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


def diffracto(ListPosition):
    """ List Position = "Sample Name", x, y, z, th,tth
    """
    mybranch=CheckBranch()
    if mybranch == "c":
        print('not a valid coammnd')
    elif mybranch == "d":
        Move_Kappa_Sample(ListPosition)
        if not isinstance(ListPosition[0],str):
            ListPosition.insert(0,"")
        name,x,y,z,tth,kth,kap,kphi=ListPosition
        caput("29idKappa:m9.VAL",tth,wait=True,timeout=18000)
    elif mybranch =="e":
        print('not a valid coammnd')


def mvxyz(ListPosition):
    """ List Position = "Sample Name", x, y, z, th"""
    mybranch=CheckBranch()
    if mybranch == "d":
        Move_Kappa_xyz(ListPosition)
    elif mybranch == "e":
        Move_RSoXS_xyz(ListPosition)
    else:
        print("function not defined for this chamber")


##############################################################################################################
##############################              Move Sample        ##############################
##############################################################################################################




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
    


def Move_Kappa_xyz(ListPosition):
    """ListPosition=[x, y, z]
       if ListPosition has more elements than it only uses the first three (i.e. can use the output of mprint())
    """
    x,y,z=ListPosition
    print("x="+str(x), " y="+str(y)," z="+str(z))
    caput("29idKappa:m2.VAL",x,wait=True,timeout=18000)
    caput("29idKappa:m3.VAL",y,wait=True,timeout=18000)
    caput("29idKappa:m4.VAL",z,wait=True,timeout=18000)

def Move_RSoXS_xyz(ListPosition):
    """ListPosition=[x, y, z]
       if ListPosition has more elements than it only uses the first three (i.e. can use the output of mprint())
    """
    if not isinstance(ListPosition[0],str):
        ListPosition.insert(0,"")
    #name,x,y,z,chi,phi,th,tth=ListPosition
    mvx(ListPosition[1])
    mvy(ListPosition[2])
    mvz(ListPosition[3])
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

def Move_RSoXS_Det(ListPosition):
    """
    ListPosition=[tth,Det_q,Det_V,BS_H,BS_V]
    """
    print("Not yet implemented, might be dangerous")




##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################









def BranchPV_StrSeq():
    """
    Reset conditions for branch_PV with:    A = Tx    and    B = Ry
    """
    caput("29id:CurrentBranch.CALC$","(A<-1 && B<-1)")




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



def CA_Live_StrSeq(scanIOC):              # do we need to add 29idb:ca5 ???
    n=7
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    ClearStringSeq(scanIOC,n)
    caput(pvstr+".DESC","CA_Live_"+scanIOC)
    n=len(Detector_List(scanIOC))
    for (i,list) in enumerate(Detector_List(scanIOC)):
        pvCA_read='29id'+list[0]+':ca'+str(list[1])+':read.SCAN CA NMS'
        pvCA_avg='29id'+list[0]+':ca'+str(list[1])+':digitalFilterSet PP NMS'

        caput(pvstr+".LNK"+str(i+1),pvCA_avg)
        caput(pvstr+".STR" +str(i+1),"Off")

        if n+1+i < 10:
            caput(pvstr+".LNK" +str(n+1+i),pvCA_read)
            caput(pvstr+".STR" +str(n+1+i),".5 second")
            caput(pvstr+".WAIT"+str(n+1+i),"After"+str(n))
        elif n+1+i == 10:
            caput(pvstr+".LNKA",pvCA_read)
            caput(pvstr+".STRA",".5 second")
            caput(pvstr+".WAITA","After"+str(n))
#    if scanIOC == 'Kappa':

#        caput(pvstr+".LNK" +str(2*n+1),'29idMZ0:scaler1.CONT CA NMS')
#        caput(pvstr+".STR" +str(2*n+1),"AutoCount")
#        caput(pvstr+".WAIT"+str(2*n+1),"After"+str(2*n))

    return pvstr+".PROC"





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


def UserAvg_Trigger_StrSeq(ioc,num):
    n=8
    ClearStringSeq(ioc,n)
    str_pv="29id"+ioc+":userStringSeq"+str(n)
    caput(str_pv+".DESC","Average Triggers_"+ioc)
    if num < 10:
        str_num=str(num)
    else:
        str_num="A"
    for i in range(1,num+1,1):
        if i < 10:
            i=str(i)
        else:
            i="A"
        avg_pv="29id"+ioc+":userAve"+i
        caput(str_pv+".LNK"+i,avg_pv+"_acquire.PROC CA NMS")
        caput(str_pv+".WAIT"+i,"After"+str_num)


def UserAvg_PV(pv,average_num,average_pts,name,mode="ONE-SHOT"):
    avgIOC=BL_ioc()
    ClearUserAvg(avgIOC,average_num)
    avg_pv="29id"+avgIOC+":userAve"+str(average_num)
    caput(avg_pv+".SCAN","Passive")
    caput(avg_pv+".INPB",pv+" CP NMS")
    caput(avg_pv+".A",average_pts)
    caput(avg_pv+".PREC",9)
    caput(avg_pv+"_mode.VAL",mode)
    caput(avg_pv+"_algorithm.VAL","AVERAGE")
    caput(avg_pv+".DESC",name)


def Cam_SaveStrSeq(camNUM):
    ioc="b"
    pvCam="29id_ps"+str(camNUM)+":"
    pvIOC="29id"+ioc+":"
    ClearStringSeq("b",2)
    caput(pvIOC+"userStringSeq2.DESC","Camera datamode")
    caput(pvIOC+"userStringSeq2.LNK1",pvCam+"cam1:Acquire CA NMS")
    caput(pvIOC+"userStringSeq2.STR1","Done")
    caput(pvIOC+"userStringSeq2.LNK2",pvCam+"cam1:ImageMode PP NMS")
    caput(pvIOC+"userStringSeq2.STR2","Single")
    caput(pvIOC+"userStringSeq2.LNK3",pvCam+"TIFF1:EnableCallbacks PP NMS")
    caput(pvIOC+"userStringSeq2.STR3","Enable")
    caput(pvIOC+"userStringSeq2.LNK4",pvCam+"TIFF1:AutoSave PP NMS")
    caput(pvIOC+"userStringSeq2.STR4","Yes")
    caput(pvIOC+"userStringSeq2.LNK5",pvCam+"TIFF1:FileNumber PP NMS")
    caput(pvIOC+"userStringSeq2.DO5",1)
    caput(pvIOC+"userStringSeq2.WAIT1","Wait")
    caput(pvIOC+"userStringSeqEnable.VAL",1)

def Cam_FreeStrSeq(camNUM):
    ioc="b"
    pvCam="29id_ps"+str(camNUM)+":"
    pvIOC="29id"+ioc+":"
    ClearStringSeq(ioc,1)
    caput(pvIOC+"userStringSeq1.DESC","Camera freerun")
    caput(pvIOC+"userStringSeq1.LNK1",pvCam+"TIFF1:EnableCallbacks PP NMS")
    caput(pvIOC+"userStringSeq1.STR1","Disable")
    caput(pvIOC+"userStringSeq1.LNK2",pvCam+"cam1:ImageMode PP NMS")
    caput(pvIOC+"userStringSeq1.STR2","Continuous")
    caput(pvIOC+"userStringSeq1.LNK3",pvCam+"cam1:Acquire PP NMS")
    caput(pvIOC+"userStringSeq1.STR3","Acquire")
    caput(pvIOC+"userStringSeq1.LNK4",pvCam+"TIFF1:AutoSave PP NMS")
    caput(pvIOC+"userStringSeq1.STR4","No")
    caput(pvIOC+"userStringSeq1.LNK5",pvCam+"TIFF1:FileNumber PP NMS")
    caput(pvIOC+"userStringSeq1.DO5",1)
    caput(pvIOC+"userStringSeq1.LNK6",pvCam+"cam1:AcquireTime PP NMS")
    caput(pvIOC+"userStringSeq1.DO6",0.015)
    caput(pvIOC+"userStringSeq1.WAIT1","Wait")
    caput(pvIOC+"userStringSeqEnable.VAL",1)



def Scan_Slit3D_StrSeq():
    n=2
    scanIOC="d"
    ClearStringSeq(scanIOC,n)
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    caput(pvstr+".DESC","Scan Slit 3D")
    caput(pvstr+".DO1","50")
    caput(pvstr+".LNK1","29idb:Slit4Vsize.VAL")
    caput(pvstr+".STR2","29idb:Slit4Vcenter.VAL")
    caput(pvstr+".LNK2","29idKappa:scan1.P1PV NPP NMS")
    caput(pvstr+".STR3","29idb:Slit4Vt2.D")
    caput(pvstr+".LNK3","29idKappa:scan1.R1PV NPP NMS")
    caput(pvstr+".STR4","-2000")
    caput(pvstr+".LNK4","29idKappa:scan1.P1SP NPP NMS")
    caput(pvstr+".STR5","2000")
    caput(pvstr+".LNK5","29idKappa:scan1.P1EP NPP NMS")
    caput(pvstr+".STR6","100")
    caput(pvstr+".LNK6","29idKappa:scan1.P1SI NPP NMS")
    caput(pvstr+".DO7","0.1")
    caput(pvstr+".LNK7","29idMZ0:scaler1.TP NPP NMS")
    caput(pvstr+".DO8","1")
    caput(pvstr+".LNK8","29idKappa:scan1.EXSC NPP NMS")
    caput(pvstr+".WAIT8","Wait")










def Kappa_DetectorSet_StrSeq():
    n=5
    scanIOC="Kappa"
    ClearStringSeq(scanIOC,n)
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    caput(pvstr+".DESC","Kappa Det Set")
    caput(pvstr+".STR1","Set")
    caput(pvstr+".LNK1","29idKappa:m9.SET CA NMS")
    caput(pvstr+".WAIT1","Wait")
    caput(pvstr+".DO2",10)
    caput(pvstr+".LNK2","29idKappa:m9.VAL CA NMS")
    caput(pvstr+".WAIT2","Wait")
    caput(pvstr+".STR3","Use")
    caput(pvstr+".LNK3","29idKappa:m9.SET CA NMS")
    caput(pvstr+".WAIT3","Wait")


def Kappa_DetectorName_StrSeq():
    n=6
    scanIOC="Kappa"
    ClearStringSeq(scanIOC,n)
    pvstr="29id"+scanIOC+":userStringSeq"+str(n)
    caput(pvstr+".DESC","Kappa Det Name")
    caput(pvstr+".STR1","d3")




def KappaPreset_StrSeq(n,User):
    scanIOC="Kappa"
    motorIOC="29idKappa:"
    motor = ["m2","m3","m4","m9","m8","m7","m1"]
    ClearStringSeq(scanIOC,n)
    pvIOC="29id"+scanIOC+":userStringSeq"+str(n)
    if User[0] == "Kappa Grazing":  phi0= 0
    if User[0] == "Kappa Transfer": phi0= 57
    caput(pvIOC+".DESC",User[0])
    caput(pvIOC+".LNK1", "29idKappa:userCalcOut9.A CA NMS")       # MPA HV pV
    caput(pvIOC+".DO1",0)                                       # MPA HV = 0
    caput(pvIOC+".WAIT1","Wait")                                # Wait for completion
    caput(pvIOC+".LNK2", "29idKappa:m1.VAL CA NMS")               # phi = phi0
    caput(pvIOC+".DO2",phi0)                                       
    caput(pvIOC+".WAIT2","Wait")                                # Wait for completion
    for i in range(3,10):
        caput(pvIOC+".LNK"+str(i),motorIOC+motor[i-3]+".VAL CA NMS")
        caput(pvIOC+".DO"+str(i),User[i-2])
        if i < 9:
            caput(pvIOC+".WAIT"+str(i),"After8")



def KappaTransfer_StrSeq():
    #User= [    DESC,        x,        y,      z,        tth,       kth,       kap,    kphi]
    User = ["Kappa Transfer",0, -2650, -650, 0, 57, 0, -88]
    n=4
    KappaPreset_StrSeq(n,User)


def KappaGrazing_StrSeq(): #Need to determine positions and then add to the Kappa graphic
    #Dial= [    DESC,        x,        y,      z,        tth,       kth,       kap,    kphi]
    User = ["Kappa Grazing",0, 0, 0, 0, 57.045, 134.76,57.045]
    n=3
    KappaPreset_StrSeq(n,User)
    
    

def MPA_SaveStrSeq():
    ioc="Kappa"
    n=2
    pvDet="29iddMPA:det1:"
    pvTIF="29iddMPA:TIFF1:"
    pvioc="29id"+ioc+":userStringSeq"+str(n)
    ClearStringSeq(ioc,n)
    caput(pvioc+".DESC","MCP datamode")
    caput(pvioc+".LNK1",pvDet+"Acquire CA NMS")
    caput(pvioc+".STR1","Done")
    caput(pvioc+".WAIT1","Wait")
    caput(pvioc+".LNK2",pvDet+"RunTimeEnable PP NMS")
    caput(pvioc+".STR2","1")
    caput(pvioc+".WAIT2","Wait")
    caput(pvioc+".LNK3",pvTIF+"EnableCallbacks PP NMS")
    caput(pvioc+".STR3","1")

def MPA_FreeStrSeq():
    ioc="Kappa"
    n=1
    pvDet="29iddMPA:det1:"
    pvioc="29id"+ioc+":userStringSeq"+str(n)
    ClearStringSeq(ioc,n)
    caput(pvioc+".DESC","MCP freerun")
    caput(pvioc+".LNK1",pvDet+"Acquire PP NMS")
    caput(pvioc+".WAIT1","Wait")
    caput(pvioc+".STR1","Done")
    caput(pvioc+".LNK2","29iddMPA:TIFF1:EnableCallbacks PP NMS")
    caput(pvioc+".STR2","0")
    caput(pvioc+".WAIT2","Wait")
    caput(pvioc+".LNK3",pvDet+"RunTimeEnable PP NMS")
    caput(pvioc+".STR3","0")
    caput(pvioc+".WAIT3","Wait")
    caput(pvioc+".LNK4",pvDet+"Acquire PP NMS")
    caput(pvioc+".STR4","Acquire")










def MPA_HV_SP_CalcOut():
    ioc="Kappa"
    n=9
    pvioc="29id"+ioc+":userCalcOut"+str(n)
    ClearCalcOut(ioc,n)
    max_HV=2990
    ratio=500
    caput(pvioc+".DESC","MPA HV SP")
    caput(pvioc+".A",0)
    caput(pvioc+".B",ratio)
    caput(pvioc+".C",max_HV)
    caput(pvioc+".CALC$","A")
    caput(pvioc+".OCAL$","MIN(A/B,C/B)")
    caput(pvioc+".OOPT",1)        # On Change
    caput(pvioc+".DOPT",1)        # Use 0CALC
    caput(pvioc+".IVOA",0)        # Continue Normally
    caput(pvioc+".OUT","29iddau1:dau1:011:DAC_Set PP NMS")

def MPA_HV_RBV_CalcOut():
    ioc="Kappa"
    n=10
    pvioc="29id"+ioc+":userCalcOut"+str(n)
    ClearCalcOut(ioc,n)
    max_HV=2750
    ratio=500
    caput(pvioc+".DESC","MPA HV RBV")
    caput(pvioc+".INPA",'29iddau1:dau1:011:DAC CP NMS')
    caput(pvioc+".B",ratio)
    caput(pvioc+".CALC$","A*B")






def Bragg_Angle_CalcOut(d,eV,l):
    n=7
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pv="29id"+scanIOC+":userCalcOut"+str(n)+"."
    h=4.135667516e-15
    c=299792458
    f=h*c*1e9*10
    caput(pv+"DESC","Bragg_Angle")
    caput(pv+"A",d)
    caput(pv+"B",l)
    caput(pv+"C",eV)
    caput(pv+"D",pi)
    caput(pv+"E",f)
    caput(pv+".CALC$","ASIN(B*E/(C*"+str(2)+"*A))*"+str(180)+"/D")

#### Obsolete?

def Bragg_Index_CalcOut(d,eV,th):
    n=8
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pv="29id"+scanIOC+":userCalcOut"+str(n)+"."
    h=4.135667516e-15
    c=299792458
    f=h*c*1e9*10
    caput(pv+"DESC","Bragg_Index")
    caput(pv+"A",d)
    caput(pv+"B",th)
    caput(pv+"C",eV)
    caput(pv+"D",pi)
    caput(pv+"E",f)
    caput(pv+"CALC$","SIN(B*D/"+str(180)+")*"+str(2)+"*A*C/E")



def KtoE_th_CalcOut():
    n=1
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pvcal="29id"+scanIOC+":userCalcOut"+str(n)
    caput(pvcal+".DESC","KtoE_th")
    caput(pvcal+".INPA","29idKappa:m8.RBV CP NMS")    #A=kth
    caput(pvcal+".INPB","29idKappa:m7.RBV CP NMS")    #B=kap
    caput(pvcal+".INPC","29idKappa:m1.RBV CP NMS")    #C=kphi
    caput(pvcal+".D",3.141592653589793)
    caput(pvcal+".E",180)
    caput(pvcal+".F",50)
    caput(pvcal+".H",57.045)
    caput(pvcal+".CALC$","((A-(G-H))*D/E-ATAN(TAN(B*D/E/2.0)*COS(F*D/E)))*E/D")
    caput(pvcal+".DOPT",0)           # Use CAL

def KtoE_chi_CalcOut():
    n=2
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pvcal="29id"+scanIOC+":userCalcOut"+str(n)
    caput(pvcal+".DESC","KtoE_chi")
    caput(pvcal+".INPA","29idKappa:m8.RBV CP NMS")    #A=kth
    caput(pvcal+".INPB","29idKappa:m7.RBV CP NMS")    #B=kap
    caput(pvcal+".INPC","29idKappa:m1.RBV CP NMS")    #C=kphi
    caput(pvcal+".D",3.141592653589793)
    caput(pvcal+".E",180)
    caput(pvcal+".F",50)
    caput(pvcal+".CALC$","(2*ASIN(SIN(B*D/E/2.0) * SIN(F*D/E)))*E/D")
    caput(pvcal+".DOPT",0)           # Use CAL

def KtoE_phi_CalcOut():
    n=3
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pvcal="29id"+scanIOC+":userCalcOut"+str(n)
    caput(pvcal+".DESC","KtoE_phi")
    caput(pvcal+".INPA","29idKappa:m8.RBV CP NMS")    #A=kth
    caput(pvcal+".INPB","29idKappa:m7.RBV CP NMS")    #B=kap
    caput(pvcal+".INPC","29idKappa:m1.RBV CP NMS")    #C=kphi
    caput(pvcal+".D",3.141592653589793)
    caput(pvcal+".E",180)
    caput(pvcal+".F",50)
    caput(pvcal+".CALC$","(C*D/E-ATAN(TAN(B*D/E/2.0)*COS(F*D/E)))*E/D")
    caput(pvcal+".DOPT",0)           # Use CAL




def EtoK_kth_CalcOut():
    n=4
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pvcal="29id"+scanIOC+":userCalcOut"+str(n)
    caput(pvcal+".DESC","EtoK_kth")
    caput(pvcal+".INPA","29idKappa:userCalcOut1.VAL CP NMS")    #A=th
    caput(pvcal+".INPB","29idKappa:userCalcOut2.VAL CP NMS")    #B=chi
    caput(pvcal+".INPC","29idKappa:userCalcOut3.VAL CP NMS")    #C=phi
    caput(pvcal+".D",3.141592653589793)
    caput(pvcal+".E",180)
    caput(pvcal+".F",50)
    caput(pvcal+".CALC$","(A*D/E-ASIN(-TAN(B*D/E/2.0)/TAN(F*D/E)))*E/D")
    caput(pvcal+".DOPT",0)           # Use CAL

def EtoK_kap_CalcOut():
    n=5
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pvcal="29id"+scanIOC+":userCalcOut"+str(n)
    caput(pvcal+".DESC","EtoK_kap")
    caput(pvcal+".INPA","29idKappa:userCalcOut1.VAL CP NMS")    #A=th
    caput(pvcal+".INPB","29idKappa:userCalcOut2.VAL CP NMS")    #B=chi
    caput(pvcal+".INPC","29idKappa:userCalcOut3.VAL CP NMS")    #C=phi
    caput(pvcal+".D",3.141592653589793)
    caput(pvcal+".E",180)
    caput(pvcal+".F",50)
    caput(pvcal+".CALC$","((2*ASIN(SIN(B*D/E/2.0) / SIN(F*D/E))))*E/D")
    caput(pvcal+".DOPT",0)           # Use CAL

def EtoK_kphi_CalcOut():
    n=6
    scanIOC='Kappa'
    ClearCalcOut(scanIOC,n)
    pvcal="29id"+scanIOC+":userCalcOut"+str(n)
    caput(pvcal+".DESC","EtoK_kphi")
    caput(pvcal+".INPA","29idKappa:userCalcOut1.VAL CP NMS")    #A=th
    caput(pvcal+".INPB","29idKappa:userCalcOut2.VAL CP NMS")    #B=chi
    caput(pvcal+".INPC","29idKappa:userCalcOut3.VAL CP NMS")    #C=phi
    caput(pvcal+".D",3.141592653589793)
    caput(pvcal+".E",180)
    caput(pvcal+".F",50)
    caput(pvcal+".CALC$","(C*D/E-ASIN(-TAN(B*D/E/2.0)/TAN(F*D/E)))*E/D")
    caput(pvcal+".DOPT",0)           # Use CAL


def SnakeScanSetup(scanIOC,scanDIM=1,Snake=None):
    """
    Creates a User Calc which will get the step size and reverse the sign if Snake is not None
    """
    if scanIOC == "Kappa":
        print("Not implemented in Kappa at the moment - need to free up user calcs")
    else:
        SnakeIOC=scanIOC
        which=1 #which user calc
        
        scanStepPV="29id"+scanIOC+":scan"+str(scanDIM)+".P1SI"
        SnakePV="29id"+SnakeIOC+":userCalcOut"+str(which)
        
        caput("29id"+SnakeIOC+":userCalcOutEnable.VAL",1) #global enable
        
        ### Setting up the user
        caput(SnakePV+".DESC","Snake Calc")
        caput(SnakePV+".INPA",scanStepPV+" NPP NMS")
        caput(SnakePV+".CALC$","A*-1*B")
        caput(SnakePV+".OUT",scanStepPV+" PP NMS")
        
        ###Setting B to 1(0) for snake(normal) scan
        if Snake is not None:
            caput(SnakePV+".B",1)
        else:
            caput(SnakePV+".B",0)
    
   


def ID_Table():
    table=caget("ID29:TableDirection")    # up = 1 , down = 0
    By=caget("ID29:ByPolaritySet")        # pos = 1, neg = 0

    Mode=ID_State2Mode("State",caget("ID29:ActualMode"))

    if By > 0:
        print("\nBy > 0")
        if table == 1:            # By=1, table = 1     => -1    => A=B
            print("table = up")
            ID_direction = -1
        elif table ==  0:        # By=1, table = 0     => +1    => A#B
            print("table = down")
            ID_direction = 1
    elif By <= 0:
        print("\nBy < 0")
        if table == 1:            # By=0, table = 1     => +1    => A=B
            print("table = up")
            ID_direction = 1
        elif table ==  0:        # By=0, table = 0     => -1    => A#B
            print("table = down")
            ID_direction = -1


    if Mode == "H" and Mode == "RCP":
        if By > 0 and table == 0:
            print("WARNING: will do a long hysteresis if decreasing energy !!!")
#    if Mode == "HN" and Mode == "LCP":
#        if By = 0 and table == 1:
#            print "WARNING: will do a long hysteresis if decreasing energy !!!"
    print("ID direction", ID_direction)
    return ID_direction

def ID_Table_CalcOut():    # Work in progress
    n=4
    ClearCalcOut("b",n)
    pvstr="29idb:userCalcOut"+str(n)
    caput(pvstr+".DESC","ID_Table")
    table="ID29:TableDirection"    # up = 1 , down = 0
    By="ID29:ByPolaritySet"        # pos = 1, neg = 0
    caput(pvstr+".INPA",table+" CP NMS")
    caput(pvstr+".INPB",By+" CP NMS")
    caput(pvstr+".CALC$","A#B")
    caput(pvstr+".OOPT","On Change")
    caput(pvstr+".DOPT","Use CALC")


def Mono_TemperatureInterlock():
    """
    userCalcOut to monitor the temperatures on the Mono if the temperature gets too high then it closes the main shutter
    #29idb:userCalcOut10.VAL =0 => OK; =1 => Too hot
    """
    pv='29idb:userCalcOut10'
    caput(pv+'.DESC', 'Mono Temperature Interlock')
    caput(pv+'.INPA','29idmono:TC1_MON CP NMS')
    caput(pv+'.INPB','29idmono:TC2_MON CP NMS')
    caput(pv+'.INPC','29idmono:TC3_MON CP NMS')
    caput(pv+'.INPD','29idmono:TC4_MON CP NMS')
    caput(pv+'.INPE','29idmono:TC5_MON CP NMS')
    caput(pv+'.INPF','29idmono:TC6_MON CP NMS')
    
    caput(pv+'.H','31')
    
    caput(pv+'.CALC','A>H | B>H | C>H |D>H')
    caput(pv+'OOPT','Transition To Non-zero')
    caput(pv+'.OUT','PC:29ID:FES_CLOSE_REQUEST.VAL PP NMS')

    
