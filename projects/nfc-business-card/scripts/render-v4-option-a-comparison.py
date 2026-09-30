#!/usr/bin/env python3
"""Render actual filled-ground failure before and after the sampling ablation."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch, Rectangle
from shapely.ops import unary_union
from v4_geometry import geometry, filled_ground

project=Path(__file__).resolve().parents[1]
records=project/'hardware/records/kicad-v4-option-a'
boards=[('hardware/kicad/v4-option-a','controls-power-audit','Local control / battery witness'),
        ('hardware/kicad/v4-option-a-integration-rejected','joint-seeded-audit','Combined routing - rejected'),
        ('artifacts/kicad-v4-option-a/sampling-ablation','sampling-ablation-audit','ADC geometry ablation - not adopted')]
fig,axes=plt.subplots(1,3,figsize=(18,6))
for ax,(directory,audit_name,title) in zip(axes,boards):
    board,pads,objects,refs=geometry(project/directory/'NFC-Card-V4.kicad_pcb')
    audit=json.loads((records/audit_name/'audit.json').read_text())
    missing=[pads[n] for n,reaches in audit['ground_pad_to_U2_EP'].items() if not reaches]
    copper=unary_union([filled_ground(board,'F.Cu'),*[o['shape'] for o in objects if o['net']=='GND' and 'F.Cu' in o['layers']]])
    pieces=list(copper.geoms) if copper.geom_type=='MultiPolygon' else [copper]
    for polygon in pieces:
        bad=any(polygon.distance(p['shape'])<.002 for p in missing)
        ax.add_patch(Patch(list(polygon.exterior.coords),color='#e68b24' if bad else '#deebdf',lw=0,zorder=1))
        for hole in polygon.interiors:
            ax.add_patch(Patch(list(hole.coords),color='white',lw=0,zorder=2))
    for o in objects:
        if 'F.Cu' not in o['layers'] or o['kind']=='keepout' or o['net']=='GND':continue
        color='#b64034' if o['kind']=='track' else '#555e68'
        shapes=list(o['shape'].geoms) if o['shape'].geom_type=='MultiPolygon' else [o['shape']]
        for p in shapes:
            ax.add_patch(Patch(list(p.exterior.coords),color=color,lw=0,zorder=3))
    for ref in ['U1','U2','U3','C3','C4','C5','C8','Q2','Q3','R20','R21','R22','R23','C25']:
        if ref in refs:
            x,y,_=refs[ref];ax.text(x,y,ref,fontsize=7,ha='center',va='center',bbox=dict(facecolor='white',alpha=.8,pad=.4,edgecolor='none'),zorder=5)
    for p in missing:
        x,y=p['at'];ax.plot(x,y,'o',ms=9,mfc='none',mec='#c82333',mew=1.7,zorder=6)
    ax.add_patch(Rectangle((182.1,110.405),9.605433,10.89,fill=False,edgecolor='#775b12',linestyle='--',linewidth=1.1,zorder=6))
    ax.set(xlim=(165,193),ylim=(122,100),aspect='equal',xlabel='KiCad X / mm',ylabel='KiCad Y / mm')
    ax.set_title(title+'\nF.Cu, viewed from top',fontsize=11)
    ax.grid(alpha=.15)
fig.suptitle('Orange: actual copper isolated from U2 EP   |   Red circles: failed GND pads   |   Dashed box: ADC envelope',fontsize=12)
fig.tight_layout()
fig.savefig(records/'return-ablation-comparison.png',dpi=180,bbox_inches='tight')
