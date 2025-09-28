import json

config = {"pi_id": "pi_1", "ip": "192.168.0.99", "port": 48630}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=4)
