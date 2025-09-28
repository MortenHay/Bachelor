import pandas as pd
import datetime as dt
import numpy as np

df = pd.DataFrame(columns=["pi_1"])

today = dt.datetime.now()
today = today.replace(hour=0, minute=0, second=0, microsecond=0)

for i in range(24):
    idx = today + dt.timedelta(hours=i)
    df.loc[idx, "pi_1"] = np.random.rand() * 10.0

df.to_csv("server_schedule.csv")
