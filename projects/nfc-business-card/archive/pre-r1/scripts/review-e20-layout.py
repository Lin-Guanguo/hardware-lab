#!/usr/bin/env python3
"""Render the measured E20 placement for discussion; never modify EDA or CAD."""
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT/'hardware/records'
OUT = ROOT/'enclosure/renders'
OUT.mkdir(exist_ok=True)
snapshot = json.loads((RECORDS/'e20-clear-placement-snapshot.json').read_text())
bounds = json.loads((RECORDS/'e20-layout-review-body-bounds.json').read_text())
components = {c['ref']: c for c in json.loads((RECORDS/'e20-layout-review-pins.json').read_text())}
config = json.loads((ROOT/'hardware/e20-design.json').read_text())
case = json.loads((ROOT/'enclosure/e20-clear-window-5.8/e20-clear-report.json').read_text())

pairs = [('C1','1','U1','32'), ('C8','1','U2','10'), ('C3','1','U2','2'),
         ('R3','2','U1','35'), ('R4','2','U1','34'), ('C22','1','J2','24'),
         ('R10','2','U1','3'), ('R11','2','U1','4'), ('R12','2','U1','5')]
distances = []
for a, pa, b, pb in pairs:
    p = next(p for p in components[a]['pins'] if p['number'] == pa)
    q = next(p for p in components[b]['pins'] if p['number'] == pb)
    assert p['net'] == q['net']
    distances.append({'from':f'{a}.{pa}', 'to':f'{b}.{pb}', 'net':p['net'],
                      'pad_center_distance_mm':math.hypot(p['x']-q['x'],p['y']-q['y'])*.0254})
under_screen = {}
for ref, b in bounds.items():
    lo, hi = b['min_mm'], b['max_mm']
    if hi[0] > 1.95 and lo[0] < 39.37 and hi[1] > 18.25 and lo[1] < 50.15:
        under_screen[ref] = {'model_height_above_pcb_mm':hi[2]-case['pcb_top_mm'],
                             'vertical_gap_to_max_screen_mm':case['screen_back_max_mm']-hi[2]}
review = {'status':'READ_ONLY_PLACEMENT_REVIEW', 'eda_modified':False,
          'screen_nominal_thickness_mm':.85, 'screen_max_thickness_mm':1.,
          'pcb_to_max_screen_back_mm':case['screen_back_max_mm']-case['pcb_top_mm'],
          'pad_distances':distances, 'under_screen':under_screen,
          'limits':['Distances are pad-centre straight lines, not routed lengths.',
                    'Body bounds are native STEP geometry, not supplier maxima.',
                    'The drawing shows current placement; no proposed moves were applied.']}
(RECORDS/'e20-layout-review.json').write_text(json.dumps(review,indent=2)+'\n')

fig = plt.figure(figsize=(15,9), facecolor='#f5f7fa')
ax = fig.add_axes([.05,.17,.64,.74])
ax.set_aspect('equal'); ax.set_xlim(-2,86); ax.set_ylim(54,-2)
ax.set_facecolor('#f5f7fa')
# Outline vertices are the native manufacturing polygon; curves are omitted only in this overview.
raw = next(p['polygon']['polygon'] for p in snapshot['polylines'] if p['layer']==11)
points = [(raw[0]*.0254,raw[1]*.0254)]; i=2
while i < len(raw):
    if raw[i] == 'ARC': i += 2
    elif raw[i] == 'L': i += 1
    if i+1 >= len(raw): break
    points.append((raw[i]*.0254,raw[i+1]*.0254)); i += 2
ax.add_patch(Polygon(points, facecolor='#e8f2e9', edgecolor='#487653', lw=1.4))
ax.add_patch(Rectangle((1.5,1.5),32.5,14,facecolor='#e5dcc0',edgecolor='#ad9760'))
ax.text(17.75,8.5,'BATTERY ENVELOPE\n32.5 x 14 x 3.4 mm',ha='center',va='center',fontsize=9,color='#655630')
ax.add_patch(Rectangle((2,18.3),37.32,31.8,facecolor='#dbeafe',alpha=.55,edgecolor='#3b82f6',lw=1.5))
ax.text(3.5,48.8,'A  SCREEN ABOVE THESE PARTS',fontsize=8.5,color='#1d4ed8')
ax.add_patch(Rectangle((60,24),22,26,facecolor='#d2eee9',edgecolor='#008a80',linestyle='--'))
ax.text(71,37,'E  NFC RESERVE\nNo routed coil yet',ha='center',va='center',fontsize=10,color='#05776c')
ax.add_patch(Rectangle((56.5,0),13,4.96,facecolor='#f6cbd2',edgecolor='#c54d64',alpha=.7))
ax.add_patch(Rectangle((39.4,26),8.3,16,fill=False,edgecolor='#778',linestyle=':'))
ax.text(42.5,42.8,'FPC access',fontsize=7,color='#667')
for p in snapshot['pads']:
    shape=p['pad']; w,h=shape[1]*.0254,shape[2]*.0254
    angle=p['rotation']; a=math.radians(angle)
    xy=[(p['x']*.0254+dx*math.cos(a)-dy*math.sin(a),p['y']*.0254+dx*math.sin(a)+dy*math.cos(a))
        for dx,dy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
    ax.add_patch(Polygon(xy,facecolor='#b8bdc8',edgecolor='none',alpha=.9))
for ref,b in bounds.items():
    lo,hi=b['min_mm'],b['max_mm']; height=hi[2]-case['pcb_top_mm']
    color='#dca65e' if ref in under_screen and height>1.2 else '#637181'
    ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor=color,edgecolor='#344252',lw=.5))
    x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
    if ref in ['U1','J1','J2'] or ref.startswith('SW'):
        ax.text(x,y,ref,ha='center',va='center',fontsize=8,color='white')
    elif ref in under_screen or ref in ['C1','C5','C6','C7','C8','C22','R3','R4']:
        ax.text(x,lo[1]-.45,ref,ha='center',va='bottom',fontsize=6.2,color='#26384d')
for index in [0,5,6]:
    row=distances[index]; a,pa=row['from'].split('.');b,pb=row['to'].split('.')
    p=next(p for p in components[a]['pins'] if p['number']==pa)
    q=next(p for p in components[b]['pins'] if p['number']==pb)
    ax.plot([p['x']*.0254,q['x']*.0254],[p['y']*.0254,q['y']*.0254],color='#bf4b57',lw=1.3,linestyle='--')
ax.text(70,6.5,'B  USB / MCU',fontsize=9,color='#a53b49',ha='center')
ax.text(24,15.8,'C  Pull-ups',fontsize=9,color='#a53b49',ha='center')
ax.text(54,49.5,'D  EPD caps',fontsize=9,color='#a53b49',ha='center')
ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)');ax.tick_params(labelsize=8)
for spine in ax.spines.values():spine.set_visible(False)
fig.text(.05,.945,'E20 | placement review before routing',fontsize=20,weight='bold',color='#17314b')
fig.text(.05,.906,'Current geometry only. Dashed red lines measure separation; they are not proposed copper routes.',fontsize=10,color='#526477')
notes=[('A  Screen clearance','Screen: 0.85 mm nominal / 1.00 mm max\nPCB to screen back: 2.02 mm\nTallest CAD part: L1, 1.51 mm\nNominal remaining gap: 0.51 mm\nSupplier maximum envelopes still needed.'),
       ('B  Local power + USB','C1 to U1 VBUS: 14.32 mm\nR3/R4 to MCU: 13.30 / 14.17 mm\nReview local grouping and resistor values.'),
       ('C  Button pull-ups','R10-R12 to MCU: 46.48-46.74 mm\nMove as a compact functional group;\nkeep clear of the module antenna.'),
       ('D  Display capacitors','C22 to its J2 pin: 6.30 mm\nGroup by served pins, then align edges.\nPreserve insertion and latch space.'),
       ('E  Visible NFC area','Keep a clean antenna zone.\nPlace labels outside copper exclusions.\nChanging loop size needs RF retuning.')]
y=.84
for title,body in notes:
    fig.text(.72,y,title,fontsize=11,weight='bold',color='#17314b')
    fig.text(.72,y-.032,body,fontsize=9.2,va='top',linespacing=1.45,color='#526477')
    y-=.16 if title.startswith('A') else .145
fig.text(.05,.075,'Amber = taller parts under the screen | Gray = native component bodies | Pads shown in pale gray',fontsize=10,color='#526477')
fig.text(.05,.048,'58 components / 0 tracks / 0 vias. Rounded profile corners simplified in this overview. Not a manufacturing drawing.',fontsize=9,color='#526477')
for ext in ['png','svg']:fig.savefig(OUT/f'e20-placement-review.{ext}',dpi=160)
print('Rendered read-only placement overview and metrics.')
