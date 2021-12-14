# Kappa Alignment

## Align M3R pitch to center of rotation:
1) start from the last known value for M3R pitch ie desired pixel value (typically betwen 110-115)
2) align direct beam on d4 and reset tth0:

        align_d4(z0,th)
        mvtth(new_value)
        tth0_set()
   
    note: &nbsp;- th can be 0 or 180 (no need to care about omega here)<br>
    &emsp;&emsp;&ensp; - at that point z0 is a rough estimate<br>
    &emsp;&emsp;&ensp; - **use d3 only to measure z** (d4 is too narrow)

3) align z at th=0:

        z0=align_z0(0)

4) find omega0 at th/2th=15,30:

        omega0=align_th0(0,z0)

5) iterate until it converges, keeping an eye on the mirror pixel position (1pxl ~ 50um in z)

6) go to th=180 and repeat steps 3 to 5 to find z180 and omega180

7) find mirror position to reach target z value $z_{opt}=0.5*(z0+z180)$ by changing the desired pixel position directly from the screen, then run:
       
         align_m3r()
         align_z0() 



8) **realign tth0** for new mirror position (step 2)

9) refine (omega180, z180) and (omega0, z0) for new tth0, keeping a close eye on the mirror to make sure it stays at the optimal position


---------------------------------------

## Determine kth_offset:

If th_0 and th_180 is the motor position at specular near th=15 and th=165, respectivaley (eg th_0=13.671 and th_180=163.65):

        Offset = 0.5*(180 - th_180 - th_0)

With motor at 0, the actual value is Offset.

---------------------------------------

##  Align M4R pitch to center of rotation:
1) move to th=90, chi=0, phi=90

2) find z:

        align_z0_chi0()

3) adjust M4R pitch (v) to match z0=z180:

        # IMPORTANT: backup/restore => s29hxp1    BUT    gui = hxp2  (for scattering)
        
        # From Nerdy:
        
        [nerdy~] su 29id
        [nerdy~] 29idHXP status
        [nerdy~] 29idHXP start
        
        [nerdy~] hxpPositionRestore
        # => gives basic instructions
        # 
        [nerdy~] cd /net/s29dserv/xorApps/epics/synApps_5_7/ioc/29idHXP/iocBoot/ioc29idHXP/hxp_backups
        [nerdy~] ls -lt
        -rw-rw-r-- 1 29id     s29admin 655 Nov 11 17:34 s29hxp1_20201111-173407.xml
        -rw-rw-r-- 1 29id     s29admin 666 Sep 25 13:15 s29hxp3_20200925-131531.xml
        -rw-rw-r-- 1 29id     s29admin 658 Dec 12  2019 s29hxp1_20191212-201925.xml
        -rw-rw-r-- 1 29iduser s29admin 659 Nov 15  2019 s29hxp1_20191115-181411.xml
        ...
        [nerdy~] hxpPositionRestore <last s29hxp1 backup name>
        
        # Move hexapod: v = Pitch , u = Roll , z = lateral
        
        [nerdy~] hxpPositionBackup s29hxp1
        
        # DONE
        


4) WARNING: check if moving M4R did not change the in/out alignmnent (M3R optimal pixel)

---------------------------------------

##  Determined kap offset:


1) compare kap scans at (th,chi,phi) = (90,0,90) and (270,0,-90):

        dscankap(-4,4,0.1)

2) watch out for the braid when going from th=90, phi=90 to th=270, phi=-90!
3) set the value of intersection (here 0.18) to 0:

![image](./figures/KapBeforeAfter.png)