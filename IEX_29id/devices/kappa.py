from epics import caget, caput
from time import sleep
from IEX_29id.utils.exp import CheckBranch
from IEX_29id.devices.motors import Move_Motor_vs_Branch


### all the function that move/scan the diffractometer:
### tth, th, phi, chi, x, y, z



def mvtth(val):
    """ Moves tth motor in the in the Kappa chamber
    """
    name="tth"
    mybranch=CheckBranch()
    #if branch == "c":
    if mybranch == "c":
        print("   tth motor does not exit")
    #elif branch == "d":
    elif mybranch == "d":
        Move_Motor_vs_Branch(name,val)



def Sync_PI_Motor():
    '''Syncronize VAL with RBV'''
    for i in [7,8,9]:
        VAL='29idKappa:m'+str(i)+'.VAL'
        RBV='29idKappa:m'+str(i)+'.RBV'
        current_RBV=caget(RBV)
        caput(VAL,current_RBV)
    print('PI motors VAL synced to RBV')



def Sync_Euler_Motor():
    ''' Sychronize 4C pseudo motor with real motors' positions'''
    caput('29idKappa:Kappa_sync.PROC',1)
    sleep(1)
    caput('29idKappa:Kappa_sync.PROC',1)
    print('Euler motors VAL/RBV synced to physical motors')



def Home_SmarAct_Motor():
    '''Home the piezo (x,y,z). Home position is middle of travel.'''
    for i in [2,3,4]:
        VAL='29idKappa:m'+str(i)+'.HOMF'
        caput(VAL,1)
        sleep(10)
    print('SamrAct motors VAL homed')

 


def tth0_set():
    current_det=caget('29idKappa:userStringSeq6.STR1',as_string=True)
    if current_det != 'd4':
        print('tth0 can only be redefined with d4')
    else:
        foo=input_d('Are you sure you want to reset tth0 (Y or N)? >')
        if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
            caput('29idKappa:m9.SET','Set')
            sleep(0.5)
            caput('29idKappa:m9.VAL',0)
            sleep(0.5)
            caput('29idKappa:m9.SET','Use')
            print("tth position reset to 0")
        else:
            print("That's ok, everybody can get cold feet in tough situation...")
