#!/usr/bin/env python3
"""Create a geometry-only ADC ablation; never modify the functional candidate."""
import copy
import json
import shutil
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union
from kicad_sexpr import child, children, prop, read, write
from v4_geometry import geometry

project = Path(__file__).resolve().parents[1]
source = project / 'hardware/kicad/v4-option-a-integration-rejected'
output = project / 'artifacts/kicad-v4-option-a/sampling-ablation'
assert not output.exists(), 'Preserve the previous counterfactual'
shutil.copytree(source, output, ignore=shutil.ignore_patterns('*.json', '~*'))
filename = 'NFC-Card-V4.kicad_pcb'
board, pads, objects, refs = geometry(source / filename)
original = copy.deepcopy(board)
removed_refs = {'Q2', 'Q3', 'R20', 'R21', 'R22', 'R23', 'C25'}
dedicated = {'BAT_ADC_SENSE', 'BAT_MEAS_EN', 'BAT_SWITCH_GATE', 'BAT_DIV_SUPPLY'}
assert {p['net'] for n,p in pads.items() if n.split('.')[0] in removed_refs} == dedicated | {'GND', 'BAT_PACK_TBD'}
for n,p in pads.items():
    if p['net'] in dedicated:
        assert n.split('.')[0] in removed_refs or n in {'U1.10', 'U1.11'}
_, _, control_objects, _ = geometry(project / 'hardware/kicad/v4-option-a' / filename)
protected_bat = {layer: unary_union([o['shape'] for o in control_objects if o['net']=='BAT_PACK_TBD' and layer in o['layers']]).buffer(.002)
                 for layer in ['F.Cu','B.Cu']}
sampling_bat_ids = {o['name'] for o in objects if o['kind'] in {'track','via'} and o['net']=='BAT_PACK_TBD'
                    and not all(protected_bat[l].covers(o['shape']) for l in o['layers'])}
removed_copper = []
for item in list(board):
    if not isinstance(item, list):
        continue
    if item[0]=='footprint' and prop(item,'Reference')[2] in removed_refs:
        board.remove(item)
    elif item[0] in ('segment','via') and (child(item,'net')[-1] in dedicated or child(item,'uuid')[1] in sampling_bat_ids):
        removed_copper.append({'uuid':child(item,'uuid')[1], 'net':child(item,'net')[-1]})
        board.remove(item)
write(output / filename, board)
extents = {}
for f in children(original, 'footprint'):
    ref = prop(f,'Reference')[2]
    if ref not in removed_refs:
        continue
    x,y,angle=refs[ref]
    from shapely import affinity
    rectangles=[]
    for r in children(f,'fp_rect'):
        if child(r,'layer')[1]=='F.CrtYd':
            rectangle=box(*map(float,child(r,'start')[1:]),*map(float,child(r,'end')[1:]))
            rectangles.append(affinity.translate(affinity.rotate(rectangle,-angle,origin=(0,0)),x,y))
    extents[ref]=unary_union(rectangles)
freed=unary_union(list(extents.values()))
record={'scope':'Geometry-only ablation; schematic intentionally unchanged, never an electrical or manufacturing candidate.',
        'source':str(source), 'output':str(output), 'removed_refs':sorted(removed_refs),
        'dedicated_nets':sorted(dedicated), 'removed_copper':removed_copper,
        'shared_GND_copper_untouched':True, 'main_BAT_and_charger_copper_preserved':True,
        'freed_courtyard_area_mm2':freed.area, 'freed_courtyard_bounds_mm':freed.bounds,
        'freed_by_ref_mm':{r:list(g.bounds) for r,g in extents.items()},
        'space_reassigned_to':[], 'reason':'Test whether removal alone restores the failed charger/LDO return components before proposing a functional sacrifice.'}
(project/'hardware/records/kicad-v4-option-a/sampling-ablation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in {'removed_copper','freed_by_ref_mm'}},indent=2))
