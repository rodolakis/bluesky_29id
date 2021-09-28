from epics import caput, caget
from IEX_29id.utils.exp import Check_run, BL_Mode_Set, BL_ioc
from IEX_29id.mda.file import MDA_CurrentDirectory
from IEX_29id.mda.file import MDA_CurrentRun
import os 
import re 
   
def Make_DataFolder(run,folder,UserName,scanIOC,ftp): #JM was here ->print full crontab command and change permissions on kip -still needs work!
    """
    Creates the User Folder on the dserv
    if ftp = True: creates the folders on kip (ftp server) and modifies the cronjob
    """
    crontime={
        'mda2ascii':'0,30 * * * * ',
        'chmod':'1,31 * * * * ',
        'data_other':'2,32 * * * * ',
        'notebook':'*/3 * * * * ',
    }
    if (folder == 'c'or folder == 'd'):
        if ftp:
            print('-------------------------------------------------------------')
            #mda2ascii
            MyPath_kip_run='/net/kip/sftp/pub/29id'+folder+'ftp/files/'+run+'/'
            MyPath_kip='/net/kip/sftp/pub/29id'+folder+'ftp/files/'+run+'/'+UserName+'/'
            cmd_mda2ascii=crontime['mda2ascii']+' /net/s29dserv/APSshare/bin/mda2ascii -d '+MyPath_kip+'ascii '+MyPath_kip+'mda/*.mda'
            print(cmd_mda2ascii)
            #chmode
            cmd_chmod=crontime['chmod']+' chmod 664  '+MyPath_kip+'ascii/*.asc'
            print(cmd_chmod)
            #notebooks
            cmd_notebook=crontime['notebook']+' /usr/bin/rsync -av --exclude=core /home/beams22/29IDUSER/Documents/User_Folders/'+UserName+'/* kip:'+MyPath_kip+'notebook >  /home/beams22/29ID/cronfiles/cptoftp-currrun-d-User.log 2>&1'
            print(cmd_notebook)
            print('-------------------------------------------------------------\n\n')
            #making folders 
            print("\n\n")
            print(MyPath_kip)
            print(MyPath_kip+"ascii")
            if not (os.path.exists(MyPath_kip_run)):
                os.mkdir(MyPath_kip_run)
                os.chmod(MyPath_kip_run, 0o775)
            if not (os.path.exists(MyPath_kip)):
                os.mkdir(MyPath_kip)
                os.chmod(MyPath_kip, 0o775)
            if not (os.path.exists(MyPath_kip+"ascii")):
                os.mkdir(MyPath_kip+'ascii')
                os.chmod(MyPath_kip+'ascii', 0o775)
            if not (os.path.exists(MyPath_kip+"notebook")):
                os.mkdir(MyPath_kip+"notebook")
                os.chmod(MyPath_kip+"notebook", 0o775)
        else:
            print("To create ftp folders & update contrab, you need to run the following as 29id:")
            
            print("\tFolder_"+str(scanIOC)+"('"+str(run)+"','"+str(UserName)+"',ftp=True)")

        MyPath_File='/home/beams/29IDUSER/Documents/User_Folders/'+UserName
        UserName = "/"+UserName
        if not (os.path.exists(MyPath_File)):
            os.mkdir(MyPath_File)
        #if folder == 'd':
            #MyPath_File_hkl='/home/beams/29IDUSER/Documents/User_Folders/'+UserName+'/hkl'
            #if not(os.path.exists(MyPath_File_hkl)):
            #    os.mkdir(MyPath_File_hkl)
    if folder == 'b':
        UserName = ''
    #MyPath_run='/net/s29data/export/data_29id'+folder+'/'+run
    MyPath_run=os.path.dirname(_userDataFolder(UserName,scanIOC))
    if not (os.path.exists(MyPath_run)):
        os.mkdir(MyPath_run)
    #MyPath_Data=MyPath_run+UserName
    MyPath_Data=_userDataFolder(UserName,scanIOC)
    if not (os.path.exists(MyPath_Data)):
        os.mkdir(MyPath_Data)
    
def _userDataFolder(userName,scanIOC,**kwargs):
    """
    Returns the path to a user folder
            dataFolder='/net/s29data/export/data_29id'+folder+'/'+run+'/'+userName
    kwargs:
        run: Check_run(); unless specified
        BLmode:  Staff / User; based on userName unless specified
            
        folder: determined by UserName and scanIOC
            folder = b (Staff)
            folder = c (User and ARPES)
            folder = d (User and Kappa)
    """
    kwargs.setdefault('run',Check_run())
    folder=""
    run=kwargs['run']
    
    if userName == 'Staff':
        folder="b"
        if "BLmode" in kwargs:
            BL_Mode_Set(kwargs["BLmode"])
        else:
            BL_Mode_Set("Staff")
    else:
        BL_Mode_Set("User")
        if scanIOC=="ARPES":
            folder="c"
        if scanIOC=="Kappa":
            folder="d"   
                  
    dataFolder='/net/s29data/export/data_29id'+folder+'/'+run+'/'+userName
    return dataFolder

def _filename_key(filename):
    return (len(filename), filename)


def Folder_mda(run,folder,UserName,scanIOC):
    """
    For Staff: folder='b', UserName='Staff'
    For ARPES: folder ='c'
    For Kappa or RSoXS: folder = 'd'
    """
    FilePrefix=scanIOC
    if UserName == 'Staff':
        UserName=""
    else:
        UserName=UserName+"/"
    MyPath="/net/s29data/export/data_29id"+folder+"/"+run+"/"+UserName+"mda"
    print("\nMDA folder: " + MyPath)
    if not (os.path.exists(MyPath)):
        os.mkdir(MyPath)
        FileNumber=1
    else:
        FileNumber=getNextFileNumber(MyPath,FilePrefix)
    if scanIOC=="Test" or scanIOC=="Kappa" or scanIOC=="ARPES" or scanIOC=="RSoXS":
        caput("29id"+scanIOC+":saveData_fileSystem","/net/s29data/export/data_29id"+folder+"/"+run)
        os.sleep(0.25) #needed so that it has time to write        
        caput("29id"+scanIOC+":saveData_subDir","/"+UserName+"mda")
    else:
        caput("29id"+scanIOC+":saveData_fileSystem","//s29data/export/data_29id"+folder+"/"+run)
        os.sleep(0.25)
        caput("29id"+scanIOC+":saveData_subDir",UserName+"mda")
    caput("29id"+scanIOC+":saveData_baseName",FilePrefix+"_")
    caput("29id"+scanIOC+":saveData_scanNumber",FileNumber)

def getNextFileNumber(data_dir, file_prefix,**kwargs):
    """
    gets the next file number for the pattern 
    data_dir/file_prefix_filenum
    
    kwargs:
        debug = False (default); if True then print lo
        q = True (default); if False then prints next file number
    """
    kwargs.setdefault("debug",False)
    kwargs.setdefault("q",True)
    
    onlyfiles = [f for f in os.listdir(data_dir) if os.isfile(os.join(data_dir, f)) and f[:len(file_prefix)] == file_prefix]
    sortedfiles = sorted(onlyfiles, key=_filename_key)
    pattern = re.compile('(.*)_(.*)\.(.*)')
    try:
        lastFile = sortedfiles[-1]
    except IndexError as errObj:
        nextFileNumber = 1
        if kwargs["debug"]:
            print("Data directory = ", data_dir)
            print("File prefix =", file_prefix)
            print("File number =", None)
            print("File extension =", "TBD")
            print("Next File number =", nextFileNumber)
    else:
        matchObj = pattern.match(lastFile)
        nextFileNumber = int(matchObj.group(2)) + 1
        if kwargs["debug"]:
            print("Data directory = ", data_dir)
            print("File prefix =", matchObj.group(1))
            print("File number =", matchObj.group(2))
            print("File extension =", matchObj.group(3))
            print("Next File number =", nextFileNumber)
    if kwargs["q"] == False:
        print("Next File Number: ",nextFileNumber)
    return nextFileNumber


def Check_Staff_Directory(**kwargs):
    """
    Switchs to the staff directory
        Uses Fold
    """
    kwargs.setdefault("scanIOC",BL_ioc())
    kwargs.setdefault("run",Check_run())
    
    scanIOC=kwargs["scanIOC"]
    run= kwargs["run"]
    
    directory = MDA_CurrentDirectory(scanIOC)
    current_run = MDA_CurrentRun(scanIOC)
    
    if directory.find('data_29idb') < 1 or current_run != run:
        print('You are not currently saving in the Staff directory and/or the desired run - REPLY "yes" to switch folder.\nThis will only work if the run directory already exists.\nOtherwise, you must open ipython as 29id to create a new run directory using:\n\tFolder_'+scanIOC+'(run,\'Staff\')')
        foo=input('\nAre you ready to switch to the '+run+' Staff directory? >')
        if foo == 'Y' or foo == 'y' or foo == 'yes'or foo == 'YES':
            print('Switching directory...')
            if scanIOC=='ARPES':
                Folder_ARPES('Staff',mdaOnly=True,**kwargs)
            elif scanIOC=='Kappa':
                Folder_Kappa('Staff',create_only=False)
        else:
            print('\nFolder not set.')
    else:
        print('Staff directory OK.')
    directory = MDA_CurrentDirectory(scanIOC)
    print('\nCurrent directory: '+directory)

