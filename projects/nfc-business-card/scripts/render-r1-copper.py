#!/usr/bin/env python3
"""Render the actual routed PCB copper on both faces, including pour exclusions."""
import argparse
import json
import runpy
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch, Circle
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from pour_geometry import parse_path, load_pours

pad_shape=runpy.run_path(str(Path(__file__).with_name('check-r1-copper.py')))['pad_shape']
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--title',default='NFC Card R1 | Routed PCB');a=ap.parse_args()
s=json.loads(a.snapshot.read_text());outline=parse_path(next(p for p in s['polylines']if p['layer']==11)['polygon']['polygon'],.0254)
fig,axes=plt.subplots(1,2,figsize=(16,6.5));fig.patch.set_facecolor('#edf2f6')
for ax,layer,title in zip(axes,(1,2),('FRONT / components + controls','REAR / NFC + debug pads')):
 ax.set_aspect('equal');ax.set_xlim(-1,85);ax.set_ylim(-2,54);ax.set_facecolor('#edf2f6');ax.axis('off');ax.set_title(title,fontsize=15,weight='bold',loc='left',pad=15)
 ax.add_patch(Patch(outline,facecolor='#203949',edgecolor='#50677a',linewidth=1))
 pour=load_pours(s).get(layer)
 if pour:
  for r in pour.regions:
   poly=orient(Polygon(r.outer,r.holes),sign=1);verts=[];codes=[]
   for ring in [poly.exterior,*poly.interiors]:
    pts=list(ring.coords);verts.extend(pts);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(pts)-2)+[MPath.CLOSEPOLY])
   ax.add_patch(PathPatch(MPath(verts,codes),facecolor='#3e6671',edgecolor='none',alpha=.75))
 for t in s['lines']:
  if t['layer']!=layer:continue
  color='#ddab64' if t['net']=='NFC1_TBD' else ('#79a595' if t['net']=='GND'else '#9abbcf')
  ax.plot([t['x1']*.0254,t['x2']*.0254],[t['y1']*.0254,t['y2']*.0254],color=color,linewidth=t['widthMil']*.0254*4,solid_capstyle='round')
 for p in s['pads']:
  if p['layer']not in (layer,12):continue
  g=pad_shape(p);ax.add_patch(Patch(list(g.exterior.coords),facecolor='#dab66c',edgecolor='none'))
 for v in s['vias']:
  x,y=v['x']*.0254,v['y']*.0254;ax.add_patch(Circle((x,y),v['diameterMil']*.0254/2,facecolor='#b1b5a2'));ax.add_patch(Circle((x,y),v['holeMil']*.0254/2,facecolor='#182c38'))
 if layer==1:
  for c in s['components']:
   x,y=c['x']*.0254,c['y']*.0254
   ax.text(x,y,c['ref'],color='white',ha='center',va='center',fontsize=5.8)
  ax.plot([2,39.32,39.32,2,2],[18.3,18.3,50.1,50.1,18.3],color='#aac1ce',linestyle='--',linewidth=.7)
  ax.text(20,34,'Screen footprint\nNo pours; battery lands at lower edge',ha='center',va='center',fontsize=10,color='#e6eef5')
 else:
  ax.text(19,32,'NFC',ha='center',va='center',fontsize=18,color='#dfbd87')
  for x,label in [(65,'GND'),(68,'3V3'),(71,'CLK'),(74,'DIO'),(77,'RST')]:
   ax.text(x,46.8,label,ha='center',fontsize=7,color='white')
  ax.invert_xaxis()
fig.suptitle(a.title,fontsize=21,weight='bold',x=.04,ha='left')
fig.text(.04,.065,'Actual exported copper. Front reference labels and the dashed screen outline are review overlays.',fontsize=10,color='#42576c')
fig.text(.04,.03,'2 copper layers / 0.8 mm PCB / rear 5-turn NFC coil. RF tuning and physical assembly remain prototype tests.',fontsize=10,color='#42576c')
fig.subplots_adjust(left=.035,right=.985,top=.86,bottom=.15,wspace=.06);a.output.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(a.output,dpi=180,facecolor=fig.get_facecolor());fig.savefig(a.output.with_suffix('.svg'),facecolor=fig.get_facecolor())
