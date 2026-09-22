#!/usr/bin/env python3
"""Two-layer grid maze router for a PCB net list.

Usage:
  pcb-maze-router.py --dump SNAPSHOT.json --tasks TASKS.json [--rip RIP.json]
                     [--width 0.15] [--pen 40] [--out routes.json]

The snapshot is produced from EasyEDA with a small script that serialises
pcb_PrimitiveLine / pcb_PrimitiveVia / pcb_PrimitivePad into
{lines, vias, pads}.  Coordinates in the snapshot are mil; everything printed
and written by this tool is millimetre.

Design rules used for obstacle inflation (JLCPCB Capability, 1 oz):
  track-track 0.102 mm, pad/via-track 0.152 mm, board edge 0.300 mm.

The tool never edits the project: it writes a routes.json that a separate
EasyEDA script turns into pcb_PrimitiveLine.create / pcb_PrimitiveVia.create
calls.  Always re-run native DRC after applying, and remember that the DRC
panel in 3.2.203 is asynchronous: trigger, wait, re-read, and reopen the page
for the true numbers.
"""
import argparse, json, math, sys, time
import numpy as np
from collections import defaultdict

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--dump', required=True)
ap.add_argument('--tasks', required=True)
ap.add_argument('--rip', default=None)
ap.add_argument('--width', type=float, default=0.20, help='track width in mm')
ap.add_argument('--pen', type=int, default=30, help='congestion cost per use')
ap.add_argument('--out', default='routes.json')
args = ap.parse_args()

DUMP_PATH = args.dump
TASKS_PATH = args.tasks
RIP_PATH = args.rip
OUT_PATH = args.out
HW_TRACK = args.width / 2
PEN_DEFAULT = args.pen

S = 39.3701
GRID = 0.1
W, H = 84.0, 52.0
NX, NY = int(W/GRID)+1, int(H/GRID)+1
PLANE = NY*NX
CL_TT, CL_PT, CL_VT, CL_VP, CL_EDGE = 0.102, 0.152, 0.152, 0.152, 0.300
VIA_OD, VIA_DR = 0.30, 0.20
HW_VIA = VIA_OD/2
HOLE_CLEARANCE = 0.30        # hole-to-hole; applies to every net, including the one being routed
OUTLINE = [(34,0),(34,15),(0,15),(0,52),(84,52),(84,20.62),(77.5,20.62),(77.5,11.38),(84,11.38),(84,0)]
# prohibited region (keepout) x 60.0-82.0, y 24.0-50.0 mm, all layers
KEEPOUT = [(60.0, 24.0, 82.0, 50.0)]

def mm(v): return v/S
xs = np.arange(NX)*GRID; ys = np.arange(NY)*GRID
XX, YY = np.meshgrid(xs, ys)
INSIDE = np.zeros((NY, NX), bool)
for i in range(len(OUTLINE)):
    x1,y1 = OUTLINE[i]; x2,y2 = OUTLINE[(i+1) % len(OUTLINE)]
    cond = ((y1 > YY) != (y2 > YY))
    with np.errstate(divide='ignore', invalid='ignore'):
        xi = (x2-x1)*(YY-y1)/(y2-y1) + x1
    INSIDE ^= (cond & (XX < xi))

def pad_box(p):
    pad = p.get('pad') or []
    if not pad: return None
    shape = pad[0].upper()
    w = mm(pad[1]) if len(pad) > 1 else 0.0
    h = mm(pad[2]) if len(pad) > 2 else w
    if shape.startswith('ELL') or shape == 'CIRCLE': w = h = max(w, h)
    if (p.get('rot') or 0) % 180 == 90: w, h = h, w
    x, y = mm(p['x']), mm(p['y'])
    return {'x0':x-w/2,'y0':y-h/2,'x1':x+w/2,'y1':y+h/2,'ell':shape.startswith('ELL'),
            'layer':p['layer'],'net':p['net'] or '','cx':x,'cy':y,'id':p['id'],'num':p['num']}

def pad_layers(p):
    return [0, 1] if p['layer'] not in (1, 2) else [p['layer']-1]

_d = json.load(open(DUMP_PATH))
pads = [b for b in (pad_box(p) for p in _d['pads']) if b]
lines = [{'net':l['net'] or '','layer':l['layer'],'x1':mm(l['x1']),'y1':mm(l['y1']),
          'x2':mm(l['x2']),'y2':mm(l['y2']),'hw':mm(l['w'])/2,'new':False} for l in _d['lines'] if l['net']]
vias = [{'net':v['net'] or '','x':mm(v['x']),'y':mm(v['y']),'rad':mm(v['od'])/2,'new':False} for v in _d['vias']]

def cells(shape_items, r):
    """shape_items: list of dicts with x0,y0,x1,y1 (rect/ell) or x1,y1,x2,y2,hw (segment)"""
    out = []
    for it in shape_items:
        if 'hw' in it:
            x1,y1,x2,y2 = it['x1'],it['y1'],it['x2'],it['y2']
            rad = it['hw'] + r
        else:
            x1,y1,x2,y2 = it['x0'],it['y0'],it['x1'],it['y1']; rad = r
        c0 = max(0,int(math.floor((min(x1,x2)-rad)/GRID))); c1 = min(NX-1,int(math.ceil((max(x1,x2)+rad)/GRID)))
        r0 = max(0,int(math.floor((min(y1,y2)-rad)/GRID))); r1 = min(NY-1,int(math.ceil((max(y1,y2)+rad)/GRID)))
        if c1 < c0 or r1 < r0: continue
        GX, GY = np.meshgrid(xs[c0:c1+1], ys[r0:r1+1])
        if 'hw' in it:
            dx, dy = x2-x1, y2-y1; L2 = dx*dx+dy*dy
            if L2 == 0: dist = np.hypot(GX-x1, GY-y1)
            else:
                t = np.clip(((GX-x1)*dx + (GY-y1)*dy)/L2, 0, 1)
                dist = np.hypot(GX-(x1+t*dx), GY-(y1+t*dy))
            m = dist <= rad
        elif it.get('ell'):
            m = np.hypot(GX-(x1+x2)/2, GY-(y1+y2)/2) <= (x2-x1)/2 + r
        else:
            dx = np.maximum(np.maximum(x1-GX, GX-x2), 0.0); dy = np.maximum(np.maximum(y1-GY, GY-y2), 0.0)
            m = np.hypot(dx,dy) <= r
        yy, xx = np.nonzero(m)
        out.append(((r0+yy).astype(np.int32), (c0+xx).astype(np.int32)))
    return out

def as_seg(pad):
    return pad  # rect items already have x0..

def build(net_keep, hw_track, hw_via):
    tr = np.zeros((2,NY,NX), bool); vi = np.zeros((2,NY,NX), bool)
    pad_i = []
    for p in pads:
        if p['net'] == net_keep: continue
        pad_i.append(p)
    for yy, xx in cells(pad_i, CL_PT + hw_track):
        for L in (0,1):
            sel = np.ones(yy.shape, bool)
            tr[L, yy, xx] = True   # conservatively mark both layers for pads (TH pads); SMD only one
    # refine: SMD pads only on their layer
    tr[:] = False; vi[:] = False
    for p in pads:
        if p['net'] == net_keep: continue
        for L in pad_layers(p):
            for yy, xx in cells([p], CL_PT + hw_track): tr[L, yy, xx] = True
            for yy, xx in cells([p], CL_VP + hw_via):   vi[L, yy, xx] = True
    for l in lines:
        if l['net'] == net_keep: continue
        for yy, xx in cells([l], CL_TT + hw_track): tr[l['layer']-1, yy, xx] = True
        for yy, xx in cells([l], CL_VT + hw_via):   vi[l['layer']-1, yy, xx] = True
    for v in vias:
        if v['net'] == net_keep: continue
        it = {'x0':v['x']-v['rad'],'y0':v['y']-v['rad'],'x1':v['x']+v['rad'],'y1':v['y']+v['rad'],'ell':True}
        for yy, xx in cells([it], CL_VT + hw_track): tr[:, yy, xx] = True
        for yy, xx in cells([it], CL_VP + hw_via):   vi[:, yy, xx] = True
    for i in range(len(OUTLINE)):
        x1,y1 = OUTLINE[i]; x2,y2 = OUTLINE[(i+1) % len(OUTLINE)]
        seg = {'x1':x1,'y1':y1,'x2':x2,'y2':y2,'hw':0.0}
        for yy, xx in cells([seg], CL_EDGE + hw_track): tr[:, yy, xx] = True
        for yy, xx in cells([seg], CL_EDGE + hw_via):   vi[:, yy, xx] = True
    for (kx0, ky0, kx1, ky1) in KEEPOUT:
        m = CL_PT + max(hw_track, hw_via)
        yy, xx = np.nonzero((xs[None, :] >= kx0 - m) & (xs[None, :] <= kx1 + m) & (ys[:, None] >= ky0 - m) & (ys[:, None] <= ky1 + m))
        tr[:, yy, xx] = True
        vi[:, yy, xx] = True
    # hole-to-hole clearance applies to same-net vias too, so mark every hole
    for v in vias:
        it = {'x0': v['x']-v['rad'], 'y0': v['y']-v['rad'], 'x1': v['x']+v['rad'], 'y1': v['y']+v['rad'], 'ell': True}
        for yy, xx in cells([it], HOLE_CLEARANCE):
            vi[0, yy, xx] = True; vi[1, yy, xx] = True
    for p in pads:
        if not p.get('hole'): continue
        for yy, xx in cells([p], HOLE_CLEARANCE):
            vi[0, yy, xx] = True; vi[1, yy, xx] = True
    tr[:, ~INSIDE] = True; vi[:, ~INSIDE] = True
    return ~tr, ~vi

# ---------- connectivity ----------
def seg_pt_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1; L2 = dx*dx+dy*dy
    if L2 == 0: return math.hypot(px-x1, py-y1)
    t = max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/L2))
    return math.hypot(px-(x1+t*dx), py-(y1+t*dy))

def seg_int(a,b):
    x1,y1,x2,y2 = a; x3,y3,x4,y4 = b
    d1=(x2-x1)*(y3-y1)-(y2-y1)*(x3-x1); d2=(x2-x1)*(y4-y1)-(y2-y1)*(x4-x1)
    d3=(x4-x3)*(y1-y3)-(y4-y3)*(x1-x3); d4=(x4-x3)*(y2-y3)-(y4-y3)*(x2-x3)
    return ((d1>0)!=(d2>0)) and ((d3>0)!=(d4>0))

class DSU:
    def __init__(s,n): s.p=list(range(n))
    def f(s,x):
        while s.p[x]!=x: s.p[x]=s.p[s.p[x]]; x=s.p[x]
        return x
    def u(s,a,b):
        ra,rb=s.f(a),s.f(b)
        if ra!=rb: s.p[rb]=ra

def components(net):
    ls=[l for l in lines if l['net']==net]; vs=[v for v in vias if v['net']==net]; ps=[p for p in pads if p['net']==net]
    NL,NV,NP=len(ls),len(vs),len(ps); dsu=DSU(NL+NV+NP)
    for i in range(NL):
        a=ls[i]
        for j in range(i+1,NL):
            b=ls[j]
            if a['layer']!=b['layer']: continue
            if seg_int((a['x1'],a['y1'],a['x2'],a['y2']),(b['x1'],b['y1'],b['x2'],b['y2'])): dsu.u(i,j); continue
            if seg_pt_dist(a['x1'],a['y1'],b['x1'],b['y1'],b['x2'],b['y2'])<0.06: dsu.u(i,j); continue
            if seg_pt_dist(a['x2'],a['y2'],b['x1'],b['y1'],b['x2'],b['y2'])<0.06: dsu.u(i,j)
    for k,v in enumerate(vs):
        for i,a in enumerate(ls):
            if seg_pt_dist(v['x'],v['y'],a['x1'],a['y1'],a['x2'],a['y2'])<=v['rad']+0.02: dsu.u(NL+k,i)
        for pi,p in enumerate(ps):
            if p['x0']-0.02<=v['x']<=p['x1']+0.02 and p['y0']-0.02<=v['y']<=p['y1']+0.02: dsu.u(NL+k,NL+NV+pi)
    for pi,p in enumerate(ps):
        for i,a in enumerate(ls):
            if (a['layer']-1) not in pad_layers(p): continue
            hit=False
            if p['x0']<=a['x1']<=p['x1'] and p['y0']<=a['y1']<=p['y1']: hit=True
            if p['x0']<=a['x2']<=p['x1'] and p['y0']<=a['y2']<=p['y1']: hit=True
            if not hit:
                for e in ((p['x0'],p['y0'],p['x1'],p['y0']),(p['x0'],p['y1'],p['x1'],p['y1']),
                          (p['x0'],p['y0'],p['x0'],p['y1']),(p['x1'],p['y0'],p['x1'],p['y1'])):
                    if seg_int((a['x1'],a['y1'],a['x2'],a['y2']),e): hit=True; break
            if hit: dsu.u(NL+NV+pi,i)
    for i in range(NP):
        for j in range(i+1,NP):
            a,b=ps[i],ps[j]
            if not (set(pad_layers(a)) & set(pad_layers(b))): continue
            if a['x0']<b['x1'] and b['x0']<a['x1'] and a['y0']<b['y1'] and b['y0']<a['y1']: dsu.u(NL+NV+i,NL+NV+j)
    g=defaultdict(list)
    for i,l in enumerate(ls): g[dsu.f(i)].append(('line',l))
    for k,v in enumerate(vs): g[dsu.f(NL+k)].append(('via',v))
    for pi,p in enumerate(ps): g[dsu.f(NL+NV+pi)].append(('pad',p))
    return list(g.values())

def group_mask(group):
    m=np.zeros((2,NY,NX),bool)
    for kind,it in group:
        if kind=='line':
            for yy,xx in cells([it],0.0): m[it['layer']-1,yy,xx]=True
        elif kind=='via':
            ob={'x0':it['x']-it['rad'],'y0':it['y']-it['rad'],'x1':it['x']+it['rad'],'y1':it['y']+it['rad'],'ell':True}
            for yy,xx in cells([ob],0.0): m[:,yy,xx]=True
        else:
            for L in pad_layers(it):
                for yy,xx in cells([it],0.0): m[L,yy,xx]=True
    return m

# ---------- dijkstra ----------
VNEIGH=[(1,0,10),(-1,0,10),(0,1,10),(0,-1,10),(1,1,14),(1,-1,14),(-1,1,14),(-1,-1,14)]
VIA_COST=400

def route(src_mask, goal_mask, track_free, via_free, usage=None, PEN=30):
    dist=np.full((2,NY,NX),np.int32(1<<30),np.int32)
    pred=np.full((2,NY,NX),np.int32(-1),np.int32)
    buckets=defaultdict(list); maxd=0
    for L in (0,1):
        yy,xx=np.nonzero(src_mask[L]&track_free[L])
        if yy.size:
            dist[L,yy,xx]=0
            buckets[0].append((L*PLANE+yy.astype(np.int64)*NX+xx).astype(np.int32))
    gidx=[]
    for L in (0,1):
        yy,xx=np.nonzero(goal_mask[L]&track_free[L])
        if yy.size:
            gidx.append(np.stack([np.full(yy.size,L,np.int32),yy.astype(np.int32),xx.astype(np.int32)],1))
    if not gidx: return None
    G=np.concatenate(gidx,0)
    Gflat=(G[:,0].astype(np.int64)*PLANE+G[:,1].astype(np.int64)*NX+G[:,2]).astype(np.int64)
    cur=0; hit=None
    while cur<=maxd:
        bl=buckets.pop(cur,None)
        if bl is None:
            cur+=1; continue
        flats=np.concatenate(bl)
        lay=(flats//PLANE).astype(np.int32); rem=(flats%PLANE)
        py=(rem//NX).astype(np.int32); px=(rem%NX).astype(np.int32)
        keep=dist[lay,py,px]==cur
        if keep.any():
            lay,py,px=lay[keep],py[keep],px[keep]
            for dx,dy,w in VNEIGH:
                qx=px+dx; qy=py+dy
                ok=(qx>=0)&(qx<NX)&(qy>=0)&(qy<NY)
                if not ok.any(): continue
                l2,qx,qy = lay[ok],qx[ok],qy[ok]
                sl,sx,sy = lay[ok],px[ok],py[ok]
                good=track_free[l2,qy,qx]
                if not good.any(): continue
                l2,qx,qy,sl,sx,sy = l2[good],qx[good],qy[good],sl[good],sx[good],sy[good]
                extra = (usage[l2,qy,qx]*PEN) if usage is not None else 0
                dnew = cur + w + extra
                better = dnew < dist[l2,qy,qx]
                if not better.any(): continue
                l2,qx,qy,sl,sx,sy,dnew = l2[better],qx[better],qy[better],sl[better],sx[better],sy[better],dnew[better]
                dist[l2,qy,qx]=dnew
                pred[l2,qy,qx]=(sl.astype(np.int64)*PLANE+sy.astype(np.int64)*NX+sx).astype(np.int32)
                uvals=np.unique(dnew)
                for u in uvals:
                    selk = dnew==u
                    flat=(l2[selk].astype(np.int64)*PLANE+qy[selk].astype(np.int64)*NX+qx[selk]).astype(np.int32)
                    buckets[int(u)].append(flat)
                    maxd=max(maxd,int(u))
            for sl in (0,1):
                sel=lay==sl
                if not sel.any(): continue
                qx,qy=px[sel],py[sel]
                good=via_free[1-sl,qy,qx]&via_free[sl,qy,qx]
                if not good.any(): continue
                qx,qy=qx[good],qy[good]
                better=(cur+VIA_COST)<dist[1-sl,qy,qx]
                if not better.any(): continue
                qx,qy=qx[better],qy[better]
                dist[1-sl,qy,qx]=cur+VIA_COST
                pred[1-sl,qy,qx]=(sl*PLANE+qy.astype(np.int64)*NX+qx).astype(np.int32)
                buckets[cur+VIA_COST].append(((1-sl)*PLANE+qy.astype(np.int64)*NX+qx).astype(np.int32))
                maxd=max(maxd,cur+VIA_COST)
        if hit is None:
            dd=np.where(dist.reshape(-1)[Gflat]<=(1<<30),dist.reshape(-1)[Gflat],1<<30)
            dmin=dist[G[:,0],G[:,1],G[:,2]].min() if G.size else 1<<30
            if dmin<=cur:
                k=int(np.argmin(dist[G[:,0],G[:,1],G[:,2]]))
                hit=(int(G[k,0]),int(G[k,2]),int(G[k,1]))
        if hit is not None and dist[hit[0],hit[2],hit[1]]<=cur: break
        cur+=1
    if hit is None: return None
    path=[]; L,x,y=hit
    while True:
        path.append((int(L),int(x),int(y)))
        if dist[L,y,x]==0: break
        p=int(pred[L,y,x])
        if p<0: break
        L=int(p//PLANE); rem=int(p%PLANE); y=rem//NX; x=rem%NX
    path.reverse()
    return path

def path_to_items(path, net):
    """path: list of (layer, cellx, celly). Returns (segments, vias) in mm."""
    wp=[path[0]]
    for k in range(1,len(path)-1):
        l0,x0,y0=path[k-1]; l1,x1,y1=path[k]; l2,x2,y2=path[k+1]
        if l1!=l0 or l2!=l1: wp.append(path[k]); continue
        d1x,d1y=x1-x0,y1-y0; d2x,d2y=x2-x1,y2-y1
        if d1x*d2y-d1y*d2x!=0 or d1x*d2x<0 or d1y*d2y<0: wp.append(path[k])
    wp.append(path[-1])
    out=[wp[0]]
    for k in range(1,len(wp)):
        l,x,y=wp[k]
        l0,x0,y0=out[-1]
        if l==l0 and x==x0 and y==y0: continue
        if l!=l0:
            out.append(wp[k]); continue
        if len(out)>=2:
            l1,x1,y1=out[-2]
            if l1==l:
                d1=(x0-x1,y0-y1); d2=(x-x0,y-y0)
                if d1[0]*d2[1]-d1[1]*d2[0]==0 and d1[0]*d2[0]>=0 and d1[1]*d2[1]>=0:
                    out[-1]=wp[k]; continue
        out.append(wp[k])
    segs=[]; vlist=[]
    for i in range(len(out)-1):
        l1,x1,y1=out[i]; l2,x2,y2=out[i+1]
        X1,Y1,X2,Y2=x1*GRID,y1*GRID,x2*GRID,y2*GRID
        if l1!=l2:
            vlist.append({'net':net,'x':X1,'y':Y1,'rad':HW_VIA,'new':True})
        elif X1!=X2 or Y1!=Y2:
            segs.append({'net':net,'layer':l1+1,'x1':X1,'y1':Y1,'x2':X2,'y2':Y2,'hw':HW_TRACK,'new':True})
    return segs, vlist


# --- rip up traces that block the remaining connections (author: auto-router local loop) ---
RIP = json.load(open(RIP_PATH)) if RIP_PATH else []
RIP_UNUSED_UNUSED = [
  ("SYS", 46.770,18.504, 47.110,18.504),
  ("SYS", 47.110,18.504, 47.364,18.758),
  ("SYS", 47.364,18.758, 47.364,21.298),
  ("SYS", 47.364,21.298, 47.110,21.552),
  ("SYS", 47.110,21.552, 45.744,21.552),
  ("SYS", 45.744,21.552, 45.020,20.828),
  ("EPD_DC_TBD", 53.882,33.250, 54.390,32.742),
  ("EPD_DC_TBD", 54.390,32.742, 54.390,26.138),
  ("EPD_BUSY_TBD", 53.800,19.000, 53.800,31.500),
  ("EPD_BUSY_TBD", 53.800,31.500, 52.600,31.500),
  ("CHG_SCL", 44.671,19.304, 44.330,19.304),
  ("CHG_SCL", 44.330,19.304, 43.695,18.669),
  ("CHG_SCL", 43.695,18.669, 43.695,18.415),
  ("CHG_SCL", 43.695,18.415, 44.076,18.034),
  ("CHG_SCL", 44.076,18.034, 50.172,18.034),
  ("CHG_SCL", 50.172,18.034, 51.299,19.161),
  ("CHG_SCL", 51.299,19.161, 51.299,23.876),
  ("CHG_SCL", 51.299,23.876, 50.283,24.892),
]
def close(a,b,t=0.03): return abs(a-b)<=t
removed=0
for net,x1,y1,x2,y2 in RIP:
    keep=[]
    for l in lines:
        fwd = close(l['x1'],x1) and close(l['y1'],y1) and close(l['x2'],x2) and close(l['y2'],y2)
        rev = close(l['x1'],x2) and close(l['y1'],y2) and close(l['x2'],x1) and close(l['y2'],y1)
        if l['net']==net and (fwd or rev): removed+=1; continue
        keep.append(l)
    lines[:] = keep
print('ripped segments:', removed, flush=True)

USAGE=np.zeros((2,NY,NX),np.int32)
def bump(mask, amt=1, halo=True):
    m=mask.copy()
    if halo:
        m2=m.copy()
        m2[1:,:]|=m[:-1,:]; m2[:-1,:]|=m[1:,:]
        m2[:,1:]|=m[:,:-1]; m2[:,:-1]|=m[:,1:]
        m=m2
    USAGE[m]+=amt

def find_pad(x,y):
    best=None; bd=1e9
    for p in pads:
        d=((p['cx']-x)**2+(p['cy']-y)**2)**0.5
        if d<bd: bd=d; best=p
    return best, bd

TASKS = json.load(open(TASKS_PATH))
out=[]
for net, srcpt, goals in TASKS:
    t0=time.time()
    comps = components(net)
    sp,_ = find_pad(*srcpt)
    src_comp = None
    for c in comps:
        if any(k=='pad' and it['id']==sp['id'] for k,it in c): src_comp=c
    if src_comp is None:
        print(net, 'SOURCE PAD NOT FOUND', flush=True); continue
    srcmask = group_mask(src_comp)
    tf, vf = build(net, HW_TRACK, HW_VIA)
    rec={'net':net,'segments':[],'vias':[],'status':[]}
    for gp in goals:
        gp_pad,_ = find_pad(*gp)
        goalmask = np.zeros((2,NY,NX),bool)
        for yy,xx in cells([gp_pad],0.0):
            for L in pad_layers(gp_pad): goalmask[L,yy,xx]=True
        p = route(srcmask, goalmask, tf, vf, usage=USAGE, PEN=PEN_DEFAULT)
        if p is None:
            rec['status'].append(['FAIL', list(gp)]); continue
        segs, vlist = path_to_items(p, net)
        rec['segments'] += segs; rec['vias'] += vlist
        rec['status'].append(['OK', list(gp), len(segs), len(vlist)])
        for s in segs:
            lines.append(s)
            for yy,xx in cells([s],0.0): srcmask[s['layer']-1,yy,xx]=True
        for s in segs:
            for yy,xx in cells([s],0.0): bump_sel = (s['layer']-1, yy, xx)
        pathmask=np.zeros((2,NY,NX),bool)
        for s in segs:
            for yy,xx in cells([s],0.0): pathmask[s['layer']-1,yy,xx]=True
        for v in vlist:
            ob={'x0':v['x']-v['rad'],'y0':v['y']-v['rad'],'x1':v['x']+v['rad'],'y1':v['y']+v['rad'],'ell':True}
            for yy,xx in cells([ob],0.0): pathmask[:,yy,xx]=True
        bump(pathmask)
        for v in vlist:
            vias.append(v)
            ob={'x0':v['x']-v['rad'],'y0':v['y']-v['rad'],'x1':v['x']+v['rad'],'y1':v['y']+v['rad'],'ell':True}
            for yy,xx in cells([ob],0.0): srcmask[:,yy,xx]=True
    rec['secs']=round(time.time()-t0,1)
    out.append(rec)
    print(net, rec['status'], rec['secs'], flush=True)
json.dump(out, open(OUT_PATH,'w'), indent=1)
print('wrote', OUT_PATH)
