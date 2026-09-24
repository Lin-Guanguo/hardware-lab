"""Study USB-driven thickness and recessed key undersides without editing the release."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'r1-rounded-rear-soft-swd254/rear-cover-study.FCStd'
TARGET_HEIGHT = float(os.environ.get('NFC_USB_HEIGHT_MM', '5.4'))
assert TARGET_HEIGHT in (4.6, 5.2, 5.3, 5.4)
BATTERY_HEIGHT = float(os.environ.get('NFC_USB_BATTERY_MM', '3.4'))
OUT = Path(os.environ['NFC_USB_HEIGHT_OUT']).resolve()
if OUT.exists():
    raise RuntimeError('Use a new output directory.')
OUT.mkdir(parents=True)
before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
doc = App.openDocument(str(SOURCE))
V = App.Vector
pcb_top = doc.getObject('PCB').Shape.BoundBox.ZMax
rear = doc.getObject('InsetRearCover').Shape.copy()
original_upper = doc.getObject('RoundedUpperShell').Shape.copy()
key_names = ['ClearKey1', 'ClearKey2', 'ClearKey3']
switch_names = ['SW1', 'SW3', 'SW2']
key_centers = [(41.1, 4.5), (41.1, 14.4), (49.6, 8.80000526)]
tips = [doc.getObject(n).Shape.BoundBox.ZMin for n in key_names]
if BATTERY_HEIGHT != 3.4:
    battery = doc.getObject('BatteryMaximum')
    b = battery.Shape.BoundBox
    battery.Shape = Part.makeBox(b.XLength,b.YLength,BATTERY_HEIGHT,V(b.XMin,b.YMin,b.ZMin))
    battery.addProperty('App::PropertyString','StudyAssumption')
    battery.StudyAssumption = 'User-reported 3 mm gauge fit; not a life-cycle maximum or compression allowance'


def shell_at(height):
    delta = 5.8-height
    lower = original_upper.common(Part.makeBox(100, 70, 3.5, V(-5, -5, -1)))
    top = original_upper.common(Part.makeBox(100, 70, 5, V(-5, -5, 2.5+delta)))
    top.translate(V(0, 0, -delta))
    return lower.fuse(top).removeSplitter()


def key_at(index, height, flange, recess):
    x, y = key_centers[index]
    bottom = height-.8-.05-flange
    face = height-.03
    cap = Part.makeCylinder(3.4, flange, V(x, y, bottom)).fuse(
        Part.makeCylinder(2, face-bottom, V(x, y, bottom)))
    if recess:
        pocket = Part.makeBox(5.6, 5.6, recess+.01, V(x-2.8, y-2.8, bottom-.01))
        # Preserve the central actuator post while relieving the switch housing.
        pocket = pocket.cut(Part.makeCylinder(1.3, recess+.03, V(x, y, bottom-.02)))
        cap = cap.cut(pocket)
    cap = cap.fuse(Part.makeCylinder(1.3, face-tips[index], V(x, y, tips[index]))).removeSplitter()
    if bottom < tips[index]:
        # Lower retention skirts must not extend the actuator post into the switch.
        cap = cap.cut(Part.makeCylinder(1.3, tips[index]-bottom+.01,
                                        V(x,y,bottom-.01))).removeSplitter()
    edges = [e for e in cap.Edges if abs(e.BoundBox.ZMin-face)<1e-7 and abs(e.BoundBox.ZMax-face)<1e-7]
    return cap.makeFillet(.2, edges)


def downward_sweep(shape, travel):
    # Every lower boundary is horizontal; extruding these faces covers all translations.
    faces = [f for f in shape.Faces if isinstance(f.Surface, Part.Plane) and f.normalAt(0, 0).z < -.99]
    assert faces
    return shape.multiFuse([f.extrude(V(0, 0, -travel)) for f in faces]).removeSplitter()


assert abs(Part.makeBox(2,3,4).common(Part.makeBox(2,3,4,V(1,0,0))).Volume-12)<1e-8
trials = []
chosen = None
for height, flange, recess in [(5.8,1,0), (5.6,.8,0), (5.4,.8,0), (5.2,.8,0),
                               (5.4,1,.4), (5.3,1,.4), (5.2,1,.4), (4.6,1,.4)]:
    upper = shell_at(height)
    row = {'height_mm': height, 'cavity_mm': height-1.6, 'flange_mm': flange,
           'underside_recess_mm': recess, 'remaining_roof_mm': flange-recess,
           'usb_top_gap_mm': height-.8-doc.getObject('Component_J1').Shape.BoundBox.ZMax,
           'battery_3_4mm_top_gap_mm': height-.8-(.8+.1+3.4),
           'battery_3_2mm_top_gap_mm': height-.8-(.8+.1+3.2), 'keys': []}
    caps = []
    for i, (x, y) in enumerate(key_centers):
        cap = key_at(i, height, flange, recess)
        switch = doc.getObject('Component_'+switch_names[i]).Shape
        gap = tips[i]-switch.BoundBox.ZMax
        travel = gap+.45
        fixed = switch.cut(Part.makeCylinder(1.4,3,V(x,y,pcb_top-.2)))
        sweep = downward_sweep(cap, travel)
        pressed = cap.copy()
        pressed.translate(V(0,0,-travel))
        other_hits = {o.Name: sweep.common(o.Shape).Volume for o in doc.Objects
                      if o.Name.startswith('Component_') and o.Name != 'Component_'+switch_names[i]}
        entry = {'key': key_names[i], 'initial_actuator_gap_mm': gap, 'translation_mm': travel,
                 'valid': cap.isValid(), 'solids': len(cap.Solids),
                 'sweep_valid': sweep.isValid(),
                 'rest_complete_switch_overlap_mm3': cap.common(switch).Volume,
                 'actual_central_tip_z_mm': cap.common(Part.makeCylinder(.5,10,V(x,y,0))).BoundBox.ZMin,
                 'sweep_upper_overlap_mm3': sweep.common(upper).Volume,
                 'sweep_fixed_switch_overlap_mm3': sweep.common(fixed).Volume,
                 'sweep_other_hits_mm3': {k:v for k,v in other_hits.items() if v>1e-7},
                 'pressed_fixed_switch_distance_mm': pressed.distToShape(fixed)[0],
                 'roof_vertical_clearance_mm': height-.8-.05-flange+recess-travel-fixed.BoundBox.ZMax,
                 'fixed_switch_top_z_mm': fixed.BoundBox.ZMax,
                 'rest_upper_distance_mm': cap.distToShape(upper)[0],
                 'sweep_pcb_overlap_mm3': sweep.common(doc.getObject('PCB').Shape).Volume}
        assert entry['valid'] and entry['solids']==1 and entry['sweep_valid']
        row['keys'].append(entry)
        caps.append(cap)
    trials.append(row)
    if recess and height == TARGET_HEIGHT:
        chosen = (upper, caps, row)

upper, caps, row = chosen
key_pass = all(k['sweep_fixed_switch_overlap_mm3']<1e-7 and k['sweep_upper_overlap_mm3']<1e-7
           and k['sweep_pcb_overlap_mm3']<1e-7 and k['rest_complete_switch_overlap_mm3']<1e-7
           and abs(k['actual_central_tip_z_mm']-tips[i])<1e-7
           and not k['sweep_other_hits_mm3'] for i,k in enumerate(row['keys']))
if TARGET_HEIGHT >= 5.2:
    assert key_pass
doc.getObject('RoundedUpperShell').Shape = upper
for name, cap in zip(key_names, caps):
    doc.getObject(name).Shape = cap
for name in ('ScreenNominal', 'ScreenPSA'):
    shape = doc.getObject(name).Shape.copy()
    shape.translate(V(0,0,TARGET_HEIGHT-5.8))
    doc.getObject(name).Shape = shape
static = {}
for obj in doc.Objects:
    if not hasattr(obj,'Shape') or obj.Name in ('RoundedUpperShell','InsetRearCover'):
        continue
    static[obj.Name] = obj.Shape.common(upper).Volume
static_pass = max(static.values())<1e-7
if TARGET_HEIGHT >= 5.2:
    assert static_pass, static
assert upper.isValid() and len(upper.Solids)==1 and upper.common(rear).Volume<1e-7
doc.recompute()
doc.saveAs(str(OUT/'rear-cover-study.FCStd'))
if key_pass and static_pass:
    for filename, shape in [('upper', upper), ('rear', rear), *[(f'key-{i+1}',s) for i,s in enumerate(caps)]]:
        shape.exportStep(str(OUT/(filename+'.step')))
        MeshPart.meshFromShape(Shape=shape, LinearDeflection=.02, AngularDeflection=.15,
                               Relative=False).write(str(OUT/(filename+'.stl')))
    Part.export([doc.getObject(n) for n in ['RoundedUpperShell','InsetRearCover',*key_names]], str(OUT/'print-parts.step'))
screen_max_bottom = TARGET_HEIGHT-.8-.06-1
report = {'status':('KEY_GEOMETRY_CANDIDATE_PROCESS_UNQUALIFIED' if key_pass and static_pass else
                    'INTERFERENCES_FOUND_DIAGNOSTIC_ONLY_NO_PRINT_EXPORTS'), 'source_sha256':before,
          'trials': trials, 'selected_height_mm':TARGET_HEIGHT,
          'battery_study_height_mm':BATTERY_HEIGHT, 'selected_key_motion_pass':key_pass,
          'selected_static_pass':static_pass,
          'selected_static_upper_intersections_mm3':static,
          'retained_rear_brep_equal':rear.exportBrepToString()==doc.getObject('InsetRearCover').Shape.exportBrepToString(),
          'regional_gaps_mm':{'usb':row['usb_top_gap_mm'], 'battery_3_4':row['battery_3_4mm_top_gap_mm'],
                              'battery_3_2_sensitivity_only':row['battery_3_2mm_top_gap_mm'],
                              'selected_battery':TARGET_HEIGHT-.8-(.8+.1+BATTERY_HEIGHT),
                              'fpc_connector':TARGET_HEIGHT-.8-doc.getObject('Component_J2').Shape.BoundBox.ZMax,
                              'mcu_max':TARGET_HEIGHT-.8-(pcb_top+2.2),
                              'screen_max_to_ferrite_0_25':screen_max_bottom-(pcb_top+.1+.25),
                              'screen_max_to_assumed_solder_1_0':screen_max_bottom-(pcb_top+1)},
          'sources':{'switch_travel':'https://tech.alpsalpine.com/cms.media/SKQGAB_KQG_719_EN_cc4e10226e.pdf#page=3'},
          'limits':['Battery height is an explicit study input; no permission to compress the cell or life-cycle size guarantee.',
                    'USB 3.49 mm occupied height is based on nominal library geometry, not a maximum supplier tolerance.',
                    'Relieved key has a 0.6 mm local roof and narrow outer skirts; strength and resin process unqualified.',
                    'Existing 0.05 mm axial/rest gaps remain smaller than an unqualified printing tolerance stack.',
                    'Fixed-switch exclusion retains the prior 1.4 mm actuator radius assumption; actual switch fit untested.',
                    '0.45 mm is the specification travel test upper bound, not a commanded operating stroke.',
                    'No removable closure, real FPC/wire routing, force/return test or manufacturing release.',
                    'Ferrite and solder gaps are stack calculations; their physical bodies were not added.'],
          'export_checks':{}}
App.closeDocument(doc.Name)
saved = App.openDocument(str(OUT/'rear-cover-study.FCStd'))
for name in ['RoundedUpperShell','InsetRearCover',*key_names]:
    shape = saved.getObject(name).Shape
    assert shape.isValid() and len(shape.Solids)==1
report['saved_reopen_valid']=True
App.closeDocument(saved.Name)
for path in OUT.glob('*.stl'):
    mesh = Mesh.Mesh(str(path))
    assert mesh.isSolid()
    report['export_checks'][path.name]={'closed':True,'facets':mesh.CountFacets}
for path in OUT.glob('*.step'):
    shape=Part.read(str(path))
    expected=5 if path.name=='print-parts.step' else 1
    assert shape.isValid() and len(shape.Solids)==expected
    report['export_checks'][path.name]={'valid':True,'solids':len(shape.Solids)}
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
report['source_unchanged']=True
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('USB_HEIGHT_STUDY_COMPLETE',report['status'],str(OUT/'report.json'))
