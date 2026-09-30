#!/usr/bin/env python3
"""Compare one rejected search with a static native-DRC geometry witness."""
import collections
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import LineString
from v4_geometry import geometry

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'projects/nfc-business-card';O=P/'hardware/records/kicad-v4-phase3/layout-review';S=P/'hardware/kicad/v4-phase3'
w=json.loads((O/'j2-witness.json').read_text());d=json.loads((O/'j2-witness-drc.json').read_text());ids={u for x in w['witness'] for u in x['uuids']}
related=[x for x in d['violations'] if any(i.get('uuid') in ids for i in x['items'])]
errors=[x for x in related if x['type']!='track_dangling']
assert not errors, errors
native=P/'artifacts/kicad-v4-phase3/j2-witness/j2-witness.kicad_pcb';_,pads,objects,_=geometry(native)
measure=[]
for line in w['witness']:
    g=LineString(line['points']).buffer(.075)
    foreign=[o for o in objects if o['net']!=line['net'] and 'B.Cu' in o['layers']]
    closest=min(foreign,key=lambda o:o['shape'].distance(g))
    measure.append({'name':line['name'],'minimum_foreign_copper_gap_mm':round(g.distance(closest['shape']),6),'nearest_object':closest['name']})
plan=json.loads((S/'wholeboard-orthogonal-lanes-spec-plan.json').read_text());reqs={x['name']:[] for x in plan['routes']}
for x in plan['routes']:reqs[x['name']].append(x)
trace=reqs['U1.39 to J2.11 south'];failure=next(x for x in plan['failures'] if x['name']=='U1.41 to J2.10 north')
result={'scope':w['scope'],'source_failure':failure,'DC_south_detour':trace,'DC_south_length_mm':round(sum(x['length_mm'] for x in trace),3), 'native_witness_violations':dict(collections.Counter(x['type'] for x in related)), 'native_all_violations':dict(collections.Counter(x['type'] for x in d['violations'])), 'native_unconnected_items':len(d['unconnected_items']), 'minimum_clearances':measure, 'witness_board_sha256':hashlib.sha256(native.read_bytes()).hexdigest(), 'conclusion':'J2 north six-lane geometry is feasible after jointly replacing the greedy fanouts. The original frozen route set really blocks RESET, but the search failure does not prove insufficient J2 area. MCU south approaches and return quality are NOT proven.'}
(O/'algorithm-case.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axs=plt.subplots(1,2,figsize=(12,8),constrained_layout=True)
colors=plt.cm.tab10.colors
for ax in axs:
    for o in objects:
        if o['kind']!='pad' and o['kind']!='via':continue
        if o['shape'].bounds[2]<164 or o['shape'].bounds[0]>171:continue
        ax.add_patch(Patch(o['shape'].exterior.coords,facecolor='#cbd2db',edgecolor='none',alpha=.5))
    ax.set(xlim=(164.7,170.5),ylim=(112,93.5),aspect='equal',xlabel='X / mm',ylabel='Y / mm');ax.grid(alpha=.2)
for i,net in enumerate([x['net'] for x in w['witness']]):
    for r in plan['routes']:
        if r['net']==net and (r['name'].endswith(' north') or r['name']=='U1.39 to J2.11 south'):
            x,y=zip(*r['points']);axs[0].plot(x,y,color=colors[i],lw=1.5,ls='-' if r['layer']=='B.Cu' else '--')
    a=next(x for x in w['witness'] if x['net']==net);x,y=zip(*a['points']);axs[1].plot(x,y,color=colors[i],lw=1.5,label=net.replace('EPD_','').replace('_TBD',''))
axs[0].scatter([167],[99.9],c='red',s=75,marker='x',zorder=6);axs[0].annotate('RESET north failed\nDC south already loops here',(167,99.9),(169,103),ha='center',fontsize=8,arrowprops={'arrowstyle':'->','color':'red'})
axs[0].set_title('Rejected greedy fanout\nEarlier paths become fixed obstacles',fontsize=11)
axs[1].set_title('Static native geometry witness\nSix lanes coexist; south entry NOT proven',fontsize=11);axs[1].legend(loc='lower right',fontsize=8)
fig.savefig(O/'algorithm-case.png',dpi=180);plt.close(fig)
print(json.dumps({'witness_clearance_errors':len(errors),'minimum_gap_mm':min(x['minimum_foreign_copper_gap_mm'] for x in measure),'open_south_ends':len(related),'DC_south_detour_mm':result['DC_south_length_mm']}))
