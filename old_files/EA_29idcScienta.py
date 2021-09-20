from epics import *
import numpy as np
from time import sleep



#-----------------------------------------------
#--- Beamline dependent PVs and definitions  ---
#-----------------------------------------------
P="29idcScienta:"
PHV=P+'HV:'
Pcam =P+'basler:cam1:'
savePlugin = P+"HDF1:"
statsPlugin = P+"Stats4:"
dtype = "h5"
#energy scaling
KEpix=0.0000845#*PE
KEwidth=0.1085#*PE


def _hv():
    hv=caget("29idmono:ENERGY_MON")
    return hv

#############################################################
########### Scienta python control functions ################
#############################################################

class Scienta:
    """
    Usage: 
        EA=Scienta()
        EA.get(); cagets all Scienta parameters and returns vars(EA); dictionary of variables
        EA.PE(),EA.KE(),EA.BE(),EA.LensMode()
    """
    
    def __init__(self):
        #High Voltage Setting
        self.PHV = PHV
        self._Pcam=Pcam
        self._savePlugin=savePlugin
        self._statsPlugin=statsPlugin
        
        self.dtype=dtype
        self.wk = None

        self.ElementSet = None #HV for XPS, LV for UPS

        self.LensMode = None
        self.PassEnergy = None
        self.KineticEnergy = None
        self.SpectraMode = None

        #Camera Settings
        self.ExpFrames = None
        self.Sweeps = 1 #here

        self.get()
        return  

    def get(self,q=1):
        """ 
        Gets the current Scienta parameters
        returns the dictionary for q!=1
        """
        for key in vars(self):
            if key not in ["PHV","_Pcam","_savePlugin","_statsPlugin","wk","ExpFrames","dtype","Sweeps"]:
                vars(self)[key]=caget(self.PHV+key+".VAL")
            if key  in ["LensMode","SpectraMode"]:
                vars(self)[key]=caget(self.PHV+key+".VAL",as_string=True)
            if key == "ExpFrames":
                vars(self)[key]=caget("29idcScienta:"+key+".VAL")
                #print(self.P,key,".VAL")
            if key == "wk":
                vars(self)[key]=caget(self.PHV+"WorkFunction")
        if q !=1:
            for key in vars(self):
                print(key+" = "+str(vars(self)[key]))

        return vars(self)

    def counts():
        """
        returns the current intensity on the Scienta using EA.
        """
        return caget(self._savePlugin+"Total_RBV")

    def _errorCheck(self,parms):
        """
        check the parameters to see if they are allowed
        returns list of errors
        """
        error=[]
        #checkList=["ElementSet","LensMode","PassEnergy","KineticEnergy","ExpFrames"]
        for check in parms:
            #if check == "ElementSet":
                #if parms[check] != "None":
                    #error.append("ElementSet is not set to (0:\"HV\" or 1:\"LV\")")  
            if check == "LensMode":
                if parms["LensMode"] not in ["Transmission", "Angular", "Angular_01", "Angular_05"]:
                    error.append("LensMode = "+parms["LensMode"]+" is not a valid")
            if check == "PassEnergy":
                if parms[check] not in [1,2,5,10,20,50,100,200,500]:
                    error.append("PassEnergy = "+str(parms["PassEnergy"])+" is not a valid")
            if check =="KineticEnergy":
                if parms[check] is None:
                    error.append("Specify a Kinetic Energy")
            if check == "ExpFrames":
                if parms["ExpFrames"] < 1:
                    error.append("Frames must be 1 or greater")
        return error

    def put(self, KE=None, PE=None, LensMode="Angular",debug=False):
        """
        Used to set all the SES parameters at once
        KE = kinetic energy (None keeps the current KE)
        PE = pass energy (None keeps the current PE)
        LensMode = "Angular"/"Transmission"
        """
        parms=self.get()
        if KE != None:
            parms.update({"KineticEnergy":KE})
        if PE != None:
            parms.update({"PassEnergy":PE})
        parms.update({"LensMode":LensMode})
        if debug:
            print(parms)
            self._setHV(parms,q=0)
        else:
            self._setHV(parms)
        
    def _setHV(self,parms,q=1):
        """
        Sets the Scienta high voltage supplies
        parms is a dictionary of the Scienta parameters 
        print the dictionary for q!=1
        """

        KEcurrent=caget(self.PHV+"KineticEnergy")
        error=self._errorCheck(parms)
        if len(error) == 0:
            HVset=["LensMode","PassEnergy","KineticEnergy"]#order of setting -- LensMode and PassEnergy do not take effect until KE is changed 
            #for key in HVset:
            #    if key != "KineticEnergy":
            #        caput(self.PHV+key,parms[key])
            #        sleep(0.25)
            #    else:
            #        if(KEcurrent != parms[key]):
            #            caput(self.PHV+key,parms[key])
            #        else:
            #            caput(self.PHV+key,parms[key]+0.001)
            #            sleep(0.25)
            #            caput(self.PHV+key,parms[key])
            caput(self.PHV+"LensMode",parms["LensMode"])
            caput(self.PHV+"PassEnergy_Set",str(parms["PassEnergy"]))
            sleep(0.25)
            if(KEcurrent == parms["KineticEnergy"]): #KEs are the same then need to update KE for changes to take effect
                caput(self.PHV+"KineticEnergy",parms["KineticEnergy"]+0.001)
                sleep(0.25)
            caput(self.PHV+"KineticEnergy",parms["KineticEnergy"])
    
            self.get()
            if q !=1:
                for key in vars(self):print(key+" = "+str(vars(self)[key]))

        else:
            for e in error:
                print(e)

        return        

    def off(self):
        """
        Zeros the high voltage supplies
        """
        self.zeroSupplies()

    def zeroSupplies(self):
        """
        Zeros the Scienta HV supplies (safe-state)
        """
        caput(self.PHV+"ZeroSupplies.RVAL",1)
        caput(self.PHV+"ZeroSuppliesSeq.PROC",1)


    def KE(self,val):
        """
        Sets the kinetic energy of the Scienta
        KE should be grearter than the PassEnergy 
        """
        parms=self.get()
        parms.update({"KineticEnergy":val})
        self._setHV(parms)


    def BE(self,val,wk=None):
        """
        Converts binding energy to kinetic energy based on the current mono
        energy and set the kinetic energy of the Scienta with work function 
            if wk is None then wk = EA.wk()

        negative binding energies are above EF
        BE maximum should be hv-5-PE
        """
        if wk is None:
            wk = self.wk
        hv=_hv()
        KE=hv-wk-val
        parms=self.get()
        parms.update({"KineticEnergy":val})
        self._setHV(parms)

    def _setwk(self,val):
        """
        Sets the wk to the value specified
        """
        caput(self.PHV+"WorkFunction",val)

    def PE(self,val):
        """
        Sets the pass energy of the Scienta
        PassEnergy: 1, 2, 5, 10, 20, 50, 100, 200, 500
        """
        parms=self.get()
        parms.update({"PassEnergy":val})
        self._setHV(parms)

    def lensMode(self,val):
        """
        Sets the pass energy of the Scienta
        LensMode: 'Transmission','Angular','Angular_01','Angular_05'
        """
        parms=self.get();print(val)
        parms.update({"LensMode":val})
        self._setHV(parms)

    def _frames(self,val,q=1):
        """
        Sets the number of frames
        Frames >=1
        """
        caput("29idcScienta:"+"ExpFrames.VAL",val)
        self.get()
        if q !=1:
            for key in vars(self):print(key+" = "+str(vars(self)[key]))
        return  

    def _ElementSet(self,mode,q=1):
        """
        Used to switch between 
        0: High Energy (XPS) and 1:Low Energy (UPS) mode
        Must be done in conjunction with changing the cabling on the front of the HV supply
        mode = 0 or 1
        """
        caput(self.PHV+"ElementSet",mode)
        self.get()
        if q !=1:
            for key in vars(self):print(key+" = "+str(vars(self)[key]))
        return  

        
    def _BurstSupplies(self,val):
        """
        BurstSupplies:'Fast','Slow'
        """
        caput(self.PHV+"BurstSupplies",val,as_string=True)

    def _AcqCalc(self,val):
        """
        AcqCalc:'Off','Live','Scan'
        """
        caput(self.PHV+"AcqCalc",val,as_string=True)

    def _AcquisitionMode(self,val):
        """
        AcquisitionMode: 'Off','Scan','Spectra'
        """
        caput(self.PHV+"AcquisitionMode",val)

    def _ScientaMode(self,val):
        """
        ScientaMode: 'BetaScan','XYScan','Fixed','BabySweep','SweepOverlapping','SweepNo'
        """
        caput(self.PHV+"ScientaMode",val,as_string=True)
    
    
    def _babySweepSteps(self,val):
        """
        sets the number of steps in baby sweep
        """
        caput(self.PHV+"babySweepSteps.VAL",val)

    def _spectraStatus(self):
        """
        checking the spectra status
        returns 1=busy or 0=idle
        """
        status=caget(self.PHV+'ScanTrigger')
        return status

    def _spectraProgress(self):
        """
        Monitors the spectra status every 30 seconds
        returns 0 when the spectra scan is idle
        """
        while True:
            status=self._spectraStatus()
            if (status==1):
                sleep(30)
            else:
                break
        return 0

    def _spectraInfo(self):
        """
        returns the pertainent information for a given spectra type
            modeNum=2; Swept=[start,stop,step]
        """
        modeNum=caget(self.PHV+"SpectraMode")
        scanType=caget(self.PHV+"SpectraMode",as_string=True)
        info=[]
        if modeNum==2: #swept
            info.append(caget(self.PHV+"sweepStartEnergy"))
            info.append(caget(self.PHV+"sweepStopEnergy"))
            info.append(caget(self.PHV+"sweepStepEnergy"))
        elif modeNum==1: #baby-swept
            info.append(caget(self.PHV+"babySweepCenter.VAL"))
        elif modeNum==0: #fixed
            info.append(caget(self.PHV+"fixedEnergy.VAL"))
        return scanType,info

    def live(self,KE=None,PE=None,LensMode="Angular"):
        """
        puts the Scienta back in live mode (no savinga and Fixed Mode) with PE and KE
            if PE or KE is None then uses the current value
        """
        if self.spectraProgress() != 1:
            parms=self.get()
            caput('29idcScienta:HV:LiveSeq',1)
            self.put(KE,PE,LensMode)
        else:
            print("Scienta spectra in progress")
            
    def _updateAttributes(self,filepath=None):
        """
        filepath is the full path to the xml file
            filepath = None; to update after making changes
            filepath='/xorApps/epics/synApps_6_1/ioc/29idcScienta/iocBoot/ioc29idcScienta/HDF5Attributes.xml'

        from 29idcScienta:HDF1: screen
            More (under process plugin)
                NDPluginBase Full
        """
        if filepath is None:
            print(caget(self._savePlugin+"NDAttributesFile",as_string=True))
        else:
            caput(self._savePlugin+"NDAttributesFile",filepath)
            sleep(1)
            print(caget(self._savePlugin+"NDAttributesStatus",as_string=True))

    def _spectra_HV_parameters(self,KE,PE,frames):
        """
        setting the analyzer parameters before a spectra
        """
        caput(self.PHV+"LensMode","Angular")
        caput(self.PHV+"PassEnergy_Set",PE)
        sleep(0.25)
        caput(self.PHV+"KineticEnergy",KE)
        caput("29idcScienta:"+"ExpFrames.VAL",frames)
        sleep(1)

    def _spectra_Swept(self,start,stop,step, PE, frames):
        """
        setting up for a swept spectra
        """
        #setting SpectraMode
        caput(self.PHV+"SpectraMode", "Sweep")
        sleep(1)
        #input spectra parameters
        self._spectra_HV_parameters(start,PE,frames)
        caput(self.PHV+"sweepStartEnergy.VAL",start)
        caput(self.PHV+"sweepStopEnergy.VAL",stop)
        caput(self.PHV+"sweepStepEnergy.VAL",step)
        sleep(1)
        #Re-Calc
        caput(self.PHV+"SweepReCalc.PROC",1)
        sleep(1)
        #Load spectra parameters
        caput(self.PHV+"SweepLoadFanout.PROC",1)
        sleep(1)


    def _spectra_BabySwept(self, KE_center,PE,frames):
        """
        setting up for a Baby-Swept
        """
        #setting SpectraMode
        caput(self.PHV+"SpectraMode", "Baby-Sweep")
        sleep(1)
        #input spectra parameters
        self._spectra_HV_parameters(KE_center,PE,frames)
        caput(self.PHV+"babySweepCenter.VAL",KE_center)
        sleep(1)
        #Load spectra parameters
        caput(self.PHV+"SweepLoadFanout.PROC",1)
        sleep(1)
        #settling time
        caput(self.PHV+"scan2.PDLY",0.25)
        caput(self.PHV+"scan2.DDLY",0.1)

    def _spectra_Fixed(self,KE_center,PE,frames):
        """
        setting up for Fixed
        """
        #setting SpectraMode
        caput(self.PHV+"SpectraMode", "Fixed")
        caput("29idcScienta:HV:SpectraMode", "Fixed")
        sleep(1)
        #input spectra parameters
        self._spectra_HV_parameters(KE_center,PE,frames)
        caput(self.PHV+"fixedEnergy.VAL",KE_center)
        sleep(1)
        
    def _spectraSetup(self,EAlist):
        """ 
        Writes EAlist to the appropriate PVs and does error checking
        
        For now any BE scans are taken care of in  ScanFunction_EA.py
        but will eventually go into the Scienta IOC and then this will
        need to be modified
        """
        scantype="spectra"
        if EAlist[-1] == "BS":
            BS=True
            EAlist=EAlist[0:-1]
        else: 
            BS=False
        Sweeps=EAlist[-1]
        Frames=EAlist[-2]
        PassEnergy=EAlist[-3]
        EnergyMode=EAlist[0]
        KElist=np.array(EAlist[1:len(EAlist)-3])
        if EAlist[0] == "BE": 
            KElist[0:-1]=_hv()-self.wk-KElist[0:-1]
        #checking parameters are valid
        parms=self.get() 
        error=[]
        for i in range(0,len(KElist)):
            parms.update({"PassEnergy":PassEnergy,"ExpFrames":Frames,
                          "LensMode":"Angular","KineticEnergy":KElist[i]-0.001})
            error=[]#self._errorCheck(self,parms) #JM
        if len(error) > 0:
            for e in len(error): 
                print(e)
        # writing scan parameters
        elif len(error) == 0: #passed check
            #Checking Progress
            if self._spectraStatus() == 1:
                print("Spectra in Progess")
            else:
                #Swept Mode
                if len(EAlist)==7: 
                    scantype="Sweep"
                    self._spectra_Swept(np.min(KElist[0:2]),np.max(KElist[0:2]),KElist[2], PassEnergy, Frames)
                    #fixed or baby sweep
                elif len(EAlist)==5: 
                    if BS is True:
                        scantype="Baby-Sweep"
                        self._spectra_BabySwept(KElist[0],PassEnergy,Frames)
                    else:
                        scantype="Fixed"
                        self._spectra_Fixed(KElist[0],PassEnergy,Frames)
                else:
                    print("not a valid number of parameters")
                "PV to initate scan"
                scanPV=self.PHV+"ScanTrigger"
            return scantype, scanPV, KElist

    def _spectraMessage(self,scantype, scanPV, KElist):
        """
        prints KE range for spectra
        """
        message=str(scantype)+" scan  KE: "
        for KE in KElist:
            message+=str(KE)+" | "
        return message[0:-2]
    
       

    def spectra(self,EAlist,run=True):
        """
        takes a Scienta spectra based on the number or parameters in EAlist
        LensMode = "Angular"
        Sweeps are handled by scanRecord outside of this modual (see scanEA)
        Fixed Mode:["KE"/"BE",CenterEnergy,PassEnergy,Frames,Sweeps] (5)
        Swept Mode:["KE"/"BE",StartEnergy,StopEnergy,StepEnergy,PassEnergy,Frames,Sweeps] (7)
        Baby Sweep (dither):["KE"/"BE",CenterEnergy,PassEnergy,Frames,Sweeps,"BS"] (6)

            (+) BE is positive below Ef
            (-) BE is negative above Ef
        """
        
        #Sending Parmeters to _spectraSetup
        scanType,scanPV, KElist =self._spectraSetup(EAlist)
        print(scanType,scanPV, KElist)
        #Getting Filename info
        fpath=caget(self._savePlugin+"FileName_RBV",as_string=True)+"_ "
        fnum=caget(self._savePlugin+"FileNumber",as_string=True)
       
        
        if run is True:
            dateandtime=time.strftime("%a %d %b %Y %H:%M:%S",time.localtime())
            print("\t"+fpath+fnum+" started at ",dateandtime,"\r")
            caput(scanPV,1,wait=True,timeout=129600)#timeout=36 hours
            dateandtime=time.strftime("%a %d %b %Y %H:%M:%S",time.localtime())
            print("\t"+fpath+fnum+" finished at ",dateandtime,"\r")


