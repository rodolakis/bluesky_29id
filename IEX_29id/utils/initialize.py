__all__ = """
    bec
    bp
    bps
    cat
    mono
    peaks
    RE
    sd
""".split()

 #https://github.com/BCDA-APS/bluesky_training/blob/main/bluesky/instrument/framework/initialize.py
 
import apstools.devices
from bluesky import plan_stubs as bps  # steps for use inside a plan
from bluesky import plans as bp  # standard scan plans
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.magics import BlueskyMagics
from bluesky.utils import PersistentDict
from bluesky.utils import ProgressBarManager
from IPython import get_ipython
from ophyd.signal import EpicsSignalBase
import bluesky
import databroker
import os
import logging
import stdlogpj

BLUESKY_MONGO_CATALOG_NAME = "29idd" 

# I prefer logging to printing
BYTE = 1
kB = 1024 * BYTE
MB = 1024 * kB
logger = stdlogpj.standard_logging_setup(
    "bluesky-session", "ipython_logger", maxBytes=1 * MB, backupCount=9
)
logger.setLevel(logging.DEBUG)
logger.info("#" * 60 + " startup")
logger.info("logging started")
logger.info(f"logging level = {logger.level}")

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
RE.waiting_hook = ProgressBarManager()

# MUST be called BEFORE any EpicsSignal objects are created.
# Set default timeout for all EpicsSignal connections & communications.

try:
    EpicsSignalBase.set_defaults(
        auto_monitor=True, timeout=60, write_timeout=60, connection_timeout=60,
    )
except RuntimeError:
    pass