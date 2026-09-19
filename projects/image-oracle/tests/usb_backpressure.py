# /// script
# requires-python = ">=3.10"
# dependencies = ["pyserial==3.5"]
# ///

import argparse
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from native_usb import NativeUsbSerial


def read_status(port, restore_counter=False):
    with NativeUsbSerial(port, baudrate=115200, timeout=0.2, write_timeout=5) as connection:
        time.sleep(0.2)
        connection.reset_input_buffer()
        connection.write(b"COUNTER\nSTATUS\n" if restore_counter else b"STATUS\n")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = connection.readline().decode("ascii", errors="replace").strip()
            if line.startswith("STATUS firmware=display_serial "):
                return dict(item.split("=", 1) for item in line.split()[1:])
    raise RuntimeError("No display_serial status reply")


def main():
    parser = argparse.ArgumentParser(description="Test display firmware with no USB reader; takes about 20 seconds.")
    parser.add_argument("--port", required=True)
    args = parser.parse_args()
    before = read_status(args.port)
    if "usb_write_max_us" not in before:
        raise RuntimeError("Firmware must include USB timing diagnostics")
    print(f"Firmware: {before['revision']}", flush=True)
    print("Drawing TEST, queueing eight STATUS replies, then closing the USB reader for 20 seconds.", flush=True)
    with NativeUsbSerial(args.port, baudrate=115200, timeout=0.2, write_timeout=5) as connection:
        # Drawing buys time to close the reader before the replies are produced.
        connection.write(b"TEST\n" + b"STATUS\n" * 8)
        connection.flush()
        time.sleep(0.02)
    time.sleep(20)
    after = read_status(args.port, restore_counter=True)
    keys = ["usb_write_max_us", "usb_dropped", "loop_gap_max_us", "counter_draw_max_us", "sample_gap_max_us"]
    for key in keys:
        print(f"{key}: {before[key]} -> {after[key]}")
    if int(after["uptime_ms"]) <= int(before["uptime_ms"]):
        raise RuntimeError("Board restarted during the test")
    if int(after["usb_dropped"]) <= int(before["usb_dropped"]):
        raise RuntimeError("No dropped messages observed; backpressure was not demonstrated")
    for key in ["usb_write_max_us", "counter_draw_max_us"]:
        if int(after[key]) >= 50000:
            raise RuntimeError(f"{key} reached 50 ms; rendering may stall")
    if int(after["loop_gap_max_us"]) >= 300000:
        raise RuntimeError("Loop gap exceeded the 300 ms allowance for drawing TEST")
    if int(after["sample_gap_max_us"]) >= 10000:
        raise RuntimeError("Button sampling gap reached 10 ms")
    print("PASS: USB backpressure did not stall the loop, drawing, or button sampling")


if __name__ == "__main__":
    main()
