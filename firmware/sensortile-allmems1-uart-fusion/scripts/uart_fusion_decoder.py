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
import threading
import queue
import numpy as np
import time




def serial_reader(port: str, baud: int, quat_queue: queue.Queue, stop_event: threading.Event, debug: bool=False):
    """Read frames from the serial port, print them, and push quaternion to the queue.

    Args:
        port: Serial device path.
        baud: Baud rate.
        quat_queue: Queue with maxsize=1 for latest quaternion.
        stop_event: Event to signal termination.
    """
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        sys.stderr.write(f"Failed to open serial port: {e}\n")
        return
    print(f"Listening on {port} at {baud} bps …")
    buffer = bytearray()
    while not stop_event.is_set():
        data = ser.read(1024)
        if not data:
            continue
        buffer.extend(data)
        while True:
            if len(buffer) < FRAME_TOTAL_LEN:
                break
            if buffer[0] != SYNC0 or buffer[1] != SYNC1:
                buffer.pop(0)
                continue
            if buffer[2] != VERSION or buffer[3] != TYPE_TELEMETRY:
                buffer.pop(0)
                continue
            payload_len = buffer[4] | (buffer[5] << 8)
            if payload_len != PAYLOAD_LEN:
                buffer.pop(0)
                continue
            if len(buffer) < FRAME_HEADER_LEN + payload_len + FRAME_CRC_LEN:
                break
            frame = buffer[:FRAME_HEADER_LEN + payload_len + FRAME_CRC_LEN]
            # Debug: dump raw frame
            if debug:
                print('RAW FRAME:', frame.hex())
            crc_received = frame[-2] | (frame[-1] << 8)
            crc_calc = crc16_ccitt(frame[2:-2])
            if crc_received != crc_calc:
                print('CRC mismatch – discarding frame')
                if debug:
                    print('CRC raw:', frame.hex())
                buffer.pop(0)
                continue

            payload = frame[FRAME_HEADER_LEN:-2]
            parsed = parse_frame(payload)
            # Print in a readable way (unchanged)
            print('--- Frame ---')
            print(f"ID: {parsed['frame_id']}, time: {parsed['t_ms']} ms, dt: {parsed['dt_ms']} ms")
            print(f"Quaternion: ({parsed['q0']}, {parsed['q1']}, {parsed['q2']}, {parsed['q3']})")
            print(f"Accel (mg): ({parsed['ax']}, {parsed['ay']}, {parsed['az']})")
            print(f"Gyro (mdps): ({parsed['gx']}, {parsed['gy']}, {parsed['gz']})")
            print(f"Mag (mgauss): ({parsed['mx']}, {parsed['my']}, {parsed['mz']})")
            print(f"Temp: {parsed['temp_c_x10'] / 10.0:.1f} °C")
            print(f"Pressure: {parsed['pressure_hpa_x100'] / 100.0:.2f} hPa")
            print(f"Calib status: 0x{parsed['calib_status']:02X}, flags: 0x{parsed['status_flags']:02X}\n")
            # Push quaternion to queue (non‑blocking, keep only latest)
            quat = np.array([parsed['q0'], parsed['q1'], parsed['q2'], parsed['q3']], dtype=np.float64)
            norm = np.linalg.norm(quat)
            if norm > 0:
                quat = quat / norm
            try:
                quat_queue.get_nowait()
            except queue.Empty:
                pass
            quat_queue.put_nowait(quat)
            del buffer[:len(frame)]
    ser.close()

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
    fields = struct.unpack('<III' + 'i'*13 + 'h' + 'i' + 'BB', payload)
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
    parser = argparse.ArgumentParser(description='Decode UART Fusion frames')
    parser.add_argument('--port', required=True, help='Serial device (e.g. /dev/ttyUSB0 or COM3)')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('--debug', action='store_true', help='Enable raw frame dump for debugging')
    args = parser.parse_args()

    quat_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()
    reader_thread = threading.Thread(target=serial_reader, args=(args.port, args.baud, quat_queue, stop_event, args.debug), daemon=True)
    reader_thread.start()

    # Run without visualisation
    try:
        while reader_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()
        reader_thread.join()

if __name__ == '__main__':
    main()
