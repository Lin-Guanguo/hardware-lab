"""Render the current E16 right-mid USB board as a review SVG.

Geometry comes from hardware/e16-right-mid-snapshot.json, which is exported
from the live E16 sheet with scripts/eda-export-e16-snapshot.js. The drawing
is a review artifact: board outline, real copper on both layers, vias, pads,
mechanical envelopes, keep-out regions, layer-13 note text and designators.
It is not a manufacturing export.
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
OX, OY = 96.0, 130.0   # top margin leaves room for the board's own layer-13 title
H_MM = 52.0
CANVAS_W, CANVAS_H = 1460, 900

# Layer 12 region objects do not expose their polygon through the bridge, so the
# extents stay hard-coded here and are documented in pcb-e16-usb-right-mid.md.
NFC_KEEP_OUT = (60.0, 24.0, 82.0, 50.0)   # 9d23f6bb076fa2f0
U1_ANTENNA_KEEP_OUT = (59.7, 0.2, 70.3, 2.5)  # d49ece88915402a1

# SW1/SW3 share the x = 38.1 column; SW2 sits east between them.
KEY_REFS = ("SW1", "SW2", "SW3")

TOP_COPPER = "#B4553F"
BOTTOM_COPPER = "#3B6FB6"
VIA_COLOUR = "#C9A227"
PAD_COLOUR = "#E2B84B"

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
    '<text x="36" y="75" class="m">铜箔（红=顶层、蓝=底层）、焊盘、过孔、位号、层 13 说明文字均取自快照；禁布区矩形用文档记录的边界（层 12 多边形不经桥接导出）</text>',
]

# Board outline comes straight from layer 11 of the live snapshot; the layer-14
# rectangle is the superseded 84 x 52 reference box, kept for comparison.
outline = next(polygon_points(p["polygon"]) for p in cur["polylines"] if p["layer"] == 11)
reference = next((polygon_points(p["polygon"]) for p in cur["polylines"] if p["layer"] == 14), None)
if reference:
    parts.append('<path d="%s" fill="none" stroke="#94A3B8" stroke-width="1.4" stroke-dasharray="6 4"/>' % path(reference))
    parts.append('<text x="%.0f" y="%.0f" class="xs m">灰色虚线 = 84 × 52 参考板框（当前板框是 L 形）</text>' % (dx(0) + 4, dy(0) + 44))
parts.append('<path d="%s" fill="#EEF2F7" stroke="#334155" stroke-width="2.4"/>' % path(outline))

# Real copper from the snapshot, bottom layer first so top traces stay readable.
for layer, colour in ((2, BOTTOM_COPPER), (1, TOP_COPPER)):
    parts.append('<g stroke="%s" fill="none" stroke-linecap="round" stroke-linejoin="round">' % colour)
    for line in cur["lines"]:
        if line["layer"] != layer:
            continue
        parts.append(
            '<path d="M %.1f %.1f L %.1f %.1f" stroke-width="%.2f"/>'
            % (
                dx(line["x1"] / MIL), dy(line["y1"] / MIL),
                dx(line["x2"] / MIL), dy(line["y2"] / MIL),
                max(1.1, line["widthMil"] / MIL * SCALE),
            )
        )
    parts.append("</g>")

# Pads and vias: real shapes and diameters from the snapshot.
pad_shapes = []
for pad in cur["pads"]:
    raw = pad.get("pad") or []
    shape = raw[0] if raw else "RECT"
    w = float(raw[1]) if len(raw) > 1 and isinstance(raw[1], (int, float)) else 6.0
    h = float(raw[2]) if len(raw) > 2 and isinstance(raw[2], (int, float)) else w
    # Pad extents are stored in the footprint's local frame.
    if abs(pad.get("rotation", 0)) % 180 == 90:
        w, h = h, w
    x, y = dx(pad["x"] / MIL), dy(pad["y"] / MIL)
    pw, ph = w / MIL * SCALE, h / MIL * SCALE
    if shape == "ELLIPSE":
        pad_shapes.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f"/>' % (x, y, pw / 2, ph / 2))
    else:
        pad_shapes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1"/>' % (x - pw / 2, y - ph / 2, pw, ph))
parts.append('<g fill="%s" fill-opacity="0.95" stroke="#8A6D14" stroke-width="0.4">%s</g>' % (PAD_COLOUR, "".join(pad_shapes)))
parts.append(
    '<g fill="%s" stroke="#6E5A12" stroke-width="0.6">%s</g>'
    % (VIA_COLOUR, "".join(
        '<circle cx="%.1f" cy="%.1f" r="%.1f"/>' % (dx(v["x"] / MIL), dy(v["y"] / MIL), max(1.7, v["diameterMil"] / MIL * SCALE / 2))
        for v in cur["vias"]
    ))
)

# Mechanical review envelopes (layer 9).
ENVELOPES = [
    (lambda x0, w: abs(x0 - 3) < 0.3 and abs(w - 30) < 0.5, "301230 电池 · 30×12", "#64748B"),
    (lambda x0, w: abs(x0 - 2) < 0.3 and abs(w - 37.42) < 0.5, "SCREEN / FPC · 37.42×31.9", "#0F766E"),
    (lambda x0, w: abs(x0 - 60) < 0.3 and abs(w - 22) < 0.5, "", "#16806B"),
    (lambda x0, w: abs(x0 - 47.5) < 0.3, "J2 FPC · 弯折/支撑待定", "#0F766E"),
    (lambda x0, w: abs(x0 - 59.75) < 0.3, "", "#B45309"),
    (lambda x0, w: abs(x0 - 35.5) < 0.3, "", "#D97706"),
]
for poly in [p for p in cur["polylines"] if p["layer"] == 9]:
    pts = polygon_points(poly["polygon"])
    x0, y0, x1, y1 = bbox(pts)
    w, h = x1 - x0, y1 - y0
    label, colour = "", "#64748B"
    for match, name, name_colour in ENVELOPES:
        if match(x0, w):
            label, colour = name, name_colour
            break
    parts.append(
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.08" stroke="%s" stroke-width="1.1" stroke-dasharray="3 3"/>'
        % (dx(x0), dy(y1), w * SCALE, h * SCALE, colour, colour)
    )
    if label:
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" class="xs" fill="%s">%s</text>'
            % (dx((x0 + x1) / 2), dy((y0 + y1) / 2), colour, html.escape(label))
        )

# Keep-out regions. Layer-12 polygons are not exposed through the bridge, so the
# two extents below are the documented values from pcb-e16-usb-right-mid.md.
x0, y0, x1, y1 = NFC_KEEP_OUT
parts.append(
    '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#16806B" fill-opacity="0.16" stroke="#16806B" stroke-width="1.8" stroke-dasharray="6 4"/>'
    % (dx(x0), dy(y1), (x1 - x0) * SCALE, (y1 - y0) * SCALE)
)
parts.append(
    '<text x="%.1f" y="%.1f" text-anchor="middle" class="s b" fill="#0E6B57">NFC 保留区（禁布，双面零铜）</text>'
    % (dx((x0 + x1) / 2), dy((y0 + y1) / 2))
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

# Bodies only for the parts whose outline carries meaning at this scale; every
# other part is already represented by its real pads and its designator.
for comp in cur["components"]:
    ref = comp["ref"]
    cx, cy = comp["x"] / MIL, comp["y"] / MIL
    pts = body(ref, cx, cy)
    if not pts:
        continue
    colour = COLORS[group_of(ref)]
    fill = "#FDE68A" if ref == "J1" else colour
    parts.append('<path d="%s" fill="none" fill-opacity="0.18" stroke="%s" stroke-width="1.6"/>' % (path(pts), colour))

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
    r = 3.4 if ref in {"J1", "U1", "J2"} else 2.2
    parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#FFFFFF" stroke-width="0.8"/>' % (dx(cx), dy(cy), r, colour))
    parts.append(
        '<text x="%.1f" y="%.1f" class="xs b" fill="#12233A" stroke="#FFFFFF" stroke-width="2.4" paint-order="stroke">%s</text>'
        % (dx(cx) + 5, dy(cy) - 4, html.escape(ref))
    )

# Layer-13 note text, drawn where the board itself carries it.
for note in [s for s in cur["strings"] if s["layer"] == 13]:
    parts.append(
        '<text x="%.1f" y="%.1f" font-size="%.1f" fill="#64748B" stroke="#FFFFFF" stroke-width="2.6" paint-order="stroke">%s</text>'
        % (dx(note["x"] / MIL), dy(note["y"] / MIL), note["fontSize"] / MIL * SCALE * 0.72, html.escape(note["text"]))
    )

# Key spacing dimension, drawn in the empty band west of the key column (the
# battery cut-out), with a short label so it clears the layer-13 note text.
kx = keys["SW1"][0]
dim_x = dx(31.5)
if key_pitch:
    parts.append(
        '<path d="M %.1f %.1f H %.1f M %.1f %.1f H %.1f M %.1f %.1f V %.1f" stroke="#D97706" stroke-width="1.2"/>'
        % (
            dim_x, dy(keys["SW1"][1]), dx(kx) - 4,
            dim_x, dy(keys["SW3"][1]), dx(kx) - 4,
            dim_x, dy(keys["SW1"][1]), dy(keys["SW3"][1]),
        )
    )
    parts.append(
        '<text x="%.1f" y="%.1f" text-anchor="end" class="s b" fill="#B45309">%.2f mm</text>'
        % (dim_x - 4, dy((keys["SW1"][1] + keys["SW3"][1]) / 2) + 4, key_pitch)
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
    ("h", "当前方案要点（2026-09-23）"),
    ("t", "板框：84 × 52 的 L 形，左下 33.5 × 15 mm 电池挖空"),
    ("t", "USB：右边缘中部，插口朝 +x，缺口 9.24 × 7.30 mm"),
    ("t", "缺口内缘 x=76.704，与 J1 封装的板边线一致"),
    ("t", "J1 接插面在板边内侧 0.8 mm，连接器不外伸，整机 84 mm"),
    ("t", "U1 (65.0, 8.0) 转 180°，天线朝下板边"),
    ("t", "电池挖空内可用电芯 ≤32.5 × 14 × 3.4 mm（净高 3.6）"),
    ("t", "NFC 保留区 x 60–82 / y 24–50，双面零铜"),
    ("t", "线圈可用区 17 × 21 mm，天线形式待 PN532 桌面实验"),
    ("h", "按键（三颗，三角排布）"),
    ("t", "SW1 (%.2f, %.2f)、SW3 (%.2f, %.2f) 同列" % (keys["SW1"][0], keys["SW1"][1], keys["SW3"][0], keys["SW3"][1])),
    ("t", "SW2 (%.2f, %.2f)，到 SW1/SW3 %.1f / %.1f mm" % (keys["SW2"][0], keys["SW2"][1], tri.get("SW1", 0), tri.get("SW3", 0))),
    ("t", "键列纵向中心距 %.2f mm，本体间隙 %.2f mm" % (key_pitch, key_pitch - 5.2)),
    ("t", "SW2 上排接 KEY_NEXT_N，下排接 GND；外壳 V7 三个 Ø4.6 孔"),
    ("h", "NFC 天线馈线（2026-09-23 落铜）"),
    ("t", "U1 pin 52 / 54 → 底层两个 1.5 mm 方形落点焊盘"),
    ("t", "6 个 0.30 / 0.20 mm 过孔，0.15 mm 线宽，两条并排走线"),
    ("t", "离线逐点核验：0 处间隙违规、孔到孔 ≥0.80 mm"),
    ("t", "线圈形式与匹配网络待 PN532 桌面实验（落点已就位）"),
    ("h", "板面数据（本图快照）"),
    ("t", "%d 个位号 · %d 个焊盘 · %d 段铜线" % (len(refs), len(cur["pads"]), len(cur["lines"]))),
    ("t", "%d 个过孔 · 2 块 GND 覆铜（顶/底）" % len(cur["vias"])),
    ("t", "原生 DRC（馈线落铜后复跑）：24 项固有 J1 槽边告警"),
    ("t", "间距 / 连接 / 孔到孔 / 覆铜间隙 全部 0"),
    ("t", "12 个焊盘离板边 0.2007 mm，板厂允许 ≥0.2 mm"),
    ("t", "制造包重导 ok：17 个 Gerber 成员 · 168 孔 · 56 位号"),
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

legend_y = 700
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
