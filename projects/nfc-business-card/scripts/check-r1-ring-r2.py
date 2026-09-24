#!/usr/bin/env python3
"""Validate the R1 0.30 mm ring and clearance candidate against its native exports."""

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
DELIVERY = ROOT / "hardware/production/r1-free-0p30-sense-ring-r2"
PROJECT = ROOT.parents[1] / "eda/NFC-Card-R1-Free-0p30-Sense-Ring-R2.eprj2"
PREFIX = "NFC-Card-R1-Free-0p30-Sense-Ring-R2"


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
    snapshot_path = RECORDS / "r1-free-0p30-sense-ring-r2-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text())
    baseline = json.loads((RECORDS / "r1-free-0p30-sense-snapshot.json").read_text())
    for field in ("components", "pads", "polylines", "regions", "strings"):
        assert snapshot[field] == baseline[field], f"Unexpected {field} change"

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
        actual = [float(row[key].removesuffix("mm")) for key in ("Ref X", "Ref Y")]
        expected = [component[key] * .0254 for key in ("x", "y")]
        error = math.dist(actual, expected)
        max_cpl_error = max(max_cpl_error, error)
        assert error < .015 and row["Layer"] == "T"
        assert abs((float(row["Rotation"]) - component["rotation"] + 180) % 360 - 180) < .01

    gerber = DELIVERY / f"{PREFIX}-gerber.zip"
    with zipfile.ZipFile(gerber) as archive:
        assert archive.testzip() is None
        all_hits, slots = drill_data(archive, "Drill_PTH_Through.DRL")
        via_hits, via_slots = drill_data(archive, "Drill_PTH_Through_Via.DRL")
        assert Counter(all_hits) == Counter(via_hits)
        assert len(via_hits) == len(snapshot["vias"]) == 169
        assert len(slots) == 4 and not via_slots
        remaining = list(via_hits)
        rings = []
        for via in snapshot["vias"]:
            expected = (via["x"] * .0254, via["y"] * .0254)
            matches = [index for index, hit in enumerate(remaining) if math.dist(expected, hit[:2]) < .003]
            assert len(matches) == 1, (via["net"], expected)
            hit = remaining.pop(matches[0])
            rings.append((via["diameterMil"] * .0254 - hit[2]) / 2)
        assert not remaining
    min_hole_gap = min(
        math.dist(a[:2], b[:2]) - (a[2] + b[2]) / 2
        for index, a in enumerate(via_hits) for b in via_hits[index + 1:]
    )
    assert min(hit[2] for hit in via_hits) >= .300
    assert min(rings) >= .100
    assert min_hole_gap >= .300

    with sqlite3.connect(f"file:{PROJECT}?mode=ro", uri=True) as db:
        assert db.execute("pragma quick_check").fetchone()[0] == "ok"
    assert json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-native-drc.json").read_text()) == []
    assert json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-pin-map-check.json").read_text()) == {"schCount": 66, "pcbCount": 66, "diff": []}
    assert json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-copper-check.json").read_text())["ok"]
    assert json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-nfc-check.json").read_text())["ok"]
    clearance = json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-clearance-audit.json").read_text())
    assert clearance["target_mm"] == .15 and clearance["pair_count_below_target"] == 0
    same_net_via_hole_pad_pairs = clearance["same_net_via_hole_to_pad_pairs_below_target"]
    profile = json.loads((RECORDS / "r1-free-0p30-sense-ring-r2-profile-check.json").read_text())
    assert profile["status"] == "PROFILE_AND_SLOTS_PASS"
    assert profile["gerber_sha256"] == sha256(gerber)
    assert profile["snapshot_sha256"] == sha256(snapshot_path)

    report = {
        "status": "LOCAL_CHECKS_PASS_VENDOR_REVIEW_REQUIRED",
        "project_sha256": sha256(PROJECT),
        "snapshot_sha256": sha256(snapshot_path),
        "gerber_sha256": sha256(gerber),
        "bom_sha256": sha256(DELIVERY / f"{PREFIX}-bom.csv"),
        "cpl_sha256": sha256(DELIVERY / f"{PREFIX}-cpl.csv"),
        "components": len(refs),
        "bom_groups": len(bom),
        "cpl_components": len(cpl),
        "maximum_cpl_reference_error_mm": max_cpl_error,
        "vias": len(via_hits),
        "drill_diameter_counts_mm": {str(key): value for key, value in sorted(Counter(hit[2] for hit in via_hits).items())},
        "minimum_via_drill_mm": min(hit[2] for hit in via_hits),
        "minimum_via_hole_gap_mm": min_hole_gap,
        "minimum_radial_annular_ring_mm": min(rings),
        "vias_below_0p10_mm_radial_ring": sum(ring < .10 for ring in rings),
        "different_net_copper_pairs_below_0p15_mm": clearance["pair_count_below_target"],
        "same_net_via_hole_to_pad_pairs_below_0p15_mm": len(same_net_via_hole_pad_pairs),
        "same_net_via_holes_touching_pad_copper": sum(item["gap_mm"] == 0 for item in same_net_via_hole_pad_pairs),
        "usb_plated_slots": len(slots),
        "native_drc_errors_after_reopen": 0,
        "qualification": "Online DFM found unresolved annular-ring, via-to-pad and SMT warnings; manual vendor review and physical validation remain required.",
    }
    (RECORDS / "r1-free-0p30-sense-ring-r2-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
