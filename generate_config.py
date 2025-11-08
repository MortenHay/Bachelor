import json

config = {
    "name": "pi_1",
    "ip": "localhost",
    "port": 12345,
    "capacity": 1.0,
    "modbus address": "dev/0",
    "baudrate": 9600,
    "WMaxLimPct": 40243,
    "AC Power": 40092,
    "Line Frequency": 40094,
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=4)
