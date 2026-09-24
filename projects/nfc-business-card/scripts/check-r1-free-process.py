#!/usr/bin/env python3
"""Check the R1 0.30 mm drill experiment against its source and export."""

import hashlib
import json
import math
import re
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "hardware/records"
DELIVERY = ROOT / "hardware/production/r1-free-0p30"
PROJECT = ROOT.parents[1] / "eda/NFC-Card-R1-Free-0p30.eprj2"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drill_data(archive, name):
    tools = {}
    hits = []
    slots = []
    active = None
    for line in archive.read(name).decode().splitlines():
        tool = re.fullmatch(r"(T\d+)C([\d.]+)", line)
        if tool:
            tools[tool[1]] = float(tool[2])
        if re.fullmatch(r"T\d+", line):
            active = line
        hit = re.fullmatch(r"X([\d.]+)Y([\d.]+)", line)
        if hit:
            hits.append((float(hit[1]), float(hit[2]), tools[active]))
        if "G85" in line:
            slots.append(line)
    return hits, slots


def main():
    original = json.loads((RECORDS / "r1-routed-snapshot.json").read_text())
    candidate_path = RECORDS / "r1-free-0p30-snapshot.json"
    candidate = json.loads(candidate_path.read_text())
    for field in ("components", "pads", "polylines", "regions", "pours", "strings"):
        assert candidate[field] == original[field], f"Unexpected {field} change"
    assert len(candidate["vias"]) == len(original["vias"]) == 153
    assert len(candidate["lines"]) == len(original["lines"]) == 819
    moved_vias = []
    changed_holes = 0
    for before, after in zip(original["vias"], candidate["vias"]):
        assert before["net"] == after["net"]
        assert before["diameterMil"] == after["diameterMil"]
        if (before["x"], before["y"]) != (after["x"], after["y"]):
            moved_vias.append(after["net"])
        if before["holeMil"] != after["holeMil"]:
            changed_holes += 1
            assert before["holeMil"] == 9.8 and after["holeMil"] == 11.8
    assert Counter(moved_vias) == Counter(["GND", "USB_CC2"])
    assert changed_holes == 97
    changed_lines = []
    for before, after in zip(original["lines"], candidate["lines"]):
        if before != after:
            changed_lines.append(after["net"])
            assert {key for key in before if before[key] != after[key]} <= {"x1", "y1", "x2", "y2"}
    assert changed_lines == ["USB_CC2", "USB_CC2"]

    gerber = DELIVERY / "NFC-Card-R1-Free-0p30-gerber.zip"
    with zipfile.ZipFile(gerber) as archive:
        assert archive.testzip() is None
        hits, slots = drill_data(archive, "Drill_PTH_Through.DRL")
        via_hits, via_slots = drill_data(archive, "Drill_PTH_Through_Via.DRL")
        assert Counter(hits) == Counter(via_hits)
        assert len(via_hits) == 153 and len(slots) == 4 and not via_slots
        assert min(hit[2] for hit in via_hits) >= 0.30
        remaining = list(via_hits)
        for via in candidate["vias"]:
            expected = (via["x"] * .0254, via["y"] * .0254)
            matches = [i for i, hit in enumerate(remaining) if math.dist(expected, hit[:2]) < .003]
            assert len(matches) == 1, (via["net"], expected)
            remaining.pop(matches[0])
        assert not remaining

    min_hole_gap = min(
        math.dist(a[:2], b[:2]) - (a[2] + b[2]) / 2
        for i, a in enumerate(via_hits) for b in via_hits[i + 1:]
    )
    assert min_hole_gap >= .30
    drill_counts = {f"{diameter:.6f}": count for diameter, count in sorted(Counter(hit[2] for hit in via_hits).items())}
    min_radial_ring = min(
        ((via["diameterMil"] * .0254) - next(hit[2] for hit in via_hits if math.dist((via["x"] * .0254, via["y"] * .0254), hit[:2]) < .003)) / 2
        for via in candidate["vias"]
    )
    assert min_radial_ring >= .075
    with sqlite3.connect(f"file:{PROJECT}?mode=ro", uri=True) as db:
        assert db.execute("pragma quick_check").fetchone()[0] == "ok"
    assert json.loads((RECORDS / "r1-free-0p30-copper-check.json").read_text())["ok"]
    assert json.loads((RECORDS / "r1-free-0p30-nfc-check.json").read_text())["ok"]
    assert json.loads((RECORDS / "r1-free-0p30-native-drc.json").read_text()) == []
    profile = json.loads((RECORDS / "r1-free-0p30-profile-check.json").read_text())
    assert profile["status"] == "PROFILE_AND_SLOTS_PASS"
    assert profile["gerber_sha256"] == sha256(gerber)
    assert profile["snapshot_sha256"] == sha256(candidate_path)
    report = {
        "status": "VENDOR_DFM_AND_ASSEMBLY_REVIEW_REQUIRED",
        "candidate_project_sha256": sha256(PROJECT),
        "original_project_sha256": sha256(ROOT.parents[1] / "eda/NFC-Card-R1.eprj2"),
        "snapshot_sha256": sha256(candidate_path),
        "gerber_sha256": sha256(gerber),
        "native_project_sqlite_quick_check": "ok",
        "vias": len(via_hits),
        "enlarged_via_drills": changed_holes,
        "moved_via_nets": moved_vias,
        "adjusted_trace_nets": changed_lines,
        "drill_diameter_counts_mm": drill_counts,
        "minimum_via_hole_gap_mm": min_hole_gap,
        "minimum_radial_annular_ring_mm": min_radial_ring,
        "plated_mounting_slots": len(slots),
        "native_drc_errors_after_reopen": 0,
        "independent_copper_and_nfc_checks": "pass",
        "profile_and_slots": profile["status"],
        "qualification": "The 0.075 mm radial annulus is a deliberate reduction from R1's 0.10 mm target. Native DRC and geometry checks do not constitute vendor acceptance or physical qualification.",
    }
    (RECORDS / "r1-free-0p30-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
