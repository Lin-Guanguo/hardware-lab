#!/usr/bin/env python3
"""Plot actual A4 copper and independently identified conflicts."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from v4_geometry import geometry,filled_ground

p=Path(__file__).resolve().parents[1];r=p/'hardware/records/kicad-v4-option-a4'
b,pads,objects,refs=geometry(p/'hardware/kicad/v4-option-a4-joint/NFC-Card-V4.kicad_pcb')
colors={'EPD_MOSI_TBD':'#2276b6','EPD_SCK_TBD':'#e76c16','EPD_CS_N_TBD':'#20934d','EPD_DC_TBD':'#a945b4','EPD_RESET_N_TBD':'#85522d','EPD_BUSY_TBD':'#e43163','USB_VBUS':'#db342b','USB_DP_CONN':'#2166bf','USB_DM_CONN':'#7d39a2','GND':'#577659','VDD_3V3':'#e09513','SYS':'#c68a30'}
fig=plt.figure(figsize=(15,11),constrained_layout=True);gs=fig.add_gridspec(2,2,width_ratios=[1,1.5]);axs=[fig.add_subplot(gs[:,0]),fig.add_subplot(gs[0,1]),fig.add_subplot(gs[1,1])]
def draw(ax,layer,lim,nets,title):
 ground=filled_ground(b,layer)
 for g in getattr(ground,'geoms',[ground]):
  if g.is_empty:continue
  ax.add_patch(Patch(g.exterior.coords,facecolor='#e2eae0',edgecolor='none'))
  for ring in g.interiors:ax.add_patch(Patch(ring.coords,facecolor='white',edgecolor='none'))
 for x in objects:
  if layer not in x['layers']:continue
  highlight=x['net'] in nets
  col=colors.get(x['net'],'#777777') if highlight else '#b6b6b6'
  ax.add_patch(Patch(x['shape'].exterior.coords,facecolor=col,edgecolor='none',alpha=1 if highlight else .35))
 x0,y0,x1,y1=lim;ax.set(xlim=(x0,x1),ylim=(y1,y0),aspect='equal',title=title,xlabel='x / mm',ylabel='y / mm');ax.grid(alpha=.18)
series=list(colors)[:6]
draw(axs[0],'B.Cu',(165.5,93,178.5,117),set(series),'A4 screen bundle / B.Cu / REJECTED')
for n in series:axs[0].plot([],[],color=colors[n],lw=3,label=n.replace('EPD_','').replace('_TBD',''))
axs[0].legend(loc='lower left',fontsize=8,framealpha=.9)
axs[0].plot(172.201,98.791,'o',ms=11,mfc='none',mec='black',mew=2)
axs[0].annotate('MOSI x SCK\n(172.201, 98.791)',(172.201,98.791),(174,95.5),fontsize=9,arrowprops={'arrowstyle':'->'},bbox={'fc':'white','alpha':.95})
for n,pin in [('MOSI',26),('SCK',24),('CS',22),('DC',20),('RESET',19),('BUSY',16)]:
 x,y=pads['U1.'+str(pin)]['at'];axs[0].text(x,116.7 if pin!=19 else 116.6,str(pin),ha='center',va='bottom',fontsize=8)
axs[0].text(171.8,116.95,'Module pin numbers (F.Cu pads)',fontsize=8,ha='center',va='top')
draw(axs[1],'F.Cu',(163,101,185,114.6),{'USB_VBUS','USB_DP_CONN','USB_DM_CONN','SYS','VDD_3V3'},'USB / supply crossover / F.Cu / REJECTED')
for ref in ['U3','C4','C5','C1','C6','C7','R3','R4','U5','U6','R1','R2']:
 x,y,_=refs[ref];axs[1].text(x,y,ref,ha='center',fontsize=9,bbox={'fc':'white','alpha':.8,'ec':'none','pad':.5})
axs[1].text(163.5,113.9,'Blue: D+   Purple: D-   Red: VBUS   Amber: 3V3 / SYS',fontsize=9,bbox={'fc':'white','alpha':.9})
draw(axs[2],'F.Cu',(181.4,106.3,186,110.7),{'USB_VBUS','GND','USB_DM_CONN'},'U6 local ground regression / F.Cu')
for pin in ['U6.1','U6.2','U6.3']:
 x,y=pads[pin]['at'];axs[2].text(x+.2,y-.13,pin,fontsize=10,bbox={'fc':'white','alpha':.85,'ec':'none'})
axs[2].annotate('VBUS crosses GND pad;\nU6.3 has no GND fill connection',pads['U6.3']['at'],(181.65,110.0),fontsize=10,arrowprops={'arrowstyle':'->'},bbox={'fc':'white','alpha':.95})
fig.suptitle('A4: incompatible copper in one saved candidate — no manufacturability claim',fontsize=15)
fig.savefig(r/'conflict-witnesses.png',dpi=170)
