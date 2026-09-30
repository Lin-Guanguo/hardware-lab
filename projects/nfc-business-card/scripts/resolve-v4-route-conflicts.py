#!/usr/bin/env python3
"""Resolve whole-net corridor conflicts without relaxing native geometry rules."""
import argparse
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path
from shapely.geometry import Point

module = importlib.util.spec_from_file_location('octilinear', Path(__file__).with_name('route-v4-octilinear.py'))
r = importlib.util.module_from_spec(module)
module.loader.exec_module(r)


def run():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('spec',type=Path)
    ap.add_argument('--limit',type=int,default=24)
    args=ap.parse_args()
    spec=json.loads(args.spec.read_text())
    planner=r.Planner(spec.get('model_board',spec['board']))
    for via in spec['vias']:
        assert not planner.add_via(via),via
    start=next(i for i,x in enumerate(spec['paths']) if x['name']=='C6.1 to C5.1')
    for req in spec['paths'][:start]:
        assert not planner.route(req),req['name']
    requests=spec['paths'][start:]
    queue=list(requests)
    done=set()
    attempts=Counter()
    ripped=Counter()
    log=[]
    unresolved=[]

    def route(req):
        before=(len(planner.objects),len(planner.vias))
        result=planner.route(req)
        if not result:
            for obj in planner.objects[before[0]:]:obj['owner']=req['name']
            for via in planner.vias[before[1]:]:via['owner']=req['name']
            done.add(req['name'])
        return result

    while queue:
        req=queue.pop(0)
        if req['name'] in done:continue
        failure=route(req)
        if not failure:
            print('ROUTED',req['name'],flush=True)
            continue
        attempts[req['name']]+=1
        if sum(attempts.values())>args.limit or attempts[req['name']]>5:
            unresolved=[req,*queue]
            log.append({'request':req['name'],'status':'bounded negotiation stopped','failure':failure})
            break
        probe=copy.deepcopy(planner)
        soft=[obj for obj in probe.objects if obj.get('owner')]
        probe.objects=[obj for obj in probe.objects if not obj.get('owner')]
        probe.routes=[];probe.vias=[]
        probe.soft_obstacles=[dict(obj,cost=3+3*ripped[obj['net']]) for obj in soft]
        count=len(probe.objects)
        proposal_failure=probe.route(req)
        if proposal_failure:
            unresolved=[req,*queue]
            log.append({'request':req['name'],'status':'immutable local escape conflict','failure':proposal_failure})
            break
        new=probe.objects[count:]
        conflicts={old['net'] for old in planner.objects if old.get('owner') for obj in new if old['net']!=obj['net'] and set(old['layers'])&set(obj['layers']) and old['shape'].distance(obj['shape'])<.200001}
        # Rebuild every mutable branch of an affected net; component joins may
        # otherwise retain a dependency on copper removed by this negotiation.
        conflicts.add(req['net'])
        names={x['name'] for x in requests if x['net'] in conflicts}
        planner.objects=[x for x in planner.objects if x.get('owner') not in names]
        planner.routes=[x for x in planner.routes if x['name'] not in names]
        planner.vias=[x for x in planner.vias if x.get('owner') not in names]
        done-=names
        for net in conflicts:ripped[net]+=1
        # Adopt the geometry that was checked against every immutable object.
        # All mutable foreign copper intersecting it was removed above.
        for obj in new:obj['owner']=req['name']
        for via in probe.vias:via['owner']=req['name']
        planner.objects.extend(new);planner.routes.extend(probe.routes);planner.vias.extend(probe.vias)
        done.add(req['name'])
        queue=[x for x in requests if x['name'] in names and x['name']!=req['name']]+[x for x in queue if x['name'] not in names]
        log.append({'request':req['name'],'ripped_nets':sorted(conflicts),'proposed_routes':len(probe.routes),'proposed_vias':len(probe.vias)})
        print('NEGOTIATE',json.dumps(log[-1]),flush=True)
    missing=[req for req in requests if req['name'] not in done]
    out={k:spec[k] for k in ('board','description','record')}
    out.update(routes=planner.routes,vias=planner.vias,failures=[{'name':x['name'],'reason':'Unresolved joint route'} for x in missing],negotiation=log)
    path=args.spec.with_name(args.spec.stem+'-resolved.json');path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'file':str(path),'routes':len(planner.routes),'vias':len(planner.vias),'failures':len(missing),'negotiations':len(log)}))


if __name__=='__main__':run()
