from os import system
from os.path import join
from ast import literal_eval
from datetime import datetime
from epics import caget
from time import strftime, localtime, sleep


from apstools.utils import run_in_thread

@run_in_thread
def play_victory_song():
    playsound()


# playsound()  # waits until song is done
# play_victory_song()  # command line comes back _while_ song is playing


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



def prompt(question):
    """
    ask a question (e.g 'Are you sure you want to do this (Y or N)? >')
    return the answer
    """
    try:
        print(question)
        foo = input()
        return foo
    except KeyboardInterrupt as e:
        raise e
    except:
        return



# def read_dict(FileName,FilePath="/home/beams22/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/"):
#     with open(join(FilePath, FileName)) as f:
#         for c,line in enumerate(f.readlines()):
#             if line[0] == '=':
#                 lastdate=line[8:16]
#             lastline=line
#         mydict=literal_eval(lastline)
#     return mydict



def RangeUp(start,end,step):
    while start <= end:
        yield start
        start += abs(step)

def RangeDown(start,end,step):
    while start >= end:
        yield start
        start -= abs(step)

def TakeClosest(myList,myNumber):
    """Given a list of integers, I want to find which number is the closest to a number x."""
    return min(myList, key=lambda x:abs(x-myNumber))

def dateandtime():
    return strftime("%a %d %b %Y %H:%M:%S",localtime())

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
    sleep(timeToWait.total_seconds())
    print(dateandtime())

def WaitForPermission():
    """
    Monitors the ID permissions and waits for the ID to be in User Mode and then breaks
    Checks the status every 30 seconds
    """
    while True:
        ID_Access=caget("ID29:AccessSecurity.VAL")
        if (ID_Access!=0):
            print("Checking ID permission, please wait..."+dateandtime())
            sleep(30)
        else:
            print("ID now in user mode -"+dateandtime())
            break
        
def WaitForBeam():
    """
    Monitors the storage ring current and breaks when the ring current is above 60 mA
    Checks the status every 30 seconds
    """
    while True:
        SR=caget("S:SRcurrentAI.VAL")
        if (SR<60):
    #        print "No beam current, please wait..."+dateandtime()
            sleep(30)
        else:
            print("Beam is back -"+dateandtime())
            break


def today(which='default'):
    dt = datetime.datetime.today()
    today_year = dt.year
    today_month = dt.month
    today_day = dt.day
    if which == 'slash':
        today_str=("{:02d}/{:02d}/{:04d}".format(today_month,today_day,today_year))
    elif which == 'int':
        today_str=int(("{:04d}{:02d}{:02d}".format(today_year,today_month,today_day)))
    else: # 'default':
        today_str=("{:04d}{:02d}{:02d}".format(today_year,today_month,today_day))
    return today_str 
 