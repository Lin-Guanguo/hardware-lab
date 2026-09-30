#!/usr/bin/env python3
"""Audit the rejected A4 joint candidate; checks never imply routing acceptance."""
import json,hashlib,math,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from shapely.geometry import LineString,Point
from shapely.strtree import STRtree
from kicad_sexpr import child,children,prop
from v4_geometry import geometry,filled_ground
import importlib.util
spec=importlib.util.spec_from_file_location("path_audit",Path(__file__).with_name("audit-v4-trial.py"))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
measured_path=module.measured_path
project=Path(__file__).resolve().parents[1];repo=project.parents[1]
r=project/'hardware/records/kicad-v4-option-a4';c=project/'hardware/kicad/v4-option-a4-joint';source=project/'hardware/kicad/v4-option-a3-local'
old=geometry(source/'NFC-Card-V4.kicad_pcb');new=geometry(c/'NFC-Card-V4.kicad_pcb')
b,p,o,f=new;ob,op,oo,of=old;definition=json.loads((r/'joint-definition.json').read_text())
expected={n:x['net'] for n,x in op.items()}
for net,m in definition['gpio'].items():expected['U1.'+str(m['new_module_pin'])]=net
expected['U1.21']='unconnected-(U1-P0.05{slash}AIN3-Pad21)'
assert {n:x['net'] for n,x in p.items()}==expected
normalize=lambda n:'' if n.startswith('unconnected-') else n
xml=ET.parse(project/'artifacts/kicad-v4-option-a4/final-netlist.xml')
sch={(n.attrib['ref'],n.attrib['pin']):normalize(net.attrib['name']) for net in xml.findall('.//nets/net') for n in net.findall('node') if not n.attrib['ref'].startswith(('XUSB','XDBG'))}
assert all(normalize(p[ref+'.'+pin]['net'])==net for (ref,pin),net in sch.items())
oldpins=json.loads((project/'hardware/records/kicad-v4/migration-audit.json').read_text())['part_pins']
ex={(x['ref'],x['pin']):x['net'] for x in oldpins}
for net,m in definition['gpio'].items():ex[('U1',str(m['new_module_pin']))]=net
ex[('U1','21')]=''
assert ex==sch
fixed=['U1','J1','J2','C23','C24','BP','BN','TP1','TP2','TP3','TP4','TP5','SW1','SW2','SW3']
assert all(f[x]==of[x] for x in fixed)
parts=lambda b:{prop(x,'Reference')[2]:(prop(x,'MPN')[2],prop(x,'LCSC')[2]) for x in children(b,'footprint') if prop(x,'MPN')}
assert parts(b)==parts(ob)
assert {'Q2','Q3','R20','R21','R22','R23','C25'}<=f.keys()
assert float(child(child(b,'general'),'thickness')[1])==.8
for ext in ['kicad_pro','kicad_dru']:
 assert (c/f'NFC-Card-V4.{ext}').read_bytes()==(source/f'NFC-Card-V4.{ext}').read_bytes(),ext
for name in ['fp-lib-table','sym-lib-table']:
 for lib in children(__import__('kicad_sexpr').read(c/name),'lib'):
  uri=child(lib,'uri')[1];assert uri.startswith('${KIPRJMOD}/') and (c/uri.replace('${KIPRJMOD}/','')).exists()
edges=lambda b:[x for x in b if isinstance(x,list) and x[0].startswith('gr_') and child(x,'layer')==['layer','Edge.Cuts']]
assert edges(b)==edges(ob)
ko=lambda b:{child(z,'name')[1]:z for z in children(b,'zone') if child(z,'keepout')}
assert ko(b)==ko(ob)
cu=lambda x:(x['kind'],tuple(x['layers']),x['shape'].wkb_hex)
assert {cu(x) for x in o if x['net']=='NFC1_TBD'}=={cu(x) for x in oo if x['net']=='NFC1_TBD'}
# Preserve actual local land, mask, paste, drill and courtyard geometry.
def num(v):
 if isinstance(v,list):
  z=[num(x) for x in v]
  if z and z[0]=='at' and len(z)==4:z[3]%=360
  return z
 try:return float(v)
 except (ValueError,TypeError):return v
fps={prop(x,'Reference')[2]:x for x in children(ob,'footprint')}
for fp in children(b,'footprint'):
 ref=prop(fp,'Reference')[2];prev=fps[ref];oldpads={x[1]:x for x in children(prev,'pad')}
 for pad in children(fp,'pad'):
  prevp=oldpads[pad[1]];assert pad[:4]==prevp[:4]
  at,pat=child(pad,'at'),child(prevp,'at');assert num(at[:3])==num(pat[:3])
  delta=(float(at[3]) if len(at)>3 else 0)-(float(pat[3]) if len(pat)>3 else 0)
  assert min((delta-f[ref][2]+of[ref][2])%360,360-(delta-f[ref][2]+of[ref][2])%360)<1e-6
  props=lambda p:{x[0]:num(x[1:]) for x in p[4:] if x[0] not in ('at','net')}
  assert props(pad)==props(prevp),ref
 graphics=lambda fp:{child(x,'uuid')[1]:num(x) for x in fp if isinstance(x,list) and x[0].startswith('fp_')}
 assert graphics(fp)==graphics(prev),ref
baseline=json.loads((r/'baseline-files.json').read_text());changed=[n for n,h in baseline.items() if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h]
assert not changed,changed
# Independent foreign-copper clearances use shapes, not native DRC classification.
spatial=STRtree([x['shape'] for x in o]);conflicts=[]
for i,x in enumerate(o):
 for j in spatial.query(x['shape'].buffer(.2)):
  if j<=i:continue
  y=o[j]
  if x['net']==y['net'] or not set(x['layers'])&set(y['layers']):continue
  if x['kind']==y['kind']=='pad' and x['name'].split('.')[0]==y['name'].split('.')[0]:continue
  gap=x['shape'].distance(y['shape'])
  if gap<.1999:
   conflicts.append({'a':x['name'],'a_net':x['net'],'b':y['name'],'b_net':y['net'],'gap_mm':round(gap,6),'layers':sorted(set(x['layers'])&set(y['layers']))})
(r/'independent-copper-conflicts.json').write_text(json.dumps(conflicts,indent=2)+'\n')
pairs=[('C1.1','U1.32'),('C3.1','BP.1'),('C3.1','U2.2'),('C8.1','U2.10'),('J1.A4B9','C8.1'),('C2.1','C4.1'),('C4.1','U3.1'),('C5.1','C9.1'),('U2.6','R19.1'),('U1.51','TP4.1'),('U1.53','TP3.1')]
metrics=[{'start':a,'end':z,'A3':measured_path(old,a,z),'A4_rejected':measured_path(new,a,z)} for a,z in pairs]
for net,m in definition['gpio'].items():
 endpoint={'CHG_SCL':'U2.8','CHG_SDA':'U2.7','CHG_INT_N':'U2.9','CHG_PG_N':'U2.3','CHG_CE_N':'U2.4','EPD_SCK_TBD':'J2.13','EPD_MOSI_TBD':'J2.14','EPD_CS_N_TBD':'J2.12','EPD_DC_TBD':'J2.11','EPD_RESET_N_TBD':'J2.10','EPD_BUSY_TBD':'J2.9'}[net]
 metrics.append({'net':net,'end':endpoint,'A3':measured_path(old,'U1.'+str(m['old_module_pin']),endpoint),'A4_rejected':measured_path(new,'U1.'+str(m['new_module_pin']),endpoint)})
(r/'path-metrics.json').write_text(json.dumps({'scope':'Centerline same-net graph only, excludes filled ground and foreign shorts. Rejected A4 lengths are NOT usable electrical paths or design benefits.','paths':metrics},indent=2)+'\n')
angles=[]
oldids={x['name'] for x in oo if x['kind']=='track'}
for x in o:
 if x['kind']!='track' or x['name'] in oldids:continue
 a,z=x['points'];dx,dy=abs(a[0]-z[0]),abs(a[1]-z[1])
 if min(dx,dy,abs(dx-dy))>.00011:angles.append({'uuid':x['name'],'net':x['net'],'points':x['points'],'length_mm':math.dist(a,z)})
drc=json.loads((r/'final-all-track-drc.json').read_text());erc=json.loads((r/'final-erc.json').read_text())
result={'status':'REJECTED JOINT CANDIDATE; NOT A RELEASE','fixed_datums':fixed,'preserved_comparison_files':len(baseline),
 'parts':len(parts(b)),'footprints':len(f),'pads':len(p),'part_pins_checked':len(sch),'gpio_changes':definition['gpio'],
 'schema_board_parity':len(drc['schematic_parity']),'unconnected':len(drc['unconnected_items']),
 'drc_mode':'--all-track-errors --refill-zones --schematic-parity','drc':dict(Counter(x['type'] for x in drc['violations'])),
 'severity':dict(Counter(x['severity'] for x in drc['violations'])),'independent_conflicting_pairs':len(conflicts),
 'new_non_octilinear_segments':angles,'placements_actual':{ref:{'A3':of[ref],'A4':xy} for ref,xy in f.items() if of[ref]!=xy},
 'rules_bom_footprint_geometry_keepouts_nfc_datums_preserved':True,'functional_parts_and_schematic_retained':True,
 'tracks':len(children(b,'segment')),'vias':len(children(b,'via'))}
(r/'identity-and-geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('gpio_changes','placements_actual','new_non_octilinear_segments')},indent=2))
print('Non-octilinear new segments',len(angles))
