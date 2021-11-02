



# kappa:
- tth0_set()
- sync kappa / fourc
- homf piezo


- dscanz(-750,750,50)
- dscanx(-0.5,0.5,0.05)  
- dscany(-0.5,0.5,0.05)  
- dscanth(-0.5,0.5,0.05) 
- dscanchi(-5,5,0.5)
- dscanphi(-5,5,0.5)
- dscankap
- dscankth
- dscankphi

- scanz(-750,750,50)
- scanx(-0.5,0.5,0.05)  
- scany(-0.5,0.5,0.05)  
- scanth(-0.5,0.5,0.05) 
- scanchi(-5,5,0.5)
- scanphi(-5,5,0.5)
- scankap
- scankth
- scankphi
- scanth2th

- align_m3r




# detector
- cts()
- setgain

- MPA_HV_Set
- MPA_HV_ON
- MPA_HV_OFF
- MPA_HV_RESET
- MPA_HV_scan
- MPA_ROI_SetUp
- MPA_ROI_SetAll

# exp:
- Switch_Branch()

# energy:
- energy(2570)
- scanhv
- scanXAS
- scanXAS_BL


# undulator:
- polarization('H')
- Switch_QP


# mono:
- grating()

# slits
- slit(100)
- SetSlit_BL
