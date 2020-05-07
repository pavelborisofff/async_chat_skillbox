"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from collections import deque


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode('utf8').strip()

        print(f'{f"<{self.login}>: " if self.login else ""}{decoded}')

        if self.login is not None:
            self.send_message(decoded)
        else:
            # login:User
            if decoded.startswith('login:'):
                login = decoded.replace('login:', '').strip()
                if login in [client.login for client in self.server.clients]:
                    self.transport.write(f'Login "{login}" already exists, choose other\n'.encode('utf8'))
                    self.transport.close()
                else:
                    self.login = login
                    if self.server.history:
                        self.transport.write(
                            f'Hi {self.login}!\nThat\'s what you missed\n'.encode('utf8')
                        )
                        self.send_history()
                    else:
                        self.transport.write(
                            f'Hi {self.login}!\n'.encode('utf8')
                        )
            else:
                self.transport.write(
                    'Bad login\n'.encode('utf8')
                )

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print('New client')

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print(f'Client {f"{self.login} " if self.login else ""}left')

    def send_message(self, content: str):
        self.server.history.append(f'<{self.login}>: {content}\n')
        message = f'<{self.login}>: {content}\n'

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(message.encode('utf8'))

    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode('utf8'))


class Server(object):
    clients: list
    history: deque

    def __init__(self):
        self.clients = []
        self.history = deque(maxlen=10)

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print('Server running ...')

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print('Server halted manually')
