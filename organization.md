
# Modules:

## devices
- <span style="color:lightgrey">arpes</span>
- detectors
- diagnostics
- kappa
- keithleys
- mono
- motors
- <span style="color:lightgrey">slit</span>
- undulator

## hklpy 

## mda
- file
- mda

## scans
- setup

## utils
- exp
- folders
- log
- misc
- plot
- status
- strings


---
---

# devices



## detectors
- <span style="color:green">Kappa_DetectorDict</span>
- set_detector <span style="color:green">(setdet,detset)</span>
- MPA_Interlock


## diagnostics
- 

## kappa
 - mvtth
 - Sync_PI_Motor
 - Sync_Euler_Motor
 - Home_SmarAct_Motor   <span style="color:green">(Sync_SmarAct_Motor)</span>
 

## keithleys
 - reset_keithley  <span style="color:green">(Reset_CA)</span>


## mono
- Reset_Mono_Limits

## motors
- Sync_Encoder_RBV
- Move_Motor_vs_Branch
- UMove_Motor_vs_Branch

## undulator
- 


---
---

# mda


## file
- MDA_GetLastFileNum
- MDA_CurrentDirectory
- MDA_CurrentPrefix
- MDA_CurrentRun
- MDA_CurrentUser

## mda 
- mda.py


---
---

# scans


## setup
- Reset_Scan
- Scan_Checksetup
- scantth
- Scan_Kappa_Motor_Go
- Scan_Kappa_Motor
- Scan_Go
- Scan_Fillin


<span style="color:orange">
Reset_Scan_Settings <br/> 
Detector_Default  <br/>  
Clear_Scan_Triggers</br>
Detector_Triggers_StrSeq</br>
Detector_List</br>
BeforeScan_StrSeq</br>
AfterScan_StrSeq</br>
Check_MainShutter</br>
Kappa_PVmotor</br>
</span>
<br/> 


___
___


# utils


## exp 
<span style="color:red">TO BE CLEANED</span>
- Check_run
- CheckBranch
- CheckBranch_Name
- BL_Mode_Set
- BL_Mode_Read
- BL_ioc
___

## folders  
<span style="color:red">TO BE CLEANED</span>
- Make_DataFolder
- _userDataFolder
- _filename_key
- Folder_mda
- Folder_ARPES
- getNextFileNumber 
- Check_Staff_Directory

<span style="color:orange">
 Folder_ARPES <br/> 
 Folder_Kappa  <br/>  
 </span>
 <br/> 

___

## log
- logname_PV
- logname_set
- logname_get
- logname_generate
- logname
- logprint
- log_headerMDA
- scanlog

<span style="color:orange"> 
SaveFile_Header <br/> 
SaveFile  <br/>  
ARPES_PVmotor</br>
Kappa_PVmotor</br>
</span>
<br/> 

## misc
- playsound
- RangeUp
- RangeDown
- TakeClosest
- dateandtime
- WaitForIt
- today


## plot
- plot_image

<span style="color:orange">
 matplotlib.image <br/> 
 matplotlib.pyplot <br/> 
 </span>
 <br/> 


## status

- Get_All
- Get_ARPES
- mprint
- Print_Motor
- Get_energy
- Get_Mono
- Get_CFF
- Get_Mirror
- Get_HXP
- Get_Slits
- Get_mARPES
- Get_mKappa
- Get_Kappa
- Get_Gain
- Get_SnapShot

<span style="color:orange">   
ARPES_PVmotor</br>
Mono_Optics</br>
SyncAllSlits</br>
Kappa_PVmotor</br>
</span>
<br/> 

## strings
- ClearStringSeq
- ClearCalcOut
- ClearUserAvg

---
---




---
---

