import asyncio


# Define a protocol class that inherits from asyncio.Protocol
class EchoProtocol(asyncio.Protocol):
    # This method is called when a new client connection is established
    def connection_made(self, transport):
        # Save a reference to the transport object
        self.transport = transport
        # Get the peer name of the client
        peername = transport.get_extra_info("peername")
        # Print a message
        print(f"Connection from {peername}")

    # This method is called when data is received from the client
    def data_received(self, data):
        # Decode the data from bytes to string
        message = data.decode()
        # Print a message
        print(f"Data received: {message}")
        # Send back the same data to the client
        self.transport.write(data)
        # Print a message
        print(f"Data sent: {message}")

    # This method is called when the client connection is closed
    def connection_lost(self, exc):
        # Print a message
        print("Connection closed")
        # Close the transport
        self.transport.close()


# Define an asynchronous function that creates and runs the server
async def main():
    # Get the current event loop
    loop = asyncio.get_running_loop()
    # Create a TCP server using the loop and the protocol class
    server = await loop.create_server(EchoProtocol, "0.0.0.0", 8888)
    # Get the server address and port
    addr = server.sockets[0].getsockname()
    # Print a message
    print(f"Serving on {addr}")
    # Run the server until it is stopped
    async with server:
        await server.serve_forever()


# Run the main function using asyncio.run()
asyncio.run(main())
