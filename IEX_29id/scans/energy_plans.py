from epics import caput
import numpy as np
from IEX_29id.utils.exp import BL_ioc, CheckBranch
from IEX_29id.scans.setup import Scan_FillIn_Table
from IEX_29id.devices.keithleys import CA_Average
from IEX_29id.devices.diagnostics import meshD_plan
from IEX_29id.devices.beamline_energy import energy, SetMono
from IEX_29id.devices.detectors import MPA_HV_ON, MPA_HV_OFF
from IEX_29id.scans.setup import Scan_Go, Clear_Scan_Positioners



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
        meshD_plan("In")
     
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
