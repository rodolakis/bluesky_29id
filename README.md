# macros_29id

## Environment setup

    $ cd src/macros_29id/
    $ activate_conda   #alias: source /APSshare/miniconda/x86_64/bin/activate
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
    $ become_bluesky   #alias: /home/beams/RODOLAKIS/bin/bluesky_2022_1.sh

    $ import bluesky
    $ RE = bluesky.RunEngine({})
    $ from IEX_29id.devices.kappa_motors import *
    $ from IEX_29id.devices.kappa_motors import kappa_motors

## Bluesky python config:

    $ ~/.ipython-bluesky/profile-bluesky
    $ ~/bin/bluesky_2022_1.sh

## Bluesky shell script:   bluesky_2022_1.sh

    $ #!/bin/bash
    $ # purpose: start bluesky for instrument operations at 29ID
    $ export CONDA_ENVIRONMENT=bluesky_2022_1
    $ export CONDA_ACTIVATE=/APSshare/miniconda/x86_64/bin/activate
    $ export IPYTHONDIR=~/.ipython-bluesky
    $ export IPYTHON_PROFILE=bluesky
    $ IPYTHON_OPTIONS=
    $ IPYTHON_OPTIONS="${IPYTHON_OPTIONS} --profile=${IPYTHON_PROFILE}"
    $ IPYTHON_OPTIONS="${IPYTHON_OPTIONS} --ipython-dir=${IPYTHONDIR}"
    $ IPYTHON_OPTIONS="${IPYTHON_OPTIONS} --IPCompleter.use_jedi=False"
    $ source ${CONDA_ACTIVATE} ${CONDA_ENVIRONMENT}
    $ ipython ${IPYTHON_OPTIONS}
