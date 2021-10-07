from IEX_29id.devices.energy import Switch_IDMode



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
