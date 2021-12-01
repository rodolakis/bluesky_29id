# from epics import caput, caget
# from math import inf, nan
# from IEX_29id.utils.exp import CheckBranch
# from IEX_29id.utils.misc import read_dict



from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsSignal, PVPositionerPC, EpicsSignalRO    
from ophyd import Component, Device
from apstools.devices import EpicsDescriptionMixin

# see 4ID-D: https://github.com/APS-4ID-POLAR/ipython-polar/blob/master/profile_bluesky/startup/instrument/devices/slits.py

class _SoftSlitSize(PVPositionerPC):
    setpoint = Component(EpicsSignal, "size.VAL")           # 29idb:Slit1Hsize.VAL   => setpoint
    readback = Component(EpicsSignalRO, "t2.C")             # 29idb:Slit1t2.C        => readback  
    sync = Component(EpicsSignal,"sync.PROC",kind='omitted')# RO means ReadOnly, those are PV that we cannot write to 
    done_value = 1                                          # done_value = 1 (Done) or 0 (moving)
    done = Component(EpicsSignalRO,'DMOV',kind='omitted')   # slits done = 29idb:Slit1VDMOV


class _SoftSlitCenter(PVPositionerPC):
    setpoint = Component(EpicsSignal, "center.VAL")         # 29idb:Slit1Hsize.VAL   => setpoint
    readback = Component(EpicsSignalRO, "t2.D")             # 29idb:Slit1t2.C        => readback  
    sync = Component(EpicsSignal,"sync.PROC",kind='omitted')               # RO means ReadOnly, those are PV that we cannot write to 
    done_value = 1                                          # done_value = 1 (Done) or 0 (moving)
    done = Component(EpicsSignalRO,'DMOV',kind='omitted')                 # slits done = 29idb:Slit1VDMOV



class _My4Slits(Device):
    H1size = Component(_SoftSlitSize, "1H")    
    V1size = Component(_SoftSlitSize, "1V")  
    H1center = Component(_SoftSlitCenter, "1H")    
    V1center = Component(_SoftSlitCenter, "1V")  
    H2size = Component(_SoftSlitSize, "2H")    
    V2size = Component(_SoftSlitSize, "2V")  
    H2center = Component(_SoftSlitCenter, "2H")    
    V2center = Component(_SoftSlitCenter, "2V")  

## Instantiate pseudo motors
slits = _My4Slits("29idb:Slit",name="motors")





#--------------------------- Old Functions ----------------------------#


# def slit(val):
#     """
#     Sets the exit slits:
#         ARPES = 0 < x < 300  um
#         Kappa  = 0 < x < 1000 um
#     """
#     SetExitSlit(val)


# def SetSlit1A(Hsize,Vsize,Hcenter,Vcenter,q=None):   
#     """move slits 1A: Hsize x Vsize centered at (Hcenter,Vcenter)"""
#     caput("29idb:Slit1Hsync.PROC",1)    # make sure slits are in sink with real motors
#     caput("29idb:Slit1Vsync.PROC",1)
#     caput("29idb:Slit1Hsize.VAL", Hsize)
#     caput("29idb:Slit1Vsize.VAL", Vsize)
#     caput("29idb:Slit1Hcenter.VAL",Hcenter)
#     caput("29idb:Slit1Vcenter.VAL",Vcenter)
#     if not q:
#         print("Slit-1A = ("+str(round(Hsize,3))+"x"+str(round(Vsize,3))+") @ ("+str(Hcenter)+","+str(Vcenter)+")")

# def SetSlit2B(Hsize,Vsize,Hcenter,Vcenter,q=None):
#     caput("29idb:Slit2Hsync.PROC",1)
#     caput("29idb:Slit2Vsync.PROC",1)
#     caput("29idb:Slit2Hsize.VAL", Hsize)
#     caput("29idb:Slit2Vsize.VAL", Vsize)
#     caput("29idb:Slit2Hcenter.VAL",Hcenter)
#     caput("29idb:Slit2Vcenter.VAL",Vcenter)
#     if not q:
#         print("Slit-2B = ("+str(Hsize)+"x"+str(Vsize)+") @ ("+str(Hcenter)+","+str(Vcenter)+")")



# def SetSlit3C(size):
#     caput("29idb:Slit3CFit.A",size)
#     print("Slit-3C =",size,"um")


# def SetSlit3D(size,position=None):
#     if position == None:
#         position=round(caget('29idb:Slit4Vt2.D'),2)
#     caput("29idb:Slit4Vcenter.VAL")
#     caput("29idb:Slit4Vsize.VAL",size,wait=True,timeout=18000)
#     print("Slit-3D =",size,"um")


# def SetSlit_BL(c2B=1,c1A=1,q=None):

#     RBV=caget("29idmono:ENERGY_MON")
#     GRT=caget("29idmono:GRT_DENSITY")
#     hv=max(RBV,500)
#     hv=min(RBV,2000)
#     c=4.2/2.2

#     if GRT==1200:
#         GRT='MEG'
#         V=0.65        #  set to 65% of RR calculation for both grt => cf 2016_2_summary
#     elif GRT==2400:
#         GRT='HEG'
#         V=0.65*c        #  set to 65% of RR calculation (no longer 80%) => cf 2016_2_summary

#     try:
#         slit_position=read_dict(FileName='Dict_Slit.txt')
#     except KeyError:
#         print("Unable to read dictionary")
#         return

#     V2center= slit_position[GRT]['S2V']
#     H2center= slit_position[GRT]['S2H']
#     V1center= slit_position[GRT]['S1V']
#     H1center= slit_position[GRT]['S1H']

#     Size1A=( Aperture_Fit(hv,1)[0]*c1A,       Aperture_Fit(hv,1)[1]*c1A )
#     Size2B=( Aperture_Fit(hv,2)[0]*c2B, round(Aperture_Fit(hv,2)[1]*c2B*V,3))
#     SetSlit1A (Size1A[0],Size1A[1],H1center,V1center,q)    # standard operating
#     SetSlit2B(Size2B[0],Size2B[1],H2center,V2center,q)


# def SetExitSlit(size):
#     branch=CheckBranch()
#     if branch == "c":
#         SetSlit3C(size)
#     elif branch == "d":
#         SetSlit3D(size)


# def Slit3C_Fit(size):
#     K0=-36.383
#     K1=0.16473
#     K2=-0.00070276
#     K3=8.4346e-06
#     K4=-5.6215e-08
#     K5=1.8223e-10
#     K6=-2.2635e-13
#     motor=K0+K1*size+K2*size**2+K3*size**3+K4*size**4+K5*size**5+K6*size**6
#     return motor

# def Slit_Coef(n):
#     if n == 1:
#         pv='29id:k_slit1A'
#         #Redshifted x (H):
#         H0=2.3325
#         H1=-.000936
#         H2=2.4e-7
#          #Redshifted z (V):
#         V0=2.3935
#         V1=-.0013442
#         V2=3.18e-7
#     if n == 2:
#         pv='29id:k_slit2B'
#         #Redshifted x (H):
#         H0=3.61
#         H1=-0.00186
#         H2=5.2e-7
#         #Redshifted z (V):
#         V0=6.8075
#         V1=-0.003929
#         V2=9.5e-7
#     K=H0,H1,H2,V0,V1,V2
#     return pv,K




# def Aperture_Fit(hv,n):
#     K=Slit_Coef(n)[1]
#     sizeH=K[0]+K[1]*hv+K[2]*hv*hv
#     sizeV=K[3]+K[4]*hv+K[5]*hv*hv
#     return [round(sizeH,3),round(sizeV,3)]



# # SetSlits:
    
# def SetSlit(n,Hsize=None,Vsize=None,Hcenter=0,Vcenter=0,q=None):
    
#     if n == 1:
#         if Hsize in [inf,nan,None]: Hsize=4.5
#         if Vsize in [inf,nan,None]: Vsize=4.5
#         SetSlit1A(Hsize,Vsize,Hcenter,Vcenter,q=None)
#     elif n == 2:
#         if Hsize in [inf,nan,None]: Hsize=6
#         if Vsize in [inf,nan,None]: Vsize=8
#         SetSlit2B(Hsize,Vsize,Hcenter,Vcenter,q=None)
#     else:
#         print('Not a valid slit number')
    
