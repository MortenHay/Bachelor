import json

config = {
    "name": "pi_1",
    "ip": "localhost",
    "port": 12345,
    "capacity": 1.0,
    "modbus address": "COM4",
    "baudrate": 9600,
    "parity": "N",
    "stopbits": 1,
    "bytesize": 8,
    "WMaxLimPct": {
        "address": 40243 - 1,
        "scalefactor": 1e-2,
        "datatype": "UINT16",
        "count": 1,
    },
    "WMaxLim_Ena": {
        "address": 40247 - 1,
        "scalefactor": 1,
        "datatype": "UINT16",
        "count": 1,
    },
    "AC Power": {
        "address": 40092 - 1,
        "scalefactor": 1,
        "datatype": "FLOAT32",
        "count": 2,
    },
    "Line Frequency": {
        "adress": 40094 - 1,
        "scalefactor": 1,
        "datatype": "FLOAT32",
        "count": 2,
    },
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=4)
