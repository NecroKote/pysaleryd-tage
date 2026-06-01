from .model import DeviceStateWant, FieldState, PacketHeader, WantState


class DeviceStateWantCommandBuilder:
    def __init__(self, device_type: PacketHeader.DeviceType):
        self.field_map = DeviceStateWant.get_builder().build()

        self._device_type = device_type
        self._mod_state = {}

    def update(self, values: WantState):
        for k, v in values.items():
            if k not in self.field_map:
                raise ValueError(f"Unknown field for want state: {k}")

        self._mod_state.update(values)
        return self

    def _get_combined_state(self, current_state: FieldState):
        want = {}

        # apply current state
        for want_field in self.field_map.keys():
            want[want_field] = current_state[want_field]

        # apply updates
        want.update(self._mod_state)

        return want

    def build(self, state: FieldState, device_header: bytes) -> bytes:
        want_state = self._get_combined_state(state)

        packet_header = PacketHeader(
            packet_type=PacketHeader.Type.DEVICE_SET,
            device_type=self._device_type,
        )

        return (
            packet_header.encode() + device_header + DeviceStateWant.encode(want_state)
        )
