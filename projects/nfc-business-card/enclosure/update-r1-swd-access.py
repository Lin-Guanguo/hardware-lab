"""Revise rounded or packed-case SWD holes into a new output directory."""
import hashlib
import json
import os
import shutil
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part

ROOT = Path(__file__).resolve().parent
PACKED = os.environ.get('NFC_SWD_ACCESS_VARIANT', 'rounded') == 'packed'
SOURCE = Path(os.environ.get('NFC_SWD_ACCESS_SOURCE', str(ROOT / (
    'r1-clear-5.8/e20-clear-assembly.FCStd' if PACKED else
    'r1-rounded-rear-soft/rear-cover-study.FCStd')))).resolve()
OUT = Path(os.environ['NFC_SWD_ACCESS_OUT']).resolve()
if OUT.exists():
    raise RuntimeError('Use a new directory; preserve existing and unsaved CAD.')
OUT.mkdir(parents=True)
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
V = App.Vector
CENTERS = [(x, 48.49876) for x in (65.92062, 68.46062, 71.00062, 73.54062, 76.08062)]
DIAMETER, MOUTH_RADIUS, THICKNESS = 1.6, .05, .8
doc = App.openDocument(str(SOURCE))
rear_obj = doc.getObject('ClearTray' if PACKED else 'InsetRearCover')
original = rear_obj.Shape.copy()
unchanged = {o.Name: o.Shape.exportBrepToString() for o in doc.Objects
             if hasattr(o, 'Shape') and o.Name != rear_obj.Name}
# Plugs include the old R0.08 mouths and remain inside the planar cover boundary.
old_centers = (json.loads((SOURCE.parent/'design-inputs.json').read_text())['swd']['pad_centers_mm']
               if PACKED else [(x, 48.5) for x in (65, 68, 71, 74, 77)])
plugs = [Part.makeCylinder(1.2, THICKNESS, V(x, y, 0)) for x, y in old_centers]
blank = original.multiFuse(plugs).removeSplitter()
holes = [Part.makeCylinder(DIAMETER/2, THICKNESS+2, V(x, y, -1)) for x, y in CENTERS]
rear = blank.cut(Part.makeCompound(holes)).removeSplitter()
mouth_edges = [e for e in rear.Edges
               if abs(e.BoundBox.ZMin) < 1e-7 and abs(e.BoundBox.ZMax) < 1e-7
               and any((e.CenterOfMass.x-x)**2+(e.CenterOfMass.y-y)**2 < 1e-10
                       for x, y in CENTERS)]
assert len(mouth_edges) == 5
rear = rear.makeFillet(MOUTH_RADIUS, mouth_edges)
rear_obj.Shape = rear
if 'AccessRevision' not in rear_obj.PropertiesList:
    rear_obj.addProperty('App::PropertyString', 'AccessRevision')
rear_obj.AccessRevision = 'SWD 1x5 2.54 mm; bore 1.60 mm; outer mouth R0.05; physical clip fit untested'
doc.recompute()
upper = doc.getObject('ClearLid' if PACKED else 'RoundedUpperShell').Shape
region = Part.makeBox(15.0, 3, 1.2, V(63.5, 47, -.2))
delta = original.cut(rear).fuse(rear.cut(original))
report = {
    'status': 'NOMINAL_SWD_ACCESS_UPDATED_NOT_PHYSICALLY_QUALIFIED',
    'source': os.path.relpath(SOURCE, ROOT), 'source_sha256': source_hash,
    'coordinate_system': 'PCB front-view XY; outside rear face Z=0',
    'centers_xy_mm': CENTERS,
    'net_order_increasing_x': ['GND', 'VDD_3V3/VTref', 'SWCLK', 'SWDIO', 'NRESET'],
    'pitch_mm': 2.54, 'bore_diameter_mm': DIAMETER,
    'outer_mouth_radius_mm': MOUTH_RADIUS,
    'outer_mouth_diameter_mm': DIAMETER+2*MOUTH_RADIUS,
    'cover_thickness_mm': THICKNESS,
    'straight_web_mm': 2.54-DIAMETER,
    'minimum_outer_surface_web_mm': 2.54-DIAMETER-2*MOUTH_RADIUS,
    'pad_depth_from_outer_rear_mm': doc.getObject('PCB').Shape.BoundBox.ZMin,
    'modified_volume_outside_access_region_mm3': delta.cut(region).Volume,
    'shell_intersection_mm3': rear.common(upper).Volume,
    'unchanged_objects': {}, 'hole_checks': [], 'exports': {},
    'limits': [
        'Generic single-row 5P 2.54 mm clip assumption accepted by user; no physical fit certification.',
        'The supplier image 1.5 mm label describes a fixture needle hole, not a verified probe tip diameter.',
        '1.6 mm bore and R0.05 mouth balance nominal access and remaining material; print and coating tolerances unqualified.',
        'Source PCB solid has no debug-pad copper; coordinates follow PCB task handoff, not a refreshed PCB STEP.',
        'No changes to RESET, thickness, keys, closure, antenna, PCB outline or battery service bodies.',
        'Existing closure, battery wire/ferrite and key-tolerance limitations remain.',
    ],
}
for name, old in unchanged.items():
    identical = doc.getObject(name).Shape.exportBrepToString() == old
    report['unchanged_objects'][name] = identical
    assert identical, name
for x, y in CENTERS:
    surfaces = [f for f in rear.Faces if isinstance(f.Surface, Part.Cylinder)
                and abs(f.Surface.Radius-DIAMETER/2) < 1e-7
                and abs(f.Surface.Center.x-x) < 1e-7 and abs(f.Surface.Center.y-y) < 1e-7]
    probe = Part.makeCylinder(.3, 1.12, V(x, y, 0))
    check = {'center_xy_mm': [x, y], 'cylindrical_faces': len(surfaces),
             'example_0_6mm_probe_shell_overlap_mm3': probe.common(rear.fuse(upper)).Volume}
    report['hole_checks'].append(check)
    assert len(surfaces) == 1 and check['example_0_6mm_probe_shell_overlap_mm3'] < 1e-8
assert rear.isValid() and len(rear.Solids) == 1
assert report['modified_volume_outside_access_region_mm3'] < 1e-8
assert report['shell_intersection_mm3'] < 1e-8
cad_name = 'e20-clear-assembly.FCStd' if PACKED else 'rear-cover-study.FCStd'
step_name = 'e20-clear-tray.step' if PACKED else 'rear.step'
stl_name = 'e20-clear-tray.stl' if PACKED else 'rear.stl'
assembly_name = 'e20-clear-assembly.step' if PACKED else 'rear-cover-study.step'
doc.saveAs(str(OUT/cad_name))
rear.exportStep(str(OUT/step_name))
physical = [o for o in doc.Objects if hasattr(o, 'Shape') and not o.Name.endswith('ServiceVolume')]
assembly_shapes = [o.Shape for o in physical] if PACKED else [upper, rear]
if PACKED:
    Part.export(physical, str(OUT/assembly_name))
else:
    Part.makeCompound(assembly_shapes).exportStep(str(OUT/assembly_name))
assembly_solids = sum(len(s.Solids) for s in assembly_shapes)
mesh = MeshPart.meshFromShape(Shape=rear, LinearDeflection=.02, AngularDeflection=.15, Relative=False)
mesh.write(str(OUT/stl_name))
if PACKED:
    for name in ('e20-clear-lid.step', 'e20-clear-lid.stl', 'e20-clear-keys.stl'):
        shutil.copyfile(SOURCE.parent/name, OUT/name)
    if (SOURCE.parent/'e20-clear-keys.step').exists():
        shutil.copyfile(SOURCE.parent/'e20-clear-keys.step', OUT/'e20-clear-keys.step')
    config = json.loads((SOURCE.parent/'design-inputs.json').read_text())
    config['swd'].update({'pad_centers_mm': CENTERS, 'pitch_mm': 2.54,
                          'access_hole_diameter_mm': DIAMETER, 'cover_hole_diameter_mm': DIAMETER,
                          'access_hole_mouth_radius_mm': MOUTH_RADIUS,
                          'tp1_shape': 'square, 1.19888 mm; TP2-TP5 round',
                          'fit_status': 'Generic 5P clip assumption; physical fit untested'})
    (OUT/'design-inputs.json').write_text(json.dumps(config, indent=2)+'\n')
    geometry = json.loads((SOURCE.parent/'e20-clear-report.json').read_text())
    geometry['debug_access'] = {'centers_mm': CENTERS, 'diameter_mm': DIAMETER,
                                'mouth_radius_mm': MOUTH_RADIUS, 'pitch_mm': 2.54}
    geometry['parts']['tray'] = {'valid': rear.isValid(), 'solids': len(rear.Solids)}
    def relation(shape):
        return {'clearance_mm': shape.distToShape(rear)[0], 'intersection_mm3': shape.common(rear).Volume}
    checks = geometry['checks']
    checks['components_to_tray'] = {o.Name.removeprefix('Component_'): relation(o.Shape)
                                    for o in doc.Objects if o.Name.startswith('Component_')}
    for key, name in [('battery_to_tray', 'BatteryMaximum'), ('board_to_tray', 'PCB'),
                      ('fpc_to_tray', 'FPCServiceVolume')]:
        checks[key] = relation(doc.getObject(name).Shape)
    screen_max = Part.makeBox(37.42, 31.9, 1, V(1.95, 18.25, geometry['screen_back_max_mm']))
    checks['screen_to_tray'] = relation(screen_max)
    for key in checks['keys']:
        shape = doc.getObject('ClearKey'+str(key['key'])).Shape
        key['tray_rest'] = relation(shape)
        pressed = shape.copy()
        pressed.translate(V(0, 0, -.30))
        key['tray_pressed'] = relation(pressed)
    geometry['swd_revision'] = {'source_cad_sha256': source_hash, 'local_check': 'swd-access-report.json',
                               'scope': 'Tray relations refreshed; all other bodies and historical checks retained.'}
    geometry['limits'].append('SWD holes use generic 2.54 mm fixture assumptions; physical clip fit untested.')
    (OUT/'e20-clear-report.json').write_text(json.dumps(geometry, indent=2)+'\n')
else:
    shutil.copyfile(SOURCE.parent/'upper.stl', OUT/'upper.stl')
App.closeDocument(doc.Name)
reopened = App.openDocument(str(OUT/cad_name))
saved = reopened.getObject('ClearTray' if PACKED else 'InsetRearCover').Shape
report['reopened_cad'] = {'valid': saved.isValid(), 'solids': len(saved.Solids),
                          'difference_mm3': saved.cut(rear).Volume+rear.cut(saved).Volume}
assert saved.isValid() and len(saved.Solids) == 1 and report['reopened_cad']['difference_mm3'] < 1e-8
App.closeDocument(reopened.Name)
for name, count in [(step_name, 1), (assembly_name, assembly_solids)]:
    shape = Part.read(str(OUT/name))
    report['exports'][name] = {'valid': shape.isValid(), 'solids': len(shape.Solids)}
    assert shape.isValid() and len(shape.Solids) == count
for name in ((stl_name, 'e20-clear-lid.stl', 'e20-clear-keys.stl') if PACKED else ('rear.stl', 'upper.stl')):
    loaded = Mesh.Mesh(str(OUT/name))
    report['exports'][name] = {'closed': loaded.isSolid(), 'facets': loaded.CountFacets}
    assert loaded.isSolid()
report['source_unchanged'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
assert report['source_unchanged']
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
if PACKED:
    (OUT/'swd-access-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status': report['status'], 'report': str(OUT/'report.json')}))
