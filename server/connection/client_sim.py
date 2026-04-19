import asyncio
import json

async def client():
    reader, writer = await asyncio.open_connection("127.0.0.1", 5000)

    mensaje = {
    "report_type": "ROBO/HURTO",
    "datetime": "2026-04-19 20:00:00",
    "lat": 55.0,
    "long": 55.0,
    "detail": "Robo en chacabuco"

    }  
    
    print("Enviando mensaje...")
    writer.write(json.dumps(mensaje).encode("utf-8"))
    await writer.drain()

asyncio.run(client())