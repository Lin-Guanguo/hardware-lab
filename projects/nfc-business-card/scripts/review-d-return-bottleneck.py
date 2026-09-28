#!/usr/bin/env python3
"""Audit D ground necks without editing copper or treating erosion as a DRC rule."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points, unary_union

ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'hardware/records'
source=REC/'board-review-d-snapshot.json'
s=json.loads(source.read_text())
spec=importlib.util.spec_from_file_location('cu',Path(__file__).with_name('check-r1-copper.py'))
cu=importlib.util.module_from_spec(spec);spec.loader.exec_module(cu)
shapes,_=cu.copper(s)
raw={l:unary_union(shapes['GND',l]) for l in [1,2]}
pads={(c['ref'],p['number']):p for c in s['components'] for p in s['pads'] if p['id'].startswith(c['id'])}
point=lambda p:Point(p['x']*.0254,p['y']*.0254)
checks=[];neck_candidates=[]
for erosion in [0,.005,.01,.02]:
    pieces={l:list(getattr(g,'geoms',[g])) for l in [1,2] for g in [raw[l].buffer(-erosion)]}
    graph=collections.defaultdict(list)
    for p in s['vias']+s['pads']:
        if p['net']!='GND' or (p.get('layer') and p['layer']!=12):continue
        ends=[(l,i) for l in [1,2] for i,g in enumerate(pieces[l]) if g.intersects(point(p))]
        if len(ends)==2:
            graph[ends[0]].append(ends[1]);graph[ends[1]].append(ends[0])
    a=next((1,i) for i,g in enumerate(pieces[1]) if g.intersects(point(pads['C8','2'])))
    z=next((1,i) for i,g in enumerate(pieces[1]) if g.intersects(point(pads['J1','A1B12'])))
    queue=[a];seen={a}
    for n in queue:
        for m in graph[n]:
            if m not in seen:seen.add(m);queue.append(m)
    checks.append({'erosion_mm':erosion,'c8_to_j1_connected':z in seen})
    if erosion==.02:
        for l,i in seen:
            for j,g in enumerate(pieces[l]):
                if (l,j) in seen:continue
                points=nearest_points(pieces[l][i],g);gap=points[0].distance(points[1])
                same_raw_piece=any(poly.covers(points[0]) and poly.covers(points[1]) for poly in getattr(raw[l],'geoms',[raw[l]]))
                if gap<.25 and same_raw_piece:
                    neck_candidates.append({'layer':l,'gap_after_erosion_mm':gap,'ends_mm':[list(p.coords)[0] for p in points]})
neck_candidates.sort(key=lambda v:v['gap_after_erosion_mm'])
section=raw[1].intersection(LineString([(60.15,4.9),(60.15,5.4)]))
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Exact per-layer GND polygon unions, conceptual plated centre links, BFS from C8.2 to J1.A1B12. Inward offsets are a diagnostic, not a manufacturing rule or current simulation.','checks':checks,'neck_search_windows':neck_candidates,'neck_vertical_section_at_x_60p15_mm':{'geometry':section.wkt,'width_mm':section.length},'verdict':'Connectivity passes, but the charger return depends on narrow copper. Not accepted as a finished power-return layout.'}
(REC/'board-review-d-return-bottleneck.json').write_text(json.dumps(report,indent=2)+'\n')
fig,axs=plt.subplots(1,len(neck_candidates),figsize=(12,6),squeeze=False)
for ax,item in zip(axs[0],neck_candidates):
    x=sum(p[0] for p in item['ends_mm'])/2;y=sum(p[1] for p in item['ends_mm'])/2
    for (net,l),parts in sorted(shapes.items(),key=lambda kv:kv[0][0]!='GND'):
        if l!=item['layer']:continue
        g=unary_union(parts)
        for poly in getattr(g,'geoms',[g]):
            if not hasattr(poly,'exterior') or not poly.intersects(Point(x,y).buffer(1)):continue
            ax.fill(*poly.exterior.xy,color='#76ac8b' if net=='GND' else '#b55b62',alpha=.85)
            for hole in poly.interiors:ax.fill(*hole.xy,color='white')
    ax.plot(*zip(*item['ends_mm']),'o--',color='#213a81',lw=1)
    ax.set(xlim=(x-.7,x+.7),ylim=(y+.7,y-.7),aspect='equal',xlabel='x / mm',ylabel='y / mm',title=f'Top GND neck search near ({x:.3f}, {y:.3f})')
    ax.grid(alpha=.2)
fig.suptitle('D charger return: connected copper is not a wide return path')
fig.text(.5,.025,'Green = actual GND; red = other copper. Blue marks the separation after 0.02 mm inward offset; not an actual gap.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(REC/'board-review-d-return-bottleneck.png',dpi=180);plt.close(fig)
print(json.dumps(report,indent=2))
