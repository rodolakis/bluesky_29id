__all__ = """
    energy_plan
    id_calc
""".split()

# TODO: Add slit3_set

from bluesky import plan_stubs as bps
import logging
from IEX_29id.devices.beamline_energy import mono, undulator, align_m3r #grt, mode?
from IEX_29id.plans.bp_slits import slitBL_set
import numpy.polynomial.polynomial as poly
from os.path import join
import ast





# TODO: Deal with m3r and allowed ranges



# TODO: hardcoded grt and mode!




def energy_plan(hv,c=1,m3r=False):
    """
    Sets the beamline energy: insertion device + mono + apertures.
    Use c < 1 to kill flux density.
    """
    # rbv = mono.energy.readback.value
    # grt= mono.grating_density.value
    # mode=undulator.actual_mode.get()   # why is value in this case not working? how to make that line a plan
    id_value=id_calc(1200,2,hv)
    if m3r: m=1
    else: m=0
    yield from bps.mv(undulator.energy,id_value)
    yield from bps.mv(mono.energy,hv)
    yield from slitBL_set(c2B=c)
    yield from bps.mv(align_m3r,m)
    yield from bps.sleep(30)
    
        
        
    # if m3r == True:
    #     if CheckBranch() == 'd':
    #         print('\nalign_m3r_epics()')
    #         try:
    #             align_m3r_epics()
    #             sleep(1)
    #             if caget('29id_m3r:RY_POS_SP') == -16.52:
    #                 align_m3r_epics()
    #         except:
    #             print('Unable to align; check camera settings.')
        
   
    

def id_calc(grt,mode,hv):    # Mode = state (0=RCP,1=LCP,2=V,3=H)
    """Calculate the ID SP for a given polarization mode and energy;
    with Mode = 0 (RCP),1 (LCP), 2 (V), 3 (H)"""
    if isinstance(grt,int): grt  = {1200:'MEG',2400:'HEG'}[grt]
    if isinstance(mode,str):mode = {'RCP':0,'LCP':1,'V':2,'H':3}[mode]
    try:
        K=id_coef(grt,mode,hv)
        #ID = K[0] + K[1]*hv**1 + K[2]*hv**2 + K[3]*hv**3 + K[4]*hv**4 + K[5]*hv**5
        ID=poly.polyval(hv,K)
    except KeyError:
        ID=0
        print('KeyError')
    return round(ID/1000,4)




def id_coef(grt,mode,hv):    # Mode = state (0=RCP,1=LCP,2=V,3=H); 
    
    """Return the ID coeff for a given polarization mode and energy;
    with Mode = 0 (RCP),1 (LCP), 2 (V), 3 (H).
    Current coefficient dictionary:
        /home/beams22/29IDUSER/Documents/User_Macros/Macros_29id/IEX_Dictionaries/Dict_IDCal.txt
    now:/home/beams3/RODOLAKIS/src/macros_29id/IEX_29id/dict/
   """
    print(grt,mode,hv)
    
    if isinstance(grt,int): grt  = {1200:'MEG',2400:'HEG'}[grt]
    if isinstance(mode,str):mode = {'RCP':0,'LCP':1,'V':2,'H':3}[mode]
    
    def read_dict(FileName,FilePath="/home/beams3/RODOLAKIS/src/macros_29id/IEX_29id/dict/"):
        with open(join(FilePath, FileName)) as f:
            for c,line in enumerate(f.readlines()):
                if line[0] == '=':
                    lastdate=line[8:16]
                lastline=line
            mydict=ast.literal_eval(lastline)
        return mydict

    
    def list_range(grt,mode,IDdict):  # extract the list of break pts for a given mode/grt 
        tmp_list=[]
        for item in (IDdict[grt][mode]):
            tmp_list.append(item[0])  
        return tmp_list


    def find_range(hv,range_list):         # returns the index for the corresponding range
        B = [x - hv for x in range_list]
        index = [i for (i, x) in enumerate(B) if x > 0]
        return(index[0])
    
    try:
        #FRPath = '/Users/fannysimoes/Box/6-Python/MyPython/Macros_29id/'   #   FR hardcoded
        ID_function=read_dict(FileName='Dict_IDCal.txt')
    
    except KeyError:
        print("Unable to read dictionary") 
        
    try:   
        Lrange = list_range(grt,mode,ID_function)
        Erange = find_range(hv,Lrange)
        K = ID_function[grt][mode][Erange][1]
        
    except KeyError:
        print("WARNING: PLease select one of the following:")
        print("        mode 0 = RCP")
        print("        mode 1 = LCP")
        print("        mode 2 = V")
        print("        mode 3 = H")
        
    return K


