#!/usr/bin/env python3
"""Measure applicable R1 layout rules; keep engineering findings separate from DRC."""
import argparse
import copy
import hashlib
import json
import math
import runpy
from pathlib import Path
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from pour_geometry import parse_path

ROOT=Path(__file__).resolve().parents[1]
COPPER=runpy.run_path(str(Path(__file__).with_name('check-r1-copper.py')))
MM=.0254
xy=lambda p:[p['x']*MM,p['y']*MM]

def review(s,pins):
    audit=COPPER['audit'](s);shapes,_=COPPER['copper'](s)
    unions={k:unary_union(v)for k,v in shapes.items()}
    outline=Polygon(parse_path(next(p for p in s['polylines'] if p['layer']==11)['polygon']['polygon'],MM))
    winding=[t for t in s['lines']if t['net']=='NFC1_TBD' and t['layer']==2 and max(t['x1'],t['x2'])*MM<34.001]
    segments=[LineString([(t['x1']*MM,t['y1']*MM),(t['x2']*MM,t['y2']*MM)])for t in winding]
    w=unary_union(segments);x0,y0,x1,y1=w.bounds
    projection=outline.intersection(LineString([(20,0),(20,55)]))
    edge_offsets={'left':x0-outline.bounds[0],'bottom':y0-projection.bounds[1],'top':projection.bounds[3]-y1}
    assert all(abs(v-3)<.002 for v in edge_offsets.values())
    widths={round(t['widthMil']*MM,5)for t in winding};assert len(widths)==1
    width=next(iter(widths))
    chamfers=[]
    for g in segments:
        a,b=g.coords;dx=abs(b[0]-a[0]);dy=abs(b[1]-a[1])
        if min(dx,dy)>.01:
            assert abs(dx-dy)<.002
            chamfers.append(math.degrees(math.atan2(dy,dx)))
    assert len(chamfers)==20
    pairs=[(a,b)for i,a in enumerate(segments)for b in segments[i+1:] if not any(math.dist(x,y)<.002 for x in a.coords for y in b.coords)]
    space=min(a.distance(b)-width for a,b in pairs);assert space>.249
    # Actual coil copper, excluding its feed/crossover, must respect the whole outline.
    edge_distance=unary_union([g.buffer(width/2)for g in segments]).distance(outline.boundary)
    assert edge_distance>2.873
    bleed=[]
    for layer,region in [(1,box(56.5,0,69.5,4.96)),(2,box(56.5,0,69.5,4.96)),(1,box(63.65,4.96,65.35,6.25))]:
        for (net,l),g in unions.items():
            area=g.intersection(region).area
            if l==layer and area>1e-5:bleed.append({'net':net,'layer':l,'area_mm2':area})
    assert not bleed
    comps={c['ref']:c for c in pins}
    ground_vias=[xy(v)for v in s['vias']if v['net']=='GND']
    services=[('C1','U2','10'),('C2','U2','1'),('C3','U2','2'),('C4','U3','1'),('C5','U3','5'),('C6','U1','28'),('C7','U1','30'),('C9','U4','1'),('C10','U4','6')]
    decoupling=[]
    for cap,ic,pin in services:
        target=next(q for q in comps[ic]['pins']if q['number']==pin)
        pad=next(q for q in comps[cap]['pins']if q['net']==target['net'])
        gp=next(q for q in comps[cap]['pins']if q['net']=='GND')
        distance=math.dist(xy(pad),xy(target))
        decoupling.append({'cap':cap,'served_pin':f'{ic}.{pin}','net':target['net'],
                           'supply_pad_distance_mm':distance,'ground_via_distance_mm':min(math.dist(xy(gp),v)for v in ground_vias),
                           'DC-001':'HIGH' if distance>8 else 'MEDIUM' if distance>5 else 'PASS'})
    esd=[]
    for ref in ['U5','U6']:
        g=next(p for p in comps[ref]['pins']if p['net']=='GND')
        distances=sorted(math.dist(xy(g),v)for v in ground_vias)
        esd.append({'ref':ref,'nearest_ground_via_mm':distances[0],'ground_vias_within_3mm':sum(d<3 for d in distances)})
    # Removing the incoming TVS leg must separate connector from protected load.
    candidates=[i for i,t in enumerate(s['lines'])if t['net']=='USB_CC2' and t['layer']==1 and abs(min(t['x1'],t['x2'])*MM-73.65)<.002 and abs(max(t['x1'],t['x2'])*MM-74.09942)<.002 and abs(t['y1']*MM-25.25014)<.002 and abs(t['y2']*MM-25.25014)<.002]
    assert len(candidates)==1
    groups=COPPER['audit'](s,candidates[0])['groups']['USB_CC2']
    pinlabel=lambda ref,num:f"{num}@({xy(next(p for p in comps[ref]['pins']if p['number']==num))[0]:.2f},{xy(next(p for p in comps[ref]['pins']if p['number']==num))[1]:.2f})"
    j,u,r=pinlabel('J1','B5'),pinlabel('U6','2'),pinlabel('R2','1')
    cc2_ok=len(groups)==2 and any(u in g and r in g and j not in g for g in groups)
    assert cc2_ok
    transitions=[]
    for v in s['vias']:
        if v['net'].startswith(('USB_D','EPD_SCK','EPD_CLK','SPI_SCK')):
            gap=min(math.dist(xy(v),g)for g in ground_vias)
            transitions.append({'net':v['net'],'xy_mm':xy(v),'nearest_ground_via_mm':gap,'above_1_6_mm_guideline':gap>1.6})
    # A detached filled copper patch has no pads, vias or trace ends: the old node-only test missed this class.
    bad=copy.deepcopy(s)
    bad['poured'].append({'net':'GND','layer':1,'fills':[{'path':[[20/.254,35/.254,'L',21/.254,35/.254,21/.254,36/.254,20/.254,36/.254,20/.254,35/.254]],'lineWidth':0}]})
    negative=COPPER['audit'](bad)
    assert negative['floating_copper'] and not negative['ok']
    sw_area=sum(unions.get(('EPD_SW',l),Polygon()).area for l in (1,2))
    # A proximity proxy, not a field/current simulation of the multi-stage e-paper pump.
    c10=next(p for p in comps['C10']['pins']if p['net']=='EPD_VDD')
    l1=next(p for p in comps['L1']['pins']if p['net']=='EPD_VDD')
    q1=next(p for p in comps['Q1']['pins']if p['net']=='EPD_SW')
    loop_proxy=Polygon([xy(c10),xy(l1),xy(q1)]).area
    return {'status':'REVIEW_REQUIRED_BEFORE_ORDER','geometry_checks_pass':audit['ok'] and not bleed and cc2_ok,
            'fixed':['Screen protrusion ground rim removed on both layers.','Five-turn coil changed to 45-degree corners with equal exposed-edge offsets.','CC2 load branch moved from the pre-TVS tee to the U6 protection pad.','Copper checker now includes detached filled islands, even without pads/vias.','Battery lands routed at user-selected B position, shifted right 1.5 mm, with a narrow top-copper exception.','Three single-layer vias and one dead stub removed; two-face copper contact is now audited.'],
            'coil':{'turns':5,'chamfers':len(chamfers),'outer_centerline_bounds_mm':[x0,y0,x1,y1],'centerline_edge_offsets_mm':edge_offsets,
                    'copper_edge_offsets_mm':{k:v-width/2 for k,v in edge_offsets.items()},'minimum_trace_space_mm':space,'minimum_copper_to_outline_mm':edge_distance,'track_width_mm':width},
            'ground':{'groups':len(audit['groups']['GND']),'floating_copper':audit['floating_copper'],'screen_foreign_copper_mm2':audit['screen_foreign_copper_mm2'],'screen_unexpected_copper_mm2':audit['screen_unexpected_copper_mm2'],'screen_poured_copper_mm2':audit['screen_poured_copper_mm2'],'single_layer_or_isolated_vias':audit['single_layer_or_isolated_vias'],'detached_fill_negative_control_rejected':True},
            'ble_keepout_intrusions':bleed,'decoupling':decoupling,'esd_ground':esd,'cc2_protection_cut_groups':groups,
            'switch_node_copper_area_mm2':sw_area,'epd_input_inductor_switch_triangle_proxy_mm2':loop_proxy,
            'fast_signal_transitions':transitions,
            'discussion_items':[{'priority':'before_order','item':'Move C1 close to U2 IN/GND or add a correctly specified local input capacitor.','evidence':'C1.1 to U2.10 = 14.28 mm; BQ25186 datasheet sections 7.2.2 and 9.1 require local input decoupling.','status':'Left for the next placement discussion; components unchanged.'},
                                {'priority':'optimization','item':'Add nearby GND stitching at five USB layer transitions.','evidence':'Five USB vias exceed the contextual 1.6 mm guideline; worst gap about 3.66 mm. This is a return-path review item, not measured USB failure.'},
                                {'priority':'physical_validation','item':'Tune with screen, case and candidate NFC ferrite in place.','evidence':'Removing the rim does not remove display/battery metal loading; 220 pF is provisional.'}],
            'applicability':{'GP-002/CK-001/DP-004':'Not applicable: two copper layers, no inner signal layers or power/ground plane pair.',
                             'BE-002':'Intentionally excluded in the NFC region; a ground ring would conflict with the antenna clearance.',
                             'GP-004':'Whole-board fill percentage is not a gate because NFC and BLE clearances are intentional.',
                             'SW-003':'E-paper boost/charge-pump topology; recorded triangle is a placement proxy, not a buck input-loop proof.',
                             'RP-001':'1.6 mm contextual guideline using 0.8 mm thickness; not a universal pass/fail or USB certification.'},
            'limits':['All distances and areas are computed from native geometry, not physical measurements.','No EMC, USB signal integrity or RF qualification performed.','Unchanged component placement does not close the C1 finding.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--pins',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();result=review(json.loads(a.snapshot.read_text()),json.loads(a.pins.read_text()))
    result['snapshot_sha256']=hashlib.sha256(a.snapshot.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['status','geometry_checks_pass','coil','switch_node_copper_area_mm2','epd_input_inductor_switch_triangle_proxy_mm2']}))
