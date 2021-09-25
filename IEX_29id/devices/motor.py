from epics import caget, caput
from time import sleep



def Sync_Encoder_RBV(ioc):
    D={}
    D["c"]=[1,2,3,4]
    D["b"]=[13,14,15,16,26,27]
    for i in D[ioc]:
        pv="29id"+ioc+":m"+str(i)+".SYNC"
        caput(pv,1)
        print(pv)
