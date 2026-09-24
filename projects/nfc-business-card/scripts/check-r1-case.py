"""Reopen R1 CAD and verify its new debug access and exported print meshes.

Run with FreeCAD's Python interpreter after building enclosure/r1-clear-5.8.
"""
import hashlib
import json
from pathlib import Path
import FreeCAD as App
import Part
import Mesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'enclosure/r1-clear-5.8'
c=json.loads((OUT/'design-inputs.json').read_text())
s=json.loads((ROOT/'hardware/records/r1-routed-snapshot.json').read_text())
r=json.loads((OUT/'e20-clear-report.json').read_text())
assert all(v['valid'] and v['solids']==1 for v in r['parts'].values())
assert all(abs(v-1)<1e-6 for v in r['checks']['support_coverage_fraction'].values())
intersections=[]
def visit(value,path=''):
    if isinstance(value,dict):
        if value.get('intersection_mm3',0)>1e-5:intersections.append(path)
        for k,v in value.items():visit(v,path+'/'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):visit(v,path+'/'+str(i))
visit(r['checks']);assert not intersections

doc=App.openDocument(str(OUT/'e20-clear-assembly.FCStd'))
tray=doc.getObject('ClearTray').Shape
supports=[o.Shape for o in doc.Objects if o.Name.startswith('PCBSupport')]
holes=[]
for i,(x,y) in enumerate(c['swd']['pad_centers_mm'],1):
    pad=next(p for p in s['pads'] if p['number']==f'TP{i}')
    error=((pad['x']*.0254-x)**2+(pad['y']*.0254-y)**2)**.5
    assert error<.002
    radius=c['swd']['access_hole_diameter_mm']/2
    bore_faces=[f for f in tray.Faces if isinstance(f.Surface,Part.Cylinder)
                and abs(f.Surface.Radius-radius)<1e-7
                and abs(f.Surface.Center.x-x)<1e-7 and abs(f.Surface.Center.y-y)<1e-7]
    assert len(bore_faces)==1
    probe=Part.makeCylinder(radius-.01,1.13,App.Vector(x,y,-.01))
    volume=probe.common(tray).Volume+sum(probe.common(p).Volume for p in supports)
    assert volume<1e-6
    holes.append({'pad':f'TP{i}','center_mm':[x,y],'registration_error_mm':error,'blocked_volume_mm3':volume,
                  'bore_diameter_mm':radius*2,'outer_mouth_radius_mm':c['swd'].get('access_hole_mouth_radius_mm',0)})
# Old screen-area access holes must be closed in the new tray.
for x in [5.00126,7.50062,9.99998,12.49934,15.00124]:
    plug=Part.makeCylinder(.8,.6,App.Vector(x,45.9994,.1))
    assert abs(plug.common(tray).Volume-plug.Volume)<1e-6
meshes={}
for name in ('tray','lid','keys'):
    path=OUT/f'e20-clear-{name}.stl';mesh=Mesh.Mesh(str(path))
    assert mesh.isSolid()
    meshes[name]={'closed_solid':True,'facets':mesh.CountFacets,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
report={'status':'NOMINAL_CAD_AND_PRINT_MESH_PASS','total_height_mm':5.8,'intersection_count':0,
        'debug_access':holes,'old_screen_access_holes_closed':True,'supports_fully_on_board':True,'meshes':meshes,
        'screen_back_to_pcb_mm':r['screen_back_max_mm']-r['pcb_top_mm'],
        'cad_sha256':hashlib.sha256((OUT/'e20-clear-assembly.FCStd').read_bytes()).hexdigest(),
        'pcb_snapshot_sha256':hashlib.sha256((ROOT/'hardware/records/r1-routed-snapshot.json').read_bytes()).hexdigest(),
        'limits':['Nominal geometry only; resin and assembly tolerances unqualified.',
                  'Generic 2.54 mm clip assumption; physical fixture fit untested.',
                  'Battery, flex, USB plug, key feel and adhesive retention require sample assembly.',
                  'Frozen CAD wire/ferrite bodies and 0.30 mm key travel checks do not qualify current wiring or maximum key travel.']}
(ROOT/'hardware/records/r1-mechanical-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
App.closeDocument(doc.Name)
