from IEX_29id.devices.eps import Switch_Branch
from IEX_29id.devices.mono import Switch_Grating
from epics import caget, caput
from IEX_29id.utils.misc import prompt
from time import sleep
from IEX_29id.devices.eps import Open_DShutter, Open_BranchShutter
from IEX_29id.scans.beamline_plans import WireScan, CheckFlux

def centroid(t=None,q=1): 
    '''
    Return position of centroid, sigma, m3r:RY (mirror pitch)
    Optional argument t to set camera intergration time.
    '''
    if t is not None:
        caput('29id_ps6:cam1:AcquireTime',t)
    else:
        t=caget('29id_ps6:cam1:AcquireTime')
    position=  round(caget('29id_ps6:Stats1:CentroidX_RBV'),2)
    sigma=round(caget('29id_ps6:Stats1:SigmaX_RBV'),2)
    intensity=round(caget('29id_ps6:Stats1:CentroidTotal_RBV'),2)
    m3rRY=round(caget("29id_m3r:RY_MON"),4)
    if q != None:
        print('(position, sigma, total intensity, integration time (s), mirror pitch):')
    return position,sigma,intensity,t,m3rRY


def align_m3r(p=118,debug=False):

    def mvm3r_pitch_FR(x):
            if -16.53<x<-16.38:
                motor_pv="29id_m3r:RY_POS_SP"
                #print('... moving to '+str(x))
                caput(motor_pv,x)
                sleep(0.5)
                caput("29id_m3r:MOVE_CMD.PROC",1)
                sleep(1)
                #print('Positioned')
            else:
                print('Out of range')

    shutter=caget('PA:29ID:SDS_BLOCKING_BEAM.VAL')
    camera=caget('29id_ps6:cam1:Acquire',as_string=True)
    hv=caget('29idmono:ENERGY_SP')
    if shutter == 'ON':
        foo=prompt('Shutter D is closed, do you want to open it (Y or N)? >')
        if foo == 'Y'.lower() or foo == 'y' or foo == 'yes'.lower():
            Open_DShutter()
        else:
            print('Aborting...')
            return
    if camera == 'Done':
        caput('29id_ps6:cam1:Acquire','Acquire') 
     
    if hv < 2190:
        caput('29id_ps6:cam1:AcquireTime',0.001)
        caput('29id_ps6:Stats1:CentroidThreshold',7)
    else:
        caput('29id_ps6:cam1:AcquireTime',0.03)
        caput('29id_ps6:Stats1:CentroidThreshold',7)
    sleep(1)    
    intensity=caget('29id_ps6:Stats1:CentroidTotal_RBV')
    if intensity < 10000:
        print('Count too low. Please adjust camera settings')
    else:   
        print('Starting...')
        mvm3r_pitch_FR(-16.52)
        position = centroid(q=None)[0]
        max_pitch=-16.39
        #print('position = '+str(position))
        while position < p:
            position = centroid(q=None)[0]
            if position < p-10:
                pitch = caget('29id_m3r:RY_POS_SP')
                mvm3r_pitch_FR(min(pitch + 0.005,max_pitch))
                #print(centroid(q=None)[4])
                position = centroid(q=None)[0]
                #print('position = '+str(position))
            elif  p-10<= position:
                pitch = caget('29id_m3r:RY_POS_SP')
                mvm3r_pitch_FR(min(pitch + 0.001,max_pitch))
                #print(centroid(q=None)[4])
                position = centroid(q=None)[0]
                #print('position = '+str(position))
        print('Done')
        print(centroid())
        print('\n')


def CheckM0M1(scanIOC='ARPES',hv=500,stay=None,wire=None,**kwargs): #JM added energy parameter
    """
    Prints Flux in C-branch
    stay = 'yes' => Leaves diagnostics in the beam
    wire ='yes'=> Does wire scans to determine M0M1 alignment
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details
    """
    Switch_Branch('c')
    Switch_Grating('HEG')
    print("\nFlux at hv=500 as off Feb 2019:  ~3.3e-06 A = ~1.5e+11 ph/s")
    Open_BranchShutter()
    CheckFlux(hv=hv,stay=stay)
    if wire is not None:
        WireScan('H',scanIOC,**kwargs)
        WireScan('V',scanIOC,**kwargs)


def Move_M3R(which,Position,q=None):    #motor = "TX","TY","TZ","RX","RY","RZ"
    """
        \"TX\" = lateral                 \"RX\" = Yaw
        \"TY\" = vertical                \"RY\" = Pitch
        \"TZ\" = longitudinal            \"RZ\" = Roll
    """
    motor_pv="29id_m3r:"+which+"_POS_SP"
    caput(motor_pv,Position)
    sleep(2)
    caput("29id_m3r:MOVE_CMD.PROC",1)
    sleep(2)
    while caget("29id_m3r:SYSTEM_STS")==0:
        sleep(.5)
    if q is not None:
        m3=caget('29id_m3r:'+which+'_MON')
        print('\nM3R:{} = {:.4f}'.format(which,m3))

def M3R_Table(branch,motor):   # WARNING: branch_pv uses: D => (Tx <= 0) and (Ry < 0) - Make sure this remains true or change it
    M3R_Table={}
    M3R_Table["C"] = {'scanIOC':'ARPES',  "TX":10,     "TY":0, "TZ":0, "RX":0,      "RY":0,       "RZ":0}
    M3R_Table["D"] = {'scanIOC':'Kappa',  "TX":-2.5,"TY":0, "TZ":0, "RX":-13.955,"RY":-16.450, "RZ":-6} # Optimized for MEG @ 500 eV on 2/29/def start
    M3R_Table["E"] = {'scanIOC':'RSoXS',  "TX":-2.000,"TY":0, "TZ":0, "RX":-13.960,"RY":-16.614, "RZ":-7.500}     #2018_3-- JM changed for RSoXS alignment max diode current
    try:
        position=M3R_Table[branch][motor]
    except KeyError:
        print("WARNING: Not a valid MIR position - check spelling!")
        position=0
    return position

############# WARNING: when changing table, make sure the string sequence below is still relevant:


def M0M1_SP(Run,Mirror,Go='no'):
    """
    put values from a given run as defined by M0M1_Table as the set points
     you will need to push the Move button
    """
    MirrorPos=M0M1_Table(Run,Mirror).split('/')
    Motor=['TX','TY','TZ','RX','RY','RZ']
    for i in range(len(Motor)):
        PV="29id_m"+str(Mirror)+":"+Motor[i]+"_POS_SP"
        Val=MirrorPos[i]#float(MirrorPos[i])
        print(PV+" = "+Val)
        caput(PV,Val)
    sleep(0.5)
    if Go == 'yes':
        caput('29id_m'+str(Mirror)+':MOVE_CMD.PROC',0,wait=True,timeout=18000)
    else:
        print(" caput(\'29id_m"+str(Mirror)+":MOVE_CMD.PROC\',0)")


def M0M1_Table(Run,Mirror):
    """
    Prints the positions TX / TY / TZ / RX / RY / RZ for either Mirror = 0 or 1 (M0 or M1) for the specified Run
    Run='default' give a reasonable starting position after homing
    M0M1_SP() will put those values as the set points, you will need to push the Move button
    """
    M0M1_Pos={}
    M0M1_Pos['default']={0:'-0.400/-22.5/0/0/0.000/0.0000',1:'0.400/-21.5/0/0/8.400/2.800'}
    M0M1_Pos['2019_1']= {0:'0.3010/-22.5/0/0/-0.151/0.0393',1:'1.449/-21.5/0/0/8.339/2.700'}
    M0M1_Pos['2019_2']= {0:'-0.400/-22.5/0/0/ 0.000/0.000',1:'0.400 /-21.5/0/0/8.436/3.000'}
    return M0M1_Pos[Run][Mirror]
