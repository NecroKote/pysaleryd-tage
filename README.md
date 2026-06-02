# pysaleryd-tage

Python asyncio library for controlling Saleryd HRV units (Erik, Tage, Emil, Carl) over their local WebSocket API.

## Installation

```
pip install pysaleryd-tage
```

## Usage

### Connect and read state

```python
import asyncio
from pysaleryd_tage.client import connected_device

async def main():
    async with connected_device("192.168.1.100") as (device, disconnected):
        print(device.info)   # DeviceInfo: model, MAC, firmware versions
        print(device.state)  # DeviceState: mode, temps, pressure, alarms, ...

        # subscribe to state changes
        device.subscribe(lambda state: print(state.mode, state.temp_in, state.pressure))

        # wait until disconnected or timeout
        await asyncio.wait_for(disconnected.wait(), timeout=60)

asyncio.run(main())
```

`connected_device(host, port=3001)` is an async context manager. It waits (up to 5 s) for the device to send its initial state before yielding. `disconnected` is an `asyncio.Event` set when the WebSocket closes.

### Send commands

```python
from pysaleryd_tage.device.command import (
    ActiveModeCommand,
    ComposedCommand,
    PacModeSettingsCommand,
    PercentModeSettingsCommand,
    PowerCommand,
    PressureModeSettingsCommand,
)

async with connected_device("192.168.1.100") as (device, _):
    # power on/off
    await device.send_command(PowerCommand.on())

    # ComposedCommand bundles multiple commands into one send.
    # Use += to build it incrementally:
    cmd = ComposedCommand()
    cmd += ActiveModeCommand.percent() # change the current mode
    cmd += PercentModeSettingsCommand(normal=60, away=30, airing=80) # setup 
    await device.send_command(cmd)

    # or construct inline
    await device.send_command(
        ComposedCommand([
            ActiveModeCommand.pressure(),
            PressureModeSettingsCommand(pressure=50),
        ])
    )

    # PAC (temperature-driven pressure) mode
    await device.send_command(
        ComposedCommand([
            ActiveModeCommand.pac(),
            PacModeSettingsCommand(cold_temp=0.0, cold_pressure=20,
                                   hot_temp=20.0, hot_pressure=60),
        ])
    )
```

## Disclaimer

This project is not affiliated with, endorsed by, or associated with the manufacturer in any way. Use at your own risk.

## License

MIT
