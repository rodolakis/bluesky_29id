#!/bin/I-AM-A-README_DO_NOT_EXECUTE


# To convert tabs to space or space to tabs:
# IMPORTANT: does need a new destination file.py > file_new.py NOT file.py > file.py (deletes all the content!!!)
#
# cp ScanFunctions_IEX.py ScanFunctions_IEXbackup.py  
# sed -e 's/    /\t/g' ScanFunctions_IEXbackup.py > ScanFunctions_IEX.py   # spaces to tabs (s/   /\t => insert 4 spaces between //)
# sed $'s/\t/    /g' ScanFunctions_IEXbackup.py ScanFunctions_IEX.py       # tabs to space (t/   /g   => insert 4 spaces between //)
#
#


# To use the version control (git):	=> see detailed help below
#================================

## to ignore a file: 
#---------------------
	add it to .gitignore file (in gedit or whatever text editor)


## to commit all files:
#---------------------

#	export VISUAL=nano
#	
#	git commit -a  	
#		
#	type all my comments
#	ctrl+O   to save
# 	press Enter
#	ctrl+X   to quit

## to commit ONE file:
#---------------------

#	export VISUAL=nano
#	
#	git add myfiletocommit.py
#	git commit myfiletocommit.py
#	
#	type all my comments
#	ctrl+O   to save
# 	press Enter
#	ctrl+X   to quit

## to see the difference:
#-----------------------

#git diff ScanFunctions_plot.py
#git difftool -t tkdiff ScanFunctions_plot.py



## to push on GitLab:
#---------------------

#	git push


## to see the files under version control:
#----------------------------------------
#	git ls-files

## to bring back changes from home computer (Fanny's iMac) to sleepy:
#-------------------------------------------------------------------
#
# On iMac:
#	commit all changes (git commit -a)
#	git fetch    =>  make sure local computer is up to date with branch master history 
#	git push
#
# On sleepy:
#	git stash    =>  store local changes aside (changes that have not been committed yet)
#	git fetch    =>  sync local computer with branch master history 
#	git status   =>  Your branch is behind 'origin/master' by 1 commit, and can be fast-forwarded: GOOD, no conflict
#	git rebase origin/master  =>  update files to sync with the branch master
#	git status   =>  you're now up to date with branch master
#	git stash apply    =>  restore local changes 
#	
#
 



# The most commonly used git commands are:
#   add        Add file contents to the index
#   bisect     Find by binary search the change that introduced a bug
#   branch     List, create, or delete branches
#   checkout   Checkout a branch or paths to the working tree
#   clone      Clone a repository into a new directory
#   commit     Record changes to the repository
#   diff       Show changes between commits, commit and working tree, etc
#   fetch      Download objects and refs from another repository
#   grep       Print lines matching a pattern
#   init       Create an empty Git repository or reinitialize an existing one
#   log        Show commit logs
#   merge      Join two or more development histories together
#   mv         Move or rename a file, a directory, or a symlink
#   pull       Fetch from and merge with another repository or a local branch
#   push       Update remote refs along with associated objects
#   rebase     Forward-port local commits to the updated upstream head
#   reset      Reset current HEAD to the specified state
#   rm         Remove files from the working tree and from the index
#   show       Show various types of objects
#   status     Show the working tree status
#   tag        Create, list, delete or verify a tag object signed with GPG





# Tp change file/dir permissions:
#================================

# Other useful commands: 
#
#	-----a-----	= all
#	-u- -g- -o-	= user/grp/other
#	rwx rwx rwx 	
#	421 421 421	= (2^2)(2^1)(2^0)
#
#	chmod 664	= -rw-rw-r-- = (4+2+0)(4+2+0)(4+0+0)
#	chmod 775	= -rwxrwxr-x = (4+2+0)(4+2+0)(4+0+1)   => for directories
#	chmod 777	= -rwxrwxrwx = (4+2+1)(4+2+1)(4+0+1)
#	
#	chmod a-x myfilename		# to remove executable to all
#	chmod g+w myfilename		# to add write permission to group
#	chmod g+s mydirectoryname	# all subdirectories have the same permissions as the parent (drwxrwsr-x)
#
#	chgrp				# to change current user group (by default it is the primary group)
#
#
#	pushd mypath
#	pushd		
#	popd
#	dirs	
#
#	kdiff3 file1 file2

	

# Snapshot:
#=======

#- navigate to th folder where the file is
#- cd .snapshot
#- ls -l
#- pick your folder
#- cp thefile ../../thefile_backup



# Add/remove extra PVs in scanrecord:
#===================================

#[junebug ~] su 29id	
#[junebug ~] ioc 29idKappa 
#[junebug /net/s29dserv/xorApps/epics/synApps_5_8/ioc/29idKappa] cd iocBoot/ioc29idKappa
#[junebug /net/s29dserv/xorApps/epics/synApps_5_8/ioc/29idKappa/iocBoot/ioc29idKappa] gedit saveData.req

# To make sure it is the right version of SynApps, for to IOC status webpage: 

#Environment Variables
#
#    ARCH = linux-x86_64
#    TOP = /net/s29dserv/xorApps/epics/synApps_5_8/ioc/29idKappa
#    EPICS_BASE = /APSshare/epics/base-3.14.12.5
#    SUPPORT = /APSshare/epics/synApps_5_8/support
#    ENGINEER = Arms
#    LOCATION = 29ID-D
#    GROUP = XSD-MM


# Retreive IOC auto-save:
#===================================

#Same as above, find IOC location form the IOC webpage, then ls -lt:

#-rwxrwxrwx 1 dohnarms s29admin 230517 Jun 18 13:53 auto_settings.savB
#-rwxrwxrwx 1 dohnarms s29admin 230517 Jun 18 13:53 auto_settings.sav
#[...]
#-rw-rw-r-- 1 29id     s29admin 230588 Jun 10 09:33 auto_settings.sav_210610-093348
#-rw-rw-r-- 1 29id     s29admin    284 Jun 10 09:33 auto_positions.sav_210610-093348
#-rw-rw-r-- 1 29id     s29admin 230600 Jun 10 09:26 auto_settings.sav_210610-092619
#-rw-rw-r-- 1 29id     s29admin    284 Jun 10 09:26 auto_positions.sav_210610-092619
#-rw-rw-r-- 1 29id     s29admin 230587 Jun 10 09:10 auto_settings.sav_210610-091028

# you can look at old setting in gedit or copy it and rename it as auto_settings.sav with the IOC off; settings will be replaced by the autsaved values at reboot
#[junebug /net/s29dserv/xorApps/epics/synApps_5_8/ioc/29idKappa/iocBoot/ioc29idKappa/autosave] gedit auto_settings_210610-093348.sav


# To modify the IPython startup:
#==============================

# Go to: 	(29id)  	cd /home/beams22/29ID/.ipython/profile_default/startup/
#	(29iduser)	cd /home/beams22/29IDUSER/.ipython/profile_default/startup/
#
#
#	.py and .ipy files in this directory will be run *prior* to any code or files specified
#	via the exec_lines or exec_files configurables whenever you load this profile.
#
#	Files will be run in lexicographical order, so you can control the execution order of files
#	with a prefix, e.g.:
#
#	    00-first.py
#	    50-middle.py
#	    99-last.ipy
#
#
#	99-StartDir => indicates the path for the macros Folder for each user id
#
# Create soft link to common ScanFunctions scripts:
#	
#	ln -s /home/beams/29IDUSER/Documents/User_Macros/Macros_29id/ScanFunctions_IEX.py 91-ScanFunctions_IEX.py




# To use M4R hexapods:  (most commands are aliased)   - 2/12/2021
#=====================

# IMPORTANT: backup/restore => s29hxp1    BUT    gui = hxp2  (for scattering)

#[sleepy~] su 29id
#[sleepy~] 29idHXP status
#[sleepy~] 29idHXP start

#[sleepy~] hxpPositionRestore
# => gives basic instructions
# 
#[sleepy~] cd /net/s29dserv/xorApps/epics/synApps_5_7/ioc/29idHXP/iocBoot/ioc29idHXP/hxp_backups
#[sleepy~] ls -lt
#-rw-rw-r-- 1 29id     s29admin 655 Nov 11 17:34 s29hxp1_20201111-173407.xml
#-rw-rw-r-- 1 29id     s29admin 666 Sep 25 13:15 s29hxp3_20200925-131531.xml
#-rw-rw-r-- 1 29id     s29admin 658 Dec 12  2019 s29hxp1_20191212-201925.xml
#-rw-rw-r-- 1 29iduser s29admin 659 Nov 15  2019 s29hxp1_20191115-181411.xml
#...
#[sleepy~] hxpPositionRestore <last s29hxp1 backup name>
#
# Move hexapod: v = Pitch , u = Roll , z = lateral
#
#[sleepy~] hxpPositionBackup s29hxp1
#
# DONE

# HXP website: http://s29hxp1.xray.aps.anl.gov/
# administrator / administrator

# To setup SRS baseline:  
#======================
#
# With shutter close, 'INPUT OFFSET' set 'ON' and 'UNCAL'
#- make sure the counts go down (not up) when closing the shutter! If the count goes up without beam, change the INVERT ON/OFF - as of 2021_2 all of our SRSs are INVERT ON (D3/D4/TEY/mesh) 
#- Set gain relatively high for the offset (same as sensitivity or more)
#- play with the tweak button one way or the other to get a stable number (ie does not slowly goes down to zero); you might need to play with the +/- for that
#- try decreasing the offset gain: if it drops to zero, then go back to previous gain and increase the number; try again. 
#- The goal is to slowly bring the gain down while keeping a non zero signal; 
#- adjust until the final INPUT OFFSET gain should be at least 1 order of magnitude lower than the SENSITIVITY with a few hundreds counts

