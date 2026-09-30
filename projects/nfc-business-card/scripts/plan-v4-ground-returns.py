#!/usr/bin/env python3
"""Plan explicit local ground connections using the saved filled copper."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
from shapely.geometry import Point
from kicad_sexpr import child, children
from v4_geometry import filled_ground

spec=importlib.util.spec_from_file_location('octilinear',Path(__file__).with_name('route-v4-octilinear.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--pads',nargs='+',required=True)
    args=ap.parse_args()
    planner=r.Planner(args.board)
    back=filled_ground(planner.board,'B.Cu')
    evidence=[];failures=[]
    for name in args.pads:
        pad=planner.pads[name];assert pad['net']=='GND'
        cx,cy=pad['at']
        candidates=[]
        for ix in range(-12,13):
            for iy in range(-12,13):
                p=(round(cx+ix*.2,4),round(cy+iy*.2,4))
                if not back.covers(Point(p).buffer(.32)) or not planner.outline.buffer(-.61).contains(Point(p)):continue
                shape=Point(p).buffer(.3)
                if any(o['net']!='GND' and o['shape'].distance(shape)<.205 for o in planner.objects):continue
                if any(o['kind']=='pad' and len(o['layers'])==1 and o['shape'].distance(Point(p))<.555 for o in planner.objects):continue
                candidates.append((math.dist(p,pad['at']),p))
        connected=False
        for _,p in sorted(candidates)[:30]:
            result=planner.route({'name':name+' local ground return','net':'GND','width':.25,'layer':'F.Cu','through':[name,list(p)],'bounds':[cx-3,cy-3,cx+3,cy+3]})
            if result:continue
            via={'name':name+' local ground stitch','net':'GND','at':p}
            assert not planner.add_via(via)
            evidence.append({'pad':name,'via_mm':p,'center_distance_mm':round(math.dist(p,pad['at']),3),'basis':'Via lands in saved B.Cu ground and clears copper, SMT drills and antenna keepout; explicit 0.25 mm F.Cu path.'})
            connected=True;break
        if not connected:failures.append({'name':name,'reason':'No local ground connection in 2.4 mm search'})
    result={'board':str(args.board),'description':'Local ground returns at named pads with real filled copper','record':'projects/nfc-business-card/hardware/records/kicad-v4-phase3/ground-apply.json','routes':planner.routes,'vias':planner.vias,'failures':failures,'evidence':evidence}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'routes':len(planner.routes),'vias':len(planner.vias),'failures':failures}))


if __name__=='__main__':main()
