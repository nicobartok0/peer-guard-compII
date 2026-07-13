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

        
        self.output_queue = asyncio.Queue()

        # Set de clientes
        self.clients = set()

    async def handle_client(self, reader, writer):
        self.clients.add(writer)
        peer = writer.get_extra_info("peername")
        print(f"Cliente añadido: {peer}")

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
            print(f"Lectura finalizada (Incomplete Read): {peer}")
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            print(f"Cerrando conexión: {peer}")

    async def _responder(self, writer, ok: bool, mensaje: str):
        respuesta = json.dumps({"ok": ok, "mensaje": mensaje}) + "\n"
        writer.write(respuesta.encode())
        await writer.drain()

    async def _crear_servidor(self, host: str, port: int):
        """Intenta levantar un servidor en el host dado. Devuelve None si falla."""
        try:
            server = await asyncio.start_server(self.handle_client, host, port)
            print(f"Escuchando en {host}:{port}")
            return server
        except OSError as e:
            print(f"No se pudo abrir socket en {host}:{port}: {e}")
            return None

    async def open(self):
        port = int(os.getenv("SERVER_PORT"))

        # Levantamos un servidor por cada familia de direcciones.
        
        servidores = [
            await self._crear_servidor("0.0.0.0", port),  # IPv4
            await self._crear_servidor("::",      port),  # IPv6
        ]

        # Filtramos los que fallaron
        servidores_activos = [s for s in servidores if s is not None]

        if not servidores_activos:
            print("No se pudo abrir ningún socket. Abortando.")
            return

        print(f"Servidor async escuchando en {len(servidores_activos)} interfaz/ces...")

        async with asyncio.TaskGroup() as tg:
            for servidor in servidores_activos:
                tg.create_task(servidor.serve_forever())

    def run(self):
        asyncio.run(self.open())

if __name__ == "__main__":
    test_conn = ConnectionManager()
    test_conn.run()