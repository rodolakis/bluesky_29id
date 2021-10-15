from epics import  caput
from IEX_29id.utils.strings import ClearStringSeq
from IEX_29id.utils.exp import BL_Mode_Read, BL_ioc
from IEX_29id.utils.misc import RangeUp
from time import sleep
### Current Amplifier:

def reset_keithley(keithley_ioc,keithley_num,rate="Slow"):
    pv="29id"+keithley_ioc+":ca"+str(keithley_num)
    caput(pv+":reset.PROC",1)
    caput(pv+":digitalFilterSet","Off")
    caput(pv+":medianFilterSet","Off")
    caput(pv+":zeroCheckSet",0)
    caput(pv+":rangeAuto",1)
    caput(pv+":rateSet",rate)
    caput(pv+":rangeAutoUlimit","20mA")
    caput(pv+":read.SCAN",".5 second")



def keithley_live_strseq(scanIOC):              # do we need to add 29idb:ca5 ???
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



def Detector_List(scanIOC):
    """
    Define the detector used for:
        keithley_live_strseq()
        Detector_Triggers_StrSeq()
        BeforeScan_StrSeq() => puts everybody in passive
        CA_Average()
    WARNING: can't have more than 5 otherwise keithley_live_strseq gets angry.
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
        reset_keithley(ca_ioc,ca_num,rate)    # change for Reset_CA(ca_ioc,ca_num) if we want to
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
