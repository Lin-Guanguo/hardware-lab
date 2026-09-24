"""Build the E20 sheet-cover assembly and verify solid clearances.

Run with FreeCAD's Python runtime and NFC_E20_OUT / NFC_E20_PCB environment
variables pointing to a new output directory and the native STEP export.
Dimensions not covered by a supplier drawing remain procurement requirements.
"""
import os
import json
import math
import re
from pathlib import Path
import FreeCAD as App
import Part
import Import
import Mesh

from types import SimpleNamespace
args = SimpleNamespace(output=Path(os.environ['NFC_E20_OUT']), pcb=Path(os.environ['NFC_E20_PCB']))
ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / 'enclosure/e20-v2/design-inputs.json').read_text())
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
if (OUT / 'e20-assembly.FCStd').exists():
    raise SystemExit('Choose a new output directory; existing assembly refused.')
S = C['stack']
PCB_Z = sum(S[k] for k in ('bottom_pc_mm', 'lower_psa_mm', 'pet_spacer_mm', 'upper_spacer_psa_mm'))
PCB_TOP = PCB_Z + S['pcb_mm']
FRAME_Z = PCB_TOP + S['frame_psa_mm']
FRAME_TOP = FRAME_Z + S['printed_frame_above_pcb_mm']
COVER_Z = FRAME_TOP + S['top_psa_mm']
TOTAL = COVER_Z + S['top_pc_mm']
V = App.Vector


def box(x, y, w, h, z, t):
    return Part.makeBox(w, h, t, V(x, y, z))


def rounded(x, y, w, h, r, z, t):
    pieces = [box(x+r, y, w-2*r, h, z, t), box(x, y+r, w, h-2*r, z, t)]
    pieces += [Part.makeCylinder(r, t, V(a, b, z)) for a in (x+r, x+w-r) for b in (y+r, y+h-r)]
    return pieces[0].multiFuse(pieces[1:]).removeSplitter()


def outline(z, t):
    data = json.loads((ROOT/'enclosure/e20-v2/outline-polygon-mm.json').read_text())
    p = V(data[0], data[1], z)
    edges = []
    i, mode = 2, 'L'
    while i < len(data):
        if isinstance(data[i], str):
            mode = data[i]; i += 1
        if mode == 'ARC':
            theta = math.radians(data[i]); q = V(data[i+1], data[i+2], z); i += 3
            delta = q-p
            center = (p+q)*.5 + V(-delta.y, delta.x, 0)/(2*math.tan(theta/2))
            rv = p-center
            mid = center + V(rv.x*math.cos(theta/2)-rv.y*math.sin(theta/2), rv.x*math.sin(theta/2)+rv.y*math.cos(theta/2), 0)
            edges.append(Part.Arc(p, mid, q).toShape())
            mode = 'L'
        else:
            q = V(data[i], data[i+1], z); i += 2
            edges.append(Part.makeLine(p, q))
        p = q
    return Part.Face(Part.Wire(edges)).extrude(V(0, 0, t))


def feature(name, shape, role, color=(.65,.75,.85)):
    o = doc.addObject('PartDesign::Feature', name)
    o.Shape = shape
    o.addProperty('App::PropertyString', 'Role'); o.Role = role
    o.addProperty('App::PropertyColor', 'DesignColor'); o.DesignColor = color
    if App.GuiUp:
        o.ViewObject.ShapeColor = color
    return o


def relation(a, b):
    return {'clearance_mm': a.distToShape(b)[0], 'intersection_mm3': a.common(b).Volume}


reference = App.newDocument('E20NativeReference')
Import.insert(str(args.pcb), reference.Name)
components = {}
expected_refs = {c['ref'] for c in json.loads((ROOT/'artifacts/e20-production-study/placed-snapshot.json').read_text())['components']}
for o in reference.Objects:
    match = re.match(r'^([A-Z]+\d+)~', o.Label)
    if match and match.group(1) in expected_refs and hasattr(o, 'Shape') and len(o.Shape.Solids):
        s = o.Shape.copy(); s.translate(V(0, 0, PCB_Z)); components[match.group(1)] = s
assert len(components) == 58, len(components)
# These asymmetric placements catch old exports and origin/axis mistakes.
assert abs(components['U1'].BoundBox.XMin-57.751) < .05
assert .15 < components['U1'].BoundBox.YMin < .35
assert abs(components['J1'].BoundBox.XMax-C['usb']['mating_face_x_mm']) < .03

doc = App.newDocument('E20SheetCoverAssembly')
board = outline(PCB_Z, S['pcb_mm'])
feature('PCB', board, 'native outline; component STEP independently exported', (.18,.44,.29))
for ref, shape in components.items():
    feature('Component_'+ref, shape, 'native EDA component model; not necessarily maximum dimensions', (.6,.62,.65))

usb_relief = box(76.65, 9.90, 9, 12.2, -.1, 5.4)
bottom = rounded(0, 0, 84, 52, 2, 0, S['bottom_pc_mm']).cut(usb_relief)
top = rounded(0, 0, 84, 52, 2, COVER_Z, S['top_pc_mm'])
keys = C['keys_xy_mm']
for x,y in keys:
    top = top.cut(Part.makeCylinder(2.2, .6, V(x,y,COVER_Z-.1)))
for x in [5.00126,7.50062,9.99998,12.49934,15.00124]:
    bottom = bottom.cut(Part.makeCylinder(.9, .5, V(x,46.0,-.1)))

frame = rounded(0,0,84,52,2,FRAME_Z,S['printed_frame_above_pcb_mm']).cut(rounded(1,1,82,50,1,FRAME_Z-.1,3.2))
battery_frame = rounded(0,0,35.5,17.3,2,.31,FRAME_TOP-.31).cut(rounded(.9,.9,33.7,15.5,1.1,.2,4.2))
frame = frame.fuse(battery_frame).cut(rounded(.9,.9,33.7,15.5,1.1,.31,FRAME_TOP))
for x,y,w,h in [(43.4,0,1,24.8),(43.4,44,1,8),(50.2,0,1,24.8),(59,19,1,33),(69.4,0,1,24.8)]:
    frame = frame.fuse(box(x,y,w,h,FRAME_Z,FRAME_TOP-FRAME_Z))
frame = frame.fuse(box(43.4,23.8,39.6,1,FRAME_TOP-1,1))
frame = frame.cut(usb_relief)
# Leave the whole RF antenna end free of plastic ribs and all metal hardware.
frame = frame.cut(box(56.5,-.1,13,4.3,FRAME_Z-.1,3.2))
for ref,s in components.items():
    b = s.BoundBox
    if ref == 'J1':
        continue
    frame = frame.cut(box(b.XMin-.25,b.YMin-.25,b.XLength+.5,b.YLength+.5,PCB_TOP-.01,b.ZMax-PCB_TOP+.26))
for x,y in keys:
    frame = frame.cut(Part.makeCylinder(3.1,2,V(x,y,FRAME_TOP-1.35)))
# Reserve a top-accessible harness path between the keys and over the charger.
# The actual pack must have a compatible lead exit; wire OD is not yet measured.
wire_path = [(34,7.5,11.8,3), (42.8,9.5,3,13), (42.8,21.5,8,3.5)]
wire_floor = 2.45
for x,y,w,h in wire_path:
    frame = frame.cut(box(x,y,w,h,wire_floor,FRAME_TOP-wire_floor+.1))
frame = frame.removeSplitter()

screen = box(2,18.3,37.32,31.8,FRAME_TOP-.85,.85)
screen_max = box(1.95,18.25,37.42,31.9,FRAME_TOP-1,1)
battery = box(1.5,1.5,32.5,14,.35,3.4)
feature('ScreenNominal',screen,'front border bonded to top sheet; active area free of adhesive',(.32,.34,.37))
feature('BatteryMaximum',battery,'unmeasured complete-pack design envelope; not supplier approval',(.8,.65,.3))
frame_obj = feature('PrintedFrame',frame,'SLA candidate; nominal perimeter 1.0 mm, battery wall 0.9 mm; local reliefs need DFM',(.38,.52,.7))
feature('BottomPC',bottom,'0.25 mm cut polycarbonate sheet',(.7,.8,.9))
feature('TopPC',top,'0.25 mm clear PC; optional opaque mask outside display',(.75,.83,.9))

# A patterned PET spacer keeps ordinary underside vias away from the cover.
spacer = outline(.31,.1).cut(usb_relief)
for x in [5.00126,7.50062,9.99998,12.49934,15.00124]:
    spacer = spacer.cut(Part.makeCylinder(1,.3,V(x,46,.25)))
feature('PETSpacer',spacer,'0.10 mm insulating PET, laminated between two 0.06 mm PSA layers')
frame_adh = frame.copy(); frame_adh.translate(V(0,0,-.06))
frame_adh = frame_adh.common(box(0,0,84,52,PCB_TOP,.06))
feature('FramePSA',frame_adh,'patterned 0.06 mm PSA between PCB and frame')
top_adh = frame.common(box(0,0,84,52,FRAME_TOP-.06,.06));top_adh.translate(V(0,0,.06))
screen_ring = box(2,18.3,37.32,31.8,FRAME_TOP,.06).cut(box(3.5,19.8,34.32,28.8,FRAME_TOP-.01,.09))
top_adh = top_adh.fuse(screen_ring)
feature('TopPSA',top_adh,'0.06 mm patterned PSA on frame and screen border')

caps = []
cap_checks = []
for i,(x,y) in enumerate(keys,1):
    flange_top=COVER_Z-.05
    cap=Part.makeCylinder(2.8,1,V(x,y,flange_top-1))
    cap=cap.fuse(Part.makeCylinder(2,TOTAL-.03-(flange_top-1),V(x,y,flange_top-1)))
    cap=cap.fuse(Part.makeCylinder(1.3,flange_top-1-(PCB_TOP+1.6),V(x,y,PCB_TOP+1.6)))
    caps.append(feature('KeyCap'+str(i),cap.removeSplitter(),'retained flange; 0.25 mm travel plus 0.05 mm free gap',(.88,.65,.3)))
    pressed=cap.copy();pressed.translate(V(0,0,-.30))
    cap_checks.append({'key':i,'frame_rest':relation(cap,frame),'frame_pressed':relation(pressed,frame),'cover_rest':relation(cap,top),'cover_pressed':relation(pressed,top)})

# FPC insertion and wire routing volumes are visible, separate assembly reservations.
fpc = box(39.4,26,8.3,16,PCB_TOP+.4,2.4)
fo=feature('FPCServiceVolume',fpc,'routing and latch-access reservation, not a verified flex bend',(.9,.45,.25))
if App.GuiUp: fo.ViewObject.Visibility=False
wire_service = box(*wire_path[0],wire_floor,1.0)
for segment in wire_path[1:]:
    wire_service = wire_service.fuse(box(*segment,wire_floor,1.0))
wo=feature('BatteryWireServiceVolume',wire_service.removeSplitter(),'3 mm wide, 1 mm high harness reservation; pack exit and wire OD unverified',(.85,.3,.2))
if App.GuiUp: wo.ViewObject.Visibility=False

checks = {'components_to_frame':{r:relation(s,frame) for r,s in components.items()},
          'components_to_top':{r:relation(s,top) for r,s in components.items()},
          'components_to_bottom':{r:relation(s,bottom) for r,s in components.items()},
          'components_to_screen_max':{r:relation(s,screen_max) for r,s in components.items()},
          'battery_to_frame':relation(battery,frame),'battery_to_pcb':relation(battery,board),
          'screen_to_frame':relation(screen_max,frame),'keys':cap_checks,
          'fpc_service_to_frame':relation(fpc,frame),
          'wire_service_to_components':{r:relation(wire_service,s) for r,s in components.items()},
          'wire_service_to_top':relation(wire_service,top)}
parts={'frame':frame,'top':top,'bottom':bottom,'pet':spacer,'top-psa':top_adh,'frame-psa':frame_adh}
report={'status':'DESIGN_CANDIDATE_NOT_FOR_ORDER','stack_mm':S,'nominal_height_mm':TOTAL,
        'allocated_max_height_mm':TOTAL+sum(C['tolerance_allocations_mm'].values()),
        'pcb_z_mm':PCB_Z,'frame_top_mm':FRAME_TOP,'screen_back_nominal_mm':FRAME_TOP-.85,
        'component_count':len(components),'parts':{k:{'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume} for k,s in parts.items()},
        'checks':checks,'limits':['Complete protected battery, flex geometry and adhesive compatibility need samples.',
          'Library STEP models are nominal approximations, not supplier maximum envelopes.',
          'Routed PCB connectivity and factory DFM approval are separate gates.',
          '0.25 mm cover stiffness, pressing force and drop performance require an assembled sample.']}
(OUT/'e20-assembly-report.json').write_text(json.dumps(report,indent=2))
doc.recompute();doc.saveAs(str(OUT/'e20-assembly.FCStd'))
Part.export([o for o in doc.Objects if hasattr(o,'Shape') and o.Name not in ('FPCServiceVolume','BatteryWireServiceVolume')],str(OUT/'e20-assembly.step'))
Part.export([frame_obj],str(OUT/'e20-frame.step'))
Mesh.export([frame_obj],str(OUT/'e20-frame.stl'))
Mesh.export(caps,str(OUT/'e20-keycaps.stl'))
# Planar cut files keep physical millimetres and carry a candidate-only note.
for name,shape in parts.items():
    if name=='frame':continue
    faces=[f for f in shape.Faces if abs(f.CenterOfMass.z-shape.BoundBox.ZMax)<1e-5 and abs(f.normalAt(0,0).z)>.99]
    paths=[]
    for face in faces:
        for wire in face.Wires:
            points=wire.discretize(Deflection=.01)
            paths.append('M '+' L '.join(f'{p.x:.4f},{52-p.y:.4f}' for p in points)+' Z')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="84mm" height="52mm" viewBox="0 0 84 52"><title>E20 '+name+' - candidate cut geometry, mm</title><path fill="none" stroke="black" stroke-width="0.05" d="'+' '.join(paths)+'"/></svg>'
    (OUT/f'e20-{name}-cut.svg').write_text(svg)
print('E20_REPORT',json.dumps({'height':TOTAL,'max':report['allocated_max_height_mm'],'frame_solids':len(frame.Solids),'out':str(OUT)}))
