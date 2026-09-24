"""Build an all-SLA clear enclosure candidate from the native E20 PCB STEP.

NFC_E20_OUT, NFC_E20_PCB and NFC_CASE_HEIGHT select the output, source and
nominal total height. NFC_E20_CONFIG can select frozen design inputs.
The two shell halves use a patterned adhesive seam.
The output is a geometric candidate, not an optical or strength qualification.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import FreeCAD as App
import Part
import Import
import Mesh

ROOT = Path(__file__).resolve().parents[1]
C = json.loads(Path(os.environ.get('NFC_E20_CONFIG', ROOT/'hardware/r1-design.json')).read_text())
K = C['clear_shell']
OUT = Path(os.environ['NFC_E20_OUT'])
SOURCE = Path(os.environ['NFC_E20_PCB'])
HEIGHT = float(os.environ['NFC_CASE_HEIGHT'])
OUT.mkdir(parents=True, exist_ok=True)
if (OUT/'e20-clear-assembly.FCStd').exists():
    raise SystemExit('Refusing to overwrite an existing assembly.')
FLOOR, LID, WALL = K['floor_mm'], K['lid_mm'], K['wall_mm']
PCB_Z = FLOOR+K['pcb_support_stack_mm']
PCB_TOP = PCB_Z+C['pcb_thickness_mm']
LID_Z = HEIGHT-LID
RIM_Z = LID_Z-K['lid_seam_psa_mm']
V = App.Vector


def box(x,y,w,h,z,t):
    return Part.makeBox(w,h,t,V(x,y,z))


def rounded(x,y,w,h,r,z,t):
    shapes=[box(x+r,y,w-2*r,h,z,t),box(x,y+r,w,h-2*r,z,t)]
    shapes += [Part.makeCylinder(r,t,V(a,b,z)) for a in (x+r,x+w-r) for b in (y+r,y+h-r)]
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def feature(name,shape,role,color=(.75,.85,.9),transparency=0):
    o=doc.addObject('PartDesign::Feature',name);o.Shape=shape
    o.addProperty('App::PropertyString','Role');o.Role=role
    o.addProperty('App::PropertyColor','DesignColor');o.DesignColor=color
    o.addProperty('App::PropertyInteger','DesignTransparency');o.DesignTransparency=transparency
    if App.GuiUp:
        o.ViewObject.ShapeColor=color;o.ViewObject.Transparency=transparency
    return o


def relation(a,b):
    return {'clearance_mm':a.distToShape(b)[0],'intersection_mm3':a.common(b).Volume}


reference=App.newDocument('E20NativeClearReference')
Import.insert(str(SOURCE),reference.Name)
expected={c['ref'] for c in json.loads((ROOT/C.get('placement_snapshot','hardware/records/e20-clear-placement-snapshot.json')).read_text())['components']}
components={}
board=None
for o in reference.Objects:
    if not hasattr(o,'Shape') or not o.Shape.Solids:continue
    if o.Label.startswith('Board~'):
        assert board is None
        board=o.Shape.copy();board.translate(V(0,0,PCB_Z))
    match=re.match(r'^([A-Z]+\d+)~',o.Label)
    if match and match.group(1) in expected:
        shape=o.Shape.copy();shape.translate(V(0,0,PCB_Z));components[match.group(1)]=shape
assert board is not None and len(components)==58
assert 1.10 < components['U1'].BoundBox.YMin < 1.2
assert abs(components['SW1'].BoundBox.Center.y-4.5)<.1
assert abs(components['J1'].BoundBox.XMax-C['usb']['mating_face_x_mm'])<.03

x,y=K['outer_offset_xy_mm'];w,h=K['outer_xy_mm']
doc=App.newDocument('E20ClearShell'+str(HEIGHT).replace('.','p'))
tray=rounded(x,y,w,h,2.6,0,RIM_Z).cut(rounded(x+WALL,y+WALL,w-2*WALL,h-2*WALL,1.4,FLOOR,RIM_Z))
# Expose the connector face to the plug overmold instead of recessing it.
front_relief=box(*C['usb'].get('case_relief_xywh_mm',[83.1,9.9,2,12.2]),-.1,HEIGHT+.2)
tray=tray.cut(front_relief)
lid=rounded(x,y,w,h,2.6,LID_Z,LID).cut(front_relief)
window=C['screen'].get('window_xywh_mm')
if window:
    lid=lid.cut(box(*window,LID_Z-.1,LID+.2)).removeSplitter()
debug_pads = C['swd'].get('pad_centers_mm', [[x,45.9994] for x in [5.00126,7.50062,9.99998,12.49934,15.00124]])
debug_hole_diameter = C['swd'].get('access_hole_diameter_mm', 2.0)
for xpad,ypad in debug_pads:
    tray=tray.cut(Part.makeCylinder(debug_hole_diameter/2,FLOOR+.2,V(xpad,ypad,-.1)))
tray=tray.removeSplitter()
for kx,ky in C['keys_xy_mm']:
    lid=lid.cut(Part.makeCylinder(2.6,LID+.2,V(kx,ky,LID_Z-.1)))
tray_obj=feature('ClearTray',tray,'transparent SLA candidate; perimeter walls; battery located by adhesive and assembly jig',(.77,.88,.92),78)
lid_obj=feature('ClearLid',lid,f'{LID} mm clear SLA lid; panel deflection unverified',(.8,.9,.94),87)
feature('PCB',board,'native EDA STEP; 0.8 mm two-layer PCB',(.12,.40,.26))
for ref,shape in components.items():
    feature('Component_'+ref,shape,'native library model, not guaranteed maximum envelope',(.6,.62,.65))

support_locations=K.get('pcb_supports_xywh_mm',[(3,49,5,1.5),(76,49,5,1.5),(37,1.5,5,2),(78,3,4,2),(76,8,5,1.2),(76,23,5,1.2)])
for i,(sx,sy,sw,sh) in enumerate(support_locations,1):
    feature('PCBSupport'+str(i),box(sx,sy,sw,sh,FLOOR,K['pcb_support_stack_mm']),
            '0.20 mm PET plus two 0.06 mm PSA layers; support below PCB',(.85,.9,.92),65)
support_coverage={str(i):box(sx,sy,sw,sh,PCB_Z,.01).common(board).Volume/(sw*sh*.01)
                  for i,(sx,sy,sw,sh) in enumerate(support_locations,1)}

screen_top=LID_Z-K['screen_psa_mm']
screen=box(2,18.3,37.32,31.8,screen_top-.85,.85)
screen_max=box(1.95,18.25,37.42,31.9,screen_top-1,1)
feature('ScreenNominal',screen,'front border bonded under aperture bezel; display exposed; maximum checked separately',(.72,.74,.73))
bx,by=C['battery']['pack_xy_mm'];bl,bw,bt=C['battery']['complete_pack_design_envelope_mm']
battery=box(bx,by,bl,bw,FLOOR+.1,bt)
feature('BatteryMaximum',battery,'unmeasured protected-pack maximum envelope, not measured hardware',(.72,.68,.49))
feature('BatteryPSA',box(3,3,27,10,FLOOR,.1),'0.10 mm battery mounting adhesive allocation',(.9,.9,.88),70)

rim_slice=tray.common(box(-1,-1,87,55,RIM_Z-.06,.06))
rim_slice.translate(V(0,0,.06))
feature('LidSeamPSA',rim_slice,'patterned 0.06 mm perimeter PSA; assembly needs an alignment jig',(.85,.9,.95),70)
screen_ring=box(2,18.3,37.32,31.8,screen_top,.06).cut(box(3.5,19.8,34.32,28.8,screen_top-.01,.08))
feature('ScreenPSA',screen_ring,'patterned border adhesive; no adhesive over active pixels',(.85,.9,.95),70)

caps=[];key_checks=[];stationary_switch_heights=[]
for i,(kx,ky) in enumerate(C['keys_xy_mm'],1):
    flange_top=LID_Z-.05
    cap=Part.makeCylinder(3.4,1,V(kx,ky,flange_top-1))
    cap=cap.fuse(Part.makeCylinder(2,HEIGHT-.03-(flange_top-1),V(kx,ky,flange_top-1)))
    head=cap.copy()
    shaft_height=flange_top-1-(PCB_TOP+1.6)
    assert shaft_height>0
    cap=cap.fuse(Part.makeCylinder(1.3,shaft_height,V(kx,ky,PCB_TOP+1.6))).removeSplitter()
    caps.append(feature('ClearKey'+str(i),cap,'0.6 mm nominal radial running gap; flange retained by lid',(.8,.88,.92),65))
    pressed=cap.copy();pressed.translate(V(0,0,-.30))
    pressed_head=head.copy();pressed_head.translate(V(0,0,-.30))
    switch_ref=['SW1','SW3','SW2'][i-1]
    assert abs(components[switch_ref].BoundBox.Center.x-kx)<.01
    assert abs(components[switch_ref].BoundBox.Center.y-ky)<.01
    stationary_switch=components[switch_ref].cut(Part.makeCylinder(1.4,3,V(kx,ky,PCB_TOP-.2)))
    stationary_switch_heights.append(stationary_switch.BoundBox.ZMax-PCB_TOP)
    key_checks.append({'key':i,'tray_rest':relation(cap,tray),'tray_pressed':relation(pressed,tray),
                       'lid_rest':relation(cap,lid),'lid_pressed':relation(pressed,lid),
                       'pressed_head_to_stationary_switch':relation(pressed_head,stationary_switch),
                       'pressed_to_other_components':{r:relation(pressed,s) for r,s in components.items() if r!=switch_ref}})

fpc=box(*K.get('fpc_service_xywh_zt_mm',[39.4,26,8.3,16,PCB_TOP+.4,2.4]))
wire_boxes=K.get('wire_service_boxes_mm',[[34,7.5,11.8,3,PCB_TOP+1.15,1],[42.8,9.5,3,13,PCB_TOP+1.15,1],[42.8,21.5,8,3.5,PCB_TOP+1.15,1]])
wire_shapes=[box(*b) for b in wire_boxes]
wire=wire_shapes[0].multiFuse(wire_shapes[1:]).removeSplitter()
for name,shape,role in [('FPCServiceVolume',fpc,'open-lid assembly access study, not a closed-flex envelope; actual flex bend unverified'),('BatteryWireServiceVolume',wire,'lead exit and wire OD unverified')]:
    o=feature(name,shape,role,(.9,.45,.25),75)
    if App.GuiUp:o.ViewObject.Visibility=False

checks={'components_to_tray':{r:relation(s,tray)for r,s in components.items()},
        'components_to_lid':{r:relation(s,lid)for r,s in components.items()},
        'components_to_screen_max':{r:relation(s,screen_max)for r,s in components.items()},
        'battery_to_tray':relation(battery,tray),'battery_to_lid':relation(battery,lid),
        'screen_to_tray':relation(screen_max,tray),'board_to_tray':relation(board,tray),
        'keys':key_checks,'fpc_to_tray':relation(fpc,tray),'fpc_to_lid':relation(fpc,lid),
        'wire_to_components':{r:relation(wire,s)for r,s in components.items()},'wire_to_lid':relation(wire,lid),
        'wire_to_screen_max':relation(wire,screen_max),'wire_to_board':relation(wire,board),
        'wire_to_keys_rest':{o.Name:relation(wire,o.Shape) for o in caps},
        'wire_to_keys_pressed':{},'support_coverage_fraction':support_coverage}
for o in caps:
    pressed=o.Shape.copy();pressed.translate(V(0,0,-.30))
    checks['wire_to_keys_pressed'][o.Name]=relation(wire,pressed)
gap=.3
support=K['pcb_support_stack_mm'];pcb=C['pcb_thickness_mm']
under_screen=[r for r,s in components.items() if s.BoundBox.XMax>1.95 and s.BoundBox.XMin<39.37
              and s.BoundBox.YMax>18.25 and s.BoundBox.YMin<50.15]
under_screen_ref=max(under_screen,key=lambda r:components[r].BoundBox.ZMax) if under_screen else None
under_screen_height=components[under_screen_ref].BoundBox.ZMax-PCB_TOP if under_screen_ref else 0
if C['nfc'].get('read_side')=='rear':
    ferrite=box(*C['nfc']['keepout_xywh_mm'],PCB_TOP+.1,C['nfc']['ferrite_allowance_mm'])
    feature('NFCFerriteServiceVolume',ferrite,'optional ferrite space only; not selected material or BOM',(.35,.40,.45),80)
    checks['optional_ferrite_to_screen_max']=relation(ferrite,screen_max)
    checks['optional_ferrite_to_components']={r:relation(ferrite,s) for r,s in components.items()}
interior_stacks={
    'usb':{'support':support,'pcb':pcb,'above_pcb':components['J1'].BoundBox.ZMax-PCB_TOP,'gap':gap},
    'battery':{'adhesive':.1,'pack_envelope':3.4,'gap':gap},
    'mcu':{'support':support,'pcb':pcb,'module_maximum':C['mcu']['body_max_mm'][2],'gap':gap},
    'display':{'support':support,'pcb':pcb,'under_screen_component':under_screen_height,'gap':gap,'screen_maximum':1.,'border_adhesive':K['screen_psa_mm']},
    'key':{'support':support,'pcb':pcb,'stationary_switch':max(stationary_switch_heights),'pressed_travel':.3,'flange':1.,'flange_lid_gap':.05,'gap':gap}}
budget={name:{'interior_terms_mm':terms,'total_height_mm':FLOOR+LID+sum(terms.values())}for name,terms in interior_stacks.items()}
budget['notes']=['Take the maximum regional stack, not the sum across regions.',
    '0.3 mm is a nominal design gap, not a worst-case tolerance guarantee.',
    'The screen has an active-area aperture; its front border remains below the printed bezel.',
    'FPCServiceVolume is open-lid assembly access and does not set the closed height; the real folded flex is unmeasured.']
budget['under_screen_component_ref']=under_screen_ref
report={'status':'GEOMETRY_CANDIDATE_NOT_FOR_ORDER','nominal_height_mm':HEIGHT,'outer_xy_mm':[w,h],
        'floor_mm':FLOOR,'lid_mm':LID,'wall_mm':WALL,'pcb_z_mm':PCB_Z,'pcb_top_mm':PCB_TOP,
        'screen_back_max_mm':screen_top-1,'source_step_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'component_count':len(components),'full_height_crossbeams':0,'display_window_xywh_mm':window,
        'debug_access':{'centers_mm':debug_pads,'diameter_mm':debug_hole_diameter},
        'under_screen_component_refs':under_screen,
        'height_budget':budget,
        'parts':{'tray':{'valid':tray.isValid(),'solids':len(tray.Solids)},'lid':{'valid':lid.isValid(),'solids':len(lid.Solids)}},
        'checks':checks,'limits':['Nominal solid clearances only; supplier tolerances are not approved.',
        'Battery complete-pack size, lead exit, screen flex, lid bonding, key feel and panel deflection require samples.',
        'CAD transparency is an illustration, not a guarantee of optical transparency after printing.',
        C.get('pcb_validation_note','PCB remains unrouted. RF tuning and production electrical gates remain open.')]}
active=C['screen']['active_xywh_mm']
window_margins=[active[0]-window[0],active[1]-window[1],
                window[0]+window[2]-active[0]-active[2],window[1]+window[3]-active[1]-active[3]]
assert all(abs(v-.4)<1e-6 for v in window_margins)
report['screen_registration']={'active_to_window_edge_margins_mm':window_margins,
    'method':'Align screen active area to the bezel using an assembly fixture, then bond the border. The FPC must not locate or preload the screen.'}
if C['screen'].get('fpc'):
    fpc_input=C['screen']['fpc']
    expected_y=C['screen']['xy_mm'][1]+C['screen']['nominal_mm'][1]-fpc_input['edge_offset_mm']-fpc_input['width_mm']/2
    actual_y=components['J2'].BoundBox.Center.y
    assert abs(expected_y-actual_y)<.01
    report['screen_registration'].update({'fpc_tail_center_y_mm':expected_y,'j2_center_y_mm':actual_y,
        'connector_rear_lead_to_screen_far_edge_mm':components['J2'].BoundBox.XMax-C['screen']['xy_mm'][0]})
(OUT/'e20-clear-report.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'design-inputs.json').write_text(json.dumps(C,indent=2)+'\n')
doc.recompute();doc.saveAs(str(OUT/'e20-clear-assembly.FCStd'))
physical=[o for o in doc.Objects if hasattr(o,'Shape') and not o.Name.endswith('ServiceVolume')]
Part.export(physical,str(OUT/'e20-clear-assembly.step'))
for name,obj in [('tray',tray_obj),('lid',lid_obj)]:
    Part.export([obj],str(OUT/f'e20-clear-{name}.step'))
    Mesh.export([obj],str(OUT/f'e20-clear-{name}.stl'))
Mesh.export(caps,str(OUT/'e20-clear-keys.stl'))
print('E20_CLEAR_REPORT',json.dumps({'height':HEIGHT,'tray_solids':len(tray.Solids),'lid_solids':len(lid.Solids),'out':str(OUT)}))
