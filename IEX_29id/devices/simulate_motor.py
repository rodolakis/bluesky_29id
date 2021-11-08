from apstools.devices import PVPositionerSoftDone
from apstools.devices import SwaitRecord

import bluesky
from bluesky import plans as bp
from bluesky import plan_stubs as bps

from ophyd import Component
from ophyd import EpicsSignal
from ophyd import PVPositionerPC

import time



motor = PVPositionerSoftDone("29idKtest:", readback_pv="gp:float2", setpoint_pv="gp:float1", tolerance=0.001, name="motor")
motor.wait_for_connection()

sim_calc = SwaitRecord("29idKtest:userCalc5", name="sim_calc")
sim_calc.wait_for_connection()

sim_calc.reset()
sim_calc
sim_calc.channels.A.input_pv.put(motor.setpoint.pvname)
sim_calc.channels.B.input_pv.put(motor.readback.pvname)
sim_calc.channels.C.input_value.put(0.1)
sim_calc.scanning_rate.put(".1 second")
sim_calc.calculation.put("MIN(ABS(A-B),C)*(A>B?1:-1)+B")
sim_calc.output_link_pv.put(motor.readback.pvname)
sim_calc.description.put(f"{motor.name} (simulated)")

sim_calcs_enable = EpicsSignal("29idKtest:userCalcEnable", name="sim_calcs_enable")
sim_calcs_enable.wait_for_connection()
sim_calcs_enable.put("Enable")

print(f"{sim_calcs_enable.get()=}")
