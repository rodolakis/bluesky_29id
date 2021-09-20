
#nEA.py 
#loads h5 and netCDF EA data using to the form used by (pynData.py)

__version__= 1.0      #JLM 4/27/2021

import re
import numpy as np
import h5py
import netCDF4 as nc

from .pynData import nData
from .pynData_ARPES import nARPES


class nEA:
    """
    nARPES class for IEX beamline
    """
    def __init__(self,*fpath,**kwargs):
        """ 
        Loads and scales data for the EA
        and returns an nData object with appropriate meta data
        kwargs:
            dtype: nc => for old Scienta driver pre-2021 
                   h5 => new new Scienta driver 
            nzeros: minimum number of digits in the file name (e.g. EA_0001.nc => nzeros=4 )
            source: string used for book keeping only
            centerChannel: center energy pixel in fixed mode
            firstChannel: 0 unless using an ROI
            degPerPix: angle scaling, (degrees per pixel)
            cropStart: used to crop the angle if not using using ROI to do so
            cropStop: used to crop the angle if not using using ROI to do so
            
            kwargs:
                crop = True (default); crops the data so that only the ROI is load
                     = False; full image
                rawData = False (default); uses the meta data to scale KE and degree
                        = True; camera pixels
        """ 
        kwargs.setdefault('debug',False)
        self.fpath=''
        
        if kwargs['debug']:
            print("\nEA")

        if fpath:
            if kwargs['debug']:
                print("fpath: ",fpath)
            self.fpath=fpath[0]
            EA=self._extractEA(**kwargs)
            varList=vars(EA)
            for key in varList:
                setattr(self, key, varList[key])
            
        else:
            pass        

    def _extractEA(self,**kwargs):
        """
        loads data and returns a nARPES object 
        q=1; quiet if q=0 then printing for debug purposes
        """
        kwargs.setdefault("debug",False)
        kwargs.setdefault("dtype","h5")
        kwargs.setdefault("nzeros",4)
        kwargs.setdefault("source","")
        kwargs.setdefault("centerChannel",512)
        kwargs.setdefault("firstChannel",318-35)
        kwargs.setdefault("degPerPix",0.03)
        kwargs.setdefault("cropStart",318)
        kwargs.setdefault("cropStop",780)
        kwargs.setdefault("source","")
        
        kwargs.setdefault("crop",True)
        kwargs.setdefault("rawData",False)
        if kwargs['debug']:print(self.fpath)

        #metadata will carry around all the various parameters needed
        metadata=kwargs

        fpath=self.fpath
        filename=fpath.split("/")[-1]
        filepath=fpath[:-len(filename)],
        prefix=filename.split("_")[0],
        dtype=filename.split(".")[-1]
        scanNum=int(re.sub("[^0-9]", "", filename.split(".")[0]))
        fileInfo={"filename":filename,
                  "filepath":filepath,
                  "prefix":prefix,
                  "dtype":dtype,
                  "scanNum":scanNum
                 }
        metadata.update({"fileInfo":fileInfo})
        metadata.update({'fpath':fpath})
        if kwargs['debug']:
            print("\nEA._extractEA")
            print("metadata:")
            print(metadata)
        
        #loading the data and copying spectra info into metadata
        if dtype=="h5":
            d = h5py.File(fpath, 'r')
            data = np.array(d['entry']['instrument']['detector']['data'])#(y=energy,x=angle)
            metadata.update(nEA._h5PVs_EA(d,**kwargs))
            if kwargs['debug']==True:
                print("data shape:",np.shape)
        elif dtype == "nc":
            d = nc.Dataset(fpath,mode='r')
            data = d.variables["array_data"][:][0]
            md=nEA._ncPVs_EA(d)
            metadata.update(nEA._ncPVs_EA(d)) 
            if kwargs['debug']==True:
                print("data shape:",np.shape)
        else:
            print(dtype+" is not a valid dtype")
        
        #scaling and cropping
        if kwargs["crop"] == True:
            #cropping the data #(y=energy,x=angle) 
            EA=nData(data[metadata["cropStart"]:metadata["cropStop"],:])
            if kwargs['debug']==True:
                print("cropping data")
        else:
            EA=nData(data)

        if kwargs["rawData"] == False:
            if kwargs['debug']==True:
                print("scaling data")
            nEA._EAscaling(EA,metadata,**kwargs)
            
        #Calculating EDC/MDC
        EDC = nData(np.nansum(EA.data[:,:], axis=0))
        ax=list(EA.scale)[0]
        EDC.updateAx('x',EA.scale[ax],EA.unit[ax])
        
        MDC = nData(np.nansum(EA.data[:,:], axis=1))
        ax=list(EA.scale)[1]
        MDC.updateAx('x',EA.scale[ax],EA.unit[ax])
        
        metadata.update({"KEscale":EA.scale['x'],"angscale":EA.scale['y']})
        metadata.update({'EDC':EDC})
        metadata.update({'MDC':MDC})
        
        spectraInfo={
                'lensMode':metadata['lensMode'],
                'acqMode':metadata['acqMode'],
                'passEnergy':metadata['passEnergy'],
                'frames':metadata['frames'],
                'sweeps':metadata['sweeps']
                }
        if metadata['acqMode']==0:
            spectraInfo.update({'sweptStart':metadata["sweptStart"],
                                'sweptStop':metadata["sweptStart"]+metadata["sweptStep"]*np.size(MDC.data),
                                'sweptStep':metadata["sweptStep"]})
        elif metadata["acqMode"] > 0: #Fixed=1, BabySweep=2
             spectraInfo.update({'kineticEnergy':metadata['kineticEnergy']})
        metadata.update({'spectraInfo':spectraInfo})
        
        #Make nData_ARPES object
        nARPES(EA,metadata)
        #_nARPES_header(metadata)
        EA.extras['scanNum']=scanNum
        if kwargs['debug']==True:
            print(type(EA))

        for key in metadata:
            setattr(d, key, metadata[key])
        return EA
    
    def _ncPVs_EA(d,**kwargs):
        """ 
        gets the meta data associated with a given hdf5 file, d
        """
        kwargs.setdefault("debug",False)
        metadata={}
        PVs={
                "sweptStart":"LowEnergy",
                "sweptStep":"EnergyStep_Swept",
                "kineticEnergy":"CentreEnergy_RBV",
                "energyPerPixel":"EnergyStep_Fixed_RBV",
                "lensMode":"LensMode", 
                "acqMode":'AcquisitionMode',
                "passEnergy":'PassEnergy',
                "frames":'Frames',
                "sweeps":'NumExposures_RBV',
                "wk":"Energy Offset",
                }
        for key in list(PVs.keys()):
            if kwargs["debug"]:
                    print(key)
            if 'Attr_'+PVs[key] in d.variables.keys():
                if "debug" in kwargs and kwargs["debug"]:
                    print({key:d.variables['Attr_'+PVs[key]][:][0]})
                metadata.update({key:d.variables['Attr_'+PVs[key]][:][0]})
            else:
                metadata.update({key:None})
                if kwargs["debug"]:
                    print({key:d.variables['Attr_'+PVs[key]][:][0]})
            key='lensMode'; strList=['Transmission','Angular']
            #metadata.update({key:strList[metadata[key]]})
           
    
        
    def _h5PVs_EA(d,**kwargs):
        """ 
        gets the meta data associated with a given hdf5 file, d
        """
        kwargs.setdefault("debug",False)
        metadata={}
        #getting spectra mode
        SpectraMode=d['entry']['instrument']['NDAttributes']["SpectraMode"][0]
        if kwargs["debug"]:
            ScientaModes=["Fixed","Baby-Sweep","Sweep"]
            print("SpectraMode: ",SpectraMode, ScientaModes[SpectraMode])
        PVs={}
        #Fixed        
        if SpectraMode==0: 
            PVs={"kineticEnergy":"fixedEnergy",
                 "energyPerPixel":"babySweepStepSize"
                }

        #Baby-Swept
        elif SpectraMode==1:
            PVs={"kineticEnergy":"babySweepCenter",
                 "energyPerPixel":"babySweepStepSize"
                }
        
        #Swept
        elif SpectraMode==2:
            PVs={"sweptStart":"sweepStartEnergy",
                 "sweptStep":"sweepStepEnergy",
                 "kineticEnergy":"KineticEnergy"
                }
                
        AnalyzerPVs={"lensMode":"LensMode",
                     "acqMode":'SpectraMode',
                     "passEnergy":'PassEnergy',
                     "frames":'ExpFrames',
                     "sweeps":'Sweeps',
                     "wk":"ScientaWorkFunction",
                    }
        PVs.update(AnalyzerPVs)
        if kwargs["debug"]:
            print("PVs: ",PVs)
        #getting the metadata
        for key in PVs:
            if PVs[key] in list(d['entry']['instrument']['NDAttributes'].keys()):
                metadata.update({key:d['entry']['instrument']['NDAttributes'][PVs[key]][0]})
            else:
                metadata.update({key:None})
        
        #Scienta driver uses a different state notation make (swept=0,fixed=1,BS=2)
        key='acqMode';strList=[2,1,0]
        metadata.update({key: strList[metadata[key]]}) 
        if kwargs["debug"]:
            print("metadata:",metadata)
        return metadata
    
    def _EAscaling(EA,metadata,**kwargs):
        """
        Scales IEX EA data
        """
        kwargs.setdefault("debug",False)
        #Set energy scale ("KE") (IOC only does DetectorMode=1) Note: acqMod is not the same as SpectraMode
        if metadata["acqMode"] == 0: #Swept=0
            Estart=metadata["sweptStart"]
            Edelta=metadata["sweptStep"]
        if metadata["acqMode"] > 0: #Fixed=1, BabySweep=2
            Estart=metadata["kineticEnergy"]-(EA.data.shape[1]/2.0)*metadata["energyPerPixel"]
            Edelta=metadata["energyPerPixel"]
    
        Escale=[Estart+Edelta*i for i,e in enumerate(EA.data[0,:])]
        Eunits="Kinetic Energy (eV)"
    
        #Set angle scale 
        angStart = (metadata["firstChannel"]-metadata["centerChannel"])*metadata["degPerPix"]
        angScale=[angStart+metadata["degPerPix"]*i for i,e in enumerate(EA.data[:,0])]
        angUnits="Degrees"
    
        #pynData data.shape = (y=angle,x=energy) 
        EA.updateAx('x',Escale,Eunits)
        EA.updateAx('y',angScale,angUnits)
    
