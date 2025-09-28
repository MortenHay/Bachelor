import requests
import pandas as pd
import json
import os

dir = os.path.dirname(os.path.abspath(__file__))

with open(f"{dir}/config.json", "r") as f:
    config = json.load(f)

id = config["pi_id"]
ip = config["ip"]
port = config["port"]

url = f"http://{ip}:{port}?pi_id={id}"
response = requests.get(url)
data = response.json()

df = pd.DataFrame.from_dict(data=data, orient="index", columns=["P_max"])
df.to_csv("schedule.csv")
