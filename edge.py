import asyncio
import websocket_client
from controllers import DroopController
import datetime as dt
from pymodbus.client import AsyncModbusSerialClient
import json


async def measure_frequency(client: AsyncModbusSerialClient, address):
    f = client.read_holding_registers(address, count=2)
    return f


async def measure_baseline():
    return 1e6


async def modbus_send_Pset(client: AsyncModbusSerialClient, address, Pset):
    client.write_registers(address, [Pset])
    return


async def measure_ac_power(client: AsyncModbusSerialClient, address):
    P = client.read_holding_registers(address, count=2)
    return


def init():
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)
    parameters = {
        "name": config["name"],
        "capacity": config["capacity"],
        "delta P": 0,
        "droop constant": 0,
        "delta P supervisor": 0,
    }

    return parameters, config


async def main():
    parameters, config = init()
    t1 = asyncio.create_task(websocket_client.main(parameters))
    droop = DroopController(0, 50, 0.1)
    while True:
        modbus_client = AsyncModbusSerialClient(config["modbus address"])
        droop.set_Kp(parameters["droop constant"])
        delta_P_edge = droop.update(
            await measure_frequency(modbus_client, config["Line Frequency"])
        )
        delta_P = delta_P_edge + parameters["delta P supervisor"]
        P_set = delta_P - await measure_baseline()
        if P_set > 0:
            await modbus_send_Pset(modbus_client, config["WMaxLimPct"], P_set)
        parameters["delta P"] = await measure_ac_power(
            modbus_client, config["AC Power"]
        )
        await asyncio.sleep(1)

    await asyncio.wait([t1])


if __name__ == "__main__":
    asyncio.run(main())
