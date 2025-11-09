import asyncio
from websockets.asyncio.server import broadcast, serve
from websockets.exceptions import ConnectionClosed
import json
import datetime as dt
from controllers import IntegralController, DroopController, DataLogger
import hashlib
import pandas as pd
import synthetics
from functools import partial

# Set of connected clients
connected_clients = {}
# global variables
Ki = 1 / 7.5
total_capacity = 0
active_bid = 0.75
frequency_span = 0.4  # Hz
droop_constant = 1


def supervisor_droop_constant(droop: DroopController):
    global droop_constant
    droop_constant = frequency_span / active_bid
    droop.set_R(droop_constant)


def edge_droop_constant(websocket):
    global droop_constant, total_capacity, active_bid
    this_capacity = connected_clients[websocket]["capacity"]
    this_provision = active_bid * this_capacity / total_capacity
    return frequency_span / this_provision


def update_total_system_capacity(connected: dict):
    global total_capacity
    total_capacity = 0
    for values in connected.values():
        total_capacity += values["capacity"]
    return total_capacity


async def update_all_droop_constants():
    total_capacity_inv = 1.0 / update_total_system_capacity(connected_clients)
    frequency_span_inv = 1.0 / frequency_span
    # Calculate single constant to scale unit capacities
    scaling_constant = total_capacity_inv * frequency_span_inv * active_bid
    tasks = []
    for websocket, values in connected_clients.items():
        R_i = scaling_constant * values["capacity"]
        values["droop constant"] = R_i
        data = {"type": "droop constant", "value": R_i}
        message = json.dumps(data)
        tasks.append(asyncio.create_task(websocket.send(message)))
    await asyncio.wait(tasks)


async def update_controllers(
    droop: DroopController,
    integrator: IntegralController,
    frequency_measurement: float,
    system_activation: float,
    time_old: dt.datetime,
    time_new: dt.datetime,
    datalogger: DataLogger | None = None,
):
    # Cascaded droop to integrator control action
    # Generate Power setpoint from frequency measurement
    supervisor_droop_constant(droop)
    activation_setpoint = droop.update(frequency_measurement)
    activation_setpoint = clamp(activation_setpoint, -active_bid, 0)
    # Use as reference for integrator and return integrated signal
    integrator.set_reference(activation_setpoint)
    print("Activation setpoint: ", activation_setpoint)
    print("Error: ", system_activation - activation_setpoint)
    return activation_setpoint, integrator.update(
        measurement=system_activation, interval=(time_new - time_old).total_seconds()
    )


def authentication(name: str, key: str):
    df = pd.read_csv("registered_units.csv", index_col=0)
    salt = str(df.loc[df["name"] == name, "salt"].iloc[0]).encode("utf-8")
    result = hashlib.pbkdf2_hmac("sha256", key.encode("utf-8"), salt, 1)
    target = str(df.loc[df["name"] == name, "hash"].iloc[0]).encode("latin-1")
    return target == result


def measure_frequency():
    return 50


def get_system_activation():
    delta_P_sys = 0
    for values in connected_clients.values():
        delta_P_sys += values["delta P"]
    return delta_P_sys


def clamp(x, x_min, x_max):
    """Clamps number x between x_min and x_max"""
    if x > x_max:
        return x_max
    if x < x_min:
        return x_min
    return x


async def consumer_handler(websocket, datalogger: DataLogger | None = None):
    capacity_old = connected_clients[websocket]["capacity"]
    async for message in websocket:
        try:
            data = json.loads(message)
            if data["type"] == "measurement":
                connected_clients[websocket]["capacity"] = data["capacity"]
                connected_clients[websocket]["delta P"] = data["delta P"]
                if datalogger:
                    datalogger.measurement(
                        data["timestamp"],
                        connected_clients[websocket]["name"],
                        "capacity",
                        data["capacity"],
                    )
                    datalogger.measurement(
                        data["timestamp"],
                        connected_clients[websocket]["name"],
                        "delta P",
                        data["delta P"],
                    )
            if connected_clients[websocket]["capacity"] != capacity_old:
                update_total_system_capacity(connected_clients)
        except Exception as e:
            print(f"invalid message recieved from {connected_clients[websocket]}")
            print(e)


async def producer_handler(websocket, datalogger: DataLogger | None = None):
    droop_constant_old = connected_clients[websocket]["droop constant"]
    while True:
        try:
            droop_constant_new = edge_droop_constant(websocket)
            if droop_constant_new != droop_constant_old:
                if datalogger:
                    datalogger.measurement(
                        timestamp(),
                        connected_clients[websocket]["name"],
                        "droop constant",
                        droop_constant_new,
                    )
                message = json.dumps(
                    {"type": "droop constant", "value": droop_constant_new}
                )
                print(f"new droop constant: {droop_constant_new}")
                await websocket.send(message)
                droop_constant_old = droop_constant_new
            await asyncio.sleep(10)
        except ConnectionClosed:
            break


def timestamp():
    return dt.datetime.now().timestamp()


# Function to handle each client connection
async def handle_client(websocket, datalogger: DataLogger | None = None):
    global test_start
    print("New client attempting to connect")
    # Receive init message from websocket
    message = await websocket.recv()
    try:
        # Load message requiring json format with {"type":"init"}
        data = json.loads(message)
        if data["type"] == "init":

            # Reject units that do not have correct name:key pair
            if not authentication(data["name"], data["key"]):
                print(f"Authentication failed for {data['name']}, key={data['key']}")
                response = json.dumps(
                    {"type": "acknowledgement", "message": "Authentication failed"}
                )
                await websocket.send(response)
                return
            # Add unit to connected_clients dict
            connected_clients[websocket] = {
                "name": data["name"],
                "capacity": data["capacity"],
                "delta P": 0.0,
            }
            if datalogger:
                datalogger.measurement(
                    data["timestamp"], data["name"], "capacity", data["capacity"]
                )
            print(f"Client connected, {data['name']}")
            # Send positive response
            response = json.dumps(
                {
                    "type": "acknowledgement",
                    "message": "Connected",
                    "synthetic start": test_start.timestamp(),
                }
            )

            await websocket.send(response)
        # Basic error handling
        else:
            raise Exception("type:init missing")
    except Exception as e:
        print("An error occured while connecting unit")
        print(e)
        response = json.dumps(
            {"type": "acknowledgement", "message": "Error occured while connecting"}
        )
        await websocket.send(response)
        return
    # Start input (consumer) and output (producer) handler functions.
    await update_all_droop_constants()
    consumer_task = asyncio.create_task(consumer_handler(websocket, datalogger))
    producer_task = asyncio.create_task(producer_handler(websocket, datalogger))
    # Continue above handlers until client disconnects
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    del connected_clients[websocket]
    print("client disconnected, updating droop constant")
    await update_all_droop_constants()
    print("all droop constants updated")


# Main function to start the WebSocket server
async def main():
    global test_start
    # Initialize controllers
    integrator = IntegralController(Ki, 0, 0)
    droop = DroopController(0, 50, 0.1)
    logger = DataLogger(f"tests/{dt.datetime.now().strftime("%d%m%y,%H%M%S")}.json")

    ### Synthetic branch
    test_start = dt.datetime.now()  # + dt.timedelta(seconds=-680)
    test = synthetics.FastRampTest(test_start)
    logger.measurement(timestamp(), "supervisor", "start", test_start.timestamp())
    ###

    event_timeout = 0

    # Open asynchronous server and serve forever
    async with serve(
        partial(handle_client, datalogger=logger), "localhost", 12345
    ) as server:
        t1 = asyncio.create_task(server.serve_forever())

        # Main control loop
        time_old = dt.datetime.now()
        while True:
            time_new = dt.datetime.now()
            # Update cascaded droop and integral controllers
            # Returned is the integrated supervisor control signal
            frequency = test.measure_frequency(time_new)
            logger.measurement(timestamp(), "supervisor", "frequency", frequency)
            system_activation = get_system_activation()
            logger.measurement(
                timestamp(), "supervisor", "delta P system", system_activation
            )
            activation_setpoint, delta_P_supervisor = await update_controllers(
                droop,
                integrator,
                frequency_measurement=frequency,
                system_activation=system_activation,
                time_old=time_old,
                time_new=time_new,
            )
            if activation_setpoint > 0:
                event_timeout = 0
            else:
                event_timeout += 1
                if event_timeout >= 5:
                    integrator.set_value(0)
            print("Delta P Supervisor ", delta_P_supervisor)
            # Broadcast to all connected clients
            logger.measurement(
                timestamp(), "supervisor", "delta P supervisor", delta_P_supervisor
            )
            broadcast(
                connected_clients,
                json.dumps({"type": "delta P supervisor", "value": delta_P_supervisor}),
            )
            # Update time stamp for next loop
            time_old = time_new
            await asyncio.sleep(1)

        # Ensure program does not exit before server closes
        await asyncio.wait([t1])


# Run the server
if __name__ == "__main__":
    asyncio.run(main())
