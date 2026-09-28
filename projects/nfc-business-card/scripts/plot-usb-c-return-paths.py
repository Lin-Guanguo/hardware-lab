#!/usr/bin/env python3
"""Plot geometric paths through actual GND copper, not simulated current density."""
import argparse
import heapq
import importlib.util
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from shapely import contains_xy
from shapely.geometry import LineString
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--candidate',choices=['c','d'],default='c');args=parser.parse_args()
STEM=ROOT/('hardware/records/usb-power-return-c' if args.candidate=='c' else 'hardware/records/board-review-d')
s=json.loads(Path(f'{STEM}-snapshot.json').read_text())
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('check-r1-copper.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
shapes,_=audit.copper(s);ground={l:unary_union(shapes['GND',l]) for l in (1,2)}
pads={(c['ref'],p['number']):p for c in s['components'] for p in s['pads'] if p['id'].startswith(c['id'])}
step=.025 if args.candidate=='d' else .1;erosion=.005 if args.candidate=='d' else .02;xs=np.arange(36.5 if args.candidate=='d' else 43,82.81,step);ys=np.arange(1.3 if args.candidate=='d' else 12.8,50.61 if args.candidate=='d' else 32.11,step);nx=len(xs);ny=len(ys);size=nx*ny
X,Y=np.meshgrid(xs,ys)
# Slight erosion rejects an apparent connection only along a sampled polygon edge.
valid=np.concatenate([contains_xy(ground[l].buffer(-erosion),X,Y).ravel() for l in (1,2)])
def node(x,y,l):return (l-1)*size+int(round((y-ys[0])/step))*nx+int(round((x-xs[0])/step))
def point(n):
 l,k=divmod(n,size);row,col=divmod(k,nx);return float(xs[col]),float(ys[row]),l+1
links={}
for v in s['vias']:
 if v['net']!='GND':continue
 x,y=v['x']*.0254,v['y']*.0254
 if not(xs[0]<=x<=xs[-1] and ys[0]<=y<=ys[-1]):continue
 a,b=node(x,y,1),node(x,y,2)
 assert valid[a] and valid[b]
 links[a]=b;links[b]=a
# Shell slots are also plated layer connections; their center is a conceptual node.
for (r,n),p in pads.items():
 if p['net']=='GND' and p['layer']==12:
  a,b=node(p['x']*.0254,p['y']*.0254,1),node(p['x']*.0254,p['y']*.0254,2)
  if 0<=a<size and size<=b<2*size and valid[a] and valid[b]:links[a]=b;links[b]=a

def path_between(start,end):
 start=node(*start);end=node(*end);assert valid[start] and valid[end]
 q=[(0,start)];best={start:0};previous={}
 while q:
  d,n=heapq.heappop(q)
  if d!=best[n]:continue
  if n==end:break
  layer,k=divmod(n,size);row,col=divmod(k,nx)
  candidates=[]
  for dr,dc in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
   rr,cc=row+dr,col+dc
   if not (0<=rr<ny and 0<=cc<nx):continue
   m=layer*size+rr*nx+cc
   if not valid[m]:continue
   if dr and dc and not(valid[layer*size+row*nx+cc] and valid[layer*size+rr*nx+col]):continue
   candidates.append((m,step*math.hypot(dr,dc)))
  if n in links:candidates.append((links[n],.8))
  for m,cost in candidates:
   nd=d+cost
   if nd<best.get(m,float('inf')):best[m]=nd;previous[m]=n;heapq.heappush(q,(nd,m))
 assert end in best,('No geometric copper path',point(start),point(end),len(best))
 nodes=[end]
 while nodes[-1]!=start:nodes.append(previous[nodes[-1]])
 return [point(n) for n in nodes[::-1]],best[end]

def pin(ref,num):
 p=pads[ref,num];return p['x']*.0254,p['y']*.0254,1
paths=[]
for label,ref,num,color in [('C8 ground to inlet','C8','2','#36738d'),('U1 USB ground to inlet','U1','33','#7c5eb3'),('U5 ESD ground to inlet','U5','3','#d24f55'),('U6 ESD ground to inlet','U6','3','#a07d18')]:
 points,length=path_between(pin(ref,num),pin('J1','A1B12'))
 paths.append({'label':label,'color':color,'grid_geometric_length_mm':length,'points_xyz_mm':points})
fig,axes=plt.subplots(2,2,figsize=(16,12) if args.candidate=='d' else (16,10))
for col,group in enumerate([paths[:2],paths[2:]]):
 for row,layer in enumerate([1,2]):
  ax=axes[row,col]
  for (net,l),parts in sorted(shapes.items(),key=lambda item:item[0][0]!='GND'):
   if l!=layer:continue
   merged=unary_union(parts)
   for g in getattr(merged,'geoms',[merged]):
    if not hasattr(g,'exterior'):continue
    ax.fill(*g.exterior.xy,color='#cce4d7' if net=='GND' else '#e5a26e' if net=='USB_VBUS' else '#c9d1e2',alpha=.85)
    for hole in g.interiors:ax.fill(*hole.xy,color='white')
  for p in group:
   pts=p['points_xyz_mm']
   for a,b in zip(pts,pts[1:]):
    if a[2]==b[2]==layer:ax.plot([a[0],b[0]],[a[1],b[1]],color=p['color'],lw=1.8)
    elif a[2]!=b[2]:ax.plot(a[0],a[1],'o',ms=4,mec=p['color'],mfc='white')
   ax.plot([],[],color=p['color'],label=p['label'])
  if layer==1:
   ax.annotate('',xy=(65,19.65),xytext=(68,19.65),arrowprops={'arrowstyle':'->','color':'#9e4d1a','lw':2})
   ax.annotate('',xy=(60,17.5),xytext=(60,19.2),arrowprops={'arrowstyle':'->','color':'#9e4d1a','lw':1.5})
  else:
   ax.annotate('',xy=(48,17.7),xytext=(49.4,17.7),arrowprops={'arrowstyle':'->','color':'#9e4d1a','lw':1.5})
  for c in s['components']:
   if c['ref'] in ['J1','U1','U2','C1','C8','U5','U6']:
    x,y=c['x']*.0254,c['y']*.0254
    if 43<x<78 and 13<y<31:ax.text(x,y,c['ref'],fontsize=8)
  if col==0:
   for v in s['vias']:
    if v['net'] in ['USB_DP_CONN','USB_DM_CONN']:
     x,y=v['x']*.0254,v['y']*.0254;ax.plot(x,y,'o',ms=6,mfc='none',mec='#2749ac')
     _,g=min((math.hypot(x-g['x']*.0254,y-g['y']*.0254),i) for i,g in enumerate(s['vias']) if g['net']=='GND')
     gv=s['vias'][g];gx,gy=gv['x']*.0254,gv['y']*.0254
     ax.plot([x,gx],[y,gy],':',color='#2749ac',lw=.8);ax.plot(gx,gy,'o',ms=4,mfc='none',mec='#2749ac')
  ax.set(xlim=(36.5,82.9) if args.candidate=='d' and col==0 else (43,78),ylim=(50.6,1.3) if args.candidate=='d' and col==0 else (31,13),aspect='equal',title=f'{"Supply return / blue rings = data transitions" if col==0 else "Protection ground paths"} — layer {layer}')
  ax.legend(fontsize=8,loc='lower left');ax.grid(alpha=.1)
fig.suptitle(f'{args.candidate.upper()} actual copper — geometric GND connections, NOT current simulation',fontsize=14)
fig.text(.5,.02,'Orange = forward VBUS copper. Colored paths = one grid path through GND; white circles = layer changes. Dotted blue = distance guide, not a trace. USB differential current is not all GND current.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,.95));fig.savefig(f'{STEM}-return-paths.png',dpi=170)
record={'method':f'{step:.2f} mm grid in actual GND copper with {erosion:.3f} mm edge erosion; plated layer changes cost 0.8 mm. Conceptual center nodes at plated holes. One available geometric path, NOT field/current/impedance or IEC ESD simulation.','paths':paths}
Path(f'{STEM}-return-paths.json').write_text(json.dumps(record,indent=2)+'\n')
print([(p['label'],round(p['grid_geometric_length_mm'],2)) for p in paths])
