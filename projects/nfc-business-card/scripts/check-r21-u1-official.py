"""Compare every R21 U1 land and its case clearance with Raytac source CAD."""

import hashlib
import json
import math
import os
import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import FreeCAD as App
import Part
from shapely.geometry import box


library_path = Path(os.environ['RAYTAC_U1_LIBRARY'])
step_path = Path(os.environ['RAYTAC_U1_STEP'])
archive_path = Path(os.environ['RAYTAC_U1_ARCHIVE']) if 'RAYTAC_U1_ARCHIVE' in os.environ else None

project = Path(__file__).resolve().parent.parent
pins_path = project / 'hardware/records/r1-layout-reset-r21-pcb-pins.json'
snapshot_path = project / 'hardware/records/r1-layout-reset-r21-routed-snapshot.json'
case_path = project / 'enclosure/r1-usb4110-6p3/r21-usb4110-height-6p3.FCStd'
out_path = project / 'hardware/records/r1-layout-reset-r21-u1-official-overlay.json'

pins = json.loads(pins_path.read_text())
u1 = {pin['number']: pin for pin in next(row for row in pins if row['ref'] == 'U1')['pins']}
snapshot = json.loads(snapshot_path.read_text())
library = ET.parse(library_path).getroot()
package = library.find('.//packages/package[@name="MDBT50Q"]')
assert package is not None
official = {land.attrib['name']: land.attrib for land in package.findall('smd')}
assert len(official) == len(u1) == 61 and official.keys() == u1.keys()
wires = [wire.attrib for wire in package.findall('wire') if wire.attrib.get('layer') == '41']
assert any(wire['x1'] == '-6.25' and wire['y1'] == '8.75'
           and wire['x2'] == '6.25' and wire['y2'] == '8.75' for wire in wires)
assert any(wire['x1'] == '-2.3' and wire['y1'] == '2.75'
           and wire['x2'] == '-0.7' and wire['y2'] == '2.75' for wire in wires)

# Official package origin is the body center in XY; the R21 U1 is rotated 180 degrees.
pin1 = u1['1']
origin_x = pin1['x'] * .0254 + float(official['1']['x'])
origin_y = pin1['y'] * .0254 + float(official['1']['y'])
center_errors = []
size_errors = []
rotation_mismatches = []
for number, land in official.items():
    expected_x = origin_x - float(land['x'])
    expected_y = origin_y - float(land['y'])
    pin = u1[number]
    center_error = math.hypot(pin['x'] * .0254 - expected_x,
                              pin['y'] * .0254 - expected_y)
    center_errors.append(center_error)
    matching = [pad for pad in snapshot['pads'] if pad['number'] == number
                and math.hypot(pad['x'] * .0254 - expected_x,
                               pad['y'] * .0254 - expected_y) < .005]
    assert len(matching) == 1, number
    pad = matching[0]
    assert pad['pad'][0] == 'RECT' and pad['layer'] == 1 and pad['hole'] is None
    size_errors.append([abs(pad['pad'][1] * .0254 - float(land['dx'])),
                        abs(pad['pad'][2] * .0254 - float(land['dy']))])
    official_rotation = int(land.get('rot', 'R0').replace('R', '')) % 180
    if official_rotation != pad['rotation'] % 180:
        rotation_mismatches.append(number)
assert max(center_errors) < .003
assert max(max(pair) for pair in size_errors) < .002
assert not rotation_mismatches

# The Eagle tRestrict drawing marks the main antenna no-ground box and its extension.
main_keepout = box(origin_x - 6.25, origin_y - 8.75,
                   origin_x + 6.25, origin_y - 3.95)
extra_keepout = box(origin_x + .7, origin_y - 3.95,
                    origin_x + 2.3, origin_y - 2.75)
sys.path.insert(0, str(project / 'scripts'))
copper = runpy.run_path(str(project / 'scripts/check-r1-copper.py'))['copper']
shapes, _ = copper(snapshot)
keepout_intrusions = []
for (net, layer), parts in shapes.items():
    if layer not in (1, 2):
        continue
    for region_name, region in [('all_layer', main_keepout), ('top_extra', extra_keepout)]:
        if region_name == 'top_extra' and layer != 1:
            continue
        area = sum(shape.intersection(region).area for shape in parts)
        if area > 1e-5:
            keepout_intrusions.append({'net': net, 'layer': layer,
                                       'region': region_name, 'area_mm2': area})
assert not keepout_intrusions

module = Part.read(str(step_path))
assert module.isValid() and len(module.Solids) == 1
raw = module.BoundBox
assert abs(raw.XLength - 10.5) < .001
assert abs(raw.YLength - 2.0) < .001
assert abs(raw.ZLength - 15.5) < .001

# The lower-shield end of the source STEP is +Z; its antenna end is -Z.
antenna_probe = Part.makeBox(12, .2, 1, App.Vector(-6, 1, -7.5))
shield_probe = Part.makeBox(12, .2, 1, App.Vector(-6, 1, 6.5))
assert module.common(antenna_probe).Volume < .001
assert module.common(shield_probe).Volume > 1
module.Placement = App.Placement(
    App.Vector(origin_x, origin_y, 1.92), App.Rotation(App.Vector(0, 1, 1), 180))
body = module.BoundBox

doc = App.openDocument(str(case_path))
shell = doc.getObject('RoundedUpperShell').Shape
board = doc.getObject('PCB').Shape
cap_gap = {ref: module.distToShape(doc.getObject('Component_' + ref).Shape)[0]
           for ref in ('C1', 'C6', 'C7')}
case_gap = module.distToShape(shell)[0]
case_overlap = module.common(shell).Volume
board_overlap = module.common(board).Volume
App.closeDocument(doc.Name)
assert case_overlap < 1e-7 and board_overlap < 1e-7

sources = {'raytac_eagle_library_sha256': hashlib.sha256(library_path.read_bytes()).hexdigest(),
           'raytac_p1mv2_step_sha256': hashlib.sha256(step_path.read_bytes()).hexdigest(),
           'r21_pins_sha256': hashlib.sha256(pins_path.read_bytes()).hexdigest(),
           'r21_snapshot_sha256': hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
           'case_sha256': hashlib.sha256(case_path.read_bytes()).hexdigest()}
if archive_path:
    sources['raytac_official_archive_sha256'] = hashlib.sha256(archive_path.read_bytes()).hexdigest()

result = {
    'source': 'https://www.raytac.com/document/act.php?act=1&index_id=30',
    'official_package': 'MDBT50Q / nRF52840 Eagle library, Footprint_Design Guide 230606',
    'matched_pin_count': len(official),
    'max_pad_center_error_mm': max(center_errors),
    'max_pad_width_error_mm': max(pair[0] for pair in size_errors),
    'max_pad_height_error_mm': max(pair[1] for pair in size_errors),
    'rotation_mismatches_mod_180': rotation_mismatches,
    'official_main_keepout_bounds_mm': list(main_keepout.bounds),
    'official_top_extra_keepout_bounds_mm': list(extra_keepout.bounds),
    'official_keepout_copper_intrusions': keepout_intrusions,
    'step_body_bbox_mm': [body.XMin, body.YMin, body.ZMin,
                          body.XMax, body.YMax, body.ZMax],
    'step_to_case_min_mm': case_gap,
    'step_to_case_overlap_mm3': case_overlap,
    'step_to_r21_board_overlap_mm3': board_overlap,
    'step_to_old_cad_cap_min_mm': cap_gap,
    'source_sha256': sources,
    'limits': [
        'The STEP is nominal; dimensional tolerances and paste/mask details are not verified.',
        'C1/C6/C7 and other case components are old CAD bodies, not a full R21 3D update.',
        'A correct pad overlay and positive shell gap do not approve near-edge SMT assembly.',
    ],
}
out_path.write_text(json.dumps(result, indent=2) + '\n')
print(out_path)
