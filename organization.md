
# Modules:

## devices
- <span style="color:lightgrey">arpes</span>
- ca  (current amplifiers)
- detector
- diagnostic
- kappa
- mono
- motor
- <span style="color:lightgrey">slit</span>
- undulator

## hklpy 

## mda
- mda

## utils
- exp
- folders
- log
- misc
- plot
- status
- strings

## scans

---
---

# devices


## ca
 - Reset_CA

## detector
- Kappa_DetectorDict
- setdet
- detset
- MPA_Interlock


## diagnostic
- 

## kappa
 - Sync_PI_Motor
 - Sync_Euler_Motor
 - Home_SmarAct_Motor
 

## mono
- Reset_Mono_Limits

## motor
- Sync_Encoder_RBV
- 

## undulator
- 

---
---




# Utils


## exp: 

- Check_run
- CheckBranch
- CheckBranch_Name
- BL_Mode_Set
- BL_Mode_Read
- BL_ioc


## folders
- Make_DataFolder
- _userDataFolder
- _filename_key
- Folder_mda
- getNextFileNumber 
- Check_Staff_Directory

<span style="color:orange">
 Folder_ARPES <br/> 
 Folder_Kappa  <br/>  
 </span>
 <br/> 


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
MDA_CurrentUser <br/> 
SaveFile_Header <br/> 
SaveFile</br> 
ID_State2Mode  <br/>  
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
ID_State2Mode  <br/>  
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


# scans
- Reset_Scan
- Scan_Check
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


---
---

