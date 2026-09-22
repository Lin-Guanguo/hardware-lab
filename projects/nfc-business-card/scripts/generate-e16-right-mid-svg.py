"""Render the current E16 right-mid USB placement as a review SVG.

Geometry comes from hardware/e16-right-mid-snapshot.json, which is exported
from the live E16 sheet with scripts/eda-export-e16-snapshot.js. The drawing is
a review artifact: board outline, mechanical envelopes, keep-out regions,
component bodies and pad-derived markers. It is not a manufacturing export.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HW = ROOT / "projects/nfc-business-card/hardware"
SNAPSHOT = HW / "e16-right-mid-snapshot.json"
OUT = ROOT / "projects/nfc-business-card/enclosure/pcba-e16-right-mid.svg"

MIL = 39.37007874015748
SCALE = 10.0
OX, OY = 96.0, 96.0
H_MM = 52.0
CANVAS_W, CANVAS_H = 1460, 900

# Layer 12 region objects do not expose their polygon through the bridge, so the
# extents stay hard-coded here and are documented in pcb-e16-usb-right-mid.md.
NFC_KEEP_OUT = (60.0, 24.0, 82.0, 50.0)   # 9d23f6bb076fa2f0
U1_ANTENNA_KEEP_OUT = (59.7, 0.2, 70.3, 2.5)  # d49ece88915402a1

# Two keys, SW1 (top) and SW3 (bottom), both on x = 38.1.
KEY_REFS = ("SW1", "SW2", "SW3")

cur = json.loads(SNAPSHOT.read_text())

GROUP = {
    "U1": "MCU",
    "J2": "EPD/FPC",
}
for ref in ["J1", "U5", "U6", "R1", "R2", "R3", "R4"]:
    GROUP[ref] = "USB/ESD"
for ref in ["U4", "C9", "C10", "R13", "L1", "Q1", "R14", "R15", "D1", "D2", "D3", "C11", "C12", "C13", "R16", "R17", "R18"]:
    GROUP[ref] = "EPD/FPC"
COLORS = {
    "USB/ESD": "#C2542F",
    "MCU": "#1D4ED8",
    "EPD/FPC": "#0F766E",
    "Power": "#A855F7",
    "Buttons": "#D97706",
    "Other": "#64748B",
}
LEGEND = [
    ("USB/ESD", "USB / ESD / CC"),
    ("Power", "充电与去耦"),
    ("EPD/FPC", "屏幕 FPC / EPD 电源"),
    ("MCU", "U1 主控（天线朝下）"),
    ("Buttons", "三键（SW1 / SW2 / SW3）"),
]


def group_of(ref: str) -> str:
    if ref not in GROUP:
        GROUP[ref] = "Buttons" if ref.startswith("SW") else "Power"
    return GROUP[ref]


def dx(x: float) -> float:
    return OX + x * SCALE


def dy(y: float) -> float:
    return OY + (H_MM - y) * SCALE


def path(points) -> str:
    return " ".join("%s %.1f %.1f" % ("M" if i == 0 else "L", dx(px), dy(py)) for i, (px, py) in enumerate(points)) + " Z"


def polygon_points(raw):
    nums = raw["polygon"] if isinstance(raw, dict) else raw
    out = []
    i = 0
    while i + 1 < len(nums):
        if isinstance(nums[i], str) or isinstance(nums[i + 1], str):
            i += 1
            continue
        out.append((nums[i] / MIL, nums[i + 1] / MIL))
        i += 2
    return out


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def rect_pts(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def body(ref, cx, cy):
    if ref == "U1":
        return rect_pts(cx, cy, 10.5, 15.5)
    if ref == "J2":
        return rect_pts(cx, cy, 9.0, 6.5)
    if ref.startswith("SW"):
        return rect_pts(cx, cy, 5.2, 5.2)
    if ref == "L1":
        return rect_pts(cx, cy, 3.0, 3.0)
    if ref == "J1":
        # Shell straddles the right board edge, opening toward +x.
        return [(cx - 2.10, cy - 5.62), (cx + 4.45, cy - 5.62), (cx + 4.45, cy + 5.62), (cx - 2.10, cy + 5.62)]
    return None


keys = {c["ref"]: (c["x"] / MIL, c["y"] / MIL) for c in cur["components"] if c["ref"] in KEY_REFS}
key_pitch = keys["SW3"][1] - keys["SW1"][1]
if "SW2" in keys:
    tri = {other: ((keys["SW2"][0] - keys[other][0]) ** 2 + (keys["SW2"][1] - keys[other][1]) ** 2) ** 0.5
           for other in ("SW1", "SW3")}
else:
    tri = {}
refs = sorted(c["ref"] for c in cur["components"])

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (CANVAS_W, CANVAS_H, CANVAS_W, CANVAS_H),
    '<rect width="%d" height="%d" fill="#F7F9FC"/>' % (CANVAS_W, CANVAS_H),
    '<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}.t{font-size:13px}.s{font-size:11.5px}.m{fill:#52657B}.xs{font-size:9.5px}.b{font-weight:bold}</style>',
    '<text x="36" y="34" font-size="25" font-weight="bold">E16 · 右侧中部 USB · L 形板框 · 三键（方案 B）</text>',
    '<text x="36" y="57" class="m">来源：E16 图页实时快照（%s）；1 mm = 10 px，Y 轴向上为板面正视</text>' % html.escape(SNAPSHOT.name),
]

# Board outline comes straight from layer 11 of the live Snapshot.
outline = next(polygon_points(p["polygon"]) for p in cur["polylines"] if p["layer"] == 11)
reference = next((polygon_points(p["polygon"]) for p in cur["polylines"] if p["layer"] == 14), None)
if reference:
    parts.append('<path d="%s" fill="none" stroke="#94A3B8" stroke-width="1.4" stroke-dasharray="6 4"/>' % path(reference))
    parts.append('<text x="%.0f" y="%.0f" class="xs m">灰色虚线 = 84 × 52 参考板框（当前板框是 L 形）</text>' % (dx(0) + 4, dy(0) + 44))
parts.append('<path d="%s" fill="#E8EDF3" stroke="#334155" stroke-width="2.4"/>' % path(outline))

# Mechanical review envelopes (layer 9).
for poly in [p for p in cur["polylines"] if p["layer"] == 9]:
    pts = polygon_points(poly["polygon"])
    x0, y0, x1, y1 = bbox(pts)
    w, h = x1 - x0, y1 - y0
    if abs(x0 - 3) < 0.3 and abs(w - 30) < 0.5:
        label, colour = "301230 电池 · 30×12", "#64748B"
    elif abs(x0 - 2) < 0.3 and abs(w - 37.42) < 0.5:
        label, colour = "SCREEN / FPC · 37.42×31.9", "#0F766E"
    elif abs(x0 - 60) < 0.3 and abs(w - 22) < 0.5:
        # The layer-12 keep-out label is drawn in the same place.
        label, colour = "", "#16806B"
    elif abs(x0 - 47.5) < 0.3:
        label, colour = "J2 FPC · 弯折/支撑待定", "#0F766E"
    elif abs(x0 - 59.75) < 0.3:
        label, colour = "", "#B45309"
    elif abs(x0 - 35.5) < 0.3:
        label, colour = "", "#D97706"
    else:
        label, colour = "", "#64748B"
    parts.append(
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.10" stroke="%s" stroke-width="1.1" stroke-dasharray="3 3"/>'
        % (dx(x0), dy(y1), w * SCALE, h * SCALE, colour, colour)
    )
    if label:
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" class="xs" fill="%s">%s</text>'
            % (dx((x0 + x1) / 2), dy((y0 + y1) / 2), colour, html.escape(label))
        )

# Keep-out regions (layer 12 objects 9d23f6bb076fa2f0 and d49ece88915402a1).
for (x0, y0, x1, y1), label, colour in [
    (NFC_KEEP_OUT, "NFC 保留区（禁布，双面零铜）", "#16806B"),
]:
    parts.append(
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.30" stroke="%s" stroke-width="1.8" stroke-dasharray="6 4"/>'
        % (dx(x0), dy(y1), (x1 - x0) * SCALE, (y1 - y0) * SCALE, colour, colour)
    )
    parts.append(
        '<text x="%.1f" y="%.1f" text-anchor="middle" class="s b" fill="%s">%s</text>'
        % (dx((x0 + x1) / 2), dy((y0 + y1) / 2), colour, html.escape(label))
    )

# The antenna keep-out sits under U1, so its label hangs below the board edge.
ax0, ay0, ax1, ay1 = U1_ANTENNA_KEEP_OUT
parts.append(
    '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#B45309" fill-opacity="0.30" stroke="#B45309" stroke-width="1.8" stroke-dasharray="6 4"/>'
    % (dx(ax0), dy(ay1), (ax1 - ax0) * SCALE, (ay1 - ay0) * SCALE)
)
parts.append(
    '<path d="M %.1f %.1f V %.1f" stroke="#B45309" stroke-width="1" stroke-dasharray="3 2"/>'
    % (dx((ax0 + ax1) / 2), dy(ay0), dy(-1.4))
)
parts.append(
    '<text x="%.1f" y="%.1f" text-anchor="middle" class="s b" fill="#B45309">U1 天线禁布区（各层不铺铜）</text>'
    % (dx((ax0 + ax1) / 2), dy(-3.0))
)

# Component bodies.
for comp in cur["components"]:
    ref = comp["ref"]
    cx, cy = comp["x"] / MIL, comp["y"] / MIL
    pts = body(ref, cx, cy)
    if not pts:
        continue
    colour = COLORS[group_of(ref)]
    fill = "#FDE68A" if ref == "J1" else colour
    parts.append('<path d="%s" fill="%s" fill-opacity="0.22" stroke="%s" stroke-width="1.8"/>' % (path(pts), fill, colour))

# Connector keep-out guide beyond the board edge.
parts.append(
    '<path d="M %.1f %.1f H %.1f M %.1f %.1f H %.1f" stroke="#C2542F" stroke-width="1.1" stroke-dasharray="4 3"/>'
    % (dx(84), dy(10.38), dx(88.4), dx(84), dy(21.62), dx(88.4))
)

# Component markers.
for comp in cur["components"]:
    ref = comp["ref"]
    cx, cy = comp["x"] / MIL, comp["y"] / MIL
    colour = COLORS[group_of(ref)]
    r = 4.6 if ref in {"J1", "U1", "J2"} else 3.0
    parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#FFFFFF" stroke-width="1"/>' % (dx(cx), dy(cy), r, colour))
    parts.append('<text x="%.1f" y="%.1f" class="xs">%s</text>' % (dx(cx) + 6, dy(cy) - 5, html.escape(ref)))

# Key spacing dimension, drawn in the empty band east of the key column.
kx = keys["SW1"][0]
dim_x = dx(kx) + 58
if key_pitch:
    parts.append(
        '<path d="M %.1f %.1f H %.1f M %.1f %.1f H %.1f M %.1f %.1f V %.1f" stroke="#D97706" stroke-width="1.2"/>'
        % (
            dim_x, dy(keys["SW1"][1]), dx(kx) + 30,
            dim_x, dy(keys["SW3"][1]), dx(kx) + 30,
            dim_x, dy(keys["SW1"][1]), dy(keys["SW3"][1]),
        )
    )
    label = "键列中心距 %.2f mm" % key_pitch
    if tri:
        label += "；SW2 到 SW1/SW3 %.1f / %.1f mm" % (tri["SW1"], tri["SW3"])
    parts.append(
        '<text x="%.1f" y="%.1f" class="s b" fill="#B45309">%s</text>' % (dim_x + 12, dy((keys["SW1"][1] + keys["SW3"][1]) / 2) + 26, label)
    )

# Coordinate ticks.
for x in range(0, 85, 10):
    parts.append(
        '<path d="M %.1f %.1f V %.1f" stroke="#94A3B8"/><text x="%.1f" y="%.1f" text-anchor="middle" class="xs m">%d</text>'
        % (dx(x), dy(0), dy(0) + 5, dx(x), dy(0) + 16, x)
    )
for y in range(0, 53, 10):
    parts.append(
        '<path d="M %.1f %.1f H %.1f" stroke="#94A3B8"/><text x="%.1f" y="%.1f" text-anchor="end" class="xs m">%d</text>'
        % (dx(0), dy(y), dx(0) - 5, dx(0) - 9, dy(y) + 3, y)
    )

PX = 1010
panel = [
    ("h", "当前方案要点"),
    ("t", "USB：右边缘中部，插口朝 +x，缺口 9.24 × 6.5 mm"),
    ("t", "J1 包络外缘 x=88.4（板外 4.45 mm），信号焊盘 x≈75.95"),
    ("t", "U1 (65.0, 8.0) 转 180°，天线朝下板边"),
    ("t", "板框：84 × 52 的 L 形，左下 33.5 × 15 mm 电池挖空"),
    ("t", "挖空对 30 × 12 电芯留 3.5 × 3 mm 余量"),
    ("t", "NFC 保留区 x 60–82 / y 24–50，双面零铜"),
    ("h", "按键（三颗，方案 B）"),
    ("t", "SW1 (38.1, 3.30)、SW3 (38.1, 15.10) 原位不动"),
    ("t", "新增 SW2 (46.3, 8.80)，到 SW1/SW3 %.1f / %.1f mm" % (tri.get("SW1", 0), tri.get("SW3", 0))),
    ("t", "SW2 上排 1/2 脚接 KEY_NEXT_N，下排 3/4 脚接 GND"),
    ("t", "键列纵向中心距 %.2f mm，本体间隙 %.2f mm" % (key_pitch, key_pitch - 5.2)),
    ("t", "外壳 V7 三个 Ø4.6 孔 + 三个齐平键帽"),
    ("h", "参考数据"),
    ("t", "%d 个位号（2026-09-23 加回第三颗）" % len(refs)),
    ("t", "%d 段铜线 · %d 个过孔 · 两层 GND 覆铜" % (len(cur["lines"]), len(cur["vias"]))),
    ("t", "原生 DRC：普通间距 0、连接 0"),
    ("t", "仅 12 项既有 J1 沉板槽边告警（7.9 mil）"),
]
row = 96
for kind, text in panel:
    if kind == "h":
        row += 12
        parts.append('<text x="%d" y="%d" font-size="15" font-weight="bold">%s</text>' % (PX, row, html.escape(text)))
        row += 22
    else:
        parts.append('<text x="%d" y="%d" class="s">%s</text>' % (PX, row, html.escape(text)))
        row += 21

legend_y = 560
parts.append('<text x="%d" y="%d" font-size="15" font-weight="bold">图例</text>' % (PX, legend_y))
for i, (key, label) in enumerate(LEGEND):
    y = legend_y + 24 + i * 22
    parts.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (PX + 8, y - 4, COLORS[key]))
    parts.append('<text x="%d" y="%d" class="s">%s</text>' % (PX + 20, y, html.escape(label)))

parts.extend(
    [
        '<text x="%.0f" y="%.0f" class="m">E16 right-mid USB · L-shaped outline · three keys (SW1/SW2/SW3) · review only · not a manufacturing export</text>'
        % (dx(0), dy(0) + 62),
        "</svg>",
    ]
)

OUT.write_text("\n".join(parts) + "\n")
print(f"wrote {OUT} from {len(cur['components'])} components, {len(cur['polylines'])} polylines")
