#!/usr/bin/env python3
"""Draw reported battery sizes against the existing E20B mechanical layout."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'hardware/records'
report=json.loads((REC/'e20b-battery-space-study.json').read_text())
bounds=json.loads((REC/'e20b-body-bounds.json').read_text())
fig=plt.figure(figsize=(17,8.6),facecolor='#f5f7fa')
fig.text(.045,.93,'E20B | battery space before changing the buttons',fontsize=23,weight='bold',color='#17334d')
fig.text(.045,.887,'Reported sizes are not measured complete-pack dimensions. All three views use the same existing PCB and case.',fontsize=11,color='#526477')
labels=['24 x 14 x 3 mm','31 x 12 x 3 mm','32 x 20 x 3 mm']
for i,option in enumerate(report['battery_options']):
    ax=fig.add_axes([.045+i*.323,.445,.293,.36]);ax.set_aspect('equal');ax.set_xlim(-.5,57);ax.set_ylim(27,-.8)
    ax.add_patch(Rectangle((-.6,-.6),58.2,28.2,facecolor='#e1e8ec',edgecolor='#91a4af'))
    ax.add_patch(Rectangle((.6,.6),56.4,26.4,facecolor='#fafbfc',edgecolor='#9baeb8'))
    ax.add_patch(Polygon([(36,1.1),(57,1.1),(57,27),(1.1,27),(1.1,17.8),(1.6,17.3),(35,17.3),(35.5,16.8),(35.5,1.6)],facecolor='#dcebe2',edgecolor='#477659',lw=1.2))
    ax.plot([2,39.32,39.32],[18.3,18.3,27],color='#6490c1',ls='--',lw=1.2)
    ax.text(4,25.7,'SCREEN / PCB AREA',color='#5c82a7',fontsize=7.3)
    for ref,b in bounds.items():
        lo,hi=b['min_mm'],b['max_mm']
        if lo[0]>57 or lo[1]>26:continue
        color='#526c85' if ref.startswith('SW') else '#9aacb7'
        ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor=color,edgecolor='#6a7c8e',lw=.4))
        if ref.startswith('SW'):ax.text((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,ref,ha='center',va='center',fontsize=8,color='white')
    length,width,height=option['nominal_lwh_mm']
    ax.add_patch(Rectangle((1.5,1.5),length,width,facecolor='#dbca94',edgecolor='#a17f39',alpha=.82,lw=1.3))
    ax.text(1.5+length/2,1.5+width/2,labels[i],ha='center',va='center',fontsize=10,color='#684f24')
    if i==2:
        ax.add_patch(Rectangle((1.5,17.3),length,4.2,facecolor='#d56666',alpha=.55,hatch='///'))
        ax.text(17.5,19.6,'4.2 mm INTO PCB',ha='center',fontsize=8,color='#8b2635',weight='bold')
    else:
        end=1.5+length
        ax.annotate('',xy=(35.5,8),xytext=(end,8),arrowprops={'arrowstyle':'<->','color':'#2b8290','lw':1.4})
        ax.text((35.5+end)/2,6.2,f'{35.5-end:.1f}',ha='center',fontsize=9,color='#2b8290')
    ax.set_title(['New shorter pack','New longer pack','Previous wider pack'][i],loc='left',pad=14,fontsize=14,weight='bold',color='#17334d');ax.axis('off')
    x=.05+i*.323
    if i<2:
        fig.text(x,.425,f"Length remainder: {option['total_length_remainder_mm']:.1f} mm total",fontsize=11,color='#17334d')
        fig.text(x,.39,f"Width remainder: {option['total_width_remainder_mm']:.1f} mm total",fontsize=11,color='#17334d')
        fig.text(x,.35,'Nominal body fits; leads / protection unverified.',fontsize=9,color='#617387')
    else:
        fig.text(x,.425,'Does not fit the existing PCB cutout.',fontsize=11,color='#963e4c')
        fig.text(x,.39,'Only 0.04 mm below max screen envelope*',fontsize=10,color='#963e4c')
        fig.text(x,.35,'Needs a wider cutout and a new height budget.',fontsize=9,color='#617387')
fig.text(.05,.275,'BUTTON OPTIONS  /  dimensional studies only',fontsize=13,weight='bold',color='#17334d')
texts=[('Keep current 3 keys','34.9 mm length span','31 mm pack: 3.9 mm total remainder'),('Shift 3 keys right by 1 mm','35.9 mm proposed length span','31 mm pack: 4.9 mm total remainder'),('Use 2 keys; expand cutout by 4 mm','38.9 mm proposed length span','31 mm pack: 7.9 mm total remainder')]
for i,rows in enumerate(texts):
    x=.05+i*.323
    fig.text(x,.228,rows[0],fontsize=10.5,weight='bold',color='#17334d')
    fig.text(x,.192,rows[1],fontsize=10,color='#526477')
    fig.text(x,.158,rows[2],fontsize=9.5,color='#526477')
fig.text(.05,.09,'Remainders combine both sides, before tolerance and wire allowances. They are not guaranteed assembly clearances.',fontsize=10,color='#617387')
fig.text(.05,.055,'*3.00 mm battery, 0.10 mm adhesive, 0.80 mm floor; PCB interference already prevents this assembly. Profiles simplified.',fontsize=9,color='#617387')
for ext in ['png','svg']:fig.savefig(ROOT/f'enclosure/renders/e20b-battery-space.{ext}',dpi=160)
