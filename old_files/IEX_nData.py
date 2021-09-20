#IEX_nData.py 
#wrapper to load data from IEX beamline as pynData
#if mda.py is in a location outside of the folder containing these files, you will need to %run first


__version__= 1.0      #JLM 4/27/2021

import os as os
from numpy import inf
import re
import h5py
import netCDF4 as nc
import tifffile

#import pynData
from .pynData.nmda import nmda,nmda_h5Group_w,nmda_h5Group_r
from .pynData.nEA import nEA
#from .pynData.nADtif import nTiff     # FR commented out to compile
from .pynData.pynData import *
try:
    from ScanFunctions_IEX import MDA_CurrentDirectory, BL_ioc, AD_CurrentDirectory, AD_prefix
    from ScanFunctions_EA import EA
except:
    print("ScanFunctions_IEX and ScanFunctions_EA are not loaded: you will need to specify path and prefix when calling IEXdata")


###################################
## default stuff (Users can modify here to load an home not using IEX function)
###################################
            


def CurrentDirectory(dtype):
    """
    Returns the current directory for:
       if "mda" is in dtype => return mda path
       elif "EA" is in dtype => returns EA path
       
       e.g. dtype=mdaEA => only get mda
    """
    if "mda" in dtype:
        try:
            path=MDA_CurrentDirectory()
        except:
            path="mda filepath needs to be specified"
        return path

    elif "EA" in dtype:
        try:
            path=AD_CurrentDirectory(EA._savePlugin)
        except:
            path="EA filepath needs to be specified"
        return path
    
        
def CurrentPrefix(dtype):
    #if dtype == "mda" or dtype == "mdaEA":
    if "mda" in dtype:
        try:
            prefix=BL_ioc()+"_"
        except:
            prefix="prefix_"
    elif "EA" in dtype:
        try:
            prefix=AD_prefix(EA._savePlugin)+"_"
        except:
            prefix="prefix_"
    return prefix

###################################
# IEX variables
def _EAvariables(dtype):
    """
    default variable for EA for IEX as fo 05/10/2021
    """
    EAvar={}
    if dtype == "EA_nc":
        EAvar["EA_dtype"]="nc"
        EAvar["EA_nzeros"]=4
        #default detector values for old nc driver
        EAvar["EA_source"] = "APS_IEX"
        EAvar["EA_centerChannel"] = 571-50
        EAvar["EA_firstChannel"] = 0
        EAvar["EA_degPerPix"] = 0.0292717
        EAvar["EA_cropStart"] = 338-50
        EAvar["EA_cropStop"] = 819-50
        
    elif dtype == "EA":
        EAvar["EA_dtype"] = "h5"
        EAvar["EA_nzeros"] = 4
        #default detector values for old nc driver
        EAvar["EA_source"] = "APS_IEX"
        EAvar["EA_centerChannel"] = 571-50
        EAvar["EA_firstChannel"] = 0
        EAvar["EA_degPerPix"] = 0.0292717
        EAvar["EA_cropStart"] = 338-50
        EAvar["EA_cropStop"] = 819-50
    return EAvar


###################################
    
def _mdaHeader_IEX(cls,headerList,**kwargs):
    """
    General IEX beamline information
    """
    kwargs.setdefault('debug',False)
    
    if kwargs['debug']:
        print('cls.prefix:',cls.prefix)
        print('BL info')
        
    setattr(cls, 'ID', {key:value[:3] for key, value in headerList.items() if 'ID29' in key}) 
    setattr(cls,'mono',{key:value[:3] for key, value in headerList.items() if 'mono' in key})
    setattr(cls,'energy',{key:value[:3] for key, value in headerList.items() if 'energy' in key.lower()})
    setattr(cls,'motor',{key:value[:3] for key, value in headerList.items() if '29idb:m' in key})
    setattr(cls,'slit',{key:value[:3] for key, value in headerList.items() if 'slit' in key.lower()} )
    if 'filename' in headerList:
        setattr(cls,'prefix',headerList['filename'].split('/')[-1].split('_')[0]+"_")

    ##kappa
    if cls.prefix.lower() == "Kappa".lower():
        if kwargs['debug']:
            print("kappa")
        _mdaHeader_Kappa(cls,headerList)
        
    #ARPES
    if cls.prefix.lower() == "ARPES".lower():
        if kwargs['debug']:
            print("ARPES")
        _mdaHeader_ARPES(cls,headerList)

def _mdaHeader_Kappa(cls,headerList):
    """
    Kappa specific header info
    """
    sampleInfo={**{key:value[:3] for key, value in headerList.items() if '29idKappa:m' in key},
                **{key:value[:3] for key, value in headerList.items() if '29idKappa:Euler' in key},
                **{key:value[:3] for key, value in headerList.items() if 'LS331' in key}}
    setattr(cls, 'sample',sampleInfo)
    setattr(cls, 'mirror',{key:value[:3] for key, value in headerList.items() if '29id_m3r' in key})
    setattr(cls, 'centroid',{key:value[:3] for key, value in headerList.items() if 'ps6' in key.lower()})
    detkeys=['29idMZ0:scaler1.TP','29idKappa:m9.RBV','29idKappa:userCalcOut10.OVAL','29iddMPA:C0O','29idKappa:userStringSeq6.STR1','29idd:Unidig1Bo0']
    detInfo={**{key:value[:3] for key, value in headerList.items() if '29idd:A' in key},
             **{key:value[:3] for key,value in headerList.items() if key in detkeys}}
    setattr(cls, 'det',detInfo)
    comment=""
    for i, key in enumerate(list(headerList.keys())):
            if re.search('saveData_comment1', key) : 
                comment=str(headerList[key][2])
            elif re.search('saveData_comment2', key) : 
                if headerList[key][2] != '':
                    comment+=' - '+str(headerList[key][2])
    setattr(cls, 'comment',comment)


def _mdaHeader_ARPES(cls,headerList):
    """
    ARPES specific header info
    """    
    sampleInfo={**{key:value[:3] for key, value in headerList.items() if '29idc:m' in key},
                **{key:value[:3] for key, value in headerList.items() if '29idARPES:LS335:TC1' in key}}
    setattr(cls, 'sample',sampleInfo)


class nEA_IEXheader():
    """
    Get IEX specific PVs and writes them to the nEA header
    """
    def __init__(self,d,dtype,**kwargs):
        """
        EA header information
        """
        metadata=self._IEXpvs(d,dtype)
        
        self.fileInfo=metadata['fileInfo']
        
        BeamlineInfo = ["hv","grating","ID","polarization","grating","exitSlit","ringCurrent"]
        self.BL={key: metadata[key] for key in BeamlineInfo}
        
        sampleInfo = ["x","y","z","theta","chi","phi","TA","TB","TEY","TEY2"]
        self.sample={key: metadata[key] for key in sampleInfo}
        

    def _IEXpvs(self,d,dtype):
        """
        returns dictionary with from extra pvs, used for the ARPES header
        """
        PVs={
        "SESslit":"m8_SESslit",
        "hv":"ActualPhotonEnergy",
        "TA":"T_A",
        "TB":"T_B",
        "TEY":"TEY",
        "TEY2":"TEY2",
        "I0":"",
        "hv":"ActualPhotonEnergy",
        "ID":"ID_Energy_RBV",
        "polarization":"ID_Mode_RBV",
        "grating":"Grating_Density",
        "exitSlit":"Slit3CRBV",
        "ringCurrent":"RingCurrent",
        "x":"m1_X",
        "y":"m2_Y",
        "z":"m3_Z",
        "theta":"m4_Theta",
        "chi":"m5_Chi",
        "phi":"m6_Phi",  
        }
        metadata={}
        ###############################
        if dtype == 'nc':
            for key in PVs:
                if 'Attr_'+PVs[key] in d.variables.keys():
                    metadata.update({key:d.variables['Attr_'+PVs[key]][:][0]})
                else:
                    metadata.update({key:None})
        ###############################
        elif dtype == "h5":
            for key in PVs:
                if PVs[key] in list(d['entry']['instrument']['NDAttributes'].keys()):
                    metadata.update({key:d['entry']['instrument']['NDAttributes'][PVs[key]][0]})
                else:
                    metadata.update({key:None})
        _EAvariables(dtype)
        return metadata

###################################
def _shortlist(*nums,llist,**kwargs):
    """
    Making a shortlist based on *num
    *num =>
        nums: for a single scan
        inf: for all num in longlist
        first,last: for all numbers between and including first and last; last can be inf
        first,last,countby: to load a subset
        [num1,num2]: to load a subset of scans
    kwargs:
        debug=False
    """
    kwargs.setdefault("debug",False)
    
    if kwargs['debug']:
        print("nums: ",nums)
        print("llist",llist)
    llist.sort()
    if type(nums[0]) is list:
        shortlist=nums[0]
    else:
        if len(nums)==1:
            if nums[0] != inf:
                first,last,countby=nums[0],nums[0],1
            else:
                first,last,countby=llist[0],llist[-1],1
        elif len(nums)==2:
            first,last=nums
            countby=1
        elif len(nums)==3:
            first,last,countby=nums
        if last == inf:
            last=llist[-1]
        #print(first,last,countby)
        shortlist=[]
        for n in range(first,last+countby,countby): 
            if n in llist:
                shortlist.append(n)
    if kwargs["debug"]:
        print("shortlist: ",shortlist)
    return shortlist
    
def _dirScanNumList(path,prefix,extension):
    """
    returns a list of scanNumbers for all files with prefix and extension in path
    """

    #getting and updating directory info
    allfiles = [f for f in os.listdir(path) if os.path.isfile(path+f)]
    #print(allfiles)

    split=prefix[-1] 
    allfiles_prefix = [x for (i,x) in enumerate(allfiles) if allfiles[i].split(split)[0]==prefix[:-1]] 
    #print(allfiles_prefix)

    allfiles_dtype = [x for (i,x) in enumerate(allfiles_prefix) if allfiles_prefix[i].split('.')[-1]==extension]
    #print(allfiles_dtype)

    allscanNumList = [int(allfiles_dtype[i][allfiles_dtype[i].find('_')+1:allfiles_dtype[i].find('_')+5]) for (i,x) in enumerate(allfiles_dtype)]
    #print(allscanNumList)

    return allscanNumList        

###################################       
class IEXdata:
    """"
    loads IEX (mda or EA) data and returns a dictionary containing pynData objects
        in Igor speak this is your experiment and the pynData objects are the waves

    ***** Usage: 
             mydata = IEXdata(first)  => single scan
                    = IEXdata(first,last,countby=1) => for a series of scans
                    = IEXdata(first,inf,overwrite=False) => all unloaded in the directory

             mydata.update(firt,last,countby) updates the object mydata by loading scans, syntax is the same as above

             myData.mda = dictionary of all individual mda scans 
             myData.EA = dictionary of all individual EA scans 
             
             mda:
                 myData.mda[scanNum].det[detNum] => nmda object
                 myData.mda[scanNum].header => extra PVs
             EA:
                 myData.EA[scanNum] => EA_nData object" 
                 
        kwargs:
            path = full path to mda files (Note: code assumes that mda, h5, mpa ... are in the same folder)
                e.g. path="/net/s29data/export/data_29idc/2021_2/Jessica/mda/" 
            prefix ="ARPES_" or "Kappa_" or "EA_"
            dtype = "mdaAD" - mda and EA/mpa if exist (default)
                  = "mda" - mda only
                  = "EA" or "EAnc" for ARPES images only h5 and nc respectively
                  = "mpa" - mpa only
        """

    def __init__(self,*scans, dtype="mdaAD",**kwargs):
        """
        *scans =>
            scanNum: for a single scan
            inf: for all scans in directory
            first,last: for all files between and including first and last; last can be inf
            first,last,countby: to load a subset
            [scanNum1,scanNum2]: to load a subset of scans
        dtype = mda / EA / EAnc / ADtif 
              = mdaAD loads EA and ADtif automatically if there files associated with the mda
                (look in the h5 or mpa directories and looks at filenames)
        
        **kwargs
            path = CurrentDirectory(dtype)
            prefix = CurrentPrefix(dtype)
            suffix = ""
            nzerors = number of digit; (4 => gives (0001))
            
            overwrite = True/False; if False, only loads unloaded data"  
            
            q=False (default prints filepath and which scans are loaded); q=True turns off printing
            debug=False (default); if debug = True then prints lots of stuff to debug the program
        """
        kwargs.setdefault('overwrite',True)
        kwargs.setdefault('q',False)
        kwargs.setdefault('debug',False)
        kwargs.setdefault("nzeros",4)
        if kwargs["debug"]:
            print("IEX_nData.__init__")

        self._scans=scans
        self.dtype=dtype
        
        self.mda={}
        self._mdaLoadedFiles =[]
        self.EA={}
        self._EALoadedFiles=[]
        self.mpa={}
        self._mpaLoadedFiles=[]
        
        if kwargs["debug"]:
            print("scans: ",scans)
            print("kwargs:",kwargs)
            for key in vars(self):
                print(key,getattr(self,key))
   
        if scans:
            kwargs.update(self._key2var(**kwargs))
            self._extractData(*scans, **kwargs)
        else:
            pass
        
        
    def _key2var(self,**kwargs):
        """
        defines default IEXdata **kwargs and
        sets self.var kwargs 
        """
        kwargs.setdefault('overwrite',True)
        kwargs.setdefault("path",CurrentDirectory(self.dtype))
        kwargs.setdefault("prefix",CurrentPrefix(self.dtype))
        kwargs.setdefault("suffix",'')
        kwargs.setdefault("nzeros",4)
        kwargs.setdefault("debug",False)
        
        if kwargs["debug"]:
            print("\nIEX_nData._key2var kwargs:",kwargs)
            
        if kwargs["q"]==False:
            print("path = "+kwargs["path"])
        
        self.path = os.path.join(kwargs['path'],"")
        self.prefix = kwargs['prefix']
        self.nzeros = kwargs['nzeros']
        self.suffix =kwargs['suffix']
        #if self.dtype == "mdaEA":
        if "mda" in self.dtype:
            self.ext="mda"
        else:
            self.ext=self.dtype
        return kwargs
        if kwargs['debug']:
            print("\n_key2var kwargs:",kwargs)
        
    def _extractData(self,*scans,**kwargs):
        """
        *scans =>
            scanNum: for a single scan
            inf: for all scans in directory
            first,last: for all files between and including first and last; last can be inf
            first,last,countby: to load a subset
            [scanNum1,scanNum2]: to load a subset of scans
        
        **kwargs
            overwrite = True; reloads all data specified by *scans
                      = False; only loads the data specified by *scans which has not already been loaded
        """
        kwargs.setdefault('debug',False)
        kwargs.setdefault('overwrite',True)
        kwargs.setdefault('q',True)

        if kwargs["debug"] == True:
            print("IEX_nData._extractData dtype: ", self.dtype)
        
        loadedList=[]
        ########################################################################
        if self.dtype == "mda":
            self.ext=self.dtype
            allscanNumList=_dirScanNumList(self.path,self.prefix,self.ext)
            shortlist=_shortlist(*scans,llist=allscanNumList)
            if kwargs["debug"] == True:
                print("shortlist: ",shortlist)
            loadedList=self._mdaIEXdata(shortlist,**kwargs)
            if kwargs["debug"] == True:
                print("loadedList: ",loadedList)

        if self.dtype == "EA" or self.dtype =="EA_nc":           
            self.ext=_EAvariables(self.dtype)["EA_dtype"] 
            allscanNumList=_dirScanNumList(self.path,self.prefix,self.ext)
            shortlist=_shortlist(*scans,llist=allscanNumList,**kwargs)
            if kwargs["debug"] == True:
                print("shortlist: ",shortlist)
            loadedList=self._eaIEXdata(shortlist,**kwargs) 
            
        if "mda" in self.dtype:
            #mda scans
            loadedList=[]
            self.ext="mda"
            MDAallscanNumList=_dirScanNumList(self.path,self.prefix,self.ext)
            MDAshortlist=_shortlist(*scans,llist=MDAallscanNumList,**kwargs)
            mdapath=os.path.dirname(self.path)
            userpath=os.path.dirname(mdapath)
            if kwargs["debug"]:
                print("mdapath: ",mdapath)
                print("userpath: ",userpath)
                
            if "AD" in self.dtype:
                AD_dtype = ""
                ADext = ""
                ADpath = ""    
                if self.prefix.lower()=="ARPES_".lower():
                    #EA files
                    AD_dtype = "EA"
                    ADext=_EAvariables(AD_dtype)["EA_dtype"]  
                    ADpath=os.path.join(userpath,ADext,'')
                elif self.prefix.lower() == "Kappa_".lower():
                    #MPA tif files
                    AD_dtype="mpa"
                    ADext="tif"
                    ADpath=os.path.join(userpath,AD_dtype,'')
                else:
                    print("no AD associated with this IOC")
                
                if kwargs["debug"]:
                    print(AD_dtype+" path: ",ADpath)
                    print(AD_dtype+" ext: ",ADext)

            for MDAscanNum in MDAshortlist:
                #load mda
                MDAloadedList=self._mdaIEXdata([MDAscanNum],**kwargs)
                loadedList.append(MDAloadedList)
                #loading AD data
                if len(ADpath)>1:
                    if 'EA' in AD_dtype: 
                        setattr(self.mda[MDAscanNum],'EA',{})
                    if 'mpa' in AD_dtype:
                        setattr(self.mda[MDAscanNum],'mpa',{})

                    if kwargs['debug']:
                        print ("MDAscanNum: ",MDAscanNum)
                    if "nzeros" in kwargs:
                        self.nzeros=kwargs["nzeros"]
                    
                    ADprefix="MDAscan"+str.zfill(str(MDAscanNum),self.nzeros)+"_"
                    if kwargs['debug']:
                        print("ADprefix",ADprefix)
                        
                    ADallscanList=_dirScanNumList(ADpath,ADprefix,ADext)
                    if kwargs['debug']:
                        print("ADallscanList",ADallscanList)#Empty
                    
                    if len(ADallscanList)>0:
                        ADshortlist=_shortlist(0,inf,llist=ADallscanList,**kwargs)
                        kwargs.update({"MDAscanNum":MDAscanNum})
                        initialVals=[]
                        
                        #getting mda attr and setting for EA
                        for i,key in enumerate(["path","prefix","ext"]):
                            initialVals.append(getattr(self, key))
                            setattr(self,key,eval('AD'+key))
                        
                        if 'EA' in AD_dtype:
                            if kwargs['debug']:
                                print("Loading EA")
                            ADloadedList=self._eaIEXdata(ADshortlist,**kwargs) 
                        elif 'mpa' in AD_dtype:
                            if kwargs['debug']:
                                print("Loading mpa")
                            ADloadedList=self._MPAIEXdata(ADshortlist,**kwargs)
                        if kwargs['debug']:
                            print("\nADloadedList",ADloadedList)

                        #setting mda attr back
                        for i,key in enumerate(["path","prefix","ext"]):
                            initialVals.append(getattr(self, key))
                            setattr(self,key,initialVals[i])  
                
        if kwargs["q"] == False:
            print("Loaded "+self.dtype+" scanNums: "+str(loadedList))
        return self
    
    def _mdaIEXdata(self,shortlist,**kwargs):
        """
        loads mda files into IEXdata.mda dictionary
        """
       
        mdaNumList = list(self.mda.keys())    
        if kwargs["overwrite"] == False: #only load new scans
            shortlist =[x for x in shortlist if x not in mdaNumList]  
            
        if kwargs["debug"]:
            print("_mdaIEXdata shortlist: ",shortlist)

        #adding scanNums from shortlist to scanNomList without duplicates
        mdaNumList+= [x for x in shortlist if x not in mdaNumList]
        mdaNumList.sort()

        #create list of filename to load
        files2load = [self.prefix+str.zfill(str(x),self.nzeros)+self.suffix+"."+self.ext for x in shortlist]

        #adding fileNames to loadedFiles without duplicates
        self._mdaLoadedFiles += [x for x in files2load if x not in self._mdaLoadedFiles]
        self._mdaLoadedFiles.sort()        

        #load files and add to / update exp dictionary
        for (i,fname) in enumerate(files2load):
            ##### File info:
            fullpath=self.path+fname
            if kwargs["debug"] == True:
                print(fullpath)
            mda=nmda(fullpath,q=1)
            headerList=mda.header.ScanRecord
            headerList.update(mda.header.all)
            _mdaHeader_IEX(mda.header,headerList)
            self.mda.update({shortlist[i]:mda})
        return shortlist

    def _eaIEXdata(self,shortlist,**kwargs):
        """loads EA and EA_nc files into IEXdata.EA dictionary
        kwargs:
            if MDAscanNum == None -> EA only 
                          != None -> mdaEA 
            debug=True; to print extras info 
        """
        
        kwargs.setdefault("MDAscanNum",None)
        kwargs.setdefault("overwrite",False)
        kwargs.setdefault("debug",False) 
        
        if kwargs["debug"]:
            print('\nIEX_nData._eaIEXdata')
            print('self.dtype:',self.dtype)
            print('kwargs:\n',kwargs)
        EANumList = list(self.EA.keys())        
        if kwargs["overwrite"] == False: #only load new scans
            shortlist =[x for x in shortlist if x not in EANumList]  
        
        #adding scanNums from shortlist to scanNomList without duplicates
        EANumList+= [x for x in shortlist if x not in EANumList]
        EANumList.sort()

        #create list of filename to load
        files2load = [self.prefix+str.zfill(str(x),self.nzeros)+self.suffix+"."+self.ext for x in shortlist]
        #adding fileNames to loadedFiles without duplicates
        self._EALoadedFiles += [x for x in files2load if x not in self._EALoadedFiles]
        self._EALoadedFiles.sort()

        #load files and add to / update exp dictionary
        for (i,fname) in enumerate(files2load):
            ##### File info:
            fullpath=os.path.join(self.path,fname)
            if kwargs["debug"]:
                print("EA fullpath: ",fullpath)
            EA=nEA((fullpath),**kwargs)#nEA(fullpath,**kwargs)
            
            if 'MDAscanNum' in kwargs and kwargs['MDAscanNum'] != None:
                self.mda[kwargs['MDAscanNum']].EA.update({shortlist[i]:EA})
            else:
                self.EA.update({shortlist[i]:EA})
        return shortlist
                                
#    def _ADIEXdata(self, shortlist,**kwargs)     #FR commented out to compile
                                

    def update(self,*scans,**kwargs):
        """
        *scans =>
            scanNum: for a single scan
            inf: for all scans in directory
            first,last: for all files between and including first and last; last can be inf
            first,last,countby: to load a subset
            [scanNum1,scanNum2]: to load a subset of scans
        dtype = mda / EA / EAnc 
        
        **kwargs
            path = CurrentDirectory(dtype)
            prefix = SaveData or ADplugin 
            suffix = ""
            nzerors = number of digit; (4 => gives (0001))
            
            overwrite = True/False; if False, only loads unloaded data"  
            
            See nmda and nEA for additional kwargs
            
            Note: see nmda and nEA for additional dtype specific **kwargs
        """  
        kwargs.setdefault('overwrite',True)
        kwargs.setdefault('debug',False)

        for key in kwargs:
            if key in ['dtype','path','prefix','suffix','nzeros']:
                 setattr(self,key,kwargs[key])
            
        self._extractData(*scans,**kwargs)
        return  
        
    def info(self):
        """
        """
        print("mda scans loaded:")
        print("\t"+str(list(self.mda.keys())))
        print("EA scans loaded:")
        print("\t"+str(list(self.EA.keys())))
        
        for key in vars(self): 
            if key[0] != "_" and key not in ['mda','EA']: 
                print(key+": "+str(vars(self)[key]))

    def save(self, fname, fdir=''):
        """
        saves the IEXdata dictionary for later reloading
        h5 file
            group: mda => contains all the mda scans
                group: mda_scanNum
                    attr: fpath
                    group: header
                        attributes with header info
                    group: det 
                        nDataGroup for each detector
                    group: posx
                        nDataGroup for each x positioner
                    group: posy ...
                        nDataGroup for each y positioner
                        
            group: EA => contains all the EA scans
                group: EA_scanNum
                    attr: fpath
                    attr: mdafname
                    group: header
                        attributes with header ino
                    group: image 
                        nDataGroup for image
                    group: EDC
                        nDataGroup for EDC
                    group: MDC ...
                        nDataGroup for MDC
                    group: nData_ARPES
                        attr: hv, wk, thetaX, thetaY, angOffset, slitDir
                        dataset:KEscale,angScale
    
        """
        #opening the file
        if fdir=='':
            fdir = os.getcwd()

        fpath = os.path.join(fdir, fname+'.h5')
        print(fpath)

        if os.path.exists(fpath):
            print('Warning: Overwriting file {}.h5'.format(fname))
        h5 = h5py.File(fpath, 'w')
        h5.attrs['creator']= 'IEX_nData'
        h5.attrs['version']= 1.0
        
        #IEXdata_attrs
        IEXdata_attrs=['dtype','path','prefix','nzeros','suffix','ext']
        for attr in IEXdata_attrs:
            h5.attrs[attr]=getattr(self,attr)
   
        
        #mda
        gmda=h5.create_group('mda')
        for scanNum in self.mda:
            nd=self.mda[scanNum]
            name='mda_'+str(scanNum)
            nmda_h5Group_w(nd,gmda,name)


            
        #EA
        gEA=h5.create_group('EA')
        for scanNum in self.EA:
            nd=self.EA[scanNum]
            name="EA_"+str(scanNum)
            nARPES_h5Group_w(nd,gEA,name)


        h5.close()
        return

                
                
def remove(cls,*scans):
    """
    *scans =>
        scanNum: for a single scan
        inf: for all scans in directory
        first,last: for all files between and including first and last; last can be inf
        first,last,countby: to load a subset
        [scanNum1,scanNum2]: to load a subset of scans
    Usage:
        remove(mydata.mda,[234,235,299])
    """
    fullList=list(cls.keys())
    shortlist=_shortlist(*scans,llist=fullList)

    for key in shortlist:
        del cls[key]
    print("removed scans: "+str(shortlist) )
    return


def h5info(f):
    h5printattrs(f)
    for group in f.keys():
        print(group)
        h5printattrs(f[group])
            
            
def h5printattrs(f): 
    for k in f.attrs.keys():
        print('{} => {}'.format(k, f.attrs[k]))

def load_IEXnData(fpath):
    """
    Loads data saved by IEXnData.save
    
    """
    h5 = h5py.File(fpath, 'r')
   
    #IEXdata
    mydata=IEXdata()
    for attr in h5.attrs:
        setattr(mydata,attr,h5.attrs[attr])  
    
    #mda
    gmda=h5['mda']
    mdaLoaded=[]
    for scan in gmda.keys():
        scanNum=int(scan.split("_")[-1])
        mydata.mda[scanNum]=nmda_h5Group_r(gmda[scan])
        mdaLoaded.append(scanNum)  
    print("mda scans: "+str(mdaLoaded))
        
    #EA
    gEA=h5['EA']
    EAloaded=[]
    for scan in gEA.keys():
        scanNum=int(scan.split("_")[-1])
        mydata.EA[scanNum]=nARPES_h5Group_r(gEA[scan])
        EAloaded.append(scanNum)
        
    print("EA scans: "+str(EAloaded))
    h5.close()
    
    return mydata


