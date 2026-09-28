"""Integrate the checked thin keys into a USB-governed enclosure candidate."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part

ROOT = Path(__file__).resolve().parent
BASE = ROOT/'r1-rounded-rear-soft-swd254/rear-cover-study.FCStd'
KEY_SOURCE = Path(os.environ['NFC_THIN_KEY_SOURCE']).resolve()
OUT = Path(os.environ['NFC_USB_FIT_OUT']).resolve()
OUT.mkdir(parents=True, exist_ok=False)
hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE,KEY_SOURCE)}
key_report = json.loads((KEY_SOURCE.parent/'report.json').read_text())
assert key_report['status']=='THIN_KEYS_PASS_HYPOTHETICAL_MOUNT_NOT_COMPLETE_ASSEMBLY'
assert key_report['source_sha256']==hashes[str(BASE)]
base = App.openDocument(str(BASE))
thin = App.openDocument(str(KEY_SOURCE))
V = App.Vector
HEIGHT, FLOOR, SUPPORT, USB_GAP = 4.8,.8,.12,.10
doc = App.newDocument('R1USBHeightCandidate')


def add(name, shape, color=(.6,.62,.65)):
    obj = doc.addObject('Part::Feature',name)
    obj.Shape = shape
    obj.addProperty('App::PropertyColor','StudyColor')
    obj.StudyColor = color
    return obj


upper = thin.getObject('UpperEnvelopeBeforeUSBRelief').Shape.copy()
usb = thin.getObject('Component_J1').Shape.BoundBox
# A conservative box avoids relying on the known-invalid USB library BREP.
usb_envelope = Part.makeBox(usb.XLength,usb.YLength,usb.ZLength,V(usb.XMin,usb.YMin,usb.ZMin))
pocket_top = usb.ZMax+USB_GAP
relief = Part.makeBox(usb.XLength+.4,usb.YLength+.4,pocket_top-3.9,
                      V(usb.XMin-.2,usb.YMin-.2,3.9))
upper = upper.cut(relief).removeSplitter()
rear = base.getObject('InsetRearCover').Shape.copy()
add('RoundedUpperShell',upper,(.71,.84,.88))
add('InsetRearCover',rear,(.82,.90,.91))
for obj in thin.Objects:
    if obj.Name=='PCB' or obj.Name.startswith('Component_'):
        add(obj.Name,obj.Shape.copy(),(.12,.40,.26) if obj.Name=='PCB' else (.6,.62,.65))
for i in range(1,4):
    add('ClearKey'+str(i),thin.getObject('Key'+str(i)).Shape.copy(),(.8,.88,.92))
for obj in base.Objects:
    if obj.Name.startswith('PCBSupport'):
        b=obj.Shape.BoundBox
        add(obj.Name,Part.makeBox(b.XLength,b.YLength,SUPPORT,V(b.XMin,b.YMin,FLOOR)),(.85,.9,.92))
    elif obj.Name in ('ScreenNominal','ScreenPSA'):
        shape=obj.Shape.copy()
        shape.translate(V(0,0,-1))
        add(obj.Name,shape,(.72,.74,.73) if obj.Name=='ScreenNominal' else (.85,.9,.95))

pcb = doc.getObject('PCB').Shape
pb = pcb.BoundBox
assert abs(pb.ZMin-(FLOOR+SUPPORT))<.0001
static={}
for obj in doc.Objects:
    if obj.Name in ('RoundedUpperShell','InsetRearCover'):
        continue
    shape=usb_envelope if obj.Name=='Component_J1' else obj.Shape
    static[obj.Name]={'upper':shape.common(upper).Volume,'rear':shape.common(rear).Volume}
assert max(v for row in static.values() for v in row.values())<1e-7, static
assert upper.common(rear).Volume<1e-7
screen=doc.getObject('ScreenNominal').Shape.BoundBox
screen_max=Part.makeBox(37.42,31.9,1,V(1.95,18.25,HEIGHT-.8-.06-1))
screen_hits={o.Name:(usb_envelope if o.Name=='Component_J1' else o.Shape).common(screen_max).Volume
             for o in doc.Objects if o.Name=='PCB' or o.Name.startswith('Component_')}
assert max(screen_hits.values())<1e-7,screen_hits
mcu=doc.getObject('Component_U1').Shape.BoundBox
mcu_max=Part.makeBox(mcu.XLength+.2,mcu.YLength+.2,2.2,V(mcu.XMin-.1,mcu.YMin-.1,pb.ZMax))
assert mcu_max.common(upper).Volume<1e-7
faces=[f for f in pcb.Faces if abs(f.BoundBox.ZMin-pb.ZMax)<1e-6 and abs(f.BoundBox.ZMax-pb.ZMax)<1e-6]
insertion={'PCB':Part.makeCompound([f.extrude(V(0,0,-10)) for f in faces]).common(upper).Volume}
for obj in doc.Objects:
    if obj.Name.startswith('Component_'):
        b=obj.Shape.BoundBox
        sweep=Part.makeBox(b.XLength,b.YLength,b.ZMax+10,V(b.XMin,b.YMin,-10))
        insertion[obj.Name]=sweep.common(upper).Volume
assert max(insertion.values())<1e-7,insertion
battery_space=Part.makeBox(32.5,14,3.2,V(1.5,1.5,FLOOR))
battery_hits={obj.Name:battery_space.common(usb_envelope if obj.Name=='Component_J1' else obj.Shape).Volume
              for obj in doc.Objects}
assert max(battery_hits.values())<1e-7,battery_hits
parts=['RoundedUpperShell','InsetRearCover','ClearKey1','ClearKey2','ClearKey3']
for name in parts:
    shape=doc.getObject(name).Shape
    assert shape.isValid() and len(shape.Solids)==1
    shape.exportStep(str(OUT/(name+'.step')))
    MeshPart.meshFromShape(Shape=shape,LinearDeflection=.02,AngularDeflection=.15,Relative=False).write(str(OUT/(name+'.stl')))
Part.export([doc.getObject(n) for n in parts],str(OUT/'parts.step'))
doc.recompute()
doc.saveAs(str(OUT/'rear-cover-study.FCStd'))
App.closeDocument(doc.Name)
saved=App.openDocument(str(OUT/'rear-cover-study.FCStd'))
assert all(saved.getObject(n).Shape.isValid() and len(saved.getObject(n).Shape.Solids)==1 for n in parts)
exports={}
for name in parts:
    mesh=Mesh.Mesh(str(OUT/(name+'.stl')))
    shape=Part.read(str(OUT/(name+'.step')))
    assert mesh.isSolid() and shape.isValid() and len(shape.Solids)==1
    exports[name]={'stl_closed':True,'step_valid_single_solid':True}
combined=Part.read(str(OUT/'parts.step'))
assert combined.isValid() and len(combined.Solids)==5
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
report={'status':'USB_FIT_CAD_CANDIDATE_NOT_MANUFACTURING_QUALIFIED','source_hashes':hashes,
        'outer_nominal_mm':[85.2,53.2,HEIGHT],'main_cavity_mm':3.2,'pcb_support_assumption_mm':SUPPORT,
        'usb_model_bounds_mm':[usb.XMin,usb.YMin,usb.ZMin,usb.XMax,usb.YMax,usb.ZMax],
        'usb_relief_xywh_mm':[usb.XMin-.2,usb.YMin-.2,usb.XLength+.4,usb.YLength+.4],
        'usb_relief_depth_mm':pocket_top-(HEIGHT-.8),'usb_roof_remaining_mm':HEIGHT-pocket_top,
        'usb_local_cavity_mm':pocket_top-FLOOR,'usb_nominal_top_gap_mm':USB_GAP,
        'usb_bottom_gap_mm':usb.ZMin-FLOOR,'swd_pad_depth_from_rear_mm':pb.ZMin,
        'battery_reserved_box_mm':[1.5,1.5,FLOOR,32.5,14,3.2],
        'battery_reserved_box_intersections_mm3':battery_hits,
        'battery_fit':'User-managed; reserved geometry only, no battery or compression assumption.',
        'static_intersections_mm3':static,'screen_max_intersections_mm3':screen_hits,
        'straight_insertion_upper_mm3':insertion,'keys':key_report['keys'],'exports':exports,
        'saved_reopen_new_parts_valid':True,'source_unchanged':True,
        'limits':['0.12 mm support and 0.4 mm key flange require material/process qualification.',
                  'USB uses a conservative bounding box because its source library BREP is invalid.',
                  'Existing full-height side notch retained; its opening already spans lowered USB.',
                  'Nominal margins do not cover the complete manufacturing tolerance stack.',
                  'Battery fit, actual FPC/wires, closure retention, strength, key return and RF remain unverified.',
                  'Insertion checks upper shell only; screen/keys must be installed first and complete assembly sequence remains untested.']}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('USB_FIT_CANDIDATE_COMPLETE',str(OUT/'report.json'))
