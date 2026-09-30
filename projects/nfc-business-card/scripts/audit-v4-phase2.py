#!/usr/bin/env python3
"""Audit native saved routing and filled copper without changing either candidate."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

import importlib.util
_spec = importlib.util.spec_from_file_location("trial_audit", Path(__file__).with_name("audit-v4-trial.py"))
_trial = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_trial)
measured_path = _trial.measured_path
from kicad_sexpr import children
from v4_geometry import geometry, filled_ground


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--label', default='V4 phase 2')
    ap.add_argument('--include-service', action='store_true')
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    data = geometry(a.board)
    board, pads, objects, refs = data
    pairs = [('C8.1','U2.10'),('C8.2','U2.11'),('C2.1','U2.1'),('C3.1','U2.2'),('C3.1','BP.1'),('J1.A4B9','C8.1'),('C4.1','U3.1'),('C4.2','U3.2'),('C5.1','U3.5'),('C5.2','U3.2'),('C1.1','U1.32'),('C7.1','U1.30'),('C6.1','U1.28'),('C10.1','L1.1'),('L1.2','Q1.3'),('Q1.2','R15.1'),('R15.2','C10.2'),('L1.2','D1.2'),('D1.1','C12.1'),('C12.2','C10.2'),('D1.2','C11.1'),('C11.2','D2.2'),('D2.2','D3.1'),('D3.2','C13.1'),('J2.2','Q1.1'),('J2.3','Q1.2'),('U1.36','J2.13'),('U1.37','J2.14'),('U1.38','J2.12'),('U1.39','J2.11'),('U1.41','J2.10'),('U1.24','J2.9'),('U1.51','TP4.1'),('U1.53','TP3.1'),('U1.34','R4.1'),('U1.35','R3.1')]
    pairs = [(s, {'R4.1':'R4.2', 'R3.1':'R3.2'}.get(e,e)) for s,e in pairs]
    pairs += [('U5.1','R3.1'),('U5.2','R4.1'),('J1.A6','U5.1'),('J1.A7','U5.2'),('U4.6','J2.15'),('C12.1','R16.1'),('R16.2','J2.21'),('C13.1','J2.23')]
    pairs += [(f'C{c}.1',f'J2.{p}') for c,p in [(14,4),(15,5),(16,16),(17,18),(18,19),(19,20),(20,22),(21,23),(22,24)]]
    if a.include_service:
        pairs += [('U1.40','TP5.1'),('U1.3','SW1.2'),('U1.4','SW2.2'),('U1.5','SW3.2'),('U2.7','U1.19'),('U2.8','U1.16'),('U2.9','U1.20'),('U2.3','U1.21'),('U2.4','U1.22'),('U1.27','U4.3'),('J1.A5','R1.1'),('J1.B5','R2.1'),('U1.11','C25.2'),('U1.10','R23.1'),('C3.1','Q2.2'),('C5.1','C9.1'),('C5.1','TP2.1')]
    report = {'board':str(a.board), 'scope':'Saved copper centerlines plus pad-center contacts. Zones excluded from path lengths; ground connectivity includes actual filled zones. Reference gaps are projected geometry, not an EMC pass.', 'tracks':len(children(board,'segment')), 'vias':len(children(board,'via')), 'paths':[]}
    for start,end in pairs:
        if start not in pads or end not in pads:
            report.setdefault('unavailable_endpoints', []).append([start, end])
            continue
        if pads[start]['net'] == pads[end]['net']:
            report['paths'].append({'start':start,'end':end,'net':pads[start]['net'], 'path':measured_path(data,start,end)})
    planes = {l:filled_ground(board,l) for l in ('F.Cu','B.Cu')}
    copper = {l:unary_union([planes[l],*[o['shape'] for o in objects if o['net']=='GND' and l in o['layers']]]) for l in planes}
    components={l:list(g.geoms) if g.geom_type=='MultiPolygon' else [g] for l,g in copper.items()}
    def contact_ids(shape,layers):
        return {(l,i) for l in layers for i,c in enumerate(components[l]) if c.distance(shape)<.002}
    links=defaultdict(set)
    for o in objects:
        if o['net']=='GND' and len(o['layers'])==2:
            ids=contact_ids(o['shape'],o['layers'])
            for i in ids: links[i].update(ids)
    todo=list(contact_ids(pads['U2.11']['shape'],['F.Cu']))
    reached=set()
    while todo:
        node=todo.pop()
        if node not in reached:
            reached.add(node)
            todo.extend(links[node]-reached)
    report['ground_pad_to_U2_EP']={n:bool(contact_ids(p['shape'],p['layers'])&reached) for n,p in pads.items() if p['net']=='GND'}
    report['ground_components_not_reaching_U2_EP']=[{'layer':l,'area_mm2':round(g.area,5)} for l,cs in components.items() for i,g in enumerate(cs) if (l,i) not in reached]
    # Clip returns to the display area so whole-board connectivity cannot hide a detour.
    window = box(155.8, 82, 185.5, 105.8)
    report['display_local_return'] = {'window_mm': list(window.bounds), 'sensitivity': [],
        'scope': 'Copper erosion is a width-sensitivity probe, not an impedance or manufacturing rule. Thermal spokes may disconnect at their half-width.'}
    return_pads = ['C12.2', 'D2.1', 'C13.2', 'R15.2', 'J2.17'] + [f'C{i}.2' for i in range(14,23)]
    for radius in [0, .05, .075, .095, .1]:
        local = {l: g.intersection(window).buffer(-radius) for l,g in copper.items()}
        pieces = {l: list(g.geoms) if g.geom_type == 'MultiPolygon' else [g] for l,g in local.items()}
        def local_ids(point, layers):
            return {(l,i) for l in layers for i,g in enumerate(pieces[l]) if g.distance(point) < .00001}
        adjacency = defaultdict(set)
        for obj in objects:
            if obj['net'] == 'GND' and len(obj['layers']) == 2:
                ids = local_ids(obj['shape'].centroid, obj['layers'])
                for node in ids: adjacency[node].update(ids)
        pending = list(local_ids(Point(pads['C10.2']['at']), ['F.Cu']))
        reached_local = set()
        while pending:
            node = pending.pop()
            if node not in reached_local:
                reached_local.add(node)
                pending.extend(adjacency[node] - reached_local)
        report['display_local_return']['sensitivity'].append({'erosion_radius_mm': radius,
            'reachable_to_C10_ground': {n: bool(local_ids(Point(pads[n]['at']), ['F.Cu']) & reached_local) for n in return_pads}})
    report['reference_gaps']=[]
    nets={pads[n]['net'] for n in ('U1.36','U1.37','U1.38','U1.39','U1.41','U1.24','U1.51','U1.53','U1.34','U1.35')}
    for net in sorted(nets):
        for layer,other in (('F.Cu','B.Cu'),('B.Cu','F.Cu')):
            lines=unary_union([LineString(o['points']) for o in objects if o['kind']=='track' and o['net']==net and o['layers']==[layer]])
            gap=lines.difference(copper[other])
            pieces=list(gap.geoms) if hasattr(gap,'geoms') else [gap]
            report['reference_gaps'].append({'net':net,'layer':layer,'length_mm':round(lines.length,3),'outside_opposite_ground_mm':round(gap.length,3),'largest_gap_mm':round(max((g.length for g in pieces),default=0),3)})
    violations=[]
    for i,x in enumerate(objects):
        if x['kind']=='keepout':continue
        for y in objects[i+1:]:
            if y['kind']=='keepout' or x['net']==y['net'] or not set(x['layers'])&set(y['layers']):continue
            if x['kind']==y['kind']=='pad' and x['name'].split('.')[0]==y['name'].split('.')[0]:continue
            gap=x['shape'].distance(y['shape'])
            if gap<.199:violations.append({'a':x['name'],'b':y['name'],'gap_mm':round(gap,6)})
    report['external_copper_clearance_failures']=violations
    (a.output/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,bounds in [('critical',(150,188,124,81)),('display',(150,186,106,81)),('power-usb',(160,193,120,98)),('overview',(110,194,130,78))]:
        height=7*(bounds[2]-bounds[3])/(bounds[1]-bounds[0])+1
        fig,axes=plt.subplots(1,2,figsize=(14,height),constrained_layout=True)
        for ax,layer in zip(axes,('F.Cu','B.Cu')):
            ground=planes[layer]
            for g in (list(ground.geoms) if hasattr(ground,'geoms') else [ground]):
                if g.is_empty:continue
                ax.add_patch(Patch(list(g.exterior.coords),color='#dce9dc',linewidth=0))
                for hole in g.interiors:ax.add_patch(Patch(list(hole.coords),color='white',linewidth=0))
            for o in objects:
                if layer not in o['layers']:continue
                color='#606060' if o['kind']=='pad' else ('#c84035' if layer=='F.Cu' else '#315fb3')
                if o['net']=='GND':color='#43845a'
                if o['kind']=='keepout':ax.add_patch(Patch(list(o['shape'].exterior.coords),fill=False,edgecolor='#d28922',hatch='///',linewidth=.6))
                else:ax.add_patch(Patch(list(o['shape'].exterior.coords),color=color,linewidth=0))
            for ref,(x,y,_) in refs.items():
                if bounds[0]<x<bounds[1] and bounds[3]<y<bounds[2]:ax.text(x,y,ref,ha='center',va='center',fontsize=6,bbox=dict(facecolor='white',alpha=.7,edgecolor='none',pad=.3))
            ax.set(xlim=bounds[:2],ylim=bounds[2:],aspect='equal',title=f'{layer} / {a.label} / NOT FOR FABRICATION',xlabel='KiCad X (mm)',ylabel='KiCad Y (mm)')
            ax.grid(alpha=.18)
        fig.savefig(a.output/f'{name}.png',dpi=160)
        plt.close(fig)
    print(json.dumps({k:report[k] for k in ('tracks','vias','ground_components_not_reaching_U2_EP','external_copper_clearance_failures')},indent=2))


if __name__=='__main__':main()
