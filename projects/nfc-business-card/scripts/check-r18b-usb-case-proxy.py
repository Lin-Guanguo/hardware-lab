"""Compare a conservative USB4110 envelope with the existing enclosure CAD."""

import json
from pathlib import Path

import FreeCAD as App
import Part

root = Path(__file__).resolve().parents[1]
output = root / 'artifacts/r18b-case-proxy.json'
source = root / 'enclosure/r1-rounded-rear-soft-swd254/rear-cover-study.FCStd'
doc = App.openDocument(str(source))
pcb = doc.getObject('PCB').Shape
old = doc.getObject('Component_J1').Shape
old_box = old.BoundBox

# Deliberately conservative envelope from the GCT body length and the existing
# connector's wider shell span. This is a packaging proxy, not a native STEP.
face_x = old_box.XMax
body_length = 7.7
shell_y_min = old_box.YMin
shell_width = old_box.YLength
pcb_top = pcb.BoundBox.ZMax
profile = 3.26
proxy = Part.makeBox(body_length, shell_width, profile,
                     App.Vector(face_x - body_length, shell_y_min, pcb_top))

intersections = {}
for obj in doc.Objects:
    if not obj.Name.startswith('Component_') or obj.Name == 'Component_J1':
        continue
    common = proxy.common(obj.Shape)
    if common.Volume > 1e-7:
        intersections[obj.Name] = round(common.Volume, 6)

floor = 0.8
support = 0.32
lid = 0.8
gap_target = 0.30
top = proxy.BoundBox.ZMax
heights = {}
for total in (5.8, 6.3):
    lid_inner = total - lid
    heights[str(total)] = {
        'lid_inner_z_mm': lid_inner,
        'usb_top_gap_mm': round(lid_inner - top, 5),
        'nominal_interference_mm': round(max(top - lid_inner, 0), 5),
    }

report = {
    'status': 'NOMINAL_PROXY_ONLY',
    'source': str(source.relative_to(root)),
    'input': {
        'connector': 'GCT USB4110-GF-A',
        'profile_above_board_mm': profile,
        'proxy_length_mm': body_length,
        'proxy_width_mm': shell_width,
        'pcb_top_z_mm': round(pcb_top, 5),
        'mating_face_x_mm': round(face_x, 5),
        'floor_mm': floor,
        'pcb_support_mm': support,
        'lid_mm': lid,
        'target_nominal_top_gap_mm': gap_target,
    },
    'proxy_box_mm': [round(v, 5) for v in
                     (proxy.BoundBox.XMin, proxy.BoundBox.XMax,
                      proxy.BoundBox.YMin, proxy.BoundBox.YMax,
                      proxy.BoundBox.ZMin, proxy.BoundBox.ZMax)],
    'other_component_solid_intersection_mm3': intersections,
    'case_heights': heights,
    'minimum_total_height_for_target_gap_mm': round(top + gap_target + lid, 5),
    'limits': [
        'Rectangular connector proxy; does not model real USB4110 STEP, shell tabs or locating pegs.',
        'The existing case CAD still contains the USB4500 body and opening, not a USB4110 model.',
        'R18B has a straight PCB edge, but the case opening and connector position are unverified.',
        'No print tolerance, solder stand-off, connector tolerance or lid deformation included.',
    ],
}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'output': str(output)}))
App.closeDocument(doc.Name)
