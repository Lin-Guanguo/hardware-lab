"""Draw an enlarged straight-side section from the rear-cover study dimensions."""
import json
import os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.font_manager import FontProperties

OUT = Path(os.environ.get('NFC_REAR_STUDY_OUT', str(Path(__file__).resolve().parent / 'r1-rounded-rear-study')))
r = json.loads((OUT/'report.json').read_text())
d = r['dimensions_mm']
font = FontProperties(fname='/System/Library/Fonts/STHeiti Medium.ttc')
plt.rcParams['font.family'] = font.get_name()
plt.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots(figsize=(12, 7), facecolor='#f7f9fa')
ax.set_facecolor('#f7f9fa')


def arc(cx, cy, radius, start, end):
    a = np.radians(np.linspace(start, end, 20))
    return list(zip(cx+radius*np.cos(a), cy+radius*np.sin(a)))


front_r, rear_r = d['front_outer_radius'], d['rear_outer_radius']
body = [(front_r,5.8),(6.5,5.8),(6.5,5),(1.2,5),(1.2,.08)]
body += arc(1.12,.08,.08,0,-90)
body += [(rear_r,0)] + arc(rear_r,rear_r,rear_r,-90,-180)
body += [(0,5.8-front_r)] + arc(front_r,5.8-front_r,front_r,180,90)
cover_x = d['rear_seam_body_edge_inset'] + d['radial_gap']
cover = [(cover_x,.08),(cover_x,.8),(6.5,.8),(6.5,0),(cover_x+.08,0)]
cover += arc(cover_x+.08,.08,.08,-90,-180)
ax.add_patch(Polygon(body, fc='#82b5c1', ec='#315a67', lw=1.5))
ax.add_patch(Polygon(cover, fc='#d5e5e9', ec='#526f79', lw=1.5))
pcb_x = 1.2 + r['pcb_min_distance_to_upper_mm']
ax.add_patch(Rectangle((pcb_x,1.12),6.5-pcb_x,.8, fc='#b9cda5', ec='#607749', lw=1.5))
ax.text(4,5.38,'顶面＋侧壁：同一个零件', ha='center',va='center',fontsize=14)
ax.text(4,.4,'独立底盖 0.8 mm',ha='center',va='center',fontsize=13)
ax.text(4,1.52,'PCB 0.8 mm',ha='center',va='center',fontsize=13)
ax.annotate('名义板边余量 0.513 mm',xy=(1.455,1.52),xytext=(2.4,2.65),
            arrowprops={'arrowstyle':'->','color':'#4e665a'},fontsize=13,color='#3c5847')
ax.annotate('背面接缝：离外轮廓约 1.33 mm',xy=(1.325,.25),xytext=(2,-1.25),
            arrowprops={'arrowstyle':'->','color':'#ab624b'},fontsize=13,color='#974d37')
ax.annotate(f'侧面顺滑过渡至背面 R{rear_r:g}',xy=(rear_r*.293,rear_r*.293),xytext=(-1.25,-.75),
            arrowprops={'arrowstyle':'->','color':'#315a67'},fontsize=12,color='#315a67')
ax.annotate(f'正面圆角 R{front_r:g}',xy=(front_r*.293,5.8-front_r*.293),xytext=(-1.35,6.32),
            arrowprops={'arrowstyle':'->','color':'#315a67'},fontsize=12,color='#315a67')
ax.text(3.3,3.8,'没有向内伸的承托台阶\n保留 PCB 从背面装入的入口',ha='center',
        fontsize=15,color='#345d68',linespacing=1.65)
ax.annotate('',xy=(.72,-.05),xytext=(.72,-.45),arrowprops={'arrowstyle':'->','color':'#315a67'})
ax.text(-1.25,1.6,'外侧',fontsize=14,color='#5e6c72')
ax.text(6.15,2.6,'内腔',fontsize=14,color='#5e6c72')
ax.set_xlim(-1.5,6.8);ax.set_ylim(-1.75,6.8);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('把缝放在背面平面内，保留圆润侧边',fontsize=22,y=.97,color='#203d47')
fig.text(.5,.035,'直边局部放大剖面 · 名义尺寸，单位 mm · 竖缝 0.25，圆角缝口约 0.41 · 胶接与定位待验证',
         ha='center',fontsize=11,color='#66777f')
fig.savefig(OUT/'section.png',dpi=170,facecolor=fig.get_facecolor(),bbox_inches='tight')
plt.close(fig)
