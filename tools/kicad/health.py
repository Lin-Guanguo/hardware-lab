#!/usr/bin/env python3
"""Check the repository KiCad runtime without changing a design."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ipc", action="store_true")
    parser.add_argument("--board", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    runtime = root / ".cache/kicad-venv/bin/python"
    if sys.prefix != str(root / ".cache/kicad-venv") and runtime.exists():
        return subprocess.call([str(runtime), __file__, *sys.argv[1:]])
    cli = shutil.which("kicad-cli")
    if not cli:
        candidate = Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
        cli = str(candidate) if candidate.exists() else None
    result = {"ok": False, "cli": cli, "python": sys.version.split()[0]}
    try:
        if not cli:
            raise RuntimeError("KiCad CLI not found")
        result["version"] = subprocess.check_output(
            [cli, "version"], text=True, timeout=15
        ).strip()
        from importlib.metadata import version
        from kipy import KiCad
        from kipy.proto.common.types import DocumentType

        result["kicad_python"] = version("kicad-python")
        upstream = root / "upstreams/kicad-happy"
        result["upstream_revision"] = subprocess.check_output(
            ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
        if args.ipc or args.board:
            client = KiCad(client_name="hardware-lab-health", timeout_ms=3000)
            result["ipc_version"] = str(client.get_version())
            docs = client.get_open_documents(DocumentType.DOCTYPE_PCB)
            result["boards"] = [str((Path(d.project.path) / d.board_filename).resolve()) for d in docs]
            if args.board and str(args.board.resolve()) not in result["boards"]:
                raise RuntimeError("Requested board is not open on this IPC connection")
        result["ok"] = True
    except Exception as error:
        result["error"] = str(error)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
