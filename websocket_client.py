import asyncio
from websockets.asyncio.client import connect
import json


async def establish_connection(websocket):
    message = json.dumps({"type": "init", "capacity": "20"})
    await websocket.send(message)
    response = await websocket.recv()
    data = json.loads(response)
    if data["type"] == "acknowledgement":
        print(data["message"])


async def consumer_handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        if data["type"] == "measurement":
            print(data["value"])


async def producer_handler(websocket):
    while True:
        ...


async def main():
    uri = "ws://localhost:12345"
    async with connect(uri) as websocket:
        await establish_connection(websocket)

    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
