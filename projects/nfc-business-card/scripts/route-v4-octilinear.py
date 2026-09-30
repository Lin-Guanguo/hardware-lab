#!/usr/bin/env python3
"""Plan named connections with exact pad contacts and octilinear copper only."""
import argparse
import heapq
import json
import math
from pathlib import Path

import numpy as np
from shapely import contains_xy
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union, polygonize
from shapely.prepared import prep

from kicad_sexpr import child
from v4_geometry import geometry


def outline(board):
    edges = []
    for item in board:
        if not isinstance(item, list) or item[0] not in ('gr_line', 'gr_arc'):
            continue
        if child(item, 'layer')[1] != 'Edge.Cuts':
            continue
        p, q = [tuple(map(float, child(item, k)[1:3])) for k in ('start', 'end')]
        if item[0] == 'gr_line':
            edges.append(LineString([p, q]))
            continue
        m = tuple(map(float, child(item, 'mid')[1:3]))
        center = np.linalg.solve(2 * (np.array([m, q]) - p), np.array([np.dot(m,m), np.dot(q,q)]) - np.dot(p,p))
        angles = [math.atan2(x[1]-center[1], x[0]-center[0]) for x in (p,m,q)]
        sweep = (angles[2]-angles[0]) % (2*math.pi)
        if (angles[1]-angles[0]) % (2*math.pi) > sweep:
            sweep -= 2*math.pi
        radius = math.dist(p,center)
        pts = [tuple(center + radius*np.array([math.cos(a),math.sin(a)])) for a in np.linspace(angles[0],angles[0]+sweep,65)]
        edges.append(LineString([p,*pts[1:-1],q]))
    polygons = list(polygonize(unary_union(edges)))
    assert len(polygons) == 1
    return polygons[0]


def bends(p, q):
    dx, dy = q[0]-p[0], q[1]-p[1]
    sx, sy = (1 if dx>=0 else -1), (1 if dy>=0 else -1)
    d = min(abs(dx),abs(dy))
    return [[p,(p[0]+sx*d,p[1]+sy*d),q],
            [p,(q[0]-sx*d,q[1]-sy*d),q],
            [p,(q[0],p[1]),q], [p,(p[0],q[1]),q]]


def simplify(points, preserve=()):
    out = []
    for p in points:
        p = tuple(round(float(x),6) for x in p)
        if out and math.dist(out[-1],p)<1e-7:
            continue
        if len(out)>1:
            u,v = np.subtract(out[-1],out[-2]), np.subtract(p,out[-1])
            if abs(u[0]*v[1]-u[1]*v[0])<1e-7 and np.dot(u,v)>0 and not any(math.dist(out[-1],q)<1e-6 for q in preserve):
                out.pop()
        out.append(p)
    return out


def length(points):
    return sum(math.dist(p,q) for p,q in zip(points,points[1:]))


class Planner:
    def __init__(self, board_path, corridors=()):
        self.board,self.pads,self.objects,_ = geometry(board_path)
        self.outline = outline(self.board)
        self.layers = ('F.Cu','B.Cu')
        self.routes, self.vias = [], []
        self.corridors=corridors
        self.soft_obstacles=[]

    def add_via(self, hole):
        shape=Point(hole['at']).buffer(.3)
        hits=[o['name'] for o in self.objects if o['net']!=hole['net'] and o['shape'].distance(shape)<.2-1e-6]
        pads=[o['name'] for o in self.objects if o['kind']=='pad' and len(o['layers'])==1 and o['shape'].distance(Point(hole['at']))<.55-1e-6]
        if hits or pads:return {'via':hole,'copper':hits,'smt_drill_gap':pads}
        self.vias.append(hole)
        self.objects.append({'name':hole.get('name','assigned via'),'net':hole['net'],'layers':list(self.layers),'shape':shape,'kind':'via'})
        return None

    def point(self, value, net):
        if isinstance(value,str):
            pad = self.pads[value]
            assert pad['net'] == net,(value,pad['net'],net)
            return pad['at']
        return tuple(value)

    def component_points(self, point, net, layers, seed_layers):
        copper=[o for o in self.objects if o['net']==net]
        connected={i for i,o in enumerate(copper) if set(o['layers'])&{self.layers[l] for l in seed_layers} and o['shape'].distance(Point(point))<1e-6}
        pending=list(connected)
        while pending:
            obj=copper[pending.pop()]
            for i,o in enumerate(copper):
                if i not in connected and set(obj['layers'])&set(o['layers']) and obj['shape'].distance(o['shape'])<1e-6:
                    connected.add(i);pending.append(i)
        points=[]
        for i in connected:
            obj=copper[i]
            positions=obj.get('points',[obj.get('at',tuple(obj['shape'].centroid.coords[0]))])
            points.extend((self.layers.index(l),tuple(p)) for l in obj['layers'] if self.layers.index(l) in layers for p in positions)
        return list(set(points))

    def route(self, request):
        net,width = request['net'],request['width']
        pts = [self.point(p,net) for p in request['through']]
        layers = [self.layers.index(x) for x in request.get('layers',[request.get('layer','F.Cu')])]
        bounds = request.get('bounds',[min(x[0] for x in pts)-3,min(x[1] for x in pts)-3,max(x[0] for x in pts)+3,max(x[1] for x in pts)+3])
        outside = self.outline.envelope.buffer(5).difference(self.outline.buffer(-(.305+width/2)))
        reserved=[c for c in self.corridors if net not in c['nets']]
        shapes = {l:unary_union([outside,*[o['shape'].buffer(.205+width/2,quad_segs=8) for o in self.objects if o['net']!=net and self.layers[l] in o['layers']],*[box(*c['bounds']) for c in reserved if c['layer']==self.layers[l]]]) for l in layers}
        prepared = {l:prep(g) for l,g in shapes.items()}
        soft={l:[(o['shape'].buffer(.205+width/2),o.get('cost',5)) for o in self.soft_obstacles if o['net']!=net and self.layers[l] in o['layers']] for l in layers}
        def free(path,l):
            path=simplify(path)
            return not prepared[l].intersects(Point(path[0]) if len(path)<2 else LineString(path))
        def direct(p,q,l):
            choices=[simplify(c) for c in bends(p,q) if free(c,l) and not any(g.intersects(LineString(c)) for g,cost in soft[l])]
            return min(choices,key=length,default=None)
        full=[]
        for index,(start,end) in enumerate(zip(pts,pts[1:])):
            start_layer=self.layers.index(request.get('start_layer',self.layers[layers[0]])) if index==0 else full[-1][0]
            end_layer=self.layers.index(request.get('end_layer',self.layers[layers[0]]))
            # An existing plated via is already a legal transition. Do not
            # require room for a second via to access its other copper face.
            def available(point, preferred):
                if any(o['kind']=='via' and o['net']==net and math.dist(o.get('at',o['shape'].centroid.coords[0]),point)<.00001 for o in self.objects):
                    return layers
                return [preferred]
            start_layers,end_layers=available(start,start_layer),available(end,end_layer)
            sources=[(l,start) for l in start_layers]
            destinations=[(l,end) for l in end_layers]
            if request.get('join_existing_copper'):
                assert len(pts)==2, 'Component joins must not bypass explicitly assigned intermediate ports'
                sources=self.component_points(start,net,layers,start_layers) or sources
                destinations=self.component_points(end,net,layers,end_layers) or destinations
                if set(sources)&set(destinations):continue
            direct_options=[(l,direct(p,q,l)) for l,p in sources for dl,q in destinations if l==dl]
            direct_options=[(l,d) for l,d in direct_options if d]
            direct_options=[(l,d) for l,d in direct_options if not any(g.intersects(LineString(d)) for g,c in soft[l])]
            if direct_options:
                used,d=min(direct_options,key=lambda item:length(item[1]))
                if d:
                    full.extend((used,p) for p in d)
                    continue
            step=float(request.get('step',.1))
            x0,y0,x1,y1=bounds
            # Align the search lattice to the exact destination. A legal
            # closely pitched bus can otherwise lie between every grid row.
            x0 += (end[0]-x0) % step
            y0 += (end[1]-y0) % step
            nx,ny=math.floor((x1-x0)/step)+1,math.floor((y1-y0)/step)+1
            xx,yy=np.meshgrid(x0+np.arange(nx)*step,y0+np.arange(ny)*step)
            blocked={l:contains_xy(g,xx,yy) for l,g in shapes.items()}
            soft_cost={l:sum((contains_xy(g,xx,yy)*cost for g,cost in soft[l]),start=np.zeros(xx.shape)) for l in layers}
            via_blocked=None
            if len(layers)>1:
                forbidden=unary_union([self.outline.envelope.buffer(5).difference(self.outline.buffer(-.605)),
                    *[o['shape'].buffer(.505,quad_segs=8) for o in self.objects if o['net']!=net],
                    *[o['shape'].buffer(.55,quad_segs=8) for o in self.objects if o['kind']=='pad' and len(o['layers'])==1],*[box(*c['bounds']).buffer(.3) for c in reserved]])
                via_blocked=contains_xy(forbidden,xx,yy)
            def xy(i,j):return x0+i*step,y0+j*step
            def nearby(p,l):
                cx,cy=round((p[0]-x0)/step),round((p[1]-y0)/step)
                choices={}
                for i in range(cx-4,cx+5):
                    for j in range(cy-4,cy+5):
                        if 0<=i<nx and 0<=j<ny and not blocked[l][j,i]:
                            route=direct(p,xy(i,j),l)
                            if route:choices[(l,i,j)]=route
                return choices
            starts={}
            for l,p in sources:
                for k,v in nearby(p,l).items():
                    if k not in starts or length(v)<length(starts[k]):starts[k]=v
            ends={k:v for l,p in destinations for k,v in nearby(p,l).items()}
            if not starts or not ends:
                return {'reason':'Blocked endpoint','start':start,'end':end,'start_exits':len(starts),'end_exits':len(ends)}
            def heuristic(key):
                l,i,j=key;x,y=xy(i,j)
                return min(max(abs(x-p[0]),abs(y-p[1]))+(math.sqrt(2)-1)*min(abs(x-p[0]),abs(y-p[1]))+(request.get('via_cost',8) if l!=dl else 0) for dl,p in destinations)
            costs={k:length(v) for k,v in starts.items()}
            parents={k:None for k in starts}
            queue=[(v+heuristic(k),v,k) for k,v in costs.items()];heapq.heapify(queue)
            visited=set();winner=None
            while queue:
                _,cost,key=heapq.heappop(queue)
                if key in visited:continue
                visited.add(key)
                if key in ends:winner=key;break
                l,i,j=key
                candidates=[((l,i+dx,j+dy),step*math.hypot(dx,dy)) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))]
                if via_blocked is not None and not via_blocked[j,i]:
                    candidates.append(((1-l,i,j),request.get('via_cost',8)))
                for k,delta in candidates:
                    nl,ni,nj=k
                    if k in visited or not (0<=ni<nx and 0<=nj<ny) or blocked[nl][nj,ni]:continue
                    if nl==l and not free([xy(i,j),xy(ni,nj)],l):continue
                    turn=0
                    parent=parents[key]
                    if parent and parent[0]==l==nl:
                        prev=(i-parent[1],j-parent[2]);now=(ni-i,nj-j)
                        if prev!=now:turn=.03
                    nc=cost+delta+turn+soft_cost[nl][nj,ni]
                    if nc<costs.get(k,float('inf')):
                        costs[k],parents[k]=nc,key
                        heapq.heappush(queue,(nc+heuristic(k),nc,k))
            if winner is None:
                closest=min(visited,key=lambda k:math.dist(xy(k[1],k[2]),end))
                cp=xy(closest[1],closest[2]);probe=LineString([cp,end])
                blockers=[{'name':o['name'],'net':o['net'],'kind':o['kind']} for o in self.objects if o['net']!=net and self.layers[closest[0]] in o['layers'] and o['shape'].distance(probe)<.205+width/2]
                return {'reason':'No path in assigned corridor','start':start,'end':end,'visited':len(visited),'closest_reached':{'layer':self.layers[closest[0]],'point':cp,'distance':math.dist(cp,end)},'direct_blockers':blockers}
            nodes=[];k=winner
            while k is not None:nodes.append(k);k=parents[k]
            nodes.reverse()
            section=[(nodes[0][0],p) for p in starts[nodes[0]]]
            section.extend((l,xy(i,j)) for l,i,j in nodes[1:])
            section.extend((winner[0],p) for p in reversed(ends[winner]))
            full.extend(section)
        groups=[]
        for l,p in full:
            if not groups or groups[-1][0]!=l:
                if groups:
                    at=p
                    hole={'net':net,'at':list(at)}
                    if not any(o['kind']=='via' and o['net']==net and math.dist(o.get('at',o['shape'].centroid.coords[0]),at)<.00001 for o in self.objects):
                        self.vias.append(hole)
                        self.objects.append({'name':request['name']+' via','net':net,'layers':list(self.layers),'shape':Point(at).buffer(.3),'kind':'via'})
                groups.append((l,[p]))
            else:groups[-1][1].append(p)
        for l,points in groups:
            points=simplify(points,pts[1:-1])
            # Long-range shortcutting is constrained to exact H/V/45 bends.
            anchors={i for i,p in enumerate(points) if any(math.dist(p,q)<1e-6 for q in pts[1:-1])}
            result=[points[0]];i=0
            while i<len(points)-1:
                best=None
                for j in range(len(points)-1,i,-1):
                    if any(i<k<j for k in anchors):continue
                    d=direct(points[i],points[j],l)
                    if d and length(d)<=length(points[i:j+1])+1e-5:
                        best=(j,d);break
                j,d=best or (i+1,[points[i],points[i+1]])
                result.extend(d[1:]);i=j
            result=simplify(result)
            if len(result)<2:continue
            for p,q in zip(result,result[1:]):
                dx,dy=abs(q[0]-p[0]),abs(q[1]-p[1])
                assert min(dx,dy,abs(dx-dy))<2e-6,(p,q)
            item={'name':request['name'],'net':net,'layer':self.layers[l],'width':width,'points':result,'length_mm':round(LineString(result).length,3)}
            self.routes.append(item)
            self.objects.append({'name':request['name'],'net':net,'layers':[self.layers[l]],'shape':LineString(result).buffer(width/2),'kind':'track','points':result})
        return None


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('spec',type=Path);a=ap.parse_args()
    spec=json.loads(a.spec.read_text());planner=Planner(spec.get('model_board',spec['board']),spec.get('reserved_corridors',[]));failures=[]
    for hole in spec.get('vias',[]):
        result=planner.add_via(hole)
        if result:failures.append(result)
    for request in spec['paths']:
        result=planner.route(request)
        if result:failures.append({'name':request['name'],**result})
        print(json.dumps({'name':request['name'],'result':result or 'routed'}),flush=True)
    out={k:spec[k] for k in ('board','description','record')}
    out.update(routes=planner.routes,vias=planner.vias,failures=failures)
    output=a.spec.with_name(a.spec.stem+'-plan.json');output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'output':str(output),'routes':len(planner.routes),'vias':len(planner.vias),'failures':len(failures)}))


if __name__=='__main__':main()
