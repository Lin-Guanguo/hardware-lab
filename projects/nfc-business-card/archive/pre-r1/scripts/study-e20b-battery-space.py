"""Measure key/pocket alternatives without editing the native PCB or saved CAD.

Run with freecadcmd. The enlarged cutouts are section studies, not final routed
board profiles; radii, copper, supports and lid holes must follow a selected option.
"""
import json
from pathlib import Path
from itertools import combinations
import FreeCAD as App
import Part

ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'hardware/records'
source=ROOT/'enclosure/e20b-functional-5.8/e20-clear-assembly.FCStd'
doc=App.openDocument(str(source))
parts={o.Name.removeprefix('Component_'):o.Shape.copy() for o in doc.Objects if o.Name.startswith('Component_')}
board=doc.getObject('PCB').Shape
tray=doc.getObject('ClearTray').Shape
lid=doc.getObject('ClearLid').Shape
pins=json.loads((REC/'e20b-layout-pins.json').read_text())
V=App.Vector
plans=[{'name':'Current three keys','cutout_x_mm':35.5,'moves':{},'remove':[]},
       {'name':'Three keys, shift 1 mm','cutout_x_mm':36.5,'moves':{'SW1':[1,0],'SW2':[1,0],'SW3':[1,0]},'remove':[]},
       {'name':'Two keys, expand 4 mm','cutout_x_mm':39.5,'moves':{'SW1':[4,0],'SW3':[4,-1.9]},'remove':['SW2']}]
results=[]
for plan in plans:
    shapes={r:s.copy() for r,s in parts.items() if r not in plan['remove']}
    for ref,(dx,dy) in plan['moves'].items():shapes[ref].translate(V(dx,dy,0))
    cut=board.cut(Part.makeBox(plan['cutout_x_mm']-34.5,17.3,2,V(34.5,0,1))) if plan['moves'] else board
    battery=Part.makeBox(31,14,3.4,V(1.5,1.5,.9))
    envelope=Part.makeBox(32.5,14,3.4,V(1.5,1.5,.9))
    near=[]
    for ref in plan['moves']:
        for other,s in shapes.items():
            if other==ref:continue
            distance=shapes[ref].distToShape(s)[0]
            if distance<1.5:near.append({'a':ref,'b':other,'distance_mm':distance,'intersection_mm3':shapes[ref].common(s).Volume})
    pad_hits=[];pad_edges=[]
    for c in pins:
        ref=c['ref']
        if ref in plan['remove']:continue
        dx,dy=plan['moves'].get(ref,[0,0])
        for p in c['pins']:
            if p['layer']!=1:continue
            w,h=p['pad'][1]*.0254,p['pad'][2]*.0254
            if round(p['rotation'])%180==90:w,h=h,w
            x,y=p['x']*.0254+dx,p['y']*.0254+dy
            if y-h/2<17.3 and x+w/2>34.5:
                edge=x-w/2-plan['cutout_x_mm']
                if edge<1:pad_edges.append({'ref':ref,'pin':p['number'],'left_pad_to_cutout_mm':edge})
                if edge<0 and x+w/2>34.5:pad_hits.append({'ref':ref,'pin':p['number']})
    result={**plan,'nominal_straight_cavity_length_mm':plan['cutout_x_mm']-.6,
            'nominal_straight_cavity_width_mm':17.3-.6,
            'total_length_remainder_31_mm':plan['cutout_x_mm']-.6-31,
            'total_length_remainder_32_5_mm':plan['cutout_x_mm']-.6-32.5,
            'right_gap_31_mm':plan['cutout_x_mm']-32.5,
            'right_gap_32_5_mm':plan['cutout_x_mm']-34,
            'left_gap_mm':.9,
            'battery31_to_board_distance_mm':battery.distToShape(cut)[0],
            'battery31_to_tray_distance_mm':battery.distToShape(tray)[0],
            'battery31_to_lid_distance_mm':battery.distToShape(lid)[0],
            'envelope_to_board_distance_mm':envelope.distToShape(cut)[0],
            'shifted_switch_neighbours':sorted(near,key=lambda x:x['distance_mm']),
            'pads_cut_by_proposed_opening':pad_hits,'pads_near_cutout':pad_edges,
            'switch_centres_mm':{c['ref']:[c['x']*.0254+plan['moves'].get(c['ref'],[0,0])[0],c['y']*.0254+plan['moves'].get(c['ref'],[0,0])[1]] for c in pins if c['ref'].startswith('SW') and c['ref'] not in plan['remove']}}
    results.append(result)
battery_options=[]
for label,length,width,height in [('New short pack',24,14,3),('New long pack',31,12,3),('Previous wide pack',32,20,3)]:
    shape=Part.makeBox(length,width,height,V(1.5,1.5,.9))
    screen_max=Part.makeBox(37.42,31.9,1,V(1.95,18.25,3.94))
    battery_options.append({'label':label,'nominal_lwh_mm':[length,width,height],
        'total_length_remainder_mm':34.9-length,'total_width_remainder_mm':16.7-width,
        'right_gap_to_pcb_straight_edge_mm':35.5-1.5-length,'lower_gap_to_pcb_straight_edge_mm':17.3-1.5-width,
        'board_intersection_mm3':shape.common(board).Volume,
        'tray_intersection_mm3':shape.common(tray).Volume,'lid_intersection_mm3':shape.common(lid).Volume,
        'screen_max_distance_mm':shape.distToShape(screen_max)[0],
        'screen_max_intersection_mm3':shape.common(screen_max).Volume,
        'lid_distance_mm':shape.distToShape(lid)[0]})
report={'status':'READ_ONLY_SPACE_STUDY_NOT_IMPLEMENTED','battery_options':battery_options,'battery_length_reported_mm':31,
        'battery_length_basis':'User reports purchasing nominal 3x14x24 and 3x12x31 mm batteries plus a previous 3x20x32 mm option. Complete pack boundaries and protection inclusion are unconfirmed; new packs not received.',
        'pack_width_height_assumed_mm':[14,3.4],'protected_pack_review_envelope_mm':[32.5,14,3.4],
        'case_height_mm':5.8,'options':results,
        'limits':['Straight cavity dimensions are geometric spans, not guaranteed maximum rectangular pack sizes; corner radii and tolerances remain.',
                  'Pocket extension is a local CAD subtraction study, not a manufacturable final profile.',
                  'Native PCB, schematic, lid and key caps have not been modified.',
                  'Selected changes require native DRC, full cap-travel/wire/support checks and rerendered CAD.',
                  'Battery width, thickness, complete sealed length and lead exit remain unmeasured.']}
(REC/'e20b-battery-space-study.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
