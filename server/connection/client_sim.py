import asyncio
import json
import os
from dotenv import load_dotenv
from pathlib import Path

async def client():
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
    reader, writer = await asyncio.open_connection(
        os.getenv("SERVER_IP"), os.getenv("SERVER_PORT")
    )

    mensaje = {
        "report_type": "ROBO/HURTO",
        "datetime": "2026-04-19 20:00:00",
        "lat": -32.8908,
        "long": -68.8272,
        "detail": "Robo en mza"
    }

    print("Enviando reporte...")
    writer.write(json.dumps(mensaje).encode("utf-8") + b"\n")
    await writer.drain()

    # Primera respuesta: ACK del reporte
    respuesta = await reader.readuntil(b"\n")
    print("ACK del servidor:", respuesta.decode().strip())

    # A partir de acá, el cliente se queda escuchando updates del heatmap
    print("Esperando actualizaciones del heatmap...\n")
    try:
        while True:
            data = await reader.readuntil(b"\n")
            mensaje_recibido = json.loads(data.decode().strip())

            if mensaje_recibido.get("tipo") == "heatmap_update":
                print("=== HEATMAP ACTUALIZADO ===")
                for zona, franjas in mensaje_recibido["data"].items():
                    print(f"  {zona}:")
                    for franja, intensidad in franjas.items():
                        if franja != "total":
                            print(f"    {franja}: {intensidad}")
                    print(f"    total reportes: {franjas['total']}")
                print("===========================\n")
            else:
                print("Mensaje recibido:", mensaje_recibido)

    except asyncio.IncompleteReadError:
        print("Conexión cerrada por el servidor.")

asyncio.run(client())