__all__ = """
    plot_latest
    plot_latest_plan
    plot_run
    plot_scatter
    plot_image
""".split()

import databroker
from apstools.utils import listruns
from IEX_29id.utils.initialize import *
from IEX_29id.devices.detectors import *
from IEX_29id.devices.beamline_energy import *
from IEX_29id.devices.kappa_motors import *
from IEX_29id.devices.kappa_motors import kappa_motors
from IEX_29id.devices.detectors import scaler
from IEX_29id.devices.slits import SetSlit4
from bluesky.plans import scan
from bluesky.callbacks import LiveTable
from bluesky.callbacks.fitting import PeakStats
from bluesky.callbacks.mpl_plotting import plot_peak_stats
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

print(list(databroker.catalog))
cat=databroker.catalog['29idd'];print('Number of scans in catalog: '+str(len(cat)))


x_motor=kappa_motors.m2
y_motor=kappa_motors.m3
z_motor=kappa_motors.m4
kphi_motor=kappa_motors.m1
kap_motor=kappa_motors.m7
kth_motor=kappa_motors.m8
tth_motor=kappa_motors.m9


def plot_latest(pos,det):
    """
    pos = x_motor (object)
    det = D3
    
    """
    ds=cat[-1].primary.read()
    #ds.plot.scatter(x=pos.name,y=det.name)
    plt.plot(ds[pos.name], ds[det.name])
    plt.xlabel(pos.name)
    plt.ylabel(det.name)
    plt.grid(color='lightgrey')
    try:
        fname='/home/beams/29IDUSER/Documents/User_Folders/lastfigure.png'
        print(fname)
        plt.savefig(fname)
    except:
        print('error saving')
        pass
    plt.show()
    
def plot_latest_plan(pos,det):
    """
    pos = x_motor (object)
    det = D3
    
    """
    plot_latest(pos,det)
    yield from bps.null()

    
def plot_scatter(pos,det):
    """
    pos= x_motor (object)
    det=D3
    
    """
    ds=cat[-1].primary.read()
    ds.plot.scatter(x=pos.name,y=det.name)
    plt.xlabel(pos.name)
    plt.ylabel(det.name)
    plt.grid(color='lightgrey')


def plot_run(run,pos,det):
    """
    pos= x_motor (object)
    det=D3
    
    """
    ds=cat[run].primary.read()
    #ds.plot.scatter(x=pos.name,y=det.name)
    plt.plot(ds[pos.name], ds[det.name])
    plt.xlabel(pos.name)
    plt.ylabel(det.name)
    plt.grid(color='lightgrey')

    

#  filepath='/home/beams/29IDUSER/Documents/User_Folders/Topp/S089.tif'
def plot_image(filepath,h=20,v=10):
    """
    filepath = '/home/beams/29IDUSER/Documents/User_Folders/UserName/TifFile.tif'
    """
    image = mpimg.imread(filepath)
    plt.figure(figsize=(h,v))
    #plt.imshow(image,cmap='gray',vmin=v1,vmax=v2)
    plt.imshow(image,cmap='gray')
    plt.axis('off')
    plt.show()
