import asyncio

class Agent:
    def __init__(self, local_host, local_port, agent_port):
        self.local_host = local_host
        self.local_port = local_port
        self.agent_port = agent_port

    async def handle_server(self, reader, writer):
        local_reader, local_writer = await asyncio.open_connection(self.local_host, self.local_port)

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

        task1 = asyncio.create_task(forward_data(reader, local_writer))
        task2 = asyncio.create_task(forward_data(local_reader, writer))
        await asyncio.wait([task1, task2], return_when=asyncio.FIRST_COMPLETED)

        local_writer.close()
        writer.close()
        await local_writer.wait_closed()
        await writer.wait_closed()

    async def start_agent(self):
        server = await asyncio.start_server(self.handle_server, '0.0.0.0', self.agent_port)
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    local_host = 'localhost'
    local_port = 80  # Порт, на котором работает nginx
    agent_port = 9000
    agent = Agent(local_host, local_port, agent_port)
    asyncio.run(agent.start_agent())
