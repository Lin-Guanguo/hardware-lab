"""Render the E16 height-budget section (5 mm stack) as a review SVG."""
from pathlib import Path

OUT = Path('/Users/linguanguo/dev/hardware-lab/projects/nfc-business-card/enclosure/nfc-card-e16-height-budget.svg')
SCALE = 12.0   # horizontal mm -> px
VSCALE = 38.0  # vertical mm -> px (exaggerated for readability)
OX, OY = 120.0, 60.0
W_MM = 40.0  # section slice through the battery area
OUTER_H = 5.0
BOTTOM = 0.8
PCB_Z0, PCB_T = 1.7, 0.8
CAP_Z0, CAP_T = 4.2, 0.8
BAT_Z0, BAT_T = 1.4, 3.0
BAT_X0, BAT_W = 3.0, 30.0
SCREEN_X0, SCREEN_W = 2.0, 37.4
SLOT_Y = (10.38, 21.62)


def y(z):  # z = height above the bottom, drawn downward from the top
    return OY + (OUTER_H - z) * VSCALE


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="640" viewBox="0 0 1000 640">',
    '<rect width="1000" height="640" fill="#F7F9FC"/>',
    '<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}.s{font-size:13px}.m{fill:#52657B}.xs{font-size:11px}</style>',
    '<text x="36" y="34" font-size="23" font-weight="bold">E16 · 5 mm 高度预算剖面（电池区切片 x 0–40 mm，纵向放大）</text>',
    '<text x="36" y="56" class="s m">GCT USB4500-03-0-A 要求 0.80 mm 板厚，PCB 不能减薄；壳壁 0.8+0.8 后留给元件的净高只有 2.6 mm</text>',
]

def box(x0, z0, w, h, fill, stroke, label=None, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    parts.append(f'<rect x="{OX + x0*SCALE:.1f}" y="{y(z0+h):.1f}" width="{w*SCALE:.1f}" height="{h*SCALE:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')
    if label:
        parts.append(f'<text x="{OX + (x0+w/2)*SCALE:.1f}" y="{y(z0+h/2)+4:.1f}" text-anchor="middle" class="xs">{label}</text>')

# shells and PCB
box(0, 0, W_MM, BOTTOM, '#8FA9C1', '#31506E', '下壳 0.8')
box(0, PCB_Z0, W_MM, PCB_T, '#9BB8AA', '#2F6B57', 'PCB 0.8（连接器硬要求）')
box(0, CAP_Z0, W_MM, CAP_T, '#B9C9DC', '#31506E', '上壳 0.8')
# battery with the intrusion highlighted
box(BAT_X0, BAT_Z0, BAT_W, BAT_T, '#E6B96E', '#8A5A12', '电池 3.0 标称')
overlap_h = (BAT_Z0 + BAT_T) - CAP_Z0
parts.append(f'<rect x="{OX + BAT_X0*SCALE:.1f}" y="{y(CAP_Z0 + overlap_h):.1f}" width="{BAT_W*SCALE:.1f}" height="{overlap_h*SCALE:.1f}" fill="#D14343" fill-opacity="0.55" stroke="#8B1E1E" stroke-width="1.4"/>')
parts.append(f'<text x="{OX + (BAT_X0+BAT_W/2)*SCALE:.1f}" y="{y(CAP_Z0 + overlap_h/2)+4:.1f}" text-anchor="middle" class="xs" fill="#7A1010">顶上壳 {overlap_h:.1f} mm（54 mm³）</text>')
# screen on the front side
box(SCREEN_X0, PCB_Z0 + PCB_T, SCREEN_W, 0.85, '#C5D5E5', '#31506E', '屏幕玻璃 0.85')
# dimensions
parts.append(f'<text x="{OX - 12:.1f}" y="{y(OUTER_H)+4:.1f}" text-anchor="end" class="xs m">5.0</text>')
parts.append(f'<text x="{OX + W_MM*SCALE + 14:.1f}" y="{y(2.6)+4:.1f}" class="xs m">元件净高 2.6</text>')
parts.append(f'<line x1="{OX + W_MM*SCALE + 6:.1f}" y1="{y(PCB_Z0+PCB_T):.1f}" x2="{OX + W_MM*SCALE + 6:.1f}" y2="{y(CAP_Z0):.1f}" stroke="#94A3B8" stroke-width="1.2"/>')

# options panel
panel = [
    '三条出路（需按实测电池包络选择）',
    'a) 换 ≤2.6 mm 薄电池：5.0 mm 目标成立',
    'b) 整机放宽到约 5.4 mm：可直接用 3 mm 电池',
    'c) 电池区局部沉台/开窗：牺牲局部强度与密封',
    '',
    '本图只画高度关系；平面开口见 pcba-e16-right-mid.svg',
]
py_ = 300
parts.append(f'<text x="120" y="{py_}" font-size="15" font-weight="bold">结论</text>')
for i, line in enumerate(panel):
    cls = 's' if i == 0 else 'xs m'
    parts.append(f'<text x="860" y="{py_ + 24 + i*20}" class="{cls}">{line}</text>')
parts.extend(['</svg>'])
OUT.write_text("\n".join(parts) + "\n")
print("wrote", OUT)
