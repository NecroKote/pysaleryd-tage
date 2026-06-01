from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from ..codec.field import (
    FieldMapBuilder,
    FieldType,
)
from ..codec.mixin import (
    DecodeableFieldsObject,
    EncodeableFieldsObject,
)

FieldState = dict[str, Any]
WantState = FieldState


@dataclass
class PacketHeader:
    SIZE = 12

    class Type(IntEnum):
        UNKNOWN = 0
        DEVICE = 1
        DEVICE_GET = 2
        DEVICE_SET = 3
        PACKET_TYPE_UPDATE_INFO = 4
        UPDATE_ABORT = 5
        UPDATE_START_UPLOAD_ESP = 6
        UPDATE_START_UPLOAD_WEB = 7
        UPDATE_START_UPLOAD_CTRLSYS = 8
        UPDATE_START_DISTRIBUTION = 9
        UPDATE_COMPLETE = 10
        UPDATE_ESP = 11
        UPDATE_WEB = 12
        UPDATE_CTRLSYS = 13
        REBOOT = 14
        ROUTER = 15
        ROUTER_SET = 16
        TIME = 17
        TEMPERATURE = 18
        START_MESH = 19
        PACKET_TYPE_MESH_BE_QUIET = 20
        PACKET_TYPE_MESH_BE_NORMAL = 21
        PACKET_TYPE_LED_PING = 22
        MODULE_SETTINGS = 23

    class DeviceType(IntEnum):
        UNKNOWN = 0
        ERIK = 1
        TAGE = 2
        EMIL = 3
        CARL = 4
        EXTENDER = 7

    packet_type: Type
    crc: int = 0
    device_type: DeviceType = DeviceType.UNKNOWN
    header_size: int = 0
    packet_size: int = 0
    last_frame: int = 0
    reserved_1: int | None = None
    reserved_2: int | None = None

    @classmethod
    def from_bytes(cls, e: bytes):
        crc = (e[3] << 24) | (e[2] << 16) | (e[1] << 8) | e[0]
        packet_type = e[4]
        device_type = cls.DeviceType(e[5])
        header_size = (e[7] << 8) | e[6]
        packet_size = (e[9] << 8) | e[8]
        last_frame = e[10] & 1
        return cls(
            cls.Type(packet_type),
            crc,
            device_type,
            header_size,
            packet_size,
            last_frame,
        )

    def encode(self):
        e = bytearray(PacketHeader.SIZE)
        e[4] = self.packet_type.value
        e[5] = self.device_type
        return bytes(e)


class ModuleSettings(DecodeableFieldsObject):
    decode_field_map = (
        FieldMapBuilder()
        .add_field("sta_ssid", 264, type=FieldType.STRING)
        .add_field("sta_ip", 264, type=FieldType.STRING)
        .add_field("time_year", 8)
        .add_field("time_month", 4)
        .add_field("time_weekday", 3)
        .add_field("time_day", 5)
        .add_field("time_hour", 5)
        .add_field("time_minute", 6)
        .add_field("time_second", 6)
        .build()
    )


class DeviceHeader(DecodeableFieldsObject, EncodeableFieldsObject):
    SIZE = 52

    encode_field_map = decode_field_map = (
        FieldMapBuilder()
        .add_field("root_list_index", 16, True)
        .add_field("mac", 48, type=FieldType.ARRAY, length_per_item=8)
        .add_field("mesh_connected", 8)
        .add_field("synced_ctrlsys", 1)
        .add_field("alarm", 1)
        .add_field("reserved_1", 6)
        .add_field("version", 128, type=FieldType.STRING)
        .add_field("rssi", 8, True)
        .add_field("channel", 8)
        .add_field("mesh_parent_bssid", 48, type=FieldType.ARRAY, length_per_item=8)
        .add_field("mesh_layer", 8)
        .add_field("heap", 32)
        # HELP: size 104 of reserved_2 is different from what's in the page source,
        # but matches observed data and is needed to reach the correct total size of 52 bytes
        .add_field("reserved_2", 104, type=FieldType.ARRAY, length_per_item=8)
        .build()
    )


def add_week_timer_fields(b: FieldMapBuilder, num_timers: int, suffix: str):
    for i in range(num_timers):
        b.add_field(f"week_timer_{i}_active_{suffix}", 1)
        b.add_field(f"week_timer_{i}_time_point_mode_{suffix}", 2)
        b.add_field(f"week_timer_{i}_mode_{suffix}", 5)
        b.add_field(f"week_timer_{i}_day_{suffix}", 3)
        b.add_field(f"week_timer_{i}_hour_{suffix}", 5)


class DeviceStateWant(DecodeableFieldsObject, EncodeableFieldsObject):
    """
    Represents the desired settings to be applied to the device.
    """

    # SIZE = 117

    @classmethod
    def get_builder(cls):
        return (
            FieldMapBuilder()
            .add_field("findlight_want", 1)
            .add_field("set_name_want", 1)
            .add_field("nexa_1_set_want", 1)
            .add_field("nexa_2_set_want", 1)
            .add_field("nexa_1_clear_want", 1)
            .add_field("nexa_2_clear_want", 1)
            .add_field("nexa_reset_want", 1)
            .add_field("pressure_test_want", 1)
            .add_field("pressure_sensor_calibrate_want", 1)
            .add_field("remove_me_from_mesh_want", 1)
            .add_field("humid_mode_want", 1)
            .add_field("reserved_1_want", 5)
            .add_field("remove_me_from_mesh_magic_want", 8)
            .add_field("percent_want", 16, True)
            .add_field("airing_want", 16, True)
            .add_field("away_want", 16, True)
            .add_field("forced_want", 16, True)
            .add_field("pressure_want", 16, True)
            .add_field("pressure_1_want", 16, True)
            .add_field("pressure_2_want", 16, True)
            .add_field("temp_1_want", 16, True)
            .add_field("temp_2_want", 16, True)
            .add_field("regulate_mode_want", 16, True)
            .add_field("system_mode_want", 16, True)
            .add_field("name_want", 128, type=FieldType.ARRAY, length_per_item=8)
            .add_field("summer_mode_want", 1)
            .add_field("reserved_want_2", 7)
            .add_field("summer_cold_start_time_hour_want", 16)
            .add_field("summer_cold_start_time_minute_want", 16)
            .add_field("summer_cold_end_time_hour_want", 16)
            .add_field("summer_cold_end_time_minute_want", 16)
            .add_field("summer_cold_temp_inside_min_want", 16)
            .add_field("summer_cold_temp_inside_max_want", 16)
            .add_field("summer_cold_temp_outside_min_want", 16)
            .add_field("summer_cold_temp_outside_max_want", 16)
            .apply(lambda b: add_week_timer_fields(b, 14, "want"))
            .add_field("regulate_speed_want", 8)
            .add_field("device_type_want", 8)
            .add_field("humid_on_limit_want", 8)
            .add_field("reserved_3_want", 256, type=FieldType.ARRAY, length_per_item=8)
        )

    @classmethod
    def get_decode_field_map(cls):
        fm = cls.get_builder().build()
        return fm

    @classmethod
    def get_encode_field_map(cls):
        return cls.get_builder().build()


class DeviceStateIs(DeviceStateWant):
    """
    Represents the current state of the device, including both desired settings and actual readings.
    """

    @classmethod
    def get_builder(cls):
        return (
            super()
            .get_builder()  # new fields are added on top of "want" fields
            # .add_stub(32)  # skip 4 bytes
            .add_field("findlight_is", 1)
            .add_field("humidity_is", 1)
            .add_field("temp_1_error_is", 1)
            .add_field("temp_2_error_is", 1)
            .add_field("fan_error_is", 1)
            .add_field("pressure_error_is", 1)
            .add_field("pressure_limit_error_is", 1)
            .add_field("reserved_error_1_is", 1)
            .add_field("reserved_error_2_is", 1)
            .add_field("reserved_error_3_is", 1)
            .add_field("summer_mode_is", 1)
            .add_field("pressure_test_is", 1)
            .add_field("humid_mode_is", 1)
            .add_field("discrete_reg_reserved_1", 3)
            .add_field("percent_is", 16, True)
            .add_field("percent_set_is", 16, True)
            .add_field("percent_min", 16, True)
            .add_field("percent_max", 16, True)
            .add_field("airing_is", 16, True)
            .add_field("airing_set_is", 16, True)
            .add_field("airing_min", 16, True)
            .add_field("airing_max", 16, True)
            .add_field("away_is", 16, True)
            .add_field("away_set_is", 16, True)
            .add_field("away_min", 16, True)
            .add_field("away_max", 16, True)
            .add_field("forced_is", 16, True)
            .add_field("forced_set_is", 16, True)
            .add_field("forced_min", 16, True)
            .add_field("forced_max", 16, True)
            .add_field("pressure_is", 16, True)
            .add_field("pressure_set_is", 16, True)
            .add_field("pressure_min", 16, True)
            .add_field("pressure_max", 16, True)
            .add_field("pressure_1_set_is", 16, True)
            .add_field("pressure_1_min", 16, True)
            .add_field("pressure_1_max", 16, True)
            .add_field("pressure_2_set_is", 16, True)
            .add_field("pressure_2_min", 16, True)
            .add_field("pressure_2_max", 16, True)
            .add_field("temp_1_is", 16, True)
            .add_field("temp_1_set_is", 16, True)
            .add_field("temp_1_min", 16, True)
            .add_field("temp_1_max", 16, True)
            .add_field("temp_2_is", 16, True)
            .add_field("temp_2_set_is", 16, True)
            .add_field("temp_2_min", 16, True)
            .add_field("temp_2_max", 16, True)
            .add_field("regulate_mode_is", 16, True)
            .add_field("regulate_mode_set_is", 16, True)
            .add_field("system_mode_is", 16, True)
            .add_field("system_mode_set_is", 16, True)
            .add_field("pressure_sensor_calibrate_is", 16, True)
            .add_field("device_type_is", 16, True)
            .add_field("program_version_ctrlsys_is", 16, True)
            .add_field("program_version_esp_is", 16, True)
            .add_field("name_is", 128, type=FieldType.STRING)
            .add_field("nexa_1_is", 136, type=FieldType.STRING)
            .add_field("nexa_2_is", 136, type=FieldType.STRING)
            .add_field("summer_cold_start_time_hour_is", 16)
            .add_field("summer_cold_start_time_minute_is", 16)
            .add_field("summer_cold_end_time_hour_is", 16)
            .add_field("summer_cold_end_time_minute_is", 16)
            .add_field("summer_cold_temp_inside_min_is", 16)
            .add_field("summer_cold_temp_inside_max_is", 16)
            .add_field("summer_cold_temp_outside_min_is", 16)
            .add_field("summer_cold_temp_outside_max_is", 16)
            .add_field("pressure_test_70_is", 16)
            .add_field("pressure_test_100_is", 16)
            .apply(lambda b: add_week_timer_fields(b, 14, "is"))
            .add_field("regulate_speed_is", 8)
            .add_field("time_year_is", 8)
            .add_field("time_month_is", 8)
            .add_field("time_day_is", 8)
            .add_field("time_weekday_is", 8)
            .add_field("time_hour_is", 8)
            .add_field("time_minute_is", 8)
            .add_field("humid_is", 8)
            .add_field("humid_on_limit_set_is", 8)
            .add_field("humid_on_limit_min_is", 8)
            .add_field("humid_on_limit_max_is", 8)
            .add_field("dallas_ch_1_outside_is", 16, True)
            .add_field("dallas_ch_2_inside_is", 16, True)
        )


WANT_IS_MAP = {
    "system_mode_want": "system_mode_set_is",
    "regulate_mode_want": "regulate_mode_set_is",
    "percent_want": "percent_set_is",
    "away_want": "away_set_is",
    "airing_want": "airing_set_is",
    "forced_want": "forced_set_is",
    "pressure_want": "pressure_set_is",
    "pressure_test_want": "pressure_test_is",
    "pressure_1_want": "pressure_1_set_is",
    "pressure_2_want": "pressure_2_set_is",
    "temp_1_want": "temp_1_set_is",
    "temp_2_want": "temp_2_set_is",
    "humid_on_limit_want": "humid_on_limit_set_is",
    "humid_mode_want": "humid_mode_is",
}


def is_state_in_sync(want: WantState, is_: FieldState) -> bool:
    for want_field, is_field in WANT_IS_MAP.items():
        is_state = is_.get(is_field)
        want_state = want.get(want_field)
        if is_state != want_state:
            return False

    return True
