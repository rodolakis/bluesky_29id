from epics import  caput



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