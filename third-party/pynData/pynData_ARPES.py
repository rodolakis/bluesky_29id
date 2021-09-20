#==============================================================================
#==============================================================================
# Domain specific applications - ARPES extensions for pynData
#      Data Format (data.shape = (z,y,x))
#          Axis x:  Energy (eV)
#          Axis y:  Angle (Degrees)
#          Axis z:  Scan axis (Theta, hv, Beta ...)
#
#       .KEscale:   original KE scale
#       .angScale:  original angle scale of detector
#       .angOffset: offset of orignal angular scaling, used for book keeping
#       .slitDir:   slit direction, 'H' or 'V'
#       .thetaX:    polar angle
#       .thetaY:    other angle
#       .hv:        photon energy in eV
#       .wk:        work function of analyzer in eV, setWk(d,val) to update-
#       .EDC        angle integrated pynData object
#       .MDC        energy integrated pynData object
#==============================================================================

#==============================================================================
# imports
#==============================================================================
import numpy as np
from .pynData import nData

#==============================================================================
# Global variables in science
#==============================================================================

kB = 8.6173423e-05          # Boltzmann k in eV/K
me = 5.68562958e-32         # Electron mass in eV*(Angstroms^(-2))*s^2
hbar = 6.58211814e-16       # hbar in eV*s
hc_over_e = 12.3984193      # hc/e in keV⋅A
hc_e = 1239.84193           # hc/e in eV*A

###############################################################################################
class _nARPES_header:
    def __init__(self,metadata):
        """
        mda header information
        """
        self.fpath=metadata['fpath']
        self.spectraInfo=metadata['spectraInfo']
        
        
class nARPES:
    def __init__(self,d,metadata):
        """
        self is an pynData object and we will add the following attribute from the metadata dictionary
            'KEscale':[],     # original KE scale
            'angScale':[],    # original angle scale of detector
            'angOffset':0     # offset of orignal angular scaling, used for book keeping
            'slitDir':'V'     # slit direction, 'H' or 'V'
            'thetaX':0,       # polar angle
            'thetaY':0,       # other angle
            'hv':22.0,        # photon energy in eV
            'wk':4.0,         # work function of analyzer in eV, setWk(d,val) to update
            ---------------- add by hand -----------------------
            'EDC'/'MDC':      # pynData EDC/MDC data
        """
       
        
        metadata.setdefault("KEscale",[])
        metadata.setdefault("angScale",[])
        metadata.setdefault("angOffset",0)
        metadata.setdefault("slitDir",'V')
        metadata.setdefault("thetaX",0)
        metadata.setdefault("thetaY",0)
        metadata.setdefault("hv",22.0)
        metadata.setdefault("wk",4.0)
        metadata.setdefault("EDC",nData(np.empty(1)))
        metadata.setdefault("MDC",nData(np.empty(1)))
        metadata.setdefault("wk",4.0)
        for key in metadata:
            setattr(d, key, metadata[key])
                   
    #==============================================================================
    # converting between KE and BE scaling
    #==============================================================================
    def scaleKE(self,ax='x'):
        """
        sets the scaling of the specificed axis to original KE scaling
        also sets the EDC scaling to the orginal KE scaling
        """
        self.updateAx(ax,np.array(self.KEscale),"Kinetic Energy (eV)")
        self.EDC.updateAx(ax,np.array(self.KEscale),"Kinetic Energy (eV)")
    
    
    def scaleBE(self,ax='x',wk=None, hv=None):
        """
        sets the scaling of the specificed axis to original BE scaling
        also sets the EDC scaling to the orginal BE scaling
        where BE = hv - KE - wk (above EF BE is negative); KE is orginal KE scaling
            wk=None uses  .wk for the work function (wk ~ hv - KE_FermiLevel)
            hv=None uses  .hv for the photon energy
    
        """
        if wk is None:
            wk=self.wk
        if hv is None:
            hv=self.hv
        KE=np.array(self.KEscale)
        BE=hv-wk-KE
        self.updateAx(ax,BE,"Binding Energy (eV)")
        self.EDC.updateAx(ax,BE,"Binding Energy (eV)")
    
    def set_wk(self,val):
        """
        updates the work function can be a single value or an array of the same length as KE
        """
        self.wk(val)
    
    def scaleAngle(self,ax='y',delta=0):
        """
        changest the angle scaling of the data and the MDC
        based on the orginal angle scale and angOffset
            newScale = angScale + angOffset + delta;
            delta=(newCoor-oldCoor); can be value or an array of the same length as angScale
        
        """
        angScale=np.array(self.angScale)
        newScale= angScale + angOffset + delta
        self.updateAx(ax,newScale,"Angle (deg)")
        self.EDC.updateAx(ax,newScale,"Angle (deg)")
    
    #==============================================================================
    # converting to and from k-space
    #==============================================================================
    
    def theta_to_k(KE, thetaX, thetaY, V0=10):
        '''
        thetaX = polar angle
        thetaY = other angle
        V0=inner potential
        kx = c*sqrt(KE)*sin(thetaX)
        ky = c*sqrt(KE)*cos(thetaX)*sin(thetaY)
        kz = c*sqrt(V0-KE*(sin(thetaX)+cos(thetaX)*sin(thetaY)+1))
        '''
        c = np.sqrt(2*me)/hbar
        kx = c*np.sqrt(KE)*np.sin(thetaX*np.pi/180.)
        ky = c*np.sqrt(KE)*np.cos(thetaX*np.pi/180.)*np.sin(thetaY*np.pi/180.)
        kz = c*np.sqrt(V0-KE*(np.sin(thetaX)+np.cos(thetaX)*np.cos(thetaY)+1))
    
        return kx, ky, kz
    
    
    
###############################################################################################

def plotEDCs(*d,**kwargs):
    '''
    Simple plot for EDCs
    *d, set of pynData_ARPES data
    
    kwargs:
        Escale="KE" or "BE"; changes the energy scale using the hv and wk from the meta data
        hv = val; if not specified uses the one from the meta data
        wk = val; if not specified uses the one from the meta data
        
    plt.legend() after script to show legend of scanNum
    '''
    for di in list(d):
        kwargs.setdefault('hv',None)
        kwargs.setdefault('wk',None)
        if "Escale" in kwargs:
            if str(kwargs["Escale"]) == "KE":
                setscaleKE(di)
            elif str(kwargs["Escale"]) == "BE":
                setscaleBE(di,hv=kwargs['hv'],wk=kwargs['wk'])
                
        plt.plot(di.EDC.scale['x'], di.EDC.data,label=di.extras['scanNum'])
        plt.xlabel(di.EDC.unit['x'])
    return
###############################################################################################
        
##########################################
# generalized code for saving and loading as part of a large hd5f -JM 4/27/21
# creates/loads subgroups    
##########################################
def nARPES_h5Group_w(nd,parent,name):
    """
    for an nData object => nd
    creates an h5 group with name=name within the parent group:
        with all ndata_ARPES attributes saved                   
    """
    #saving ndata array
    g=nData_h5Group_w(nd,parent,name)
    
    #EDC/MDC
    nData_h5Group_w(nd.EDC,g,"EDC")
    nData_h5Group_w(nd.EDC,g,"MDC")
    
    for attr in ['hv','wk','thetaX','thetaY','KEscale','angScale','angOffset']:
        if type(getattr(nd,attr)) == type(None):
            g.create_dataset(attr, data=np.array([]) , dtype='f')
        else:
            g.create_dataset(attr, data=np.array(getattr(nd,attr)) , dtype='f')
    for attr in ['slitDir']:
        g.attrs[attr]=str(getattr(nd,attr))
    return g

def nARPES_h5Group_r(h):
    """           
    """
    d=nData_h5Group_r(h)
    
    #EDC/MDC
    d.EDC=nData_h5Group_r(h['EDC'])
    d.MDC=nData_h5Group_r(h['MDC']) 
    
    
    #val=ast.literal_eval(h5['mda']['mda_'+str(scanNum)]['header'][hkey].attrs[key])
    for attr in ['hv','wk','thetaX','thetaY','KEscale','angScale','angOffset']:
        setattr(d,attr,h[attr])
    for attr in ['slitDir','fpath']:
        if attr in h.attrs:
            setattr(d,attr,ast.literal_eval(h.attrs[attr]))
    return d   
            
