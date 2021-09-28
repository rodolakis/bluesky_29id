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

def ARPES_PVmotor(name):
    """
    used to get the PV associated with a given motor(pnuemonic)
    have gotten rid of all hard coding of the motors, use this instead
    usage:
        ARPES_PVmotor('phi') => ['29idc:m6.RBV', '29idc:m6.VAL', '29idc:m6.SPMG','29idc:m6']
    """
    motor={'x': 1,
      'y':2,
      'z':3,
      'th':4,
      'chi':5,
      'phi':6,
      }
    if name in motor:
        m=str(motor[name])
        PV='29idc:m'+m
        m_VAL=PV+'.VAL'
        m_RBV=PV+'.RBV'
        m_SPMG=PV+'.SPMG'
    return [m_RBV,m_VAL,m_SPMG,PV]


def Move_ARPES_Motor(name,val):
    """
    Moves a motor in the ARPES chamber based on common name, not PV name
    name = x,y,z,th,chi,phi
    """
    m_RBV=ARPES_PVmotor(name)[0]
    m_VAL=ARPES_PVmotor(name)[1]
    caput(m_VAL,val,wait=True,timeout=18000)
def Kappa_PVmotor(name):
    if name == "x":
        m_VAL="29idKappa:m2.VAL"
        m_RBV="29idKappa:m2.RBV"
    elif name == "y":
        m_VAL="29idKappa:m3.VAL"
        m_RBV="29idKappa:m3.RBV"
    elif name == "z":
        m_VAL="29idKappa:m4.VAL"
        m_RBV="29idKappa:m4.RBV"
    elif name == "tth":
        m_VAL="29idKappa:m9.VAL"
        m_RBV="29idKappa:m9.RBV"
    elif name == "kth":
        m_VAL="29idKappa:m8.VAL"
        m_RBV="29idKappa:m8.RBV"
    elif name == "kap":
        m_VAL="29idKappa:m7.VAL"
        m_RBV="29idKappa:m7.RBV"
    elif name == "kphi":
        m_VAL="29idKappa:m1.VAL"
        m_RBV="29idKappa:m1.RBV"
    elif name == "th":
        m_VAL="29idKappa:Euler_Theta"
        m_RBV="29idKappa:Euler_ThetaRBV"
    elif name == "chi":
        m_VAL="29idKappa:Euler_Chi"
        m_RBV="29idKappa:Euler_ChiRBV"
    elif name == "phi":
        m_VAL="29idKappa:Euler_Phi"
        m_RBV="29idKappa:Euler_PhiRBV"
    return [m_RBV,m_VAL]


def Move_Kappa_Motor(name,val):
    m_RBV=Kappa_PVmotor(name)[0]
    m_VAL=Kappa_PVmotor(name)[1]
    caput(m_VAL,val,wait=True,timeout=18000)

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

