from IEX_29id.utils.strings import ClearCalcOut,  ClearStringSeq
from time import sleep
from epics import caget, caput
from IEX_29id.scans.setup import Scan_FillIn,  Scan_Go
from IEX_29id.utils.exp import BL_Mode_Read
from math import *

import numpy as np
import numpy.polynomial.polynomial as poly
#import pandas as pd

# def Kappa_Detector_Offset(detector):
#     """
#     detector = d3, d4, mcp, apd, yag
#     """
#     #det={'d4': 0.0,'d3': 7.684, 'mcp': 18.275, 'apd': 29.753, 'yag': 33.269, }   # up to 2020_3
#     det={'d4': 0.0,'d3': -29.123, 'mcp': -18.6416-0.2+0.11, 'apd': 0.0, 'yag': 4.036 }    # 2021_1
#     angle=det[detector]
#     return angle


def set_detector(detector):
    """
    detector = d3, d4, mcp, apd, yag
    Reset tth for a given detector.
    """
    caput('29idKappa:det:set',detector)
    return detector
    
def MPA_Interlock():
    ioc="Kappa"
    n=7
    pvioc="29id"+ioc+":userCalcOut"+str(n)
    ClearCalcOut(ioc,n)
    LLM=-16
    HLM=-6
    caput(pvioc+".DESC","MPA Interlock")
    caput(pvioc+".INPA","29idKappa:m9.DRBV CP NMS")
    caput(pvioc+".B",1)
    caput(pvioc+".CALC$","ABS((("+str(LLM)+"<A && A<"+str(HLM)+") && (B>0))-1)")
    caput(pvioc+".OCAL$",'A')
    caput(pvioc+".OOPT",2)    # When zero
    caput(pvioc+".DOPT",0)    # Use CALC
    caput(pvioc+".IVOA",0)    # Continue Normally
    caput(pvioc+".OUT","29iddMPA:C0O PP NMS")

def setgain(det,gain,unit):
    """
    det  = 'SRS1', 'SRS2', 'SRS3', 'SRS4','mesh','tey','d3','d4'
    gain = 1,2,5,10,20,50,100,200,500
    unit = 'pA, 'nA', 'uA', 'mA'
    """

def cts(time):
    """
    Sets the integration time for the scalers
    """
    ScalerInt(time)

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



