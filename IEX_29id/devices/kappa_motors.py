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
""".split()



# from epics import caget, caput
# from time import sleep
# from IEX_29id.utils.exp import CheckBranch
# from IEX_29id.utils.misc import prompt
# from IEX_29id.devices.motors import Move_Motor_vs_Branch
# from IEX_29id.devices.motors import UMove_Motor_vs_Branch
# from IEX_29id.devices.arpes_motors import Move_ARPES_Sample

### all the function that moves the diffractometer:
### tth, th, phi, chi, x, y, z, sample

  
# RE = bluesky.RunEngine({​​​​​​​​​}​​​​​​​​​)



## TODO: 
# mvrx/y/z/tth/kth/kphi/kap
# mvth/phi/chi
# mvrth/chi/phi
# uan, tth0_set 
# sample
# Sync_PI_Motor, Sync_Euler_Motor, Home_SmarAct_Motor


from bluesky import plan_stubs as bps
import logging
from ophyd import EpicsMotor, EpicsSignal, PVPositionerPC, EpicsSignalRO
from ophyd import Component, Device
from apstools.devices import EpicsDescriptionMixin
#from hkl.geometries import E4CV

#logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class MyEpicsMotor(EpicsDescriptionMixin, EpicsMotor):   # adds the .DESC field to EpicsMotor
    pass


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


kappa_motors = _KappaMotors("29idKtest:m", name="motors")  



class _Status(Device):
    st1  = Component(EpicsSignal, "1")    ## kphi    29idKappa:m1.VAL   29idKappa:m1.RBV
    st2  = Component(EpicsSignal, "2")    ## x
    st3  = Component(EpicsSignal, "3")    ## y 
    st4  = Component(EpicsSignal, "4")    ## z


status  = _Status("29idKtest:gp:text",name="status")



def _pick_motor(number):
    return getattr(kappa_motors, f"m{number}")


def _quickmove_plan(value,motor_number):
    motor = _pick_motor(motor_number)
    desc  = motor.desc.get()
    yield from bps.mv(motor,value)
    yield from bps.mv(status.st1, desc+" = "+str(motor.position))
    motor.log.logger.info("%s = %d", desc, motor.position)

def _quickmove_rel_plan(value,motor_number):
    motor = _pick_motor(motor_number)
    desc  = motor.desc.get()
    yield from bps.mv(status.st2,f"Old {desc} = {motor.position}")
    yield from bps.mvr(motor,value)
    yield from bps.mv(status.st3,f"New {desc} = {motor.position}")
    motor.log.logger.info("%s = %d", desc, motor.position)



class SoftRealMotor(PVPositionerPC):
    setpoint = Component(EpicsSignal, "")
    readback = Component(EpicsSignalRO, ".RBV")
    desc = Component(EpicsSignalRO,".DESC")

class _KappaPseudoMotors(Device):
    th  = Component(SoftRealMotor, "29idKappa:Euler_Theta")    # 29idKappa:Euler_Theta     => caput
    chi = Component(SoftRealMotor, "29idKappa:Euler_Chi")      # 29idKappa:Euler_Theta.RBV => caget
    phi = Component(SoftRealMotor, "29idKappa:Euler_Phi")

pseudo_motors = _KappaPseudoMotors("",name="motors")


def _quickmove_soft_plan(value,motor):
    #desc  = motor.desc.get()  # .DESC field does not get autosaved
    desc = motor.name.split('_')[-1]
    yield from bps.mv(motor,value)
    yield from bps.mv(status.st1, f"{desc} = {motor.position}")
    motor.log.logger.info("%s = %d", desc, motor.position)


def _quickmove_soft_rel_plan(value,motor):
    desc = motor.name.split('_')[-1]
    yield from bps.mv(status.st2,f"Old {desc} = {motor.position}")
    yield from bps.mvr(motor,value)
    yield from bps.mv(status.st3,f"New {desc} = {motor.position}")
    motor.log.logger.info("%s = %d", desc, motor.position)


def mvth(value):
    """
    moves th to value 
    """
    yield from _quickmove_soft_plan(value,pseudo_motors.th)

def mvchi(value):
    """
    moves th to value 
    """
    yield from _quickmove_soft_plan(value,pseudo_motors.chi)


def mvphi(value):
    """
    moves th to value 
    """
    yield from _quickmove_soft_plan(value,pseudo_motors.phi)

def mvrth(value):
    """
    moves th to value 
    """
    yield from _quickmove_soft_rel_plan(value,pseudo_motors.th)

def mvrchi(value):
    """
    moves th to value 
    """
    yield from _quickmove_soft_rel_plan(value,pseudo_motors.chi)


def mvrphi(value):
    """
    moves th to value 
    """
    yield from _quickmove_soft_rel_plan(value,pseudo_motors.phi)


def mvkphi(value):
    """
    moves kphi to value 
    """
    yield from _quickmove_plan(value,1)


def mvx(value):
    """
    moves x to value 
    """
    yield from _quickmove_plan(value,2)


def mvy(value):
    """
    moves y to value 
    """
    yield from _quickmove_plan(value,3)


def mvz(value):
    """
    moves z to value 
    """
    yield from _quickmove_plan(value,4)


def mvkap(value):
    """
    moves kap to value 
    """
    yield from _quickmove_plan(value,7)


def mvkth(value):
    """
    moves kth to value 
    """
    yield from _quickmove_plan(value,8)


def mvtth(value):
    """
    moves tth to value 
    """
    yield from _quickmove_plan(value,9)



def mvrkphi(value):
    """
    relative move kphi by value 
    """
    yield from _quickmove_rel_plan(value,1)


def mvrx(value):
    """
    moves x to value 
    """
    yield from _quickmove_rel_plan(value,2)


def mvry(value):
    """
    moves y to value 
    """
    yield from _quickmove_rel_plan(value,3)


def mvrz(value):
    """
    moves z to value 
    """
    yield from _quickmove_rel_plan(value,4)


def mvrkap(value):
    """
    moves kap to value 
    """
    yield from _quickmove_rel_plan(value,7)


def mvrkth(value):
    """
    moves kth to value 
    """
    yield from _quickmove_rel_plan(value,8)


def mvrtth(value):
    """
    moves tth to value 
    """
    yield from _quickmove_rel_plan(value,9)
















# [4:31 PM] Jemian, Pete R.
    
# In [18]: from ophyd import EpicsSignal
# In [19]: f = EpicsSignal("gp:gp:int1", name="f")
# In [20]: f.get()
# Out[20]: 0
# In [21]: RE(bps.mv(f, 2))
# Out[21]: ()
# In [22]: f.get()
# Out[22]: 2
# In [23]: RE(bps.mvr(f, 1))
# Out[23]: ()
# In [24]: f.get()
# Out[24]: 3





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



# def uan(tth,th):
#     """ Moves tth and th motors simultaneously in the in the Kappa chamber
#     """
#     caput(Kappa_PVmotor("tth")[1],tth)
#     caput(Kappa_PVmotor("th")[1],th)
#     while True:
#         MotorBusy=caget("29idKappa:alldone.VAL",as_string=True)
#         if MotorBusy!='done':
#     #        print "No beam current, please wait..."+dateandtime()
#             sleep(0.1)
#         else:
#             print('tth='+str(tth)+' th='+str(th))
#             break




# def sample(ListPosition):
#     """
#     ARPES: ListPosition = ["Sample Name", x, y, z, th, chi, phi]
#     Kappa: ListPosition = ["Sample Name", x, y, z, tth, kth, kap, kphi]; tth does not move
#     RSoXS: ListPosition=["Sample Name",x,y,z,chi,phi,th,tth]
#     """
#     mybranch=CheckBranch()
#     if mybranch == "c":
#         Move_ARPES_Sample(ListPosition)
#     elif mybranch == "d":
#         Move_Kappa_Sample(ListPosition)
#         print("tth is kept fixed.")


# def Move_Kappa_Sample(ListPosition):
#     """ListPosition = ["Sample Name", x, y, z, tth, kth, kap, kphi]
#     keeps tth fixes
#      """
#     if not isinstance(ListPosition[0],str):
#         ListPosition.insert(0,"")
#     #tth=round(caget("29idHydra:m1.RBV"),2)
#     name,x,y,z,tth,kth,kap,kphi=ListPosition
#     print("\nx="+str(x), " y="+str(y)," z="+str(z), " tth="+str(tth), " kth="+str(kth), " kap="+str(kap), " kphi="+str(kphi),"\n")
#     caput("29idKappa:m2.VAL",x,wait=True,timeout=18000)
#     caput("29idKappa:m3.VAL",y,wait=True,timeout=18000)
#     caput("29idKappa:m4.VAL",z,wait=True,timeout=18000)
#     caput("29idKappa:m8.VAL",kth,wait=True,timeout=18000)
#     caput("29idKappa:m7.VAL",kap,wait=True,timeout=18000)
#     caput("29idKappa:m1.VAL",kphi,wait=True,timeout=18000)
#     print("Sample now @:",name)







