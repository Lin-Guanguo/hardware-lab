"""Build a separate rear-seam study; preserve the active PCB and enclosure."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Part
import Mesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'enclosure/r1-clear-5.8/e20-clear-assembly.FCStd'
CONFIG = SOURCE.parent / 'design-inputs.json'
OUT = Path(os.environ['NFC_REAR_STUDY_OUT']).resolve()
if OUT.exists():
    raise RuntimeError('Output directory must be new; existing CAD is never overwritten.')
OUT.mkdir(parents=True)
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (SOURCE, CONFIG)}
C = json.loads(CONFIG.read_text())
K = C['clear_shell']
V = App.Vector
X, Y = K['outer_offset_xy_mm']
W, H = K['outer_xy_mm']
HEIGHT, WALL, PANEL = 5.8, 1.2, .8
GAP = .25
STYLE = os.environ.get('NFC_REAR_STUDY_STYLE', 'original')
assert STYLE in ('original', 'soft')
PLAN_RADIUS, FRONT_RADIUS, REAR_RADIUS = (3.2, 1.2, .7) if STYLE == 'soft' else (2.6, .6, .4)


def rounded(inset, z, thickness):
    x, y = X + inset, Y + inset
    w, h, r = W - 2 * inset, H - 2 * inset, PLAN_RADIUS - inset
    shapes = [Part.makeBox(w - 2*r, h, thickness, V(x+r, y, z)),
              Part.makeBox(w, h - 2*r, thickness, V(x, y+r, z))]
    shapes += [Part.makeCylinder(r, thickness, V(a, b, z))
               for a in (x+r, x+w-r) for b in (y+r, y+h-r)]
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def horizontal_edges(shape, z):
    return [e for e in shape.Edges if abs(e.BoundBox.ZMin-z) < 1e-6
            and abs(e.BoundBox.ZMax-z) < 1e-6]


def add(name, shape, color, transparency=0):
    obj = doc.addObject('PartDesign::Feature', name)
    obj.Shape = shape
    obj.addProperty('App::PropertyColor', 'StudyColor')
    obj.StudyColor = color
    obj.addProperty('App::PropertyInteger', 'StudyTransparency')
    obj.StudyTransparency = transparency
    return obj


def overlap(a, b):
    return a.common(b).Volume


src = App.openDocument(str(SOURCE))
doc = App.newDocument('R1InsetRearCoverStudy')
outer = rounded(0, 0, HEIGHT)
outer = outer.makeFillet(FRONT_RADIUS, horizontal_edges(outer, HEIGHT))
outer = outer.makeFillet(REAR_RADIUS, horizontal_edges(outer, 0))
body = outer.cut(rounded(WALL, -1, HEIGHT-PANEL+1)).removeSplitter()
wx, wy, ww, wh = C['screen']['window_xywh_mm']
# Round the aperture without consuming the existing 0.4 mm active-area margin.
window = Part.makeBox(ww-.6, wh, 2, V(wx+.3, wy, 4.5)).fuse(
    Part.makeBox(ww, wh-.6, 2, V(wx, wy+.3, 4.5)))
for a in (wx+.3, wx+ww-.3):
    for b in (wy+.3, wy+wh-.3):
        window = window.fuse(Part.makeCylinder(.3, 2, V(a, b, 4.5)))
body = body.cut(window).removeSplitter()
for x, y in C['keys_xy_mm']:
    body = body.cut(Part.makeCylinder(2.6, 2, V(x, y, 4.5)))
# All remaining coplanar front edges are aperture edges; outer fillets are lower.
front_edges = [e for e in horizontal_edges(body, HEIGHT)
               if wx-.01 <= e.CenterOfMass.x <= wx+ww+.01
               and wy-.01 <= e.CenterOfMass.y <= wy+wh+.01]
for x, y in C['keys_xy_mm']:
    front_edges += [e for e in horizontal_edges(body, HEIGHT)
                    if (e.CenterOfMass.x-x)**2+(e.CenterOfMass.y-y)**2 < .01]
body = body.makeFillet(.12, front_edges)
rx, ry, rw, rh = C['usb']['case_relief_xywh_mm']
relief = Part.makeBox(rw, rh, HEIGHT+2, V(rx, ry, -1))
body = body.cut(relief).removeSplitter()
# Soften exposed USB notch edges, retaining the original connector datum.
usb_edges = [e for e in body.Edges if abs(e.BoundBox.XMin-rx) < 1e-5
             and abs(e.BoundBox.XMax-rx) < 1e-5]
body = body.makeFillet(.12, usb_edges)
rear_inner_edges = [e for e in horizontal_edges(body, 0)
                    if e.BoundBox.XMin >= X+WALL-1e-6
                    and e.BoundBox.XMax <= X+W-WALL+1e-6
                    and e.BoundBox.YMin >= Y+WALL-1e-6
                    and e.BoundBox.YMax <= Y+H-WALL+1e-6]
body = body.makeFillet(.08, rear_inner_edges)
cover = rounded(WALL+GAP, 0, PANEL).cut(relief).removeSplitter()
cover = cover.makeFillet(.08, horizontal_edges(cover, 0))
for x, y in C['swd']['pad_centers_mm']:
    cover = cover.cut(Part.makeCylinder(1, 1, V(x, y, -.1)))
debug_edges = [e for e in horizontal_edges(cover, 0)
               if any((e.CenterOfMass.x-x)**2+(e.CenterOfMass.y-y)**2 < .01
                      for x, y in C['swd']['pad_centers_mm'])]
cover = cover.makeFillet(.08, debug_edges)
upper = add('RoundedUpperShell', body, (.71, .84, .88), 45)
rear = add('InsetRearCover', cover, (.82, .90, .91), 25)
copied = []
for old in src.Objects:
    if not hasattr(old, 'Shape') or not old.Shape.Solids:
        continue
    if old.Name in ('ClearTray', 'ClearLid', 'LidSeamPSA') or old.Name.endswith('ServiceVolume'):
        continue
    shape = old.Shape.copy()
    if old.Name.startswith('ClearKey'):
        shape = shape.makeFillet(.2, horizontal_edges(shape, shape.BoundBox.ZMax))
    color = old.DesignColor if hasattr(old, 'DesignColor') else (.5, .5, .5)
    copied.append(add(old.Name, shape, color))

pcb = doc.getObject('PCB').Shape
pb = pcb.BoundBox
# Calibrate the intersection calculation on a deliberately asymmetric fixture.
control_a = Part.makeBox(2, 3, 4)
control_b = Part.makeBox(2, 3, 4, V(1, 0, 0))
assert abs(overlap(control_a, control_b)-12) < 1e-8

top_faces = [f for f in pcb.Faces
             if abs(f.BoundBox.ZMin-pb.ZMax) < 1e-6 and abs(f.BoundBox.ZMax-pb.ZMax) < 1e-6]
assert top_faces
pcb_sweep = Part.makeCompound([f.extrude(V(0, 0, -12)) for f in top_faces])
insertion = {'PCB_exact_outline': overlap(pcb_sweep, body)}
# Component boxes conservatively bound every intermediate position, not just samples.
for obj in copied:
    if not obj.Name.startswith('Component_'):
        continue
    b = obj.Shape.BoundBox
    swept_box = Part.makeBox(b.XLength, b.YLength, b.ZMax+10, V(b.XMin, b.YMin, -10))
    insertion[obj.Name] = overlap(swept_box, body)

ledges = []
for inset in (1.2, 1.4, 1.7, 2.0):
    ring = rounded(0, 0, 1).cut(rounded(inset, -.1, 1.2)).cut(relief)
    ledges.append({'inset_mm': inset, 'opening_xy_mm': [W-2*inset, H-2*inset],
                   'straight_edge_gap_mm': (W-2*inset-pb.XLength)/2,
                   'pcb_sweep_intersection_mm3': overlap(pcb_sweep, ring)})

static = {o.Name: {'upper_mm3': overlap(o.Shape, body), 'rear_mm3': overlap(o.Shape, cover)}
          for o in copied}
key_motion = {}
for name, switch_name in zip(['ClearKey1','ClearKey2','ClearKey3'], ['SW1','SW3','SW2']):
    key = doc.getObject(name).Shape.copy()
    switch = doc.getObject('Component_'+switch_name).Shape
    x, y = key.BoundBox.Center.x, key.BoundBox.Center.y
    travel = key.BoundBox.ZMin-switch.BoundBox.ZMax+.45
    key.translate(V(0, 0, -travel))
    fixed = switch.cut(Part.makeCylinder(1.4, 3, V(x, y, pb.ZMax-.2)))
    key_motion[name] = {'translation_mm': travel, 'upper_mm3': overlap(key, body),
                        'fixed_switch_mm3': overlap(key, fixed)}
doc.recompute()
output_cad = OUT / 'rear-cover-study.FCStd'
doc.saveAs(str(output_cad))
Part.export([upper, rear], str(OUT/'rear-cover-study.step'))
for name, obj in [('upper', upper), ('rear', rear)]:
    Mesh.export([obj], str(OUT/(name+'.stl')))
mesh_results = {name: Mesh.Mesh(str(OUT/(name+'.stl'))).isSolid() for name in ('upper','rear')}
App.closeDocument(doc.Name)
reopened = App.openDocument(str(output_cad))
reopen_results = {name: {'valid': reopened.getObject(name).Shape.isValid(),
                         'solids': len(reopened.getObject(name).Shape.Solids)}
                  for name in ('RoundedUpperShell', 'InsetRearCover')}
assert all(v['valid'] and v['solids'] == 1 for v in reopen_results.values())
assert all(mesh_results.values())
assert all(v < 1e-6 for v in insertion.values()), insertion
assert all(v < 1e-6 for row in static.values() for v in row.values()), static
assert all(row['upper_mm3'] < 1e-6 and row['fixed_switch_mm3'] < 1e-6 for row in key_motion.values())
assert ledges[-1]['pcb_sweep_intersection_mm3'] > 1
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in hashes.items())
report = {
    'status': 'GEOMETRY_STUDY_ONLY_CLOSURE_NOT_QUALIFIED', 'source_sha256': hashes, 'style': STYLE,
    'dimensions_mm': {'outer': [W,H,HEIGHT], 'pcb_measured': [pb.XLength,pb.YLength],
        'rear_entry': [W-2*WALL,H-2*WALL], 'cover': [W-2*(WALL+GAP),H-2*(WALL+GAP),PANEL],
        'rear_seam_body_edge_inset': WALL, 'rear_seam_center_inset': WALL+GAP/2,
        'radial_gap': GAP, 'front_outer_radius': FRONT_RADIUS, 'rear_outer_radius': REAR_RADIUS,
        'plan_outer_radius': PLAN_RADIUS, 'rear_flat_rim_width': WALL-REAR_RADIUS-.08, 'front_opening_edge_radius': .12,
        'rear_seam_mouth_width': GAP+2*.08, 'upper_rear_seam_edge_radius': .08,
        'cover_rear_edge_radius': .08, 'key_face_edge_radius': .2},
    'pcb_min_distance_to_upper_mm': pcb.distToShape(body)[0],
    'cover_min_distance_to_upper_mm': cover.distToShape(body)[0],
    'ledge_comparison': ledges, 'static_intersections_mm3': static,
    'straight_insertion_upper_intersections_mm3': insertion,
    'maximum_key_motion': key_motion, 'reopened': reopen_results, 'closed_meshes': mesh_results,
    'limits': ['Frozen source CAD geometry; does not claim synchronization to live copper or new battery wiring.',
        'No continuous inward shelf: cover needs an alignment fixture and an unqualified vertical adhesive joint.',
        '0.25 mm nominal seam is a design allocation, not a tolerance-qualified fit.',
        'Source PCB/component shape or conservative boxes clear the upper shell during straight insertion; this excludes loose wires, actual flex, tools and assembly fixtures.',
        'Screen and keycaps must be fitted into the upper shell before inserting the PCB; insertion past these items remains an assembly-process check.',
        '0.8 mm broad panels, local edge rounding, resin, glue, coating allowance and panel stiffness need supplier review and physical samples.',
        'Rear USB relief remains open through the outer rim, matching the existing USB access datum.',
        'No new snap fits, locators, production release, RF validation or electrical DRC are claimed.']}
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print('REAR_STUDY_OK', str(OUT))
