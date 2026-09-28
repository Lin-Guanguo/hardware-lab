#!/usr/bin/env python3
"""Audit and render Placement A; this partial PCB cannot pass fabrication gates."""
import collections
import argparse
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
from shapely.geometry import LineString, Point, Polygon, box

PROJECT = Path(__file__).resolve().parents[1]
RECORDS = PROJECT / "hardware/records"
STEM = RECORDS / "midmount-placement-a"
MM = .0254
spec = importlib.util.spec_from_file_location("copper_audit", Path(__file__).with_name("check-r1-copper.py"))
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", type=Path, help="Successful output of eda-export-midmount-candidate.js")
args = parser.parse_args()
if args.capture:
    capture = json.loads(args.capture.read_text())
    assert capture["success"]
    data = capture["result"]
    assert data["project"]["name"] == "NFC-Card-R2-Midmount-Placement-A"
    for key, suffix in [("snapshot", "snapshot.json"), ("pins", "pcb-pins.json"),
                        ("rules", "rules.json"), ("netlist", "schematic.enet")]:
        Path(f"{STEM}-{suffix}").write_text(json.dumps(data[key], ensure_ascii=False, indent=2)+"\n")
    Path(f"{STEM}-bom.tsv").write_text(data["bom"])
    errors = []
    def flatten(value):
        if isinstance(value, list):
            for item in value:
                flatten(item)
        elif isinstance(value, dict):
            if "errorType" in value:
                errors.append({k:v for k,v in value.items() if k in
                               ["errorType", "errorObjType", "ruleName", "obj1", "obj2", "net", "pos", "objs"]})
            else:
                flatten(value.get("list", []))
    flatten(data["drc"])
    Path(f"{STEM}-drc.json").write_text(json.dumps({"project": data["project"],
        "status": "PARTIAL_ROUTING_NOT_PASSED", "errors": errors}, ensure_ascii=False, indent=2)+"\n")


def load(suffix):
    return json.loads(Path(f"{STEM}-{suffix}").read_text())


def named_pads(snapshot):
    result = {}
    for c in snapshot["components"]:
        for p in snapshot["pads"]:
            if p["id"].startswith(c["id"]):
                result[c["ref"], p["number"]] = p
    return result


def xy(p):
    return p["x"] * MM, p["y"] * MM


def normalized_nfc(snapshot):
    lines = [tuple(round(t[k], 3) if isinstance(t[k], (int, float)) else t[k]
                   for k in ["layer", "x1", "y1", "x2", "y2", "widthMil"])
             for t in snapshot["lines"] if t["net"] == "NFC1_TBD"]
    vias = [tuple(round(v[k], 3) for k in ["x", "y", "diameterMil", "holeMil"])
            for v in snapshot["vias"] if v["net"] == "NFC1_TBD"]
    return sorted(lines), sorted(vias)


snapshot = load("snapshot.json")
rules = load("rules.json")["config"]
assert abs(rules["Physics"]["Via Size"]["viaSize"]["form"]["viaOuterdiameterMin"]-.6) < .00001
assert all(v >= .19999 for row in rules["Spacing"]["Safe Spacing"]["copperThickness1oz"]["tables"]["1"]["content"][:7] for v in row)
baseline = json.loads((RECORDS / "r1-layout-reset-r21-routed-snapshot.json").read_text())
current, before = named_pads(snapshot), named_pads(baseline)
assert normalized_nfc(snapshot) == normalized_nfc(baseline), "NFC geometry changed"
assert len(snapshot["components"]) == 66 and len(current) == 256
assert not snapshot["pours"] and not snapshot["poured"]

# Calibrate the asymmetric pad convention against GCT's 1.10 x 0.30 mm land.
pad = current["J1", "A6"]
g = audit_module.pad_shape(pad)
assert abs(g.bounds[2] - g.bounds[0] - 1.1) < .003
assert abs(g.bounds[3] - g.bounds[1] - .3) < .003

components = {c["ref"]: c for c in snapshot["components"]}
old_components = {c["ref"]: c for c in baseline["components"]}
moved = [ref for ref, c in components.items()
         if any(abs(c[k] - old_components[ref][k]) > .003 for k in ["x", "y", "rotation"])]
assert not set(moved) & {"U1", "C1", "C6", "C7", "U2", "U3", "J2", "SW1", "SW2", "SW3"}
board_pads = [p for p in snapshot["pads"] if not any(p["id"].startswith(c["id"]) for c in components.values())]
old_board = {p["id"]: p for p in baseline["pads"]}
assert all(p == old_board[p["id"]] for p in board_pads), "Battery/debug pads changed"

bom = list(csv.DictReader(io.StringIO(Path(f"{STEM}-bom.tsv").read_text()), delimiter="\t"))
bom_refs = {ref for row in bom for ref in row["Designator"].split(",")}
assert bom_refs == components.keys()
j1_bom = next(row for row in bom if row["Designator"] == "J1")
assert j1_bom["Supplier Part"] == "C5354966"

netlist = load("schematic.enet")
sch = {c["props"]["Designator"]: c for c in netlist["components"].values()}
assert all(sch[ref]["pinInfoMap"][number].get("net", "") == p["net"] for (ref, number), p in current.items())

new_nets = {"USB_DP_CONN", "USB_DM_CONN"}
items = []
for p in snapshot["pads"]:
    for layer in ([1, 2] if p["layer"] == 12 else [p["layer"]]):
        items.append((p["id"], p["net"], layer, audit_module.pad_shape(p), False))
for i, t in enumerate(snapshot["lines"]):
    items.append((f"track{i}", t["net"], t["layer"], LineString([
        (t["x1"]*MM, t["y1"]*MM), (t["x2"]*MM, t["y2"]*MM)]).buffer(t["widthMil"]*MM/2), t["net"] in new_nets))
for i, v in enumerate(snapshot["vias"]):
    for layer in (1, 2):
        items.append((f"via{i}", v["net"], layer, Point(xy(v)).buffer(v["diameterMil"]*MM/2), v["net"] in new_nets))
minimum, violations = 100.0, []
for i, (name, net, layer, shape, new) in enumerate(items):
    for name2, net2, layer2, shape2, new2 in items[i+1:]:
        if layer != layer2 or net == net2 or not (new or new2):
            continue
        gap = shape.distance(shape2)
        minimum = min(minimum, gap)
        if gap < .199:
            violations.append([name, name2, gap])
assert not violations, violations

copper = audit_module.audit(snapshot)
assert not copper["floating_copper"] and not copper["dead_ends"]
assert not copper["single_layer_or_isolated_vias"]
assert not copper["screen_unexpected_copper_mm2"]
for net, pins in [("USB_DP_CONN", [("J1", "A6"), ("J1", "B6"), ("U5", "1")]),
                  ("USB_DM_CONN", [("J1", "A7"), ("J1", "B7"), ("U5", "2")])]:
    labels = {f"{current[key]['number']}@({xy(current[key])[0]:.2f},{xy(current[key])[1]:.2f})" for key in pins}
    assert any(labels <= set(group) for group in copper["groups"][net]), (net, labels)

services = [("C9", "1", "U4", "1"), ("C10", "1", "U4", "6"), ("C10", "1", "U4", "5"),
            ("C12", "1", "D1", "1"), ("C13", "1", "D3", "2"), ("R15", "1", "Q1", "2")]
distances = [{"pads": f"{a}.{b} - {c}.{d}",
              "before_mm": math.dist(xy(before[a,b]), xy(before[c,d])),
              "after_mm": math.dist(xy(current[a,b]), xy(current[c,d]))} for a,b,c,d in services]
gap_before = audit_module.pad_shape(before["L1", "2"]).distance(audit_module.pad_shape(before["Q1", "3"]))
gap_after = audit_module.pad_shape(current["L1", "2"]).distance(audit_module.pad_shape(current["Q1", "3"]))
triangle = lambda pads: Polygon([xy(pads[key]) for key in [("C10", "1"), ("L1", "1"), ("Q1", "3")]]).area

slots = [current["J1", n] for n in ["17", "18", "19", "20"]]
front_x = max(p["x"]*MM for p in slots)
smt_x = pad["x"]*MM
drc = load("drc.json")
counts = collections.Counter((e["errorType"], e["errorObjType"]) for e in drc["errors"])
report = {
    "status": "PARTIAL_PLACEMENT_AND_USB_FANOUT_NOT_FOR_FABRICATION",
    "counts": {"components": len(components), "component_pins": len(current), "all_pads": len(snapshot["pads"]),
               "tracks": len(snapshot["lines"]), "vias": len(snapshot["vias"]), "bom_groups": len(bom)},
    "moved_components": moved, "nfc_geometry_unchanged": True, "battery_debug_pads_unchanged": True,
    "pin_nets_match": True, "usb_local_three_pad_connectivity": True,
    "usb_new_copper_min_other_net_clearance_mm": minimum,
    "usb_new_vias": [{"xy_mm": xy(v), "hole_mm": v["holeMil"]*MM, "diameter_mm": v["diameterMil"]*MM}
                     for v in snapshot["vias"] if v["net"] in new_nets],
    "usb4500_nominal_datum_mm": {"front_slots_x": front_x, "axis_y": sum(p["y"]*MM for p in slots)/4,
                                "pad_front_v": front_x-smt_x-1.1/2, "pad_rear_v": front_x-smt_x+1.1/2,
                                "slot_span": max(p["y"]*MM for p in slots)-min(p["y"]*MM for p in slots)},
    "named_pad_center_distances": distances,
    "l1_q1_copper_gap_mm": {"before": gap_before, "after": gap_after},
    "l1_q1_mask_gap_estimate_mm": {"before": gap_before-2*.05100066, "after": gap_after-2*.05100066},
    "display_triangle_proxy_mm2_not_routed_loop": {"before": triangle(before), "after": triangle(current)},
    "native_drc_counts": [{"category": a, "kind": b, "count": n} for (a,b),n in sorted(counts.items())],
    "unrouted_or_split_nets": sorted(copper["split_nets"]),
    "independent_copper": {k:copper[k] for k in ["dead_ends", "floating_copper", "single_layer_or_isolated_vias", "screen_unexpected_copper_mm2"]},
    "open_gates": ["Merged board outline and connector cutout are not fabrication-ready; footprint e62 remains unapproved.",
                   "USB protection ground, CC, VBUS and downstream data routing are incomplete.",
                   "Four retained NFC lead vias are below the new 0.60 mm outside-diameter target.",
                   "Display placement proxies are not routed current-loop or thermal verification.",
                   "FPC fold, plug insertion, tolerances, process rails and panelization remain unverified.",
                   "J1 imported 3D association is invalid; no synchronized enclosure validation.",
                   "Battery ratings, display peak load and VBUS protection remain open."]}
Path(f"{STEM}-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")

fig, axes = plt.subplots(1, 3, figsize=(19, 7), gridspec_kw={"width_ratios": [1.6, 1, 1]})
colors = {"USB_DP_CONN":"#ce3f57", "USB_DM_CONN":"#296fb8", "NFC1_TBD":"#a5862b"}
for ax in axes:
    ax.set_aspect("equal")
    for p in snapshot["polylines"]:
        if p["layer"] != 11:
            continue
        points = audit_module.parse_path(p["polygon"]["polygon"], MM)
        ax.plot(*zip(*points), color="#303d49", lw=1.1)
    for p in snapshot["pads"]:
        g = audit_module.pad_shape(p)
        ax.fill(*g.exterior.xy, color="#dfaf64", edgecolor="#865b28", lw=.25)
    for t in snapshot["lines"]:
        ax.plot([t["x1"]*MM,t["x2"]*MM],[t["y1"]*MM,t["y2"]*MM],
                color=colors.get(t["net"],"#555"),lw=max(.4,t["widthMil"]*MM*3),
                linestyle="--" if t["layer"]==2 and t["net"]!="NFC1_TBD" else "-")
    for v in snapshot["vias"]:
        ax.add_patch(plt.Circle(xy(v), v["diameterMil"]*MM/2, color=colors.get(v["net"],"#666")))
        ax.add_patch(plt.Circle(xy(v), v["holeMil"]*MM/2, color="white"))
    ax.add_patch(Rectangle((76.7,21.38),6.2,9.24,facecolor="none",edgecolor="#9c5fad",ls="--",lw=1))
    ax.grid(alpha=.12)
    ax.tick_params(labelsize=8)
    ax.set_xlabel("PCB x / mm")
axes[0].add_patch(Rectangle((1.5,1.5),32.5,14,facecolor="#e8edf0",edgecolor="#728493",ls="--"))
axes[0].add_patch(Rectangle((1.95,18.25),37.42,31.9,facecolor="none",edgecolor="#728493",ls="--"))
axes[0].text(17.75,8,"301030 battery cavity\nPack outline not measured",ha="center",fontsize=8)
for ax, bounds, title in zip(axes, [(0,85,53,0),(70.5,82,30,21),(60.5,81,46,28)],
                           ["PCB coordinates / y displayed downward", "USB local crossover / 3 vias", "Display power / placement only"]):
    ax.set_xlim(bounds[:2]);ax.set_ylim(bounds[2:]);ax.set_title(title,fontsize=11)
    for ref,c in components.items():
        x,y=xy(c)
        if bounds[0]<x<bounds[1] and bounds[3]<y<bounds[2]:
            if ax==axes[0] and not ref.startswith(("U","J","SW")):
                continue
            ax.text(x,y,ref,fontsize=7,ha="center",va="bottom",color="#102435",bbox={"facecolor":"white","alpha":.7,"pad":.2,"edgecolor":"none"})
fig.suptitle("0.8 mm mid-mount study — PARTIAL ROUTING, NOT FOR FABRICATION",fontsize=15)
fig.text(.5,.035,"Dashed blue = bottom trace; purple box = nominal cutout reference only. Ground return and merged board outline remain open.",ha="center",fontsize=10)
fig.tight_layout(rect=(0,.07,1,.94))
fig.savefig(f"{STEM}-review.png",dpi=180)
print(json.dumps({k:report[k] for k in ["counts","moved_components","usb_new_copper_min_other_net_clearance_mm","l1_q1_copper_gap_mm","display_triangle_proxy_mm2_not_routed_loop"]},ensure_ascii=False,indent=2))
print("Partial-stage checks passed; full copper connectivity and fabrication gates remain open.")
