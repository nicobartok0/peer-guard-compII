import asyncio
import json
import os
from dotenv import load_dotenv
from pathlib import Path



async def client():
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
    print(os.getenv("SERVER_IP"))
    reader, writer = await asyncio.open_connection(os.getenv("SERVER_IP"), os.getenv("SERVER_PORT"))

    mensaje = {
        "report_type": "ROBO/HURTO",
        "datetime": "2026-04-19 20:00:00",
        "lat": -32.889478119247,
        "long": -68.844776140965,
        "detail": "Robo en chacabuco"
    }

    print("Enviando mensaje...")
    writer.write(json.dumps(mensaje).encode("utf-8") + b"\n")
    await writer.drain()

    respuesta = await reader.readuntil(b"\n")
    print("Respuesta del servidor:", respuesta.decode().strip())

    writer.close()
    await writer.wait_closed()

asyncio.run(client())