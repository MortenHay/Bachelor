import asyncio
import websocket_client
from controllers import DroopController
import datetime as dt
from pymodbus.client import AsyncModbusSerialClient
import json
from numpy import mean


async def measure_frequency(client: AsyncModbusSerialClient, address):
    f = await client.read_holding_registers(address, count=2)
    return client.convert_from_registers(f.registers, client.DATATYPE.FLOAT64)


async def measure_baseline(baseline_list: list, current_index: int, size: int):
    new_baseline = 1e6
    if len(baseline_list) < size:
        baseline_list.append(new_baseline)
    else:
        baseline_list[current_index] = new_baseline
    current_index += 1
    current_index %= size
    return new_baseline, current_index


async def modbus_send_Pset(client: AsyncModbusSerialClient, address, Pset):
    registers = client.convert_to_registers(Pset, client.DATATYPE.FLOAT64)
    response = await client.write_registers(address, registers)
    return response


async def measure_ac_power(client: AsyncModbusSerialClient, address):
    P = await client.read_holding_registers(address, count=2)
    return client.convert_from_registers(P.registers, client.DATATYPE.FLOAT64)


def clamp(x, x_min, x_max):
    """Clamps number x between x_min and x_max"""
    if x > x_max:
        return x_max
    if x < x_min:
        return x_min
    return x


async def update_capacity(baseline_list: list, parameters: dict):
    while True:
        await asyncio.sleep(30)
        new_capacity = mean(baseline_list)
        parameters["capacity"] = new_capacity


def init():
    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)
    parameters = {
        "name": config["name"],
        "capacity": config["capacity"],
        "supervisor ip": config["ip"],
        "supervisor port": config["port"],
        "delta P": 0,
        "droop constant": 0,
        "delta P supervisor": 0,
    }

    return parameters, config


async def main():
    parameters, config = init()
    t1 = asyncio.create_task(websocket_client.main(parameters))
    droop = DroopController(0, 50, 0.1)
    modbus_client = AsyncModbusSerialClient(config["modbus address"])
    await modbus_client.connect()
    baseline_list = []
    baseline_list_size = 60
    current_index = 0
    t2 = asyncio.create_task(update_capacity(baseline_list, parameters))
    try:
        while True:
            while not t1.done():
                droop.set_R(parameters["droop constant"])
                delta_P_edge = droop.update(
                    await measure_frequency(modbus_client, config["Line Frequency"])
                )
                baseline, current_index = await measure_baseline(
                    baseline_list, current_index, baseline_list_size
                )
                delta_P = delta_P_edge + parameters["delta P supervisor"]
                # Flip sign of droop
                delta_P = clamp(delta_P, baseline, 0)
                P_set = baseline + delta_P
                await modbus_send_Pset(modbus_client, config["WMaxLimPct"], P_set)
                P_measurement = await measure_ac_power(
                    modbus_client, config["AC Power"]
                )
                parameters["delta P"] = baseline - P_measurement  # type: ignore #
                await asyncio.sleep(1)
            print("Lost connection to supervisor.")
            print("Reconnecting ...")
            t1 = asyncio.create_task(websocket_client.main(parameters))

    finally:
        modbus_client.close()
        t1.cancel()
        t2.cancel()


if __name__ == "__main__":
    asyncio.run(main())
