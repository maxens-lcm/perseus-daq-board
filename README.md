# PERSEUS DAQ Board

Firmware and project files for the PERSEUS DAQ board.

This first import intentionally keeps the firmware repository lightweight: it does not vendor the full ST `fp-sns-allmems1` package. It stores only the SensorTile ALLMEMS1 override files needed for the PERSEUS UART fusion stream.

## Firmware

See:

```text
firmware/sensortile-allmems1-uart-fusion/
```

The overlay starts from ST `FP-SNS-ALLMEMS1`:

```text
Projects/STM32L476JG-SensorTile/Applications/ALLMEMS1
```

Default behavior is conservative: the UART fusion stream is disabled unless `ALLMEMS1_ENABLE_UART_FUSION_STREAM` is explicitly enabled.
