import numpy as np


class DroopController:
    def __init__(self, Kp=1.0, reference=0.0, offset=0.0):
        self.Kp = Kp
        self.reference = reference
        self.offset = offset

    def update(self, meas):
        # Main function to update control signal
        if np.abs(self.reference - meas) <= self.offset:
            # Signal within offset should return 0
            return 0
        if meas > self.reference:
            # Proportional control logic with offset from reference
            return self.Kp * (self.reference + self.offset - meas)
        else:
            return self.Kp * (self.reference - self.offset - meas)

    # Set functions
    def set_Kp(self, Kp):
        self.Kp = Kp

    def set_reference(self, reference):
        self.reference = reference

    def set_offset(self, offset):
        self.offset = offset


class IntegralController:
    def __init__(self, Ki, reference, initial_value=0):
        self.Ki = Ki
        self.reference = reference
        # Possibility for initial integral value
        self.current_value = initial_value

    def update(self, measurement, interval):
        # Main integral control action
        # Add area under error curve since last measurement
        self.current_value += (measurement - self.reference) * interval
        return self.current_value

    # Set functions
    def set_Ki(self, new_Ki):
        self.Ki = new_Ki

    def set_reference(self, new_reference):
        self.reference = new_reference

    def set_value(self, new_value):
        self.current_value = new_value


# Test script
if __name__ == "__main__":
    droop = DroopController(0.5, 50, 0.1)
    meas = [50, 50.05, 50.1, 50.5, 49.5]
    for m in meas:
        print(droop.update(m))
