#!/usr/bin/env python3
"""Diff the schematic netlist against the live PCB pin map.

The schematic side comes from EasyEDA's "EasyEDA" netlist export
(SCH_ManufactureData.getNetlistFile) and the PCB side from
scripts/eda-export-pcb-pins.js. Both sides are keyed by designator + pin number,
so the check catches changed, added and dropped connections, not just refs.

Usage:
    python3 check-netlist-consistency.py --sch sch-netlist.enet --pcb pcb-pins.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def schematic_map(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    pins: dict[str, str] = {}
    for comp in data["components"].values():
        ref = comp["props"]["Designator"]
        for number, info in comp.get("pinInfoMap", {}).items():
            pins[f"{ref}:{number}"] = info.get("net") or ""
    return pins


def pcb_map(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    pins: dict[str, str] = {}
    for comp in data:
        ref = comp["ref"]
        for pin in comp.get("pins", []):
            pins[f"{ref}:{pin['number']}"] = pin.get("net") or ""
    return pins


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sch", type=Path, required=True, help="schematic netlist export")
    parser.add_argument("--pcb", type=Path, required=True, help="PCB pin dump from eda-export-pcb-pins.js")
    parser.add_argument("--limit", type=int, default=20, help="diff rows to print")
    args = parser.parse_args()

    sch = schematic_map(args.sch)
    pcb = pcb_map(args.pcb)

    sch_refs = {key.split(":")[0] for key in sch}
    pcb_refs = {key.split(":")[0] for key in pcb}
    only_sch = sorted(sch_refs - pcb_refs)
    only_pcb = sorted(pcb_refs - sch_refs)

    mismatches = []
    for key in sorted(set(sch) | set(pcb)):
        left, right = sch.get(key), pcb.get(key)
        if left is None or right is None:
            mismatches.append((key, left, right))
        elif left != right:
            mismatches.append((key, left, right))

    print(f"schematic refs {len(sch_refs)} · PCB refs {len(pcb_refs)} · schematic pins {len(sch)} · PCB pins {len(pcb)}")
    print(f"refs only in schematic: {only_sch or 'none'}")
    print(f"refs only in PCB: {only_pcb or 'none'}")
    print(f"pin/net mismatches: {len(mismatches)}")
    for key, left, right in mismatches[: args.limit]:
        print(f"  {key}: schematic={left!r} pcb={right!r}")
    if len(mismatches) > args.limit:
        print(f"  ... {len(mismatches) - args.limit} more")

    return 1 if (only_sch or only_pcb or mismatches) else 0


if __name__ == "__main__":
    raise SystemExit(main())
