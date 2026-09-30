#!/usr/bin/env python3
"""Continuously test BUSY escape space without routing order or lattice search."""
import hashlib
import importlib.util
import json
from pathlib import Path

from shapely.geometry import Point, box
from shapely.ops import unary_union
from v4_geometry import geometry

project=Path(__file__).resolve().parents[1]
records=project/'hardware/records/kicad-v4-option-a2'
path=project/'hardware/kicad/v4-option-a2-full/NFC-Card-V4.kicad_pcb'
b,pads,objects,_=geometry(path)
spec=importlib.util.spec_from_file_location('router',Path(__file__).with_name('route-v4-octilinear.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
boundary=module.outline(b)
plan=json.loads((path.parent/'successful-batch-plan.json').read_text())
ids=json.loads((records/'full-successful-batch-ipc.json').read_text())['created_ids']
names={};i=0
for r in plan['routes']:
    for _ in range(len(r['points'])-1):names[ids[i]]=r['name'];i+=1
for v in plan['vias']:
    names[ids[i]]=v['net']+' new via';i+=1
assert i==len(ids)
source,destination=pads['U1.24'],pads['J2.9']
results=[]
for variant in ['current','remove_new_VBUS_MCU_branch','remove_MCU_rail_copper_only']:
    removed=[];kept=[]
    for o in objects:
        take = variant=='remove_new_VBUS_MCU_branch' and names.get(o['name'])=='VBUS MCU branch'
        take |= variant=='remove_MCU_rail_copper_only' and o['net']=='VDD_3V3' and o['kind'] in ['track','via'] and o['shape'].intersects(box(168,109,173.5,114))
        (removed if take else kept).append(o)
    barriers=unary_union([o['shape'].buffer(.275,quad_segs=32) for o in kept if o['net']!=source['net'] and 'F.Cu' in o['layers']])
    free=boundary.buffer(-.375).difference(barriers)
    components=list(free.geoms) if hasattr(free,'geoms') else [free]
    component=next((g for g in components if g.covers(Point(source['at']))),None)
    assert component is not None
    forbidden=unary_union([*[o['shape'].buffer(.5,quad_segs=32) for o in kept if o['net']!=source['net']],*[o['shape'].buffer(.55,quad_segs=32) for o in kept if o['kind']=='pad' and len(o['layers'])==1]])
    possible=component.intersection(boundary.buffer(-.6)).difference(forbidden)
    point=None if possible.is_empty else list(possible.representative_point().coords[0])
    results.append(dict(variant=variant,removed_objects=[dict(id=o['name'],net=o['net']) for o in removed],source_F_component_area_mm2=round(component.area,6),source_F_component_bounds_mm=component.bounds,destination_in_same_F_component=component.covers(Point(destination['at'])),possible_via_center_area_mm2=round(possible.area,9),continuous_via_witness_mm=point))
report=dict(board=str(path),board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scope='Independent continuous buffered geometry, not A* or a grid. Other tracks treated as present for each explicit counterfactual. No counterfactual is electrically complete; no conclusion of global board area insufficiency.',trace_width_mm=.15,clearance_mm=.2,via_mm=[.6,.3],smd_to_drill_mm=.4,results=results)
(records/'busy-continuous-geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(results,indent=2))
