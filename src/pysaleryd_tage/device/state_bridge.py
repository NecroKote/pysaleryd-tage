from .command import (
    ActiveModeCommand,
    ComposedCommand,
    PacModeSettingsCommand,
    PercentModeSettingsCommand,
    PowerCommand,
    PressureModeSettingsCommand,
)
from .state import DeviceState


def get_current_state_command(state: DeviceState) -> ComposedCommand:
    """
    Get a command that would set the device to the current state.

    Useful for storing the current state as "want" state, e.g. before going to away mode, and then restoring it later.
    """

    command = ComposedCommand()
    command += PowerCommand(power=state.mode != DeviceState.RegulateMode.OFF)

    if state.mode in (
        DeviceState.RegulateMode.PERCENT,
        DeviceState.RegulateMode.PRESSURE,
        DeviceState.RegulateMode.PAC,
    ):
        command += ActiveModeCommand(mode=state.mode)

    if state.mode == DeviceState.RegulateMode.PERCENT:
        command += PercentModeSettingsCommand(
            normal=state.percent_normal,
            away=state.percent_away,
            airing=state.percent_airing,
        )
    elif state.mode == DeviceState.RegulateMode.PRESSURE:
        command += PressureModeSettingsCommand(pressure=state.pressure_set)
    elif state.mode == DeviceState.RegulateMode.PAC:
        command += PacModeSettingsCommand(
            cold_temp=state.pac_cold_temp,
            cold_pressure=state.pac_cold_pressure,
            hot_temp=state.pac_hot_temp,
            hot_pressure=state.pac_hot_pressure,
        )

    return command
