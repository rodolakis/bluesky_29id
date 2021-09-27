from epics import caget, caput
from time import sleep




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

 
