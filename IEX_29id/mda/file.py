from epics import caput, caget
from IEX_29id.utils.exp import BL_ioc 


def MDA_GetLastFileNum(scanIOC=None):
    if scanIOC is None:
        scanIOC=BL_ioc()
    FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")-1
    return FileNum

def MDA_CurrentDirectory(scanIOC=None):
    if scanIOC is None:
        scanIOC=BL_ioc()
    Dir=caget("29id"+scanIOC+":saveData_fileSystem",as_string=True)
    subDir=caget("29id"+scanIOC+":saveData_subDir",as_string=True)
    FilePath = Dir +'/'+subDir+"/"
    if FilePath[1]=='/':
        FilePath="/net"+FilePath[1:]
    FilePath=FilePath.replace('//','/') 
    return FilePath   

def MDA_CurrentPrefix(scanIOC=None):
    if scanIOC is None:
        scanIOC=BL_ioc()
    Prefix=caget("29id"+scanIOC+":saveData_baseName",as_string=True)
    return Prefix
   
def MDA_CurrentRun(scanIOC=None):
    if scanIOC is None:
        scanIOC=BL_ioc()
    directory = MDA_CurrentDirectory(scanIOC)
    m=directory.find('data_29id')+len('data_29id')+2
    current_run=directory[m:m+6]
    return current_run
   
def MDA_CurrentUser(scanIOC=None):
    if scanIOC is None:
        scanIOC=BL_ioc()
    subdir=caget("29id"+scanIOC+":saveData_subDir",as_string=True)
    m=subdir.find('/mda')
    if m == 0 : current_user='Staff'
    elif m > 0: current_user=subdir[1:m]
    else: current_user="";print("WARNING: MDA_CurrentUser is empty string")
    return current_user   