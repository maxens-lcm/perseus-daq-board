# SensorTile ALLMEMS1 UART Fusion Overlay

This folder contains only the files changed or added on top of ST `fp-sns-allmems1` for the SensorTile ALLMEMS1 application.

Base ST path:

```text
Projects/STM32L476JG-SensorTile/Applications/ALLMEMS1
```

## Safety policy

The UART stream is opt-in. By default this overlay preserves ST behavior:

- BLE remains unchanged
- SD logging remains unchanged
- sensor acquisition remains unchanged
- MotionFX remains unchanged
- no UART stream is initialized unless enabled explicitly

To enable the UART stream, uncomment this line in `ALLMEMS1_config.h`:

```c
#define ALLMEMS1_ENABLE_UART_FUSION_STREAM
```

When enabled, USB CDC printf is disabled through `ALLMEMS1_DISABLE_USB_CDC` to avoid pin/function conflicts.

## UART settings

Initial debug settings:

```text
Baudrate      : 115200
Data bits     : 8
Parity        : none
Stop bits     : 1
Flow control  : none
Cadence       : 1 Hz by default
```

The SensorTile outputs UART logic. RS422 or RS485 conversion is done by the PERSEUS DAQ board transceivers.

## CoolTerm

Use:

```text
Port          : FTDI / USB serial adapter
Baudrate      : 115200
Data bits     : 8
Parity        : None
Stop bits     : 1
Flow control  : None
Local echo    : Off
```

Expected stream when enabled:

```text
BOOT,ALLMEMS1_UART_FUSION_STREAM
FUS,frame_id,t_ms,dt_ms,ax,ay,az,gx,gy,gz,mx,my,mz,q0,q1,q2,q3,calib
```

## Apply overlay

From a clean ST checkout:

```sh
cd /path/to/fp-sns-allmems1
cp -R /path/to/perseus-daq-board/firmware/sensortile-allmems1-uart-fusion/overrides/* .
```

Then build the normal CubeIDE ALLMEMS1 project.
