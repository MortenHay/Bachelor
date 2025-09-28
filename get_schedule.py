import requests
import pandas as pd
import json

port = 48630

with open("config.json", "r") as f:
    config = json.load(f)

id = config["pi_id"]
url = f"http://localhost:{port}?pi_id={id}"
response = requests.get(url)
data = response.json()

df = pd.DataFrame.from_dict(data=data, orient="index", columns=["P_max"])
df.to_csv("schedule.csv")
