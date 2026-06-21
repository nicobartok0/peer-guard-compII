# El objeto de este módulo será encargado de manejar las
# conexiones utilizando socket.
# Esto es tanto para las consultas HACIA la db como DESDE la db.
import asyncio
import os
from dotenv import load_dotenv
import json
from server.validator.validator import Validator
from server.tasks.enrichment import enriquecer
from pathlib import Path

class ConnectionManager:
    def __init__(self):
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

        # Cola entre el CONNECTION MANAGER y el cliente
        # (heatmap / broadcast, vía Redis)
        self.output_queue = asyncio.Queue()

        # Set de clientes
        self.clients = set()

    async def handle_client(self, reader, writer):
        self.clients.add(writer)
        print("Cliente añadido")

        try:
            while True:
                data = await reader.readuntil(b"\n")
                message_str = data.decode().strip()

                try:
                    message_json = json.loads(message_str)
                except json.JSONDecodeError:
                    await self._responder(writer, False, "JSON inválido")
                    continue

                ok, resultado = Validator.validate(message_json)

                if ok:
                    enriquecer.delay(resultado)
                    await self._responder(writer, True, "Reporte recibido")
                else:
                    await self._responder(writer, False, resultado)

        except asyncio.IncompleteReadError:
            print("Lectura finalizada (Incomplete Read)")
        finally:
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()
            print("Cerrando...")

    async def _responder(self, writer, ok: bool, mensaje: str):
        respuesta = json.dumps({"ok": ok, "mensaje": mensaje}) + "\n"
        writer.write(respuesta.encode())
        await writer.drain()

    async def open(self):
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