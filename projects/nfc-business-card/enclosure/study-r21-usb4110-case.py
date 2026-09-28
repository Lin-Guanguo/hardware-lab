"""Build an isolated R21 board and USB4110 enclosure geometry candidate."""

import hashlib
import json
import math
import os
import re
import zipfile
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
SOURCE = ROOT / 'r1-rounded-rear-soft-swd254/rear-cover-study.FCStd'
PRODUCTION = PROJECT / 'hardware/production/r1-layout-reset-r21'
GERBER = PRODUCTION / 'NFC-Card-R1-Layout-Reset-R21-USB-CC2-gerber.zip'
PINS = PROJECT / 'hardware/records/r1-layout-reset-r21-pcb-pins.json'
OUT = Path(os.environ['NFC_R21_USB4110_CASE_OUT']).resolve()
if OUT.exists():
    raise RuntimeError('Use a new output directory.')
OUT.mkdir(parents=True)
hashes = {str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
          for path in (SOURCE, GERBER, PINS)}
V = App.Vector


def board_from_gerber(data):
    expression = re.compile(r'G0([123])X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([12])\*')
    edges = []
    current = None
    arcs = 0
    for line in data.splitlines():
        match = expression.fullmatch(line)
        if not match:
            continue
        mode, x, y, i, j, draw = match.groups()
        end = (int(x) / 1e6, int(y) / 1e6)
        if draw == '2':
            current = end
            continue
        assert current is not None
        start = V(current[0], current[1], 0)
        finish = V(end[0], end[1], 0)
        if mode == '1':
            edge = Part.makeLine(start, finish)
        else:
            assert i is not None and j is not None
            center = (current[0] + int(i) / 1e6, current[1] + int(j) / 1e6)
            first_angle = math.atan2(current[1] - center[1], current[0] - center[0])
            last_angle = math.atan2(end[1] - center[1], end[0] - center[0])
            sweep = (-((first_angle - last_angle) % (2 * math.pi)) if mode == '2'
                     else (last_angle - first_angle) % (2 * math.pi))
            radius = math.dist(current, center)
            middle = V(center[0] + radius * math.cos(first_angle + sweep / 2),
                       center[1] + radius * math.sin(first_angle + sweep / 2), 0)
            edge = Part.Arc(start, middle, finish).toShape()
            arcs += 1
        edges.append(edge)
        current = end
    wire = Part.Wire(edges)
    assert wire.isClosed() and len(edges) == 13 and arcs == 6
    face = Part.Face(wire)
    assert abs(face.Area - 3497.53103094) < .001
    board = face.extrude(V(0, 0, .8))
    board.translate(V(0, 0, 1.12))
    assert board.isValid() and len(board.Solids) == 1
    return board, face.Area


with zipfile.ZipFile(GERBER) as archive:
    board, board_area = board_from_gerber(archive.read('Gerber_BoardOutlineLayer.GKO').decode())
    npth = archive.read('Drill_NPTH_Through.DRL').decode()
holes = [(float(x), float(y)) for x, y in
         re.findall(r'^X([\d.]+)Y([\d.]+)$', npth, re.MULTILINE)]
assert len(holes) == 2 and 'T01C0.649986' in npth
for x, y in holes:
    board = board.cut(Part.makeCylinder(.649986 / 2, 1, V(x, y, 1.02)))
board = board.removeSplitter()
assert board.isValid() and len(board.Solids) == 1
pin_data = json.loads(PINS.read_text())
j1_pins = next(row['pins'] for row in pin_data if row['ref'] == 'J1')
front_shell_x = max(pin['x'] * .0254 for pin in j1_pins if pin['number'] in ('8', '9', '10', '11'))
face_x = front_shell_x + 2.85
doc = App.openDocument(str(SOURCE))
old_connector_face = doc.getObject('Component_J1').Shape.BoundBox.XMax
assert abs(face_x - old_connector_face) < .01
old_upper = doc.getObject('RoundedUpperShell').Shape
old_board_volume = doc.getObject('PCB').Shape.Volume

# Extend the existing vertical wall band and lift the roof, screen and buttons.
lower = old_upper.common(Part.makeBox(100, 70, 4, V(-5, -5, -1)))
top = old_upper.common(Part.makeBox(100, 70, 10, V(-5, -5, 2.5)))
top.translate(V(0, 0, .5))
upper = lower.fuse(top).removeSplitter()
assert upper.isValid() and len(upper.Solids) == 1

# Rectangular envelope follows the GCT nominal length, shell width and profile.
connector = Part.makeBox(7.7, 8.94, 3.26, V(face_x - 7.7, 26 - 4.47, 1.92))
tabs = Part.makeBox(7.7, 11.3, .63, V(face_x - 7.7, 26 - 5.65, 1.92))
mouth_clearance = Part.makeBox(10, 9.54, 3.86, V(face_x - 8, 26 - 4.77, 1.62))
connector_gap = upper.distToShape(connector)[0]
assert abs(connector_gap - .32) < .001
assert upper.common(mouth_clearance).Volume < 1e-7
assert upper.common(tabs).Volume < 1e-7
assert upper.common(board).Volume < 1e-7
rear = doc.getObject('InsetRearCover').Shape
assert upper.common(rear).Volume < 1e-7

key_names = ('ClearKey1', 'ClearKey2', 'ClearKey3')
switch_names = ('SW1', 'SW3', 'SW2')
centers = ((41.1, 4.5), (41.1, 14.4), (49.6, 8.80000526))
key_checks = []
for name, switch_name, (x, y) in zip(key_names, switch_names, centers):
    original = doc.getObject(name).Shape
    tip = original.BoundBox.ZMin
    key = original.copy()
    key.translate(V(0, 0, .5))
    key = key.fuse(Part.makeCylinder(1.3, .51, V(x, y, tip))).removeSplitter()
    assert key.isValid() and len(key.Solids) == 1
    switch = doc.getObject('Component_' + switch_name).Shape
    travel = tip - switch.BoundBox.ZMax + .45
    fixed = switch.cut(Part.makeCylinder(1.4, 3, V(x, y, board.BoundBox.ZMax - .2)))
    downward_faces = [face for face in key.Faces
                      if isinstance(face.Surface, Part.Plane) and face.normalAt(0, 0).z < -.99]
    assert downward_faces
    sweep = key.multiFuse([face.extrude(V(0, 0, -travel)) for face in downward_faces]).removeSplitter()
    other_hits = {}
    for obj in doc.Objects:
        if obj.Name.startswith('Component_') and obj.Name not in ('Component_' + switch_name,
                                                                   'Component_J1'):
            overlap = sweep.common(obj.Shape).Volume
            if overlap > 1e-7:
                other_hits[obj.Name] = overlap
    check = {'key': name, 'travel_mm': travel, 'valid': key.isValid(),
             'rest_switch_overlap_mm3': key.common(switch).Volume,
             'swept_fixed_switch_overlap_mm3': sweep.common(fixed).Volume,
             'swept_upper_overlap_mm3': sweep.common(upper).Volume,
             'swept_board_overlap_mm3': sweep.common(board).Volume,
             'swept_other_component_overlap_mm3': other_hits}
    assert max(check['rest_switch_overlap_mm3'], check['swept_fixed_switch_overlap_mm3'],
               check['swept_upper_overlap_mm3'], check['swept_board_overlap_mm3']) < 1e-7
    assert not other_hits
    doc.getObject(name).Shape = key
    key_checks.append(check)

doc.getObject('RoundedUpperShell').Shape = upper
doc.getObject('PCB').Shape = board
doc.getObject('Component_J1').Shape = connector
doc.getObject('Component_J1').Label = 'USB4110 nominal envelope (not STEP)'
for name in ('ScreenNominal', 'ScreenPSA'):
    shape = doc.getObject(name).Shape.copy()
    shape.translate(V(0, 0, .5))
    doc.getObject(name).Shape = shape

intersections = {}
for obj in doc.Objects:
    if obj.Name.startswith('Component_') and obj.Name != 'Component_J1':
        amount = upper.common(obj.Shape).Volume
        if amount > 1e-7:
            intersections[obj.Name] = amount
assert not intersections
assert upper.common(doc.getObject('ScreenNominal').Shape).Volume < 1e-7
assert upper.common(doc.getObject('ScreenPSA').Shape).Volume < 1e-7
doc.recompute()
model = OUT / 'r21-usb4110-height-6p3.FCStd'
doc.saveAs(str(model))
App.closeDocument(doc.Name)

saved = App.openDocument(str(model))
for name in ('RoundedUpperShell', 'InsetRearCover', 'PCB', 'Component_J1', *key_names):
    shape = saved.getObject(name).Shape
    assert shape.isValid() and len(shape.Solids) == 1
upper = saved.getObject('RoundedUpperShell').Shape
assert upper.distToShape(saved.getObject('Component_J1').Shape)[0] > .319
assert upper.common(saved.getObject('PCB').Shape).Volume < 1e-7
physical = [saved.getObject(name) for name in ('RoundedUpperShell', 'InsetRearCover', *key_names)]
Part.export(physical, str(OUT / 'case-parts.step'))
step = Part.read(str(OUT / 'case-parts.step'))
assert step.isValid() and len(step.Solids) == 5
mesh = MeshPart.meshFromShape(Shape=upper, LinearDeflection=.03,
                              AngularDeflection=.2, Relative=False)
mesh_path = OUT / 'upper.stl'
mesh.write(str(mesh_path))
assert Mesh.Mesh(str(mesh_path)).isSolid()
App.closeDocument(saved.Name)

checks = {'source_hashes': hashes, 'source_unchanged': all(
    hashlib.sha256((PROJECT / path).read_bytes()).hexdigest() == digest
    for path, digest in hashes.items()),
    'gerber_board_area_mm2': board_area,
    'gerber_npth_holes_mm': holes,
    'old_board_to_r21_volume_delta_mm3': board.Volume - old_board_volume,
    'connector_face_x_mm': face_x,
    'connector_body_box_mm': [connector.BoundBox.XMin, connector.BoundBox.XMax,
                              connector.BoundBox.YMin, connector.BoundBox.YMax,
                              connector.BoundBox.ZMin, connector.BoundBox.ZMax],
    'nominal_connector_to_shell_mm': connector_gap,
    'nominal_tab_envelope_to_shell_mm': upper.distToShape(tabs)[0],
    'mouth_clearance_shell_overlap_mm3': 0,
    'key_checks': key_checks,
    'other_component_shell_intersections_mm3': intersections,
    'saved_reopened_valid': True,
    'step_valid': True,
    'step_solids': len(step.Solids),
    'upper_stl_closed': True,
    'status': 'NOMINAL_GEOMETRY_CANDIDATE_NOT_MANUFACTURING_RELEASE',
    'limits': ['USB4110 body uses official nominal dimensions in a rectangular envelope, not a manufacturer STEP or plug fit.',
               'The board reference models the R21 outline and two NPTH locating holes, not the 165 PTH vias.',
               'The old CAD component positions other than J1/PCB are not refreshed from R21.',
               'No print tolerance, solder standoff, USB mating plug, shell tab, or locating-peg solid is modeled.',
               'U1 placement and 0.066 mm board-edge clearance are unchanged.']}
assert checks['source_unchanged']
(OUT / 'report.json').write_text(json.dumps(checks, indent=2) + '\n')
print('R21_USB4110_CASE_CANDIDATE', str(OUT / 'report.json'))
