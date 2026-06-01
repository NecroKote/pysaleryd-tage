import asyncio
from contextlib import asynccontextmanager

from websockets.asyncio.client import connect

from .device.device import SalerydDevice


@asynccontextmanager
async def connected_device(host: str, port: int = 3001):
    device = SalerydDevice()
    disconnected = asyncio.Event()

    async def _consumer(ws):
        async for message in ws:
            await device.on_receive(message)
        disconnected.set()

    async def _producer(ws):
        await device.process(ws.send)

    async with connect(f"ws://{host}:{port}") as ws:
        consumer_task = asyncio.create_task(_consumer(ws))
        producer_task = asyncio.create_task(_producer(ws))

        try:
            await asyncio.wait_for(device.is_ready.wait(), timeout=5)
            yield device, disconnected

        finally:
            consumer_task.cancel()
            producer_task.cancel()
            await asyncio.gather(consumer_task, producer_task, return_exceptions=True)
