# El objeto de este módulo será encargado de manejar las
# conexiones utilizando socket.
# Esto es tanto para las consultas HACIA la db como DESDE la db.

import asyncio
import os
from dotenv import load_dotenv
import json

class ConnectionManager:
    def __init__(self, input_queue, output_queue):
        load_dotenv()
        # Creo la cola entre el CONNECTION MANAGER y
        # los worker de ENRIQUECIMIENTO
        self.input_queue = input_queue

        # Creo la cola entre el CONNECTION MANAGER y
        # el cliente (Recibirá por REDIS)
        self.output_queue = output_queue


        self.clients = set()

    async def handle_client(self, reader, writer):
        self.clients.add(writer)
        try:
            while True:
                data = await reader.readuntil(b"\n")
                message_str = data.decode().strip()

                try:
                    message_json = json.loads(message_str)
                except json.JSONDecodeError:
                    print("JSON Inválido:", message_str)
                    continue

                print("Recibido JSON: ", message_json)

                await self.input_queue.put((writer, message_json))
        except asyncio.IncompleteReadError:
            pass
        finally:
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def open(self):
        print(os.getenv("SERVER_IP"))
        
        server = await asyncio.start_server(
        self.handle_client, str(os.getenv("SERVER_IP")), int(os.getenv("SERVER_PORT"))
        )
        
        print("Servidor async escuchando...")
        
        async with server:
            await server.serve_forever()

    def run(self):
        asyncio.run(self.open())

if __name__ == "__main__":
    test_conn = ConnectionManager()
    test_conn.run()