from dataclasses import dataclass
from typing import Self

from ..transport.device import DeviceState as TransportDeviceState
from ..transport.model import PacketHeader


@dataclass
class DeviceInfo:
    """contains device stats that doesn't change that often"""

    device_type: PacketHeader.DeviceType
    wifi_mac: str
    wifi_version: str
    ctrl_version: str
    name: str

    @classmethod
    def from_state(cls, transport_state: TransportDeviceState) -> Self:
        header, state = transport_state

        return cls(
            device_type=PacketHeader.DeviceType(state["device_type_is"]),
            wifi_mac=":".join(hex(b)[2:] for b in header["mac"]),
            wifi_version=header["version"],
            ctrl_version=".".join(str(state["program_version_ctrlsys_is"])),
            name=state["name_is"],
        )
