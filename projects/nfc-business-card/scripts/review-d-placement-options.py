#!/usr/bin/env python3
"""Compare offline placement and optional feature-removal hypotheses against immutable D pad geometry."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PlotPolygon
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from pour_geometry import parse_path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / 'hardware/records'
SOURCE = RECORDS / 'board-review-d-snapshot.json'
SHA = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert SHA == 'b41283e216670f814a63f064995077f8df891c49a579c98a16db24af93236a0c', 'Reassess candidates against the changed baseline.'
s = json.loads(SOURCE.read_text())
spec = importlib.util.spec_from_file_location('copper_audit', Path(__file__).with_name('check-r1-copper.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
cs = {c['ref']: c for c in s['components']}
pads = {(c['ref'], p['number']): p for c in s['components'] for p in s['pads'] if p['id'].startswith(c['id'])}
# Pad envelopes are screening obstacles, not verified physical courtyards.
envelopes = {r: unary_union([audit.pad_shape(p) for (ref, _), p in pads.items() if ref == r]).envelope for r in cs}
owned_ids = {p['id'] for p in pads.values()}
for p in s['pads']:
    if p['id'] not in owned_ids:
        envelopes['standalone:' + p['number']] = audit.pad_shape(p).envelope
outline = Polygon(parse_path(next(p['polygon']['polygon'] for p in s['polylines'] if p['layer'] == 11), .0254))
keepouts = [box(0,17,39.62,52), box(56.5,0,69.5,4.96), box(63.65,4.96,65.35,6.25)]
charger = ['U2','C2','C3','C8','R5','R6','R7','R8','R9']
boost = ['U4','C9','C10','R13','L1','Q1','R14','R15','D1','D2','D3','C11','C12','R16','C13']
charger_links = [('U2','7','U1','19'),('U2','8','U1','16'),('U2','9','U1','20'),('U2','3','U1','21'),('U2','4','U1','22'),('U2','1','U3','1'),('U2','10','J1','B4A9'),('U2','6','R19','1')]
boost_links = [('Q1','1','J2','2'),('R15','1','J2','3'),('D3','2','J2','23'),('R16','2','J2','21'),('U4','1','U3','5'),('U4','3','U1','27'),('C10','1','J2','15')]
options = [
    ('charger-turn', charger, (45.72,19.304), 270, 4, 0, charger_links),
    ('boost-loose', boost, (71,37), 0, .5, -3.5, boost_links),
    ('boost-tight', boost, (71,37), 0, -.5, -6, boost_links),
    ('charger-ntc-fixed', charger, (45.72,19.304), 270, 1.5, 3.5, charger_links),
]

def xy(p):
    return (p['x']*.0254, p['y']*.0254)


def transformed(point, origin, angle, dx, dy):
    x,y = point[0]-origin[0], point[1]-origin[1]
    t = math.radians(angle)
    return (origin[0]+math.cos(t)*x-math.sin(t)*y+dx,
            origin[1]+math.sin(t)*x+math.cos(t)*y+dy)


report = {'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': SHA,
          'status': 'OFFLINE_PLACEMENT_HYPOTHESES_NOT_ROUTED',
          'limitations': ['Pad envelopes only; no verified body/courtyard/height/paste model.',
                         'Existing tracks, vias and pours deliberately excluded: affected routes would need rebuilding.',
                         'No native DRC, return-path, thermal, protection, assembly or manufacturing validation.',
                         'Selected endpoint distances are geometric proxies, not realizable routes or predicted via counts.',
                         'Options are evaluated independently, not as a combined board.'], 'options': []}
layouts = [envelopes]
for name, refs, origin, angle, dx, dy, links in options:
    new = {r: affinity.translate(affinity.rotate(envelopes[r], angle, origin=origin), dx, dy) for r in refs}
    companion = {}
    if name == 'charger-turn':
        ntc = next(p for p in s['pads'] if p['number'] == 'NTC')
        nx,ny = xy(ntc)
        companion['NTC'] = {'before_mm':[nx,ny], 'after_mm':[46.5,24.2]}
        new['standalone:NTC'] = affinity.translate(envelopes['standalone:NTC'],46.5-nx,24.2-ny)
    moved = unary_union(list(new.values()))
    fixed = unary_union([g for r,g in envelopes.items() if r not in new])
    nearest = min((g.distance(envelopes[f]),r,f) for r,g in new.items() for f in envelopes if f not in new)
    distances = []
    for r,n,f,fn in links:
        old = xy(pads[r,n]); target = xy(pads[f,fn]); newpoint = transformed(old,origin,angle,dx,dy)
        distances.append({'from': f'{r}.{n}', 'to': f'{f}.{fn}', 'net': pads[r,n]['net'],
                          'before_mm': math.dist(old,target), 'after_mm': math.dist(newpoint,target)})
    # A rigid transform must preserve every intra-group pad distance.
    group = [xy(p) for (r,n),p in pads.items() if r in refs]
    delta = max(abs(math.dist(p,q)-math.dist(transformed(p,origin,angle,dx,dy),transformed(q,origin,angle,dx,dy))) for p in group for q in group)
    assert delta < 1e-10
    before = sum(d['before_mm'] for d in distances); after = sum(d['after_mm'] for d in distances)
    row = {'name':name,'refs':refs,'rotation_in_snapshot_xy_degrees':angle,'origin_mm':origin,'translation_mm':[dx,dy],
           'companion_pad_moves':companion,
           'centres_after_mm':{r: transformed(xy(cs[r]),origin,angle,dx,dy) for r in refs},
           'min_moved_to_fixed_pad_envelope_gap_mm':nearest[0], 'nearest_pair':nearest[1:],
           'inside_outline_with_0p2mm_screen':outline.buffer(-.2).covers(moved),
           'exclusion_overlap_mm2': moved.intersection(unary_union(keepouts)).area,
           'max_internal_pad_distance_change_mm':delta,'selected_connections':distances,
           'selected_distance_sum_before_mm':before,'selected_distance_sum_after_mm':after,
           'selected_distance_sum_reduction_percent':100*(before-after)/before}
    assert row['inside_outline_with_0p2mm_screen'] and row['exclusion_overlap_mm2'] == 0
    row['minimum_internal_envelope_gap_mm'] = min(g.distance(h) for r,g in new.items() for f,h in new.items() if r < f)
    if name.startswith('charger'):
        bp = xy(next(p for p in s['pads'] if p['number'] == 'BP'))
        bat = xy(pads['U2','2'])
        row['battery_pad_to_U2_BAT_distance_mm'] = {'before':math.dist(bp,bat), 'after':math.dist(bp,transformed(bat,origin,angle,dx,dy))}
    assert nearest[0] > (.2 if name == 'boost-tight' else .5)
    report['options'].append(row)
    layouts.append(envelopes | new)

adc_refs = ['Q2','Q3','R20','R21','R22','R23','C25']
adc_nets = ['BAT_DIV_SUPPLY','BAT_SWITCH_GATE','BAT_MEAS_EN','BAT_ADC_SENSE']
adc_area = unary_union([envelopes[r] for r in adc_refs]).envelope
adc_routes = {}
for net in adc_nets:
    lines = [t for t in s['lines'] if t['net'] == net]
    adc_routes[net] = {'segments':len(lines),'vias':sum(v['net'] == net for v in s['vias']),
                       'explicit_track_length_mm':sum(math.hypot(t['x1']-t['x2'],t['y1']-t['y2'])*.0254 for t in lines)}
report['optional_battery_adc_removal'] = {'refs':adc_refs,'pad_envelope_bounds_mm':adc_area.bounds,
    'pad_envelope_area_mm2':adc_area.area,'dedicated_routes':adc_routes,
    'remaining_components_if_removed':len(cs)-len(adc_refs),
    'limits':['No removal executed; user described a conditional fallback.',
              'Bounding rectangle is not entirely reclaimed routing area.',
              'Shared BAT_PACK_TBD and GND require branch-level editing; their whole nets must not be deleted.',
              'Loses this external MCU-controlled battery-voltage measurement path; no replacement capability assumed.',
              'Does not itself repair C8 ground or screen boost routing.']}

fig, axes = plt.subplots(1,3,figsize=(16,8),sharex=True,sharey=True)
for index,(ax,layout,title) in enumerate(zip(axes,layouts[:3],['D baseline','Charger turn + shift hypothesis','Boost shift: limited benefit'])):
    ax.plot(*outline.exterior.xy,color='#444444',linewidth=1)
    for g in keepouts:
        ax.add_patch(PlotPolygon(list(g.exterior.coords),facecolor='#ddd',alpha=.8))
    selected = [] if index == 0 else options[index-1][1]
    for r,g in layout.items():
        color = '#d89431' if r in charger else '#278990' if r in boost else '#bbbbbb'
        ax.add_patch(PlotPolygon(list(g.exterior.coords),facecolor=color,alpha=.55,edgecolor=color))
        if r in selected or r in ['U1','U2','U3','J1','J2','SW1','SW2','SW3','Q1','C8']:
            x,y=g.centroid.coords[0];ax.text(x,y-.6,r,fontsize=7,ha='center')
    if index:
        row=report['options'][index-1]
        ax.text(40,49,f"Selected endpoint sum: {row['selected_distance_sum_before_mm']:.1f} -> {row['selected_distance_sum_after_mm']:.1f} mm\nPad-envelope gap to fixed parts: {row['min_moved_to_fixed_pad_envelope_gap_mm']:.2f} mm",fontsize=8)
        if index == 1:
            ax.text(40,45.5,'Requires moving the NTC spare pad to (46.5, 24.2)',fontsize=8,color='#995500')
            g=layout['standalone:NTC']; ax.text(g.centroid.x,g.centroid.y,'NTC',fontsize=7)
    ax.set_title(title); ax.set_xlim(38,84);ax.set_ylim(51,0);ax.set_aspect('equal');ax.set_xlabel('x / mm');ax.grid(alpha=.15)
axes[0].set_ylabel('y / mm')
fig.suptitle('D placement study | orange: charger | teal: display power | rectangles: PAD envelopes\nGeometric screening only; no routed candidate and no fabrication approval',fontsize=12)
fig.tight_layout(rect=(0,0,1,.94))
fig.savefig(RECORDS/'d-placement-options.png',dpi=150)
(RECORDS/'d-placement-options.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for row in report['options']:
    print(row['name'],round(row['selected_distance_sum_before_mm'],3),round(row['selected_distance_sum_after_mm'],3),round(row['selected_distance_sum_reduction_percent'],1),'%',row['nearest_pair'],round(row['min_moved_to_fixed_pad_envelope_gap_mm'],3))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
