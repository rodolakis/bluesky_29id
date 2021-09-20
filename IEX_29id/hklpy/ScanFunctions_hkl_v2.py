####### load the hklpy package
import gi
gi.require_version('Hkl', '5.0')
#from hkl.diffract import E4CV, E4CH  #this works for mu=0
from hkl.geometries import E4CV, E4CH, SimulatedE4CV, SimulatedK4CV  #this works for mu=0
from hkl.util import Lattice
from hkl.user import *
from hkl.diffract import Constraint
# need these to connect with our motors and then diffractometer
from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent
from ophyd import PseudoSingle
from ophyd import PVPositioner
from ophyd import SoftPositioner
from epics import caput
from epics import caget
from ScanFunctions_IEX import Lambda2eV
from ScanFunctions_IEX import eV2Lambda
from ScanFunctions_IEX import EtoK


# get some diffractometer support from https://github.com/BCDA-APS/use_bluesky/blob/master/lessons/instrument/devices/TODO/diffractometer.py

"""add to capabilities of any diffractometer"""
import collections
import pyRestTable

# AxisConstraints = collections.namedtuple(
#     "AxisConstraints", 
#     ("low_limit", "high_limit", "value", "fit"))


# class DiffractometerMixin(Device):
#     """
#     add to capabilities of any diffractometer
#     Provides:
    
#     * applyConstraints()
#     * resetConstraints()
#     * showConstraints()
#     * undoLastConstraints()
#     * forwardSolutionsTable()
#     """
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._constraints_stack = []

#     def applyConstraints(self, constraints):
#         self._push_current_constraints()
#         self._set_constraints(constraints)

#     def resetConstraints(self):
#         """set constraints back to initial settings"""
#         if len(self._constraints_stack) > 0:
#             self._set_constraints(self._constraints_stack[0])
#             self._constraints_stack = []

#     def showConstraints(self):
#         tbl = pyRestTable.Table()
#         tbl.labels = "axis low_limit high_limit value fit".split()
#         for m in self.real_positioners._fields:
#             tbl.addRow((
#                 m,
#                 *self.calc[m].limits,
#                 self.calc[m].value,
#                 self.calc[m].fit))
#         print(tbl)

#     def undoLastConstraints(self):
#         if len(self._constraints_stack) > 0:
#             self._set_constraints(self._constraints_stack.pop())

#     def _push_current_constraints(self):
#         constraints = {
#             m: AxisConstraints(
#                 *self.calc[m].limits,
#                 self.calc[m].value,
#                 self.calc[m].fit)
#             for m in self.real_positioners._fields
#             # TODO: any other positioner constraints 
#         }
#         self._constraints_stack.append(constraints)

#     def _set_constraints(self, constraints):
#         for axis, constraint in constraints.items():
#             self.calc[axis].limits = (constraint.low_limit, constraint.high_limit)
#             self.calc[axis].value = constraint.value
#             self.calc[axis].fit = constraint.fit

#     # calculate using the current UB matrix & constraints
#     def forwardSolutionsTable(self, reflections, full=False):
#         """
#         return table of computed solutions for each of supplied hkl reflections
#         """
#         _table = pyRestTable.Table()
#         motors = self.real_positioners._fields
#         _table.labels = "(hkl) solution".split() + list(motors)
#         for reflection in reflections:
#             try:
#                 solutions = self.calc.forward(reflection)
#             except ValueError as exc:
#                 solutions = exc
#             if isinstance(solutions, ValueError):
#                 row = [reflection, "none"]
#                 row += ["" for m in motors]
#                 _table.addRow(row)
#             else:
#                 for i, s in enumerate(solutions):
#                     row = [reflection, i]
#                     row += [f"{getattr(s, m):.5f}" for m in motors]
#                     _table.addRow(row)
#                     if not full:
#                         break   # only show the first (default) solution
#         return _table


####### Build diffractometer:

# Define pseudo motors:

class Sim4CMotor(PVPositioner): 
    done_value = 0
    
    setpoint = FormattedComponent(EpicsSignal,
                                    "{prefix}Euler_{circle}",
                                    kind="normal")
    readback = FormattedComponent(EpicsSignalRO,
                                    "{prefix}Euler_{circle}RBV",
                                    kind="normal")
    done = FormattedComponent(EpicsSignalRO,
                                   "{prefix}Kappa_busy",
                                   kind="omitted")
    
    def __init__(self, *args, circle=None, **kwargs):
        self.circle = circle
        super().__init__(*args, **kwargs)  
        self.readback.name = self.name
        

        

# define the 4-circle, based on expecting motor PVs
class FourCircleDiffractometer(E4CV):
#    pass
    h = Component(PseudoSingle, '', labels=("hkl", "fourc"))
    k = Component(PseudoSingle, '', labels=("hkl", "fourc"))
    l = Component(PseudoSingle, '', labels=("hkl", "fourc"))
# # We use soft motor here:
#     omega = Component(SoftPositioner, labels=("motor", "fourc"))
#     chi =   Component(SoftPositioner, labels=("motor", "fourc"))
#     phi =   Component(SoftPositioner, labels=("motor", "fourc"))
#     tth =   Component(SoftPositioner, labels=("motor", "fourc"))
# Real motor version:
    omega = Component(Sim4CMotor, '29idKappa:',circle='Theta', labels=("motor", "fourc"))
    chi =   Component(Sim4CMotor, '29idKappa:',circle='Chi',   labels=("motor", "fourc"))
    phi =   Component(Sim4CMotor, '29idKappa:',circle='Phi',   labels=("motor", "fourc"))
    tth =   Component(EpicsMotor, "29idKappa:m9", labels=("motor", "fourc"))

    
# create the 4-circle diffractometer object
fourc = FourCircleDiffractometer('', name="fourc")
select_diffractometer(fourc)


# What the available modes with this diffractometer?
print(f"\n{fourc.name} modes: {fourc.engine.modes}")


# Define motors RBVs:
tth_rbv = EpicsSignalRO('29idKappa:m9.RBV', name="tth_rbv")
omega_rbv = EpicsSignalRO('29idKappa:Euler_ThetaRBV', name="omega_rbv")
chi_rbv = EpicsSignalRO('29idKappa:Euler_ChiRBV', name="chi_rbv")
phi_rbv = EpicsSignalRO('29idKappa:Euler_PhiRBV', name="phi_rbv")
kth_rbv = EpicsSignalRO('29idKappa:m8.RBV', name="kth_rbv")
kap_rbv = EpicsSignalRO('29idKappa:m7.RBV', name="kap_rbv")
kphi_rbv =EpicsSignalRO('29idKappa:m1.RBV', name="tth_rbv")



# SPEC equivalent of setmode.
# The planned experiment could use contant phi

fourc.calc.engine.mode = "constant_phi"
print(f"\nselected mode: {fourc.calc.engine.mode}\n")

# Setup cut point / soft limits:

diffractometer_constraints = {
        # axis: Constraint(lo_limit, hi_limit, value, fit)
        "omega": Constraint(-20, 150, 0, True),
        "chi": Constraint(-30, 100, 0, True),
        # "phi": Constraint(0, 0, 0, False),
        "tth": Constraint(0, 180, 0, True),
    }
fourc.apply_constraints(diffractometer_constraints)
fourc.show_constraints()


print('\nWARNING: wavelength set to {:.3f} A = {:.2f} eV'.format(fourc.calc.wavelength,fourc.calc.energy*1e3))
caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
caput('29idKappa:UBlambda',fourc.calc.wavelength)



####### Tools and functions:


## Where motor: wh(fourc)

def wh(E=None,sync=True,diffractometer=fourc):
    """
    1117.KAPPA29ID_sim> wh
    H K L =  0  0  1.7345
    Alpha = 20  Beta = 20  Azimuth = 90
    Omega = 32.952  Lambda = 1.54
    Two Theta       Theta         Chi         Phi     K_Theta       Kappa       K_Phi
    40.000000   20.000000   90.000000   57.048500   77.044988  134.755995  114.093455

    https://certif.com/downloads/css_docs/spec_manA4.pdf
    """
    if sync == True:
        fourcSyncToMotor()
    if E != None:
        fourc.calc.wavelength = eV2Lambda(E)
        caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
        caput('29idKappa:UBlambda',fourc.calc.wavelength)
        print('\nOverwritting energy: E = ',str(E))
    self = diffractometer
    table = pyRestTable.Table()
    table.labels = "term value".split()
    table.addRow(("diffractometer", self.name))
    table.addRow(("Sample",self.calc.sample.name))
    table.addRow(("a",self.calc.sample.lattice[0]))
    table.addRow(("b",self.calc.sample.lattice[1]))
    table.addRow(("c",self.calc.sample.lattice[2]))
    table.addRow(("wavelength (angstrom)", self.calc.wavelength))
    table.addRow(("energy (eV)", self.calc.energy*1e3))    

    for item in "h k l".split():
        table.addRow((item, getattr(self, item).position))

    for item in self.real_positioners:
        table.addRow((item.attr_name, item.position))

    e_theta =  fourc.real_positioners[0].position    
    e_chi = fourc.real_positioners[1].position
    e_phi = fourc.real_positioners[2].position
    k_th,k_kap,k_phi=EtoK(e_theta,e_chi,e_phi,k_arm=50)

    table.addRow(("kth", k_th))
    table.addRow(("kap", k_kap))
    table.addRow(("kphi", k_phi))  
    
    print(table)
    
    
    
    
    


## Calculate hkl:

def changeMode(mode):
    '''Change diffractometer mode: 
    'bissector', 'constant_omega', 'constant_chi', 'constant_phi', 'double_diffraction', 'psi_constant'
    '''
    fourc.calc.engine.mode = mode
    print('Now using: ',fourc.calc.engine.mode)


def cahkl(h,k,l,solution=0,q=None):
    '''Calculate omega,chi,phi,tth,kth,kap,kphi for a given h,k,l reflection.
    By default return the first solution (index 0).
    Does not move motors.
    '''
    
    try:
        n=len(fourc.calc.forward((h,k,l)))
        if solution > n-1:
            print('Only {} solution(s)'.format(n))
            print('Defaulting solution = 0'.format(n))
            solution = 0
        e_theta =  round(fourc.calc.forward((h,k,l))[solution][0],5)
        e_chi = round(fourc.calc.forward((h,k,l))[solution][1],5)
        e_phi = round(fourc.calc.forward((h,k,l))[solution][2],5)   
        e_tth = round(fourc.calc.forward((h,k,l))[solution][3],5)   
        k_th,k_kap,k_phi=EtoK(e_theta,e_chi,e_phi,k_arm=50)
        energy_Ang=fourc.calc.wavelength
        energy_eV= fourc.calc.energy*1e3
        caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
        caput('29idKappa:UBlambda',fourc.calc.wavelength)

        if q == None:
            print("Sample = {:s} ".format(fourc.calc.sample.name))
            print("Lattice = {:.3f},{:.3f},{:.3f} ".format(fourc.calc.sample.lattice[0],fourc.calc.sample.lattice[1],fourc.calc.sample.lattice[2]))
            print('LAMBDA = {:.3f} \thv = {:.3f}'.format(energy_Ang,energy_eV))
            print('Mode = {:s}'.format(fourc.calc.engine.mode))
            return (e_theta,e_chi,e_phi,e_tth,k_th,k_kap,k_phi)
    except ValueError as err:
        print(err)


def mvhkl(h,k,l):
    result=cahkl(h,k,l)
    if result is not None:
        mvth(result[0])
        mvchi(result[1])
        mvphi(result[2])
        mvtth(result[3])
    else:
        print('Error')    
        
        
def cahkl_table(reflections):
    """
    Display table with all solutions for a series of reflections.
    Need more than one reflection (otherwise use cahkl fct.
    """
    try:
        energy_Ang=fourc.calc.wavelength
        energy_eV= fourc.calc.energy*1e3
        caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
        caput('29idKappa:UBlambda',fourc.calc.wavelength)
        print("Sample = {:s} ".format(fourc.calc.sample.name))
        print("Lattice = {:.3f},{:.3f},{:.3f} ".format(fourc.calc.sample.lattice[0],fourc.calc.sample.lattice[1],fourc.calc.sample.lattice[2]))
        print('LAMBDA = {:.3f} \thv = {:.3f}'.format(energy_Ang,energy_eV))
        print('Mode = {:s}'.format(fourc.calc.engine.mode))
        print(fourc.forwardSolutionsTable(reflections, full=True))
    except:
        print('Need more than one reflection - e.g.:\nreflections=((0.1,0.1,0.1),(0.1,0,0))')



## caput/caget motors:

        
def fourcRealPosition():
    """ caget motors RBV """
    caput('29idKappa:Kappa_sync.PROC',1)
    e_theta=omega_rbv.get()
    e_chi=chi_rbv.get()
    e_phi=phi_rbv.get()
    e_tth=tth_rbv.get()
    k_th=kth_rbv.get()
    k_kap=kap_rbv.get()
    k_phi=kphi_rbv.get() 
    print('omega = {:.5f}  \tchi = {:.5f}  \tphi = {:.5f}'.format(e_theta,e_chi,e_phi))
    print('tth = {:.5f}  \tkth = {:.5f}  \tkap = {:.5f}  \tkphi = {:.5f}'.format(e_tth,k_th,k_kap,k_phi))
    return e_theta,e_chi,e_phi,e_tth,k_th,k_kap,k_phi

def fourcSyncToMotor():
    """ Set the diffractometer (fourc) to the current motor RBV values (including beamline energy)"""
    eV=caget('29idmono:ENERGY_MON')
    fourc.calc.wavelength = eV2Lambda(eV)
    energy_Ang=fourc.calc.wavelength
    energy_eV= fourc.calc.energy*1e3
    caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
    caput('29idKappa:UBlambda',fourc.calc.wavelength)
    fourc.omega.move(omega_rbv.get())
    fourc.chi.move(chi_rbv.get())
    fourc.phi.move(phi_rbv.get())
    fourc.tth.move(tth_rbv.get())
    print('LAMBDA = {:.3f} \thv = {:.3f}'.format(energy_Ang,energy_eV))
    print('Sync to motor:\nomega = {:.5f}  \tchi = {:.5f}  \tphi = {:.5f}'.format(omega_rbv.get(),chi_rbv.get(),phi_rbv.get()))
    print('tth = {:.5f}  \tkth = {:.5f}  \tkap = {:.5f}  \tkphi = {:.5f}'.format(tth_rbv.get(),kth_rbv.get(),kap_rbv.get(),kphi_rbv.get()))

def fourcSimMove(omega_SP,chi_SP,phi_SP,tth_SP):
    """ Simulate a move to a given set of angles"""
    k_th,k_kap,k_phi=EtoK(omega_SP,chi_SP,phi_SP,k_arm=50)
    fourc.tth.move(tth_SP)
    fourc.omega.move(omega_SP)
    fourc.chi.move(chi_SP)
    fourc.phi.move(phi_SP)
    print('Simulate motion to:\nomega = {:.5f}  \tchi = {:.5f}  \tphi = {:.5f}'.format(omega_SP,chi_SP,phi_SP))
    print('tth = {:.5f}  \tkth = {:.5f}  \tkap = {:.5f}  \tkphi = {:.5f} '.format(tth_SP,k_th,k_kap,k_phi))
    return fourc.real_position




####### Experimental parameters:


def sampleNew(name,A,B,C,Alpha,Beta,Gamma):
    """Add new sample to  diffractometer."""
    try:
        mysample = fourc.calc.new_sample(name,    
            lattice=Lattice(
                a=A, b=B, c=C, 
                alpha=Alpha, beta=Beta, gamma=Gamma))
        print(mysample)
        caput('29idKappa:UBsample',fourc.calc.sample.name)
        caput('29idKappa:UBlattice',fourc.calc.sample.lattice)
    except ValueError:
        print('\nERROR: This sample already exist. Sample name is unique (dictionnary key). To change sample parameters, use sampleUpdate(...)')

def sampleChange(sample_key):
    """Change current sample."""
    fourc.calc.sample = fourc.calc._samples[sample_key]    # define the current sample
    caput('29idKappa:UBsample',fourc.calc.sample.name)
    caput('29idKappa:UBlattice',fourc.calc.sample.lattice)
    print("\nCurrent sample: "+fourc.calc.sample.name)

def sampleUpdate(a,b,c,alpha,beta,gamma):
    """update current sample lattice."""
    fourc.calc.sample.lattice = (a,b,c,alpha,beta,gamma) # define the current sample
    caput('29idKappa:UBsample',fourc.calc.sample.name)
    caput('29idKappa:UBlattice',fourc.calc.sample.lattice)
    print("\n"+fourc.calc.sample.name+": "+str(fourc.calc.sample.lattice))

def sampleList():
    """List all samples currently defined in fourc; specify  current one."""
    for x in list(fourc.calc._samples.keys())[1:]:
        print("\n======= "+x+" :")
        print(fourc.calc._samples[x].lattice)
        print(fourc.calc._samples[x].U)
    print("\nCurrent sample: "+fourc.calc.sample.name)

def sampleRBV():
    """List all samples currently defined in fourc; specify  current one."""
    for x in list(fourc.calc._samples.keys())[1:]:
        print("\n======= "+x+" :")
        print(fourc.calc._samples[x].lattice)
        print(fourc.calc._samples[x].U)
    print("\nCurrent sample: "+fourc.calc.sample.name)


def setor(h,k,l,tth0,omega0,chi0,phi0):
    """Define a reflection in fourc"""
    r1 = fourc.calc.sample.add_reflection(     
    h,k,l,
    position=fourc.calc.Position(
        tth=tth0, omega=omega0, chi=chi0, phi=phi0))
    return(r1)

#def setor2(h,k,l,tth2,omega2,chi2,phi2):
#    """Define 2nd reflection to fourc. Redundant - this is the exact same function as setor1, just need to change the reflection name."""
#    r2 = fourc.calc.sample.add_reflection(     
#    h,k,l,
#    position=fourc.calc.Position(
#        tth=tth2, omega=omega2, chi=chi2, phi=phi2))
#    return(r2)


def UBcalc(r1,r2,sync=True):
    """Compute the UB matrix with two reflections for a given energy.
    If sync=True (default), sync calculation with current beamline motors/energy.
    """
    #fourc.calc.wavelength = eV2Lambda(eV)  # to remove
    fourc.calc.sample.compute_UB(r1, r2)
    UB=fourc.calc.sample.UB
    #print(fourc.calc.sample.UB)
    print("\nUB Matrix for"+fourc.calc.sample.name+":\n"+str(UB)+'\n')
    if sync==True:
        fourcSyncToMotor()
    caput('29idKappa:UBmatrix',UB.reshape(9,1))   # flattened to a 9x1 matrix
    # add cahkl for current position?
    return fourc.calc.sample.UB
    
def UBrbv():
    UB=caget('29idKappa:UBmatrix')  # flattened to a 9x1 matrix
    return(UB.reshape(3,3))         # reshape to a 3x3 matrix


def UBenergy(eV):
    """Update diffractometer energy. 
    To sync to beamline energy, use UBenergy(getE())"""
    fourc.calc.wavelength = eV2Lambda(eV)
    print("\nCurrent energy: "+str(round(Lambda2eV(fourc.calc.wavelength),2)))
    caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
    caput('29idKappa:UBlambda',fourc.calc.wavelength)

    
def UBenergy_rbv():
    """Return diffractometer energy. """
    eV=Lambda2eV(fourc.calc.wavelength)
    print("\nCurrent energy: "+str(round(eV,2)))


####### Scan functions:




def _scan_hkl_array(mytable,settling_time=0.2,cts=1,scanIOC='Kappa',scanDIM=1,**kwargs):
    """
    Uses bluesky pyhkl to calculate the motor positions for an hkl scan:
    
        mytable = _hkl_array(hkl1,hkl2,npts,eV)
                = (table_omega, table_chi, table_phi, table_tth)

    Save the corresponding table into a txt file (CSV) as scan_####.txt                 
    Logging is automatic    
        **kwargs are the optional logging arguments see scanlog() for details
    """
    
    def hkl_vals(array_h,array_k,array_l,scanIOC="Kappa",scanDIM=1):
        IOC="29id"+scanIOC+":"
        scanPV=IOC+"scan"+str(scanDIM)
        Det_h=46
        #setting up hkl as a detector
        q=["H","K","L"]
        for i,e in enumerate([array_h,array_k,array_l]):
            ArrayCalc=IOC+"userArrayCalc"+str(i+1)
            #adding description
            caput(ArrayCalc+".DESC",'<'+q[i]+'>')
            #changing the number of points in the array
            caput(ArrayCalc+".NUSE",len(e))
            #putting arrays in array calc
            caput(ArrayCalc+".AA",e)
            #put scanRecord N for indexing 
            caput(ArrayCalc+".INPA",scanPV+".CPT CP NMS")
            #Make calc
            caput(ArrayCalc+".CALC","AA[A,A]")
            #output pv
            caput(ArrayCalc+".OUT",ArrayCalc+".L NPP NMS")
            #Add detector to scanRecord
            caput(scanPV+".D"+str(Det_h+i)+"PV",ArrayCalc+".L")
            print(caget(ArrayCalc+".DESC")+" = [D"+str(Det_h+i)+"]")

    # Set counting time:
    ScalerInt(cts)
    
    # Extract individual arrays:
    table_omega = mytable[0]
    table_chi   = mytable[1]
    table_phi   = mytable[2]
    table_tth   = mytable[3]
    table_hkl   = mytable[4]
    
    array_h = mytable[4][:,0]
    array_k = mytable[4][:,1]
    array_l = mytable[4][:,2]

    hkl_vals(array_h,array_k,array_l,scanIOC,scanDIM)
    print(caget('29idKappa:m9.DESC')+" = [D54]")
    print(caget('29idKappa:Euler_ThetaRBV.DESC')+"  = [D55]")
    print(caget('29idKappa:Euler_ChiRBV.DESC')  +" = [D56]")
    print(caget('29idKappa:Euler_PhiRBV.DESC')  +" = [D57]")

    #FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")
    #table2csv((FileNum,array_h.tolist(),array_k.tolist(),array_l.tolist(),table_tth.tolist(),table_omega.tolist(),table_chi.tolist(),table_phi.tolist()),filePath=mypath,separator=',')


    # Fill-in sscan record: 
    Scan_FillIn_Table('29idKappa:m9.VAL'     ,"29idKappa:m9.RBV"        ,scanIOC, scanDIM, table_tth,   posNum=1)
    Scan_FillIn_Table('29idKappa:Euler_Theta',"29idKappa:Euler_ThetaRBV",scanIOC, scanDIM, table_omega, posNum=2)
    Scan_FillIn_Table('29idKappa:Euler_Chi'  ,"29idKappa:Euler_ChiRBV"  ,scanIOC, scanDIM, table_chi,   posNum=3)
    Scan_FillIn_Table('29idKappa:Euler_Phi'  ,"29idKappa:Euler_PhiRBV"  ,scanIOC, scanDIM, table_phi,   posNum=4)
    
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","PRIOR POS")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)
     
    # Scanning
    
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)
 
    
    # Setting everything back
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",0.1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P1SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P2SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P3SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P4SM","LINEAR") 
    
    # Need to clear positionner!
    Clear_Scan_Positionners(scanIOC)



def scanhkl(hkl1,hkl2,npts,ct,E=None,run=True,mycomment=''):
    '''With hkl1=[h1,k1,l1] and hkl2=[h2,k2,l2]
    If E = None (default), uses the current beamline energy.
    Use run=False to display trajectory to make sure all reflections are within reach.
    '''
    if E is None:
        E=getE()
    UBenergy(E)
    myarray=_hkl_array(hkl1,hkl2,npts,E)
    print("Number of accessible reflections: ",str(len(myarray[4])))
    if run == True:
        #scanHKL(myarray,settling_time=0.2,cts=ct,mypath=path,comment=mycomment)
        _scan_hkl_array(myarray,settling_time=0.2,cts=ct,comment=mycomment)
    elif run == False:
        cahkl_table(myarray[4])

def scanhkl_test(hkl1,hkl2,npts,ct,E=None):
    '''Print the hkl trajectory for hkl1=[h1,k1,l1] and hkl2=[h2,k2,l2]
    If E = None (default), uses the current beamline energy.
    '''
    if E is None:
        E=getE()
    cahkl_table(_hkl_array(hkl1,hkl2,npts,E)[4])


def _hkl_array(hkl_start,hkl_stop,npts,eV):
    """ 
    Uses bluesky pyhkl to calculate a numpy array with the motors' trajectory for a given hkl scan.
    """
    # Set diffractometer energy:
    fourc.calc.wavelength = eV2Lambda(eV)
    caput('29idKappa:UBenergy',Lambda2eV(fourc.calc.wavelength))
    caput('29idKappa:UBlambda',fourc.calc.wavelength)

    # Generate a list of hkl position
    list_hkl_in = fourc.calc.calc_linear_path(hkl_start,hkl_stop,npts, num_params=3)  

    # Initialize motor table:
    list_omega=[]
    list_tth=[]
    list_chi=[]
    list_phi=[]
    list_hkl_out=[]
    
    # Compute motor positions for each hkl point & append to the motor tables:
    for hkl in list_hkl_in:
        try:
            list_omega.append(fourc.calc.forward(hkl)[0][0])
            list_chi.append(fourc.calc.forward(hkl)[0][1])
            list_phi.append(fourc.calc.forward(hkl)[0][2])
            list_tth.append(fourc.calc.forward(hkl)[0][3]) 
            list_hkl_out.append(hkl) 
        except ValueError as err:
            list_hkl_in.remove(hkl)   # not removing all the unobtainable values
            #print(str(hkl)+' : Error -  Unobtainable reflection:  Q > 2k?')

    # Return a list of arrays:
    return np.asarray(list_omega),np.asarray(list_chi),np.asarray(list_phi),np.asarray(list_tth),np.asarray(list_hkl_out)        
        


def table2csv(hkl_table,filePath=None,separator=','):
    #Need to make this smarter to not record unobtainable hkl reflections - data size missmatch
    if filePath is None:
        user=MDA_CurrentUser()
        filePath="/home/beams/29IDUSER/Documents/User_Folders/"+user+'/hkl/'
    scanNum=hkl_table[0]
    scanNumstr=str.zfill(str(scanNum),0)
    fileName='scan_'+scanNumstr+'.txt'
    with open(join(filePath, fileName), "a+") as f:   
        f.write('h'+separator+'k'+separator+'l'+separator+'tth'+separator+'th'+separator+'chi'+separator+'phi'+'\n')
        for (i) in range(len(hkl_table[1])):
            f.write(str(hkl_table[1][i])+separator+str(hkl_table[2][i])+separator+str(hkl_table[3][i])+separator+str(hkl_table[4][i])+separator+str(hkl_table[5][i])+separator+str(hkl_table[6][i])+separator+str(hkl_table[7][i])+'\n')
        print('\nWriting hkl table to:',join(filePath, fileName))



def scanhkl_E(StartStopStepLists,hkl,mono_offset,settling_time=0.2,cts=1,scanIOC='Kappa',scanDIM=1,**kwargs):
    """
    Uses bluesky pyhkl to calculate the motor positions for an energy scan at constant Q:
    
    StartStopStepLists is a list of lists for the different scan ranges
        StartStopStepList[[start1,stop1,step1],[start2,stop2,step2],...]
        Note duplicates are removed and the resulting array is sorted in ascending order
    
    hkl=(h,k,l)
                     
    Logging is automatic    
        **kwargs are the optional logging arguments see scanlog() for details
    """
    
    # Set counting time:
    ScalerInt(cts)

    # caget beamline parameters:
    if scanIOC is None:
        scanIOC=BL_ioc()
    ID_Mode, ID_QP, ID_SP, ID_RBV, hv, grt = Get_energy()

    
    # Target hkl:
    h,k,l=hkl
    
    # Create energy trajectory (can have variable step size):
    mytable_hv=Scan_MakeTable(StartStopStepLists)   
    
    caput('29idKappa:UBenergy',mytable_hv[0])
    caput('29idKappa:UBlambda',eV2Lambda(mytable_hv[0]))


    # Initialize motor table:
    mytable_ID=np.array([])
    mytable_omega=np.array([])
    mytable_chi=np.array([])
    mytable_phi=np.array([])
    mytable_tth=np.array([])

    
    # Compute motor positions for each energy point & append to the motor tables:
    for eV in mytable_hv:
        fourc.calc.wavelength = eV2Lambda(eV+mono_offset)
        mytable_ID=np.append(mytable_ID,ID_Calc(grt,ID_Mode,eV))  
        e_omega=round(fourc.calc.forward((h,k,l))[0][0],5)
        e_chi = round(fourc.calc.forward((h,k,l))[0][1],5)
        e_phi = round(fourc.calc.forward((h,k,l))[0][2],5)   
        e_tth = round(fourc.calc.forward((h,k,l))[0][3],5)  
        mytable_omega=np.append(mytable_omega,e_omega)
        mytable_chi=np.append(mytable_chi,e_chi)
        mytable_phi=np.append(mytable_phi,e_phi)
        mytable_tth=np.append(mytable_tth,e_tth)
           

    # Fill-in sscan record: 
    Scan_FillIn_Table('29idmono:ENERGY_SP',"29idmono:ENERGY_MON",scanIOC, scanDIM, mytable_hv, posNum=1)
    Scan_FillIn_Table('ID29:EnergyScanSeteV',"",                 scanIOC, scanDIM, mytable_ID, posNum=2)
    Scan_FillIn_Table('29idKappa:m9.VAL'     ,"29idKappa:m9.RBV"        ,scanIOC, scanDIM, mytable_tth,   posNum=3)
    Scan_FillIn_Table('29idKappa:Euler_Theta',"29idKappa:Euler_ThetaRBV",scanIOC, scanDIM, mytable_omega, posNum=4)
    #Scan_FillIn_Table('29idKappa:Euler_Chi'  ,"29idKappa:Euler_ChiRBV"  ,scanIOC, scanDIM, mytable_chi,  posNum=5)
    
    #Setting the beamline energy to the first point
    energy(mytable_hv[0])
    
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)
     
    #Scanning
    FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)    
    
    #Setting everything back
    energy(hv)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",0.1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P1SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P2SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P3SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P4SM","LINEAR") 
    
    # Need to clear positionner!
    Clear_Scan_Positionners(scanIOC)
#    print(mytable_hv)
#    print(mytable_ID)
#    print(mytable_omega)
#    print(mytable_tth)
    
 # to be saved in text file like scanhkl:

    return FileNum,mytable_hv.tolist(),mytable_ID.tolist(),mytable_omega.tolist(),mytable_chi.tolist() ,mytable_phi.tolist() ,mytable_tth.tolist() 



def scanhkl_mono(StartStopStepLists,hkl,mono_offset=0,settling_time=0.2,cts=1,scanIOC='Kappa',scanDIM=1,**kwargs):
    """
    Uses bluesky pyhkl to calculate the motor positions for an energy scan at constant Q:
    mono_offset => if you want to artificially shift the energy for the reciprocal space calulation (to match integer hkl indexes)
    StartStopStepLists is a list of lists for the different scan ranges
        StartStopStepList[[start1,stop1,step1],[start2,stop2,step2],...]
        Note duplicates are removed and the resulting array is sorted in ascending order
    
    hkl=(h,k,l)
                     
    Logging is automatic    
        **kwargs are the optional logging arguments see scanlog() for details
    """
    
    # Set counting time:
    ScalerInt(cts)

    # caget beamline parameters:
    if scanIOC is None:
        scanIOC=BL_ioc()
    ID_Mode, ID_QP, ID_SP, ID_RBV, hv, grt = Get_energy()

    
    # Target hkl:
    h,k,l=hkl
    
    # Create energy trajectory (can have variable step size):
    mytable_hv=Scan_MakeTable(StartStopStepLists)   
    
    caput('29idKappa:UBenergy',mytable_hv[0])
    caput('29idKappa:UBlambda',eV2Lambda(mytable_hv[0]))


    #mytable_ID=np.array([])
    mytable_omega=np.array([])
    mytable_chi=np.array([])
    mytable_phi=np.array([])
    mytable_tth=np.array([])

    
    # Compute motor positions for each energy point & append to the motor tables:
    for eV in mytable_hv:
        fourc.calc.wavelength = eV2Lambda(eV+mono_offset)
        #mytable_ID=np.append(mytable_ID,ID_Calc(grt,ID_Mode,eV))  
        e_omega=round(fourc.calc.forward((h,k,l))[0][0],5)
        e_chi = round(fourc.calc.forward((h,k,l))[0][1],5)
        e_phi = round(fourc.calc.forward((h,k,l))[0][2],5)   
        e_tth = round(fourc.calc.forward((h,k,l))[0][3],5)  
        mytable_omega=np.append(mytable_omega,e_omega)
        mytable_chi=np.append(mytable_chi,e_chi)
        mytable_phi=np.append(mytable_phi,e_phi)
        mytable_tth=np.append(mytable_tth,e_tth)
           

    # Fill-in sscan record: 
    Scan_FillIn_Table('29idmono:ENERGY_SP',"29idmono:ENERGY_MON",scanIOC, scanDIM, mytable_hv, posNum=1)
    #Scan_FillIn_Table('ID29:EnergyScanSeteV',"",                 scanIOC, scanDIM, mytable_ID, posNum=1)
    Scan_FillIn_Table('29idKappa:m9.VAL'     ,"29idKappa:m9.RBV"        ,scanIOC, scanDIM, mytable_tth,   posNum=2)
    Scan_FillIn_Table('29idKappa:Euler_Theta',"29idKappa:Euler_ThetaRBV",scanIOC, scanDIM, mytable_omega, posNum=3)
    Scan_FillIn_Table('29idKappa:Euler_Chi'  ,"29idKappa:Euler_ChiRBV"  ,scanIOC, scanDIM, mytable_chi,  posNum=4)
    
    #Setting the beamline energy to the mid point: we can try it that way, or just add the middle energy (where to park the ID) as an argument
    n=len(mytable_hv)
    energy(mytable_hv[int(n/2)])
    
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PASM","STAY")
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",settling_time)
     
    #Scanning
    FileNum  = caget("29id"+scanIOC+":saveData_scanNumber")
    Scan_Go(scanIOC,scanDIM=scanDIM,**kwargs)    
    
    #Setting everything back
    energy(hv)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".PDLY",0.1)
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P1SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P2SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P3SM","LINEAR") 
    caput("29id"+scanIOC+":scan"+str(scanDIM)+".P4SM","LINEAR") 
    
    # Need to clear positionner!
    Clear_Scan_Positionners(scanIOC)
#    print(mytable_hv)
#    print(mytable_ID)
#    print(mytable_omega)
#    print(mytable_tth)
    
 # to be saved in text file like scanhkl:

    return FileNum,mytable_hv.tolist(),mytable_omega.tolist(),mytable_chi.tolist() ,mytable_phi.tolist() ,mytable_tth.tolist() 