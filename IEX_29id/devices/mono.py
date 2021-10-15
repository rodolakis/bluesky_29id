from epics import caget, caput
from time import sleep
from IEX_29id.devices.energy import SetSlit_BL
from IEX_29id.utils.misc import dateandtime, SetMono, Open_MainShutter
from IEX_29id.devices.eps import Close_MainShutter


def Reset_Mono_Limits():
#    caput("29idmono_GRT_TYPE_SP.ONST", 'MEG_PA')
#    caput("29idmono_GRT_TYPE_SP.TWST", 'HEG_JY')
#    caput("29idmono_GRT_TYPE_SP.THST", 'MEG_JY')
    caput("29idmono:ENERGY_SP.DRVL",200)
    caput("29idmono:ENERGY_SP.LOW",200)
    caput("29idmono:ENERGY_SP.LOLO",200)
    caput("29idmono:ENERGY_SP.LOPR",200)
    print("Mono limits have been reset.")


def Check_Grating():
    GRTd=caget("29idmono:GRT_DENSITY")
    if GRTd == 1200:
        GRT = "MEG"
    elif GRTd == 2400:
        GRT = "HEG"
    return GRT



def Move_GRT(which):
    MonoeV=round(caget("29idmono:ENERGY_MON"),1)
    Current_Shutter=caget("EPS:29:ID:SS2:POSITION")
    if Current_Shutter!=1:
        Close_MainShutter()
        while caget("EPS:29:ID:SS2:POSITION")!=1:
               sleep(0.5)
    if which == "Imp_MEG":
           caput("29idmonoGRT_TYPE_SP",1,wait=True,timeout=18000)          # MEG Imp
           caput("29idmonoGRT:X_DCPL_CALC.PROC",1,wait=True,timeout=18000)
           while caget("29idmonoGRT:X.RBV")!=3.872:
               sleep(0.5)
    elif which == "HEG":
           caput("29idmonoGRT_TYPE_SP",2,wait=True,timeout=18000)          # HEG
           caput("29idmonoGRT:X_DCPL_CALC.PROC",1,wait=True,timeout=18000)
           while caget("29idmonoGRT:X.RBV")!=68.000:
               sleep(0.5)
    elif which == "MEG":
           caput("29idmonoGRT_TYPE_SP",3,wait=True,timeout=18000)          # MEG
           caput("29idmonoGRT:X_DCPL_CALC.PROC",1,wait=True,timeout=18000)
           while caget("29idmonoGRT:X.RBV")!=130.624:
               sleep(0.5)
    SetMono(MonoeV)
    if Current_Shutter!=1:
        Open_MainShutter()
        while caget("EPS:29:ID:PS2:POSITION")!=2:
               sleep(0.5)
    print("Mono Grating:",which)

def Switch_Grating(which):
    if which in ["HEG","MEG","Imp_MEG"]:
        print("\n")
        Actual_GRT=caget('29idmonoGRT_TYPE_MON')
        if which == "HEG":
            if Actual_GRT != 2:
                print("Switching grating, please wait...")
                caput("29idmonoGRT_TYPE_SP",2,wait=True,timeout=18000)         # HEG
                caput("29idb:gr:move",1,wait=True,timeout=18000)
                sleep(20)
                Current_GRT=caget('29idmonoGRT_TYPE_MON')
                if (Current_GRT!=2):
                    print("Failed - Switching grating again...")
                    Move_GRT(which)
                    SetSlit_BL()
                else:
                    print(dateandtime()," -  Current mono grating: HEG")
            else:
                print(dateandtime()," -  Current mono grating: HEG")
        elif which == "Imp_MEG":
#            print "Old MEG."
            if Actual_GRT != 1:
                print("Switching grating, please wait...")
                caput("29idmonoGRT_TYPE_SP",1,wait=True,timeout=18000)         # MEG
                caput("29idb:gr:move",1,wait=True,timeout=18000)
                sleep(2)
                Current_GRT=caget('29idmonoGRT_TYPE_MON')
                if (Current_GRT!=1):
                    print("Failed - Switching grating again...")
                    Move_GRT(which)
                    SetSlit_BL()
                else:
                    print(dateandtime()," -  Current mono grating: MEG Imp")
            else:
                print(dateandtime()," -  Current mono grating: MEG Imp")
        elif which == "MEG":  #JY MEG
#            print "JY MEG"
            if Actual_GRT != 3:
                print("Switching grating, please wait...")
                Move_GRT(which)
                #caput("29idb:gr:move",1,wait=True,timeout=18000)     missing the 3rd slot
                sleep(2)
                Current_GRT=caget('29idmonoGRT_TYPE_MON')
                if (Current_GRT!=3):
                    print("Failed - Switching grating again...")
                    Move_GRT(which)
                    SetSlit_BL()
                else:
                    print(dateandtime()," -  Current mono grating: MEG")
                Open_MainShutter()
            else:
                print(dateandtime()," -  Current mono grating: MEG")
        SetSlit_BL()
    else:
        print("WARNING: Not a valid grating name, please select one of the following:")
        print(" \"HEG\" for high resolution, \"MEG_JY\" for high flux \"MEG\" is soon to be obsolete ")


def grating(which):
    """
    Change mono grating: which = \"HEG\", \"MEG\"
        HEG = high resolution, low flux
        MEG = medium resolution, high flux
    """
    Switch_Grating(which)