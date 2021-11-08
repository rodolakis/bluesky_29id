# macros_29id

## Environment setup


    $conda env create --force -f mac_2022_1.yml

    $ conda create -n bluesky python=3.9 jupyter numpy
    $ conda activate bluesky
    $ pip install pyepics
    $ conda install jupyter
    $ conda install -c prjemian apstools
    $ conda install -c conda-forge bluesky



    $ ssh -l rodolakis —Y -L 4044:bashful.xray.aps.anl.gov:4000 xgate.xray.aps.anl.gov
    $ password = crypto
    $ ssh -Y wow.xray.aps.anl.gov
    $ become_bluesky
    $ ipython_bluesky


# New environment for Mac

    $conda env create --force -f mac_2022_1.yml
