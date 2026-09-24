"""Read the saved rounded candidate without changing CAD or print exports."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Mesh
import Part

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'r1-rounded-rear-soft/rear-cover-study.FCStd'
OUT = Path(os.environ['NFC_PRINT_REVIEW_OUT']).resolve()
if OUT.exists():
    raise RuntimeError('Use a new report path to preserve earlier evidence.')
before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
doc = App.openDocument(str(SOURCE))
names = ['RoundedUpperShell', 'InsetRearCover', 'ClearKey1', 'ClearKey2', 'ClearKey3']
parts = {}
for name in names:
    shape = doc.getObject(name).Shape
    box = shape.BoundBox
    points, _ = shape.tessellate(0.005)
    sampled_bounds = [[min(getattr(p, axis) for p in points),
                       max(getattr(p, axis) for p in points)] for axis in ('x', 'y', 'z')]
    cylinders = []
    for face in shape.Faces:
        surface = face.Surface
        if isinstance(surface, Part.Cylinder):
            cylinders.append({'radius_mm': surface.Radius,
                              'center_xy_mm': [surface.Center.x, surface.Center.y],
                              'z_mm': [face.BoundBox.ZMin, face.BoundBox.ZMax]})
    parts[name] = {'valid': shape.isValid(), 'solids': len(shape.Solids),
                   'conservative_occ_bbox_mm': [box.XLength, box.YLength, box.ZLength],
                   'sampled_extent_mm': [hi - lo for lo, hi in sampled_bounds],
                   'sampled_bounds_mm': sampled_bounds,
                   'z_mm': [box.ZMin, box.ZMax], 'volume_mm3': shape.Volume,
                   'cylindrical_faces': cylinders}
upper = doc.getObject(names[0]).Shape
rear = doc.getObject(names[1]).Shape
pcb = doc.getObject('PCB').Shape
report = {
    'status': 'NOMINAL_GEOMETRY_ONLY_PROCESS_NOT_QUALIFIED',
    'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': before,
    'extent_method': 'Surface tessellation at 0.005 mm; approximate. OCC boxes may overbound spline fillets.',
    'parts': parts,
    'nominal_distances_mm': {
        'pcb_to_upper': pcb.distToShape(upper)[0],
        'rear_to_upper': rear.distToShape(upper)[0],
        **{name + '_to_upper': doc.getObject(name).Shape.distToShape(upper)[0]
           for name in names[2:]},
    },
    'shell_intersection_mm3': upper.common(rear).Volume,
    'meshes': {},
    'limits': ['No strength, warpage, coating, adhesive or hardware testing.',
               'Frozen component geometry excludes current battery wiring and ferrite changes.',
               'This script does not sample global minimum wall thickness.'],
}
for name in ('upper', 'rear'):
    mesh = Mesh.Mesh(str(SOURCE.parent / (name + '.stl')))
    report['meshes'][name] = {'closed': mesh.isSolid(), 'facets': mesh.CountFacets}
App.closeDocument(doc.Name)
report['source_unchanged'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before
assert report['source_unchanged']
assert all(p['valid'] and p['solids'] == 1 for p in parts.values())
assert all(m['closed'] for m in report['meshes'].values())
assert report['shell_intersection_mm3'] < 1e-8
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'report': str(OUT)}))
