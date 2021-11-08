# macros_29id

## Environment setup

    $ cd src/macros_29id/
    $ activate_conda
    $ conda env create --force -f mac_2022_1.yml
    $ conda env create --force -f linux_2022_1.yml

    $ conda create -n bluesky python=3.9 jupyter numpy
    $ conda activate bluesky
    $ pip install pyepics
    $ conda install jupyter
    $ conda install -c prjemian apstools
    $ conda install -c conda-forge bluesky


## Start ipython from wow:

    $ ssh -l rodolakis —Y -L 4044:bashful.xray.aps.anl.gov:4000 xgate.xray.aps.anl.gov
    $ password = crypto
    $ ssh -Y wow.xray.aps.anl.gov
    $ become_bluesky

    $ import bluesky
    $ RE = bluesky.RunEngine({})
    $ from IEX_29id.devices.kappa_motors import *
    $ from IEX_29id.devices.kappa_motors import kappa_motors
    