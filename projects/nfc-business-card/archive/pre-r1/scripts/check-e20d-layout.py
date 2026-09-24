#!/usr/bin/env python3
"""Audit the E20D placement, RF reservation and moved connector geometry."""
import json
import math
from pathlib import Path
from pour_geometry import load_pours,calibrate
ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'hardware/records'
load=lambda name:json.loads((REC/name).read_text())
s=load('e20d-placement-snapshot.json');old=load('e20b-placement-snapshot.json')
cs={c['ref']:c for c in load('e20d-layout-pins.json')};base={c['ref']:c for c in load('e20b-layout-pins.json')}
plan=json.loads((ROOT/'hardware/e20d-placement.json').read_text())
refinement=json.loads((ROOT/'hardware/e20d-refinement.json').read_text())
initial={c['ref']:c for c in load('e20d-initial-layout-pins.json')}
assert len(s['components'])==58 and len(s['pads'])==248 and not s['lines'] and not s['vias']
assert all(abs(math.remainder(c['rotation']-base[r]['rotation'],360))<1e-6 for r,c in cs.items() if r not in ['C23','C24','C10','R13'])
for ref,target in refinement['components_mm'].items():
    c=cs[ref]
    assert abs(c['x']*.0254-target[0])<.003 and abs(c['y']*.0254-target[1])<.003
    assert abs(math.remainder(c['rotation']-target[2],360))<1e-6
for ref,c in cs.items():
    assert {p['number']:p['net'] for p in c['pins']}=={p['number']:p['net'] for p in initial[ref]['pins']}
for ref in ['SW1','SW2','SW3']:
    assert abs((cs[ref]['x']-base[ref]['x'])*.0254-1)<.003
    assert abs(cs[ref]['y']-base[ref]['y'])<.003
j1_errors=[]
for p in cs['J1']['pins']:
    q=next(v for v in base['J1']['pins'] if v['number']==p['number'])
    assert p['net']==q['net'] and p['pad']==q['pad'] and abs((p['rotation']-q['rotation'])%360)<1e-6
    j1_errors.append(max(abs(p['x']-q['x'])*.0254,abs((p['y']-q['y'])*.0254-plan['usb_translation_y_mm'])))
assert max(j1_errors)<.003
rf=[3,19,35,45];overlaps=[]
for p in s['pads']:
    w,h=p['pad'][1]*.0254,p['pad'][2]*.0254
    # Rotated bounding rectangles conservatively contain all exported pad shapes.
    angle=math.radians(p['rotation']);wx=abs(w*math.cos(angle))+abs(h*math.sin(angle));hy=abs(w*math.sin(angle))+abs(h*math.cos(angle))
    x,y=p['x']*.0254,p['y']*.0254
    if x+wx/2>rf[0] and x-wx/2<rf[2] and y+hy/2>rf[1] and y-hy/2<rf[3]:overlaps.append(p['id'])
assert not overlaps
pours=load_pours(s);ok,calibration=calibrate(pours);assert ok
samples={};spoke_intrusions=[]
for layer,pour in pours.items():
    hits=0;count=0
    for ix in range(128):
        for iy in range(104):
            x,y=3+.125+ix*.25,19+.125+iy*.25;count+=1
            hits+=pour.contains(x,y)
    samples[str(layer)]={'sample_spacing_mm':.25,'points':count,'filled_points':hits}
    for sp in pour.spokes:
        xs=[sp.start[0],sp.end[0]];ys=[sp.start[1],sp.end[1]]
        if max(xs)>3 and min(xs)<35 and max(ys)>19 and min(ys)<45:spoke_intrusions.append({'layer':layer,'start':sp.start,'end':sp.end})
assert all(v['filled_points']==0 for v in samples.values()) and not spoke_intrusions
power=['U4','C9','C10','L1','Q1','R13','R14','R15','D1','C11','C12','D2','R16','D3','C13']
for ref in power:
    assert abs((initial[ref]['x']-base[ref]['x'])*.0254-36)<.003 and abs(initial[ref]['y']-base[ref]['y'])<.003
metrics=[]
for ref in power:
    for pin in cs[ref]['pins']:
        if not pin['net'] or pin['net'] in ['GND','VDD_3V3']:continue
        targets=[p for p in cs['J2']['pins'] if p['net']==pin['net']]
        if not targets:continue
        oldpin=next(p for p in base[ref]['pins'] if p['number']==pin['number'])
        oldtargets=[p for p in base['J2']['pins'] if p['net']==pin['net']]
        before=min(math.hypot(p['x']-oldpin['x'],p['y']-oldpin['y'])*.0254 for p in oldtargets)
        after=min(math.hypot(p['x']-pin['x'],p['y']-pin['y'])*.0254 for p in targets)
        metrics.append({'from':ref+'.'+pin['number'],'net':pin['net'],'nearest_j2_pin_before_mm':before,'nearest_j2_pin_after_mm':after})
ci=next(p for p in cs['C8']['pins'] if p['number']=='1');ui=next(p for p in cs['U2']['pins'] if p['number']=='10')
refinement_distances=[]
for a,ap,b,bp in [('C9','1','U4','1'),('C10','1','U4','6'),('C10','1','L1','1'),('R13','1','U4','3'),('C11','2','D2','2'),('D2','2','D3','1'),('D3','2','C13','1')]:
    item={'from':a+'.'+ap,'to':b+'.'+bp}
    for label,data in [('before_mm',initial),('after_mm',cs)]:
        p=next(p for p in data[a]['pins'] if p['number']==ap);q=next(p for p in data[b]['pins'] if p['number']==bp)
        assert p['net']==q['net']
        item[label]=math.hypot(p['x']-q['x'],p['y']-q['y'])*.0254
    refinement_distances.append(item)
old_sw={(c['ref'],p['number']):(p['x'],p['y']) for c in initial.values() for p in c['pins'] if p['net']=='EPD_SW'}
new_sw={(c['ref'],p['number']):(p['x'],p['y']) for c in cs.values() for p in c['pins'] if p['net']=='EPD_SW'}
assert old_sw==new_sw
report={'status':'UNROUTED_GEOMETRY_AUDIT','components':58,'pads':248,'tracks':0,'vias':0,'usb_center_y_mm':cs['J1']['y']*.0254,
        'usb_pin_translation_max_error_mm':max(j1_errors),'battery_straight_span_mm':[35.9,16.7],
        '31mm_pack_length_total_remainder_mm':4.9,'31mm_pack_right_gap_at_x1_5_mm':4,
        'c8_to_u2_in_pad_distance_mm':math.hypot(ci['x']-ui['x'],ci['y']-ui['y'])*.0254,
        'rf_region_xyxy_mm':rf,'pads_in_rf_region':overlaps,'pour_parser_calibration':calibration,
        'rf_pour_grid_check':samples,'rf_spoke_bbox_intrusions':spoke_intrusions,
        'coil_outer_centerline_study_mm':[30,24],'coil_outer_rectangle_area_study_mm2':720,
        'previous_coil_outer_rectangle_area_study_mm2':18*21.3,'display_power_moved_refs':power,
        'initial_display_power_translation_mm':[36,0],'power_to_j2_pin_distances':metrics,
        'later_refinement':refinement,'refinement_pad_distances':refinement_distances,'epd_sw_pad_positions_unchanged_by_refinement':True,
        'limits':['RF coil is reserved, not routed; no inductance, coupling or read-range test.',
                  'Pour exclusion samples and conservative pad checks do not certify RF performance.',
                  'Pad-centre distances are not routed current loops; some J2 branches get longer.',
                  '3D, profile and native DRC results are recorded separately.']}
(REC/'e20d-layout-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
