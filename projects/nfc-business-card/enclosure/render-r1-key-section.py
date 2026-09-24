"""Draw dimension-based central key sections; omit fillets and moving actuators."""
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from shapely.geometry import box
from shapely.ops import unary_union

out = Path(os.environ['NFC_USB_HEIGHT_OUT'])
report = json.loads((out/'report.json').read_text())
fig, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=True)
rows = [report['trials'][i] for i in (0, 2, 4)]
titles = ['5.8 mm | existing flange', '5.4 mm | flat 0.8 mm flange', '5.4 mm | recessed underside']
if report['selected_height_mm'] < 5.4:
    heights = (5.4,5.2,4.6) if report['selected_height_mm']==4.6 else (5.4,5.3,5.2)
    rows = [next(r for r in report['trials'] if r['height_mm']==h and r['underside_recess_mm']>.0)
            for h in heights]
    titles = [f'{r["height_mm"]:.1f} mm | cavity {r["cavity_mm"]:.1f} mm' for r in rows]
for ax, row, title in zip(axes, rows, titles):
    h, f, recess = row['height_mm'], row['flange_mm'], row['underside_recess_mm']
    k = row['keys'][0]
    bottom, face = h-.85-f, h-.03
    cap = unary_union([box(-3.4,bottom,3.4,bottom+f), box(-2,bottom,2,face), box(-1.3,3.52,1.3,face)])
    if recess:
        cap = cap.difference(unary_union([box(-2.8,bottom-.01,-1.3,bottom+recess),
                                         box(1.3,bottom-.01,2.8,bottom+recess)]))
    if bottom < 3.52:
        cap = cap.difference(box(-1.3,bottom-.01,1.3,3.52))
    ax.add_patch(Polygon(list(cap.exterior.coords),fill=False,edgecolor='#267d9a',linestyle='--',linewidth=1.3))
    pts = [(x,z-k['translation_mm']) for x,z in cap.exterior.coords]
    ax.add_patch(Polygon(pts,facecolor='#9acbd9',edgecolor='#267d9a'))
    for x0,x1 in [(-4,-2.6),(2.6,4)]:
        ax.add_patch(Rectangle((x0,h-.8),x1-x0,.8,facecolor='#d7dde1',edgecolor='#768792'))
    for x0,x1 in [(-2.6,-1.4),(1.4,2.6)]:
        ax.add_patch(Rectangle((x0,1.92),x1-x0,k['fixed_switch_top_z_mm']-1.92,
                               facecolor='#626b78',edgecolor='#3f4c58'))
    ax.add_patch(Rectangle((-4,1.12),8,.8,facecolor='#b7d9c6',edgecolor='#69957b'))
    gap=k['roof_vertical_clearance_mm']
    ax.annotate('',xy=(2.2,k['fixed_switch_top_z_mm']+gap),xytext=(2.2,k['fixed_switch_top_z_mm']),
                arrowprops={'arrowstyle':'|-|','color':'#af5138','linewidth':1})
    ax.text(.5, .025, f'Roof / housing vertical gap: {gap:.2f} mm\nLocal roof: {row["remaining_roof_mm"]:.2f} mm',
            transform=ax.transAxes,ha='center',fontsize=10,color='#8d412e')
    ax.set_title(title,loc='left',fontsize=12,weight='bold')
    ax.set_xlim(-4.1,4.1);ax.set_ylim(.7,6.1);ax.set_aspect('equal')
    ax.set_xlabel('Offset from button centre / mm')
    ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Height from outside rear face / mm')
fig.suptitle('Key travel and underside relief | Geometry study',x=.05,ha='left',weight='bold',fontsize=17)
fig.text(.05,.075,'Filled blue: maximum checked travel. Dashed blue: rest position. Grey: fixed switch housing and shell.\nDimension-based centre sections: fillets, terminals and moving actuator omitted. Not a print or strength qualification.',fontsize=10,color='#4e6170')
fig.subplots_adjust(top=.83,bottom=.22,left=.05,right=.98,wspace=.16)
fig.savefig(out/'key-section.png',dpi=170)
