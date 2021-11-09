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
    tth0_set
    sync_PI_motors
    sync_4C_motors
    home_smaract_motors
""".split()



### all the function that moves the diffractometer:
### tth, th, phi, chi, x, y, z, sample

  
# RE = bluesky.RunEngine({​​​​​​​​​}​​​​​​​​​)



## TODO: 
# tth0_set 
# Sync_PI_Motor, Sync_Euler_Motor, Home_SmarAct_Motor


from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor, EpicsSignal, PVPositionerPC, EpicsSignalRO, Signal    
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
    homf = Component(EpicsSignal,".HOMF")
    dval = Component(EpicsSignal,".DVAL")



class _KappaMotors(Device):
    m1  = Component(MyEpicsMotor, "1")    ## kphi    29idKappa:m1.VAL => setpoint
    m2  = Component(MyEpicsMotor, "2")    ## x       29idKappa:m1.RBV => readback
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


class _SoftMotor(PVPositionerPC):
    setpoint = Component(EpicsSignal, "")
    readback = Component(EpicsSignalRO, ".RBV")   # RO means ReadOnly, those are PV that we cannot write to 
    desc = Component(EpicsSignalRO,".DESC")
 #   done = Component(Signal,kind='omitted',value = 0)   # fourc done = 29idKappa:Kappa_busy
 #   done_value = 0                                      # done_value = 0 (Done) or 1 (Busy)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.parent.busy.subscribe(self.done_callback)
       
    # def done_callback(self,*args,**kwargs):
    #     self.done.put(self.parent.ready)




class _FourcMotors(Device):
    th  = Component(_SoftMotor, "29idKappa:Euler_Theta")    # 29idKappa:Euler_Theta     => setpoint
    chi = Component(_SoftMotor, "29idKappa:Euler_Chi")      # 29idKappa:Euler_Theta.RBV => readback
    phi = Component(_SoftMotor, "29idKappa:Euler_Phi")
#    busy_record = Component(EpicsSignalRO, "29idKappa:Kappa_busy", done_value=0,kind='omitted')

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


def sync_PI_motors():
    """
    Synchronize VAL with RBV for tth,kth,kap
    """
    kap_motor = kappa_motors.m7
    kth_motor = kappa_motors.m8
    tth_motor = kappa_motors.m9
    yield from bps.abs_set(kap_motor.sync,1)
    yield from bps.abs_set(kth_motor.sync,1)
    yield from bps.abs_set(tth_motor.sync,1)

def sync_4C_motors():
    """
    Sychronize 4C pseudo motors (VAL) to real motors' positions
    """
    # TODO: test; original script was: proc / sleep(1) / proc
    sync_4C = EpicsSignal("29idKappa:Kappa_sync.PROC", name="sync_4C")
    yield from bps.abs_set(sync_4C,1)


def home_smaract_motors():
    """
    Home the piezo (x,y,z). Home position is middle of travel.
    """
    # TODO: test; is there a callback? or do I need to bos.sleep? original script sleep(10)
    x_motor = kappa_motors.m2
    y_motor = kappa_motors.m3
    z_motor = kappa_motors.m4
    yield from bps.abs_set(x_motor.homf,1)
    yield from bps.abs_set(y_motor.homf,1)
    yield from bps.abs_set(z_motor.homf,1)


def tth0_set():
    """ reset tth = 0 for the current tth position
        tth0 = 0 is defined as direct on small diode (d4)
    """
    # TODO: test, and find a way to handle the print statement
    current_detector = EpicsSignal("29idKappa:det:set", name="current_detector")
    mydetector = current_detector.get()
    tth_motor = kappa_motors.m9 
    if mydetector == 0:
        yield from bps.mv(tth_motor.offset_freeze_switch,1) # frozen offset
        yield from bps.mv(tth_motor.user_offset,0)          # we want the user and dial set to 0 when direct beam is on the small diode (d4)
        yield from bps.mv(tth_motor.set_use_switch,1)       # switch from Use to Set
        yield from bps.mv(tth_motor.user_setpoint,0)        # set user to 0    
        yield from bps.mv(tth_motor.dval,0)                 # set dial to 0
        yield from bps.mv(tth_motor.set_use_switch,0)       # switch back from Set to Use
    else:
        print('tth0 is defined as direct beam on d4 only')
    



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
    # TODO: add name?
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
    # TODO: Add the log info


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


# ----------------------------------------------------------------------------------------------------------------



# def tth0_set():
#     current_det=caget('29idKappa:det:set',as_string=True)
#     if current_det != 'd4':
#         print('tth0 can only be redefined with d4')
#     else:
#         foo=input_d('Are you sure you want to reset tth0 (Y or N)? >')
#         if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
#             caput('29idKappa:m9.SET','Set')
#             sleep(0.5)
#             caput('29idKappa:m9.VAL',0)
#             caput('29idKappa:m9.DVAL',0)
#             sleep(0.5)
#             caput('29idKappa:m9.SET','Use')
#             print("tth position reset to 0")
#         else:
#             pzss


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




