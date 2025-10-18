import asyncio
from websockets.asyncio.server import broadcast, serve
from websockets.exceptions import ConnectionClosed
import json
import datetime as dt

# Set of connected clients
connected_clients = {}


async def consumer_handler(websocket):
    async for message in websocket:
        print(message)


async def producer_handler(websocket):
    while True:
        try:
            message = json.dumps(
                {"type": "measurement", "value": dt.datetime.now().second}
            )
            await websocket.send(message)
            await asyncio.sleep(1)
        except ConnectionClosed:
            break


# Function to handle each client connection
async def handle_client(websocket):
    message = await websocket.recv()
    data = json.loads(message)

    if data["type"] == "init":
        connected_clients[websocket] = data["capacity"]
        print(f"Client connected, {data['capacity']}")
        response = json.dumps({"type": "acknowledgement", "message": "connected"})
        asyncio.create_task(websocket.send(response))

    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    print("client disconnected")


# Main function to start the WebSocket server
async def main():
    async with serve(handle_client, "localhost", 12345) as server:
        await server.serve_forever()


# Run the server
if __name__ == "__main__":
    asyncio.run(main())
