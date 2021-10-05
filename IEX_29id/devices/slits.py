from epics import caput, caget
from IEX_29id.utils.exp import CheckBranch

def slit(val):
    """
    Sets the exit slits:
        ARPES = 0 < x < 300  um
        Kappa  = 0 < x < 1000 um
    """
    SetExitSlit(val)


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

def SetSlit3D(size,position=None):
    if position == None:
        position=round(caget('29idb:Slit4Vt2.D'),2)
    caput("29idb:Slit4Vcenter.VAL",position,wait=True,timeout=18000)
    caput("29idb:Slit4Vsize.VAL",size,wait=True,timeout=18000)
    print("Slit-3D =",size,"um")