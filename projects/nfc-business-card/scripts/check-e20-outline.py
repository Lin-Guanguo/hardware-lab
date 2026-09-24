#!/usr/bin/env python3
"""Check the Gerber profile and USB mounting slots against the native outline."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--gerber',type=Path,required=True)
p.add_argument('--snapshot',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
s=json.loads(a.snapshot.read_text())
profiles=[i for i in s['polylines'] if i['layer']==11]
assert len(profiles)==1,'Expected one native board outline'
raw=profiles[0]['polygon']['polygon']
expected=[(raw[0]*.0254,raw[1]*.0254)]
i=2
while i<len(raw):
    if raw[i]=='L':i+=1
    elif raw[i]=='ARC':i+=2
    expected.append((raw[i]*.0254,raw[i+1]*.0254));i+=2
with zipfile.ZipFile(a.gerber) as z:
    names=z.namelist();gko=[n for n in names if n.endswith('.GKO')]
    assert len(gko)==1,'Expected one Gerber outline layer'
    text=z.read(gko[0]).decode()
    assert '%MOMM*%' in text,'Expected millimetres'
    fmt=re.search(r'%FSLAX(\d)(\d)Y(\d)(\d)\*%',text);assert fmt
    scale=10**int(fmt.group(2));paths=[];arcs=[];previous=None
    for line in text.splitlines():
        m=re.search(r'G0([123])X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([12])\*',line)
        if not m:continue
        mode,x,y,dx,dy,draw=m.groups();point=(int(x)/scale,int(y)/scale)
        if draw=='2':paths.append([point])
        else:
            assert paths
            paths[-1].append(point)
            if mode in ('2','3'):
                radius=math.hypot(int(dx),int(dy))/scale
                center=(previous[0]+int(dx)/scale,previous[1]+int(dy)/scale)
                assert abs(math.dist(center,point)-radius)<.002,'Invalid arc'
                arcs.append(radius)
        previous=point
    assert len(paths)==1 and math.dist(paths[0][0],paths[0][-1])<.002,'Open or duplicate profile'
    assert len(paths[0])==len(expected),'Profile vertex count differs'
    assert all(any(math.dist(e,v)<.002 for v in paths[0])for e in expected),'Profile differs from native outline'
    assert len(arcs)==8 and all(min(abs(r-.5),abs(r-2))<.002 for r in arcs),'Wrong corner radii'
    assert not any(n.endswith('.GME') for n in names),'Unexpected mechanical outline export'
    drill=z.read(next(n for n in names if n.endswith('PTH_Through.DRL'))).decode()
    tools = {m[1]: float(m[2]) for m in re.finditer(r'(T\d+)C([\d.]+)', drill)}
    slots=[]
    active_tool = None
    for line in drill.splitlines():
        if re.fullmatch(r'T\d+', line): active_tool = line
        m = re.fullmatch(r'X([\d.]+)Y([\d.]+)G85X([\d.]+)Y([\d.]+)', line)
        if m:
            assert active_tool in tools and abs(tools[active_tool]-.6)<.002, 'USB slot tool diameter changed'
            x,y,X,Y=map(float,m.groups());assert abs(y-Y)<.002,'USB slot axis changed'
            slots.append(abs(X-x))
    assert len(slots)==4 and all(abs(x-y)<.002 for x,y in zip(sorted(slots),[.8,.8,1.2,1.2]))
report={'status':'PROFILE_AND_SLOTS_PASS','closed_contours':1,
        'bbox_mm':[min(x for x,y in expected),min(y for x,y in expected),max(x for x,y in expected),max(y for x,y in expected)],
        'arc_radii_mm':arcs,'usb_slot_centerline_lengths_mm':slots,'conflicting_mechanical_layer':False,
        'gerber_sha256':hashlib.sha256(a.gerber.read_bytes()).hexdigest(),
        'snapshot_sha256':hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),
        'scope':'Outline and mounting-slot geometry only. Copper connectivity and physical performance require separate checks.'}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
