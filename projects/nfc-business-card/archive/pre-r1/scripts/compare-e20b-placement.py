#!/usr/bin/env python3
"""Compare exported E20 and E20B placement, without editing either board."""
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Patch

ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'hardware/records'
OUT=ROOT/'enclosure/renders'
load=lambda name:json.loads((REC/name).read_text())
snapshots=[load('e20-clear-placement-snapshot.json'),load('e20b-placement-snapshot.json')]
pins=[{c['ref']:c for c in load(f)} for f in ['e20-layout-review-pins.json','e20b-layout-pins.json']]
body_bounds=[load(f) for f in ['e20-layout-review-body-bounds.json','e20b-body-bounds.json']]
plan=json.loads((ROOT/'hardware/e20b-functional-placement.json').read_text())
pairs=[('C1','1','U1','32'),('C8','1','U2','10'),('C2','1','U2','1'),('C3','1','U2','2'),
       ('C4','1','U3','1'),('C5','1','U3','5'),('C6','1','U1','28'),('C7','1','U1','30'),
       ('R3','2','U1','35'),('R4','2','U1','34'),('R10','2','U1','3'),('R11','2','U1','4'),('R12','2','U1','5')]
pairs += [(f'C{i}','1','J2',str(j)) for i,j in zip(range(14,23),[4,5,16,18,19,20,22,23,24])]
metrics=[]
for a,pa,b,pb in pairs:
    row={'from':f'{a}.{pa}','to':f'{b}.{pb}'}
    for name,cs in zip(['before_mm','after_mm'],pins):
        p=next(p for p in cs[a]['pins'] if p['number']==pa)
        q=next(p for p in cs[b]['pins'] if p['number']==pb)
        assert p['net']==q['net']
        row['net']=p['net'];row[name]=math.hypot(p['x']-q['x'],p['y']-q['y'])*.0254
    metrics.append(row)
boost=['U4','C9','C10','L1','Q1','R13','R14','R15','D1','C11','C12','D2','R16','D3','C13']
relative_error=0
for ref in boost:
    a,b=pins[0][ref],pins[1][ref]
    relative_error=max(relative_error,abs((b['x']-a['x'])*.0254-2.5),abs((b['y']-a['y'])*.0254))
    assert a['rotation']==b['rotation']
assert relative_error<.003
pad_gaps=[]
for s in snapshots:
    pads={p['number']:p for p in s['pads'] if p['number'] in ['BP','BN','NTC']}
    p,q=pads['BP'],pads['BN']
    pad_gaps.append((math.hypot(p['x']-q['x'],p['y']-q['y'])-(p['pad'][1]+q['pad'][1])/2)*.0254)
fixed=['U1','U2','U3','U5','U6','J1','J2','SW1','SW2','SW3']
assert all(all(abs(pins[0][r][k]-pins[1][r][k])<1e-5 for k in ['x','y','rotation']) for r in fixed)
for s in snapshots:assert len(s['components'])==58 and len(s['pads'])==248 and not s['lines'] and not s['vias']
assert snapshots[0]['polylines']==snapshots[1]['polylines']
# Region IDs may change during native copy; compare actual exclusion geometry.
assert [{k:v for k,v in r.items() if k!='id'} for r in snapshots[0]['regions']]==[{k:v for k,v in r.items() if k!='id'} for r in snapshots[1]['regions']]
report={'status':'PLACEMENT_COMPARISON_ONLY','component_moves':len(plan['components_mm']),
        'standalone_pad_moves':len(plan['standalone_pads_mm']),'components':58,'pads':248,'tracks':0,'vias':0,
        'distance_metrics':metrics,'battery_positive_negative_pad_edge_gap_mm':dict(zip(['before','after'],pad_gaps)),
        'display_cap_distance_sum_mm':{k:sum(m[k] for m in metrics[13:]) for k in ['before_mm','after_mm']},
        'switching_group_translation_mm':[2.5,0],'translation_max_error_mm':relative_error,
        'fixed_references':fixed,'outline_and_exclusion_geometry_unchanged':True,
        'limits':['Pad-centre straight-line distances are not routed lengths or measured electrical performance.',
                  'SW-002 copper area and DC-003 via proximity cannot be evaluated before routing.',
                  'Display power group preserves internal placement; its real switching loop includes J2 and still needs routing review.',
                  'BP/BN diameter is unchanged; wire and assembly sample tests remain open.']}
(REC/'e20b-placement-comparison.json').write_text(json.dumps(report,indent=2)+'\n')

colors={'Power':'#d1943b','USB':'#8770b5','Display':'#4a8fae','Controls':'#77849b','MCU':'#344d65','NFC':'#319586'}
def group(ref):
    if ref=='U1':return 'MCU'
    if ref in ['J1','U5','U6','R1','R2','R3','R4']:return 'USB'
    if ref in ['J2','R17','R18']+boost or ref.startswith('C') and 14<=int(ref[1:])<=22:return 'Display'
    if ref.startswith('SW') or ref in ['R10','R11','R12']:return 'Controls'
    if ref in ['C23','C24']:return 'NFC'
    return 'Power'

fig=plt.figure(figsize=(18,10.6),facecolor='#f4f7fa')
fig.text(.045,.95,'NFC card | functional placement comparison',fontsize=24,weight='bold',color='#19334d')
fig.text(.045,.915,'Native EDA component positions and STEP bodies. Same board outline, 5.8 mm case and RF exclusions.',fontsize=11,color='#526477')
for idx,(s,cs,bounds) in enumerate(zip(snapshots,pins,body_bounds)):
    ax=fig.add_axes([.045+idx*.48,.34,.445,.535]);ax.set_aspect('equal');ax.set_xlim(-1,85);ax.set_ylim(52.5,-1)
    raw=next(p['polygon']['polygon'] for p in s['polylines'] if p['layer']==11)
    points=[(raw[0]*.0254,raw[1]*.0254)];i=2
    while i<len(raw):
        if raw[i]=='ARC':i+=2
        elif raw[i]=='L':i+=1
        if i+1>=len(raw):break
        points.append((raw[i]*.0254,raw[i+1]*.0254));i+=2
    ax.add_patch(Polygon(points,facecolor='#e3ece7',edgecolor='#5e7d6a',lw=1.1))
    ax.add_patch(Rectangle((1.5,1.5),32.5,14,facecolor='#ded6b9',edgecolor='#b4a57a'))
    ax.text(17.75,8.5,'BATTERY\nunmeasured envelope',ha='center',va='center',fontsize=9,color='#766536')
    ax.add_patch(Rectangle((2,18.3),37.32,31.8,facecolor='#e6f0ff',edgecolor='#6c98c5',alpha=.62,lw=1.2))
    ax.text(3.8,21.6,'SCREEN ABOVE',fontsize=8.5,color='#4c77a2')
    ax.add_patch(Rectangle((60,24),22,26,facecolor='#d4eae4',edgecolor='#319586',linestyle='--'))
    ax.text(71,36.3,'NFC RESERVE\ncoil not routed',ha='center',va='center',fontsize=10,color='#247969')
    ax.add_patch(Rectangle((56.5,0),13,4.96,facecolor='#eed6dc',edgecolor='#ad5b73',alpha=.7))
    ax.text(63,2.3,'RF KEEP-OUT',ha='center',fontsize=6.3,color='#8e3854')
    ax.add_patch(Rectangle((39.4,26),8.3,16,fill=False,edgecolor='#81929f',linestyle=':'))
    ax.text(43.5,33.9,'FPC\naccess',ha='center',fontsize=8,color='#718290')
    for p in s['pads']:
        w,h=p['pad'][1]*.0254,p['pad'][2]*.0254;a=math.radians(p['rotation'])
        xy=[(p['x']*.0254+dx*math.cos(a)-dy*math.sin(a),p['y']*.0254+dx*math.sin(a)+dy*math.cos(a)) for dx,dy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
        ax.add_patch(Polygon(xy,facecolor='#aab6bc',edgecolor='none'))
        if p['number'] in ['BP','BN','NTC']:ax.text(p['x']*.0254,p['y']*.0254+1.65,p['number'],ha='center',fontsize=6,color='#735329')
    for ref,b in bounds.items():
        lo,hi=b['min_mm'],b['max_mm'];x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
        ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor=colors[group(ref)],edgecolor='#425266',lw=.45))
        if ref in ['U1','J1','J2'] or ref.startswith('SW'):
            ax.text(x,y,ref,ha='center',va='center',fontsize=8,color='white')
        elif ref.startswith('C') and 14<=int(ref[1:])<=22:
            ax.text(hi[0]+.5,y,ref,va='center',fontsize=6.5,color='#334d62')
        elif ref in ['C1','C6','C7']:
            ax.text(x,hi[1]+.35,ref,ha='center',va='top',fontsize=6.1,color='#334d62')
        else:ax.text(x,lo[1]-.25,ref,ha='center',va='bottom',fontsize=6.1,color='#334d62')
    for a,pa,b,pb in [pairs[0],pairs[10]]:
        p=next(p for p in cs[a]['pins'] if p['number']==pa);q=next(p for p in cs[b]['pins'] if p['number']==pb)
        ax.plot([p['x']*.0254,q['x']*.0254],[p['y']*.0254,q['y']*.0254],color='#b65b60',lw=1,alpha=.85,linestyle='--')
    ax.set_title(['E20  /  original placement','E20B  /  functional candidate'][idx],loc='left',pad=14,fontsize=15,weight='bold',color='#19334d')
    ax.axis('off')
fig.legend(handles=[Patch(facecolor=v,label=k) for k,v in colors.items()],loc='lower center',bbox_to_anchor=(.5,.292),ncol=6,frameon=False,fontsize=10)
notes=[('LOCAL MCU POWER','C1 to VBUS: 14.32 → 1.24 mm','C6/C7 also closer to supply pins.'),
       ('CHARGER CLUSTER','BAT capacitor: 4.60 → 1.83 mm','Input, SYS, BAT and regulator caps grouped.'),
       ('USB + CONTROLS','USB resistors: 13–14 → 2.0–2.1 mm','Pull-ups moved next to MCU input pins.'),
       ('DISPLAY + ASSEMBLY','Ordered capacitor column; wider battery pads','15-part display power block shifted as a unit.')]
for i,(title,headline,body) in enumerate(notes):
    x=.05+i*.24
    fig.text(x,.255,title,fontsize=11,weight='bold',color='#19334d')
    fig.text(x,.217,headline,fontsize=9.5,color='#19334d')
    fig.text(x,.185,body,fontsize=9,color='#617387')
fig.text(.05,.12,'Distance arrows are comparisons, not copper routes. Screen outline is transparent here to expose components hidden beneath it.',fontsize=10,color='#617387')
fig.text(.05,.085,'58 components / 248 pads / 0 tracks / 0 vias in both layouts. Candidate only: electrical values, routing, RF and sample fit remain open.',fontsize=10,color='#617387')
fig.text(.05,.05,'Rounded outline corners simplified for this overview. Colors identify functions; they do not specify solder mask or component finish.',fontsize=9,color='#617387')
for ext in ['png','svg']:fig.savefig(OUT/f'e20b-functional-comparison.{ext}',dpi=160)
print(json.dumps(report,indent=2))
