from dataclasses import dataclass
from enum import IntEnum
from typing import Protocol, Self

from ..transport.model import WantState


class DeviceCommand(Protocol):
    def to_want_state(self) -> WantState: ...


@dataclass
class ComposedCommand:
    commands: list[DeviceCommand] = None

    def __post_init__(self):
        if self.commands is None:
            self.commands = []

    def add(self, command: DeviceCommand) -> None:
        self.commands.append(command)

    def remove(self, command: DeviceCommand) -> None:
        self.commands.remove(command)

    def __iadd__(self, command: DeviceCommand) -> "Self":
        self.add(command)
        return self

    def __isub__(self, command: DeviceCommand) -> "Self":
        self.remove(command)
        return self

    def to_want_state(self) -> WantState:
        state: WantState = {}
        for cmd in self.commands:
            state.update(cmd.to_want_state())
        return state


class SystemMode(IntEnum):
    OFF = 0
    ON = 1
    # RESET = 2
    # FACTORY = 85


class RegulateMode(IntEnum):
    PERCENT = 1
    PRESSURE = 2
    PAC = 3  # pressure-temperature


def _validate_percent(value: int) -> None:
    if not 20 <= value <= 100:
        raise ValueError(f"Percent must be 20-100, got {value}")


def _validate_pressure(value: int) -> None:
    if not 5 <= value <= 700:
        raise ValueError(f"Pressure must be 5-700 Pa, got {value}")


def _validate_in_range(value: int, min_value: int, max_value: int, name: str) -> None:
    if not min_value <= value <= max_value:
        raise ValueError(f"{name} must be {min_value}-{max_value}, got {value}")


@dataclass
class PowerCommand:
    """Power on/off. Composes with any mode command."""

    power: bool | None = None

    def to_want_state(self) -> WantState:
        if self.power is None:
            return {}
        return {"system_mode_want": SystemMode.ON if self.power else SystemMode.OFF}

    @classmethod
    def on(cls) -> "PowerCommand":
        return cls(power=True)

    @classmethod
    def off(cls) -> "PowerCommand":
        return cls(power=False)


@dataclass
class ActiveModeCommand:
    """Set current active mode"""

    mode: RegulateMode

    def to_want_state(self) -> WantState:
        return {"regulate_mode_want": self.mode}

    @classmethod
    def percent(cls) -> "ActiveModeCommand":
        return cls(mode=RegulateMode.PERCENT)

    @classmethod
    def pressure(cls) -> "ActiveModeCommand":
        return cls(mode=RegulateMode.PRESSURE)

    @classmethod
    def pac(cls) -> "ActiveModeCommand":
        return cls(mode=RegulateMode.PAC)


@dataclass
class PercentModeSettingsCommand:
    """
    Percent-regulated mode settings for `RegulateMode.PERCENT`.

    A set of predefined % values for individual cases:
    - Normal - daily normal mode
    - Away - triggered via remote. Usually lowered setting to conserve energy
    - Airing - triggered via remote. Usually higher setting to accommodate higher
    """

    normal: int | None = None
    away: int | None = None
    airing: int | None = None

    def __post_init__(self):
        for val in (self.normal, self.away, self.airing):
            if val is not None:
                _validate_percent(val)

    def to_want_state(self) -> WantState:
        state: WantState = {}
        if self.normal is not None:
            state["percent_want"] = self.normal
        if self.away is not None:
            state["away_want"] = self.away
        if self.airing is not None:
            state["airing_want"] = self.airing
        return state


@dataclass
class PressureModeSettingsCommand:
    """
    Pressure-regulated mode settings for `RegulateMode.PRESSURE`

    Set's target pressure to a constant value.
    """

    pressure: int

    def __post_init__(self):
        _validate_pressure(self.pressure)

    def to_want_state(self) -> WantState:
        return {"pressure_want": self.pressure}


@dataclass
class PacModeSettingsCommand:
    """
    PAC (temperature driven pressure) mode for `RegulateMode.PAC`.

    Defines two points on a 2-axis chart, that linearly controls the target pressure:
    - cold point - set's the lower-left point on the chart
    - hot point - set's the upper-right point on the chart

    The active pressure target will be chosen based on current Outside temperature within the given limits
    """

    cold_pressure: int | None = None
    cold_temp: float | None = None

    hot_pressure: int | None = None
    hot_temp: float | None = None

    def __post_init__(self):
        self.cold_pressure is not None and _validate_pressure(self.cold_pressure)
        self.cold_temp is not None and _validate_in_range(
            self.cold_temp, -20, 40, "cold_temp"
        )
        self.hot_pressure is not None and _validate_pressure(self.hot_pressure)
        self.hot_temp is not None and _validate_in_range(
            self.hot_temp, -20, 40, "hot_temp"
        )

        if self.cold_temp and self.hot_temp and self.cold_temp > self.hot_temp:
            raise ValueError("Cold temp cannot be higher than hot temp")

    def to_want_state(self) -> WantState:
        state: WantState = {}
        if self.cold_pressure is not None:
            state["pressure_1_want"] = self.cold_pressure
        if self.cold_temp is not None:
            state["temp_1_want"] = int(self.cold_temp * 10.0)

        if self.hot_pressure is not None:
            state["pressure_2_want"] = self.hot_pressure
        if self.hot_temp is not None:
            state["temp_2_want"] = int(self.hot_temp * 10.0)

        return state
