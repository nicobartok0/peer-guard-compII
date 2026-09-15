import asyncio
import os
from dotenv import load_dotenv
import json
import redis.asyncio as aioredis
from server.validator.validator import Validator
from server.tasks.enrichment import enriquecer
from pathlib import Path
import socket

class ConnectionManager:
    def __init__(self):
        load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
        self.output_queue = asyncio.Queue()
        self.clients = set()

        # Cliente Redis asíncrono para Pub/Sub
        # (no podemos usar el cliente síncrono dentro de asyncio)
        self._redis = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=2,
            decode_responses=True,
        )

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
            print(f"Lectura finalizada: {peer}")
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            print(f"Cerrando conexión: {peer}")

    async def _responder(self, writer, ok: bool, mensaje: str):
        respuesta = json.dumps({"ok": ok, "mensaje": mensaje}) + "\n"
        writer.write(respuesta.encode())
        await writer.drain()

    async def _broadcast_heatmap(self, heatmap: dict) -> None:
        if not self.clients:
            return
        mensaje = json.dumps({"tipo": "heatmap_update", "data": heatmap}) + "\n"
        clientes_caidos = set()
        for writer in self.clients:
            try:
                writer.write(mensaje.encode())
                await writer.drain()
            except Exception:
                # Si el cliente se cayó, lo marcamos para sacar del set
                clientes_caidos.add(writer)
        self.clients -= clientes_caidos

    async def _escuchar_heatmap(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("heatmap_update")
        print("Suscrito al canal heatmap_update")

        async for mensaje in pubsub.listen():
            if mensaje["type"] != "message":
                # El primer mensaje es siempre una confirmación de suscripción,
                # no datos reales — lo ignoramos.
                continue
            try:
                heatmap = json.loads(mensaje["data"])
                await self._broadcast_heatmap(heatmap)
                print(f"Heatmap broadcasteado a {len(self.clients)} cliente/s")
            except json.JSONDecodeError:
                print("Error decodificando heatmap desde Pub/Sub")

    async def _crear_servidor(self, host: str, port: int):
        try:
            server = await asyncio.start_server(self.handle_client, host, port)
            print(f"Escuchando en {host}:{port}")
            return server
        except OSError as e:
            print(f"No se pudo abrir socket en {host}:{port}: {e}")
            return None

    async def open(self):
        port = int(os.getenv("SERVER_PORT"))

        # getaddrinfo devuelve una lista de tuplas:
        # (family, type, proto, canonname, sockaddr)
        # Usamos AI_PASSIVE para obtener las direcciones de escucha
        # (equivalente a 0.0.0.0 para IPv4 y :: para IPv6)
        infos = await asyncio.get_event_loop().getaddrinfo(
            None,          # host None + AI_PASSIVE = todas las interfaces
            port,
            type=socket.SOCK_STREAM,
            flags=socket.AI_PASSIVE,
        )

        # Filtramos duplicados por familia — en algunos sistemas getaddrinfo
        # puede devolver la misma familia más de una vez
        familias_vistas = set()
        servidores = []
        for family, *_, sockaddr in infos:
            if family in familias_vistas:
                continue
            familias_vistas.add(family)
            host = sockaddr[0]
            servidor = await self._crear_servidor(host, port)
            if servidor is not None:
                servidores.append(servidor)

        if not servidores:
            print("No se pudo abrir ningún socket. Abortando.")
            return

        print(f"Servidor async escuchando en {len(servidores)} interfaz/ces...")

        async with asyncio.TaskGroup() as tg:
            for servidor in servidores:
                tg.create_task(servidor.serve_forever())
            tg.create_task(self._escuchar_heatmap())
    def run(self):
        asyncio.run(self.open())

if __name__ == "__main__":
    test_conn = ConnectionManager()
    test_conn.run()