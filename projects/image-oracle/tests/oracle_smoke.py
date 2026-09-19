# /// script
# requires-python = ">=3.10"
# dependencies = ["pyserial==3.5"]
# ///

from pathlib import Path
import sys
import time
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from native_usb import NativeUsbSerial
from oracle import request, fields


def main():
    parser = argparse.ArgumentParser(description="Verify live frames, frozen state, and USB backpressure; do not press MID during the test.")
    parser.add_argument("--port", required=True)
    args = parser.parse_args()
    with NativeUsbSerial(args.port, baudrate=115200, timeout=0.2, write_timeout=5) as connection:
        time.sleep(0.2)
        connection.reset_input_buffer()
        before = fields(request(connection, "STATUS", "STATUS"))
        assert before["firmware"] == "oracle_live" and before["camera"] == "1", before
        assert int(before["live_frame"]) > 0, before
        frozen = fields(request(connection, "SNAP", "SNAP"))
        start = time.monotonic()
        time.sleep(2)
        after = fields(request(connection, "STATUS", "STATUS"))
        elapsed = time.monotonic() - start
        fps = (int(after["preview_frames"]) - int(before["preview_frames"])) / elapsed
        assert int(after["live_frame"]) > int(before["live_frame"]), after
        assert after["snapshots"] == frozen["snapshot"], "Do not press MID during the test"
        assert after["frozen_frame"] == frozen["frame"] and after["hash"] == frozen["hash"], after
        assert after["oracle"] == frozen["oracle"], after
        print(f"PASS: preview advances at approximately {fps:.1f} FPS while frozen pixels/hash remain unchanged", flush=True)
        # Snapshot drawing lets the reader close before the queued status replies are produced.
        connection.write(b"SNAP\n" + b"STATUS\n" * 8)
        connection.flush()
        time.sleep(0.02)
    time.sleep(5)
    with NativeUsbSerial(args.port, baudrate=115200, timeout=0.2, write_timeout=5) as connection:
        time.sleep(0.2)
        connection.reset_input_buffer()
        final = fields(request(connection, "STATUS", "STATUS"))
    assert int(final["uptime_ms"]) > int(after["uptime_ms"]), "Board restarted"
    assert int(final["preview_frames"]) > int(after["preview_frames"]) + 10, final
    assert int(final["usb_dropped"]) > int(after["usb_dropped"]), "USB backpressure was not demonstrated"
    assert final["camera_errors"] == before["camera_errors"], final
    assert int(final["usb_write_max_us"]) < 50000, final
    assert int(final["sample_gap_max_us"]) < 10000, final
    assert int(final["loop_gap_max_us"]) < 250000, final
    print("PASS: preview and button sampling continue without a USB reader")
    print(" ".join(f"{key}={value}" for key, value in final.items()))


if __name__ == "__main__":
    main()
