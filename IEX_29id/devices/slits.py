from epics import caput, caget
from IEX_29id.utils.exp import CheckBranch
from IEX_29id.devices.energy import SetSlit2B, Aperture_Fit, read_dict, SetSlit1A

def slit(val):
    """
    Sets the exit slits:
        ARPES = 0 < x < 300  um
        Kappa  = 0 < x < 1000 um
    """
    SetExitSlit(val)




def SetSlit3D(size,position=None):
    if position == None:
        position=round(caget('29idb:Slit4Vt2.D'),2)
    caput("29idb:Slit4Vcenter.VAL",position,wait=True,timeout=18000)
    caput("29idb:Slit4Vsize.VAL",size,wait=True,timeout=18000)
    print("Slit-3D =",size,"um")


def SetSlit_BL(c2B=1,c1A=1,q=None):

    RBV=caget("29idmono:ENERGY_MON")
    GRT=caget("29idmono:GRT_DENSITY")
    hv=max(RBV,500)
    hv=min(RBV,2000)
    c=4.2/2.2

    if GRT==1200:
        GRT='MEG'
        V=0.65        #  set to 65% of RR calculation for both grt => cf 2016_2_summary
    elif GRT==2400:
        GRT='HEG'
        V=0.65*c        #  set to 65% of RR calculation (no longer 80%) => cf 2016_2_summary

    try:
        slit_position=read_dict(FileName='Dict_Slit.txt')
    except KeyError:
        print("Unable to read dictionary")
        return

    V2center= slit_position[GRT]['S2V']
    H2center= slit_position[GRT]['S2H']
    V1center= slit_position[GRT]['S1V']
    H1center= slit_position[GRT]['S1H']

    Size1A=( Aperture_Fit(hv,1)[0]*c1A,       Aperture_Fit(hv,1)[1]*c1A )
    Size2B=( Aperture_Fit(hv,2)[0]*c2B, round(Aperture_Fit(hv,2)[1]*c2B*V,3))
    SetSlit1A (Size1A[0],Size1A[1],H1center,V1center,q)    # standard operating
    SetSlit2B(Size2B[0],Size2B[1],H2center,V2center,q)
def SetExitSlit(size):
    branch=CheckBranch()
    if branch == "c":
        SetSlit3C(size)
    elif branch == "d":
        SetSlit3D(size)

def SetSlit3C(size):
    position=round(Slit3C_Fit(size),1)
    caput("29idb:Slit3CFit.A",size,wait=True,timeout=18000)
    print("Slit-3C =",size,"um  -  ( m24 =",position,")")

def Slit3C_Fit(size):
    K0=-36.383
    K1=0.16473
    K2=-0.00070276
    K3=8.4346e-06
    K4=-5.6215e-08
    K5=1.8223e-10
    K6=-2.2635e-13
    motor=K0+K1*size+K2*size**2+K3*size**3+K4*size**4+K5*size**5+K6*size**6
    return motor

