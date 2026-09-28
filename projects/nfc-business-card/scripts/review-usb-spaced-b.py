#!/usr/bin/env python3
"""Check and render USB Spaced B without treating partial routing as fabrication approval."""
import argparse
import collections
import csv
import importlib.util
import io
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import LineString, Point

PROJECT = Path(__file__).resolve().parents[1]
RECORDS = PROJECT / "hardware/records"
STEM = RECORDS / "usb-spaced-b"
MM = .0254
spec = importlib.util.spec_from_file_location("copper_audit", Path(__file__).with_name("check-r1-copper.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def errors(value):
    if isinstance(value, list):
        for item in value:
            yield from errors(item)
    elif isinstance(value, dict):
        if "errorType" in value:
            yield value
        else:
            yield from errors(value.get("list", []))


def load(suffix):
    return json.loads(Path(f"{STEM}-{suffix}").read_text())


def xy(p):
    return p["x"] * MM, p["y"] * MM


def named_pads(snapshot):
    return {(c["ref"], p["number"]): p for c in snapshot["components"] for p in snapshot["pads"]
            if p["id"].startswith(c["id"])}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", type=Path, help="Output of eda-export-midmount-candidate.js with B open")
args = parser.parse_args()
if args.capture:
    capture = json.loads(args.capture.read_text())
    assert capture["success"]
    data = capture["result"]
    assert data["project"]["name"] == "NFC-Card-R2-USB-Spaced-B"
    for key, suffix in [("snapshot", "snapshot.json"), ("pins", "pcb-pins.json"),
                        ("rules", "rules.json"), ("netlist", "schematic.enet")]:
        Path(f"{STEM}-{suffix}").write_text(json.dumps(data[key], ensure_ascii=False, indent=2)+"\n")
    Path(f"{STEM}-bom.tsv").write_text(data["bom"])
    Path(f"{STEM}-drc.json").write_text(json.dumps({"project": data["project"],
        "status": "PARTIAL_ROUTING_NOT_PASSED", "errors": list(errors(data["drc"]))}, ensure_ascii=False, indent=2)+"\n")

s = load("snapshot.json")
a = json.loads((RECORDS / "midmount-placement-a-snapshot.json").read_text())
pads = named_pads(s)
apads = named_pads(a)
components = {c["ref"]: c for c in s["components"]}
old_components = {c["ref"]: c for c in a["components"]}
changed = [ref for ref, c in components.items() if c != old_components[ref]]
assert set(changed) == {"U5", "U6", "R1", "R2"}
assert len(components) == 66 and len(pads) == 256 and len(s["pads"]) == 266
assert [{**p, "widthMil": round(p["widthMil"], 4)} for p in s["polylines"]] == [{**p, "widthMil": round(p["widthMil"], 4)} for p in a["polylines"]]
assert s["regions"] == a["regions"]
assert [t for t in s["lines"] if t["net"] == "NFC1_TBD"] == [t for t in a["lines"] if t["net"] == "NFC1_TBD"]
assert [v for v in s["vias"] if v["net"] == "NFC1_TBD"] == [v for v in a["vias"] if v["net"] == "NFC1_TBD"]
old_board_pads = {p["id"]: p for p in a["pads"]}
for p in s["pads"]:
    owner = next((c["ref"] for c in s["components"] if p["id"].startswith(c["id"])), None)
    if owner not in changed:
        assert p == old_board_pads[p["id"]], (owner, p["number"])
assert not s["pours"] and not s["poured"]
assert load("rules.json")["config"] == json.loads((RECORDS / "midmount-placement-a-rules.json").read_text())["config"]

sch = {c["props"]["Designator"]: c for c in load("schematic.enet")["components"].values()}
assert sch.keys() == components.keys()
assert all(sch[ref]["pinInfoMap"][number].get("net", "") == p["net"] for (ref, number), p in pads.items())
bom = list(csv.DictReader(io.StringIO(Path(f"{STEM}-bom.tsv").read_text()), delimiter="\t"))
assert {ref for row in bom for ref in row["Designator"].split(",")} == components.keys()

# Calibrate the pad orientation independently against the asymmetric GCT land.
g = audit.pad_shape(pads["J1", "A6"])
assert abs(g.bounds[2]-g.bounds[0]-1.1) < .003 and abs(g.bounds[3]-g.bounds[1]-.3) < .003
new_tracks = [t for t in s["lines"] if t["net"] != "NFC1_TBD"]
new_vias = [v for v in s["vias"] if v["net"] != "NFC1_TBD"]
assert all(abs(v["holeMil"]*MM-.3) < .001 and abs(v["diameterMil"]*MM-.6) < .001 for v in new_vias)
items = []
for p in s["pads"]:
    for layer in ([1, 2] if p["layer"] == 12 else [p["layer"]]):
        items.append((p["id"], p["net"], layer, audit.pad_shape(p), False, "pad"))
for i, t in enumerate(s["lines"]):
    items.append((f"track{i}", t["net"], t["layer"], LineString([
        (t["x1"]*MM, t["y1"]*MM), (t["x2"]*MM, t["y2"]*MM)]).buffer(t["widthMil"]*MM/2), t["net"] != "NFC1_TBD", "track"))
for i, v in enumerate(s["vias"]):
    for layer in (1, 2):
        items.append((f"via{i}", v["net"], layer, Point(xy(v)).buffer(v["diameterMil"]*MM/2), v["net"] != "NFC1_TBD", "via"))
pairs = []
for i, (name, net, layer, g, new, kind) in enumerate(items):
    for name2, net2, layer2, g2, new2, kind2 in items[i+1:]:
        if layer != layer2 or net == net2 or not (new or new2):
            continue
        pairs.append({"gap_mm": g.distance(g2), "objects": [name, name2], "kinds": [kind, kind2]})
assert min(p["gap_mm"] for p in pairs) >= .245
assert min(p["gap_mm"] for p in pairs if "via" in p["kinds"]) >= .295
hole_to_pad = min(Point(xy(v)).buffer(v["holeMil"]*MM/2).distance(audit.pad_shape(p))
                  for v in new_vias for p in s["pads"] if p["layer"] in (1, 2))
assert hole_to_pad > .4
result = audit.audit(s)
for key in ["dead_ends", "floating_copper", "single_layer_or_isolated_vias", "screen_unexpected_copper_mm2"]:
    assert not result[key], (key, result[key])
complete_nets = ["USB_DP_CONN", "USB_DM_CONN", "USB_DP_MCU", "USB_DM_MCU", "USB_CC1", "USB_CC2"]
assert all(net not in result["split_nets"] for net in complete_nets)
ground_pins = [("J1", n) for n in ["A1B12", "B1A12", "17", "18", "19", "20"]] + [(r, n) for r, n in [("U5", "3"), ("U6", "3"), ("R1", "2"), ("R2", "2")]]
labels = {f"{n}@({xy(pads[r,n])[0]:.2f},{xy(pads[r,n])[1]:.2f})" for r, n in ground_pins}
assert any(labels <= set(group) for group in result["groups"]["GND"])
assert "GND" in result["split_nets"] and "USB_VBUS" in result["split_nets"]

drc = load("drc.json")["errors"]
counts = collections.Counter((e["errorType"], e["errorObjType"]) for e in drc)
assert counts["Clearance Error in the same footprint", "Board Outline to SMD Pad"] == 12
assert counts["Physical Error", "Via Size"] == 4
assert all(kind in ["Connection Error", "Clearance Error in the same footprint", "Physical Error"] for kind, _ in counts)
report = {
    "status": "USB_SIGNAL_ROUTING_CHECKED_FULL_BOARD_AND_RETURN_POURS_INCOMPLETE",
    "counts": {"components": 66, "component_pins": 256, "pads": 266, "tracks": len(s["lines"]), "vias": len(s["vias"]), "bom_groups": len(bom)},
    "moved_vs_a": changed, "unchanged_nfc_outline_keepouts_other_components": True,
    "complete_signal_nets": complete_nets, "usb_local_ground_connected": True,
    "new_vias_by_net": dict(collections.Counter(v["net"] for v in new_vias)),
    "new_copper_min_other_net_clearance_mm": min(p["gap_mm"] for p in pairs),
    "new_trace_via_min_other_net_clearance_mm": min(p["gap_mm"] for p in pairs if "pad" not in p["kinds"]),
    "new_via_min_other_net_clearance_mm": min(p["gap_mm"] for p in pairs if "via" in p["kinds"]),
    "new_via_hole_to_any_smt_pad_min_mm": hole_to_pad,
    "u5_ground_pad_to_first_via_center_mm": math.dist(xy(pads["U5", "3"]), (72.0, 26.2)),
    "u6_ground_pad_to_first_via_center_mm": math.dist(xy(pads["U6", "3"]), (68.9, 22.2)),
    "native_drc": [{"category": k, "kind": t, "count": n} for (k,t),n in sorted(counts.items())],
    "split_or_unrouted_nets": sorted(result["split_nets"]),
    "open_gates": ["VBUS is unrouted and protection selection remains open.",
                   "Local USB ground is not yet joined to the board ground; continuous return pours remain open.",
                   "Merged cutout, footprint-to-edge acceptance, U1 assembly edge and enclosure tolerances remain open.",
                   "No Gerber solder-mask, online DFM or signal-integrity acceptance is claimed."]}
Path(f"{STEM}-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")

colors = {"USB_DP_CONN":"#c53c58", "USB_DM_CONN":"#286db2", "USB_DP_MCU":"#c53c58", "USB_DM_MCU":"#286db2", "USB_CC1":"#099a86", "USB_CC2":"#9e60ac", "GND":"#89969a"}
fig, axes = plt.subplots(1, 3, figsize=(20, 7), gridspec_kw={"width_ratios":[1,1,1.45]})
for ax, snap, bounds, title in zip(axes, [a,s,s], [(65,82,33,19),(65,82,33,19),(51,82,33,13)], ["A: initial crossover / 3 vias", "B: expanded crossover / 2 vias", "B: signal routing to MCU / return pours pending"]):
    for p in snap["pads"]:
        g = audit.pad_shape(p)
        ax.fill(*g.exterior.xy, color="#e5b66d", edgecolor="#946933", lw=.3)
    for t in snap["lines"]:
        if t["net"] == "NFC1_TBD":
            continue
        ax.plot([t["x1"]*MM,t["x2"]*MM],[t["y1"]*MM,t["y2"]*MM],color=colors.get(t["net"],"#444"),lw=t["widthMil"]*MM*5,ls="--" if t["layer"] == 2 else "-")
    for v in snap["vias"]:
        if v["net"] == "NFC1_TBD":
            continue
        ax.add_patch(plt.Circle(xy(v),v["diameterMil"]*MM/2,color=colors[v["net"]]))
        ax.add_patch(plt.Circle(xy(v),v["holeMil"]*MM/2,color="white"))
    for c in snap["components"]:
        x,y=xy(c)
        if bounds[0]<x<bounds[1] and bounds[3]<y<bounds[2]:
            ax.text(x,y,c["ref"],fontsize=7,ha="center",va="bottom",bbox={"facecolor":"white","alpha":.75,"edgecolor":"none","pad":.2})
    ax.add_patch(Rectangle((76.7,21.38),6.2,9.24,fill=False,edgecolor="#ac70b4",ls=":",lw=1))
    ax.set_xlim(bounds[:2]);ax.set_ylim(bounds[2:]);ax.set_aspect("equal");ax.grid(alpha=.15);ax.set_xlabel("PCB x / mm");ax.set_title(title,fontsize=10)
fig.suptitle("USB Spaced B — signal routing checked; full PCB / manufacturing NOT APPROVED",fontsize=14)
fig.text(.5,.04,"Red D+ / blue D- / green CC1 / purple CC2 / grey GND. Dashed = bottom. PCB y displayed downward; not an assembly view.",ha="center",fontsize=10)
fig.tight_layout(rect=(0,.07,1,.93));fig.savefig(f"{STEM}-review.png",dpi=180)
print(json.dumps(report,ensure_ascii=False,indent=2))
