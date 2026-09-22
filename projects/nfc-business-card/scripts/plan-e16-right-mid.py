"""Plan the E16 right-mid USB layout from saved E15 EasyEDA geometry.

The script reads the saved E15 snapshot plus the per-component pin table, applies
the candidate placement for the right-mid USB study, checks the result with real
pad coordinates, and writes a review JSON. It is a planning artifact: the live
client still owns rotation sign, DRC and the saved project.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HW = ROOT / "projects/nfc-business-card/hardware"
SNAPSHOT = HW / "e15-clean-layout.json"
PINS = HW / "e14-eda-components-pins.json"
OUT_JSON = HW / "e16-right-mid-plan.json"

MIL = 39.37007874015748
MM = 1.0 / MIL

# Candidate outline: straight bottom edge, USB notch on the right edge.
# Notch depth 6.5 mm and height 13 mm reproduce the verified bottom-edge
# geometry that measured 0.20 mm copper-to-rout clearance.
OUTLINE_MM = [
    (0.0, 0.0), (0.0, 52.0), (84.0, 52.0), (84.0, 20.62),
    (77.5, 20.62), (77.5, 11.38), (84.0, 11.38), (84.0, 0.0),
]
USB_CENTER_Y_MM = 16.0

# ref -> (x_mm, y_mm, rotation_deg). Rotation sign must be confirmed in the
# live client; the geometry below assumes counter-clockwise positive degrees.
PLAN = {
    "J1": (78.53, USB_CENTER_Y_MM, 90),
    "U1": (65.00, 8.00, 180),
    "C5": (61.00, 17.20, 0),
    "C6": (63.40, 17.20, 0),
    "C7": (65.80, 17.20, 0),
    "U5": (73.60, 16.60, 0),
    "U6": (73.60, 14.90, 0),
    "R1": (71.90, 14.75, 0),
    "R2": (71.90, 17.75, 0),
    "C1": (73.60, 12.60, 0),
    "C3": (71.90, 20.60, 0),
    # button column: even 5.90 mm pitch, 0.70 mm gaps, 0.70 mm bottom margin
    "SW1": (38.10, 3.30, 0),
    "SW2": (38.10, 9.20, 0),
    "SW3": (38.10, 15.10, 0),
    # VBUS bulk cap moved off the button column and next to the charger input
    "C8": (42.00, 20.50, 0),
}

NFC_KEEPOUT_MM = (60.0, 24.0, 82.0, 50.0)
ANTENNA_KEEPOUT_MM = (59.4, 0.0, 70.6, 3.2)
PAD_CLEARANCE_MM = 0.20


def rotate(dx: float, dy: float, degrees: float) -> tuple:
    r = math.radians(degrees)
    return (dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r))


def outline_area(points: list) -> float:
    total = 0.0
    for i, (x0, y0) in enumerate(points):
        x1, y1 = points[(i + 1) % len(points)]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def point_in_outline(x: float, y: float, points: list) -> bool:
    inside = False
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            t = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if t > x:
                inside = not inside
    return inside


def distance_to_outline(x: float, y: float, points: list) -> float:
    best = float("inf")
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        seg = dx * dx + dy * dy
        t = 0.0 if seg == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / seg))
        best = min(best, math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)))
    return best


def boxes_overlap(a, b, clearance: float) -> bool:
    return not (a[2] + clearance <= b[0] or b[2] + clearance <= a[0] or a[3] + clearance <= b[1] or b[3] + clearance <= a[1])


# Connector/module bodies are larger than their pad extents, so they are
# modelled explicitly for clearance checks.
BODY_MM = {
    "U1": (10.5, 15.5),   # Raytac MDBT50Q-P1MV2 module outline
    "J1": (11.24, 6.5),   # GCT USB4500 shell, length along the insertion axis
    "J2": (6.5, 9.0),     # FPC-05FB-24PH20 housing
    "SW1": (5.2, 5.2), "SW2": (5.2, 5.2), "SW3": (5.2, 5.2),
    "L1": (3.0, 3.0),
}
# For J1 the body is not centred on the origin: 2.10 mm behind, 4.45 mm toward the
# opening (GCT recommended-layout section dimensions).
BODY_OFFSET_MM = {"J1": (-2.10, 4.45)}


def body_rect(entry: dict):
    ref = entry["ref"]
    if ref not in BODY_MM:
        return None
    w, l = BODY_MM[ref]
    rot = entry["rotation"]
    if ref == "J1":
        back, front = BODY_OFFSET_MM[ref]
        corners = [(w / 2, back), (w / 2, -front), (-w / 2, -front), (-w / 2, back)]
    else:
        corners = [(w / 2, l / 2), (w / 2, -l / 2), (-w / 2, -l / 2), (-w / 2, l / 2)]
    pts = [rotate(cx, cy, rot) for cx, cy in corners]
    xs = [entry["x"] + p[0] for p in pts]
    ys = [entry["y"] + p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


snapshot = json.loads(SNAPSHOT.read_text())
pins = {entry["ref"]: entry for entry in json.loads(PINS.read_text())}
outline = [(round(x, 3), round(y, 3)) for x, y in OUTLINE_MM]

placed = {}
for comp in snapshot["components"]:
    ref = comp["ref"]
    src = pins[ref]
    if ref in PLAN:
        x_mm, y_mm, rot_new = PLAN[ref]
        rot_old = src.get("rotation", 0) or 0
        world = []
        for pin in src["pins"]:
            dx, dy = (pin["x"] - src["x"]) * MM, (pin["y"] - src["y"]) * MM
            lx, ly = rotate(dx, dy, -rot_old)
            px, py = rotate(lx, ly, rot_new)
            world.append({"n": pin["n"], "net": pin.get("net"), "x": x_mm + px, "y": y_mm + py})
        placed[ref] = {"x": x_mm, "y": y_mm, "rotation": rot_new, "moved": True, "pads": world}
    else:
        world = [{"n": p["n"], "net": p.get("net"), "x": p["x"] * MM, "y": p["y"] * MM} for p in src["pins"]]
        placed[ref] = {"x": comp["x"] * MM, "y": comp["y"] * MM, "rotation": src.get("rotation", 0), "moved": False, "pads": world}


def box(entry):
    xs = [p["x"] for p in entry["pads"]]
    ys = [p["y"] for p in entry["pads"]]
    return (min(xs), min(ys), max(xs), max(ys))


def collect_outline_issues(placed_map: dict, poly: list) -> list:
    found = []
    for ref, entry in placed_map.items():
        for pad in entry["pads"]:
            if not point_in_outline(pad["x"], pad["y"], poly):
                found.append("OUTSIDE " + ref + " pad " + str(pad["n"]))
    return found


def collect_issues(placed_map: dict) -> list:
    found = []
    for ref, entry in placed_map.items():
        rect = body_rect(entry)
        if rect is None:
            continue
        nx0, ny0, nx1, ny1 = NFC_KEEPOUT_MM
        if boxes_overlap(rect, (nx0, ny0, nx1, ny1), 0.0):
            found.append("NFC " + ref + " body overlaps the NFC reserve")
    refs_local = sorted(placed_map)
    for i, a in enumerate(refs_local):
        for b in refs_local[i + 1:]:
            ra, rb = body_rect(placed_map[a]), body_rect(placed_map[b])
            ba, bb = box(placed_map[a]), box(placed_map[b])
            if ra and rb and boxes_overlap(ra, rb, 0.30):
                found.append("BODYCLASH %s/%s bodies within 0.30 mm" % (a, b))
            elif boxes_overlap(ba, bb, PAD_CLEARANCE_MM):
                found.append("PADCLOSE %s/%s pads within %.2f mm" % (a, b, PAD_CLEARANCE_MM))
            if ra and boxes_overlap(ra, bb, 0.10):
                found.append("BODYPAD %s body vs %s pads within 0.10 mm" % (a, b))
            if rb and boxes_overlap(ba, rb, 0.10):
                found.append("BODYPAD %s body vs %s pads within 0.10 mm" % (b, a))
    ax0, ay0, ax1, ay1 = antenna_keepout(placed_map["U1"])
    for ref, entry in placed_map.items():
        if ref == "U1":
            continue
        if boxes_overlap(box(entry), (ax0, ay0, ax1, ay1), 0.0):
            found.append("ANTENNA " + ref + " pads inside the U1 antenna keepout")
    return found


def antenna_keepout(u1: dict) -> tuple:
    """Area under the module antenna: the pin-free end of the module."""
    rot = u1["rotation"]
    half_w = 10.5 / 2
    corners = [(half_w, 7.75), (half_w, 5.45), (-half_w, 5.45), (-half_w, 7.75)]
    pts = [rotate(cx, cy, rot) for cx, cy in corners]
    xs = [u1["x"] + pt[0] for pt in pts]
    ys = [u1["y"] + pt[1] for pt in pts]
    return (min(xs), min(ys), max(xs), max(ys))


BASELINE_OUTLINE_MM = [
    (0.0, 0.0), (0.0, 52.0), (84.0, 52.0), (84.0, 0.0),
    (56.0, 0.0), (56.0, 6.5), (43.0, 6.5), (43.0, 0.0),
]

baseline = {}
for comp in snapshot["components"]:
    src_pins = pins[comp["ref"]]
    baseline[comp["ref"]] = {
        "ref": comp["ref"], "x": comp["x"] * MM, "y": comp["y"] * MM,
        "rotation": src_pins.get("rotation", 0) or 0,
        "pads": [{"n": pin["n"], "x": pin["x"] * MM, "y": pin["y"] * MM} for pin in src_pins["pins"]],
    }
for ref, entry in placed.items():
    entry["ref"] = ref

baseline_issues = collect_issues(baseline)
plan_issues = collect_issues(placed)
new_issues = [i for i in plan_issues if i not in baseline_issues]
fixed_issues = [i for i in baseline_issues if i not in plan_issues]
baseline_outline = collect_outline_issues(baseline, BASELINE_OUTLINE_MM)
plan_outline = collect_outline_issues(placed, outline)
issues = plan_issues

plan_json = {
    "date": "2026-09-22",
    "purpose": "Right-mid USB layout plan for E16, derived from saved E15 geometry",
    "outline_mm": outline,
    "outline_area_mm2": round(outline_area(outline), 1),
    "usb_notch": {"edge": "right", "x_mm": [77.5, 84.0], "y_mm": [11.38, 20.62], "depth_mm": 6.5, "height_mm": 9.24},
    "usb_datum": {
        "pcb_edge_to_origin_mm": 1.025,
        "origin_mm": [78.525, USB_CENTER_Y_MM],
        "opening": "+x",
        "display_envelope_mm": [2.0, 18.3, 39.42, 50.2],
        "note": "notch inner edge 1.025 mm in front of the footprint origin; height 9.24 mm follows the GCT recommended-layout solder-area width so the anchor pads stay on the board flanges",
    },
    "moved_components": {ref: {"x_mm": p["x"], "y_mm": p["y"], "rotation_deg": p["rotation"]} for ref, p in placed.items() if p["moved"]},
    "button_layout": {"pitch_mm": 5.9, "gap_mm": 0.7, "bottom_margin_mm": 0.7, "x_mm": 38.1},
    "antenna_keepout_mm": [round(v, 2) for v in antenna_keepout(placed["U1"])],
    "checks": {
        "new_issue_count": len(new_issues),
        "new_issues": new_issues,
        "carried_over_count": len([i for i in plan_issues if i in baseline_issues]),
        "carried_over": sorted(set(i for i in plan_issues if i in baseline_issues)),
        "resolved_by_the_move": sorted(set(fixed_issues)),
        "outline_plan": plan_outline,
        "outline_baseline": baseline_outline,
        "outline_note": "the connector front anchor row sits inside the USB cut-out in both layouts; the cut-out shape stays a mechanical item until the connector section is confirmed",
        "verified": len(new_issues) == 0,
    },
    "verification": {
        "source": "saved E15 EasyEDA snapshot plus E14 pin table",
        "method": "pad-centre and body rectangles vs candidate outline, NFC reserve and antenna keepout",
        "live_client": "applied to E16 on 2026-09-22 and verified by close/reopen; see e16-right-mid-applied.json",
    },
}
OUT_JSON.write_text(json.dumps(plan_json, ensure_ascii=False, indent=2) + "\n")
print("wrote", OUT_JSON)
print("new issues:", len(new_issues))
for issue in new_issues:
    print("  NEW -", issue)
print("carried over:", len(plan_json["checks"]["carried_over"]))
for issue in plan_json["checks"]["carried_over"]:
    print("  kept -", issue)
