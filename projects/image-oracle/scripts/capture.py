# /// script
# requires-python = ">=3.10"
# dependencies = ["pyserial==3.5"]
# ///

import argparse
import sys
import time
from pathlib import Path

import serial

from native_usb import NativeUsbSerial


def main():
    parser = argparse.ArgumentParser(description="Capture one JPEG from camera_serial firmware.")
    parser.add_argument("--port", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Output already exists: {args.output}")

    with NativeUsbSerial(args.port, baudrate=115200, timeout=1, write_timeout=5) as connection:
        time.sleep(2)
        startup = connection.read(connection.in_waiting)
        if b"waiting for download" in startup:
            raise RuntimeError("Board is in download mode; press EN/RST without holding BOOT.")
        connection.reset_input_buffer()
        connection.write(b"SNAP\n")

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            line = connection.readline()
            if line.startswith(b"ERROR "):
                raise RuntimeError(line.decode(errors="replace").strip())
            if line.startswith(b"JPEG "):
                fields = line.split()
                if len(fields) != 4:
                    raise RuntimeError(f"Invalid frame header: {line!r}")
                size, width, height = map(int, fields[1:])
                break
            if line:
                print(line.decode(errors="replace").strip(), file=sys.stderr)
        else:
            raise RuntimeError("No JPEG header received; check firmware and port.")

        if not 4 <= size <= 1024 * 1024:
            raise RuntimeError(f"Unexpected JPEG size: {size}")
        payload = bytearray()
        deadline = time.monotonic() + size * 10 / 115200 + 10
        while len(payload) < size and time.monotonic() < deadline:
            payload.extend(connection.read(min(4096, size - len(payload))))
        if len(payload) != size:
            raise RuntimeError(f"Incomplete JPEG: expected {size}, received {len(payload)} bytes")
        if connection.read(5) != b"\nEND\n":
            raise RuntimeError("Missing end marker; the serial transfer may be corrupted")
        if not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
            raise RuntimeError("Invalid JPEG boundary markers")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(payload)
    print(f"Saved {width}x{height} JPEG ({size} bytes): {args.output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, serial.SerialException) as error:
        sys.exit(str(error))
