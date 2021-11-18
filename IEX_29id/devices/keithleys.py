from ophyd.scaler import ScalerCH
from ophyd import Component
from ophyd import EpicsSignal
from .preamp_base import PreamplifierBaseDevice
from apstools.device import SRS570_PreAmplifier
import logging
import pint
 
logger = logging.getLogger(__name__)
 
scaler = ScalerCH("29idMZ0:scaler1", name="scaler")
 
class PreAmplifier(Device):
 A1 = Component(SRS570_PreAmplifier, "1")
 A2 = Component(SRS570_PreAmplifier, "2")
 A3 = Component(SRS570_PreAmplifier, "3")
 A4 = Component(SRS570_PreAmplifier, "4")
SRS = PreAmplifier("29idd:A", name = "SRS")
 
class Keithley6485(Device):
 rate = Component(EpicsSignal, "rate", write_pv="rateSet")
 range= Component(EpicsSignalRO,'range')
 autorange = Component(EpicsSignal, "rangeAuto", write_pv="rangeAutoSet")
 autoulimit = Component(EpicsSignal, "rateAutoUlimit", write_pv="rateAutoUlimitSet")
 autollimit = Component(EpicsSignal, "rateAutoLlimit", write_pv="rateAutoLlimitSet")
 zerocheck = Component(EpicsSignal, "zeroCheck", write_pv= "zeroCheckSet")
 zerocorrect = Component(EpicsSignal, "zeroCorrect", write_pv= "zeroCorrectSet")
 medianfilter = Component(EpicsSignal, "medianFilter", write_pv= "medianFilterSet")
 medianfilterrank = Component(EpicsSignal, "medianFilterRank", write_pv= "medianFilterRankSet")
 digitalfilter = Component(EpicsSignal, "digitalFilter", write_pv= "digitalFilterSet")
 filtercount = Component(EpicsSignal, "digitalFilterCount", write_pv= "digitalFilterCountSet")
 filtercontrol = Component(EpicsSignal, "digitalFilterControl", write_pv= "digitalFilterControlSet")
 
class Keithley29id(Device):
 ca1 = Component(Keithley6485, "1") 
 ca2 = Component(Keithley6485, "2") 
 ca3 = Component(Keithley6485, "3") 
 ca4 = Component(Keithley6485, "4") 
 ca5 = Component(EpicsMotor, "5") 
 ca6 = Component(EpicsMotor, "6") 
 ca7 = Component(EpicsMotor, "7") 
 ca8 = Component(EpicsMotor, "8") 
 ca9 = Component(EpicsMotor, "9") 
 ca10 = Component(EpicsMotor, "10") 
 ca11 = Component(EpicsMotor, "11") 
 ca12 = Component(EpicsMotor, "12") 
 ca13 = Component(EpicsMotor, "13") 
 ca14 = Component(EpicsMotor, "14") 
 ca15 = Component(EpicsMotor, "15") 
keithley_objects = Keithley6485("29idb:ca", name="rate")




# from epics import  caput, caget
# from IEX_29id.utils.strings import ClearStringSeq
# from IEX_29id.utils.exp import BL_Mode_Read, BL_ioc
# from IEX_29id.utils.misc import RangeUp
# from time import sleep
# import numpy as np


# def ca2flux(ca,hv=None,p=1):
#     curve=LoadResponsivityCurve()
#     responsivity=curve[:,0]
#     energy=curve[:,1]
#     charge = 1.602e-19
#     if hv is None:
#         hv=caget('29idmono:ENERGY_SP')
#         print("\nCalculating flux for:")
#         print("   hv = %.1f eV" % hv)
#         print("   ca = %.3e Amp" % ca)
#     eff=np.interp(hv,energy,responsivity)
#     flux = ca/(eff*hv*charge)
#     if p is not None:
#         print("Flux = %.3e ph/s\n" % flux)
#     return flux



# def LoadResponsivityCurve():
#     FilePath='/home/beams/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/'
#     FileName="DiodeResponsivityCurve"
#     data = np.loadtxt(FilePath+FileName, delimiter=' ', skiprows=1)
#     return data


# def reset_keithley(keithley_ioc,keithley_num,rate="Slow"):
#     pv="29id"+keithley_ioc+":ca"+str(keithley_num)
#     caput(pv+":reset.PROC",1)
#     caput(pv+":digitalFilterSet","Off")
#     caput(pv+":medianFilterSet","Off")
#     caput(pv+":zeroCheckSet",0)
#     caput(pv+":rangeAuto",1)
#     caput(pv+":rateSet",rate)
#     caput(pv+":rangeAutoUlimit","20mA")
#     caput(pv+":read.SCAN",".5 second")


# def reset_all_keithley(rate="Slow"):
#     for i in [1,2,3,4,5,9,10,12,13,14,15]:
#         reset_keithley("b",i,rate)
#     for i in [1,2]:
#         reset_keithley("c",i,rate)
#     #for i in [1,2,3,4,5]:
#     for i in [2,3,4]:
#         reset_keithley("d",i,rate)
#     caput("29idb:ca5:read.SCAN","Passive")    # CA5 in passive
#     print("\nAll the current amplifiers have been reset; ca5 set to passive.")


# def keithley_live_strseq(scanIOC):              # do we need to add 29idb:ca5 ???
#     n=7
#     pvstr="29id"+scanIOC+":userStringSeq"+str(n)
#     ClearStringSeq(scanIOC,n)
#     caput(pvstr+".DESC","CA_Live_"+scanIOC)
#     n=len(Detector_List(scanIOC))
#     for (i,list) in enumerate(Detector_List(scanIOC)):
#         pvCA_read='29id'+list[0]+':ca'+str(list[1])+':read.SCAN CA NMS'
#         pvCA_avg='29id'+list[0]+':ca'+str(list[1])+':digitalFilterSet PP NMS'

#         caput(pvstr+".LNK"+str(i+1),pvCA_avg)
#         caput(pvstr+".STR" +str(i+1),"Off")

#         if n+1+i < 10:
#             caput(pvstr+".LNK" +str(n+1+i),pvCA_read)
#             caput(pvstr+".STR" +str(n+1+i),".5 second")
#             caput(pvstr+".WAIT"+str(n+1+i),"After"+str(n))
#         elif n+1+i == 10:
#             caput(pvstr+".LNKA",pvCA_read)
#             caput(pvstr+".STRA",".5 second")
#             caput(pvstr+".WAITA","After"+str(n))
# #    if scanIOC == 'Kappa':

# #        caput(pvstr+".LNK" +str(2*n+1),'29idMZ0:scaler1.CONT CA NMS')
# #        caput(pvstr+".STR" +str(2*n+1),"AutoCount")
# #        caput(pvstr+".WAIT"+str(2*n+1),"After"+str(2*n))

#     return pvstr+".PROC"



# def Detector_List(scanIOC):
#     """
#     Define the detector used for:
#         keithley_live_strseq()
#         Detector_Triggers_StrSeq()
#         BeforeScan_StrSeq() => puts everybody in passive
#         CA_Average()
#     WARNING: can't have more than 5 otherwise keithley_live_strseq gets angry.
#     """

#     BL_mode=BL_Mode_Read()[0]
#     if scanIOC == "ARPES":
#         CA_list=[["c",1],["b",15],["b",4],["b",13]]
#     elif scanIOC == "Kappa":
#         CA_list=[["d",2],["d",3],["d",4],["b",14]]
#     elif scanIOC == "RSoXS":
#         CA_list=[["d",3],["d",4],["d",5],["b",14],]
#     else:
#         CA_list=[]
# #    if BL_mode == 1:
# #        CA_list=[["b",1],["b",2],["b",3],["b",4],["b",5]] #JM was here
# #        CA_list=[["b",15],["d",2],["d",3],["d",4],["b",14]]
#     return CA_list






# def CA_Name(ca_ioc,ca_num):    #{motor,position}
#     ca={}
#     ca["b"] = {4:'Slit1A',13:'Slit3C',14:'MeshD',15:'DiodeC'}
#     ca["c"] = {1:'TEY'   ,2:'Diode'}
#     ca["d"] = {1:'APD'   ,2:'TEY',  3:'D-3',  4:'D-4',5:'RSoXS Diode'}
#     try:
#         name=ca[ca_ioc][ca_num]
#     except:
#         name=""
#     return name 


# def CA_Autoscale(ca_ioc,ca_num,On_Off='On',gain=7):
#     """
#     On_Off= 'On' => Turns On the Autoscale; gain is irrelevant.
#     On_Off= 'Off' => Turns Off the Autoscale with gain below:
#             0 = 2nA
#             1 = 20nA
#             2 = 200nA
#             3 = 2uA
#             4 = 20uA
#             5 = 200uA
#             6 = 2mA
#             7 = 20mA
#     """
#     pv="29id"+ca_ioc+":ca"+str(ca_num)
#     caput(pv+":rangeAutoSet",On_Off)
#     sleep(0.5)
#     caput(pv+":rangeSet",gain)
#     print(pv,"Autoscale",On_Off)
#     if On_Off == 'Off':
#             sleep(1)
#             print("Gain set to:",caget(pv+":range",as_string=True))


