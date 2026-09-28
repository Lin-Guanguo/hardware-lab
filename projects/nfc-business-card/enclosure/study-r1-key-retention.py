"""Build a recessed key flange for supplier review at the fixed case height."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'r1-usb-fit-4.8/rear-cover-study.FCStd'
OUT=Path(os.environ['NFC_KEY_RETENTION_OUT']).resolve()
OUT.mkdir(parents=True,exist_ok=False)
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
doc=App.openDocument(str(SOURCE))
V=App.Vector
centers=[(41.1,4.5),(41.1,14.4),(49.6,8.80000526)]
switches=['SW1','SW3','SW2']
upper=doc.getObject('RoundedUpperShell').Shape
rear=doc.getObject('InsetRearCover').Shape
pcb=doc.getObject('PCB').Shape
checks=[]
for i,((x,y),ref) in enumerate(zip(centers,switches),1):
    old=doc.getObject('ClearKey'+str(i))
    tip=3.32
    top,bottom,face=3.95,3.15,4.77
    cap=Part.makeCylinder(3.4,.8,V(x,y,bottom)).fuse(Part.makeCylinder(2,face-bottom,V(x,y,bottom)))
    pocket=Part.makeBox(5.6,5.6,.41,V(x-2.8,y-2.8,bottom-.01))
    pocket=pocket.cut(Part.makeCylinder(1.3,.43,V(x,y,bottom-.02)))
    cap=cap.cut(pocket)
    cap=cap.cut(Part.makeCylinder(1.3,tip-bottom+.01,V(x,y,bottom-.01))).removeSplitter()
    edges=[e for e in cap.Edges if abs(e.BoundBox.ZMin-face)<1e-7 and abs(e.BoundBox.ZMax-face)<1e-7]
    cap=cap.makeFillet(.2,edges)
    switch=doc.getObject('Component_'+ref).Shape
    gap=tip-switch.BoundBox.ZMax
    travel=gap+.45
    fixed=switch.cut(Part.makeCylinder(1.4,3,V(x,y,pcb.BoundBox.ZMax-.2)))
    lower_faces=[f for f in cap.Faces if isinstance(f.Surface,Part.Plane) and f.normalAt(0,0).z<-.99]
    sweep=cap.multiFuse([f.extrude(V(0,0,-travel)) for f in lower_faces]).removeSplitter()
    hits={o.Name:sweep.common(o.Shape).Volume for o in doc.Objects
          if (o.Name.startswith('Component_') and o.Name!='Component_'+ref and o.Name!='Component_J1')
          or o.Name in ('PCB','RoundedUpperShell','InsetRearCover','ScreenNominal')}
    # The USB library BREP is invalid; use its conservative bounds.
    b=doc.getObject('Component_J1').Shape.BoundBox
    hits['USB_bounds']=sweep.common(Part.makeBox(b.XLength,b.YLength,b.ZLength,V(b.XMin,b.YMin,b.ZMin))).Volume
    hits['fixed_switch']=sweep.common(fixed).Volume
    rest=cap.common(switch).Volume
    assert cap.isValid() and len(cap.Solids)==1 and sweep.isValid()
    assert rest<1e-7 and max(hits.values())<1e-7,hits
    added=cap.cut(old.Shape).Volume
    assert added>0
    rotations={}
    for angle in (5,15,45):
        turned=sweep.copy()
        turned.rotate(V(x,y,0),V(0,0,1),angle)
        rotations[str(angle)]=turned.common(fixed).Volume
    # Added lobes remain in this annulus for every possible angular orientation.
    all_angles=Part.makeCylinder(3.4,.4+travel,V(x,y,bottom-travel)).cut(
        Part.makeCylinder(2.8,.42+travel,V(x,y,bottom-travel-.01)))
    rotation_hits={o.Name:all_angles.common(o.Shape).Volume for o in doc.Objects
                   if (o.Name.startswith('Component_') and o.Name!='Component_'+ref and o.Name!='Component_J1')
                   or o.Name in ('PCB','RoundedUpperShell','InsetRearCover','ScreenNominal')}
    rotation_hits['fixed_switch']=all_angles.common(fixed).Volume
    rotation_hits['USB_bounds']=all_angles.common(Part.makeBox(b.XLength,b.YLength,b.ZLength,V(b.XMin,b.YMin,b.ZMin))).Volume
    assert max(rotation_hits.values())<1e-7,rotation_hits
    old.Shape=cap
    checks.append({'key':i,'contact_gap_mm':gap,'checked_travel_mm':travel,'rest_switch_overlap_mm3':rest,
                   'sweep_intersections_mm3':hits,'added_flange_volume_mm3':added,
                   'roof_clearance_at_full_travel_mm':3.55-travel-fixed.BoundBox.ZMax,
                   'rotated_sweep_fixed_switch_overlap_mm3':rotations,
                   'full_rotation_added_lobes_sweep_intersections_mm3':rotation_hits})
doc.recompute()
doc.saveAs(str(OUT/'rear-cover-study.FCStd'))
exports={}
for i in range(1,4):
    shape=doc.getObject('ClearKey'+str(i)).Shape.copy()
    x,y=centers[i-1]
    shape.translate(V(-x,-y,-3.15))
    shape.exportStep(str(OUT/f'key-{i}.step'))
    MeshPart.meshFromShape(Shape=shape,LinearDeflection=.01,AngularDeflection=.12,Relative=False).write(str(OUT/f'key-{i}.stl'))
    assert Part.read(str(OUT/f'key-{i}.step')).isValid()
    assert Mesh.Mesh(str(OUT/f'key-{i}.stl')).isSolid()
    exports[str(i)]={'step_valid':True,'stl_closed':True,'size_nominal_mm':[6.8,6.8,1.62]}
Part.export([doc.getObject('RoundedUpperShell')],str(OUT/'matching-upper.step'))
App.closeDocument(doc.Name)
saved=App.openDocument(str(OUT/'rear-cover-study.FCStd'))
assert all(saved.getObject('ClearKey'+str(i)).Shape.isValid() for i in range(1,4))
App.closeDocument(saved.Name)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report={'status':'SUPPLIER_REVIEW_KEY_CANDIDATE_NOT_PRINT_QUALIFIED','source_sha256':source_hash,
        'outer_height_mm':4.8,'main_cavity_mm':3.2,'head_diameter_mm':4,'flange_diameter_mm':6.8,
        'flange_outer_axial_height_mm':.8,'recess_xy_mm':[5.6,5.6],'recess_depth_mm':.4,
        'remaining_roof_mm':.4,'central_post_diameter_mm':2.6,'head_edge_radius_mm':.2,
        'guide_hole_diameter_mm':5.2,'nominal_radial_guide_gap_mm':.6,
        'flange_radial_overlap_beyond_hole_mm':.8,'outer_lobe_width_at_axis_mm':.6,
        'keys':checks,'exports':exports,'source_unchanged':True,'saved_reopen_keys_valid':True,
        'all_angle_nominal_added_lobes_clear':True,
        'limits':['0.4 mm roof remains above the switch; this is not an all-0.8 mm wall design.',
                  '0.8 mm axial outer lobes have a maximum 0.6 mm radial width at the axes; supplier acceptance remains open.',
                  'No new elastic snap: flange is captured after rear assembly.',
                  'Added lobes pass a conservative full-rotation annulus check against nominal bodies; real switch geometry and tolerances remain unverified.',
                  'Sanding can remove excess material, not restore missing material or flange strength.',
                  '0.05 mm contact/rest allocations and 0.08 mm travel clearance require actual fitting.',
                  'PCB support assumption, actuator exclusion and other case limitations remain unchanged.']}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('KEY_RETENTION_COMPLETE',str(OUT/'report.json'))
