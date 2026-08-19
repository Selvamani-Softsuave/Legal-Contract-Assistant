import asyncio
import websockets

async def f():
    async with websockets.connect('ws://localhost:8080/api/v1/ws/events') as ws:
        print('connected')
        await asyncio.sleep(2)
        print('done')

asyncio.run(f())
