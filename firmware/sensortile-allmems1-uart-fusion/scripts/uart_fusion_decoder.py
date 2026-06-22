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

# Optional graphics – import only when needed
try:
    import pyglet
    from pyglet.gl import *
except Exception:
    pyglet = None  # will be checked when --visual is used


def serial_reader(port: str, baud: int, quat_queue: queue.Queue, stop_event: threading.Event):
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
            crc_received = frame[-2] | (frame[-1] << 8)
            crc_calc = crc16_ccitt(frame[2:-2])
            if crc_received != crc_calc:
                print('CRC mismatch – discarding frame')
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

class QuaternionVisualizer:
    """Simple pyglet window that draws a rotating cube based on incoming quaternion data."""

    def __init__(self, quat_queue: queue.Queue):
        if not pyglet:
            raise RuntimeError('pyglet is not available – install it to use --visual')
        self.quat_queue = quat_queue
        self.window = pyglet.window.Window(width=800, height=600, caption='Quaternion Cube')
        glEnable(GL_DEPTH_TEST)
        # Simple cube vertices
        self.vertices = [
            (-1, -1,  1), ( 1, -1,  1), ( 1,  1,  1), (-1,  1,  1),
            (-1, -1, -1), ( 1, -1, -1), ( 1,  1, -1), (-1,  1, -1),
        ]
        # indices removed, using faces list
        # indices list removed
        self.faces = [
            (0, 1, 2, 3),  # front
            (4, 5, 6, 7),  # back
            (0, 4, 7, 3),  # left
            (1, 5, 6, 2),  # right
            (3, 2, 6, 7),  # top
            (0, 1, 5, 4),  # bottom
        ]
        @self.window.event
        def on_draw():
            self.window.clear()
            # Compute rotation matrix (default identity)
            rot = np.identity(4, dtype=np.float32)
            try:
                quat = self.quat_queue.get_nowait()
                w, x, y, z = quat
                rot = np.array([
                    [1 - 2*y*y - 2*z*z,   2*x*y - 2*z*w,       2*x*z + 2*y*w, 0],
                    [2*x*y + 2*z*w,       1 - 2*x*x - 2*z*z,   2*y*z - 2*x*w, 0],
                    [2*x*z - 2*y*w,       2*y*z + 2*x*w,       1 - 2*x*x - 2*y*y, 0],
                    [0, 0, 0, 1]
                ], dtype=np.float32)
            except queue.Empty:
                pass
            # Transform vertices (no Z translation for 2D view)
            glClearColor(0.0, 0.0, 0.0, 1.0)  # black background
            glDisable(GL_DEPTH_TEST)  # disable depth for simple wireframe
            transformed_vertices = []
            for v in self.vertices:
                vec = np.array([v[0], v[1], v[2], 1.0], dtype=np.float32)
                tv = rot @ vec
                tv[2] -= 5.0
                transformed_vertices.append(tv[:3])
            # Draw cube as wireframe using GL_LINES
            # Build line vertex list from faces
            line_vertices = []
            for face in self.faces:
                # edges: (0-1,1-2,2-3,3-0)
                a, b, c, d = face
                for start, end in ((a, b), (b, c), (c, d), (d, a)):
                    x1, y1, z1 = transformed_vertices[start]
                    x2, y2, z2 = transformed_vertices[end]
                    line_vertices.extend([x1, y1, z1, x2, y2, z2])
            # Uniform light‑blue color

            # Clear screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            # Draw lines
            pyglet.graphics.draw(len(line_vertices) // 3, GL_LINES,
                                 position=('f', line_vertices))
            # Re-enable depth test after drawing (optional)
            glEnable(GL_DEPTH_TEST)
    
        @self.window.event
        def on_close():
            pyglet.app.exit()

    def run(self):
        pyglet.app.run()

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
    parser = argparse.ArgumentParser(description='Decode UART Fusion frames with optional visualisation')
    parser.add_argument('--port', required=True, help='Serial device (e.g. /dev/ttyUSB0 or COM3)')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('--visual', action='store_true', help='Show 3‑D cube visualisation')
    args = parser.parse_args()

    quat_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()
    reader_thread = threading.Thread(target=serial_reader, args=(args.port, args.baud, quat_queue, stop_event), daemon=True)
    reader_thread.start()

    if args.visual:
        if not pyglet:
            sys.stderr.write('pyglet not installed – install with "pip install pyglet" and retry.\n')
            stop_event.set()
            reader_thread.join()
            sys.exit(1)
        visual = QuaternionVisualizer(quat_queue)
        try:
            visual.run()
        finally:
            stop_event.set()
            reader_thread.join()
    else:
        try:
            while reader_thread.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            stop_event.set()
            reader_thread.join()

if __name__ == '__main__':
    main()
