from droop import DroopController
import numpy as np
from time import sleep
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt

P_max = 10.0  # in MW
freq_span = 0.4  # FCR-D Spans 400 mHz


def clamp(x, x_min, x_max):
    """Clamps number x between x_min and x_max"""
    if x > x_max:
        return x_max
    if x < x_min:
        return x_min
    return x


def update_controller(droop: DroopController, meas):
    """Helper function to update controller and clamp output"""
    return -clamp(droop.update(meas), -P_max, P_max)  # type: ignore


# Kp is P_max size over span of FCR-D (400 mHz)
Kp = P_max / freq_span

droop = DroopController(Kp, 50, 0.1)
meas = np.arange(49, 51, 0.01)
res = np.zeros(len(meas))

for i in range(len(meas)):
    res[i] = update_controller(droop, meas[i])
"""
plt.figure()
plt.plot(meas, res)
plt.show()"""


# main loop
while True:
    now = dt.datetime.now()
    df = pd.read_csv("schedule.csv", index_col=0)
    df.index = pd.DatetimeIndex(df.index)
    P_max = 0.0
    for i in range(len(df)):
        print(df.index[i])
        if now < df.index[i]:  # type: ignore
            break
        P_max = df.loc[df.index[i], "P_max"]
    droop.set_Kp(P_max / freq_span)  # type: ignore
    meas = 50 + (np.random.random())
    print(f"{meas} Hz")
    activation = update_controller(droop, meas)
    print(f"{activation} MW")
    print(f"Time to complete {(dt.datetime.now()-now).microseconds*1e-3}ms")
    sleep(1)
