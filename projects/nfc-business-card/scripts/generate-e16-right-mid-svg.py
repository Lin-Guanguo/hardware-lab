"""Render the E16 right-mid USB layout plan as a review SVG.

Positions come from the saved E15 snapshot plus the checked plan JSON, so the
drawing shows real pad coordinates for the moved parts. This is a review
artifact, not a manufacturing export.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HW = ROOT / "projects/nfc-business-card/hardware"
SNAPSHOT = HW / "e15-clean-layout.json"
PINS = HW / "e14-eda-components-pins.json"
PLAN = HW / "e16-right-mid-plan.json"
OUT = ROOT / "projects/nfc-business-card/enclosure/pcba-e16-right-mid.svg"

MIL = 39.37007874015748
SCALE = 10.0
OX, OY = 90.0, 72.0
OUTER_W, OUTER_H = 84.0, 52.0

NEW_OUTLINE = [(0, 0), (0, 52), (84, 52), (84, 20.62), (77.5, 20.62), (77.5, 11.38), (84, 11.38), (84, 0)]
OLD_OUTLINE = [(0, 0), (0, 52), (84, 52), (84, 0), (56, 0), (56, 6.5), (43, 6.5), (43, 0)]

snapshot = json.loads(SNAPSHOT.read_text())
pins = {entry["ref"]: entry for entry in json.loads(PINS.read_text())}
plan = json.loads(PLAN.read_text())
moved = plan["moved_components"]


def polygon_points(raw):
    """Parse EasyEDA polygon data: [x, y, 'L', x, y, ...]."""
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


def dx(x: float) -> float:
    return OX + x * SCALE


def dy(y: float) -> float:
    return OY + (OUTER_H - y) * SCALE


def path(points) -> str:
    return " ".join(("%s %.1f %.1f" % ("M" if i == 0 else "L", dx(px), dy(py))) for i, (px, py) in enumerate(points)) + " Z"


def rotate(ax, ay, deg):
    r = math.radians(deg)
    return (ax * math.cos(r) - ay * math.sin(r), ax * math.sin(r) + ay * math.cos(r))


def world_pads(ref: str):
    src = pins[ref]
    if ref in moved:
        x_mm, y_mm, rot_new = moved[ref]["x_mm"], moved[ref]["y_mm"], moved[ref]["rotation_deg"]
        rot_old = src.get("rotation", 0) or 0
        out = []
        for pin in src["pins"]:
            ox = (pin["x"] - src["x"]) / MIL
            oy = (pin["y"] - src["y"]) / MIL
            lx, ly = rotate(ox, oy, -rot_old)
            px, py = rotate(lx, ly, rot_new)
            out.append((x_mm + px, y_mm + py, pin["n"], pin.get("net")))
        return out
    return [((pin["x"]) / MIL, (pin["y"]) / MIL, pin["n"], pin.get("net")) for pin in src["pins"]]


def centre(ref: str):
    if ref in moved:
        return moved[ref]["x_mm"], moved[ref]["y_mm"]
    for comp in snapshot["components"]:
        if comp["ref"] == ref:
            return comp["x"] / MIL, comp["y"] / MIL
    raise KeyError(ref)


def rect_points(cx, cy, w, l, rot):
    corners = [(-w / 2, -l / 2), (w / 2, -l / 2), (w / 2, l / 2), (-w / 2, l / 2)]
    pts = [rotate(ax, ay, rot) for ax, ay in corners]
    return [(cx + px, cy + py) for px, py in pts]


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1420" height="860" viewBox="0 0 1420 860">',
    '<rect width="1420" height="860" fill="#F7F9FC"/>',
    '<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}.small{font-size:12px}.muted{fill:#52657B}.tiny{font-size:9px}</style>',
    '<text x="36" y="32" font-size="24" font-weight="bold">E16 · USB 右侧中部布局（已落盘）</text>',
    '<text x="36" y="53" class="muted">来源：E15 保存快照 + 已校验的布局方案；1 mm = 10 px，Y 轴向上为板面正视</text>',
    '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="7 5"/>' % (dx(0), dy(52), OUTER_W * SCALE, OUTER_H * SCALE),
    '<path d="%s" fill="none" stroke="#94A3B8" stroke-width="1.6" stroke-dasharray="6 4"/>' % path(OLD_OUTLINE),
    '<path d="%s" fill="#E5EAF0" stroke="#334155" stroke-width="2.4"/>' % path(NEW_OUTLINE),
]

# Mechanical zones from the saved snapshot (battery, screen, NFC, J2, keys).
labels = ["301230 电池 · 30×12", "SCREEN / FPC", "NFC RESERVE · 22×26", "J2 FPC", "SW1", "SW2", "SW3", "U1 旧位置（E15）"]
mech = [p for p in snapshot["polylines"] if p["layer"] == 9]
for poly, label in zip(mech, labels):
    pts = polygon_points(poly["polygon"])
    xs = [pt[0] for pt in pts]
    ys = [pt[1] for pt in pts]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    dash = "6 4" if label.startswith("NFC") else "3 3"
    colour = "#16806B" if label.startswith("NFC") else "#64748B"
    parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.12" stroke="%s" stroke-width="1" stroke-dasharray="%s"/>'
                 % (dx(x0), dy(y1), (x1 - x0) * SCALE, (y1 - y0) * SCALE, colour, colour, dash))
    parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="tiny" fill="%s">%s</text>'
                 % (dx((x0 + x1) / 2), dy((y0 + y1) / 2), colour, html.escape(label)))

for region in snapshot["regions"]:
    pts = polygon_points(region["polygon"])
    xs = [pt[0] for pt in pts]
    ys = [pt[1] for pt in pts]
    parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#B8E0D7" fill-opacity="0.35" stroke="#16806B" stroke-width="1.6" stroke-dasharray="6 4"/>'
                 % (dx(min(xs)), dy(max(ys)), (max(xs) - min(xs)) * SCALE, (max(ys) - min(ys)) * SCALE))

# U1 module body and antenna keep-out.
u1x, u1y = centre("U1")
u1rot = moved["U1"]["rotation_deg"]
parts.append('<path d="%s" fill="#356AA0" fill-opacity="0.20" stroke="#356AA0" stroke-width="2"/>' % path(rect_points(u1x, u1y, 10.5, 15.5, u1rot)))
ax0, ay0, ax1, ay1 = plan["antenna_keepout_mm"]
parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#E08B4A" fill-opacity="0.30" stroke="#B45309" stroke-width="1.6" stroke-dasharray="5 3"/>'
             % (dx(ax0), dy(ay1), (ax1 - ax0) * SCALE, (ay1 - ay0) * SCALE))
parts.append('<path d="M %.1f %.1f V %.1f" stroke="#B45309" stroke-width="1" stroke-dasharray="3 2"/>' % (dx((ax0 + ax1) / 2), dy(ay1), dy(-1.4)))
parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="11" font-weight="bold" fill="#8A4B08">U1 天线净空（各层不铺地）</text>'
             % (dx((ax0 + ax1) / 2), dy(-2.6)))

# J1 shell and pads.
j1x, j1y = centre("J1")
j1rot = moved["J1"]["rotation_deg"]
shell = [(j1x + px, j1y + py) for px, py in [rotate(ax, ay, j1rot) for ax, ay in [(-5.62, -4.45), (5.62, -4.45), (5.62, 2.10), (-5.62, 2.10)]]]
parts.append('<path d="%s" fill="#C47F67" fill-opacity="0.30" stroke="#A2543C" stroke-width="2"/>' % path(shell))
parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="12" font-weight="bold" fill="#8A3B22">J1 USB-C · 插口朝右</text>' % (dx(80.0), dy(7.8)))
for px, py, num, net in world_pads("J1"):
    parts.append('<circle cx="%.1f" cy="%.1f" r="2.1" fill="#A2543C"/>' % (dx(px), dy(py)))

parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#1D4ED8" stroke-width="1.4" stroke-dasharray="5 3"/>'
             % (dx(69.6), dy(22.2), 7.6 * SCALE, 10.4 * SCALE))
parts.append('<text x="%.1f" y="%.1f" class="small" font-weight="bold" fill="#1D4ED8">USB ESD / CC / VBUS 群</text>' % (dx(69.9), dy(22.8)))

# Antenna keep-out of the connector overhang: the shell continues past the board edge.
parts.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#A2543C" stroke-width="1.2" stroke-dasharray="4 3"/>'
             % (dx(78.5), dy(9.5), dx(88.4), dy(9.5)))
parts.append('<path d="M %.1f %.1f L %.1f %.1f" stroke="#A2543C" stroke-width="1.2" stroke-dasharray="4 3"/>'
             % (dx(78.5), dy(22.5), dx(88.4), dy(22.5)))
parts.append('<text x="%.1f" y="%.1f" class="tiny" fill="#8A3B22">本体外伸约 4.45 mm</text>' % (dx(80.2), dy(19.2)))

# All components: moved ones highlighted, the rest muted.
for comp in snapshot["components"]:
    ref = comp["ref"]
    x_mm, y_mm = centre(ref)
    was = (comp["x"] / MIL, comp["y"] / MIL)
    if ref in moved:
        parts.append('<circle cx="%.1f" cy="%.1f" r="4.0" fill="#1D4ED8" stroke="#FFFFFF" stroke-width="1"/>' % (dx(x_mm), dy(y_mm)))
        parts.append('<circle cx="%.1f" cy="%.1f" r="3.0" fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2 2"/>' % (dx(was[0]), dy(was[1])))
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3 3"/>'
                     % (dx(was[0]), dy(was[1]), dx(x_mm), dy(y_mm)))
        if ref in ("U1", "J1"):
            parts.append('<text x="%.1f" y="%.1f" class="tiny" font-weight="bold">%s</text>' % (dx(x_mm) + 6, dy(y_mm) - 5, html.escape(ref)))
    else:
        parts.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="#94A3B8"/>' % (dx(x_mm), dy(y_mm)))
        parts.append('<text x="%.1f" y="%.1f" class="tiny" fill="#64748B">%s</text>' % (dx(x_mm) + 4, dy(y_mm) - 3, html.escape(ref)))

for x in range(0, 85, 10):
    parts.append('<path d="M %.1f %.1f V %.1f" stroke="#64748B"/><text x="%.1f" y="%.1f" text-anchor="middle" class="tiny">%d</text>'
                 % (dx(x), dy(0) - 5, dy(0), dx(x), dy(0) - 10, x))
for y in range(0, 53, 10):
    parts.append('<path d="M %.1f %.1f H %.1f" stroke="#64748B"/><text x="%.1f" y="%.1f" text-anchor="end" class="tiny">%d</text>'
                 % (dx(0) - 5, dy(y), dx(0), dx(0) - 10, dy(y) + 3, y))

parts.extend([
    '<text x="90" y="652" class="muted">浅灰虚线 = E15 原 84×52 板框（底边 USB 缺口）；深色实线 = 右侧中部 USB 新板框</text>',
    '<text x="90" y="672" class="muted">蓝色实心 = 本次移动的元件，灰色小圆 = 保留原位；灰色虚圈 = 移动前位置</text>',
    '<text x="982" y="90" font-size="17" font-weight="bold">方案要点</text>',
    '<text x="982" y="116" class="small">USB：右边缘中部，插口朝 +x</text>',
    '<text x="982" y="138" class="small">缺口：9.24 × 6.5 mm，内缘距连接器原点 1.025 mm</text>',
    '<text x="982" y="160" class="small">U1：下移并转 180°，天线朝下板边</text>',
    '<text x="982" y="182" class="small">天线净空：x 59.75–70.25, y 0.25–2.55 mm</text>',
    '<text x="982" y="204" class="small">USB ESD / CC / VBUS 群集中到 J1 左侧</text>',
    '<text x="982" y="226" class="small">去耦 C5–C7 跟随 U1 电源脚</text>',
    '<text x="982" y="262" font-size="15" font-weight="bold">离线校验</text>',
    '<text x="982" y="288" class="small">新增几何冲突：0</text>',
    '<text x="982" y="310" class="small">沿用项：J2 与 C16/C17 贴近（原布局已有）</text>',
    '<text x="982" y="332" class="small">顺带解决：R1 原来压在底边缺口上</text>',
    '<text x="982" y="354" class="small">连接器前锚脚仍落在缺口内（两版一致）</text>',
    '<text x="982" y="376" class="small">已在 E16 落盘并通过关闭重开验证</text>',
    '<text x="982" y="700" class="small" font-weight="bold" fill="#1D4ED8">原生 DRC：220 → 213，间距 8 → 1，无新增</text>',
    '<text x="982" y="412" font-size="15" font-weight="bold">移动清单（原 → 新，mm）</text>',
    '<text x="982" y="438" class="small">J1  (49.5, 5.5) → (78.5, 16.0)，转 90°</text>',
    '<text x="982" y="460" class="small">U1  (76.2, 12.7) → (65.0, 8.0)，转 180°</text>',
    '<text x="982" y="482" class="small">C5/C6/C7 → (61.0 / 63.4 / 65.8, 17.2)</text>',
    '<text x="982" y="504" class="small">U5/U6 → (73.6, 16.6) / (73.6, 14.9)</text>',
    '<text x="982" y="526" class="small">R1/R2 → (71.9, 14.75) / (71.9, 17.75)</text>',
    '<text x="982" y="548" class="small">C1/C3 → (73.6, 12.6) / (71.9, 20.6)</text>',
    '<text x="982" y="584" font-size="15" font-weight="bold">下一步</text>',
    '<text x="982" y="610" class="small">1. 已在 E16 落盘，关闭重开保持</text>',
    '<text x="982" y="632" class="small">2. 间距 8 → 1，锚脚冲突清零</text>',
    '<text x="982" y="654" class="small">3. 下一步：按 CC → DP/DM → VBUS → GND 布线</text>',
    '<text x="982" y="676" class="small">4. 再同步外壳开孔与外伸包络</text>',
    '<text x="90" y="712" class="muted">E16 right-mid USB · applied to the E16 sheet · review only · not a manufacturing export</text>',
    '</svg>',
])

OUT.write_text("\n".join(parts) + "\n")
print("wrote", OUT)
