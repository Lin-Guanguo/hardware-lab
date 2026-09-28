#!/usr/bin/env python3
"""Audit the saved USB C candidate; report electrical and manufacturing gates separately."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from pour_geometry import parse_path, load_pours, calibrate

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / 'hardware/records'
STEM = RECORDS / 'usb-power-return-c'
MM = .0254
spec = importlib.util.spec_from_file_location('copper_audit', Path(__file__).with_name('check-r1-copper.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def errors(value):
    if isinstance(value, list):
        for item in value:
            yield from errors(item)
    elif isinstance(value, dict):
        if 'errorType' in value:
            yield value
        else:
            yield from errors(value.get('list', []))


def load(suffix):
    return json.loads(Path(f'{STEM}-{suffix}').read_text())


def xy(p):
    return p['x'] * MM, p['y'] * MM


from gerber_geometry import flashes


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--capture', type=Path)
parser.add_argument('--gerber-dir', type=Path, required=True)
parser.add_argument('--cpl', type=Path, required=True)
args = parser.parse_args()
if args.capture:
    capture = json.loads(args.capture.read_text())
    assert capture['success']
    d = capture['result']
    assert d['project'] == {'uuid':'53006cfb7653a00a8462cb5322b8bf243b84d3b7ddbcc4abbad89751703d51b4','name':'NFC-Card-R2-USB-Power-Return-C'}
    for key, suffix in [('snapshot','snapshot.json'),('pins','pcb-pins.json'),('rules','rules.json'),('netlist','schematic.enet')]:
        Path(f'{STEM}-{suffix}').write_text(json.dumps(d[key], ensure_ascii=False, indent=2)+'\n')
    Path(f'{STEM}-bom.tsv').write_text(d['bom'])
    Path(f'{STEM}-drc.json').write_text(json.dumps({'project':d['project'],'status':'PARTIAL_USB_STUDY_NOT_FABRICATION_APPROVAL','errors':list(errors(d['drc']))},ensure_ascii=False,indent=2)+'\n')
s = load('snapshot.json')
b = json.loads((RECORDS/'usb-spaced-b-snapshot.json').read_text())
assert s['components'] == b['components'] and s['pads'] == b['pads']
assert s['polylines'] == b['polylines']
assert all(r in s['regions'] for r in b['regions']) and len(s['regions']) == len(b['regions'])+1
assert load('rules.json')['config'] == json.loads((RECORDS/'usb-spaced-b-rules.json').read_text())['config']
assert [t for t in s['lines'] if t['net'] not in ['GND','USB_VBUS']] == [t for t in b['lines'] if t['net']!='GND']
assert [v for v in s['vias'] if v['net'] not in ['GND','USB_VBUS']] == [v for v in b['vias'] if v['net']!='GND']
pads = {(c['ref'],p['number']):p for c in s['components'] for p in s['pads'] if p['id'].startswith(c['id'])}
assert len(pads)==256 and len(s['components'])==66
sch = {c['props']['Designator']:c for c in load('schematic.enet')['components'].values()}
assert all(sch[r]['pinInfoMap'][n].get('net','')==p['net'] for (r,n),p in pads.items())
bom = list(csv.DictReader(io.StringIO(Path(f'{STEM}-bom.tsv').read_text()),delimiter='\t'))
assert {r for row in bom for r in row['Designator'].split(',')} == sch.keys()
# GCT's asymmetric land calibrates rotation before any pad-to-hole measurement.
g = audit.pad_shape(pads['J1','A6'])
assert abs(g.bounds[2]-g.bounds[0]-1.1)<.003 and abs(g.bounds[3]-g.bounds[1]-.3)<.003
calibration_ok, calibration = calibrate(load_pours(s))
assert calibration_ok and len(calibration)==2
actual = audit.audit(s)
for key in ['dead_ends','floating_copper','single_layer_or_isolated_vias','screen_unexpected_copper_mm2']:
    assert not actual[key], (key,actual[key])
complete = ['USB_DP_CONN','USB_DM_CONN','USB_DP_MCU','USB_DM_MCU','USB_CC1','USB_CC2','USB_VBUS']
assert all(n not in actual['split_nets'] for n in complete)
required_ground = [('J1',n) for n in ['A1B12','B1A12','17','18','19','20']]+[('U5','3'),('U6','3'),('R1','2'),('R2','2'),('C1','2'),('C8','2'),('U1','33'),('U2','5'),('U2','11')]
labels = {f'{n}@({xy(pads[r,n])[0]:.2f},{xy(pads[r,n])[1]:.2f})' for r,n in required_ground}
assert any(labels<=set(group) for group in actual['groups']['GND'])
shapes,nodes = audit.copper(s)
# Check every active antenna region and the complete screen exclusion, including fills.
keepout_results = []
baseline_shapes, _ = audit.copper(b)
for region in b['regions']:
    if region['id']=='1c2979245a7f5d36':
        continue
    keepout = Polygon(parse_path(region['complexPolygon'],MM))
    intrusion = 0.0
    for (net,layer),parts in shapes.items():
        if net=='NFC1_TBD' or region['layer'] not in (12,layer):
            continue
        existing = unary_union(baseline_shapes.get((net,layer),[]))
        area = unary_union(parts).difference(existing).intersection(keepout).area
        intrusion += area
    assert intrusion < .00001, (region['id'],intrusion)
    keepout_results.append({'id':region['id'],'added_foreign_copper_area_mm2':intrusion})
new_vias = [v for v in s['vias'] if v['net']!='NFC1_TBD']
assert all(abs(v['holeMil']*MM-.3)<.001 and abs(v['diameterMil']*MM-.6)<.001 for v in new_vias)
hole_gaps = {}
for same in [True,False]:
    pairs = [(Point(xy(v)).buffer(v['holeMil']*MM/2).distance(audit.pad_shape(p)),i,p['id'])
             for i,v in enumerate(new_vias) for p in s['pads'] if p['layer'] in (1,2) and ((p['net']==v['net'])==same)]
    gap,i,pid = min(pairs)
    assert gap>.4
    hole_gaps['same_net' if same else 'different_net'] = {'gap_mm':gap,'via_mm':xy(new_vias[i]),'pad':pid}
# Native clearances remain authoritative; this samples actual filled copper independently.
spacing=[]
for (net,layer),gs in shapes.items():
    if net in ('NFC1_TBD','GND'):
        continue
    u=unary_union(gs)
    for (other,l),others in shapes.items():
        if other==net or l!=layer:
            continue
        spacing.append((u.distance(unary_union(others)),net,other,layer))
assert min(spacing)[0]>=.198, min(spacing)  # Polygon/arc sampling tolerance only; native rules stay 0.20 mm.
discrete=[]
for p in s['pads']:
    for layer in ([1,2] if p['layer']==12 else [p['layer']]):
        discrete.append((p['net'],layer,audit.pad_shape(p),'pad'))
for t in s['lines']:
    discrete.append((t['net'],t['layer'],LineString([(t['x1']*MM,t['y1']*MM),(t['x2']*MM,t['y2']*MM)]).buffer(t['widthMil']*MM/2),'track'))
via_clearances=[]
for v in new_vias:
    g=Point(xy(v)).buffer(v['diameterMil']*MM/2)
    via_clearances += [(g.distance(shape),v['net'],net,xy(v),kind) for net,layer,shape,kind in discrete if net!=v['net']]
minimum_via_gap=min(via_clearances)
assert minimum_via_gap[0]>=.199
# Six unchanged data vias: a connected stitch must touch copper on both faces.
via_returns=[]
for v in s['vias']:
    if v['net'] not in ('USB_DP_CONN','USB_DM_CONN'):
        continue
    distance,gv = min((math.dist(xy(v),xy(g)),xy(g)) for g in s['vias'] if g['net']=='GND')
    via_returns.append({'net':v['net'],'xy_mm':xy(v),'nearest_ground_via_mm':gv,'distance_mm':distance,'within_1p6mm_review_target':distance<=1.6})
assert len(via_returns)==6
return_geometry=[]
for net in complete[:4]:
    total=covered=0.0; worst=(0,None)
    for t in s['lines']:
        if t['net']!=net:
            continue
        reference=unary_union(shapes['GND',3-t['layer']])
        line=LineString([(t['x1']*MM,t['y1']*MM),(t['x2']*MM,t['y2']*MM)])
        total+=line.length; covered+=line.intersection(reference).length
        for i in range(math.ceil(line.length/.025)+1):
            p=line.interpolate(min(i*.025,line.length));distance=p.distance(reference)
            if distance>worst[0]:worst=(distance,list(p.coords)[0])
    return_geometry.append({'net':net,'trace_length_sum_mm':total,'opposite_ground_projection_mm':covered,'max_sampled_lateral_gap_mm':worst[0],'worst_xy_mm':worst[1]})
# Projection is diagnostic only: pad/via antipads and finite obstacles are counted.
counts=collections.Counter((e['errorType'],e['errorObjType']) for e in load('drc.json')['errors'])
assert counts['Clearance Error in the same footprint','Board Outline to SMD Pad']==12
assert counts['Physical Error','Via Size']==4
assert all(k[0]=='Connection Error' or k in [('Clearance Error in the same footprint','Board Outline to SMD Pad'),('Physical Error','Via Size')] for k in counts)
# Same-version Gerber independently establishes the current 0.20 mm library gap.
gdir=args.gerber_dir
copper=flashes((gdir/'Gerber_TopLayer.GTL').read_text())
mask={layer:flashes((gdir/name).read_text()) for layer,name in [(1,'Gerber_TopSolderMaskLayer.GTS'),(2,'Gerber_BottomSolderMaskLayer.GBS')]}
j1=[]
for (ref,num),p in pads.items():
    if ref!='J1':continue
    matches=[f for f in copper if math.dist(f[:2],xy(p))<.002]
    assert len(matches)==1
    x,y,g=matches[0]
    expected=audit.pad_shape(p)
    assert max(abs(a-z) for a,z in zip(g.bounds,expected.bounds))<.002
    m=[f for f in mask[1] if math.dist(f[:2],xy(p))<.002]
    assert len(m)==1
    j1.append({'number':num,'net':p['net'],'x':x,'y':y,'bounds':g.bounds,'mask_bounds':m[0][2].bounds,'smt':not p['hole']})
outline=(gdir/'Gerber_BoardOutlineLayer.GKO').read_text()
chains=[];chain=[]
for x,y,op in re.findall(r'G0[123]X(-?\d+)Y(-?\d+)(?:I-?\d+J-?\d+)?D0([12])\*',outline):
    pt=(int(x)/1e6,int(y)/1e6)
    if op=='2':
        if chain:chains.append(chain)
        chain=[pt]
    else:chain.append(pt)
if chain:chains.append(chain)
assert len(chains)==2 and chains[0][0]==chains[0][-1] and chains[1][0]!=chains[1][-1]
notch=chains[1];back=min(x for x,y in notch);span=max(y for x,y in notch if abs(x-back)<1e-6)-min(y for x,y in notch if abs(x-back)<1e-6)
front=max(p['x'] for p in j1 if not p['smt']);smt=[p for p in j1 if p['smt']]
gaps=[back-p['bounds'][2] for p in smt]
assert len(smt)==12 and max(gaps)-min(gaps)<.00001 and .199<min(gaps)<.201
mask_bridges=[max(a['mask_bounds'][1],b['mask_bounds'][1])-min(a['mask_bounds'][3],b['mask_bounds'][3]) for a,b in zip(sorted(smt,key=lambda p:p['y']), sorted(smt,key=lambda p:p['y'])[1:])]
# Every new USB via is tented in both exported mask layers (no opening at its drill).
mask_hole=[];open_vias=[]
for v in new_vias:
    hole=Point(xy(v)).buffer(v['holeMil']*MM/2)
    for layer,fs in mask.items():
        if any(f[2].contains(Point(xy(v))) for f in fs):open_vias.append({'xy_mm':xy(v),'layer':layer})
        mask_hole += [hole.distance(f[2]) for f in fs]
assert not open_vias and min(mask_hole)>.3
drill=(gdir/'Drill_PTH_Through.DRL').read_text()
tools={int(n):float(d) for n,d in re.findall(r'T(\d+)C([\d.]+)',drill)}
slots=[];tool=None
for line in drill.splitlines():
    match=re.fullmatch(r'T(\d+)',line)
    if match:tool=int(match[1])
    match=re.fullmatch(r'X([\d.]+)Y([\d.]+)G85X([\d.]+)Y([\d.]+)',line)
    if match:
        x1,y1,x2,y2=map(float,match.groups());diameter=tools[tool]
        slots.append({'ends_mm':[[x1,y1],[x2,y2]],'width_mm':diameter,'length_mm':math.dist((x1,y1),(x2,y2))+diameter})
assert len(slots)==4 and all(abs(p['width_mm']-.6)<.00001 for p in slots)
assert sorted(round(p['length_mm'],3) for p in slots)==[1.4,1.4,1.8,1.8]
cpl_rows=csv.DictReader(io.StringIO(args.cpl.read_text(encoding='utf-16')),delimiter='\t')
cpl_j1=next(row for row in cpl_rows if row['Designator']=='J1')
report={'status':'USB_LOCAL_CONNECTIVITY_CHECKED_FREEZE_BLOCKED','counts':{'components':66,'component_pins':256,'pads':len(s['pads']),'tracks':len(s['lines']),'vias':len(s['vias']),'pours':len(s['pours']),'bom_groups':len(bom)},
 'unchanged_vs_b':['components','pads','schematic pin nets','BOM references','all signal and NFC copper','board outlines','original antenna/screen keepouts','native rules'],
 'complete_nets':complete,'usb_u1_u2_ground_same_physical_component':True,'floating_copper':actual['floating_copper'],'dead_ends':actual['dead_ends'],'single_face_vias':actual['single_layer_or_isolated_vias'],
 'pour_unit_calibration':calibration,'antenna_and_screen_keepout_checks':keepout_results,'hole_to_smt_copper_mm':hole_gaps,'minimum_sampled_non_nfc_copper_spacing':min(spacing),'minimum_usb_via_to_other_discrete_copper':minimum_via_gap,'via_counts_by_net':dict(collections.Counter(v['net'] for v in s['vias'])),
 'six_data_via_returns':via_returns,'return_projection_diagnostic':return_geometry,
 'return_limit':'Connected two-face ground, not an uninterrupted reference plane. Projection includes pad/via antipads; no 95% pass claim or impedance/ESD test claim.',
 'native_drc':[{'category':k,'kind':t,'count':n} for (k,t),n in sorted(counts.items())], 'split_or_unrouted_nets':sorted(actual['split_nets']),
 'manufacturing':{'gerber_outline_chains':len(chains),'closed_outer_and_open_library_notch':True,'library_notch_back_x_mm':back,'library_notch_sidewall_span_mm':span,'front_slot_row_x_mm':front,'library_notch_back_v_mm':front-back,'smt_front_v_mm':front-smt[0]['bounds'][2],'smt_rear_v_mm':front-smt[0]['bounds'][0],'pad_to_library_notch_mm':min(gaps),'library_back_offset_from_gct_4p6_mm':4.6-(front-back),'j1_soldermask_min_bridge_mm':min(mask_bridges),'usb_via_mask_openings':open_vias,'usb_via_hole_to_any_mask_opening_min_mm':min(mask_hole),'cpl_j1':{k:cpl_j1[k] for k in ['Mid X','Mid Y','Ref X','Ref Y','Rotation']},'j1_pads':j1,'plated_slots':slots},
 'open_gates':['VBUS protection clamp versus U1/U2 ratings not selected; both branches still directly share the unprotected input.','Battery current ratings and load peak/current-limit policy remain unknown.','The 1.95 mm local data-to-ground-via distance is a review clue, not a proven defect. Geometric return paths are verified; impedance, ESD and USB performance remain untested.','Closed manufacturing notch, GCT body fit versus shifted library back edge, corner relief, tolerances and factory acceptance unresolved.','Four retained NFC lead vias violate the unchanged via-size rule. Full-board routing, online DFM and physical tests remain open.'],
 'gerber_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(gdir.iterdir()) if p.is_file()}}
Path(f'{STEM}-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Render from actual filled copper; signal traces remain visibly distinct from their reference.
fig,axes=plt.subplots(2,1,figsize=(16,10))
for ax,layer in zip(axes,[1,2]):
    for (net,l),parts in shapes.items():
        if l!=layer:continue
        merged=unary_union(parts)
        for g in getattr(merged,'geoms',[merged]):
            if not hasattr(g,'exterior'):continue
            ax.fill(*g.exterior.xy,color='#b8e2cc' if net=='GND' else '#d86742' if net=='USB_VBUS' else '#5578ba',alpha=.9)
            for hole in g.interiors:ax.fill(*hole.xy,color='white')
    for v in s['vias']:ax.add_patch(plt.Circle(xy(v),v['holeMil']*MM/2,color='white'))
    for c in s['components']:
        x,y=xy(c)
        if 42<x<83 and 12<y<33:ax.text(x,y,c['ref'],fontsize=7)
    ax.add_patch(Rectangle((69.5,17.8),4,2.7,fill=False,ec='#aa5728',ls=':'))
    ax.set(xlim=(42,83),ylim=(33,12),aspect='equal',title=f'Actual filled copper / layer {layer}');ax.grid(alpha=.12)
fig.suptitle('USB Power / Return C — local study, NOT FOR FABRICATION',fontsize=14)
fig.text(.5,.012,'Green = GND; orange = VBUS; blue = other nets. Dotted box = protection planning area; no part/footprint selected.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.035,1,.95));fig.savefig(f'{STEM}-review.png',dpi=170);plt.close(fig)
# Factory evidence: dimensioned library geometry and enlarged copper/mask/edge detail.
fig,axes=plt.subplots(1,2,figsize=(13,7),gridspec_kw={'width_ratios':[1.15,1]})
cy=(min(p['y'] for p in j1 if not p['smt'])+max(p['y'] for p in j1 if not p['smt']))/2
ax=axes[0]
for p in j1:
    shape=next(f[2] for f in copper if math.dist(f[:2],(p['x'],p['y']))<.002)
    coords=list(shape.exterior.coords);ax.fill([y-cy for x,y in coords],[front-x for x,y in coords],color='#be8c44',alpha=.7)
for slot in slots:
    shape=LineString(slot['ends_mm']).buffer(slot['width_mm']/2)
    coords=list(shape.exterior.coords);ax.fill([y-cy for x,y in coords],[front-x for x,y in coords],color='white',edgecolor='#777',lw=.6)
ax.plot([y-cy for x,y in notch],[front-x for x,y in notch],color='#be4d42',lw=2,label='Current library open outline')
ax.axhline(4.6,color='#256885',ls='--',label='GCT pad-front / recommended back datum')
ax.axhline(front-82.899999,color='#777',ls=':',label='Existing straight outer edge')
ax.annotate('',xy=(-span/2,1.1),xytext=(span/2,1.1),arrowprops={'arrowstyle':'<->'})
ax.text(0,1.35,f'Sidewall span {span:.5f} mm',ha='center')
ax.text(0,2.6,f'Current back v={front-back:.5f}\nPad front v={front-smt[0]["bounds"][2]:.5f}\nNominal gap {min(gaps):.5f} mm\nSlots 0.60 x 1.40 / 1.80 mm',ha='center',fontsize=10)
ax.set(xlim=(-6.7,6.7),ylim=(-2.2,7),aspect='equal',xlabel='u across connector / mm',ylabel='v into PCB from front slot row / mm',title='Current C Gerber, same geometry as A/B')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.10),fontsize=8)
ax=axes[1]
for p in smt:
    if 24.0<p['y']<26.9:
        for bounds,col,alpha in [(p['mask_bounds'],'#8fc6aa',.5),(p['bounds'],'#be8c44',.8)]:
            x0,y0,x1,y1=bounds;ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color=col,alpha=alpha))
        ax.text(75.35,p['y'],p['number'],ha='right',va='center',fontsize=9)
ax.axvline(back,color='#be4d42',label='Library back edge');ax.axvline(front-4.6,color='#256885',ls='--',label='GCT back datum')
ax.annotate('',xy=(smt[0]['bounds'][2],24.0),xytext=(back,24.0),arrowprops={'arrowstyle':'<->'})
ax.text(76.62,23.84,f'{min(gaps):.5f} mm copper gap',ha='center',fontsize=9)
ax.text(76.25,27.25,f'Min mask bridge {min(mask_bridges):.5f} mm\nMask expansion ~0.0508 mm / side',ha='center',fontsize=9)
ax.set(xlim=(75.05,77.35),ylim=(27.65,23.55),aspect='equal',xlabel='PCB x / mm',ylabel='PCB y / mm',title='Copper / mask opening / nominal edge')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.10),fontsize=8)
fig.suptitle('USB4500 factory review — open outline and fit unresolved',fontsize=14)
fig.tight_layout(rect=(0,.08,1,.95));fig.savefig(f'{STEM}-factory.png',dpi=180);plt.close(fig)
print(json.dumps({k:v for k,v in report.items() if k not in ['manufacturing','gerber_sha256','unchanged_vs_b']},ensure_ascii=False,indent=2))
