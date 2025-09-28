import numpy as np


class DroopController:
    def __init__(self, Kp=1.0, reference=0.0, offset=0.0):
        self.Kp = Kp
        self.reference = reference
        self.offset = offset

    def update(self, meas):
        if np.abs(self.reference - meas) <= self.offset:
            return 0
        if meas > self.reference:
            return self.Kp * (self.reference + self.offset - meas)
        else:
            return self.Kp * (self.reference - self.offset - meas)

    def set_Kp(self, Kp):
        self.Kp = Kp

    def set_reference(self, reference):
        self.reference = reference

    def set_offset(self, offset):
        self.offset = offset


# Test script
if __name__ == "__main__":
    droop = DroopController(0.5, 50, 0.1)
    meas = [50, 50.05, 50.1, 50.5, 49.5]
    for m in meas:
        print(droop.update(m))
