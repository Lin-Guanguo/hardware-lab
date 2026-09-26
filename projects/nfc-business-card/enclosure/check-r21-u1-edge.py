"""Compare nominal U1 edge options against R21 pins and the case candidate."""

import hashlib
import json
import re
import zipfile
from pathlib import Path

import FreeCAD as App
import Part


PROJECT = Path(__file__).resolve().parent.parent
PINS = PROJECT / 'hardware/records/r1-layout-reset-r21-pcb-pins.json'
CASE = PROJECT / 'enclosure/r1-usb4110-6p3/r21-usb4110-height-6p3.FCStd'
GERBER = PROJECT / 'hardware/production/r1-layout-reset-r21/NFC-Card-R1-Layout-Reset-R21-USB-CC2-gerber.zip'
REPORT = PROJECT / 'hardware/records/r1-layout-reset-r21-u1-edge-options.json'

pins = json.loads(PINS.read_text())
u1 = next(item for item in pins if item['ref'] == 'U1')
pin1 = next(item for item in u1['pins'] if item['number'] == '1')

# Raytac Rev L section 2.2: pin 1 is (0.60, 11.50) from the module corner.
# The R21 footprint is rotated 180 degrees, so this is its lower-right pin.
right = pin1['x'] * .0254 + .60
bottom = pin1['y'] * .0254 + 11.50
left = right - 10.50
top = bottom - 15.50
with zipfile.ZipFile(GERBER) as archive:
    outline = archive.read('Gerber_BoardOutlineLayer.GKO').decode()
board_top = 1.10
assert re.search(r'G01X37000000Y1100000D01\*', outline)
assert re.search(r'G02X80900001Y1100000I-1999999J0D01\*', outline)
nominal_edge = top - board_top

doc = App.openDocument(str(CASE))
shell = doc.getObject('RoundedUpperShell').Shape
caps = {ref: doc.getObject('Component_' + ref).Shape.BoundBox
        for ref in ('C1', 'C6', 'C7')}
cap_top = min(box.YMin for box in caps.values())
options = []
for depth in (.5, 1.0, 2.434):
    strip = Part.makeBox(right - left, depth, .8,
                         App.Vector(left, board_top - depth, 1.12))
    options.append({'board_top_extension_mm': depth,
                    'resulting_u1_nominal_edge_mm': nominal_edge + depth,
                    'case_overlap_mm3': shell.common(strip).Volume,
                    'case_min_distance_mm': shell.distToShape(strip)[0]})
App.closeDocument(doc.Name)

result = {
    'source_sha256': {str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in (PINS, GERBER, CASE)},
    'raytac_nominal_body_xy_mm': [left, top, right, bottom],
    'r21_board_top_y_mm': board_top,
    'nominal_u1_to_board_edge_mm': nominal_edge,
    'closest_c1_c6_c7_body_top_y_mm': cap_top,
    'nominal_u1_to_cap_body_gap_mm': cap_top - bottom,
    'after_u1_0p5mm_inward_gap_to_caps_mm': cap_top - bottom - .5,
    'hypothetical_top_board_extensions': options,
    'limits': [
        'Raytac body coordinates use nominal dimensions and five-pad orientation check, not a full 61-pad overlay.',
        'C1/C6/C7 body boxes come from the prior case CAD; positions match R21 snapshot but are not refreshed R21 3D models.',
        'Board extensions are rectangular collision probes, not manufacturable outline edits.',
        'A zero-volume shell contact is not manufacturing clearance.',
        'A 5 mm temporary panel rail could increase distance to the carrier edge, but assembly acceptance and RF keepout are unverified.',
    ],
}
REPORT.write_text(json.dumps(result, indent=2) + '\n')
print(REPORT)
