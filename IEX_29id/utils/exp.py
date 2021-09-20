
from pyepics import caput, caget
from .folders import *
from .strings import ClearCalcOut
import datetime


def Check_run():
    todays_date = datetime.today()
    
    date1 = ( 1, 1)   # start date run_1
    date2 = ( 5, 1)   # start date run_2
    date3 = (10, 1)   # start date run_3
    
    datex = (todays_date.month,todays_date.day)
    
    if date1 <= datex < date2:
        run=str(todays_date.year)+'_1'
    elif date2 <= datex < date3:
        run=str(todays_date.year)+'_2'
    else:
        run=str(todays_date.year)+'_3'
    print('Current run:', run)
    return(run)



## BeamLine mode functions
def BL_Mode_Set(which):
    """
    which = "Staff", "User", "He" (Helium Lamp), "RSoXS"; if which is not specified then i=4
    """
    n=5
    ClearCalcOut("b",n)
    pvstr="29idb:userCalcOut"+str(n)
    caput(pvstr+".DESC","BL_Mode")
    if which == "Staff":
        i=1        # Staff
    elif which == "He":
        i=2        # Helium
    elif which == "User":
        i=0        # User
    elif which == "RSoXS":
        i=3
    else:
        i=4
    caput(pvstr+".A",i)

def BL_Mode_Read():
    caput("29idb:userCalcOut5.PROC",1)            # After reboot value return to 0 even if A=1
    BL_mode=caget("29idb:userCalcOut5.VAL")        # User = 0, Staff = 1, He = 2, Other = 3
    if BL_mode == 1:
        which="Staff"
    elif BL_mode == 2:
        which="He Lamp"
    elif BL_mode == 0:
        which="User"
    elif BL_mode == 3:
        which="RSoXS"
    elif BL_mode == 4:
        which="Other"
    return BL_mode,which


def BL_ioc():
    BL_mode=BL_Mode_Read()[0]            # User = 0, Staff = 1, He = 2
    if BL_mode == 0 or BL_mode == 1:         # User + Staff
        branch=CheckBranch()            # TO BE REMOVED ONCE WE HAVE IT AS A GLOBAL VARIABLE
        if branch == "c":
            scanIOC='ARPES'
        if branch == "d":
            scanIOC='Kappa'
    elif  BL_mode == 2:                    # Helium
        scanIOC='ARPES'
    elif  BL_mode ==3:                    # RSoXS chamber
        scanIOC='RSoXS'
    return scanIOC



def WaitForIt(D,H,M):
    """
    D = how many days from now
    H,M = what time that day in 24h clock

    e.g.: if today is           Wed Nov 21 at 14:00
        WaitForIt(2,9,0) => Fri Nov 23 at  9:00
    """
    t = datetime.datetime.today()
    day = datetime.timedelta(days=D)
    future = t + day
    returnTime = datetime.datetime(future.year, future.month, future.day, H, M)
    timeToWait = returnTime - t
    s=round(timeToWait.total_seconds(),1)
    m=round(timeToWait.total_seconds()/60.0,1)
    h=round(timeToWait.total_seconds()/3600.0,1)
    print("Now is:      "+str(t))
    print("Target date: "+str(returnTime))
    print("Sleeping for "+str(s)+" s = "+str(m)+" m = "+str(h)+" h")
    print("Waaaaaaaait for it...")
    time.sleep(timeToWait.total_seconds())
    print(dateandtime())


def playsound(sound='FF'):
    """
    plays a sound when run
    'FF' Final Fantasy victory sound
    'ding' a subtle ding noise
    'hallelujah' hallelujah chorus
    """
    if sound == 'FF':
        sounds = '/home/beams/29IDUSER/Documents/User_Macros/Macros_29id/Sound_Files/VictoryFF.wav'
    elif sound == 'ding':
        sounds = '/home/beams/29IDUSER/Documents/User_Macros/Macros_29id/Sound_Files/ding.wav'
    elif sound == 'hallelujah':
        sounds = '/home/beams/29IDUSER/Documents/User_Macros/Macros_29id/Sound_Files/hallelujah.wav'
    system('aplay ' + sounds)

def RangeUp(start,end,step):
    while start <= end:
        yield start
        start += abs(step)

def RangeDown(start,end,step):
    while start >= end:
        yield start
        start -= abs(step)

def EgForLoop():
    for hv in RangeDown(2000,500,-500):
        print(hv)
    for hv in RangeUp(500,2000,500):
        print(hv)

def TakeClosest(myList,myNumber):
    """Given a list of integers, I want to find which number is the closest to a number x."""
    return min(myList, key=lambda x:abs(x-myNumber))



def Check_Staff_Directory(**kwargs):
    """
    Switchs to the staff directory
        Uses Fold
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("run",Check_run())
    
    scanIOC=kwargs["scanIOC"]
    run= kwargs["run"]
    
    directory = MDA_CurrentDirectory(scanIOC)
    current_run = MDA_CurrentRun(scanIOC)
    
    if directory.find('data_29idb') < 1 or current_run != run:
        print('You are not currently saving in the Staff directory and/or the desired run - REPLY "yes" to switch folder.\nThis will only work if the run directory already exists.\nOtherwise, you must open ipython as 29id to create a new run directory using:\n\tFolder_'+scanIOC+'(run,\'Staff\')')
        foo=input('\nAre you ready to switch to the '+run+' Staff directory? >')
        if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
            print('Switching directory...')
            if scanIOC=='ARPES':
                Folder_ARPES('Staff',mdaOnly=True,**kwargs)
            elif scanIOC=='Kappa':
                Folder_Kappa('Staff',create_only=False)
        else:
            print('\nFolder not set.')
    else:
        print('Staff directory OK.')
    directory = MDA_CurrentDirectory(scanIOC)
    print('\nCurrent directory: '+directory)

