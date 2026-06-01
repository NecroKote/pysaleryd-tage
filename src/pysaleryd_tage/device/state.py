from dataclasses import dataclass
from enum import IntEnum
from typing import Self

from ..transport.device import DeviceState as TransportDeviceState


@dataclass
class DeviceState:
    class RegulateMode(IntEnum):
        OFF = 0
        PERCENT = 1
        PRESSURE = 2
        PAC = 3
        AWAY = 4
        AIRING = 5
        HUMIDITY = 6
        PRESSURE_TEST = 7
        FORCED_OFF = 8
        FORCED_PERCENT = 9
        FORCED_PRESSURE = 10
        WK_OFF = 11
        WK_AWAY = 12
        WK_AIRING = 13
        NEXA_AWAY = 14
        NEXA_AIRING = 15
        SUMMER_AIRING = 16

    # current state
    mode: RegulateMode
    temp_in: float
    temp_out: float
    pressure: int
    percent: int

    # alarm states
    alarm_pressure_sensor: bool
    alarm_pressure_reached: bool
    alarm_temp_out: bool
    alarm_temp_in: bool
    alarm_fan: bool
    alarm_in_sync: bool

    # current settings
    percent_normal: int
    percent_away: int
    percent_airing: int
    pressure_set: int
    pac_cold_temp: int
    pac_cold_pressure: int
    pac_hot_temp: int
    pac_hot_pressure: int

    # optional state
    humidity_out: int | None = None
    humidity_in: int | None = None

    @classmethod
    def from_state(cls, transport_state: TransportDeviceState) -> Self:
        header, state = transport_state
        temp_divisor = 10.0

        return cls(
            mode=cls.RegulateMode(state["regulate_mode_is"]),
            temp_in=state["temp_2_is"] / temp_divisor,
            temp_out=state["temp_1_is"] / temp_divisor,
            pressure=state["pressure_is"],
            percent=state["percent_is"],
            alarm_pressure_sensor=state["pressure_error_is"] != 0,
            alarm_pressure_reached=state["pressure_limit_error_is"] != 0,
            alarm_temp_out=state["temp_1_error_is"] != 0,
            alarm_temp_in=state["temp_2_error_is"] != 0,
            alarm_fan=state["fan_error_is"] != 0,
            alarm_in_sync=header["synced_ctrlsys"] != 1,
            percent_normal=state["percent_set_is"],
            percent_away=state["away_set_is"],
            percent_airing=state["airing_set_is"],
            pressure_set=state["pressure_set_is"],
            pac_cold_temp=state["temp_1_set_is"] / temp_divisor,
            pac_cold_pressure=state["pressure_1_set_is"],
            pac_hot_temp=state["temp_2_set_is"] / temp_divisor,
            pac_hot_pressure=state["pressure_2_set_is"],
            humidity_in=state["dallas_ch_2_inside_is"] or None,
            humidity_out=state["dallas_ch_1_outside_is"] or None,
        )
