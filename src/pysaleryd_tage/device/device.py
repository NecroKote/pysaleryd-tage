import asyncio
from typing import Any, Callable

from ..observable import Observable
from ..transport.device import DeviceState as TransportDeviceState
from ..transport.device import SalerydDeviceTransport, SendCallback
from .command import DeviceCommand
from .info import DeviceInfo
from .state import DeviceState

type StateCallback = Callable[[DeviceState], Any]


class SalerydDevice:
    """
    - keeps the transport
    - passed packets to transport
    - hold current readable state
    - hold "static" device info
    """

    def __init__(self) -> None:
        self._transport_state_observable = Observable[TransportDeviceState]().subscribe(
            self._on_raw_state_changed
        )
        self._transport = SalerydDeviceTransport(self._transport_state_observable)
        self.observable_state = Observable[DeviceState]()
        self.is_ready = asyncio.Event()
        self._info: DeviceInfo | None = None

    def subscribe(self, callback: StateCallback) -> None:
        self.observable_state.subscribe(callback)

    def unsubscribe(self, callback: StateCallback) -> None:
        self.observable_state.unsubscribe(callback)

    async def _on_raw_state_changed(self, state: TransportDeviceState) -> None:
        if not self.is_ready.is_set():
            self._info = DeviceInfo.from_state(state)

        self.is_ready.set()
        device_state = DeviceState.from_state(state)
        await self.observable_state.notify(device_state)

    @property
    def state(self) -> DeviceState | None:
        if raw_state := self._transport.latest_state():
            return DeviceState.from_state(raw_state)

    @property
    def info(self) -> DeviceInfo | None:
        return self._info

    async def on_receive(self, packet: bytes) -> None:
        await self._transport.on_packet(packet)

    async def send_command(self, command: DeviceCommand):
        await self._transport.set_values(command.to_want_state())

    async def process(self, send_cb: SendCallback) -> None:
        while True:
            await self._transport.process_pending(send_cb)
            await asyncio.sleep(0.1)
