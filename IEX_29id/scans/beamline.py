from time import sleep
from epics import caget, caput

def CheckFlux(hv=500,mode='RCP',stay=None):
    Switch_IDMode(mode)
    energy(hv)
    branch=CheckBranch()
    SR=round(caget("S:SRcurrentAI.VAL"),2)
    if branch == "c":
        current_slit=caget('29idb:Slit3CFit.A')
        diodeC_plan('In')
        diode=caget('29idb:ca15:read')
    elif branch == "d":
        current_slit=caget('29idb:Slit4Vsize.VAL')
        diodeD_plan("In")
        diode=caget('29idb:ca14:read')
    SetExitSlit(50)
    flux=ca2flux(diode)
    print("\n----- Current on diode   : %.3e" % diode, "A")
    print("----- Corresponding flux: %.3e" % flux, "ph/s \n")
    print("----- Storage ring current: %.2f" % SR, "mA")
    if stay is None:
        all_diag_out()
    SetExitSlit(current_slit)









def WireScan(which,scanIOC=None,diag='In',**kwargs):
    """
    Scans the wires located just downstream of M0/M1, 
         which = 'H' for the horizontal, typically CA2
         which = 'V' for the vertical, typically CA3
    diag ='In' -> AllDiagIn(), otherwise you have to put any diagnostics in by hand
    Logging is automatic: use **kwargs or the optional logging arguments see scanlog() for details    
    """
    
    if scanIOC is None:
        scanIOC=BL_ioc()
    if diag == 'In':
        AllDiagIn()
    if which=='H':
        print("\n================== H wire scan (29idb:ca3):")
        Scan_FillIn("29idb:m1.VAL","29idb:m1.RBV",scanIOC,1,-13,-27,-0.25)

    elif which=='V':
        print("\n================== V wire scan (29idb:ca2):")
        Scan_FillIn("29idb:m2.VAL","29idb:m2.RBV",scanIOC,1,-17,-30,-0.25)
    Scan_Go(scanIOC,scanDIM=1,**kwargs)


def Notes_from_20191212():
    print(""" looking at diode 3 in scattering chamber, open 3D all the way (2000)
        WARNING: 10% energy detune is enough to see the 2 lobes with 2B but not for 1A => 20% 
        Red shifted  (485eV) = edges give center of the grating
        Blue shifted (510eV) = gaussian center gives center of the beam
        => we want the slit centered on the grating center and the beam centered on the slits/grating
        => 5 urad down = 1 mm negative motion on 2B-V with HEG""")


def Procedure_Alignment_M1():
    print("""\n-Start with a very red shifted line cut to localize the edges of the grating:
                Set_IDraw(510)
                mono(485)
                Scan_NarrowSlit('2V',[0.25,-8,8,0.5])
                Scan_NarrowSlit('2H',[0.25,-4,4,0.5])
    => Verticaly: The edges/center of the grating define the center of 2V 
    => Horizontaly: The edges are defined by the aperture upstream. 
        As long as the beam makes it through the pipe to the next mirror, we are good. 
        Each M1 pitch will have its own slit-2H zero
        It can be a good idea to check that GRT or M2 translation does not change anything.
\n-Once the slits are centered on the grating, center resonant beam on the grating (zero slit):
                Get_Mirror(1)   # to get current values
                for roll in RangeUp(3,4,0.2):
                    print('\\n')
                    Move_M1('RZ',roll)
                    sleep(5)
                    Scan_MonoVsSlit('2V',[0.25,-0.5,0.5,0.25],[490,530,2])
                for pitch in RangeUp(8.5,8.7,0.05):
                    print('\\nMove_M1('RY',pitch)')
                    Move_M1('RY',pitch)
                    sleep(5)
                    Scan_MonoVsSlit('2H',[0.25,-0.5,0.5,0.25],[490,530,2])
    => The resonant beam is the slit value for the most blue shifted curve.
    
    WARNING: It is more accurate (and easier) to compare the leading edge of the ID peak 
    than trying to look at the perpendicular direction (slit line cut) because of the 
    asymetry in the beam intensity (uneven carbon strip along the grating?)
""")


    # 2017_3 - HEG after opitmization:  mba_b_0241-0244
    # 2018_1 - HEG before opitmization: mba_b_0005-0008

def StartOfTheWeek(GRT,branch,wait,**kwargs):
    """
    This should be run every at the start of every week; 50 min total.
    Switch to C-branch,.
    If wait='yes', wait for next day a 8:05.
    
    kwargs defaults:
        run = None: used today's date to set run appropriatetly 
        repeat = False: sets everything: switches branch, sets BL_Mode to Staff, resets scan/CAs/mono
        scanType = ['slit1','wire','flux','monoVslit']
        sound = False; no sounds
              = True => plays sound after Slit1A scans and when script is complete
    }
    steering out => move beam more positive (10 urad ~ 0.25 mm)
    steering up  => move beam more positive (10 urad ~ 0.25 mm)
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault('repeat',False)
    kwargs.setdefault('run',Check_run())
    kwargs.setdefault('scanType',['slit1','wire','flux','monoVslit'])
    kwargs.setdefault('sound',False)
    
    for scan in kwargs['scanType']: 
        if scan not in ['slit1','wire','flux','monoVslit']:
            print(scan+" is not a valid scan scanType=['slit1','wire','flux','monoVslit']")
            return
    
    scanIOC=kwargs['scanIOC']
    run=kwargs['run']
    
    if branch == 'c': 
        scanIOC='ARPES'
        CA_Autoscale('b',15,'Off',7) #turn off autoscaling on CA15
    elif branch == 'd': 
        scanIOC='Kappa'
        
    print("\n\n================== Sets Directory:")
    Check_Staff_Directory(**kwargs)
    FileName='StartOfTheWeek_log.txt'
    logname_set(FileName,scanIOC)
    FirstScan=None
    

    #Stuff that doesn't need beam & does not need to be run if repeating SoTW:

    print("\n\n================== Sets Beamline & Scans:")
    Switch_Grating(GRT)
    if not kwargs['repeat']:    
        Switch_Branch(branch)
        BL_Mode_Set('Staff')
        Reset_Scan(BL_ioc()); Reset_CA_all(); Reset_Mono_Limits()
        Get_All()
    
    shutter=caget('PA:29ID:S'+branch.upper()+'S_BLOCKING_BEAM.VAL')
    if shutter == 'ON':
        foo=input_d('Shutter '+branch.upper()+' is closed, do you want to open it (Y or N)? >')
        if foo == 'Y'.lower() or foo == 'y' or foo == 'yes'.lower():
            Open_BranchShutter()
        else:
            print('Aborting...')
            return

    
    all_diag_out(keep_diode_in=True)

    if wait =='Y' or wait == 'y' or wait == 'yes'or wait == 'YES' or wait == True:
        t = datetime.datetime.today()
        if 0 <= t.hour <= 8:
            WaitForIt(0,8,5)
        else:    
            WaitForIt(1,8,5)

    print("\n\n================== Start ID:")
    ID_OnOff=caget('ID29:Main_on_off.VAL')
    if ID_OnOff==1:  # 0 = On, 1 = Off
        ID_Start('RCP')
    else:
        polarization('RCP')



    if not kwargs['repeat']:    
        logprint("\n\n================== Start Of The Week @ "+today('slash')+':\n',FileName=FileName)

    ###### Scan front-end slit center:
    
    if 'slit1' in kwargs['scanType']:
        print("\n\n================== Slit 1A scans:")
        SetID_Raw(2000)
        Scan_SlitCenter('1H',-3,3,0.1,comment='Slit center - 1H')
        FirstScan=MDA_GetLastFileNum()
        Scan_SlitCenter('1V',-3,3,0.1,comment='Slit center - 1V')
        SetSlit1A(4.5,4.5,0,0)
        if kwargs['sound']:
            playsound()

    ###### Wire scans: 
    if 'wire' in kwargs['scanType']:
        SetID_Raw(2000)
        SetSlit1A(4.5,4.5,0,0)
        WireScan('H',comment='Wire scan - H')     # by default puts all meshes in + DiodeC
        WireScan('V',comment='Wire scan - V')

    ###### Mono/slit scans: 
    if 'monoVslit' in kwargs['scanType']:
        if GRT=="HEG":
            slit(300)
        else:
            slit(200)
        print("\n\n================== Mono/slit scans:")
        mono(500)
        SetSlit_BL()
        all_diag_out(keep_diode_in=True)
        SetID_Raw(500)
        Scan_MonoVsSlit('2V',[0.25,-2,2,0.5],[475,515,2],comment='Mono/Slit - 2V')    #10min
        Scan_MonoVsSlit('2H',[0.25,-2,2,0.5],[475,515,2],comment='Mono/Slit - 2H')    #10min
        Scan_MonoVsSlit('1V',[0.5,-0.75,0.75,0.25],[475,515,2],comment='Mono/Slit - 1V')    #10min
        Scan_MonoVsSlit('1H',[0.5,-0.75,0.75,0.25],[475,515,2],comment='Mono/Slit - 1H')    #10min
    
    ###### Check flux: 
    if 'flux' in kwargs['scanType']:
        print("\n\n================== Check Flux:")
        CheckFlux(stay='y')
        slit(50)
        energy(500)
        scanhv(475,525,1,comment='Mono Scan @ 500eV')
        all_diag_out()

    print("\n\n================== All done:")
    print("\nDon't forget to put back the user folder !!!!")
    
    ###### Plotting instructions and return first scan number 
    if FirstScan is not None:
        logprint(comment="\nFirstScan = "+str(FirstScan))
        print('plot_StartOfTheWeek("'+branch+'",'+str(FirstScan)+')' )
    print('\nREMEMBER to update slit center using:     update_slit_dict()')
    
    if kwargs['sound']:
        playsound()
        
    return FirstScan
    

  