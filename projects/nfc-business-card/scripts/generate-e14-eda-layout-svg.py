"""Render an E14 plan view from a saved EasyEDA coordinate snapshot.

The output deliberately shows the actual PCB outline and primitive coordinates,
including legacy board/mechanical geometry. It is a review drawing, not a
manufacturing drawing.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "projects/nfc-business-card/hardware/e14-eda-snapshot.json"
OUT = ROOT / "projects/nfc-business-card/enclosure/pcba-e14-battery-layout.svg"
MIL_PER_MM = 39.37007874015748
# The magenta Layer-14 reference rectangle is the global EDA 0,0 frame.
# Keeping that origin makes the 84 × 52 mm target envelope and the actual
# Layer-11 outline land in the same coordinate system.
ORIGIN_MIL = (0.0, 0.0)
SCALE = 10.0
OX, OY = 90.0, 72.0
OUTER_W, OUTER_H = 84.0, 52.0

# The snapshot is taken from the live E14 PCB on 2026-09-22.
data = json.loads(SNAPSHOT.read_text())
components = data["components"]
polylines = data["polylines"]
regions = data["regions"]


def mm(value: float, axis: int) -> float:
    return (float(value) - ORIGIN_MIL[axis]) / MIL_PER_MM


def display_y(y: float, height: float = 0.0) -> float:
    """Map EasyEDA's saved Y coordinate to the plan-view screen coordinate.

    The PCB editor's top view places the saved Y=0 edge at the bottom of the
    canvas.  SVG coordinates grow downwards, so the physical plan must be
    flipped around the 52 mm review envelope when rendered.
    """
    return OUTER_H - y - height


def polygon_points(raw: list) -> list[tuple[float, float]]:
    # EDA polygon format is [x, y, "L", x, y, ...].  Only the first point
    # carries the command token; all following points are pairs.
    nums = raw["polygon"] if isinstance(raw, dict) else raw
    points = []
    i = 0
    while i + 1 < len(nums):
        if isinstance(nums[i], str):
            i += 1
            continue
        if isinstance(nums[i + 1], str):
            i += 1
            continue
        points.append((mm(nums[i], 0), mm(nums[i + 1], 1)))
        i += 2
    return points


def path_d(points: list[tuple[float, float]]) -> str:
    return " ".join(
        f"{'M' if i == 0 else 'L'} {OX + x*SCALE:.1f} {OY + display_y(y)*SCALE:.1f}"
        for i, (x, y) in enumerate(points)
    ) + " Z"


def rect_from_points(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


outline = next(polygon_points(p["polygon"]) for p in polylines if p["layer"] == 11)
mechanical = [
    (p["id"], polygon_points(p["polygon"]))
    for p in polylines
    if p["layer"] == 9
]
legacy_reference = [
    (p["id"], polygon_points(p["polygon"]))
    for p in polylines
    if p["layer"] == 14 and p["id"] != "0b3fe8f9b48c6981"
]
keepouts = [polygon_points(r["polygon"]) for r in regions]

if len(outline) != 11:
    raise ValueError(f"unexpected Layer 11 point count: {len(outline)}")
if round(max(x for x, _ in outline), 1) != 82.5 or round(max(y for _, y in outline), 1) != 50.5:
    raise ValueError("Layer 11 outline did not parse in the global 84 × 52 mm frame")

# Group labels are based on reference designators and exact EDA positions.
def group(ref: str) -> str:
    if ref == "J1" or ref in {"U5", "U6"} or ref in {"R1", "R2", "R3", "R4"}:
        return "USB/ESD"
    if ref in {"U1"}:
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
    '<text x="36" y="32" font-size="24" font-weight="bold">E14 · EasyEDA 实际坐标平面图</text>',
    '<text x="36" y="53" class="muted">来源：E14 PCB 保存重开后的 2026-09-22 快照；单位坐标保留 mil，图中按 1 mm = 10 px 绘制</text>',
]

# Target envelope is dotted; actual outline is the filled polygon.
parts.append(f'<rect x="{OX:.1f}" y="{OY:.1f}" width="{OUTER_W*SCALE:.1f}" height="{OUTER_H*SCALE:.1f}" fill="none" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="7 5"/>')
parts.append('<text x="90" y="62" class="small muted">目标外包络 84 × 52 mm</text>')
parts.append(f'<path d="{path_d(outline)}" fill="#E5EAF0" stroke="#334155" stroke-width="2.4"/>')
parts.append('<text x="930" y="90" font-size="17" font-weight="bold">当前 E14 真实状态</text>')
parts.append('<text x="930" y="116" class="small">板框仍是历史/候选几何，含缺口和非矩形段</text>')
parts.append('<text x="930" y="138" class="small">电池尚未成为 PCB 元件或封装</text>')
parts.append('<text x="930" y="160" class="small">Layer9 / Layer14 / PROHIBIT 均按原始图元保留</text>')
parts.append('<text x="930" y="182" class="small">这是布局审查图，不是下单图</text>')

# Show exact layer-9 mechanical rectangles without assigning unsupported semantics.
for idx, (pid, pts) in enumerate(mechanical, 1):
    x, y, w, h = rect_from_points(pts)
    py = display_y(y, h)
    parts.append(f'<rect x="{OX+x*SCALE:.1f}" y="{OY+py*SCALE:.1f}" width="{w*SCALE:.1f}" height="{h*SCALE:.1f}" fill="#CBD5E1" fill-opacity="0.15" stroke="#64748B" stroke-width="1" stroke-dasharray="3 3"/>')
    if pid == "0df0fd14140f6851":
        label = "J2/屏幕机械区（37.42×31.90）"
        parts.append(f'<text x="{OX+(x+w/2)*SCALE:.1f}" y="{OY+display_y(y+h/2)*SCALE:.1f}" text-anchor="middle" class="small">{label}</text>')
    elif pid == "be5a8ef32ca73c6f":
        parts.append(f'<text x="{OX+(x+w/2)*SCALE:.1f}" y="{OY+display_y(y+h/2)*SCALE:.1f}" text-anchor="middle" class="tiny">NFC RESERVE · Layer9 22×26</text>')

# Layer-14 reference geometry is separate from the target envelope. Keep it
# visible because it explains why the former battery reserve must not be
# mistaken for the current 301230 placement.
for pid, pts in legacy_reference:
    x, y, w, h = rect_from_points(pts)
    py = display_y(y, h)
    parts.append(f'<rect x="{OX+x*SCALE:.1f}" y="{OY+py*SCALE:.1f}" width="{w*SCALE:.1f}" height="{h*SCALE:.1f}" fill="#F3C98B" fill-opacity="0.12" stroke="#B45309" stroke-width="1.4" stroke-dasharray="4 3"/>')
    parts.append(f'<text x="{OX+(x+w/2)*SCALE:.1f}" y="{OY+display_y(y+h/2)*SCALE:.1f}" text-anchor="middle" class="tiny">历史 Layer14 reserve · {pid[:6]}</text>')

# Exact prohibited regions from E14. Their saved names are only PROHIBIT;
# preserve the geometry without inventing an NFC meaning.
for index, pts in enumerate(keepouts, 1):
    x, y, w, h = rect_from_points(pts)
    parts.append(f'<path d="{path_d(pts)}" fill="#B8E0D7" fill-opacity="0.38" stroke="#16806B" stroke-width="2" stroke-dasharray="6 4"/>')
    parts.append(f'<text x="{OX+(x+w/2)*SCALE:.1f}" y="{OY+display_y(y+h/2)*SCALE:.1f}" text-anchor="middle" font-size="11">实际禁布区 {index} · PROHIBIT</text>')

# Battery is a target envelope, intentionally marked as not in the PCB snapshot.
bx, by, bw, bh = 3.0, 1.5, 30.0, 12.0
parts.append(f'<rect x="{OX+bx*SCALE:.1f}" y="{OY+display_y(by,bh)*SCALE:.1f}" width="{bw*SCALE:.1f}" height="{bh*SCALE:.1f}" fill="#F0C886" fill-opacity="0.42" stroke="#B45309" stroke-width="2" stroke-dasharray="7 4"/>')
parts.append(f'<text x="{OX+(bx+bw/2)*SCALE:.1f}" y="{OY+display_y(by+bh/2)*SCALE:.1f}" text-anchor="middle" font-size="12">301230 目标（未入 PCB）</text>')

# Exact component points. Labels use the designator, so no guessed body dimensions are shown.
for c in components:
    x, y = mm(c["x"], 0), mm(c["y"], 1)
    py = display_y(y)
    ref = html.escape(c["ref"] or "?")
    g = group(c["ref"] or "")
    color = COLORS[g]
    r = 4.4 if ref in {"J1", "J2", "U1"} else 2.7
    parts.append(f'<circle cx="{OX+x*SCALE:.1f}" cy="{OY+py*SCALE:.1f}" r="{r}" fill="{color}" stroke="#FFFFFF" stroke-width="1"/>')
    # Keep labels readable while still showing every designator.
    tx = OX + x*SCALE + 5
    ty = OY + py*SCALE - 4
    parts.append(f'<text x="{tx:.1f}" y="{ty:.1f}" class="tiny">{ref}</text>')

# Reference labels for the principal anchors.
for ref, label in [("J1", "USB-C"), ("U1", "MCU"), ("J2", "FPC"), ("SW1", "SW1"), ("SW2", "SW2"), ("SW3", "SW3")]:
    c = next(c for c in components if c["ref"] == ref)
    x, y = mm(c["x"], 0), mm(c["y"], 1)
    parts.append(f'<text x="{OX+x*SCALE+8:.1f}" y="{OY+display_y(y)*SCALE+12:.1f}" font-size="12" font-weight="bold">{label} ({ref})</text>')

# Coordinate ticks.
for x in range(0, 85, 10):
    px = OX + x*SCALE
    parts.append(f'<path d="M {px:.1f} {OY-5:.1f} V {OY:.1f}" stroke="#64748B"/><text x="{px:.1f}" y="{OY-10:.1f}" text-anchor="middle" class="tiny">{x}</text>')
for y in range(0, 53, 10):
    py = OY + display_y(y)*SCALE
    parts.append(f'<path d="M {OX-5:.1f} {py:.1f} H {OX:.1f}" stroke="#64748B"/><text x="{OX-10:.1f}" y="{py+3:.1f}" text-anchor="end" class="tiny">{y}</text>')
parts.append('<text x="90" y="610" class="muted">坐标方向：图面按 EasyEDA 画布视图翻转 Y；原始 EDA 数值 Y=0 在图面下边，Y 增大向上。</text>')
parts.append('<text x="930" y="255" font-size="15" font-weight="bold">图例</text>')
legend = [("USB/ESD", "USB / ESD / CC"), ("Power", "充电 / 稳压 / 去耦"), ("EPD/FPC", "屏幕 FPC / EPD 电源"), ("MCU", "U1 主控"), ("Buttons", "按键")]
for i, (key, label) in enumerate(legend):
    y = 280 + i*24
    parts.append(f'<circle cx="942" cy="{y-4}" r="5" fill="{COLORS[key]}"/><text x="955" y="{y}" class="small">{label}</text>')
parts.append('<text x="930" y="430" class="small">该图揭示了需要继续修正的项目：</text>')
parts.append('<text x="930" y="452" class="small">1. 电池目标与当前板框必须重新定义</text>')
parts.append('<text x="930" y="474" class="small">2. 屏幕/FPC 区需和外壳窗口同步</text>')
parts.append('<text x="930" y="496" class="small">3. USB 开口、板边和器件净距需重画</text>')
parts.append('<text x="930" y="518" class="small">4. 走线完成前不能生成制造稿</text>')
parts.append('<text x="90" y="665" class="muted">旧示意图已另存为 pcba-e14-battery-layout-intended.svg；本图以 E14 实际图元快照为准。</text>')
parts.append('</svg>')
OUT.write_text("\n".join(parts) + "\n")
print(f"wrote {OUT} from {len(components)} components, {len(polylines)} polylines, {len(regions)} regions")
