import asyncio
from contextlib import asynccontextmanager

from websockets.asyncio.client import connect

from .device.device import SalerydDevice


@asynccontextmanager
async def connected_device(
    host: str,
    port: int = 3001,
    recv_timeout: float | None = 4.0,
):
    device = SalerydDevice()
    disconnected = asyncio.Event()

    async def _consumer(ws, event: asyncio.Event):
        async for message in ws:
            event.set()
            await device.on_receive(message)

        disconnected.set()

    async def _producer(ws):
        await device.process(ws.send)

    async def _consumer_watchdog(ws, event: asyncio.Event):
        while True:
            event.clear()
            await asyncio.sleep(recv_timeout)
            if not event.is_set():
                break

        disconnected.set()

    async with connect(
        f"ws://{host}:{port}",
        ping_interval=None,
        ping_timeout=None,
    ) as ws:
        got_packet_event = asyncio.Event()

        tasks = [
            asyncio.create_task(_consumer(ws, got_packet_event)),
            asyncio.create_task(_producer(ws)),
        ]

        if recv_timeout is not None:
            tasks.append(asyncio.create_task(_consumer_watchdog(ws, got_packet_event)))

        try:
            await asyncio.wait_for(device.is_ready.wait(), timeout=recv_timeout)
            yield device, disconnected

        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
