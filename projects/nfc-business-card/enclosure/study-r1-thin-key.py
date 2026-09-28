"""Check thin captive keys with a hypothetical lower PCB mounting stack."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'r1-rounded-rear-soft-swd254/rear-cover-study.FCStd'
OUT = Path(os.environ['NFC_THIN_KEY_OUT']).resolve()
OUT.mkdir(parents=True, exist_ok=False)
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
doc = App.openDocument(str(SOURCE))
V = App.Vector
height = 4.8
pcb_shift = -.2
flange = .4
centers = [(41.1,4.5), (41.1,14.4), (49.6,8.80000526)]
switches = ['SW1','SW3','SW2']
original = doc.getObject('RoundedUpperShell').Shape
lower = original.common(Part.makeBox(100,70,3.5,V(-5,-5,-1)))
top = original.common(Part.makeBox(100,70,5,V(-5,-5,3.5)))
top.translate(V(0,0,-1))
upper = lower.fuse(top).removeSplitter()
assert upper.isValid() and len(upper.Solids)==1
components = {}
for obj in doc.Objects:
    if obj.Name=='PCB' or obj.Name.startswith('Component_'):
        shape = obj.Shape.copy()
        shape.translate(V(0,0,pcb_shift))
        components[obj.Name] = shape
component_validity = {name:shape.isValid() for name,shape in components.items()}
keys = []
for i, ((x,y), switch_name) in enumerate(zip(centers,switches),1):
    switch = components['Component_'+switch_name]
    tip = doc.getObject('ClearKey'+str(i)).Shape.BoundBox.ZMin+pcb_shift
    face, bottom = height-.03, height-.8-.05-flange
    cap = Part.makeCylinder(3.4,flange,V(x,y,bottom)).fuse(
        Part.makeCylinder(2,face-bottom,V(x,y,bottom))).fuse(
        Part.makeCylinder(1.3,bottom-tip,V(x,y,tip))).removeSplitter()
    edges = [e for e in cap.Edges if abs(e.BoundBox.ZMin-face)<1e-7 and abs(e.BoundBox.ZMax-face)<1e-7]
    cap = cap.makeFillet(.2,edges)
    gap = tip-switch.BoundBox.ZMax
    travel = gap+.45
    fixed = switch.cut(Part.makeCylinder(1.4,3,V(x,y,components['PCB'].BoundBox.ZMax-.2)))
    faces = [f for f in cap.Faces if isinstance(f.Surface,Part.Plane) and f.normalAt(0,0).z<-.99]
    sweep = cap.multiFuse([f.extrude(V(0,0,-travel)) for f in faces]).removeSplitter()
    hits = {name:sweep.common(shape).Volume for name,shape in components.items()
            if name!='Component_'+switch_name}
    hits.update(upper=sweep.common(upper).Volume, fixed_switch=sweep.common(fixed).Volume)
    rest_overlap = cap.common(switch).Volume
    assert cap.isValid() and len(cap.Solids)==1 and sweep.isValid()
    assert rest_overlap<1e-7 and max(hits.values())<1e-7, hits
    keys.append({'key':i, 'contact_gap_mm':gap, 'checked_translation_mm':travel,
                 'flange_to_fixed_body_vertical_gap_mm':bottom-travel-fixed.BoundBox.ZMax,
                 'rest_overlap_mm3':rest_overlap, 'motion_hits_mm3':hits})
    obj = doc.getObject('ClearKey'+str(i))
    obj.Shape = cap

report = {'status':'THIN_KEYS_PASS_HYPOTHETICAL_MOUNT_NOT_COMPLETE_ASSEMBLY',
          'source_sha256':source_hash,'outer_height_mm':height,'main_cavity_mm':height-1.6,
          'assumed_pcb_support_mm':.12,'pcb_lowered_mm':-pcb_shift,
          'key_flange_mm':flange,'key_face_diameter_mm':4,'key_flange_diameter_mm':6.8,
          'key_stem_diameter_mm':2.6,'keys':keys,
          'regional_gaps_before_relief_mm':{
              'usb':height-.8-components['Component_J1'].BoundBox.ZMax,
              'mcu_max':height-.8-components['PCB'].BoundBox.ZMax-2.2,
              'fpc':height-.8-components['Component_J2'].BoundBox.ZMax,
              'screen_max_to_assumed_solder_1mm':height-.8-.06-1-components['PCB'].BoundBox.ZMax-1},
          'limits':['0.12 mm support is an unqualified design assumption; no material stack selected.',
                    'USB needs local relief and a lowered opening; neither is modeled here.',
                    'Battery, support solids, screen, rear fit and assembly sequence are not checked.',
                    '0.4 mm flange is a custom part proposal; no matching stock key or print qualification.',
                    '0.05 mm axial gap and 1.4 mm moving actuator exclusion remain assumptions.',
                    'No battery compression or compressed battery dimension is used.']}
# Save only the scope checked; do not present stale supports or battery as a fitted assembly.
study = App.newDocument('ThinKeyStudy')
for name,shape in [('UpperEnvelopeBeforeUSBRelief',upper),*components.items(),
                   *[(f'Key{i}',doc.getObject(f'ClearKey{i}').Shape) for i in range(1,4)]]:
    study.addObject('Part::Feature',name).Shape=shape
study.recompute()
study.saveAs(str(OUT/'thin-key-study.FCStd'))
App.closeDocument(study.Name)
saved=App.openDocument(str(OUT/'thin-key-study.FCStd'))
assert all(saved.getObject(name).Shape.isValid() for name in
           ['UpperEnvelopeBeforeUSBRelief','Key1','Key2','Key3'])
assert {name:saved.getObject(name).Shape.isValid() for name in components} == component_validity
report['preexisting_invalid_library_shapes'] = [name for name,valid in component_validity.items() if not valid]
App.closeDocument(saved.Name)
App.closeDocument(doc.Name)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report['saved_reopen_valid']=True
report['source_unchanged']=True
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],str(OUT/'report.json'))
