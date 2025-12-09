import asyncio
import websocket_client
from controllers import DroopController
import datetime as dt
from pymodbus.client import AsyncModbusSerialClient
import json
from numpy import mean
import synthetics


async def modbus_init_client(config: dict):
    """_summary_

    Args:
        config (dict): _description_

    Returns:
        _type_: _description_
    """
    modbus_client = AsyncModbusSerialClient(
        port=config["modbus address"],
        timeout=3,
        baudrate=int(config["baudrate"]),
        bytesize=int(config["bytesize"]),
        parity=config["parity"],
        stopbits=int(config["stopbits"]),
    )
    await modbus_client.connect()
    # Start power limit operating mode with no cap
    await modbus_write(modbus_client, "WMaxLimPct", config, 100)
    await modbus_write(modbus_client, "WMaxLim_Ena", config, 1)
    return modbus_client


async def modbus_read(client: AsyncModbusSerialClient, command: str, config: dict):
    com_dict = config[command]
    rr = await client.read_holding_registers(
        com_dict["address"], count=com_dict["count"]
    )
    return (
        client.convert_from_registers(
            rr.registers, getattr(client.DATATYPE, com_dict["datatype"])
        )
        * com_dict["scalefactor"]
    )


async def modbus_write(
    client: AsyncModbusSerialClient, command: str, config: dict, value
):
    com_dict = config[command]
    scale = int(1 / com_dict["scalefactor"])
    value = value * scale
    if "INT" in com_dict["datatype"]:
        value = int(value)
    print("Sending ", value, " to ", command)
    rr = client.convert_to_registers(
        value,
        getattr(client.DATATYPE, com_dict["datatype"]),
    )
    return await client.write_registers(com_dict["address"], rr)


async def measure_frequency(client: AsyncModbusSerialClient, config):
    return await modbus_read(client, "Line Frequency", config)


async def measure_baseline(sensor, baseline_list: list, current_index: int, size: int):
    # No actual sensors connected
    # new_baseline = sensor["capacity"]
    new_baseline = sensor
    if len(baseline_list) < size:
        baseline_list.append(new_baseline)
    else:
        baseline_list[current_index] = new_baseline
    current_index += 1
    current_index %= size
    return new_baseline, current_index


async def send_Pset(client: AsyncModbusSerialClient, config, Pset):
    percentage = Pset / config["WMaxLimPct"]["inverter cap"] * 100
    print("sending P__set: ", percentage, "%")
    await modbus_write(client, "WMaxLimPct", config, percentage)
    await modbus_write(client, "WMaxLim_Ena", config, 1)
    print("WmaxLimPct read: ", await modbus_read(client, "WMaxLimPct", config))
    print("WmaxLim_Ena read: ", await modbus_read(client, "WMaxLim_Ena", config))


async def measure_ac_power(client: AsyncModbusSerialClient, config):
    return await modbus_read(client, "AC Power", config)


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
        "power": 0,
        "delta P": 0,
        "droop constant": 0,
        "delta P supervisor": 0,
        "synthetic start": 0,
        "connected": False,
    }

    return parameters, config


async def main():
    parameters, config = init()
    t1 = asyncio.create_task(websocket_client.main(parameters))
    droop = DroopController(0, 50, 0.1)

    modbus_client = await modbus_init_client(config)

    baseline_list = []
    baseline_list_size = 60
    current_index = 0
    P_measurement = await measure_ac_power(modbus_client, config)
    baseline, current_index = await measure_baseline(
        P_measurement, baseline_list, current_index, baseline_list_size
    )
    t2 = asyncio.create_task(update_capacity(baseline_list, parameters))
    try:
        while True:
            while not t1.done():
                while not parameters["connected"]:
                    print("Connecting ...")

                    await asyncio.sleep(5)
                while parameters["synthetic start"] == 0:
                    await asyncio.sleep(1)
                """test = synthetics.FastRampTest(
                    dt.datetime.fromtimestamp(parameters["synthetic start"])
                )"""
                test = synthetics.sine_test(
                    "sine_test.csv",
                    dt.datetime.fromtimestamp(parameters["synthetic start"]),
                )
                droop.set_R(parameters["droop constant"])
                frequency_measurement = test.measure_frequency(dt.datetime.now())
                delta_P_edge = droop.update(frequency_measurement)
                delta_P_edge = clamp(
                    delta_P_edge, -0.4 / parameters["droop constant"], 0
                )
                delta_P = delta_P_edge + parameters["delta P supervisor"]

                delta_P = clamp(delta_P, -baseline, 0)
                # Flip sign of droop
                if delta_P < 0:
                    P_set = baseline + delta_P
                    await send_Pset(modbus_client, config, P_set)
                    P_measurement = await measure_ac_power(modbus_client, config)

                else:
                    await modbus_write(modbus_client, "WMaxLim_Ena", config, 0)
                    P_measurement = await measure_ac_power(modbus_client, config)
                    baseline, current_index = await measure_baseline(
                        P_measurement, baseline_list, current_index, baseline_list_size
                    )
                ###
                parameters["delta P"] = min(P_measurement - baseline, 0)  # type: ignore #
                parameters["power"] = P_measurement
                print("Target: ", delta_P)
                print("Delta P:", parameters["delta P"])
                await asyncio.sleep(0.1)
            parameters["connected"] = False
            print("Lost connection to supervisor.")
            print("Reconnecting ...")
            t1 = asyncio.create_task(websocket_client.main(parameters))

    finally:
        await modbus_write(modbus_client, "WMaxLim_Ena", config, 0)
        await modbus_write(modbus_client, "WMaxLimPct", config, 100)
        modbus_client.close()
        t1.cancel()


#        t2.cancel()


if __name__ == "__main__":
    asyncio.run(main())
