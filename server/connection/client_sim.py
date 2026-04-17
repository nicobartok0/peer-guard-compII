import asyncio

async def client():
    reader, writer = await asyncio.open_connection("127.0.0.1", 5000)

    print("Enviando mensaje...")
    writer.write(b"Hola servidor")
    await writer.drain()

    data = await reader.read(1024)
    print("Respuesta del servidor:", data.decode())

    writer.close()
    await writer.wait_closed()

asyncio.run(client())