#!/usr/bin/env python3
"""Reassign verified MCU GPIOs in an unopened A3 copy; prepare explicit A4 placement."""
import copy
import hashlib
import json
import math
import uuid
from pathlib import Path
from kicad_sexpr import child, children, prop, read, write, Quoted, remove, walk

project = Path(__file__).resolve().parents[1]
source = project/'hardware/kicad/v4-option-a3-local'
target = project/'hardware/kicad/v4-option-a4-joint'
records = project/'hardware/records/kicad-v4-option-a4'
assert not list(target.glob('~*.lck'))
filename = 'NFC-Card-V4.kicad_pcb'
assert (source/filename).read_bytes() == (target/filename).read_bytes(), 'Only run on the untouched A3 copy'
# GPIO alternatives are verified against Raytac Rev.L, tables 2.5 and section 2.6.
mapping = {
 'CHG_SCL': (16,36,'P0.27','P0.14'), 'CHG_SDA': (19,37,'P0.26','P0.13'),
 'CHG_INT_N': (20,39,'P0.04','P0.15'), 'CHG_PG_N': (21,38,'P0.05','P0.16'),
 'CHG_CE_N': (22,41,'P0.06','P0.17'),
 'EPD_SCK_TBD': (36,24,'P0.14','P0.08'), 'EPD_MOSI_TBD': (37,26,'P0.13','P1.09'),
 'EPD_CS_N_TBD': (38,22,'P0.16','P0.06'), 'EPD_DC_TBD': (39,20,'P0.15','P0.04'),
 'EPD_RESET_N_TBD': (41,19,'P0.17','P0.26'), 'EPD_BUSY_TBD': (24,16,'P0.08','P0.27'),
}
sheet = target/'2_02 MCU and controls.kicad_sch'
s = read(sheet)
u = next(x for x in children(s,'symbol') if prop(x,'Reference') and prop(x,'Reference')[2]=='U1')
lib = next(x for x in children(child(s,'lib_symbols'),'symbol') if x[1]==child(u,'lib_id')[1])
assert child(u,'at') == ['at','114.3','86.36','0']
pins = {int(child(p,'number')[1]):p for p in walk(lib,'pin')}
pin_at = {n:(round(114.3+float(child(p,'at')[1]),5),round(86.36-float(child(p,'at')[2]),5)) for n,p in pins.items()}
old_labels = {x[1]:x for x in children(s,'global_label') if x[1] in mapping}
assert len(old_labels)==len(mapping)
new_by_pin = {x[1]:net for net,x in mapping.items()}
for net,(old,new,og,ng) in mapping.items():
 label = old_labels[net]
 expected=(pin_at[old][0]+(-7.62 if pin_at[old][0]<114.3 else 7.62),pin_at[old][1])
 assert math.dist(tuple(map(float,child(label,'at')[1:3])),expected)<1e-5, net
 if old in new_by_pin:
  label[1] = Quoted(new_by_pin[old])
 else:
  s.remove(label)
  wire = next(w for w in children(s,'wire') if {tuple(round(float(v),4) for v in p[1:]) for p in child(w,'pts')[1:]}=={tuple(round(v,4) for v in pin_at[old]),tuple(round(v,4) for v in expected)})
  s.remove(wire)
  s.append(['no_connect',['at',*map(str,pin_at[old])],['uuid',Quoted(str(uuid.uuid4()))]])
# The one newly used pin gets a labelled stub; no symbol pin numbering changes.
assert set(new_by_pin)-{x[0] for x in mapping.values()} == {26}
nc=next(x for x in children(s,'no_connect') if tuple(map(float,child(x,'at')[1:3]))==pin_at[26]);s.remove(nc)
p=pin_at[26]; q=(round(p[0]-7.62,5),p[1])
label=copy.deepcopy(old_labels['CHG_SCL']);label[1]=Quoted(new_by_pin[26]);child(label,'at')[1:]=[*map(str,q),'180'];child(label,'uuid')[1]=Quoted(str(uuid.uuid4()))
# Hidden intersheet-reference placement follows the label.
for item in children(label,'property'):
 at=child(item,'at')
 if at: at[1:3]=list(map(str,q))
s.append(label)
s.append(['wire',['pts',['xy',*map(str,p)],['xy',*map(str,q)]],['stroke',['width','0'],['type','default']],['uuid',Quoted(str(uuid.uuid4()))]])
write(sheet,s)
b=read(target/filename);u=next(f for f in children(b,'footprint') if prop(f,'Reference')[2]=='U1')
for pad in children(u,'pad'):
 n=int(pad[1])
 if n in new_by_pin: child(pad,'net')[1]=Quoted(new_by_pin[n])
 elif n==21: child(pad,'net')[1]=Quoted('unconnected-(U1-P0.05{slash}AIN3-Pad21)')
write(target/filename,b)
placements={'U2':[158,107.3,180],'C3':[157.2,103.5,90],'C2':[161.5,105.3,180],
 'C8':[161.5,107.4,0],'R19':[155.4,109.6,180],'NTC':[154,107.5,0],'R7':[155,104.9,0],
 'U3':[166.1,108.4,90],'C4':[169.5,108.4,180],'C5':[162.8,109.35,180],
 'R3':[164.7,112.5,270],'R4':[166.5,112.5,270],
 'R5':[151.7,103.5,0],'R6':[151.7,105.4,0],'R8':[151.7,107.3,0],'R9':[151.7,109.2,0]}
result={'source':str(source),'source_pcb_sha256':hashlib.sha256((source/filename).read_bytes()).hexdigest(),
 'gpio':{net:{'old_module_pin':v[0],'new_module_pin':v[1],'old_gpio':v[2],'new_gpio':v[3]} for net,v in mapping.items()},
 'new_no_connect_module_pin':21,'new_used_module_pin':26,'placements':placements}
(records/'joint-definition.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
