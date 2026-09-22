"""Render the cleaned E15 EasyEDA PCB candidate as a review SVG.

The source is a saved EasyEDA snapshot, so every board/mechanical primitive
and component marker is rendered from the actual EDA coordinates.  This is a
layout review artifact; the board has no copper routing yet and is not a
vendor manufacturing export.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "projects/nfc-business-card/hardware/e15-clean-layout.json"
OUT = ROOT / "projects/nfc-business-card/enclosure/pcba-e15-clean-layout.svg"
MIL_PER_MM = 39.37007874015748
OUTER_W, OUTER_H = 84.0, 52.0
SCALE = 10.0
OX, OY = 90.0, 72.0

data = json.loads(SNAPSHOT.read_text())
components = data["components"]
polylines = data["polylines"]
regions = data["regions"]
strings = data["strings"]


def mm(value: float) -> float:
    return float(value) / MIL_PER_MM


def display_y(y: float, height: float = 0.0) -> float:
    # EasyEDA's saved Y=0 edge is the lower edge in the top-view canvas.
    return OUTER_H - y - height


def polygon_points(raw: list) -> list[tuple[float, float]]:
    """Parse EasyEDA polygon data: [x, y, 'L', x, y, ...]."""
    nums = raw["polygon"] if isinstance(raw, dict) else raw
    points: list[tuple[float, float]] = []
    i = 0
    while i + 1 < len(nums):
        if isinstance(nums[i], str):
            i += 1
            continue
        if isinstance(nums[i + 1], str):
            i += 1
            continue
        points.append((mm(nums[i]), mm(nums[i + 1])))
        i += 2
    return points


def path_d(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    commands = []
    for i, (x, y) in enumerate(points):
        commands.append(f"{'M' if i == 0 else 'L'} {OX + x*SCALE:.1f} {OY + display_y(y)*SCALE:.1f}")
    return " ".join(commands) + " Z"


def rect_from_points(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


outline = next(polygon_points(p["polygon"]) for p in polylines if p["layer"] == 11)
reference = next(polygon_points(p["polygon"]) for p in polylines if p["layer"] == 14)
mechanical = [polygon_points(p["polygon"]) for p in polylines if p["layer"] == 9]
keepouts = [polygon_points(r["polygon"]) for r in regions]

if len(outline) != 9:
    raise ValueError(f"unexpected E15 Layer 11 point count: {len(outline)}")
if round(max(x for x, _ in outline), 1) != 84.0 or round(max(y for _, y in outline), 1) != 52.0:
    raise ValueError("E15 board candidate did not parse as 84 x 52 mm")
if len(components) != 56 or len(data["pads"]) != 242:
    raise ValueError("E15 snapshot counts changed; refresh the snapshot before rendering")


def group(ref: str) -> str:
    if ref == "J1" or ref in {"U5", "U6"} or ref in {"R1", "R2", "R3", "R4"}:
        return "USB/ESD"
    if ref == "U1":
        return "MCU"
    if ref == "J2" or ref.startswith(("U4", "C9", "C10", "R13", "L1", "Q1", "R14", "R15", "D1", "D2", "D3", "C11", "C12", "C13", "R16", "R17", "R18")):
        return "EPD/FPC"
    if ref.startswith("C") or ref.startswith("R") or ref in {"U2", "U3"}:
        return "Power"
    if ref.startswith("SW"):
        return "Buttons"
    return "Other"


COLORS = {
    "USB/ESD": "#C47F67",
    "MCU": "#356AA0",
    "EPD/FPC": "#4A8C7A",
    "Power": "#B276A6",
    "Buttons": "#C28A43",
    "Other": "#64748B",
}

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="820" viewBox="0 0 1260 820">',
    '<rect width="1260" height="820" fill="#F7F9FC"/>',
    '<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}.small{font-size:12px}.muted{fill:#52657B}.tiny{font-size:9px}.coord{font-size:10px;fill:#334155}</style>',
    '<text x="36" y="32" font-size="24" font-weight="bold">E15 · 清理版 PCB 候选布局</text>',
    '<text x="36" y="53" class="muted">来源：EasyEDA 保存重开后的 E15 快照；单位坐标保留 mil，图面按 1 mm = 10 px 绘制</text>',
]

# 84 x 52 reference frame and actual candidate board outline.
parts.append(f'<rect x="{OX:.1f}" y="{OY:.1f}" width="{OUTER_W*SCALE:.1f}" height="{OUTER_H*SCALE:.1f}" fill="none" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="7 5"/>')
parts.append(f'<path d="{path_d(outline)}" fill="#E5EAF0" stroke="#334155" stroke-width="2.4"/>')
parts.append(f'<path d="{path_d(reference)}" fill="none" stroke="#B45309" stroke-width="1.2" stroke-dasharray="4 3"/>')
parts.append('<text x="90" y="62" class="small muted">目标外包络 / 候选板框：84 × 52 mm</text>')

parts.extend([
    '<text x="930" y="90" font-size="17" font-weight="bold">当前主方向</text>',
    '<text x="930" y="116" class="small">USB-C：底边中部，缺口 x≈43–56 mm</text>',
    '<text x="930" y="138" class="small">屏幕：左上；电池目标：左下</text>',
    '<text x="930" y="160" class="small">NFC 保留区：右上；U1：右下</text>',
    '<text x="930" y="182" class="small">左侧中部 USB：保留为备选，尚未占用板框</text>',
    '<text x="930" y="204" class="small">本图是布局审查图，不是下单图</text>',
])

# Layer-9 mechanical rectangles are named by the Layer-13 labels in the
# snapshot.  The order is stable because the clean script creates them in the
# same order as this list.
mechanical_labels = [
    "301230 目标电池 · 30×12",
    "SCREEN / FPC · 37.42×31.90",
    "NFC RESERVE · 22×26",
    "J2 FPC · bend/support TBD",
    "SW1",
    "SW2",
    "SW3",
    "U1 candidate · RF clearance TBD",
]
for pts, label in zip(mechanical, mechanical_labels):
    x, y, w, h = rect_from_points(pts)
    parts.append(f'<rect x="{OX+x*SCALE:.1f}" y="{OY+display_y(y,h)*SCALE:.1f}" width="{w*SCALE:.1f}" height="{h*SCALE:.1f}" fill="#CBD5E1" fill-opacity="0.18" stroke="#64748B" stroke-width="1" stroke-dasharray="3 3"/>')
    parts.append(f'<text x="{OX+(x+w/2)*SCALE:.1f}" y="{OY+display_y(y+h/2)*SCALE:.1f}" text-anchor="middle" class="tiny">{html.escape(label)}</text>')

for pts in keepouts:
    x, y, w, h = rect_from_points(pts)
    parts.append(f'<path d="{path_d(pts)}" fill="#B8E0D7" fill-opacity="0.42" stroke="#16806B" stroke-width="2" stroke-dasharray="6 4"/>')
    parts.append(f'<text x="{OX+(x+w/2)*SCALE:.1f}" y="{OY+display_y(y+h/2)*SCALE+14:.1f}" text-anchor="middle" class="small">NFC REVIEW KEEP-OUT</text>')

# Exact component centers.  We show every designator but do not invent body
# dimensions from the footprint name.
for c in components:
    x, y = mm(c["x"]), mm(c["y"])
    ref = html.escape(c["ref"] or "?")
    color = COLORS[group(c["ref"] or "")]
    radius = 4.4 if ref in {"J1", "J2", "U1"} else 2.7
    px, py = OX + x*SCALE, OY + display_y(y)*SCALE
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{radius}" fill="{color}" stroke="#FFFFFF" stroke-width="1"/>')
    parts.append(f'<text x="{px+5:.1f}" y="{py-4:.1f}" class="tiny">{ref}</text>')

# Principal anchors and the USB datum.
for ref, label in [("J1", "USB-C · bottom-center"), ("U1", "MCU · lower-right"), ("J2", "FPC"), ("SW1", "SW1"), ("SW2", "SW2"), ("SW3", "SW3")]:
    c = next(c for c in components if c["ref"] == ref)
    x, y = mm(c["x"]), mm(c["y"])
    parts.append(f'<text x="{OX+x*SCALE+8:.1f}" y="{OY+display_y(y)*SCALE+12:.1f}" font-size="12" font-weight="bold">{html.escape(label)}</text>')

# Coordinate ticks use physical plan coordinates: x from left, y from bottom.
for x in range(0, 85, 10):
    px = OX + x*SCALE
    parts.append(f'<path d="M {px:.1f} {OY-5:.1f} V {OY:.1f}" stroke="#64748B"/><text x="{px:.1f}" y="{OY-10:.1f}" text-anchor="middle" class="tiny">{x}</text>')
for y in range(0, 53, 10):
    py = OY + display_y(y)*SCALE
    parts.append(f'<path d="M {OX-5:.1f} {py:.1f} H {OX:.1f}" stroke="#64748B"/><text x="{OX-10:.1f}" y="{py+3:.1f}" text-anchor="end" class="tiny">{y}</text>')

parts.extend([
    '<text x="90" y="610" class="muted">坐标方向：图面显示为物理平面；EasyEDA 原始 Y=0 在图面下边，Y 增大向上。</text>',
    '<text x="930" y="255" font-size="15" font-weight="bold">图例</text>',
])
legend = [("USB/ESD", "USB / ESD / CC"), ("Power", "充电 / 稳压 / 去耦"), ("EPD/FPC", "屏幕 FPC / EPD 电源"), ("MCU", "U1 主控"), ("Buttons", "按键")]
for i, (key, label) in enumerate(legend):
    y = 280 + i*24
    parts.append(f'<circle cx="942" cy="{y-4}" r="5" fill="{COLORS[key]}"/><text x="955" y="{y}" class="small">{label}</text>')
parts.extend([
    '<text x="930" y="430" class="small">当前 E15 统计：56 元件 · 242 焊盘 · 0 铜线 · 0 过孔</text>',
    '<text x="930" y="452" class="small">清理内容：移除旧多边形、旧文字与旧区域</text>',
    '<text x="930" y="474" class="small">待完成：原理图一致性、走线、DRC、RF/USB 净距</text>',
    '<text x="930" y="496" class="small">左中 USB 备选仅在屏幕/FPC 净距通过后再比较</text>',
    '<text x="930" y="518" class="small">E14 旧图保留为历史证据，未覆盖</text>',
    '<text x="90" y="665" class="muted">E15 clean layout · USB primary = bottom-center · review only</text>',
    '</svg>',
])

OUT.write_text("\n".join(parts) + "\n")
print(f"wrote {OUT} from {len(components)} components, {len(polylines)} polylines, {len(regions)} regions")
