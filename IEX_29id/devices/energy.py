from time import sleep
from epics import caget, caput
from IEX_29id.utils.misc import dateandtime, RangeUp
import numpy.polynomial.polynomial as poly
from IEX_29id.utils.exp import CheckBranch, WaitForPermission,  Check_MainShutter, BL_ioc, AllDiag_dict
from math import *
from IEX_29id.devices.undulator import ID_State2Mode, ID_Coef, ID_Range, SetID, SetID_keV_pV
from os.path import join
import ast
from IEX_29id.devices.slits import SetSlit_BL,  Slit_Coef
from IEX_29id.devices.detectors import MPA_HV_ON, MPA_HV_OFF, Detector_List
from IEX_29id.scans.setup import Scan_Go, Scan_Progress, Scan_FillIn_Table
from IEX_29id.devices.kappa import Clear_Scan_Positioners

import numpy as np



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

def Open_MainShutter():
    caput("PC:29ID:FES_OPEN_REQUEST.VAL",1, wait=True,timeout=180000)
    print("Opening Main Shutter...")



def Check_Grating():
    GRTd=caget("29idmono:GRT_DENSITY")
    if GRTd == 1200:
        GRT = "MEG"
    elif GRTd == 2400:
        GRT = "HEG"
    return GRT


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


def Aperture_Fit(hv,n):
    K=Slit_Coef(n)[1]
    sizeH=K[0]+K[1]*hv+K[2]*hv*hv
    sizeV=K[3]+K[4]*hv+K[5]*hv*hv
    return [round(sizeH,3),round(sizeV,3)]

def read_dict(FileName,FilePath="/home/beams22/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/"):
    with open(join(FilePath, FileName)) as f:
        for c,line in enumerate(f.readlines()):
            if line[0] == '=':
                lastdate=line[8:16]
            lastline=line
        mydict=ast.literal_eval(lastline)
    return mydict
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

def Open_DShutter():
    branch="D"
    caput("PC:29ID:S"+branch+"S_OPEN_REQUEST.VAL",1,wait=True,timeout=18000)
    print("Opening "+branch+"-Shutter...")   
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

def MeshD(In_Out):
    "Inserts/retracts RSXS mesh (post-slit); arg = \"In\" or \"Out\""
    diag=AllDiag_dict()
    motor=28; position=position=diag[In_Out][motor]
    if type(position) == list:
        position=position[0]
    caput("29idb:m"+str(motor)+".VAL",position,wait=True,timeout=18000)
    print("\nD5D Au-Mesh: "+ In_Out)


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
        CA_Filter (ca_ioc,ca_num,avg_pts,rate,quiet,scanDIM)


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
        Clear_Scan_Positioners (scanIOC,scanDIM)

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


def Energy_Range(grating,IDmode):
    BL_range={}    #   Slit:PE
    BL_range["HEG"]  = { "H":(250,2000), "V":(440,2000), "RCP":(400,2000), "LCP":(400,2000)  }
    BL_range["MEG"]  = { "H":(250,2500), "V":(440,2500), "RCP":(400,2500), "LCP":(400,2500) }
    energy_min, energy_max = BL_range[grating][IDmode]
    return energy_min, energy_max

