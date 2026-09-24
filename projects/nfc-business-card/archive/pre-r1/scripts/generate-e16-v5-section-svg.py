"""Render the current E16 V5 enclosure stack as a review cross-section SVG.

Three slices, all in enclosure coordinates (z = 0 at the outside of the bottom
plate): through the battery pocket, through the key column and through the
panel/FPC area. Numbers come from enclosure/nfc-card-e16-enclosure-v5-report.json
and the measured component heights in hardware/e16-right-mid-snapshot.json, so
the drawing has to be regenerated when the model changes.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENCL = ROOT / "projects/nfc-business-card/enclosure"
OUT = ENCL / "nfc-card-e16-v5-stack-section.svg"
REPORT = ENCL / "nfc-card-e16-enclosure-v5-report.json"

HSCALE = 10.0          # mm along the card -> px
VSCALE = 58.0          # mm of height -> px (exaggerated 5.8x)
PANEL_W = 84.0         # mm of the card drawn in every slice
MARGIN_X = 150.0
PANEL_TOP = 96.0
PANEL_GAP = 96.0
CANVAS_W = int(MARGIN_X * 2 + PANEL_W * HSCALE + 250)
CANVAS_H = int(PANEL_TOP + 3 * (4.5 * VSCALE) + 2 * PANEL_GAP + 90)

report = json.loads(REPORT.read_text())
stack = report["height_stack_mm"]
PLATE_B = stack["bottom_plate"]
GAP_B = stack["under_pcb_clearance"]
PCB_T = stack["pcb"]
CAV_T = stack["top_cavity"]
PLATE_T = stack["top_plate"]
TOTAL = stack["total"]
PCB_Z0 = PLATE_B + GAP_B
PCB_TOP = PCB_Z0 + PCB_T
CAVITY_TOP = PCB_TOP + CAV_T
BITE = report["battery_bite_mm"]
CELL = (2.5, BITE[3] - 2.5, 30.0, 3.0)          # x0, x1, width, height (nominal 301230)
RIB_Z0, RIB_H = 3.6, 0.4                        # pocket ceiling rib
STEM_TOP = 3.0                                  # SKQGABE010: 1.5 mm above the PCB top
CAP_BOSS_BOTTOM = 3.05
PANEL_BACK = 3.05
FOAM_TOP = PANEL_BACK
SCREEN_T = 0.85
WINDOW = report["screen"]["window_mm"]          # x0, y0, w, h

COLORS = {
    "shell": ("#8FA9C1", "#31506E"),
    "pcb": ("#9BB8AA", "#2F6B57"),
    "cell": ("#E6B96E", "#8A5A12"),
    "part": ("#A855F7", "#6B21A8"),
    "screen": ("#C5D5E5", "#31506E"),
    "cap": ("#F0C7A0", "#B45309"),
    "foam": ("#CBD5E1", "#64748B"),
    "air": ("#FFFFFF", "#94A3B8"),
}


def y(panel_top: float, z: float) -> float:
    return panel_top + (TOTAL - z) * VSCALE


def rect(parts, panel_top, x0, z0, w, h, key, label=None, label_dx=0.0, dash=None, opacity=1.0):
    fill, stroke = COLORS[key]
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(
        f'<rect x="{MARGIN_X + x0 * HSCALE:.1f}" y="{y(panel_top, z0 + h):.1f}" width="{w * HSCALE:.1f}" '
        f'height="{h * VSCALE:.1f}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="1.5"{extra}/>'
    )
    if label:
        parts.append(
            f'<text x="{MARGIN_X + (x0 + w / 2) * HSCALE + label_dx:.1f}" y="{y(panel_top, z0 + h / 2) + 4:.1f}" '
            f'text-anchor="middle" class="xs">{label}</text>'
        )


def dim(parts, panel_top, z0, z1, x_px, text, anchor="start"):
    parts.append(
        f'<line x1="{x_px:.1f}" y1="{y(panel_top, z0):.1f}" x2="{x_px:.1f}" y2="{y(panel_top, z1):.1f}" '
        f'stroke="#94A3B8" stroke-width="1.2"/>'
    )
    parts.append(
        f'<text x="{x_px + (8 if anchor == "start" else -8):.1f}" y="{y(panel_top, (z0 + z1) / 2) + 4:.1f}" '
        f'text-anchor="{anchor}" class="xs m">{text}</text>'
    )


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#F7F9FC"/>',
    '<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}'
    '.t{font-size:15px;font-weight:bold}.s{font-size:12.5px}.m{fill:#52657B}.xs{font-size:10.5px}</style>',
    f'<text x="36" y="40" font-size="24" font-weight="bold">E16 外壳 V5 · 4.5 mm 叠层剖面（纵向放大 5.8×，来源 geometry v5 report）</text>',
    f'<text x="36" y="64" class="s m">三张切片：电池袋（y≈8）· 按键列（y=14）· 屏幕/FPC 区（y≈34）；虚线为元件参考包络，不是制造图</text>',
]

panel = PANEL_TOP

# --- slice 1: through the battery pocket -----------------------------------
parts.append(f'<text x="36" y="{panel - 18:.1f}" class="t">1 · 电池袋切片（y≈8，x 0–33.5 无板，x &gt; 33.5 为 PCB 区）</text>')
rect(parts, panel, 0, 0, PANEL_W, PLATE_B, "shell", "下壳底板 0.4")
rect(parts, panel, BITE[0], PLATE_B, BITE[2], PCB_T + GAP_B, "air", "")
rect(parts, panel, CELL[0], PLATE_B + 0.4 - 0.4, 0, 0, "air")  # keep geometry helpers honest
rect(parts, panel, CELL[0], PLATE_B, CELL[2], 3.0, "cell", "301230 电芯 3.0（标称）")
rect(parts, panel, 1.0, RIB_Z0, 32.0, RIB_H, "shell", "电池袋加强筋 0.4")
rect(parts, panel, 0, CAVITY_TOP, PANEL_W, PLATE_T, "shell", "上盖 0.5", dash="4 3")
rect(parts, panel, BITE[2], PCB_Z0, PANEL_W - BITE[2], PCB_T, "pcb", "PCB 0.8")
dim(parts, panel, PLATE_B + 3.0, CAVITY_TOP, MARGIN_X + 44 * HSCALE, "电芯顶到上盖内表面 0.6 mm")
dim(parts, panel, 0, PLATE_B, MARGIN_X - 12, "0.4", anchor="end")
dim(parts, panel, CAVITY_TOP, TOTAL, MARGIN_X - 12, "0.5", anchor="end")

# --- slice 2: through the key column ---------------------------------------
panel += 4.5 * VSCALE + PANEL_GAP
parts.append(f'<text x="36" y="{panel - 18:.1f}" class="t">2 · 按键列切片（y=14，SW3 + 齐平键帽）</text>')
rect(parts, panel, 0, 0, PANEL_W, PLATE_B, "shell", "下壳底板 0.4")
rect(parts, panel, BITE[2], PCB_Z0, PANEL_W - BITE[2], PCB_T, "pcb", "PCB 0.8")
rect(parts, panel, 35.5, PCB_TOP, 5.2, 1.5, "part", "SW3 本体 1.5")
rect(parts, panel, 36.9, STEM_TOP, 2.4, CAP_BOSS_BOTTOM - STEM_TOP, "air", "")
rect(parts, panel, 36.0, CAVITY_TOP - PLATE_T, 4.2, PLATE_T, "cap", "")
rect(parts, panel, 36.9, CAP_BOSS_BOTTOM, 2.4, CAVITY_TOP - CAP_BOSS_BOTTOM, "cap", "")
rect(parts, panel, 0, CAVITY_TOP, 36.0, PLATE_T, "shell")
rect(parts, panel, 40.2, CAVITY_TOP, PANEL_W - 40.2, PLATE_T, "shell", "上盖 0.5")
rect(parts, panel, 36.0, CAVITY_TOP, 4.2, PLATE_T, "air", "", dash="3 2")
parts.append(f'<text x="{MARGIN_X + 20 * HSCALE:.1f}" y="{y(panel, 4.25) + 4:.1f}" class="xs m">上盖在 Ø4.6 键孔处断开</text>')
parts.append(f'<text x="{MARGIN_X + 42 * HSCALE:.1f}" y="{y(panel, 4.25) + 4:.1f}" class="xs" fill="#B45309">键帽 Ø4.2 × 0.5 骑在孔里</text>')
parts.append(
    f'<line x1="{MARGIN_X + 38.1 * HSCALE:.1f}" y1="{y(panel, STEM_TOP):.1f}" '
    f'x2="{MARGIN_X + 60 * HSCALE:.1f}" y2="{y(panel, STEM_TOP):.1f}" stroke="#B45309" stroke-width="1" stroke-dasharray="3 2"/>'
)
parts.append(
    f'<text x="{MARGIN_X + 61 * HSCALE:.1f}" y="{y(panel, STEM_TOP) + 4:.1f}" class="xs" fill="#B45309">'
    f'按键顶面 z=3.0，距上盖内表面 1.0 mm——由键帽补上</text>'
)
dim(parts, panel, STEM_TOP, CAP_BOSS_BOTTOM, MARGIN_X + 30 * HSCALE, "0.05 间隙")
dim(parts, panel, CAP_BOSS_BOTTOM, CAVITY_TOP, MARGIN_X + 30 * HSCALE, "0.95 键帽柱")
parts.append(
    f'<text x="{MARGIN_X + 50 * HSCALE:.1f}" y="{y(panel, 3.55) + 4:.1f}" class="xs m">'
    f'键帽顶面与上盖齐平 z=4.5，按下走完 0.25 mm 行程</text>'
)

# --- slice 3: through the panel and FPC ------------------------------------
panel += 4.5 * VSCALE + PANEL_GAP
parts.append(f'<text x="36" y="{panel - 18:.1f}" class="t">3 · 屏幕 / FPC 切片（y≈34，最高元件与屏背间隙）</text>')
rect(parts, panel, 0, 0, PANEL_W, PLATE_B, "shell", "下壳底板 0.4")
rect(parts, panel, 0, PCB_Z0, PANEL_W, PCB_T, "pcb", "PCB 0.8（y=34 处整幅连续）")
rect(parts, panel, 28.0, PCB_TOP, 3.0, 1.51, "part", "最高元件 1.51")
rect(parts, panel, 2.0, PANEL_BACK, 37.32, SCREEN_T, "screen", "GDEH0154E01 屏 0.85")
rect(parts, panel, WINDOW[0], CAVITY_TOP, WINDOW[2], PLATE_T, "air", "屏窗 27.8")
rect(parts, panel, 0, CAVITY_TOP, PANEL_W, PLATE_T, "shell", "上盖 0.5")
rect(parts, panel, 2.0, PANEL_BACK - 0.0, 0, 0, "air")
dim(parts, panel, PANEL_BACK, CAVITY_TOP - PLATE_T, MARGIN_X + 1.0 * HSCALE, "屏背 1.5 mm 泡棉（压缩）", anchor="end")
dim(parts, panel, PCB_TOP, PANEL_BACK, MARGIN_X + 46 * HSCALE, "元件 1.51 → 屏背 0.04")
parts.append(
    f'<text x="{MARGIN_X + 62 * HSCALE:.1f}" y="{y(panel, 3.4) + 4:.1f}" class="xs m">'
    f'FPC 从屏东缘 x=39.32 下到 J2 x≈48.0，通道内最高件 z=1.95</text>'
)

# --- legend ---------------------------------------------------------------
legend_x = MARGIN_X + PANEL_W * HSCALE + 40
legend = [("shell", "打印壳 / 加强筋"), ("pcb", "PCB 0.8（GCT 要求）"), ("cell", "301230 电芯 3.0"),
          ("part", "元件参考高度"), ("screen", "屏模块"), ("cap", "齐平键帽"), ("air", "空气 / 间隙")]
ly = PANEL_TOP + 10
parts.append(f'<text x="{legend_x:.0f}" y="{ly:.0f}" class="t">图例</text>')
for i, (key, label) in enumerate(legend):
    fill, stroke = COLORS[key]
    parts.append(f'<rect x="{legend_x:.0f}" y="{ly + 22 + i * 26:.0f}" width="18" height="14" fill="{fill}" stroke="{stroke}"/>')
    parts.append(f'<text x="{legend_x + 26:.0f}" y="{ly + 34 + i * 26:.0f}" class="s">{label}</text>')
facts = [
    "",
    "总高 4.5 = 0.4 底板 + 0.3 板下间隙 + 0.8 PCB + 2.5 顶腔 + 0.5 上盖",
    "电池袋：底板 201 mm³、上盖 251.25 mm³ 体积回归通过",
    "真实元件干涉：0（J1 顶面 3.87，余量 0.13 mm）",
    "键帽：Ø4.2 骑 Ø4.6 孔，行程 0.25 mm 不越程",
    "打印：JLC 8001 树脂推荐壁厚 >0.8，本设计 0.4/0.5",
    "→ 需要能稳定做薄壁的工艺，或改薄片前盖路线",
]
for i, line in enumerate(facts):
    parts.append(f'<text x="{legend_x:.0f}" y="{ly + 250 + i * 22:.0f}" class="xs m">{line}</text>')

parts.append("</svg>")
OUT.write_text("\n".join(parts) + "\n")
print("wrote", OUT)
