#!/usr/bin/env python3
"""Render native front placement and a clearly labelled rear antenna study."""
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'hardware/records'
s=json.loads((REC/'e20d-placement-snapshot.json').read_text())
bounds=json.loads((REC/'e20d-body-bounds.json').read_text())
plan=json.loads((ROOT/'hardware/e20d-placement.json').read_text())
labels=json.loads((REC/'e20d-designators.json').read_text())
raw=next(p['polygon']['polygon'] for p in s['polylines'] if p['layer']==11)
points=[];i=0
while i<len(raw):
    if raw[i]=='ARC':i+=2
    elif raw[i]=='L':i+=1
    points.append((raw[i]*.0254,raw[i+1]*.0254));i+=2
fig=plt.figure(figsize=(18,10),facecolor='#f5f7fa')
fig.text(.045,.94,'E20D | front controls, rear NFC',fontsize=25,weight='bold',color='#17334d')
fig.text(.045,.9,'Native placement candidate: three keys +1 mm, USB centred, display power components moved to the right.',fontsize=11,color='#526477')
for side in range(2):
    ax=fig.add_axes([.045+side*.48,.29,.445,.56]);ax.set_aspect('equal');ax.set_ylim(-1,53)
    ax.set_xlim((-1,85) if side==0 else (85,-1))
    ax.add_patch(Rectangle((-.6,-.6),85.2,53.2,facecolor='#e4edf0',edgecolor='#8ba3b0',lw=1.2))
    ax.add_patch(Polygon(points,facecolor='#ddebe3',edgecolor='#48765a',lw=1.4))
    ax.add_patch(Rectangle((1.5,1.5),31,12,facecolor='#d8c99d',edgecolor='#ad9252'))
    ax.text(17,7.5,'31 x 12 x 3 mm\nnominal battery',ha='center',va='center',fontsize=10,color='#725a30')
    ax.plot([76,85],[26,26],ls=':',lw=1,color='#9b638c')
    if side==0:
        ax.add_patch(Rectangle((2,18.3),37.32,31.8,facecolor='#d8e2ea',edgecolor='#5a7c99',lw=1.3))
        ax.add_patch(Rectangle((4.4,20.7),27,27,facecolor='#eef2f5',edgecolor='#89a0b5',lw=.8))
        ax.text(17.9,33.5,'DISPLAY\nno components\nbeneath it',ha='center',va='center',fontsize=12,color='#526f8e',linespacing=1.5)
        ax.add_patch(Rectangle((39.32,28.01),13.955,12.5,facecolor='#d4a05b',edgecolor='#af8144',alpha=.65))
        ax.text(43.6,34.26,'FPC',ha='center',va='center',fontsize=8,color='#886631')
        ax.add_patch(Rectangle((72.5,5.5),9,13,fill=False,edgecolor='#9b91ac',lw=1,ls='--'))
        ax.text(77,12,'SPARE\n9 x 13',ha='center',va='center',fontsize=8,color='#887995')
        ax.add_patch(Rectangle((56.5,0),13,4.96,facecolor='#eed3dc',edgecolor='#b16c85',alpha=.5))
        for p in s['pads']:
            if p['layer']!=1:continue
            w,h=p['pad'][1]*.0254,p['pad'][2]*.0254;a=math.radians(p['rotation'])
            xy=[(p['x']*.0254+dx*math.cos(a)-dy*math.sin(a),p['y']*.0254+dx*math.sin(a)+dy*math.cos(a)) for dx,dy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
            ax.add_patch(Polygon(xy,facecolor='#a9b9bf',edgecolor='none'))
        for ref,b in bounds.items():
            lo,hi=b['min_mm'],b['max_mm'];x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
            color='#566d86' if ref.startswith('SW') or ref=='U1' else '#b69555' if ref in plan['components_mm'] and ref not in ['J1','U5','U6','R1','R2','C23','C24'] else '#658c9f'
            ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor=color,edgecolor='#53697b',lw=.45))
            if ref in ['U1','J1','J2'] or ref.startswith('SW'):ax.text(x,y,ref,ha='center',va='center',fontsize=8,color='white')
            elif ref in labels:
                a=labels[ref]
                ax.text(a['x']*.0254,a['y']*.0254,ref,ha='left' if a['alignMode']==2 else 'center',va='center',fontsize=6,color='#40556c')
            elif ref in ['U4','L1','Q1']:
                ax.text(x,y,ref,ha='center',va='center',fontsize=5.8,color='white')
        ax.text(67,48.8,'DISPLAY POWER',ha='center',fontsize=8,color='#997332')
    else:
        ax.add_patch(Rectangle((3,19),32,26,facecolor='#dbebe4',edgecolor='#448d7d',ls='--',lw=1.2))
        # This continuous path illustrates the reservation; it is not native PCB copper.
        path=[(4,20)]
        for n in range(5):
            left,top,right,bottom=4+n*.5,20+n*.5,34-n*.5,44-n*.5
            path.extend([(right,top),(right,bottom),(left,bottom),(left,top+.5)])
        ax.plot([p[0] for p in path],[p[1] for p in path],color='#ae8441',lw=1.8)
        ax.text(19,31.5,'REAR NFC\n30 x 24 mm\nplanned geometry',ha='center',va='center',fontsize=12,color='#387669',linespacing=1.5)
        for p in s['pads']:
            if p['layer']!=2:continue
            w,h=p['pad'][1]*.0254,p['pad'][2]*.0254
            ax.add_patch(Rectangle((p['x']*.0254-w/2,p['y']*.0254-h/2),w,h,facecolor='#b29659',edgecolor='#8d7648',lw=.5))
        ax.text(10,49,'SWD retained',ha='center',fontsize=8,color='#657c8d')
        b=bounds['J1'];lo,hi=b['min_mm'],b['max_mm']
        ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor='#8795a7',edgecolor='#53697b',lw=.8))
        ax.text(79.5,26,'USB',ha='center',va='center',fontsize=8,color='white',rotation=90)
        ax.text(60,12,'Front-side parts hidden\nby the opaque PCB',ha='center',va='center',fontsize=10,color='#768b91')
    ax.set_title(['FRONT  /  display + three keys + visible circuits','REAR  /  tap this face against the phone'][side],loc='left',pad=14,fontsize=13,weight='bold',color='#17334d');ax.axis('off')
notes=[('Battery room','35.9 mm length span\n31 mm nominal pack: 4.9 mm total remainder'),('Centred USB','Socket centre at Y = 26.0 mm\nBoard slot, case opening and supports follow'),('Clear screen cavity','15 display-power parts moved to the right\n2.02 mm from PCB top to max screen back'),('RF remains a prototype','Both-layer copper exclusion is reserved\nScreen loading / ferrite / tuning need tests')]
for i,(title,body) in enumerate(notes):
    x=.05+i*.24;fig.text(x,.23,title,fontsize=12,weight='bold',color='#17334d');fig.text(x,.198,body,fontsize=9.5,color='#526477',va='top',linespacing=1.5)
fig.text(.05,.10,'Views use CAD +Y up; rear is mirrored. Coil and flex shapes illustrate reservations; coil copper and the final flex bend are not modelled.',fontsize=10,color='#526477')
fig.text(.05,.065,'58 components / 248 pads / 0 tracks / 0 vias. Candidate only; transparent casing does not guarantee a visible copper finish through solder mask.',fontsize=9.5,color='#617387')
for ext in ['png','svg']:fig.savefig(ROOT/f'enclosure/renders/e20d-front-rear.{ext}',dpi=160)
