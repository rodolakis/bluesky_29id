from IEX_29id.devices.energy import Switch_IDMode, Open_MainShutter, Check_Grating, ID_Calc, SetRange, SetID_keV_pV
from epics import caput,caget, poly
from time import sleep
from IEX_29id.utils.exp import WaitForPermission, Check_MainShutter
from IEX_29id.utils.misc import dateandtime


def ID_Calc(grt,mode,hv):    # Mode = state (0=RCP,1=LCP,2=V,3=H)
    """Calculate the ID SP for a given polarization mode and energy;
    with Mode = 0 (RCP),1 (LCP), 2 (V), 3 (H)"""
    if type(mode)== str:
        mode={'RCP':0,'LCP':1,'V':2,'H':3}[mode]
    try:
        K=ID_Coef(grt,mode,hv)
        #ID = K[0] + K[1]*hv**1 + K[2]*hv**2 + K[3]*hv**3 + K[4]*hv**4 + K[5]*hv**5
        ID=poly.polyval(hv,K)
    except KeyError:
        print("WARNING: PLease select one of the following:")
        print("        mode 0 = RCP")
        print("        mode 1 = LCP")
        print("        mode 2 = V")
        print("        mode 3 = H")
        ID=caget("ID29:EnergySeteV")
    return round(ID,1)


def ID_State2Mode(which,mode):
    ID_State2Mode={}
    ID_State2Mode["Mode"]  = {"RCP":0, "LCP":1, "V":2, "H":3, "HN":4}
    ID_State2Mode["State"] = {0:"RCP", 1:"LCP", 2:"V", 3:"H", 4:"HN"}
    try:
        ID=ID_State2Mode[which][mode]
    except KeyError:
        print("WARNING: Not a valid ID mode!")
    return ID

#replace with    ?
#   ID_Mode_list=['RCP','LCP','V','H','HN']
#   ID_Mode=ID_Mode_list[caget("ID29:ActualMode")]

def polarization(which):
    """
    Change beam polarization: which = \"H\", \"V\", \"RCP\" or \"LCP\"
    """
    Switch_IDMode(which)

def ID_Coef(grt,mode,hv):    # Mode = state (0=RCP,1=LCP,2=V,3=H); 
    
    """Return the ID coeff for a given polarization mode and energy;
    with Mode = 0 (RCP),1 (LCP), 2 (V), 3 (H).
    Current coefficient dictionary:
        /home/beams22/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/Dict_IDCal.txt
    """
    def ListRange(grt,mode,IDdict):  # extract the list of break pts for a given mode/grt 
        tmp_list=[]
        for item in (IDdict[grt][mode]):
            tmp_list.append(item[0])  
        return tmp_list


    def FindRange(hv,range_list):         # returns the index for the corresponding range
        B = [x - hv for x in range_list]
        index = [i for (i, x) in enumerate(B) if x > 0]
        return(index[0])
    
    try:
        #FRPath = '/Users/fannysimoes/Box/6-Python/MyPython/Macros_29id/'   #   FR hardcoded
        ID_function=read_dict(FileName='Dict_IDCal.txt')
    
    except KeyError:
        print("Unable to read dictionary") 
        
    try:   
        Lrange = ListRange(grt,mode,ID_function)
        Erange = FindRange(hv,Lrange)
        K = ID_function[grt][mode][Erange][1]
        
    except KeyError:
        print("WARNING: PLease select one of the following:")
        print("        mode 0 = RCP")
        print("        mode 1 = LCP")
        print("        mode 2 = V")
        print("        mode 3 = H")
        
    return K




def ID_Range():      # mode = state (0=RCP,1=LCP,2=V,3=H)
    Mode=caget("ID29:ActualMode")
    GRT=caget("29idmono:GRT_DENSITY")
    ID_min=[400,400,440,250,250]
    ID_max=3800
    hv_min=[390,390,430,245,245]
    if GRT == 2400:
        hv_max=2000
    elif GRT == 1200:
        hv_max=3000
    return ID_min[Mode],hv_min[Mode],hv_max,ID_max

def ID_Ready(q=None):
    while True:
        checkready=caget("ID29:feedback.VAL")
        checkbusy=caget("ID29:BusyRecord")
        if (checkready!="Ready")|(checkbusy==1):
            sleep(2)
        else:
            break
    if q is None:
        print("ID Ready")

def ID_Stop():
    WaitForPermission()
    caput("ID29:Main_on_off.VAL",1,wait=True,timeout=18000)

def Check_IDMode(which):
    if which in ["RCP","LCP","V","H"]:
        Mode=ID_State2Mode("Mode",which)
        Check_MainShutter()
        ActualMode=caget("ID29:ActualMode")
        if Mode != ActualMode:
            print("Switching ID mode, please wait...")
            caput("ID29:DesiredMode.VAL",Mode,wait=True,timeout=18000)     # RCP
            ID_Ready()
    else:
        print("WARNING: Not a valid polarization mode, please select one of the following:")
        print(" \"RCP\", \"LCP\", \"H\", \"V\" ")

def Switch_IDMode(which):
    "Change ID polarization; which = \"H\", \"V\", \"RCP\" or \"LCP\""
    GRT=caget("29idmono:GRT_DENSITY")
    if which in ["RCP","LCP","V","H"]:
        Mode=ID_State2Mode("Mode",which)
        Check_MainShutter()
        ActualMode=caget("ID29:ActualMode")
        if Mode != ActualMode:
            print("Turning ID off...")
            ID_Stop()
            
            sleep(10)
            caput("ID29:EnergySet.VAL",3.8)
            caput("ID29:Main_on_off.VAL",0,wait=True,timeout=18000)
            print("Switching ID mode, please wait...")
            caput("ID29:DesiredMode.VAL",Mode,wait=True,timeout=18000)     # RCP
            ID_Ready()
        print("ID Mode:",which)
    else:
        print("WARNING: Not a valid polarization mode, please select one of the following:")
        print(" \"RCP\", \"LCP\", \"H\", \"V\" ")


def SetID_Raw(hv):
    "Sets the ID set point to a specific value (hv(eV)) which will not likely be optimum"
    Check_MainShutter()
    Mode=caget("ID29:ActualMode")
    Mode_RBV=("state",Mode)
    ID_min=ID_Range()[0]
    ID_max=ID_Range()[3]
    ID_SP=min(max(hv,ID_min),ID_max)*1.0
    if hv < ID_min or hv > ID_max:
        print("\nWARNING:Set point out of BL energy range !!!")
        print("Please select a different energy.")
    else:
        ID_SP_RBV=round(caget("ID29:EnergySet.VAL"),3)*1000
        if ID_SP == ID_SP_RBV:                # checks if ID is already at the SP energy
            ID_RBV=caget("ID29:EnergyRBV")
            print("ID SET : "+"%.1f" % ID_SP, "eV")
            #print "\nID SET : "+"%.1f" % ID_SP, "eV"
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            print(caget('ID29:TableDirection',as_string=True))
        else:
            caput("ID29:EnergyScanSet.VAL",ID_SP/1000,wait=True,timeout=18000)
            sleep(1)
            caput("ID29:EnergyScanSet.VAL",(ID_SP+0.001)/1000,wait=True,timeout=18000)
            caput('ID29:StartRamp.VAL',1)
            #caput("ID29:EnergyScanSeteV",ID_SP,wait=True,timeout=18000)
            ID_Ready(q='q')
            print("\nID SET : "+"%.1f" % ID_SP, "eV")
            sleep(5)
            ID_RBV=caget("ID29:EnergyRBV")
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            ID_DIF=abs(ID_RBV-ID_SP)
            ID_BW=ID_SP*0.095
            if ID_DIF>ID_BW:
                sleep(20)
                ID_RBV=caget("ID29:EnergyRBV")
                print("\nID RBV : "+"%.1f" % ID_RBV, "eV")
                ID_DIF=abs(ID_RBV-ID_SP)
                if ID_DIF>ID_BW:
                    ID_Restart()
                    SetID_Raw(hv)
            print(caget('ID29:TableDirection',as_string=True))

def ID_Restart():
    Mode=caget("ID29:ActualMode")
    print("Restarting ID", dateandtime())
    caput("ID29:Main_on_off.VAL",1,wait=True,timeout=18000)
    sleep(10)
    while True:
        RBV=caget("ID29:Energy.VAL")
        checkready=caget("ID29:feedback.VAL")
        checkbusy=caget("ID29:BusyRecord")
        if (checkready!="Ready") or (RBV < 3.7):
            sleep(2)
        elif ((checkready=="Ready") and (RBV > 3.7)) and (checkbusy=="Busy"):
            caput("ID29:Busy.VAL",0)
        else:
            break
    sleep(10)
    caput("ID29:EnergySet.VAL",3.8)
    caput("ID29:Main_on_off.VAL",0,wait=True,timeout=18000)
    ID_Ready()
    caput("ID29:DesiredMode.VAL",Mode,wait=True,timeout=18000)
    sleep(10)

    print("ID is back ON", dateandtime())

def Switch_IDQP(energy,mode,QP):
    QP=max(70,QP)
    ID_Stop()
    caput("ID29:QuasiRatioIn.C",QP)
    ID_Start(mode)
    sleep(15)
    SetID_Raw(energy)
    Byq=caget("ID29:ByqRdbk")
    Vcoil=caget("ID29:ByRdbk.VAL")
    ratio=Byq/Vcoil
    ratio_RBV=caget("ID29:QuasiRatio.RVAL")
    print("QP ratio =", round(ratio,3)*100,"%")
    print("QP RBV   =", ratio_RBV,"%")
    sleep(15)



def ID_Start(Mode):
    "Starts ID with a specific polarization; Mode = \"H\", \"V\", \"RCP\" or \"LCP\""
    WaitForPermission()
    print("Starting ID  -  "+dateandtime())
    caput("ID29:EnergySet.VAL",3.8)
    caput("ID29:Main_on_off.VAL",0,wait=True,timeout=18000)
    ID_Ready()
    Switch_IDMode(Mode)
    while True:
        SS1=caget("EPS:29:ID:SS1:POSITION")
        SS2=caget("EPS:29:ID:SS2:POSITION")
        PS2=caget("EPS:29:ID:PS2:POSITION")
        check=SS1*SS2*PS2
        if (check!=8):
            print("MAIN SHUTTER CLOSED !!!" , dateandtime())
            Open_MainShutter()
            sleep(60)
        else:
            print("Shutter is now open" , dateandtime())
            break




def SetID(hv):
    "Sets optimum ID set point for hv(eV) (max intensity)"
    Check_MainShutter()
    GRT=Check_Grating()
    hv_SP=round(SetRange(hv),3)
    ID_min=ID_Range()[0]
    if hv_SP == round(hv,2) and hv_SP < 3001:
        Mode=caget("ID29:ActualMode")
        ID_SP=max(ID_Calc(GRT,Mode,hv_SP),ID_min)
        ID_SP_RBV=round(caget("ID29:EnergySet.VAL"),4)*1000
        if ID_SP == ID_SP_RBV:                    # compare ID (eV)SP to the (keV)SP energy
            ID_RBV=caget("ID29:EnergyRBV")
            print("\nID SET : "+"%.1f" % ID_SP, "eV")
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            print(caget('ID29:TableDirection',as_string=True))
        else:
            caput("ID29:EnergyScanSeteV",ID_SP,wait=True,timeout=18000)
            sleep(1)
            caput("ID29:EnergyScanSeteV",ID_SP+0.001,wait=True,timeout=18000)

            ID_Ready()
            print("\nID SET : "+"%.1f" % ID_SP, "eV")
            sleep(5)
            ID_RBV=caget("ID29:EnergyRBV")
            print("ID RBV : "+"%.1f" % ID_RBV, "eV")
            ID_DIF=abs(ID_RBV-ID_SP)
            ID_BW=ID_SP*0.095
            if ID_DIF>ID_BW:
                sleep(20)
                ID_RBV=caget("ID29:EnergyRBV")
                print("ID RBV : "+"%.1f" % ID_RBV, "eV")
                ID_DIF=abs(ID_RBV-ID_SP)
                if ID_DIF>ID_BW:
                    ID_Restart()
                    SetID_keV_pV(hv_SP)
            print(caget('ID29:TableDirection',as_string=True))
#    elif  2450 < hv_SP < 3000:
#        print("Not calibrated above 2450 eV. ID set point needs to be determined manually.")
    else:
        print("Please select a different energy.")

def SetID_keV_pV(hv_eV):
    "Sets optimum ID set point for hv(eV) (max intensity) using KeV PVs"
    Check_MainShutter()
    hv_SP=SetRange(hv_eV)                # check hv range
    GRT=Check_Grating()
    if hv_SP == hv_eV:
        Mode=caget("ID29:ActualMode")
        ID_SP=ID_Calc(GRT,Mode,hv_SP)/1000.0        # ID_SP in keV
        ID_SP_RBV=round(caget("ID29:EnergySet.VAL"),3)    # ID_SP_RBV in keV
        if ID_SP == ID_SP_RBV:                # checks if ID is already at the SP energy
            ID_RBV=caget("ID29:Energy.VAL")
            print("\nID SET : "+"%.3f" % ID_SP, "keV")
            print("ID RBV : "+"%.3f" % ID_RBV, "keV")
            print(caget('ID29:TableDirection',as_string=True))
        else:
            caput("ID29:EnergyScanSet",ID_SP,wait=True,timeout=18000)
            sleep(1)
            caput("ID29:EnergyScanSet",ID_SP+0.0001,wait=True,timeout=18000)
        
            ID_Ready()
            print("\nID SET : "+"%.3f" % ID_SP, "keV")
            sleep(5)
            ID_RBV=caget("ID29:Energy.VAL")
            print("ID RBV : "+"%.3f" % ID_RBV, "keV")
            ID_DIF=abs(ID_RBV-ID_SP)
            ID_BW=ID_SP*0.095
            if ID_DIF > ID_BW:
                sleep(20)
                ID_RBV=caget("ID29:Energy.VAL")
                print("\nID RBV : "+"%.3f" % ID_RBV, "keV")
                ID_DIF=abs(ID_RBV-ID_SP)
                if ID_DIF > ID_BW:
                    ID_Restart()
                    SetID_keV_pV(hv_eV)
            print(caget('ID29:TableDirection',as_string=True))
    else:
        print("Please select a different energy.")
