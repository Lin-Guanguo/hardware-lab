#!/usr/bin/env python3
"""Compare actual isolated copper and bounded local returns for option A2."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import Point, box
from shapely.ops import unary_union
from v4_geometry import geometry, filled_ground

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('candidate', type=Path)
ap.add_argument('output', type=Path)
args = ap.parse_args()
project = Path(__file__).resolve().parents[1]
old = project / 'hardware/kicad/v4-option-a-integration-rejected/NFC-Card-V4.kicad_pcb'
names = ['C3.2', 'C4.2', 'U3.2', 'R19.2', 'R14.2']
args.output.mkdir(parents=True, exist_ok=True)
report = {'scope': 'Native saved fill plus explicit copper. Erosion is a diagnostic, not an impedance or fabrication limit.', 'boards': []}
fig, axes = plt.subplots(2, 2, figsize=(15, 12), constrained_layout=True)
for row, path in enumerate([old, args.candidate]):
    b, pads, objects, refs = geometry(path)
    copper = {l: unary_union([filled_ground(b,l), *[o['shape'] for o in objects if o['net']=='GND' and l in o['layers']]]) for l in ['F.Cu','B.Cu']}

    def reach(window, seed, radius=0):
        cropped = {l:g.intersection(window).buffer(-radius) for l,g in copper.items()}
        components = {l:list(g.geoms) if g.geom_type=='MultiPolygon' else [g] for l,g in cropped.items()}
        def contacts(shape, layers):
            return {(l,i) for l in layers for i,g in enumerate(components[l]) if g.distance(shape)<.00001}
        graph = defaultdict(set)
        for o in objects:
            if o['net']=='GND' and len(o['layers'])==2:
                ids = contacts(Point(o['at']),o['layers'])
                for node in ids: graph[node].update(ids)
        reached = set()
        todo = list(contacts(Point(pads[seed]['at']),['F.Cu']))
        while todo:
            n = todo.pop()
            if n not in reached:
                reached.add(n)
                todo.extend(graph[n]-reached)
        hits = {n:bool(contacts(Point(p['at']),p['layers'])&reached) for n,p in pads.items() if p['net']=='GND'}
        return hits, components, reached

    hits, components, reached = reach(box(100,70,200,140),'U2.11')
    entry = {'path':str(path),'five_pads':{n:hits[n] for n in names},'local_returns':[]}
    if row:
        west=refs['U3'][0]<175
        for label, bounds, seed, endpoints in [
            ('LDO bypass', ((165,104,175.5,110.5) if west else (178.2,98.1,185.1,105.8)),'U3.2',['C4.2','C5.2']),
            ('Charger bypass', ((169,101,182,110.1) if west else (173,102.5,182,110.1)),'U2.11',['C3.2','C8.2','C2.2','R19.2']),
            ('Display rail return', ((165,94,185.1,110.5) if west else (178.2,94,185.1,105.8)),'U3.2',['C9.2','U4.2']),
            ('MCU bypass', (164.5,109,178.5,115.2),'C7.2',['C1.2','C6.2','U1.33','U1.15'])]:
            for radius in [0,.05,.075,.095]:
                local,_,_ = reach(box(*bounds),seed,radius)
                entry['local_returns'].append(dict(name=label,window_mm=bounds,seed=seed,erosion_radius_mm=radius,reachable={n:local.get(n) for n in endpoints}))
    report['boards'].append(entry)
    for column, layer in enumerate(['F.Cu','B.Cu']):
        ax=axes[row,column]
        for i,g in enumerate(components[layer]):
            if g.is_empty: continue
            ax.add_patch(Patch(g.exterior.coords,facecolor='#dce9dc' if (layer,i) in reached else '#e98a36',linewidth=0))
            for hole in g.interiors:ax.add_patch(Patch(hole.coords,facecolor='white',linewidth=0))
        for o in objects:
            if layer not in o['layers'] or o['kind']=='keepout':continue
            ax.add_patch(Patch(o['shape'].exterior.coords,facecolor='#428354' if o['net']=='GND' else '#626a75' if o['kind']=='pad' else '#bd554c' if layer=='F.Cu' else '#416db7',linewidth=0))
        for ref in ['U1','U2','U3','C1','C2','C3','C4','C5','C6','C7','C8','C9','R19','R14','U5','U6','J1','J2']:
            x,y,_=refs[ref];ax.text(x,y,ref,ha='center',fontsize=7,clip_on=True,bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=.2))
        for n in names:
            if not hits[n]:ax.plot(*pads[n]['at'],'o',ms=10,mfc='none',mec='#ca2525',mew=1.5)
        ax.set(xlim=(164,187),ylim=(116,94),aspect='equal',title=('A rejected merge' if not row else 'A2 current candidate')+' / '+layer+' / top view',xlabel='KiCad X / mm',ylabel='KiCad Y / mm')
        ax.grid(alpha=.15)
fig.savefig(args.output/'ground-comparison.png',dpi=170)
(args.output/'returns.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['boards'][-1],indent=2))
