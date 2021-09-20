def Reset_Scan(scanIOC,scanDIM=1,**kwargs):
    """
    Reset scan record; the current IOC is defined by BL_ioc() (i.e. mirror position).
    kwargs:
        scaler='y', for Kappa IOC only, ARPES ignors this keyword
        detTrig=2, for ARPES/Kappa IOC, used to clear SES/MPA trigger
        
    """

    kwargs.setdefault("scaler",'y')
    scaler=kwargs['scaler']
    
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    print("\nResetting "+pv)
    #Clear Scan Settings
    Reset_Scan_Settings(scanIOC,scanDIM)    # Reset scan settings to default: ABSOLUTE, STAY, 0.05/0.1 positioner/detector settling time
    #Setting Detectors
    Detector_Default(scanIOC,scanDIM)
    #Clearing the Detector Triggers
    Clear_Scan_Triggers(scanIOC,scanDIM)
    
    if scanIOC == 'ARPES':
        caput(pv+".T1PV",Detector_Triggers_StrSeq(scanIOC))
        print("\nDetector triggered:", Detector_List(scanIOC))
        
    if scanIOC == 'Kappa':
        caput('29idKappa:UBmatrix',[0,0,0,0,0,0,0,0,0])
        caput('29idKappa:UBsample','')
        caput('29idKappa:UBlattice',[0,0,0,0,0,0])
        caput('29idKappa:UBenergy',0)
        caput('29idKappa:UBlambda',0)
        if scaler == 'y':
            caput(pv+".T1PV",'29idMZ0:scaler1.CNT')
            caput('29idMZ0:scaler1.TP',0.1)
            print('Kappa scalers are triggered. Counting time set to 0.1s')
            #Reset_CA_all(); Reset_MonoMPA_ROI_Trigger()
        else:
            caput(pv+".T1PV",Detector_Triggers_StrSeq(scanIOC))
            print('Kappa scalers are NOT triggered. Using Current Amplifiers (CA)')
            print("\nDetector triggered:", Detector_List(scanIOC))
#     if scanIOC=='Kappa' and scaler is not None:
#         print('\nDo you want to use the scalers as detector trigger? (Note to self: to be modified  (FR))>')
#         foo = input()
#         if foo in ['yes','y','Y','YES']:
#             caput(pv+".T1PV",'29idMZ0:scaler1.CNT')
#             caput('29idMZ0:scaler1.TP',0.1)
#             print('Scalers added as trigger 2')
#             print('Counting time set to 0.1s')
#     else:
#         print('\nScalers not triggered. To trigger use: \n\n       Reset_Scan(\'Kappa\',scaler=\'y\')')
    caput(pv+".BSPV",BeforeScan_StrSeq(scanIOC))
    caput(pv+".ASPV",AfterScan_StrSeq(scanIOC,scanDIM))
    caput(pv+".BSCD",1)
    caput(pv+".BSWAIT","Wait")
    caput(pv+".ASCD",1)
    caput(pv+".ASWAIT","Wait")
    #SaveData
    caput("29id"+scanIOC+":saveData_realTime1D",1)
    #Check that detector and positioner PVs are good
    sleep(10)
    Scan_Check(scanIOC,scanDIM)

### Reset detectors in scan record:
def Scan_Check(scanIOC,scanDIM=1):
    """
    Check if any of the detectors or positions are not connected
    """
    print('Checking if all detectors & positioners are connected...')
    pv="29id"+scanIOC+":scan"+str(scanDIM)
    #Detectors
    for i in range(1,71):
        num=(str(i).zfill(2))
        pvd=caget(pv+".D"+num+"PV")
        if pvd !='': 
            det=PV(pvd); sleep(0.1)#smallest sleep to allow for PV traffic
            if not det.connected:
                print("Detector "+num+" has a bad PV:  "+det.pvname+" not connected")
    #Positioners
    for i in range(1,5):
        num=str(i)
        pvp=caget(pv+".P"+num+"PV")
        if pvp != '': 
            pos=PV(pvp)
            if not pos.connected:
                print("Positioner "+num+" has a BAD PV:  "+pos.pvname+" not connected")

            