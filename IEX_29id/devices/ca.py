from epics import caget, caput
from time import sleep


### Current Amplifier:

def Reset_CA(ca_ioc,ca_num,rate="Slow"):
    pv="29id"+ca_ioc+":ca"+str(ca_num)
    caput(pv+":reset.PROC",1)
    caput(pv+":digitalFilterSet","Off")
    caput(pv+":medianFilterSet","Off")
    caput(pv+":zeroCheckSet",0)
    caput(pv+":rangeAuto",1)
    caput(pv+":rateSet",rate)
    caput(pv+":rangeAutoUlimit","20mA")
    caput(pv+":read.SCAN",".5 second")