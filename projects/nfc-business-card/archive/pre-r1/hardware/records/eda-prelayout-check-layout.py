import json,math,sqlite3
from pathlib import Path
from itertools import combinations
root=Path(__file__).parent

def read_result(name):return json.loads((root/(name+'.json')).read_text())['result']
def rows(source):
 out={}
 for line in source.splitlines():
  a,b=line.split('||');a=json.loads(a);b=json.loads(b.rstrip('|'));out[(a['type'],a.get('id',''))]=b
 return out

def rotate(x,y,angle):
 a=math.radians(angle);return x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)

def bbox(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-5 and min(a[3],b[3])-max(a[1],b[1])>1e-5

def inside(x,y,polygon):
 result=False
 for (ax,ay),(bx,by) in zip(polygon,polygon[1:]+polygon[:1]):
  if abs((bx-ax)*(y-ay)-(by-ay)*(x-ax))<1e-5 and min(ax,bx)-1e-5<=x<=max(ax,bx)+1e-5 and min(ay,by)-1e-5<=y<=max(ay,by)+1e-5:return True
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:result=not result
 return result

plan=json.loads((root/'plan.json').read_text());a=read_result('final-before-reopen');b=read_result('reopened-data');ra,rb=rows(a['source']),rows(b['source'])
source_normalizations=[]
for k in set(ra)&set(rb):
 if k[0]=='COMPONENT':
  ra[k]['angle']%=360;rb[k]['angle']%=360
 if k[0]=='LAYER' and ra[k].get('inactiveTransparency')!=rb[k].get('inactiveTransparency'):
  source_normalizations.append('Inactive-layer transparency restored by client')
  ra[k]['inactiveTransparency']=rb[k]['inactiveTransparency']
 if k[0]=='LAYER' and not ra[k].get('use') and not rb[k].get('use') and ra[k].get('inactiveColor')!=rb[k].get('inactiveColor'):
  source_normalizations.append('Client changed inactive color on unused inner layers 5/10')
  ra[k]['inactiveColor']=rb[k]['inactiveColor']
 if k[0]=='RULE_SELECTOR' and k[1]=='["RULE_SELECTOR",["NET",""]]':
  if ra[k]['ruleKeyValue']=={} and rb[k]['ruleKeyValue']=={'NET_LENGTH_TOLERANCE':['default',None]}:
   source_normalizations.append('Client materialized default empty-net length-tolerance selector')
   ra[k]['ruleKeyValue']=rb[k]['ruleKeyValue']
source_changes=[str(k) for k in set(ra)|set(rb) if k[0]!='DOCHEAD' and ra.get(k)!=rb.get(k)]
footprints={f['footprint']['uuid']:rows(f['source']) for f in read_result('footprint-sources')}
sch=json.loads(Path('projects/nfc-business-card/hardware/schematic-draft.enet').read_text());expected={c['props']['Designator']:{p:v['net'] for p,v in c['pinInfoMap'].items()} for c in sch['components'].values()}
net_errors=[];placement_errors=[];pads=[];bodies=[]
for c in b['components']:
 ref=c['ref'];x,y,r=c['x']*.0254,c['y']*.0254,c['rotation'];px,py,pr=plan['placements'][ref]
 if max(abs(x-px),abs(y-py),abs((r-pr+180)%360-180))>1e-5:placement_errors.append(ref)
 actual={p['padNumber']:p['net'] for p in c['pads']}
 if actual!=expected[ref]:net_errors.append(ref)
 def transform(u,v):
  dx,dy=rotate(u*.0254,v*.0254,r);return x+dx,y+dy
 for (typ,pid),v in footprints[c['footprint']['uuid']].items():
  if typ=='PAD':
   p=v['defaultPad'];w,h=p['width'],p['height'];corners=[]
   for dx,dy in [(-w/2,-h/2),(-w/2,h/2),(w/2,h/2),(w/2,-h/2)]:
    dx,dy=rotate(dx,dy,v['padAngle']);corners.append(transform(v['centerX']+dx,v['centerY']+dy))
   pads.append({'ref':ref,'pin':v['num'],'bounds_mm':bbox(corners),'corners':corners})
  elif typ=='POLY' and v.get('layerId')==48:
   assert set(z for z in v['path'] if isinstance(z,str))<={'L'}
   numbers=[n for n in v['path'] if not isinstance(n,str)];bodies.append({'ref':ref,'bounds_mm':bbox([transform(u,v) for u,v in zip(numbers[::2],numbers[1::2])])})
board=plan['board_outline_mm'];outside=[p['ref']+':'+p['pin'] for p in pads if not all(inside(x,y,board) for x,y in p['corners'])]
pad_overlaps=[(p['ref']+':'+p['pin'],q['ref']+':'+q['pin']) for p,q in combinations(pads,2) if p['ref']!=q['ref'] and overlap(p['bounds_mm'],q['bounds_mm'])]
body_overlaps=[(p['ref'],q['ref']) for p,q in combinations(bodies,2) if overlap(p['bounds_mm'],q['bounds_mm'])]
nfc_hits=[p['ref']+':'+p['pin'] for p in pads if overlap(p['bounds_mm'],[61,25,84,50])]
stack=sum(v.get('thickness',0) for (typ,pid),v in rb.items() if typ=='LAYER_PHYS')*.0254
with sqlite3.connect('file:eda/NFC-Business-Card.eprj2?mode=ro',uri=True) as db:database_check=db.execute('pragma quick_check').fetchone()[0]
report={'components':len(b['components']),'pads':len(pads),'save_reopen_changes':source_changes,'client_normalizations':sorted(set(source_normalizations)),'pad_net_mismatches_vs_schematic':net_errors,'placement_errors':placement_errors,'pad_corners_outside_board':outside,'inter_component_pad_bbox_overlaps':pad_overlaps,'component_body_bbox_overlaps':body_overlaps,'pad_overlaps_nfc_reserve':nfc_hits,'layer_stack_mm':stack,'database_quick_check':database_check,'scope':'Axis-aligned footprint/body and pad bounds for current rotations. Does not verify trace routing, true courtyard, solder-mask, slot clearance, 3D fit, material strength, RF or manufacturing readiness. USB body intentionally overhangs; pads must stay on PCB.'}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(root/'pad-geometry.json').write_text(json.dumps({'pads':pads,'bodies':bodies},indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
assert not any([source_changes,net_errors,placement_errors,outside,pad_overlaps,body_overlaps,nfc_hits])
assert abs(stack-.8)<.0001 and database_check=='ok'
