#!/usr/bin/env python3
"""Check the independent R1 battery-sensing candidate and its exports."""

import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "hardware/records"
DELIVERY = ROOT / "hardware/production/r1-free-0p30-sense"
PROJECT = ROOT.parents[1] / "eda/NFC-Card-R1-Free-0p30-Sense.eprj2"
PREFIX = "NFC-Card-R1-Free-0p30-Sense"


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
    snapshot_path = RECORDS / "r1-free-0p30-sense-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text())
    refs = {component["ref"]: component for component in snapshot["components"]}
    assert len(refs) == len(snapshot["components"]) == 66
    bom = list(csv.DictReader(io.StringIO((DELIVERY / f"{PREFIX}-bom.csv").read_bytes().decode("utf-16")), delimiter="\t"))
    cpl = list(csv.DictReader(io.StringIO((DELIVERY / f"{PREFIX}-cpl.csv").read_bytes().decode("utf-16")), delimiter="\t"))
    bom_refs = [ref.strip() for row in bom for ref in row["Designator"].split(",")]
    assert len(bom_refs) == len(set(bom_refs)) == 66 and set(bom_refs) == set(refs)
    assert len(cpl) == 66 and {row["Designator"] for row in cpl} == set(refs)
    max_cpl_error = 0
    for row in cpl:
        component = refs[row["Designator"]]
        measured = [float(row[key].removesuffix("mm")) for key in ("Ref X", "Ref Y")]
        expected = [component[key] * .0254 for key in ("x", "y")]
        error = math.dist(measured, expected)
        max_cpl_error = max(max_cpl_error, error)
        assert error < .015 and row["Layer"] == "T"
        assert abs((float(row["Rotation"]) - component["rotation"] + 180) % 360 - 180) < .01

    gerber = DELIVERY / f"{PREFIX}-gerber.zip"
    with zipfile.ZipFile(gerber) as archive:
        assert archive.testzip() is None
        hits, slots = drill_data(archive, "Drill_PTH_Through.DRL")
        via_hits, via_slots = drill_data(archive, "Drill_PTH_Through_Via.DRL")
        assert Counter(hits) == Counter(via_hits)
        assert len(via_hits) == len(snapshot["vias"]) == 170
        assert len(slots) == 4 and not via_slots
        remaining = list(via_hits)
        radial_rings = []
        for via in snapshot["vias"]:
            expected = (via["x"] * .0254, via["y"] * .0254)
            matches = [i for i, hit in enumerate(remaining) if math.dist(expected, hit[:2]) < .003]
            assert len(matches) == 1, (via["net"], expected)
            hit = remaining.pop(matches[0])
            radial_rings.append((via["diameterMil"] * .0254 - hit[2]) / 2)
        assert not remaining
    minimum_hole_gap = min(
        math.dist(a[:2], b[:2]) - (a[2] + b[2]) / 2
        for i, a in enumerate(via_hits) for b in via_hits[i + 1:]
    )
    assert minimum_hole_gap > .30

    with sqlite3.connect(f"file:{PROJECT}?mode=ro", uri=True) as db:
        assert db.execute("pragma quick_check").fetchone()[0] == "ok"
    assert json.loads((RECORDS / "r1-free-0p30-sense-native-drc.json").read_text()) == []
    pin_check = json.loads((RECORDS / "r1-free-0p30-sense-pin-map-check.json").read_text())
    assert pin_check == {"schCount": 66, "pcbCount": 66, "diff": []}
    assert json.loads((RECORDS / "r1-free-0p30-sense-copper-check.json").read_text())["ok"]
    assert json.loads((RECORDS / "r1-free-0p30-sense-nfc-check.json").read_text())["ok"]
    profile = json.loads((RECORDS / "r1-free-0p30-sense-profile-check.json").read_text())
    assert profile["status"] == "PROFILE_AND_SLOTS_PASS"
    assert profile["gerber_sha256"] == sha256(gerber)
    assert profile["snapshot_sha256"] == sha256(snapshot_path)

    report = {
        "status": "VENDOR_DFM_AND_ASSEMBLY_REVIEW_REQUIRED",
        "project_sha256": sha256(PROJECT),
        "snapshot_sha256": sha256(snapshot_path),
        "gerber_sha256": sha256(gerber),
        "components": len(refs),
        "bom_groups": len(bom),
        "cpl_components": len(cpl),
        "maximum_cpl_reference_error_mm": max_cpl_error,
        "vias": len(via_hits),
        "drill_diameter_counts_mm": {str(k): v for k, v in sorted(Counter(hit[2] for hit in via_hits).items())},
        "minimum_via_drill_mm": min(hit[2] for hit in via_hits),
        "minimum_via_hole_gap_mm": minimum_hole_gap,
        "minimum_radial_annular_ring_mm": min(radial_rings),
        "vias_below_0p10_mm_radial_ring": sum(ring < .10 for ring in radial_rings),
        "usb_plated_slots": len(slots),
        "native_drc_errors": 0,
        "schematic_pcb_component_mismatches": 0,
        "copper_nfc_profile_checks": "pass",
        "qualification": "Local geometry only. Sub-0.30 mm drill values and 0.076 mm radial rings require redesign or vendor approval; no manufacturing acceptance is implied.",
    }
    (RECORDS / "r1-free-0p30-sense-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
