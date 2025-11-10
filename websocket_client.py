import asyncio
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed
import json
import datetime as dt


async def establish_connection(websocket, key, parameters):
    message = json.dumps(
        {
            "type": "init",
            "name": parameters["name"],
            "key": key,
            "capacity": parameters["capacity"],
            "timestamp": dt.datetime.now().timestamp(),
        }
    )
    await websocket.send(message)
    response = await websocket.recv()
    data = json.loads(response)
    if data["type"] == "acknowledgement":
        print(data["message"])
        parameters["synthetic start"] = data["synthetic start"]
        parameters["connected"] = True


async def consumer_handler(websocket, parameters: dict):
    async for message in websocket:
        data = json.loads(message)
        if data["type"] == "droop constant":
            parameters["droop constant"] = data["value"]
        elif data["type"] == "delta P supervisor":
            parameters["delta P supervisor"] = data["value"]


async def producer_handler(websocket, parameters):
    while True:
        data = {
            "type": "measurement",
            "delta P": parameters["delta P"],
            "capacity": parameters["capacity"],
            "timestamp": dt.datetime.now().timestamp(),
        }
        message = json.dumps(data)
        await websocket.send(message)
        await asyncio.sleep(1)


async def main(parameters: dict):
    flag = True
    while flag:
        uri = f"ws://{parameters['supervisor ip']}:{parameters['supervisor port']}"
        with open("key.txt") as f:
            key = f.read().replace("\n", "")
        try:
            print("1")
            async with connect(uri, open_timeout=3) as websocket:
                print("2")
                await establish_connection(websocket, key, parameters)
                flag = False
                print("3")
                consumer_task = asyncio.create_task(
                    consumer_handler(websocket, parameters)
                )
                producer_task = asyncio.create_task(
                    producer_handler(websocket, parameters)
                )
                done, pending = await asyncio.wait(
                    [consumer_task, producer_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                print(done)
                for task in pending:
                    task.cancel()
        except TimeoutError:
            print("Timeout reached. Retrying ...")
            pass


if __name__ == "__main__":
    asyncio.run(main({"value": 0}))
