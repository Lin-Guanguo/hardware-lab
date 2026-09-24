#!/usr/bin/env python3
"""Prove the E18 NFC terminals separate when one spiral segment is removed.

The schematic short-circuit flag intentionally gives both NFCT pins one net.
Ordinary netlist and DRC checks therefore cannot detect a copper bypass of the
coil. This audit removes one known outer-loop segment from a snapshot copy and
requires the two NFCT pins and tuning capacitors to fall into opposite groups.
"""

import argparse
import json
import runpy
from pathlib import Path

AUDIT = Path(__file__).with_name("check-e16-copper-connectivity.py")
MIL = 39.37007874015748


def near(a, b):
    return abs(a - b) < 0.03


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    lines = snapshot["lines"]
    cuts = [i for i, line in enumerate(lines)
            if line["net"] == "NFC1_TBD" and line["layer"] == 2
            and near(line["x1"] / MIL, 60.6) and near(line["x2"] / MIL, 60.6)
            and near(min(line["y1"], line["y2"]) / MIL, 27.6)
            and near(max(line["y1"], line["y2"]) / MIL, 48.9)]
    if len(cuts) != 1:
        raise SystemExit(f"expected one outer-loop cut segment, found {len(cuts)}")
    lines.pop(cuts[0])
    report = runpy.run_path(str(AUDIT))["audit"](snapshot)
    nfc = [entry for entry in report["split_nets"] if entry["net"] == "NFC1_TBD"]
    if len(nfc) != 1 or len(nfc[0]["groups"]) != 2:
        raise SystemExit("coil endpoints remain joined, or unexpected NFC groups were found")

    expected = [
        ("52@(61.25,4.05)", "NFC1@(68.00,23.00)", "1@(67.20,22.60)"),
        ("54@(61.25,3.25)", "NFC2@(71.40,23.00)", "1@(72.30,22.60)"),
    ]
    groups = [set(group) for group in nfc[0]["groups"]]
    matching = [[index for index, group in enumerate(groups)
                 if all(label in group for label in branch)] for branch in expected]
    if any(len(indexes) != 1 for indexes in matching) or matching[0] == matching[1]:
        raise SystemExit("NFCT pins, antenna landings or tuning capacitors are on the wrong branch")
    print(json.dumps({"ok": True, "cut_line_index": cuts[0], "nfc_groups": 2,
                      "branches": expected}, indent=2))


if __name__ == "__main__":
    main()
