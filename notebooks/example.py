

__all__ = """
    aps
    bec
    bp
    bps
    cat
    kappa
    logger
    mono
    peaks
    RE
    sd
    undulator
    scaler1
    timebase
    TEY
    D3
    D4
    MCP
    meshD
""".split()


import apstools.devices
from bluesky import plan_stubs as bps  # steps for use inside a plan
from bluesky import plans as bp  # standard scan plans
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.magics import BlueskyMagics
from bluesky.utils import PersistentDict
from bluesky.utils import ProgressBarManager
from IPython import get_ipython
from ophyd import Component
from ophyd import Device
from ophyd import EpicsMotor
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import PseudoSingle
from ophyd import PVPositioner
from ophyd import PVPositionerPC
from ophyd import Signal
from ophyd.scaler import ScalerCH
from ophyd.signal import AttributeSignal
from ophyd.signal import EpicsSignalBase
import bluesky
import databroker
import logging
import os
import pint
import stdlogpj

BLUESKY_MONGO_CATALOG_NAME = "29idd" 

# I prefer logging to printing
BYTE = 1
kB = 1024 * BYTE
MB = 1024 * kB
# logger = stdlogpj.standard_logging_setup(
#     "bluesky-session", "ipython_logger", maxBytes=1 * MB, backupCount=9
# )
# logger.setLevel(logging.DEBUG)
# logger.info("#" * 60 + " startup")
# logger.info("logging started")
# logger.info(f"logging level = {logger.level}")

#--------------------------------------------------------
# setup the Bluesky framework first

# connect with the data
cat = databroker.catalog[BLUESKY_MONGO_CATALOG_NAME]

# prepare the RunEngine
RE = bluesky.RunEngine({})
RE.subscribe(cat.v1.insert)  # send run data to databroker

# To remember "scan_id" and other such metadata (md), need
# to save config to disk.  That's the role of PersistentDict.
# Here, we define a directory to be used.  And create it if
# it does not exist already.
home_dir = os.environ["HOME"]
md_dir_name = "Bluesky_RunEngine_md"
persistent_md_dir = os.path.join(home_dir, ".config", md_dir_name)
if not os.path.exists(persistent_md_dir):
    logger.info(
        "New directory to store RE.md between sessions: %s",
        persistent_md_dir
    )
    os.makedirs(persistent_md_dir)
RE.md = PersistentDict(persistent_md_dir)  # synchronizes RE.md with persistent_md_dir

# supplemental data: baselines, monitors
sd = bluesky.SupplementalData()
RE.preprocessors.append(sd)

# LiveTable and LivePlot during scan
bec = BestEffortCallback()
RE.subscribe(bec)
peaks = bec.peaks  # just as alias for less typing

# Register bluesky IPython magics.
get_ipython().register_magics(BlueskyMagics)

# Add a progress bar.
# RE.waiting_hook = ProgressBarManager()

# MUST be called BEFORE any EpicsSignal objects are created.
# Set default timeout for all EpicsSignal connections & communications.
try:
    EpicsSignalBase.set_defaults(
        auto_monitor=True, timeout=60, write_timeout=60, connection_timeout=60,
    )
except RuntimeError:
    pass

#--------------------------------------------------------
# support functions for units conversion

def convert(value, egu, to_egu):
    return pint.Quantity(value, egu).to(to_egu).magnitude

def eV2keV(value):
    return convert(value, "eV", "keV")

def keV2eV(value):
    return convert(value, "keV", "eV")

#--------------------------------------------------------
# define the structures to be used

class UndulatorEnergy(PVPositioner):  # in keV
    setpoint = Component(EpicsSignal, "EnergyScanSet")
    readback = Component(EpicsSignalRO, "Energy")
    done = Component(Signal,kind='omitted',value = True)
    done_value = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent.feedback.subscribe(self.done_callback)
        self.parent.busy_record.subscribe(self.done_callback)
        
    def done_callback(self,*args,**kwargs):
        self.done.put(self.parent.ready)
    
#     def cb_put(self, *args, **kwargs):
#         # TODO: confirm this works as expected
#         # TODO: consider the calibration dictionary for commanded vs actual energy

class MyUndulator(Device):   # in keV
    """29ID has a special undulator, not APS Undulator A."""
    energy = Component(UndulatorEnergy, "")
    actual_mode = Component(EpicsSignal, "ActualMode", write_pv='DesiredMode', string=True, kind='config') 
    quasi_ratio_raw = Component(EpicsSignal, "QuasiRatio.RVAL", write_pv='QuasiRatioIn.C', kind='config')
    main_on_off = Component(EpicsSignal, 'Main_on_off', string=True, kind='config')
    feedback = Component(EpicsSignalRO, 'feedback', string=True, kind='omitted')
    busy_record = Component(EpicsSignalRO, 'BusyRecord', string=True, kind='omitted')
    
#     @property
#     def ready(self):
#         print('ready?')
#         status=(self.feedback.get() == "Ready") and (self.busy_record.get() != 1)
#         print(f"{status = }")
#         return status
    
    @property
    def ready(self):
        status=(self.feedback.get() == "Ready") and (self.busy_record.get() != 1)
        #print(f"ready? {status = },  {self.feedback.get() = },  {self.busy_record.get() = }")
        return status

    
    def wait_until_ready(self):
        while not self.ready:
            yield from bps.sleep(0.1)   # bps = bluesky plan stub


class MonoEnergy(PVPositioner):  # in keV
    setpoint = Component(EpicsSignal, "ENERGY_SP")
    readback = Component(EpicsSignalRO, "ENERGY_MON")
    done = Component(EpicsSignalRO,'ERDY_STS',kind='omitted',string=True)
    done_value = 'Ready'      
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readback.name = self.name


class Monochromator(Device):
    energy = Component(MonoEnergy, "29idmono:")
    mirror_pitch = Component(EpicsMotor, "29idmonoMIR:P")
    grating_pitch = Component(EpicsMotor, "29idmonoGRT:P")
    grating_density = Component(EpicsSignal, "29idmono:GRT_DENSITY")
    mirror_status = Component(EpicsSignalRO, "29idmonoMIR:P_AXIS_STS")
    grating_status = Component(EpicsSignalRO, "29idmonoGRT:P_AXIS_STS")
    
    @property
    def status(self): #test.get(as_string=True) in ("Moving", "Positioned")
        return self.mirror_status.get(as_string=True) in  ("Moving", "Positioned") and self.grating_status.get(as_string=True) in  ("Moving", "Positioned")
        

# class SoftRealMotor(PVPositionerPC):
#     setpoint = Component(EpicsSignal, "")
#     readback = Component(EpicsSignalRO, "RBV")

# class My4Circle(E4CV):
#     h = Component(PseudoSingle, "")
#     k = Component(PseudoSingle, "")
#     l = Component(PseudoSingle, "")

#     omega = Component(SoftRealMotor, "29idKappa:Euler_Theta")
#     chi = Component(SoftRealMotor, "29idKappa:Euler_Chi")
#     phi = Component(SoftRealMotor, "29idKappa:Euler_Phi")
#     tth = Component(EpicsMotor, "29idKappa:m9")
#     _real = ["omega", "chi", "phi", "tth"]
#     # now, the extra motors
#     kth = Component(EpicsMotor, "29idKappa:m8")
#     kap = Component(EpicsMotor, "29idKappa:m7")
#     kphi = Component(EpicsMotor, "29idKappa:m1")

#--------------------------------------------------------
# define (and configure) the ophyd objects

aps = apstools.devices.ApsMachineParametersDevice(name="aps")
undulator = MyUndulator("ID29:", name="undulator") #, egu="keV"?
# TODO: shutters?
# TODO: slits?
# TODO: mirrors?
# TODO: baseline stream (extra PVs)
# TODO: Futur plans => secondary stream
# TODO: scan mono+ID
# TODO: calibration ID


mono = Monochromator("", name="mono")

scaler1 = ScalerCH("29idMZ0:scaler1", name="scaler1", labels=["scalers", "detectors"])
scaler1.stage_sigs['preset_time']=1
scaler1.wait_for_connection()
scaler1.select_channels()  # choose just the channels with EPICS names
# make shortcuts to specific channels assigned in EPICS
timebase = scaler1.channels.chan01.s
TEY = scaler1.channels.chan02.s
D3 = scaler1.channels.chan03.s
D4 = scaler1.channels.chan04.s
MCP = scaler1.channels.chan05.s
meshD = scaler1.channels.chan14.s
TEYcalc = EpicsSignalRO('29idMZ0:scaler1_calc1.B',name='TEYcalc')
D3calc = EpicsSignalRO('29idMZ0:scaler1_calc1.C',name='D3calc')
D4calc = EpicsSignalRO('29idMZ0:scaler1_calc1.D',name='D4calc')
MCPcalc = EpicsSignalRO('29idMZ0:scaler1_calc1.E',name='MCPcalc')

kappa = My4Circle("", name="kappa")
hkl.user.select_diffractometer(kappa)


# choose WHICH detector based on the PV (sets tth 0 position)
det_selected = EpicsSignal("29idKappa:userStringSeq6.STR1", name="det_selected", string=True)
HV = EpicsSignal("29idKappa:userCalcOut10.OVAL", name="HV")
centroidM3R = EpicsSignal("29id_ps6:Stats1:CentroidX_RBV", name="centroidM3R")

if mono.grating_density.get() == 1200:
    GRT="MEG"
elif mono.grating_density.get() == 2400:
    GRT="HEG"
branch = EpicsSignal("29id:CurrentBranch", name="branch")
