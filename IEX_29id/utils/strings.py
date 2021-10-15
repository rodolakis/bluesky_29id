from epics import caput
from IEX_29id.utils.misc import RangeUp

##############################################################################################################
###########################            String Sequences & User Average         ######################
##############################################################################################################

def ClearStringSeq(ioc,n):
    pvstr="29id"+ioc+":userStringSeq"+str(n)
    caput(pvstr+".DESC","")
    for i in RangeUp(1,9,1):
        caput(pvstr+".STR"+str(i),"")  # => 4th was populated by some EA stuff
        caput(pvstr+".LNK"+str(i),"")
        caput(pvstr+".DOL"+str(i),"")
        caput(pvstr+".DO"+str(i),0.0)
        caput(pvstr+".DLY"+str(i),0.0)
        caput(pvstr+".WAIT"+str(i),"NoWait")
    caput(pvstr+".STRA","")
    caput(pvstr+".LNKA","")
    caput(pvstr+".DOLA","")
    caput(pvstr+".DOA",0.0)
    caput(pvstr+".DLYA",0.0)
    caput(pvstr+".WAITA","NoWait")
    caput(pvstr+".FLNK","")


def ClearCalcOut(ioc,n):
    pvstr="29id"+ioc+":userCalcOut"+str(n)
    caput(pvstr+".DESC","")
    for i in ["A","B","C","D","E","F","G","H","I","J","K","L"]:
        caput(pvstr+".INP"+i,"")
        caput(pvstr+"."+i,0)
    caput(pvstr+".CALC$","A")
    caput(pvstr+".OCAL$","A")
    caput(pvstr+".OUT","")
    caput(pvstr+".OOPT","On Change")

def ClearUserAvg(avgIOC,n):
    avg_pv="29id"+avgIOC+":userAve"+str(n)
    caput(avg_pv+".DESC","")
    caput(avg_pv+".INPB","")
