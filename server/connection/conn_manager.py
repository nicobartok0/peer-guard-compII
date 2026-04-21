# El objeto de este módulo será encargado de manejar las
# conexiones utilizando socket.
# Esto es tanto para las consultas HACIA la db como DESDE la db.

import asyncio
import os
from dotenv import load_dotenv
import json
from server.factory.report_factory import ReportFactory
from server.validator.validator import Validator

class ConnectionManager:
    def __init__(self):
        load_dotenv()
        # Creo la cola entre el CONNECTION MANAGER y
        # los worker de ENRIQUECIMIENTO
        self.input_queue = asyncio.Queue()

        # Creo la cola entre el CONNECTION MANAGER y
        # el cliente (Recibirá por REDIS)
        self.output_queue = asyncio.Queue()

        # Creo un SET de clientes
        self.clients = set()

    # Función asíncrona de manejo de clientes para cada cliente
    async def handle_client(self, reader, writer):
        # añado el writer del cliente actual al set
        self.clients.add(writer)
        print("Cliente añadido")

        try:
            while True:
                # Leo la información hasta el código de escape
                # ACÁ hay un error
                print("Leyendo información...")
                data = await reader.readuntil(b"\n")
                message_str = data.decode().strip()
                print("MEnsaje: ",      message_str)

                try:
                    # Intento cargar el JSON del mensaje
                    message_json = json.loads(message_str)
                    print("Mensaje cargado.")
                except json.JSONDecodeError:
                    print("JSON Inválido:", message_str)
                    continue

                print("Recibido JSON: ", message_json)

                # Ingreso el JSON a la cola del receptor
                print(type(message_json))
                await self.input_queue.put(
                    (writer, 
                     ReportFactory.create(
                        Validator.validate(message_json)[1]
                        )
                    )
                )
                # DEBUG: Sacar más adelante. Imprime si el objeto llega a estar en la QUEUE
                print(list(self.input_queue._queue))
        except asyncio.IncompleteReadError:
            print("Lectura finalizada (Incomplete Read)")
            pass
        finally:
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()
            print("Cerrando...")

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
    #input_queue = asyncio.Queue()
    #output_queue = asyncio.Queue()
    
    test_conn = ConnectionManager()
    test_conn.run()