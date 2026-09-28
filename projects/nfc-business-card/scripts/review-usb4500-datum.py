#!/usr/bin/env python3
"""Compare archived R14/R17 J1 geometry with the USB4500 A1 drawing.

Read-only, revision-specific analysis; not a footprint generator or DRC.
Writes a report and a nominal geometry comparison under hardware/records.
"""

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/records/usb4500-datum-review-2026-09-28"
MM = 0.0254
DRAWING = {"slot_row_pitch_mm": 4.0, "slot_span_mm": 11.24,
           "smt_front_mm": 4.6, "smt_rear_mm": 5.7,
           "notch_sidewall_spacing_mm": 9.24, "pcb_front_mm": -1.6}


def outline_segments(raw):
    previous = (raw[0] * MM, raw[1] * MM)
    index = 2
    while index < len(raw):
        angle = 0
        if raw[index] == "L":
            index += 1
        elif raw[index] == "ARC":
            angle = raw[index + 1]
            index += 2
        point = (raw[index] * MM, raw[index + 1] * MM)
        yield previous, point, angle
        previous = point
        index += 2


def review(revision):
    stem = f"r1-layout-reset-r{revision}"
    snapshot = ROOT / f"hardware/records/{stem}-routed-snapshot.json"
    folder = ROOT / f"hardware/production/{stem}"
    archive = folder / f"NFC-Card-R1-Layout-Reset-R{revision}-gerber.zip"
    s = json.loads(snapshot.read_text())
    j1 = next(c for c in s["components"] if c["ref"] == "J1")
    pads = [p for p in s["pads"] if p["id"].startswith(j1["id"])]
    smt = [p for p in pads if not p["hole"]]
    slots = [p for p in pads if p["hole"]]
    assert len(smt) == 12 and len(slots) == 4
    assert all(p["rotation"] == 90 for p in pads)
    front_x = max(p["x"] for p in slots) * MM
    center_y = (min(p["y"] for p in slots) + max(p["y"] for p in slots)) * MM / 2

    def local(point):
        return point[1] - center_y, front_x - point[0]

    profile = [p for p in s["polylines"] if p["layer"] == 11]
    assert len(profile) == 1
    segments = list(outline_segments(profile[0]["polygon"]["polygon"]))
    # Validate the snapshot against independently parsed exported geometry.
    with zipfile.ZipFile(archive) as z:
        copper = z.read("Gerber_TopLayer.GTL").decode()
        outline = z.read("Gerber_BoardOutlineLayer.GKO").decode()
    assert "%FSLAX26Y26*%" in copper and "%MOMM*%" in copper
    assert "%FSLAX26Y26*%" in outline and "%MOMM*%" in outline
    apertures = {int(n): (shape, float(w), float(h)) for n, shape, w, h in
                 re.findall(r"%ADD(\d+)([RO]),([\d.]+)X([\d.]+)\*%", copper)}
    flashes = []
    active = None
    for line in copper.splitlines():
        select = re.fullmatch(r"G54D(\d+)\*", line)
        if select:
            active = int(select[1])
        flash = re.fullmatch(r"G01X(-?\d+)Y(-?\d+)D03\*", line)
        if flash and active in apertures:
            flashes.append((int(flash[1]) / 1e6, int(flash[2]) / 1e6, apertures[active]))
    for pad in pads:
        matches = [f for f in flashes if math.dist(f[:2], (pad["x"] * MM, pad["y"] * MM)) < .002]
        assert len(matches) == 1, f"Missing/ambiguous copper flash: {pad['number']}"
        shape, width, height = matches[0][2]
        assert shape == ("R" if not pad["hole"] else "O")
        # Asymmetric rectangles/ovals independently check the rotation convention.
        assert abs(width - pad["pad"][2] * MM) < 2e-6
        assert abs(height - pad["pad"][1] * MM) < 2e-6
    vertices = [(int(x) / 1e6, int(y) / 1e6) for x, y in
                re.findall(r"G0[123]X(-?\d+)Y(-?\d+)(?:I-?\d+J-?\d+)?D0[12]\*", outline)]
    assert len(vertices) == len(segments) + 1
    assert all(min(math.dist(b, v) for v in vertices) < 2e-6 for _, b, _ in segments)
    local_segments = [(local(a), local(b), angle) for a, b, angle in segments]
    backs = [(a, b) for a, b, angle in local_segments if angle == 0 and
             abs(a[1] - b[1]) < 1e-6 and 0 < a[1] < 7 and a[0] * b[0] < 0]
    assert len(backs) == 1
    back_a, back_b = backs[0]
    walls = [(a, b) for a, b, angle in local_segments if angle == 0 and
             abs(a[0] - b[0]) < 1e-6 and 4 < abs(a[0]) < 5 and abs(a[1] - b[1]) > 3]
    assert len(walls) == 2
    pad_front = [front_x - (p["x"] + p["pad"][2] / 2) * MM for p in smt]
    pad_rear = [front_x - (p["x"] - p["pad"][2] / 2) * MM for p in smt]
    assert max(pad_front) - min(pad_front) < 1e-6
    cpl_path = folder / f"NFC-Card-R1-Layout-Reset-R{revision}-cpl.csv"
    rows = csv.DictReader(io.StringIO(cpl_path.read_text(encoding="utf-16")), delimiter="\t")
    cpl = next(row for row in rows if row["Designator"] == "J1")
    metrics = {
        "slot_row_pitch_mm": front_x - min(p["x"] for p in slots) * MM,
        "slot_span_mm": (max(p["y"] for p in slots) - min(p["y"] for p in slots)) * MM,
        "smt_front_mm": pad_front[0], "smt_rear_mm": pad_rear[0],
        "notch_back_mm": back_a[1],
        "pad_to_notch_gap_mm": pad_front[0] - back_a[1],
        "notch_back_straight_span_mm": abs(back_a[0] - back_b[0]),
        "notch_sidewall_spacing_mm": abs(walls[0][0][0] - walls[1][0][0]),
        "pcb_front_mm": min(p[1] for wall in walls for p in wall),
        "smt_front_error_from_drawing_mm": pad_front[0] - DRAWING["smt_front_mm"],
    }
    result = {"metrics": metrics, "cpl_j1": {k: cpl[k] for k in
              ("Mid X", "Mid Y", "Ref X", "Ref Y", "Rotation")},
              "export_check": "16 copper-flash centers agree within 0.002 mm (snapshot rounding); dimensions and outline vertices within 0.000002 mm",
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (snapshot, archive, cpl_path)}}
    return result, pads, local, local_segments


results = {r: review(r) for r in (14, 17)}
report = {"scope": "Nominal archived geometry only; no manufacturing approval or new PCB.",
          "datum": "u across connector; v into PCB; origin at midpoint of front mounting slots. mm.",
          "drawing": {"source": "https://gct.co/connector/usb4500", "revision": "A1, 2023-05-31",
                      "manual_dimension_transcription": DRAWING,
                      "limitation": "Undimensioned cutout corner reliefs are not reconstructed."},
          "revisions": {f"R{r}": results[r][0] for r in results}}
OUT.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

fig, axes = plt.subplots(1, 3, figsize=(14, 5.7), sharex=True, sharey=True)
colors = ["#1c6853", "#2a63a5", "#b44331"]
for ax, label, color in zip(axes, ("GCT A1 / nominal", "R14 / exported", "R17 / exported"), colors):
    ax.set_title(label, fontsize=14, fontweight="bold", pad=15)
    ax.axhline(0, color="#8b949e", linestyle=":", linewidth=1)
    ax.grid(alpha=.15)
    ax.set(xlim=(-6.6, 6.6), ylim=(-2.1, 7.8), xlabel="u across connector (mm)")
    ax.set_aspect("equal")
    ax.spines[["top", "right"]].set_visible(False)

for revision, ax, color in zip((14, 17), axes[1:], colors[1:]):
    result, pads, local, segments = results[revision]
    for pad in pads:
        u, v = local((pad["x"] * MM, pad["y"] * MM))
        w, h = pad["pad"][1] * MM, pad["pad"][2] * MM
        if pad["hole"]:
            ax.add_patch(FancyBboxPatch((u-w/2, v-h/2), w, h,
                         boxstyle=f"round,pad=0,rounding_size={w/2}", fill=False, ec=color))
            hw, hh = pad["hole"][1] * MM, pad["hole"][2] * MM
            ax.add_patch(FancyBboxPatch((u-hw/2, v-hh/2), hw, hh,
                         boxstyle=f"round,pad=0,rounding_size={hw/2}", fill=False, ec="#66717a", lw=.7))
        else:
            ax.add_patch(Rectangle((u-w/2, v-h/2), w, h, facecolor=color, alpha=.5))
    for a, b, angle in segments:
        if not angle:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=1.6)
        else:
            theta = math.radians(angle)
            cx = (a[0]+b[0])/2 - (b[1]-a[1])/(2*math.tan(theta/2))
            cy = (a[1]+b[1])/2 + (b[0]-a[0])/(2*math.tan(theta/2))
            start = math.atan2(a[1]-cy, a[0]-cx)
            radius = math.hypot(a[0]-cx, a[1]-cy)
            arc = [start+theta*i/30 for i in range(31)]
            ax.plot([cx+radius*math.cos(t) for t in arc], [cy+radius*math.sin(t) for t in arc], color=color, lw=1.6)
    m = result["metrics"]
    ax.text(0, 1.6, f"Sidewalls: {m['notch_sidewall_spacing_mm']:.3f} mm\nBack straight: {m['notch_back_straight_span_mm']:.3f} mm",
            ha="center", fontsize=10, linespacing=1.7)
    ax.text(0, 6.8, f"Pad-to-cutout gap: {m['pad_to_notch_gap_mm']:.3f} mm", ha="center", color=color, fontsize=11, weight="bold")

ax = axes[0]
for u in (-3.2, -2.4, -1.75, -1.25, -.75, -.25, .25, .75, 1.25, 1.75, 2.4, 3.2):
    width = .6 if abs(u) > 2 else .3
    ax.add_patch(Rectangle((u-width/2, 4.6), width, 1.1, facecolor=colors[0], alpha=.5))
for u in (-5.62, 5.62):
    for v, length in ((0, 2.2), (4, 1.8)):
        ax.add_patch(FancyBboxPatch((u-.5, v-length/2), 1, length,
                     boxstyle="round,pad=0,rounding_size=0.5", fill=False, ec=colors[0]))
        ax.add_patch(FancyBboxPatch((u-.3, v-(length-.4)/2), .6, length-.4,
                     boxstyle="round,pad=0,rounding_size=0.3", fill=False, ec="#66717a", lw=.7))
for sign in (-1, 1):
    ax.plot([sign*6.6, sign*4.62, sign*4.62], [-1.6, -1.6, 4.3], color=colors[0], lw=1.6)
ax.plot([-4.1, 4.1], [4.6, 4.6], color=colors[0], lw=1.6)
ax.text(0, 1.6, "Sidewalls: 9.240 mm\nCorner reliefs omitted*", ha="center", fontsize=10, linespacing=1.7)
ax.text(0, 6.8, "Pad front: v = 4.600 mm", ha="center", color=colors[0], fontsize=11, weight="bold")
ax.set_ylabel("v into PCB from front slot row (mm)")
fig.suptitle("USB4500: compare pads and cutout using mounting slots as the datum", fontsize=16, y=.98)
fig.text(.5, .11, "v = 0 is the front mounting-slot row. Copper shaded; holes outlined. Board material lies above the cutout back edge.", ha="center", fontsize=10)
fig.text(.5, .06, "*GCT corner reliefs lack explicit dimensions; the drawing panel is a dimensional sketch, not a fabrication footprint.", ha="center", fontsize=10)
fig.subplots_adjust(left=.06, right=.98, bottom=.20, top=.87, wspace=.18)
fig.savefig(OUT.with_suffix(".png"), dpi=160)
plt.close(fig)
print(json.dumps({f"R{r}": results[r][0]["metrics"] for r in results}, indent=2))
