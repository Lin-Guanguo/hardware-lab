# /// script
# requires-python = ">=3.10"
# dependencies = ["pyserial==3.5"]
# ///

import argparse
import sys
import time

import serial

from native_usb import NativeUsbSerial


def main():
    parser = argparse.ArgumentParser(description="Send one command to display_serial firmware.")
    parser.add_argument("--port", required=True)
    parser.add_argument("command", choices=[
        "STATUS", "COUNTER", "TEST", "RED", "GREEN", "BLUE", "WHITE", "BLACK", "LIGHT_ON", "LIGHT_OFF"
    ])
    args = parser.parse_args()
    with NativeUsbSerial(args.port, baudrate=115200, timeout=0.5, write_timeout=5) as connection:
        time.sleep(0.5)
        startup = connection.read(connection.in_waiting)
        if b"waiting for download" in startup:
            raise RuntimeError("Board is in download mode; unplug and reconnect USB without pressing BOOT.")
        connection.reset_input_buffer()
        connection.write((args.command + "\n").encode("ascii"))
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            line = connection.readline().decode("utf-8", errors="replace").strip()
            if not line:
                continue
            print(line)
            if "waiting for download" in line:
                raise RuntimeError("Board is in download mode; unplug and reconnect USB without pressing BOOT.")
            if line.startswith("ERROR "):
                raise RuntimeError("The board rejected the display command.")
            if args.command == "STATUS" and line.startswith("STATUS firmware=display_serial "):
                return
            if line == f"OK {args.command}":
                return
        raise RuntimeError("No expected reply; check the port and display_serial firmware.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, serial.SerialException) as error:
        sys.exit(str(error))
