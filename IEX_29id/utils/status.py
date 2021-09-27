from epics import caget
from .exp import BL_ioc, CheckBranch
from .misc import dateandtime


def Get_All():
    print("\n")
    print("===========================================================")
    Get_energy(q=None)
    print("-----------------------------------------------------------")
    Get_Mono()
    print("-----------------------------------------------------------")
    Get_Slits()
    print("-----------------------------------------------------------")
    Get_Mirror(1)
    Get_Mirror(2)
    Get_Mirror(3)
    print("-----------------------------------------------------------")
    ARPES=Get_mARPES()[1]
    Kappa=Get_mKappa()[1]
    print("ARPES = ",ARPES)
    print("Kappa = ",Kappa)
    print("===========================================================")

def Get_ARPES():
    print("\n")
    print("===========================================================")
    Get_energy(q=None)
    print("-----------------------------------------------------------")
    Get_Mono()
    print("-----------------------------------------------------------")
    Get_Slits()
    print("-----------------------------------------------------------")
    Get_Mirror(3)
    print("-----------------------------------------------------------")
    ARPES=Get_mARPES()[1]
    print("APRES = ",ARPES)
    print("===========================================================")


def mprint():
    """ 
    Print motor position in current branch as defined by Check_Branch()
    """
    return Print_Motor()

def Print_Motor():
    mybranch=CheckBranch()
    if mybranch == "c":
        x=round(caget(ARPES_PVmotor('x')[0]),2)
        y=round(caget(ARPES_PVmotor('y')[0]),2)
        z=round(caget(ARPES_PVmotor('z')[0]),2)
        th=round(caget(ARPES_PVmotor('th')[0]),2)
        chi=round(caget(ARPES_PVmotor('chi')[0]),2)
        phi=round(caget(ARPES_PVmotor('phi')[0]),2)
        return [x,y,z,th,chi,phi]
    #    print "x="+str(x), " y="+str(y)," z="+str(z), " theta="+str(th)
        print("\nx,y,z,th = ["+str(x)+","+str(y)+","+str(z)+","+str(th)+","+str(chi)+","+str(phi)+"]")
    elif mybranch == "d":
        x=round(caget("29idKappa:m2.RBV"),0)
        y=round(caget("29idKappa:m3.RBV"),0)
        z=round(caget("29idKappa:m4.RBV"),0)
        tth= round(caget("29idKappa:m9.RBV"),2)
        kth= round(caget("29idKappa:m8.RBV"),2)
        kap= round(caget("29idKappa:m7.RBV"),2)
        kphi=round(caget("29idKappa:m1.RBV"),2)
        th= round(caget("29idKappa:Euler_ThetaRBV"),3)
        chi= round(caget("29idKappa:Euler_ChiRBV"),3)
        phi=round(caget("29idKappa:Euler_PhiRBV"),3)
        #(th,chi,phi)=KtoE(kth,kap,kphi)
        print("\nx,y,z,tth,th,chi,phi   = ["+str(x)+","+str(y)+","+str(z)+","+str(tth)+","+str(th)+","+str(chi)+","+str(phi)+"]")
        print("x,y,z,tth,kth,kap,kphi = ["+str(x)+","+str(y)+","+str(z)+","+str(tth)+","+str(kth)+","+str(kap)+","+str(kphi)+"]")
        #print "\ntth,th,chi,phi = ["+str(round(tth,1))+","+str(round(th,1))+","+str((round(chi,1)))+","+str((round(phi,1)))+"]"
        pos=[x,y,z,tth,kth,kap,kphi]
        return pos
    #elif mybranch == "e":
    #    print(Get_mRSoXS()[1])


def Get_energy(q=1):
    """ returns: ID_Mode, ID_QP, ID_SP, ID_RBV, hv, grt """
    ID_Mode_list=['RCP','LCP','V','H','NH']
    ID_Mode=ID_Mode_list[caget("ID29:ActualMode")]
    ID_QP=caget("ID29:QuasiRatio.RVAL")
    ID_SP=caget("ID29:EnergySet.VAL")*1000
    ID_RBV=caget("ID29:Energy.VAL")*1000
    hv=caget("29idmono:ENERGY_MON")
    density=caget("29idmono:GRT_DENSITY")
    grt={1200:'MEG',2400:'HEG'}[density]
    if q != 1:
        print(" ID SP  : "+"%.2f" % ID_SP , "eV    ID mode : "+ID_Mode)
        print(" ID RBV : "+"%.2f" % ID_RBV, "eV    QP mode : "+str(ID_QP) +" %")
        print(" Mono   : "+"%.2f" % hv,"eV    GRT : "+grt)
    return (ID_Mode,ID_QP,ID_SP,ID_RBV,hv,grt)




def Get_Mono(q=0):
    """
    prints mono variables for current setting using Mono_Optics()
    for quiet Mono_Optics()
    returns [[MirrorInfo],[GratingInfo],[MotorPositions]]
    """
    Mono=Mono_Optics()
    MIR_Type  =Mono[0][0]
    MIR_Offset=Mono[0][1]
    MIR_Tx=    Mono[0][2]
    GRT_Type  =Mono[1][0]
    GRT_Offset=Mono[1][1]
    GRT_Tx=    Mono[1][2]
    GRT_DL=    Mono[1][3]
    GRT_B2=    Mono[1][4]
    CFF=  Mono[2][0]
    TUN0= Mono[2][1]
    TUN1= Mono[2][2]
    TUN2= Mono[2][3]
    TUN3= Mono[2][4]
    ARM=  Mono[2][5]
    print(" Mono Optics: "+MIR_Type+" -  "+GRT_Type)
    print(" MIR Offset : "+"%.4f" % MIR_Offset , "    MIR Tx : "+"%.3f" % MIR_Tx)
    print(" GRT Offset : "+"%.4f" % GRT_Offset , "    GRT Tx : "+"%.3f" % GRT_Tx)
    print(" GRT b2 : "+"%.4e" % GRT_B2 , "    GRT Density: "+"%.1f" % GRT_DL,"l/mm")
    print(" cff : "+"%.4f" % CFF , "         exit arm: "+"%.1f" % ARM,"mm")
    print(" tun0 : "+"%.4e" % TUN0 , "    tun1: "+"%.4e" % TUN1)
    print(" tun2 : "+"%.4e" % TUN2 , "    tun3: "+"%.4e" % TUN3)
    return Mono_Optics()


def Get_CFF():
    Mono=Mono_Optics()
    CFF=  Mono[2][0]
    TUN0= Mono[2][1]
    TUN1= Mono[2][2]
    TUN2= Mono[2][3]
    TUN3= Mono[2][4]
    ARM=  Mono[2][5]
    print(" cff : "+"%.4f" % CFF , "          exit arm: "+"%.1f" % ARM,"mm")
    print(" tun0 : "+"%.4e" % TUN0 , "    tun1: "+"%.4e" % TUN1)
    print(" tun2 : "+"%.4e" % TUN2 , "    tun3: "+"%.4e" % TUN3)
    return Mono_Optics()

def Get_Mirror(n):
    branch=CheckBranch()
    if n == 0 or n == 1:
        Tx=caget("29id_m"+str(n)+":TX_MON")
        Ty=caget("29id_m"+str(n)+":TY_MON")
        Tz=caget("29id_m"+str(n)+":TZ_MON")
        Rx=caget("29id_m"+str(n)+":RX_MON")
        Ry=caget("29id_m"+str(n)+":RY_MON")
        Rz=caget("29id_m"+str(n)+":RZ_MON")
        print(" M"+str(n)+" @ "+"%.3f" % Tx, "/","%.3f" % Ty, "/","%.3f" % Tz, "/","%.3f" % Rx, "/","%.3f" % Ry, "/","%.3f" % Rz)
    if n == 3:
        Tx=caget("29id_m"+str(n)+"r:TX_MON")
        Ty=caget("29id_m"+str(n)+"r:TY_MON")
        Tz=caget("29id_m"+str(n)+"r:TZ_MON")
        Rx=caget("29id_m"+str(n)+"r:RX_MON")
        Ry=caget("29id_m"+str(n)+"r:RY_MON")
        Rz=caget("29id_m"+str(n)+"r:RZ_MON")
    #     Get_HXP()
        print(" M"+str(n)+"R @ "+"%.3f" % Tx, "/","%.3f" % Ty, "/","%.3f" % Tz, "/","%.3f" % Rx, "/","%.5f" % Ry, "/","%.3f" % Rz)
        if branch == "d":
            print(" => In D branch")
        elif branch == "c":
            print(" => In C branch")

def Get_HXP():
    branch=CheckBranch()
    if branch == "d":
        Tx=caget("29idHXP:hxp2:m1.RBV")
        Ty=caget("29idHXP:hxp2:m2.RBV")
        Tz=caget("29idHXP:hxp2:m3.RBV")
        Rx=caget("29idHXP:hxp2:m4.RBV")
        Ry=caget("29idHXP:hxp2:m5.RBV")
        Rz=caget("29idHXP:hxp2:m6.RBV")
        print(" M4R @ "+"%.3f" % Tx, "/","%.3f" % Ty, "/","%.3f" % Tz, "/","%.3f" % Rx, "/","%.3f" % Ry, "/","%.3f" % Rz)
    elif branch == "c":
        Tx=caget("29idHXP:hxp1:m1.RBV")
        Ty=caget("29idHXP:hxp1:m2.RBV")
        Tz=caget("29idHXP:hxp1:m3.RBV")
        Rx=caget("29idHXP:hxp1:m4.RBV")
        Ry=caget("29idHXP:hxp1:m5.RBV")
        Rz=caget("29idHXP:hxp1:m6.RBV")
        print(" M3A @ "+"%.3f" % Tx, "/","%.3f" % Ty, "/","%.3f" % Tz, "/","%.3f" % Rx, "/","%.3f" % Ry, "/","%.3f" % Rz)
        Tx=caget("29idHXP:hxp3:m1.RBV")
        Ty=caget("29idHXP:hxp3:m2.RBV")
        Tz=caget("29idHXP:hxp3:m3.RBV")
        Rx=caget("29idHXP:hxp3:m4.RBV")
        Ry=caget("29idHXP:hxp3:m5.RBV")
        Rz=caget("29idHXP:hxp3:m6.RBV")
        print(" M4A @ "+"%.3f" % Tx, "/","%.3f" % Ty, "/","%.3f" % Tz, "/","%.3f" % Rx, "/","%.3f" % Ry, "/","%.3f" % Rz)

def Get_Slits():
    SyncAllSlits()
    Hsize=round(caget("29idb:Slit1Hsize.VAL"),2)
    Vsize=round(caget("29idb:Slit1Vsize.VAL"),2)
    Hcenter=round(caget("29idb:Slit1Hcenter.VAL"),2)
    Vcenter=round(caget("29idb:Slit1Vcenter.VAL"),2)
    print(" Slit-1A = ("+str(Hsize)+"x"+str(Vsize)+") @ ("+str(Hcenter)+","+str(Vcenter)+")")
    Hsize=round(caget("29idb:Slit2Hsize.VAL"),2)
    Vsize=round(caget("29idb:Slit2Vsize.VAL"),2)
    Hcenter=round(caget("29idb:Slit2Hcenter.VAL"),2)
    Vcenter=round(caget("29idb:Slit2Vcenter.VAL"),2)
    print(" Slit-2B = ("+str(Hsize)+"x"+str(Vsize)+") @ ("+str(Hcenter)+","+str(Vcenter)+")")
    Csize=round(caget("29idb:Slit3CRBV"),0)
    print(" Slit-3C = "+str(Csize)+" um")
    Dsize=caget("29idb:Slit4Vsize.VAL")
    Dcenter=round(caget("29idb:Slit4Vcenter.VAL"),0)
    print(" Slit-3D = "+str(Dsize)+" um @ "+str(Dcenter)+" um")


def Get_mARPES(mode='User'):
    if mode == 'Dial':
        suffix='.DRBV'
    else:
        suffix='.RBV'
    x  =round(caget(ARPES_PVmotor('x')[3]+suffix),3)
    y  =round(caget(ARPES_PVmotor('y')[3]+suffix),3)
    z  =round(caget(ARPES_PVmotor('z')[3]+suffix),3)
    th =round(caget(ARPES_PVmotor('th')[3]+suffix),3)
    phi=round(caget(ARPES_PVmotor('phi')[3]+suffix),3)
    chi=round(caget(ARPES_PVmotor('chi')[3]+suffix),3)
    ARPES=[x,y,z,th,phi,chi]
    return mode,ARPES

def Get_mKappa(mode='User'):
    if mode == 'Dial':
        suffix='DRBV'
    else:
        suffix='RBV'
    x  =round(caget("29idKappa:m2."+suffix),1)
    y  =round(caget("29idKappa:m3."+suffix),1)
    z  =round(caget("29idKappa:m4."+suffix),1)
    tth =round(caget("29idKappa:m9."+suffix),3)
    kth =round(caget("29idKappa:m8."+suffix),3)
    kap =round(caget("29idKappa:m7."+suffix),3)
    kphi=round(caget("29idKappa:m1."+suffix),3)
    Kappa=[x,y,z,tth,kth,kap,kphi]
    return mode,Kappa

def Get_Kappa():
    print("\n")
    print("===========================================================")
    Get_energy(q=None)
    print("-----------------------------------------------------------")
    Get_Mono()
    print("-----------------------------------------------------------")
    Get_Slits()
    print("-----------------------------------------------------------")
    Get_Mirror(3)
    print("-----------------------------------------------------------")
    Kappa=Get_mKappa()[1]
    print("Kappa = ",Kappa)
    print("===========================================================")


def Get_Gain():
    d3=caget("29idMZ0:scaler1.S3")
    d4=caget("29idMZ0:scaler1.S4")
    m=caget("29idMZ0:scaler1.S14")
    A2_gain=caget('29idd:A2sens_num.VAL',as_string=True)
    A2_unit=caget('29idd:A2sens_unit.VAL',as_string=True)
    A3_gain=caget('29idd:A3sens_num.VAL',as_string=True)
    A3_unit=caget('29idd:A3sens_unit.VAL',as_string=True)
    A1_gain=caget('29idd:A1sens_num.VAL',as_string=True)
    A1_unit=caget('29idd:A1sens_unit.VAL',as_string=True)
    print("D3 = "+str(d3)+"\t @ "+A2_gain+" "+A2_unit)
    print("D4 = "+str(d4)+"\t @ "+A3_gain+" "+A3_unit)
    print("mesh = "+str(m)+"\t @ "+A1_gain+" "+A1_unit)


def Get_SnapShot(which=None):
    """
    prints current settings in D-branch (Kappa) 
    """
    if which == None:
        which = BL_ioc()
    if which == 'Kappa':
        print("Snapshot: "+str(dateandtime()))
        Get_All()

        print("\n---Motors---")
        for m in [2,3,4,9,8,7,1]:
            pv="29idKappa:m"+str(m)
            val=round(caget(pv+".VAL"),3)
            rbv=round(caget(pv+".RBV"),)
            stat=caget(pv+".STAT",as_string=True)
            stup=caget(pv+".STUP",as_string=True)
            print(pv +"\t VAL = "+str(val)+"     \tRBV = "+str(rbv)+"\t"+stat+"\t"+stup)
        print("\n---Temperature---")
        for sp in [1,2]:
            pv="29idc:LS340:TC1"
            val=caget(pv+":wr_SP"+str(sp))
            rbv=caget(pv+":SP"+str(sp))
            print(pv+"_"+str(sp)+"\t SP = "+str(val)+"\t\t RBV = "+str(rbv))
        print("\t\t\t   Range = "+str(caget(pv+":Rg_rdbk",as_string=True))+"\t Power = "+str(caget(pv+":Heater")))

        print("\n---Mesh---")
        #pv='29idd:A2sens_num.VAL
        pv="29idb:m28"
        print("Position: "+pv+"\t VAL = "+str(caget(pv+".VAL"))+"\t RBV = "+str(caget(pv+".RBV")))

        print("\n---Scalers---")
        Get_Gain()

        print("\n---MPA---")
        HV_SP="29idKappa:userCalcOut9.A"
        HV_RBV="29idKappa:userCalcOut10.OVAL"
        HV_Status="29iddMPA:C0O"
        HV_AcqTime="29iddMPA:det1:AcquireTime"
        print("HV_SP = "+str(caget(HV_SP))+"\t\tHV_RBV = "+str(caget(HV_RBV)))
        print("status = "+str(caget(HV_Status))+"\t\t Acq time = "+str(caget(HV_AcqTime)))



def Get_PID(which='LHe'):
    T=caget("29idARPES:LS335:TC1:IN1")
    SP=caget("29idARPES:LS335:TC1:OUT1:SP")
    P=caget("29idARPES:LS335:TC1:P1")
    I=caget("29idARPES:LS335:TC1:I1")
    D=caget("29idARPES:LS335:TC1:D1")
    Range=caget("29idARPES:LS335:TC1:HTR1:Range",as_string=True)
#    print SP,P,I,D,Range
    print("Current T:", T,'K')
    print("PID[\'"+which+"\',"+str(SP)+"]=["+str(P)+","+str(I)+","+str(D)+",\'"+Range+"\']")