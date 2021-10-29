__all__ = """
    mvx
    mvy
    mvz
    mvkphi
    mvkth
    mvkap
    mvtth
    mvth
    mvchi
    mvphi
    mvrx
    mvry
    mvrz
    mvrkphi
    mvrkth
    mvrkap
    mvrtth
    mvrth
    mvrchi
    mvrphi
    mprint
    mvsample
    uan
""".split()



### all the function that moves the diffractometer:
### tth, th, phi, chi, x, y, z, sample

  
# RE = bluesky.RunEngine({​​​​​​​​​}​​​​​​​​​)



## TODO: 
# mvrx/y/z/tth/kth/kphi/kap X
# mvth/phi/chi X
# mvrth/chi/phi X
# uan X
# tth0_set 
# sample X
# Sync_PI_Motor, Sync_Euler_Motor, Home_SmarAct_Motor


from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor, EpicsSignal, PVPositionerPC, EpicsSignalRO
from ophyd import Component, Device
from apstools.devices import EpicsDescriptionMixin
#from hkl.geometries import E4CV

#logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)



##### Create class to describe real motors (x,y,z,kphi,kth,kap,tth)

# class EpicsDescriptionMixin(EpicsDescriptionMixin, EpicsMotor):   # adds the .DESC field to EpicsMotor
#     pass

class MyEpicsMotor(EpicsMotor):
    sync = Component(EpicsSignal, ".SYNC")
    desc = Component(EpicsSignalRO,".DESC")



class _KappaMotors(Device):
    m1  = Component(MyEpicsMotor, "1")    ## kphi    29idKappa:m1.VAL   29idKappa:m1.RBV
    m2  = Component(MyEpicsMotor, "2")    ## x
    m3  = Component(MyEpicsMotor, "3")    ## y 
    m4  = Component(MyEpicsMotor, "4")    ## z
#   m5  = Component(MyEpicsMotor, "5")    ## not allocated
#   m6  = Component(MyEpicsMotor, "6")    ## not allocated
    m7  = Component(MyEpicsMotor, "7")    ## kap
    m8  = Component(MyEpicsMotor, "8")    ## kth
    m9  = Component(MyEpicsMotor, "9")    ## tth

## Instantiate real motors
kappa_motors = _KappaMotors("29idKtest:m", name="motors")  # kappa_motors.m1


##### Create class to describe pseudo motors (th,chi,phi)


class SoftRealMotor(PVPositionerPC):
    setpoint = Component(EpicsSignal, "")
    readback = Component(EpicsSignalRO, ".RBV")
    desc = Component(EpicsSignalRO,".DESC")

class _FourcMotors(Device):
    th  = Component(SoftRealMotor, "29idKappa:Euler_Theta")    # 29idKappa:Euler_Theta     => caput
    chi = Component(SoftRealMotor, "29idKappa:Euler_Chi")      # 29idKappa:Euler_Theta.RBV => caget
    phi = Component(SoftRealMotor, "29idKappa:Euler_Phi")

## Instantiate pseudo motors
fourc_motors = _FourcMotors("",name="motors")



##### Create class to write to str PVs for troubleshooting

class _Status(Device):
    st1  = Component(EpicsSignal, "1")        
    st2  = Component(EpicsSignal, "2")    
    st3  = Component(EpicsSignal, "3")     
    st4  = Component(EpicsSignal, "4")    

## Instantiate status
status  = _Status("29idKtest:gp:text",name="status")  # =>  status.st1/2/3/4


##### Create class to write to str PVs for troubleshooting

# class _SyncMotors(Device):
#     sync7  = Component(EpicsSignal, "7")        
#     sync8  = Component(EpicsSignal, "8")    
#     sync9  = Component(EpicsSignal, "9")     

# ## Instantiate status
# sync  = _SyncMotors("29idKtest:m",name="sync") 


def _quickmove_plan(value,motor):
    desc  = motor.desc.get()
    if desc == '':
        desc = motor.name.split('_')[-1]
    yield from bps.mv(motor,value)
    yield from bps.mv(status.st1, f"{desc} = {motor.position}")
    motor.log.logger.info("%s = %d", desc, motor.position)


def _quickmove_rel_plan(value,motor):
    desc  = motor.desc.get()
    if desc == '':
        desc = motor.name.split('_')[-1]
    yield from bps.mv(status.st2,f"Old {desc} = {motor.position}")
    yield from bps.mvr(motor,value)
    yield from bps.mv(status.st3,f"New {desc} = {motor.position}")
    motor.log.logger.info("%s = %d", desc, motor.position)


def uan(tth_value,th_value):
    tth_motor = kappa_motors.m9
    th_motor  = fourc_motors.th
    yield from bps.mv(tth_motor,tth_value,th_motor,th_value)
    yield from bps.mv(status.st1, f"tth = {tth_motor.position}; th = {th_motor.position}")
    # Add the log info


def mprint():
    """
    print all motors position
    """
    yield from bps.mv(status.st4, f"{kappa_motors.m2.position},{kappa_motors.m3.position},{kappa_motors.m4.position},{kappa_motors.m1.position},{kappa_motors.m7.position},{kappa_motors.m8.position},{kappa_motors.m9.position}")
    # Add the log info


def mvsample(positions=None):
    """
    move diffractometer to a specific position listed as positions=[x,y,z,kphi,kap,kth,tth]
    default positions is st4
    does not move tth
    """
    if not positions:
        positions = status.st4.get()
        positions=[float(s) for s in positions.split(',')]
    x,y,z,kphi,kap,kth,tth=positions
    yield from bps.mv(kappa_motors.m2,x,kappa_motors.m3,y,kappa_motors.m4,z,
            kappa_motors.m1,kphi,kappa_motors.m7,kap,kappa_motors.m8,kth)
    # Add the log info


def mvth(value):
    """
    moves th to value 
    """
    yield from _quickmove_plan(value,fourc_motors.th)

def mvchi(value):
    """
    moves th to value 
    """
    yield from _quickmove_plan(value,fourc_motors.chi)


def mvphi(value):
    """
    moves th to value 
    """
    yield from _quickmove_plan(value,fourc_motors.phi)


def mvx(value):
    """
    moves x to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m2)


def mvy(value):
    """
    moves y to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m3)


def mvz(value):
    """
    moves z to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m4)


def mvkphi(value):
    """
    moves kphi to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m1)


def mvkap(value):
    """
    moves kap to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m7)


def mvkth(value):
    """
    moves kth to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m8)


def mvtth(value):
    """
    moves tth to value 
    """
    yield from _quickmove_plan(value,kappa_motors.m9)

def mvrth(value):
    """
    moves th to value 
    """
    yield from _quickmove_rel_plan(value,fourc_motors.th)

def mvrchi(value):
    """
    moves th to value 
    """
    yield from _quickmove_rel_plan(value,fourc_motors.chi)


def mvrphi(value):
    """
    moves th to value 
    """
    yield from _quickmove_rel_plan(value,fourc_motors.phi)


def mvrx(value):
    """
    moves x to value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m2)


def mvry(value):
    """
    moves y to value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m3)


def mvrz(value):
    """
    moves z to value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m4)


def mvrkphi(value):
    """
    relative move kphi by value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m1)


def mvrkap(value):
    """
    moves kap to value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m7)


def mvrkth(value):
    """
    moves kth to value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m8)


def mvrtth(value):
    """
    moves tth to value 
    """
    yield from _quickmove_rel_plan(value,kappa_motors.m9)


def sync_PI_motors():
    """
    Synchronize VAL with RBV for tth,kth,kap
    """
    kap_motor = kappa_motors.m7
    kth_motor = kappa_motors.m8
    tth_motor = kappa_motors.m9
    yield from bps.mv(kap_motor.sync, 1,kth_motor.sync, 1,tth_motor.sync, 1)



















# ----------------------------------------------------------------------------------------------------------------





# def Sync_PI_Motor():
#     '''Syncronize VAL with RBV'''
#     for i in [7,8,9]:
#         VAL='29idKappa:m'+str(i)+'.VAL'
#         RBV='29idKappa:m'+str(i)+'.RBV'
#         current_RBV=caget(RBV)
#         caput(VAL,current_RBV)
#     print('PI motors VAL synced to RBV')



# def Sync_Euler_Motor():
#     ''' Sychronize 4C pseudo motor with real motors' positions'''
#     caput('29idKappa:Kappa_sync.PROC',1)
#     sleep(1)
#     caput('29idKappa:Kappa_sync.PROC',1)
#     print('Euler motors VAL/RBV synced to physical motors')



# def Home_SmarAct_Motor():
#     '''Home the piezo (x,y,z). Home position is middle of travel.'''
#     for i in [2,3,4]:
#         VAL='29idKappa:m'+str(i)+'.HOMF'
#         caput(VAL,1)
#         sleep(10)
#     print('SamrAct motors VAL homed')


# def tth0_set():
#     current_det=caget('29idKappa:userStringSeq6.STR1',as_string=True)
#     if current_det != 'd4':
#         print('tth0 can only be redefined with d4')
#     else:
#         foo=prompt('Are you sure you want to reset tth0 (Y or N)? >')
#         if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
#             caput('29idKappa:m9.SET','Set')
#             sleep(0.5)
#             caput('29idKappa:m9.VAL',0)
#             sleep(0.5)
#             caput('29idKappa:m9.SET','Use')
#             print("tth position reset to 0")
#         else:
#             print("That's ok, everybody can get cold feet in tough situation...")



