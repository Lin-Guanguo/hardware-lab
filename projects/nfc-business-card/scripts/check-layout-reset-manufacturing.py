#!/usr/bin/env python3
"""Verify R20/R21 native sources and matching Gerber, BOM, and CPL exports."""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RECORDS = ROOT / "hardware/records"
TAGS = {
    "r20": ("NFC-Card-R1-Layout-Reset-R20-Via-Clearance", 167, 4),
    "r21": ("NFC-Card-R1-Layout-Reset-R21-USB-CC2", 165, 2),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drill_hits(archive, name):
    tools = {}
    active = None
    hits = []
    slots = []
    for line in archive.read(name).decode().splitlines():
        if match := re.fullmatch(r"(T\d+)C([\d.]+)", line):
            tools[match[1]] = float(match[2])
        if re.fullmatch(r"T\d+", line):
            active = line
        if match := re.fullmatch(r"X([\d.]+)Y([\d.]+)", line):
            hits.append((float(match[1]), float(match[2]), tools[active]))
        if "G85" in line:
            slots.append(line)
    return hits, slots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", choices=TAGS)
    args = parser.parse_args()
    tag, expected_vias, expected_cc2_vias = TAGS[args.candidate]
    source = REPO / "eda" / f"{tag}.eprj2"
    production = ROOT / "hardware/production" / f"r1-layout-reset-{args.candidate}"
    record_prefix = f"r1-layout-reset-{args.candidate}"
    output = RECORDS / f"{record_prefix}-manufacturing.json"
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as db:
        assert db.execute("pragma quick_check").fetchone()[0] == "ok"
    snapshot_path = RECORDS / f"{record_prefix}-routed-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text())
    refs = {component["ref"]: component for component in snapshot["components"]}
    assert len(refs) == len(snapshot["components"]) == 66
    pins = json.loads((RECORDS / f"{record_prefix}-pcb-pins.json").read_text())
    assert len(pins) == 66 and sum(len(component["pins"]) for component in pins) == 256
    if args.candidate == "r21":
        r20_pins = json.loads((RECORDS / "r1-layout-reset-r20-pcb-pins.json").read_text())
        assert pins == r20_pins
    bom = list(csv.DictReader(io.StringIO((production / f"{tag}-bom.csv").read_bytes().decode("utf-16")), delimiter="\t"))
    cpl = list(csv.DictReader(io.StringIO((production / f"{tag}-cpl.csv").read_bytes().decode("utf-16")), delimiter="\t"))
    bom_refs = [ref.strip() for row in bom for ref in row["Designator"].split(",")]
    assert len(bom_refs) == len(set(bom_refs)) == 66 and set(bom_refs) == set(refs)
    assert len(cpl) == 66 and {row["Designator"] for row in cpl} == set(refs)
    placement_error = 0.0
    for row in cpl:
        comp = refs[row["Designator"]]
        expected = (comp["x"] * .0254, comp["y"] * .0254)
        actual = tuple(float(row[key].removesuffix("mm")) for key in ("Ref X", "Ref Y"))
        placement_error = max(placement_error, math.dist(actual, expected))
        assert math.dist(actual, expected) < .015 and row["Layer"] == "T"

    gerber = production / f"{tag}-gerber.zip"
    with ZipFile(gerber) as archive:
        assert archive.testzip() is None
        via_hits, via_slots = drill_hits(archive, "Drill_PTH_Through_Via.DRL")
        all_hits, all_slots = drill_hits(archive, "Drill_PTH_Through.DRL")
        npth_hits, npth_slots = drill_hits(archive, "Drill_NPTH_Through.DRL")
        assert len(via_hits) == len(snapshot["vias"]) == expected_vias
        assert Counter(via_hits) == Counter(all_hits) and not via_slots and not all_slots and not npth_slots
        assert len(npth_hits) == 2
        remaining = list(via_hits)
        rings = []
        for via in snapshot["vias"]:
            center = (via["x"] * .0254, via["y"] * .0254)
            matches = [index for index, hit in enumerate(remaining) if math.dist(center, hit[:2]) < .003]
            assert len(matches) == 1, (via["net"], center)
            hit = remaining.pop(matches[0])
            rings.append((via["diameterMil"] * .0254 - hit[2]) / 2)
        assert not remaining and min(rings) >= .10
        assert min(hit[2] for hit in via_hits) >= .299
    clearance = json.loads((RECORDS / f"{record_prefix}-clearance-audit.json").read_text())
    copper = json.loads((RECORDS / f"{record_prefix}-copper-check.json").read_text())
    nfc = json.loads((RECORDS / f"{record_prefix}-nfc-check.json").read_text())
    profile = json.loads((RECORDS / f"{record_prefix}-profile-check.json").read_text())
    assert clearance["pair_count_below_target"] == 0
    assert clearance["same_net_via_hole_to_pad_danger_pairs_below_0p10_mm"] == 0
    assert copper["ok"] and nfc["ok"] and profile["ok"]
    cc2_vias = sum(via["net"] == "USB_CC2" for via in snapshot["vias"])
    cc2_tracks = [line for line in snapshot["lines"] if line["net"] == "USB_CC2"]
    cc2_length = sum(math.hypot(line["x2"] - line["x1"], line["y2"] - line["y1"]) * .0254
                     for line in cc2_tracks)
    assert cc2_vias == expected_cc2_vias
    result = {
        "status": "LOCAL_CHECKS_PASS_VENDOR_DFM_REQUIRED",
        "project_sha256": digest(source),
        "snapshot_sha256": digest(snapshot_path),
        "gerber_sha256": digest(gerber),
        "bom_sha256": digest(production / f"{tag}-bom.csv"),
        "cpl_sha256": digest(production / f"{tag}-cpl.csv"),
        "components": len(refs),
        "pcb_pin_nets_unchanged_vs_r20": True if args.candidate == "r21" else None,
        "bom_groups": len(bom),
        "cpl_components": len(cpl),
        "maximum_cpl_reference_error_mm": round(placement_error, 6),
        "vias": len(via_hits),
        "usb_cc2_vias": cc2_vias,
        "usb_cc2_track_length_mm": round(cc2_length, 3),
        "minimum_via_drill_mm": min(hit[2] for hit in via_hits),
        "minimum_radial_annular_ring_mm": round(min(rings), 6),
        "different_net_copper_pairs_below_0p15_mm": clearance["pair_count_below_target"],
        "same_net_via_hole_to_pad_pairs_below_0p10_mm": clearance["same_net_via_hole_to_pad_danger_pairs_below_0p10_mm"],
        "usb_plated_slots": 0,
        "usb_npth_locating_holes": len(npth_hits),
        "native_drc_after_reopen": 0,
        "qualification": "Local geometry only; online PCB/SMT DFM, assembly and enclosure fit are separate gates.",
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
