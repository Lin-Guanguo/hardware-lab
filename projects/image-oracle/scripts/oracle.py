# /// script
# requires-python = ">=3.10"
# dependencies = ["pyserial==3.5"]
# ///

import argparse
from pathlib import Path
import struct
import sys
import time
import zlib

import serial
from native_usb import NativeUsbSerial


def request(connection, command, prefix):
    connection.write((command + "\n").encode("ascii"))
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        line = connection.readline().decode("ascii", errors="replace").strip()
        if line.startswith("ERROR ") or "waiting for download" in line:
            raise RuntimeError(line)
        if line.startswith(prefix + " "):
            return line
    raise RuntimeError(f"No {prefix} reply to {command}; inspect firmware and port before retrying")


def fields(line):
    return dict(item.split("=", 1) for item in line.split()[1:])


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


def export_frozen(connection, output):
    status = fields(request(connection, "STATUS", "STATUS"))
    if status.get("firmware") != "oracle_live" or status["snapshots"] == "0":
        raise RuntimeError("No oracle_live snapshot; press MID or send SNAP first")
    width, height = 112, 84
    image = bytearray()
    image_hash = 2166136261
    for y in range(height):
        row = fields(request(connection, f"ROW {y}", "ROW"))
        if row["snapshot"] != status["snapshots"] or int(row["y"]) != y:
            raise RuntimeError("Snapshot changed during export; retry without pressing MID")
        data = bytes.fromhex(row["pixels"])
        if len(data) != width * 2:
            raise RuntimeError("Incomplete pixel row")
        image.append(0)
        for byte in data:
            image_hash = ((image_hash ^ byte) * 16777619) & 0xffffffff
        for x in range(width):
            pixel = int.from_bytes(data[x * 2:x * 2 + 2], "big")
            image.extend(((pixel >> 11) * 255 // 31, ((pixel >> 5) & 63) * 255 // 63, (pixel & 31) * 255 // 31))
    if image_hash != int(status["hash"], 16):
        raise RuntimeError("Exported pixels do not match the snapshot hash")
    answer = "TRUE" if image_hash & 0x80000000 else "FALSE"
    if answer != status["oracle"]:
        raise RuntimeError("Oracle result does not match the exported pixels")
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += png_chunk(b"IDAT", zlib.compress(bytes(image)))
    png += png_chunk(b"IEND", b"")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as image_file:
        image_file.write(png)
    print(f"Saved {width}x{height}: {output.resolve()}; hash={image_hash:08X} oracle={answer}")


def main():
    parser = argparse.ArgumentParser(description="Query, freeze, or export the third Image Oracle firmware.")
    parser.add_argument("--port", required=True)
    parser.add_argument("command", choices=["STATUS", "SNAP", "EXPORT"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "EXPORT" and (args.output is None or args.output.suffix.lower() != ".png"):
        parser.error("EXPORT requires --output <new-file.png>")
    if args.command != "EXPORT" and args.output is not None:
        parser.error("--output is only used with EXPORT")
    if args.output is not None and args.output.exists():
        parser.error(f"Output already exists: {args.output}")
    with NativeUsbSerial(args.port, baudrate=115200, timeout=0.2, write_timeout=5) as connection:
        time.sleep(0.2)
        startup = connection.read(connection.in_waiting)
        if b"waiting for download" in startup:
            raise RuntimeError("Board is in download mode; reconnect USB without pressing BOOT")
        connection.reset_input_buffer()
        if args.command == "EXPORT":
            export_frozen(connection, args.output)
        else:
            print(request(connection, args.command, args.command))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, serial.SerialException) as error:
        sys.exit(str(error))
