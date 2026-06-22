#!/usr/bin/env python3
"""uart_fusion_decoder.py

Python script to read and decode the binary UART Fusion frames emitted by the
PERSEUS DAQ board firmware (see uart_fusion_stream.c).

It expects a USB‑to‑UART (FTDI) dongle connected to the STM32 UART5 pins.
The script uses pyserial to read raw bytes, synchronises on the frame sync
pattern (0xA5 0x5A), validates the CRC‑CCITT (0xFFFF seed, polynomial 0x1021) and
prints the decoded fields in a human‑readable format.

Usage:
    python3 uart_fusion_decoder.py --port /dev/ttyUSB0 --baud 9600

Dependencies:
    pip install pyserial
"""
import argparse
import serial
import struct
import sys

SYNC0 = 0xA5
SYNC1 = 0x5A
VERSION = 0x01
TYPE_TELEMETRY = 0x01
PAYLOAD_LEN = 72  # bytes, as defined in uart_fusion_stream.h
FRAME_HEADER_LEN = 6
FRAME_CRC_LEN = 2
FRAME_TOTAL_LEN = FRAME_HEADER_LEN + PAYLOAD_LEN + FRAME_CRC_LEN

def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    """Compute CRC‑CCITT (XModem) over *data*.
    Polynomial 0x1021, seed 0xFFFF.
    """
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def parse_frame(payload: bytes):
    """Parse the telemetry payload into a dict.
    The layout matches the C function UART_FusionStream_SendFrame.
    """
    # struct layout (little‑endian):
    #   uint32_t frame_id
    #   uint32_t t_ms
    #   uint32_t dt_ms
    #   int32_t q0, q1, q2, q3
    #   int32_t ax, ay, az
    #   int32_t gx, gy, gz
    #   int32_t mx, my, mz
    #   int16_t temp_c_x10
    #   int32_t pressure_hpa_x100
    #   uint8_t calib_status
    #   uint8_t status_flags
    fields = struct.unpack('<IIIiiiiiiiiiiiiihI BB', payload)
    keys = [
        'frame_id', 't_ms', 'dt_ms',
        'q0', 'q1', 'q2', 'q3',
        'ax', 'ay', 'az',
        'gx', 'gy', 'gz',
        'mx', 'my', 'mz',
        'temp_c_x10', 'pressure_hpa_x100',
        'calib_status', 'status_flags'
    ]
    return dict(zip(keys, fields))

def main():
    parser = argparse.ArgumentParser(description='Decode UART Fusion frames from an FTDI serial port')
    parser.add_argument('--port', required=True, help='Serial device (e.g. /dev/ttyUSB0 or COM3)')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate (default: 9600)')
    args = parser.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        sys.stderr.write(f"Failed to open serial port: {e}\n")
        sys.exit(1)

    print(f"Listening on {args.port} at {args.baud} bps …")
    buffer = bytearray()
    while True:
        # Read whatever is available
        data = ser.read(1024)
        if not data:
            continue
        buffer.extend(data)
        # Try to find a complete frame
        while True:
            if len(buffer) < FRAME_TOTAL_LEN:
                break
            # Look for sync pattern at start of buffer
            if buffer[0] != SYNC0 or buffer[1] != SYNC1:
                # discard first byte and continue searching
                buffer.pop(0)
                continue
            # Verify version and type
            if buffer[2] != VERSION or buffer[3] != TYPE_TELEMETRY:
                # corrupt header; discard first byte
                buffer.pop(0)
                continue
            # Payload length (little‑endian 16‑bit)
            payload_len = buffer[4] | (buffer[5] << 8)
            if payload_len != PAYLOAD_LEN:
                # Unexpected length – skip this byte
                buffer.pop(0)
                continue
            # Ensure we have the whole frame
            if len(buffer) < FRAME_HEADER_LEN + payload_len + FRAME_CRC_LEN:
                break
            frame = buffer[:FRAME_HEADER_LEN + payload_len + FRAME_CRC_LEN]
            # Compute CRC over header+payload (excluding sync bytes)
            crc_received = frame[-2] | (frame[-1] << 8)
            crc_calc = crc16_ccitt(frame[2:-2])
            if crc_received != crc_calc:
                print('CRC mismatch – discarding frame')
                # drop first byte and try again
                buffer.pop(0)
                continue
            payload = frame[FRAME_HEADER_LEN:-2]
            parsed = parse_frame(payload)
            # Print in a readable way
            print('--- Frame ---')
            print(f"ID: {parsed['frame_id']}, time: {parsed['t_ms']} ms, dt: {parsed['dt_ms']} ms")
            print(f"Quaternion: ({parsed['q0']}, {parsed['q1']}, {parsed['q2']}, {parsed['q3']})")
            print(f"Accel (mg): ({parsed['ax']}, {parsed['ay']}, {parsed['az']})")
            print(f"Gyro (mdps): ({parsed['gx']}, {parsed['gy']}, {parsed['gz']})")
            print(f"Mag (mgauss): ({parsed['mx']}, {parsed['my']}, {parsed['mz']})")
            print(f"Temp: {parsed['temp_c_x10'] / 10.0:.1f} °C")
            print(f"Pressure: {parsed['pressure_hpa_x100'] / 100.0:.2f} hPa")
            print(f"Calib status: 0x{parsed['calib_status']:02X}, flags: 0x{parsed['status_flags']:02X}\n")
            # Remove processed frame from buffer
            del buffer[:len(frame)]

if __name__ == '__main__':
    main()
