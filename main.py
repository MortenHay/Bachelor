from droop import DroopController
import numpy as np
from time import sleep

bid = 10  # in MW


def clamp(x, x_min, x_max):
    """Clamps number x between x_min and x_max"""
    if x > x_max:
        return x_max
    if x < x_min:
        return x_min
    return x


# Kp is bid size over span of FCR-D (400 mHz)
Kp = bid / 0.4

droop = DroopController(Kp, 50, 0.1)

while True:
    meas = 50 + (np.random.random())
    print(f"{meas} Hz")
    activation = droop.update(meas)
    activation = -clamp(activation, -bid, 0)
    print(f"{activation} MW")
    sleep(1)
