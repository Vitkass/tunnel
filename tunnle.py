import asyncio

class TunnelServer:
    def __init__(self, agent_host, agent_port, public_port):
        self.agent_host = agent_host
        self.agent_port = agent_port
        self.public_port = public_port

    async def handle_client(self, reader, writer):
        agent_reader, agent_writer = await asyncio.open_connection(self.agent_host, self.agent_port)

        async def forward_data(source, destination):
            try:
                while True:
                    data = await source.read(1024)
                    if not data:
                        break
                    destination.write(data)
                    await destination.drain()
            except asyncio.CancelledError:
                pass

        task1 = asyncio.create_task(forward_data(reader, agent_writer))
        task2 = asyncio.create_task(forward_data(agent_reader, writer))
        await asyncio.wait([task1, task2], return_when=asyncio.FIRST_COMPLETED)

        agent_writer.close()
        writer.close()
        await agent_writer.wait_closed()
        await writer.wait_closed()

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.public_port)
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    agent_host = 'localhost'
    agent_port = 9000
    public_port = 8000
    server = TunnelServer(agent_host, agent_port, public_port)
    asyncio.run(server.start_server())
