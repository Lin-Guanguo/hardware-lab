"""Draw nominal central sections of the flat and relieved flange candidates."""
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle
from shapely.geometry import box
from shapely.ops import unary_union

out=Path(os.environ['NFC_KEY_RETENTION_OUT'])
fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
for ax,thick,title in zip(axes,[False,True],['A | Flat flange: 0.40 mm','B | Relieved flange: 0.80 mm outer lobes']):
    shapes=[box(-3.4,3.55,3.4,3.95),box(-2,3.55,2,4.77),box(-1.3,3.32,1.3,3.55)]
    if thick:
        shapes += [box(-3.4,3.15,-2.8,3.55),box(2.8,3.15,3.4,3.55)]
    cap=unary_union(shapes)
    ax.add_patch(Polygon(list(cap.exterior.coords),facecolor='#94c8df',edgecolor='#29607b',lw=1.6))
    for a,b in [(-4.5,-2.6),(2.6,4.5)]:
        ax.add_patch(Rectangle((a,4),b-a,.8,facecolor='#d8dcdf',edgecolor='#777f85'))
    for a,b in [(-2.6,-1.4),(1.4,2.6)]:
        ax.add_patch(Rectangle((a,1.72),b-a,1.25,facecolor='#777f85'))
    ax.add_patch(Rectangle((-4.5,.92),9,.8,facecolor='#b6d5bc',edgecolor='#608368'))
    ax.annotate('4.00 mm head',xy=(0,4.77),xytext=(0,5.3),ha='center',arrowprops={'arrowstyle':'->'})
    ax.annotate('0.40 mm roof',xy=(-2.3,3.75),xytext=(-4.4,5.8),ha='left',fontsize=10,
                arrowprops={'arrowstyle':'->','connectionstyle':'angle,angleA=-90,angleB=180,rad=5'})
    if thick:
        ax.annotate('0.80 mm axial height\n0.60 mm radial width',xy=(3.1,3.5),xytext=(4.4,2.25),ha='right',fontsize=10,
                    arrowprops={'arrowstyle':'->'})
    ax.text(0,.35,'6.80 mm flange | 5.20 mm guide hole',ha='center',fontsize=10)
    ax.set_title(title,loc='left',fontsize=12,weight='bold')
    ax.set_xlim(-4.7,4.7);ax.set_ylim(.2,6.2);ax.set_aspect('equal')
    ax.set_xlabel('Offset from key centre / mm')
    ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Height above outside rear face / mm')
fig.suptitle('Key retention | Same 4.8 mm enclosure',x=.07,ha='left',fontsize=17,weight='bold')
fig.text(.07,.045,'Nominal centre section at rest. Fillets and moving switch actuator omitted.\nBlue: printed key. Light grey: shell. Dark grey: fixed switch body. Green: PCB. Not a strength qualification.',fontsize=10,color='#485a67')
fig.subplots_adjust(left=.07,right=.98,top=.85,bottom=.20,wspace=.16)
fig.savefig(out/'flange-section.png',dpi=170)
