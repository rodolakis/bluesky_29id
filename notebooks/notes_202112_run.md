




# General questions:
- <b>Answered:</b> how to set-up data broker? do I need to "change" it between users? No.
- <b>Answered:</b> how do I create a new catalog for a new experiment/users? we keep the same catalog; we change the metadata RE.md (see setup new user below)
- <b>Answered:</b> how do I reset the scan id number? 

        RE.md["scan_id"]      # returns the last scan_id
        RE.md["scan_id"] = 0  # set the next scan_id to 1
        RE.md["scan_id"] = 202112080000

- <b>Answered:</b> how to setup new user experiment: eg [USAXS setup_new_user.py](https://github.com/APS-USAXS/ipython-usaxs/blob/master/profile_bluesky/startup/instrument/utils/setup_new_user.py) 
- how do I set my profile for Jupyter like I do for ipython ?(my alias pointing to profile-bluesky gets over-written by my profile-default)
- how to delete a kernel?
- <b>Answered (partially):</b> BestEffortsCallback: 
    - can I turn off the visualisation of the baseline and/or limit it to a subset of pvs?
    - can I customize the plot visualisation to display only a subset of scaler (not all)? add grey scale? see [BestEffortsCallback doc](https://github.com/bluesky/bluesky/blob/1f277a044e5b23ae5f98c86d77c3871b4c9a1dc5/bluesky/callbacks/best_effort.py#L72-L78)
- how does the logger work?
- <b>Answered:</b> how to extract data for user? 
    - Overview: [here](https://github.com/BCDA-APS/bluesky_training/blob/main/export-bluesky-data.md)
    - Export to CSV: [here](https://nbviewer.org/github/BCDA-APS/bluesky_training/blob/main/export-to-csv.ipynb)
- <b>Answered:</b> can I call slit1_set in slitbl_set? Yes
- <b>To do:</b> scan time estimate and progress bar? => NIKEA (general or bluesky) 




# Questions for Pete:

- troubleshot soft motors (4C) done value?
- how to implement the busy/done for align_m3r pv?
- how can I make an ERF fit (derivative?) 
- how can I fit as part of a plan ? eg align_tth_plan = scan tth, find peak, return peak, playsound 
    see [Max's plan](https://github.com/APS-29ID-IEX/alignSample)
- how do I add the m3r centroid (EpicsSignal, not scaler) to my detectors? 
- how to implement a detector/positioner settling time?
- what's wrong with ps.reset()?


# TODO:
- check out apstools.plans.TuneAxis
- separate plans from devices
- create a custom_name.py in devices package (x_motor = kappa_motors.m2, srs4=srs.A4 ect...)
- how to load my instrument? 
    - instrument import: instrument package where _ _init_ _.py import all devices in defined order
    - copy PJ module structure and adapt exp setup to 29id
- rename scaler channels (d3, d4, mcp, tey - no caps); rename select_detector detector_select
- check code for energy calibration and slits (make sure there is no bad mix of ophyd and plans)
- rename slits.py/slits object
- move read dictionary to utils.misc (currently in both bp_slits and bp_energy)
- troubleshot utils.plot (mono not defined?)
- test LivePlot
- look at 4ID-D slits: https://github.com/APS-4ID-POLAR/ipython-polar/tree/master/profile_bluesky/startup/instrument/devices
    - what do I gain from it?
    - what is a Formatted component
    - sd.beamline.append(wbslit)

  
  

 # Notes:
- caput/caget:
    - caput = somepv.put()
    - caget = somepv.get()
    - <b>DO NOT USE somepv.<u>value</u></b>
- test plan: _summarize_plan_ in bluesky.simulator
- different streams:
    - primary stream: what gets triggered at every point
    - baseline: before and after snapshot
    - monitors: saved at the device own rate
- md={'comment':'demo'}: dictionnary of metadata

            def my_plan(detlist, count_time=1, md=None):
                if md is None: md={}
                yield from bp.count(det,md=md)
    - all standart plan have md=None arg
    - needs to be built in for custom plans like above
    - run = cat[-1]: run.metadata["start"] and run.metadata["stop"] (stop contains success message) 
- to print in a plan:

        print('tth0 is defined as direct beam on d4 only')
        yield from bps.null()
- staging = dictionary:
    - use m1.stage.sigs to see dictionary
    - m1.component_names to see keys
    - called by bp, not bps 
- BestEffortsCallback: eg: bec.disable_table(), see [documentation](https://github.com/bluesky/bluesky/blob/1f277a044e5b23ae5f98c86d77c3871b4c9a1dc5/bluesky/callbacks/best_effort.py#L72-L78)
- Extract dataset: 

        ds["noisy"].to_numpy()
        'to_cdms2',
        'to_dataframe',
        'to_dataset',
        'to_dict',
        'to_index',
        'to_iris',
        'to_masked_array',
        'to_netcdf',
        'to_numpy',
        'to_pandas',
        'to_series',
        'to_unstacked_dataset'

