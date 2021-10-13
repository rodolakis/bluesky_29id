# Bluesky documentation reference tables

## The most common ophyd imports

class | import | description | URL
--- | --- | --- | ---
`EpicsSignal` | `from ophyd import EpicsSignal` | connect with ONE PV | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device
`EpicsSignalRO` | `from ophyd import EpicsSignalRO` | connect with ONE read-only PV | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device
`EpicsSignalWithRBV` | `from ophyd import EpicsSignalWithRBV` | connect with TWO PVs (one for read AND one for write) | https://blueskyproject.io/ophyd/generated/ophyd.areadetector.base.EpicsSignalWithRBV.html#ophyd.areadetector.base.EpicsSignalWithRBV
`EpicsMotor` | `from ophyd import EpicsMotor` | connect with ONE EPICS motor record | https://blueskyproject.io/ophyd/generated/ophyd.epics_motor.EpicsMotor.html#ophyd.epics_motor.EpicsMotor
`ScalerCH` | `from ophyd.scaler import ScalerCH` | connect with one EPICS scaler record | https://blueskyproject.io/ophyd/generated/ophyd.scaler.ScalerCH.html#ophyd.scaler.ScalerCH
`Signal` | `from ophyd import Signal` | fundamental single piece of information, non-EPICS, in Python memory only
`Device` | `from ophyd import Device` | make a group of Signal(s) and/or Device(s) | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device
`Component` | `from ophyd import Component` | Used in a Device to define one attribute | part of https://blueskyproject.io/ophyd/tutorials/device.html?highlight=epicssignalro#define-a-custom-device

EpicsSignalWithRBV is for PV pairs that fit this pattern:

ioc:thing           # this is a SP
ioc:thing_RBV       # this is read only

signal = EpicsSignalWithRBV("ioc:thing", name="signal")


other: EPICS Area Detector, MCA

## The most common bluesky imports
description | import | URL
--- | --- | ---
Pre-assembled Plans | `from bluesky import plans as bp` | https://blueskyproject.io/bluesky/plans.html
Stub Plans (used in plans) | `from bluesky import plan_stubs as bps` | https://blueskyproject.io/bluesky/plans.html#stub-plans

Other: databroker, metadata, baseline, monitor