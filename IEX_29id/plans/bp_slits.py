
__all__ = """
    slit1_set
    slit2_set
    slit4_set
    slitBL_set
    slits_calc
""".split()

# TODO: Add slit3_set

from bluesky import plan_stubs as bps
import logging
from IEX_29id.devices.beamline_energy import mono
from IEX_29id.devices.slits import slits
from os.path import join
import ast




def slit4_set(size, center= None):
    if center == None:
        center = slits.V4center.position
    sync_4V = slits.V4center.sync
    #yield from bps.abs_set(sync_4V,1)
    size_motor = slits.V4size.setpoint
    center_motor = slits.V4center.setpoint
    yield from bps.mv(size_motor, size, center_motor, center)
    
    
# def slit3_set(size):
#     size_motor = slits.V3size.setpoint
#     yield from bps.mv(size_motor, size)    
    
    
def slit2_set(Hsize,Vsize,Hcenter,Vcenter):
    #sync_2H = slits.center_2H.sync
    #yield from bps.abs_set(sync_2H,1)
    #sync_2V = slits.center_2V.sync
    #yield from bps.abs_set(sync_2V,1)
    Hsize_motor = slits.H2size.setpoint
    Vsize_motor = slits.V2size.setpoint
    Hcenter_motor = slits.H2center.setpoint
    Vcenter_motor = slits.V2center.setpoint
    yield from bps.mv(Hsize_motor, Hsize, Vsize_motor, Vsize, Hcenter_motor, Hcenter, Vcenter_motor, Vcenter)
    
    
def slit1_set(Hsize,Vsize,Hcenter,Vcenter):
    #sync_1H = slits.center_1H.sync
    #yield from bps.abs_set(sync_1H,1)
    #sync_1V = slits.center_1V.sync
    #yield from bps.abs_set(sync_1V,1)
    Hsize_motor = slits.H1size.setpoint
    Vsize_motor = slits.V1size.setpoint
    Hcenter_motor = slits.H1center.setpoint
    Vcenter_motor = slits.V1center.setpoint
    yield from bps.mv(Hsize_motor, Hsize, Vsize_motor, Vsize, Hcenter_motor, Hcenter, Vcenter_motor, Vcenter)
    

def slitBL_set(c2B=1,c1A=1):
    H1size,V1size,H1center,V1center,H2size,V2size,H2center,V2center=slits_calc(c2B,c1A)
    yield from slit2_set(H2size,V2size,H2center,V2center)
    yield from slit1_set(H1size,V1size,H1center,V1center)
    # H1size_motor = slits.H1size.setpoint
    # V1size_motor = slits.V1size.setpoint
    # H1center_motor = slits.H1center.setpoint
    # V1center_motor = slits.V1center.setpoint
    # H2size_motor = slits.H2size.setpoint
    # V2size_motor = slits.V2size.setpoint
    # H2center_motor = slits.H2center.setpoint
    # V2center_motor = slits.V2center.setpoint
    # yield from bps.mv(H1size_motor, H1size, V1size_motor, V1size, H1center_motor, H1center, V1center_motor, V1center)
    # yield from bps.mv(H2size_motor, H2size, V2size_motor, V2size, H2center_motor, H2center, V2center_motor, V2center)
    

    
def slits_calc(c2B=1,c1A=1):

    # RBV = mono.energy.readback.value
    # GRT = mono.grating_density.value

    RBV = mono.energy.readback.get()
    GRT = mono.grating_density.get()
    
    hv=max(RBV,500)
    hv=min(RBV,2000)
    c=4.2/2.2

    GRT,V={1200:('MEG',0.65),2400:('HEG',0.65*c)}[GRT]
    
    def read_dict(FileName,FilePath="/home/beams3/RODOLAKIS/src/macros_29id/IEX_29id/dict/"):
        with open(join(FilePath, FileName)) as f:
            for c,line in enumerate(f.readlines()):
                if line[0] == '=':
                    lastdate=line[8:16]
                lastline=line
            mydict=ast.literal_eval(lastline)
        return mydict
    
    
    def aperture_fit(hv,n):
        K=slit_coef(n)
        sizeH=K[0]+K[1]*hv+K[2]*hv*hv
        sizeV=K[3]+K[4]*hv+K[5]*hv*hv
        return [round(sizeH,3),round(sizeV,3)]


    def slit_coef(n):
        if n == 1:
            H0,H1,H2=(2.3325,-.000936,2.4e-7)     # Redshifted x (H)
            V0,V1,V2=(2.3935,-.0013442,3.18e-7)   # Redshifted z (V)
        if n == 2:
            H0,H1,H2=(3.61,-0.00186,5.2e-7)       # Redshifted x (H)
            V0,V1,V2=(6.8075,-0.003929,9.5e-7)          # Redshifted z (V)
        K=H0,H1,H2,V0,V1,V2
        return K
    
    
    try:
        slit_position=read_dict(FileName='Dict_Slit.txt')
    except KeyError:
        print("Unable to read dictionary")
        return

    V2center= slit_position[GRT]['S2V']
    H2center= slit_position[GRT]['S2H']
    V1center= slit_position[GRT]['S1V']
    H1center= slit_position[GRT]['S1H']

    size1A=( aperture_fit(hv,1)[0]*c1A,       aperture_fit(hv,1)[1]*c1A )
    size2B=( aperture_fit(hv,2)[0]*c2B, round(aperture_fit(hv,2)[1]*c2B*V,3))
    H1size,V1size=size1A
    H2size,V2size=size2B
    
    return H1size,V1size,H1center,V1center,H2size,V2size,H2center,V2center 

