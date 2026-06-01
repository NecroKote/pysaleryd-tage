from asyncio import Event, Future
from logging import getLogger
from typing import Awaitable, Callable, NamedTuple

from ..observable import Observable
from .command import DeviceStateWantCommandBuilder
from .model import DeviceHeader, DeviceStateIs, FieldState, PacketHeader, WantState

type SendCallback = Callable[[bytes], Awaitable[None]]
type RawStateChangedCallback = Callable[[DeviceState], Awaitable[None]]


class DeviceStateParts(NamedTuple):
    raw_header: bytes
    header: FieldState
    state: FieldState


class DeviceState(NamedTuple):
    header: FieldState
    state: FieldState


class SalerydDeviceTransport:
    """Handles Saleryd device transport level communication and state management"""

    def __init__(self, state_observable: Observable[DeviceState] | None = None):
        self._log = getLogger(self.__class__.__name__)
        self._pending_value_applies: list[tuple[WantState, Future[None]]] = []

        self._got_fresh_device_packet = Event()
        self._last_device_packet_parts: DeviceStateParts | None = None

        self._state_observable = state_observable

    async def on_packet(self, packet: bytes):
        if len(packet) < PacketHeader.SIZE:
            self._log.warning("Received too short packet (%d bytes)", len(packet))
            return

        header, msg = (
            PacketHeader.from_bytes(packet[: PacketHeader.SIZE]),
            packet[PacketHeader.SIZE :],
        )

        match header:
            case PacketHeader(packet_type=PacketHeader.Type.MODULE_SETTINGS):
                self._log.debug("< module settings packet")
                # module_settings = ModuleSetting.decode(msg[: header.packet_size])
                ...

            case PacketHeader(packet_type=PacketHeader.Type.DEVICE):
                self._log.debug("< device state packet")

                header_bytes = msg[: header.header_size]
                device_header = DeviceHeader.decode(header_bytes)

                body_bytes = msg[
                    header.header_size : header.header_size + header.packet_size
                ]
                device_state = DeviceStateIs.decode(body_bytes)

                self._last_device_packet_parts = DeviceStateParts(
                    header_bytes,
                    device_header,
                    device_state,
                )
                self._got_fresh_device_packet.set()

                # notify callbacks in parallel
                if self._state_observable:
                    await self._state_observable.notify(
                        DeviceState(device_header, device_state)
                    )

            # case PacketHeader(packet_type=PacketHeader.Type.DEVICE_SET):
            #     device_header_raw = msg[: DeviceHeader.SIZE]
            #     device_header = DeviceHeader.decode(device_header_raw)
            #     device_state_raw = msg[DeviceHeader.SIZE :]
            #     want_state = DeviceStateWant.decode(device_state_raw)

            case _:
                self._log.warning("Unknown packet type %s", header.packet_type)

    def set_values(self, values: WantState):
        """schedule the desired field value changes"""

        self._log.debug("scheduling setting values: %r ...", values)

        future: Future[None] = Future()
        self._pending_value_applies.append((values, future))

        return future

    async def process_pending(self, byte_writer: SendCallback):
        """
        Check pending value applications and send commands if needed
        """

        if not self._pending_value_applies:
            return

        builder = DeviceStateWantCommandBuilder(PacketHeader.DeviceType.TAGE)

        # combine all pending value applications and gather all the futures to be resolved
        futures: list[Future[None]] = []
        while self._pending_value_applies:
            values, future = self._pending_value_applies.pop(0)

            try:
                builder.update(values)
            except Exception as e:
                self._log.warning("failed building command: %s", e)
                future.set_exception(e)
                continue

            futures.append(future)

        if not futures:
            return

        self._log.debug("waiting for fresh device packet to build command ...")

        self._got_fresh_device_packet.clear()
        await self._got_fresh_device_packet.wait()

        self._log.debug("building set command command using fresh state ...")
        # build and send command
        try:
            if parts := self._last_device_packet_parts:
                command = builder.build(parts.state, parts.raw_header)
                self._log.debug(
                    "-> sending device set command (%d bytes)", len(command)
                )
                await byte_writer(command)

        except Exception as e:
            self._log.warning("failed sending command: %s", e)

            # fail all futures
            for future in futures:
                future.set_exception(e)
        else:
            # resolve all futures
            for future in futures:
                future.set_result(None)

    def latest_state(self) -> DeviceState | None:
        """get the latest known device state"""

        if parts := self._last_device_packet_parts:
            return DeviceState(parts.header, parts.state)

        return None

    async def get_latest_state(self, refresh: bool = False) -> DeviceState:
        """wait for and get the latest known device state"""

        if refresh:
            self._got_fresh_device_packet.clear()

        await self._got_fresh_device_packet.wait()

        if state := self.latest_state():
            return state

        raise RuntimeError("no device state available")
