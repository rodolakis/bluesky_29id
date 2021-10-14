from epics import caget, caput
from IEX_29id.utils.exp import CheckBranch



def Sync_Encoder_RBV(ioc):
    D={}
    D["c"]=[1,2,3,4]
    D["b"]=[13,14,15,16,26,27]
    for i in D[ioc]:
        pv="29id"+ioc+":m"+str(i)+".SYNC"
        caput(pv,1)
        print(pv)





def Move_Motor_vs_Branch(name,val):
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        Move_ARPES_Motor(name,val)
        RBV=round(caget(ARPES_PVmotor(name)[0]),3)
    #elif branch == "d":
    elif mybranch == "d":
        #caput('29idKappa:Kappa_sync.PROC',1)
        Move_Kappa_Motor(name,val)
        RBV=round(caget(Kappa_PVmotor(name)[0]),3)
    #elif mybranch == "e":
    #    Move_RSoXS_Motor(name,val)
    #    RBV=round(caget(RSoXS_PVmotor(name)[0]),3)
    print(name+" = "+ str(RBV))



def UMove_Motor_vs_Branch(name,val):
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        RBV=round(caget(ARPES_PVmotor(name)[0]),3)
        print("Old: "+name+" = "+ str(RBV))
        Move_ARPES_Motor(name,val+RBV)
        RBV=round(caget(ARPES_PVmotor(name)[0]),3)
    #elif branch == "d":
    elif mybranch == "d":
        RBV=round(caget(Kappa_PVmotor(name)[0]),3)
        print("Old: "+name+" = "+ str(RBV))
        Move_Kappa_Motor(name,val+RBV)
        RBV=round(caget(Kappa_PVmotor(name)[0]),3)
    #elif mybranch == "e":
    #    RBV=round(caget(RSoXS_PVmotor(name)[0]),3)
    #    print("Old: "+name+" = "+ str(RBV))
    #    Move_RSoXS_Motor(name,val+RBV)
    #    RBV=round(caget(RSoXS_PVmotor(name)[0]),3)
    print("New: "+name+" = "+ str(RBV))

