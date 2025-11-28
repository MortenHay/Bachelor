import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import asyncio
import pandas as pd


class Ramp:
    def __init__(
        self,
        start_frequency,
        end_frequency,
        start_time: dt.datetime,
        end_time: dt.datetime,
    ):
        self.start_frequency = start_frequency
        self.end_frequency = end_frequency
        self.start_time = start_time
        self.end_time = end_time

        self.df = (end_frequency - start_frequency) / (
            end_time - start_time
        ).total_seconds()


class FastRampTest:
    def __init__(self, start_time: dt.datetime):
        s = self.s
        self.start_frequency = 50.1
        self.start_time = start_time
        self.ramps = [
            Ramp(50.1, 50.55, s(30), s(33.1)),
            Ramp(50.55, 50.1, s(34.9), s(39.9)),
            Ramp(50.1, 50.5, s(90), s(91.7)),
            Ramp(50.5, 50.1, s(390), s(391.7)),
            Ramp(50.1, 51.0, s(690), s(693.8)),
            Ramp(51.0, 50.0, s(750), s(754.2)),
        ]

    def measure_frequency(self, time: dt.datetime):
        for ramp in self.ramps:
            if time <= ramp.start_time:
                return ramp.start_frequency
            elif time <= ramp.end_time:
                return (
                    ramp.start_frequency
                    + ramp.df * (time - ramp.start_time).total_seconds()
                )
        return self.ramps[-1].end_frequency

    def s(self, seconds):
        return self.start_time + dt.timedelta(seconds=seconds)


class sine_test:
    def __init__(self, test_csv, time_start) -> None:
        self.df = pd.read_csv(test_csv, delimiter=";", decimal=",").dropna()
        self.time_start = time_start

    def measure_frequency(self, time):
        offset = (time - self.time_start).total_seconds()
        if offset <= self.df["Time"].iloc[0]:
            return 50
        elif offset <= self.df["Time"].iloc[-1]:
            return np.interp(offset, self.df["Time"], self.df["Frequency"])
        else:
            return 50


class Inverter:
    def __init__(self, capacity=1.0, delay=1.0):
        self.capacity = capacity
        self.power = capacity
        self.delay = delay

    async def set_power(self, power):
        await asyncio.sleep(self.delay)
        self.power = power

    def set_capacity(self, capacity):
        self.capacity = capacity

    def measure_ac_power(self):
        return self.power

    def measure_baseline(self):
        return self.capacity


if __name__ == "__main__":
    start = dt.datetime.now()
    test = FastRampTest(dt.datetime.now())
    ts = np.linspace(0, 800, 10000)
    fs = np.array([test.measure_frequency(start + dt.timedelta(seconds=t)) for t in ts])
    plt.plot(ts, fs)
    plt.xlabel("Time since test start [s]", weight="bold")
    plt.ylabel("Frequency [Hz]", weight="bold")
    plt.title("Fast ramp test frequency signal", weight="bold")
    plt.xlim(0, 800)
    plt.show()
