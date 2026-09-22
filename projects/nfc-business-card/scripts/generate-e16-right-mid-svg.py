"""Render the applied E16 right-mid USB layout as a review SVG.

Current geometry comes from the live E16 snapshot exported through the EasyEDA
bridge; the E15 snapshot supplies the "before" positions. The drawing is a
review artifact: it shows board outline, mechanical envelopes, component bodies
and real pad-derived markers, not a manufacturing export.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HW = ROOT / "projects/nfc-business-card/hardware"
CURRENT = HW / "e16-right-mid-snapshot.json"
BEFORE = HW / "e15-clean-layout.json"
OUT = ROOT / "projects/nfc-business-card/enclosure/pcba-e16-right-mid.svg"

MIL = 39.37007874015748
SCALE = 10.0
OX, OY = 96.0, 96.0
W_MM, H_MM = 84.0, 52.0
CANVAS_W, CANVAS_H = 1460, 900

cur = json.loads(CURRENT.read_text())
old = json.loads(BEFORE.read_text())
old_pos = {c["ref"]: (c["x"] / MIL, c["y"] / MIL) for c in old["components"]}
old_outline = [(0, 0), (0, 52), (84, 52), (84, 0), (56, 0), (56, 6.5), (43, 6.5), (43, 0)]

GROUP = {}
for ref in ["J1", "U5", "U6", "R1", "R2", "R3", "R4"]:
    GROUP[ref] = "USB/ESD"
GROUP["U1"] = "MCU"
for ref in ["J2", "U4", "C9", "C10", "R13", "L1", "Q1", "R14", "R15", "D1", "D2", "D3", "C11", "C12", "C13", "R16", "R17", "R18"]:
    GROUP[ref] = "EPD/FPC"
COLORS = {"USB/ESD": "#C2542F", "MCU": "#1D4ED8", "EPD/FPC": "#0F766E", "Power": "#A855F7", "Buttons": "#D97706", "Other": "#64748B"}
LEGEND = [("USB/ESD", "USB / ESD / CC"), ("Power", "充电与去耦"), ("EPD/FPC", "屏幕 FPC / EPD 电源"), ("MCU", "U1 主控（天线朝下）"), ("Buttons", "三键")]


def group_of(ref: str) -> str:
    if ref not in GROUP:
        GROUP[ref] = "Buttons" if ref.startswith("SW") else "Power"
    return GROUP[ref]


def dx(x: float) -> float:
    return OX + x * SCALE


def dy(y: float) -> float:
    return OY + (H_MM - y) * SCALE


def path(points) -> str:
    return " ".join(("%s %.1f %.1f" % ("M" if i == 0 else "L", dx(px), dy(py))) for i, (px, py) in enumerate(points)) + " Z"


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
        # shell straddles the right board edge, opens toward +x
        return [(cx - 2.10, cy - 5.62), (cx + 4.45, cy - 5.62), (cx + 4.45, cy + 5.62), (cx - 2.10, cy + 5.62)]
    return None


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (CANVAS_W, CANVAS_H, CANVAS_W, CANVAS_H),
    '<rect width="%d" height="%d" fill="#F7F9FC"/>' % (CANVAS_W, CANVAS_H),
    '<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}.t{font-size:13px}.s{font-size:11.5px}.m{fill:#52657B}.xs{font-size:9.5px}.b{font-weight:bold}</style>',
    '<text x="36" y="34" font-size="25" font-weight="bold">E16 · 右侧中部 USB + 三键重排（已落盘）</text>',
    '<text x="36" y="57" class="m">来源：通过 EDA 桥接导出的 E16 实时快照；虚线为 E15 原位置。1 mm = 10 px，Y 轴向上为板面正视</text>',
]

# comparison outlines
parts.append('<path d="%s" fill="none" stroke="#94A3B8" stroke-width="1.6" stroke-dasharray="6 4"/>' % path(old_outline))
current_outline = [(0, 0), (0, 52), (84, 52), (84, 20.62), (77.5, 20.62), (77.5, 11.38), (84, 11.38), (84, 0)]
parts.append('<path d="%s" fill="#E8EDF3" stroke="#334155" stroke-width="2.4"/>' % path(current_outline))
parts.append('<text x="%.0f" y="%.0f" class="xs m">浅灰虚线 = E15 原板框（底边 USB 缺口）</text>' % (dx(0), dy(52) - 8))

# mechanical review envelopes (layer 9)
for poly in [p for p in cur["polylines"] if p["layer"] == 9]:
    pts = polygon_points(poly["polygon"])
    x0, y0, x1, y1 = bbox(pts)
    w, h = x1 - x0, y1 - y0
    if abs(x0 - 3) < 0.3 and abs(w - 30) < 0.5:
        label, colour = "301230 电池 · 30×12", "#64748B"
    elif abs(x0 - 2) < 0.3 and abs(w - 37.42) < 0.5:
        label, colour = "SCREEN / FPC · 37.42×31.9", "#0F766E"
    elif abs(x0 - 60) < 0.3 and abs(w - 22) < 0.5:
        label, colour = "NFC RESERVE · 22×26", "#16806B"
    elif abs(x0 - 47.5) < 0.3:
        label, colour = "J2 FPC · 弯折/支撑待定", "#0F766E"
    elif abs(x0 - 59.75) < 0.3:
        label, colour = "", "#B45309"
    elif abs(x0 - 35.5) < 0.3:
        label, colour = "", "#D97706"
    else:
        label, colour = "", "#64748B"
    parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.10" stroke="%s" stroke-width="1.1" stroke-dasharray="3 3"/>'
                 % (dx(x0), dy(y1), w * SCALE, h * SCALE, colour, colour))
    if label:
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="xs" fill="%s">%s</text>'
                     % (dx((x0 + x1) / 2), dy((y0 + y1) / 2), colour, html.escape(label)))

# NFC keep-out region (the live region object does not expose its polygon)
NFC_KEEP_OUT = (60.0, 24.0, 82.0, 50.0)
nx0, ny0, nx1, ny1 = NFC_KEEP_OUT
parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#B8E0D7" fill-opacity="0.35" stroke="#16806B" stroke-width="1.6" stroke-dasharray="6 4"/>'
             % (dx(nx0), dy(ny1), (nx1 - nx0) * SCALE, (ny1 - ny0) * SCALE))
parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="t b" fill="#0F6B59">NFC 保留区（禁布）</text>'
             % (dx((nx0 + nx1) / 2), dy((ny0 + ny1) / 2)))

# component bodies
for comp in cur["components"]:
    ref = comp["ref"]
    cx, cy = comp["x"] / MIL, comp["y"] / MIL
    pts = body(ref, cx, cy)
    if not pts:
        continue
    colour = COLORS[group_of(ref)]
    fill = "#FDE68A" if ref == "J1" else colour
    parts.append('<path d="%s" fill="%s" fill-opacity="0.22" stroke="%s" stroke-width="1.8"/>' % (path(pts), fill, colour))

# connector overhang guide beyond the board edge
parts.append('<path d="M %.1f %.1f H %.1f M %.1f %.1f H %.1f" stroke="#C2542F" stroke-width="1.1" stroke-dasharray="4 3"/>'
             % (dx(84), dy(10.38), dx(88.4), dx(84), dy(21.62), dx(88.4)))
parts.append('<text x="%.1f" y="%.1f" class="xs" fill="#C2542F">板外 4.45 mm</text>' % (dx(84.3), dy(24.0)))
parts.append('<path d="M %.1f %.1f V %.1f" stroke="#B45309" stroke-width="1" stroke-dasharray="3 2"/>' % (dx(65.0), dy(0.25), dy(-1.6)))
parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="s b" fill="#B45309">U1 天线净空（各层不铺地）</text>' % (dx(65.0), dy(-3.0)))

# component markers: current + ghost of the old position
moved_refs = {"J1", "U1", "C5", "C6", "C7", "U5", "U6", "R1", "R2", "C1", "C3", "SW1", "SW2", "SW3", "C8"}
for comp in cur["components"]:
    ref = comp["ref"]
    cx, cy = comp["x"] / MIL, comp["y"] / MIL
    colour = COLORS[group_of(ref)]
    r = 4.6 if ref in {"J1", "U1", "J2"} else 3.0
    parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#FFFFFF" stroke-width="1"/>' % (dx(cx), dy(cy), r, colour))
    if ref in moved_refs and ref in old_pos:
        ox, oy = old_pos[ref]
        parts.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2 2"/>' % (dx(ox), dy(oy)))
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#CBD5E1" stroke-width="1" stroke-dasharray="3 3"/>'
                     % (dx(ox), dy(oy), dx(cx), dy(cy)))
    parts.append('<text x="%.1f" y="%.1f" class="xs">%s</text>' % (dx(cx) + 6, dy(cy) - 5, html.escape(ref)))

# coordinate ticks
for x in range(0, 85, 10):
    parts.append('<path d="M %.1f %.1f V %.1f" stroke="#94A3B8"/><text x="%.1f" y="%.1f" text-anchor="middle" class="xs m">%d</text>'
                 % (dx(x), dy(0), dy(0) + 5, dx(x), dy(0) + 16, x))
for y in range(0, 53, 10):
    parts.append('<path d="M %.1f %.1f H %.1f" stroke="#94A3B8"/><text x="%.1f" y="%.1f" text-anchor="end" class="xs m">%d</text>'
                 % (dx(0), dy(y), dx(0) - 5, dx(0) - 9, dy(y) + 3, y))

PX = 1010
panel = [
    ("h", "方案要点"),
    ("t", "USB：右边缘中部，插口朝 +x"),
    ("t", "缺口 9.24 × 6.5 mm（对齐 GCT 焊接区宽度）"),
    ("t", "J1 (78.5, 16.0)，信号焊盘在 x≈75.95"),
    ("t", "U1 (65.0, 8.0) 转 180°，天线朝下板边"),
    ("t", "天线净空 x 59.75–70.25, y 0.25–2.55"),
    ("t", "USB ESD / CC / VBUS 群集中到 J1 左侧"),
    ("h", "三键与显示"),
    ("t", "三键 x=38.1，等距 5.90 mm，间隙 0.70 mm"),
    ("t", "距下板边 0.70 mm；整列避开屏幕包络"),
    ("t", "屏幕包络上移 1.30 mm 到 y 18.3–50.2"),
    ("t", "C8 由 (33.0, 17.8) 移到 (42.0, 20.5)"),
    ("h", "原生 DRC 对照"),
    ("t", "E15 基线 220 → 现在 213"),
    ("t", "普通间距 8 → 1（剩余为既有测试点冲突）"),
    ("t", "同封装 12 项不变（槽边 0.20 mm 名义值）"),
    ("t", "锚脚落入缺口的问题已消除，无新增错误"),
    ("h", "下一步"),
    ("t", "1. USB CC → DP/DM → VBUS → GND 布线"),
    ("t", "2. 连接器三维复核外壳与缺口法兰"),
    ("t", "3. 外壳右壁开孔 + NFC 馈线规划"),
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

legend_y = 96 + 500
parts.append('<text x="%d" y="%d" font-size="15" font-weight="bold">图例</text>' % (PX, legend_y))
for i, (key, label) in enumerate(LEGEND):
    y = legend_y + 24 + i * 22
    parts.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (PX + 8, y - 4, COLORS[key]))
    parts.append('<text x="%d" y="%d" class="s">%s</text>' % (PX + 20, y, html.escape(label)))
parts.append('<circle cx="%d" cy="%d" r="2.6" fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2 2"/>' % (PX + 8, legend_y + 146))
parts.append('<text x="%d" y="%d" class="s">虚线空圈 = 移动前位置</text>' % (PX + 20, legend_y + 150))

parts.extend([
    '<text x="%.0f" y="%.0f" class="m">E16 right-mid USB + three-key respacing · applied to the E16 sheet · review only · not a manufacturing export</text>' % (dx(0), dy(0) + 62),
    '</svg>',
])

OUT.write_text("\n".join(parts) + "\n")
print("wrote", OUT)
