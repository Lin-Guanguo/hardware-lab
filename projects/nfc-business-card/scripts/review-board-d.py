#!/usr/bin/env python3
"""Audit D's actual copper and same-version manufacturing outputs."""
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
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from gerber_geometry import flashes, positive_regions
from pour_geometry import parse_path, load_pours, calibrate

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / 'hardware/records'
STEM = RECORDS / 'board-review-d'
MM = .0254
spec = importlib.util.spec_from_file_location('copper_audit', Path(__file__).with_name('check-r1-copper.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def errors(value):
    if isinstance(value, list):
        for v in value:
            yield from errors(v)
    elif isinstance(value, dict):
        if 'errorType' in value:
            yield value
        else:
            yield from errors(value.get('list', []))


def xy(p):
    return p['x']*MM, p['y']*MM


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--capture', type=Path, help='Fresh native API capture; defaults to the saved D records.')
ap.add_argument('--gerber-dir', type=Path, required=True)
ap.add_argument('--cpl', type=Path, required=True)
a = ap.parse_args()
if a.capture:
    capture = json.loads(a.capture.read_text())
    assert capture['success']
    d = capture['result']
else:
    drc_record=json.loads(Path(f'{STEM}-drc.json').read_text())
    d={'project':drc_record['project'],'drc':drc_record['errors'],'bom':Path(f'{STEM}-bom.tsv').read_text()}
    for key,suffix in [('snapshot','snapshot.json'),('pins','pcb-pins.json'),('rules','rules.json'),('netlist','schematic.enet')]:
        d[key]=json.loads(Path(f'{STEM}-{suffix}').read_text())
assert d['project'] == {'uuid':'859b1e5943e253f5bcd58e9ad5433d951b2daa27d38febc2be012f497502b89d','name':'NFC-Card-R2-Board-Review-D'}
for key, suffix in [('snapshot','snapshot.json'),('pins','pcb-pins.json'),('rules','rules.json'),('netlist','schematic.enet')]:
    Path(f'{STEM}-{suffix}').write_text(json.dumps(d[key], ensure_ascii=False, indent=2)+'\n')
Path(f'{STEM}-bom.tsv').write_text(d['bom'])
es = list(errors(d['drc']))
Path(f'{STEM}-drc.json').write_text(json.dumps({'project':d['project'],'status':'REVIEW_CANDIDATE_NOT_FOR_FABRICATION','errors':es},ensure_ascii=False,indent=2)+'\n')
s = d['snapshot']
c = json.loads((RECORDS/'usb-power-return-c-snapshot.json').read_text())
pads = {(q['ref'],p['number']):p for q in s['components'] for p in s['pads'] if p['id'].startswith(q['id'])}
sch = {q['props']['Designator']:q for q in d['netlist']['components'].values()}
assert len(s['components']) == len(sch) == 66 and len(pads) == 256
assert all(sch[r]['pinInfoMap'][n].get('net','')==p['net'] for (r,n),p in pads.items())
assert d['rules']['config'] == json.loads((RECORDS/'usb-power-return-c-rules.json').read_text())['config']
usb_signals = ['USB_DP_CONN','USB_DM_CONN','USB_DP_MCU','USB_DM_MCU','USB_CC1','USB_CC2']
for kind in ['lines','vias']:
    assert collections.Counter(json.dumps(t,sort_keys=True) for t in s[kind] if t['net'] in usb_signals) == collections.Counter(json.dumps(t,sort_keys=True) for t in c[kind] if t['net'] in usb_signals)
assert all(r in s['regions'] for r in c['regions'])
bom = list(csv.DictReader(io.StringIO(d['bom']),delimiter='\t'))
assert {r for row in bom for r in row['Designator'].split(',')} == sch.keys()
actual = audit.audit(s)
shapes, _ = audit.copper(s)
calibration_ok, calibration = calibrate(load_pours(s))
assert calibration_ok
# The asymmetric connector land checks orientation independently of its centre.
j1_shape = audit.pad_shape(pads['J1','A6'])
assert abs(j1_shape.bounds[2]-j1_shape.bounds[0]-1.1)<.003
assert abs(j1_shape.bounds[3]-j1_shape.bounds[1]-.3)<.003
antenna = []
for bounds,layers in [((56.5,0,69.5,4.96),[1,2]),((63.65,4.96,65.35,6.25),[1])]:
    keepout = box(*bounds)
    area = sum(unary_union(parts).intersection(keepout).area for (net,l),parts in shapes.items() if l in layers and net!='NFC1_TBD')
    antenna.append({'bounds_mm':bounds,'layers':layers,'foreign_copper_mm2':area})
hole_gaps = {}
for same in [True,False]:
    gap,i,pid = min((Point(xy(v)).buffer(v['holeMil']*MM/2).distance(audit.pad_shape(p)),i,p['id']) for i,v in enumerate(s['vias']) for p in s['pads'] if p['layer'] in [1,2] and ((p['net']==v['net'])==same))
    hole_gaps['same_net' if same else 'different_net'] = {'gap_mm':gap,'via_mm':xy(s['vias'][i]),'via_net':s['vias'][i]['net'],'pad':pid}
hole_hole = min((math.dist(xy(v),xy(w))-(v['holeMil']+w['holeMil'])*MM/2,i,j) for i,v in enumerate(s['vias']) for j,w in enumerate(s['vias']) if i<j)
counts=collections.Counter((e['errorType'],e['errorObjType']) for e in es)
outline=Polygon(parse_path(next(p['polygon']['polygon'] for p in s['polylines'] if p['layer']==11),MM))
assert outline.is_valid and len([p for p in s['polylines'] if p['layer']==11])==1
copper=flashes((a.gerber_dir/'Gerber_TopLayer.GTL').read_text())
mask={l:flashes((a.gerber_dir/name).read_text()) for l,name in [(1,'Gerber_TopSolderMaskLayer.GTS'),(2,'Gerber_BottomSolderMaskLayer.GBS')]}
paste_text=(a.gerber_dir/'Gerber_TopPasteMaskLayer.GTP').read_text()
paste=flashes(paste_text)+positive_regions(paste_text)
manufacturing={}
for ref in ['J1','J2','U1','U2','U3','U4']:
    groups={kind:[] for kind in ['copper','mask','paste']}
    for (r,n),p in pads.items():
        if r!=ref:continue
        for kind,fs in [('copper',copper),('mask',mask[1]),('paste',paste)]:
            matches=[g for x,y,g in fs if audit.pad_shape(p).contains(g.representative_point())] if kind=='paste' else [g for x,y,g in fs if math.dist((x,y),xy(p))<.002]
            if p['hole'] and kind=='paste':continue
            assert len(matches)==1,(ref,n,kind,len(matches))
            if kind=='copper':assert max(abs(x-y) for x,y in zip(matches[0].bounds,audit.pad_shape(p).bounds))<.002
            groups[kind].append((n,matches[0]))
    manufacturing[ref]={kind:{'apertures':len(v),'minimum_gap_mm':min(g.distance(h) for i,(_,g) in enumerate(v) for _,h in v[i+1:])} for kind,v in groups.items()}
    if ref=='U2':
        ep={k:next(g for n,g in v if n=='11') for k,v in groups.items()}
        manufacturing[ref]['exposed_pad_paste']={'copper_bounds_mm':ep['copper'].bounds,'paste_bounds_mm':ep['paste'].bounds,'area_ratio':ep['paste'].area/ep['copper'].area}
cpl = list(csv.DictReader(io.StringIO(a.cpl.read_text(encoding='utf-16')), delimiter='\t'))
assert {row['Designator'] for row in cpl} == sch.keys()
for row in cpl:
    component = next(q for q in s['components'] if q['ref']==row['Designator'])
    assert math.dist((float(row['Ref X'].removesuffix('mm')),float(row['Ref Y'].removesuffix('mm'))),xy(component)) < .002
    assert abs((float(row['Rotation'])-component['rotation']+180)%360-180) < .002
outline_text=(a.gerber_dir/'Gerber_BoardOutlineLayer.GKO').read_text();chains=[];chain=[]
for x,y,op in re.findall(r'G0[123]X(-?\d+)Y(-?\d+)(?:I-?\d+J-?\d+)?D0([12])\*',outline_text):
    pt=(int(x)/1e6,int(y)/1e6)
    if op=='2':
        if chain:chains.append(chain)
        chain=[pt]
    else:chain.append(pt)
if chain:chains.append(chain)
assert len(chains)==1 and chains[0][0]==chains[0][-1],chains
smt=[p for (r,n),p in pads.items() if r=='J1' and not p['hole']]
front=max(xy(p)[0] for (r,n),p in pads.items() if r=='J1' and p['hole'])
back=76.699035
edge_gaps=[back-g.bounds[2] for x,y,g in copper if any(math.dist((x,y),xy(p))<.002 for p in smt)]
assert len(edge_gaps)==12
open_vias=[];mask_gap=math.inf
for v in s['vias']:
    hole=Point(xy(v)).buffer(v['holeMil']*MM/2)
    for l,fs in mask.items():
        if any(g.contains(Point(xy(v))) for x,y,g in fs):open_vias.append({'via':xy(v),'layer':l})
        mask_gap=min(mask_gap,min(hole.distance(g) for x,y,g in fs))
returns=[]
for v in s['vias']:
    if v['net'] in ['USB_DP_CONN','USB_DM_CONN']:
        distance,gxy=min((math.dist(xy(v),xy(g)),xy(g)) for g in s['vias'] if g['net']=='GND')
        returns.append({'net':v['net'],'xy_mm':xy(v),'nearest_gnd_via_mm':gxy,'distance_mm':distance})
assert len(returns)==6
moved=[{'ref':q['ref'],'before_mm':[old['x']*MM,old['y']*MM,old['rotation']],'after_mm':[q['x']*MM,q['y']*MM,q['rotation']]} for q in s['components'] for old in c['components'] if q['ref']==old['ref'] and any(q[k]!=old[k] for k in ['x','y','rotation'])]
report={'status':'CONDITIONAL_BOARD_REVIEW_NOT_PRODUCTION_RELEASE','counts':{'components':len(s['components']),'component_pins':len(pads),'pads':len(s['pads']),'tracks':len(s['lines']),'vias':len(s['vias']),'pours':len(s['pours']),'bom_groups':len(bom)},'netlist_consistent':True,'same_version_cpl_positions_verified':len(cpl),'unchanged_usb_signal_copper':True,'native_rules_unchanged':True,'component_moves_from_c':moved,'native_drc':[{'category':t,'kind':k,'count':n} for (t,k),n in sorted(counts.items())],'actual_copper':actual,'pour_unit_calibration':calibration,'antenna':antenna,'hole_to_smt':hole_gaps,'minimum_via_hole_to_via_hole_mm':hole_hole,'via_counts_by_net':dict(collections.Counter(v['net'] for v in s['vias'])),'six_usb_data_via_returns':returns,'manufacturing':manufacturing,'usb_outline':{'closed_gerber_chains':len(chains),'gct_front_slot_x_mm':front,'back_x_mm':back,'back_v_mm':front-back,'sidewall_span_mm':9.24,'corner_relief_radius_assumed_mm':.25,'signed_copper_front_to_back_mm':edge_gaps,'factory_acceptance':False},'via_mask':{'openings_at_via_centres':open_vias,'hole_to_any_aperture_min_mm':mask_gap,'tenting_is_not_plugging':True},'gerber_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.gerber_dir.iterdir()) if p.is_file()},'open_decisions':['USB flush-edge lands, assumed corner relief and machining tolerance need factory acceptance.','U1 body-to-edge clearance and panel/depanel process remain conditional.','VBUS protection is not selected; load and battery ratings are incomplete.','No physical USB/ESD, power/thermal, screen, NFC/BLE or assembly measurements.']}
# A deliberate winding cut must break the coil; mere net equality is insufficient.
cut = next(i for i,t in enumerate(s['lines']) if t['net']=='NFC1_TBD' and t['layer']==2 and abs(t['x1']*MM-34)<.002 and abs(t['x2']*MM-34)<.002 and abs(t['y1']-t['y2'])*MM>15)
cut_groups = audit.audit(s, omit_line=cut)['groups']['NFC1_TBD']
assert len(cut_groups)==2
report['nfc_winding_cut_proof']={'omitted_line':cut,'line':s['lines'][cut],'groups_after_cut':cut_groups,'passed':True}
dtools={};slots=[];hits=[];active=None
for line in (a.gerber_dir/'Drill_PTH_Through.DRL').read_text().splitlines():
    tool=re.fullmatch(r'(T\d+)C([\d.]+)',line)
    if tool:dtools[tool[1]]=float(tool[2])
    if re.fullmatch(r'T\d+',line):active=line
    hit=re.fullmatch(r'X([\d.]+)Y([\d.]+)',line)
    if hit:hits.append((float(hit[1]),float(hit[2]),dtools[active]))
    slot=re.fullmatch(r'X([\d.]+)Y([\d.]+)G85X([\d.]+)Y([\d.]+)',line)
    if slot:
        x1,y1,x2,y2=map(float,slot.groups());diam=dtools[active]
        slots.append({'ends_mm':[[x1,y1],[x2,y2]],'width_mm':diam,'length_mm':math.dist((x1,y1),(x2,y2))+diam})
assert len(hits)==len(s['vias']) and len(slots)==4
assert sorted(round(v['length_mm'],3) for v in slots)==[1.4,1.4,1.8,1.8]
assert all(abs(v['width_mm']-.6)<.00001 for v in slots)
annuli=[]
for v in s['vias']:
    match=[h for h in hits if math.dist(h[:2],xy(v))<.002]
    # The retained NFC via getter differs from Excellon by one 0.1-mil tick.
    assert len(match)==1 and abs(match[0][2]-v['holeMil']*MM)<.0026
    flashes_at_hole=[g for x,y,g in copper if math.dist((x,y),xy(v))<.002]
    assert len(flashes_at_hole)==1
    x0,y0,x1,y1=flashes_at_hole[0].bounds
    annuli.append((min(x1-x0,y1-y0)-match[0][2])/2)
report['drills']={'via_hits_verified':len(hits),'minimum_diameter_mm':min(h[2] for h in hits),'native_getter_diameter_tolerance_mm':.0026,'minimum_radial_annulus_mm':min(annuli),'plated_slots':slots}
Path(f'{STEM}-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Show the whole electronic area, with both actual copper layers and exclusion edges.
fig,axs=plt.subplots(1,2,figsize=(16,10))
for ax,l in zip(axs,[1,2]):
    for (net,layer),gs in sorted(shapes.items(),key=lambda item:item[0][0]!='GND'):
        if layer!=l:continue
        for g in getattr(unary_union(gs),'geoms',[unary_union(gs)]):
            if not hasattr(g,'exterior'):continue
            ax.fill(*g.exterior.xy,color='#b7d8c7' if net=='GND' else '#d69439' if net=='NFC1_TBD' else '#c05953' if l==1 else '#5378b0',alpha=.9)
            for ring in g.interiors:ax.fill(*ring.xy,color='white')
    ax.plot(*outline.exterior.xy,color='#333',lw=.8)
    for v in s['vias']:ax.add_patch(plt.Circle(xy(v),v['holeMil']*MM/2,color='white'))
    for q in s['components']:
        ax.text(*xy(q),q['ref'],fontsize=6,ha='center')
    ax.add_patch(Rectangle((69.5,17.8),4,2.7,fill=False,ls=':',ec='#835b33'))
    ax.set(xlim=(35.5,83.5),ylim=(51.5,.3),aspect='equal',title=f'D actual copper - layer {l}');ax.grid(alpha=.1)
fig.suptitle('Board Review D - conditional candidate, NOT FOR FABRICATION')
fig.tight_layout();fig.savefig(f'{STEM}-review.png',dpi=180);plt.close(fig)
for layer in [1,2]:
    fig,ax=plt.subplots(figsize=(16,10))
    for (net,l),parts in sorted(shapes.items(),key=lambda item:item[0][0]!='GND'):
        if l!=layer:continue
        merged=unary_union(parts)
        for g in getattr(merged,'geoms',[merged]):
            if not hasattr(g,'exterior'):continue
            color='#d3e5d9' if net=='GND' else '#b77c21' if net=='NFC1_TBD' else '#b74542' if layer==1 else '#416fae'
            ax.fill(*g.exterior.xy,color=color)
            for ring in g.interiors:ax.fill(*ring.xy,color='white')
    for v in s['vias']:ax.add_patch(plt.Circle(xy(v),v['holeMil']*MM/2,color='white'))
    for q in s['components']:ax.text(*xy(q),q['ref'],fontsize=7,ha='center')
    ax.plot(*outline.exterior.xy,color='#222',lw=.9)
    ax.set(xlim=(.3,83.7),ylim=(51.7,.3),aspect='equal',xlabel='x / mm',ylabel='y / mm',title=f'D actual copper — {"top" if layer==1 else "bottom"}; front-coordinate view, NOT FOR FABRICATION')
    fig.tight_layout();fig.savefig(f'{STEM}-{"top" if layer==1 else "bottom"}.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,7))
for ax in axs:
    ax.plot(*outline.exterior.xy,color='#be4d42',lw=1.5)
    for (r,n),p in pads.items():
        if r!='J1':continue
        g=next(g for x,y,g in copper if math.dist((x,y),xy(p))<.002)
        ax.fill(*g.exterior.xy,color='#bd8b45',alpha=.8)
        ax.text(*xy(p),n,fontsize=6,ha='center',clip_on=True)
    ax.grid(alpha=.15)
axs[0].set(xlim=(74.8,83.4),ylim=(33,19),aspect='equal',title='One closed outline / unchanged lands',xlabel='PCB x / mm',ylabel='PCB y / mm')
axs[0].text(79.8,25.9,'9.24 mm\nsidewall span\n\nR0.25 relief\nASSUMED',ha='center',fontsize=10)
axs[1].set(xlim=(75.25,77.2),ylim=(27.5,24),aspect='equal',title='Copper flush to nominal back edge',xlabel='PCB x / mm')
axs[1].text(.5,-.11,f'Nominal signed gap {min(edge_gaps):.5f} mm\nFactory acceptance unresolved',transform=axs[1].transAxes,ha='center',fontsize=8)
fig.suptitle('USB4500 - 0.8 mm board / GCT v=4.60 datum / conditional machining')
fig.tight_layout();fig.savefig(f'{STEM}-factory.png',dpi=180);plt.close(fig)
print(json.dumps({k:report[k] for k in ['status','counts','native_drc','hole_to_smt','minimum_via_hole_to_via_hole_mm','antenna']},ensure_ascii=False,indent=2))
print('split',len(actual['split_nets']),'dead ends',len(actual['dead_ends']),'floating',len(actual['floating_copper']),'single-face vias',len(actual['single_layer_or_isolated_vias']))
