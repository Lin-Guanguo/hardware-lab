#!/usr/bin/env python3
"""Jointly check supply, return, USB fanout and the complete charger-control bundle."""
import json
from pathlib import Path
from shapely.geometry import LineString, Point
from v4_geometry import geometry

root=Path(__file__).resolve().parents[3]
directory=root/'projects/nfc-business-card/hardware/kicad/v4-option-a2-expanded-rejected'
_,pads,objects,_=geometry(directory/'NFC-Card-V4.kicad_pcb')
plan=json.loads((directory/'power-plan.json').read_text())
routes=plan['routes']+json.loads((directory/'display-power-plan.json').read_text())['routes']
vias=plan['vias']


def trace(name,net,layer,points,width=.15):
    points=[pads[x]['at'] if isinstance(x,str) else x for x in points]
    routes.append(dict(name=name,net=net,layer=layer,points=points,width=width))


def via(net,*points):
    vias.extend(dict(net=net,at=p) for p in points)


trace('USB DP paired connector contacts','USB_DP_CONN','F.Cu',['J1.B6',(185.4,103.2505),(184.8495,102.7),(183.8,102.7),(183.8,104.2505),'J1.A6'])
trace('USB DP through protector','USB_DP_CONN','F.Cu',[(183.8,102.7),(183.2,103.3),(183.2,104.85),'U5.1'])
trace('USB DM first contact','USB_DM_CONN','F.Cu',['J1.A7',(185.0005,103.7505),(184.8,103.55)])
trace('USB DM second contact','USB_DM_CONN','F.Cu',['J1.B7',(185.0995,104.7505),(184.8,105.05)])
trace('USB DM local layer bridge','USB_DM_CONN','B.Cu',[(184.8,103.55),(184.8,105.05),(184.05,105.8),(183,105.8)])
trace('USB DM through protector','USB_DM_CONN','F.Cu',[(183,105.8),(182.55,106.25),'U5.2'])
via('USB_DM_CONN',(184.8,103.55),(184.8,105.05),(183,105.8))
trace('USB VBUS upper contact','USB_VBUS','F.Cu',['J1.B4A9',(185.2,101.6005),(185.2,100.6)],.35)
trace('USB VBUS lower contact','USB_VBUS','F.Cu',['J1.A4B9',(185,106.4005),(185,106.4)],.35)
trace('USB VBUS connector bridge','USB_VBUS','B.Cu',[(185.2,100.6),(185.6,101),(185.6,105.8),(185,106.4),(182.7,108.7),(181.2,108.7)],.35)
trace('USB VBUS charger inlet','USB_VBUS','F.Cu',[(181.2,108.7),'C8.1'],.35)
trace('USB VBUS MCU bridge','USB_VBUS','B.Cu',[(181.2,108.7),(179,110.9),(176.2,110.9),(175.9,111.2),(168.2,111.2),(168.1,111.1)],.35)
trace('USB VBUS MCU bypass inlet','USB_VBUS','F.Cu',[(168.1,111.1),(167.6,111.6),'C1.1'],.35)
via('USB_VBUS',(185.2,100.6),(185,106.4),(181.2,108.7),(168.1,111.1))
trace('USB protector local return','GND','F.Cu',['U5.3',(183.5,104.9)],.25)
trace('CC protector local return','GND','F.Cu',['U6.3',(182.8,108.4),(182.5,108.1),(182.5,107.7)],.25)
trace('Load switch local return','GND','F.Cu',['U4.2',(179.2,96.4)],.25)
via('GND',(183.5,104.9),(182.5,107.7),(179.2,96.4))

trace('SCL local main','CHG_SCL','F.Cu',[(177.001,109.05),'U1.16'])
trace('SCL pullup bridge','CHG_SCL','B.Cu',[(177.001,112.2),(178.6,113.799),(178.6,116)])
trace('SCL pullup contact','CHG_SCL','F.Cu',[(178.6,116),'R6.2'])
via('CHG_SCL',(177.001,112.2),(178.6,116))
trace('SDA main escape','CHG_SDA','F.Cu',['U2.7',(176.6,112.2),(175.7,113.1)])
trace('SDA inner row bridge','CHG_SDA','B.Cu',[(175.7,113.1),(175.7,115.401),(175.001,116.1)])
trace('SDA inner pad','CHG_SDA','F.Cu',[(175.001,116.1),'U1.19'])
trace('SDA pullup contact','CHG_SDA','F.Cu',['U1.19',(179.1125,114.834),'R5.2'])
via('CHG_SDA',(175.7,113.1),(175.001,116.1))
trace('INT charger escape','CHG_INT_N','F.Cu',['U2.9',(177.4,109.7),(178.1,110.4)])
trace('INT over SCL SDA','CHG_INT_N','B.Cu',[(178.1,110.4),(174.8,110.4),(174.6,110.6)])
trace('INT MCU contact','CHG_INT_N','F.Cu',[(174.601,110.6),'U1.20'])
trace('INT pullup branch','CHG_INT_N','B.Cu',[(178.1,110.4),(179.7,112),(179.7,116.6),(178.6,117.7)])
trace('INT pullup contact','CHG_INT_N','F.Cu',[(178.6,117.7),'R8.2'])
via('CHG_INT_N',(178.1,110.4),(174.6,110.6),(178.6,117.7))
trace('PG north escape','CHG_PG_N','F.Cu',['U2.3',(177,106.15),(176.05,106.15),(175.4,105.5)])
trace('PG over ground spine','CHG_PG_N','B.Cu',[(175.4,105.5),(175.4,108.1)])
trace('PG MCU approach','CHG_PG_N','F.Cu',[(175.4,108.1),(175.4,112.2),(175.3,112.3)])
trace('PG inner row bridge','CHG_PG_N','B.Cu',[(175.3,112.3),(175.3,115.201),(174.201,116.3)])
trace('PG inner pad','CHG_PG_N','F.Cu',[(174.201,116.3),'U1.21'])
trace('PG pullup branch','CHG_PG_N','B.Cu',[(174.201,116.3),(174.201,118.8),(178,118.8),(178.6,119.4)])
trace('PG pullup contact','CHG_PG_N','F.Cu',[(178.6,119.4),'R9.2'])
via('CHG_PG_N',(175.4,105.5),(175.4,108.1),(175.3,112.3),(174.201,116.3),(178.6,119.4))
trace('CE north escape','CHG_CE_N','F.Cu',['U2.4',(176.6,106.6),(175.05,106.6),(174.9,106.45)])
trace('CE over ground spine','CHG_CE_N','B.Cu',[(174.9,106.45),(174.9,108.1)])
trace('CE MCU approach','CHG_CE_N','F.Cu',[(174.9,108.1),(173.801,109.199),'U1.22'])
trace('CE pullup bridge','CHG_CE_N','B.Cu',[(174.9,108.1),(176.1,109.3),(178.7,109.3),(180.2,110.8),(180.2,111.4)])
trace('CE pullup contact','CHG_CE_N','F.Cu',[(180.2,111.4),(179.6465,111.9535),'R7.2'])
via('CHG_CE_N',(174.9,106.45),(174.9,108.1),(180.2,111.4))

for pad, point in [('U1.36',(170.9,116.134)),('U1.38',(170.7,116.934)),('U1.40',(171.5,117.734)),('U1.27',(171.801,116.2))]:
    net=pads[pad]['net']
    trace(pad+' inward escape',net,'F.Cu',[pad,point])
    via(net,point)

generated=[dict(name=r['name'],net=r['net'],layers=[r['layer']],shape=LineString(r['points']).buffer(r['width']/2),kind='track') for r in routes]
generated += [dict(name=v['net']+' via '+str(v['at']),net=v['net'],layers=['F.Cu','B.Cu'],shape=Point(v['at']).buffer(.3),kind='via',at=v['at']) for v in vias]
failures=[]
for r in routes:
    for p,q in zip(r['points'],r['points'][1:]):
        dx,dy=abs(q[0]-p[0]),abs(q[1]-p[1])
        assert min(dx,dy,abs(dx-dy))<1e-5,(r['name'],p,q)
for i,o in enumerate(generated):
    for other in objects+generated[:i]:
        if o['net']!=other['net'] and set(o['layers'])&set(other['layers']):
            gap=o['shape'].distance(other['shape'])
            if gap<.2-1e-5:failures.append(dict(a=o['name'],b=other['name'],gap_mm=round(gap,6)))
    if o['kind']=='via':
        for p in pads.values():
            gap=Point(o['at']).distance(p['shape'])
            if len(p['layers'])==1 and gap<.55-1e-5:failures.append(dict(a=o['name'],b=p['name'],smd_to_drill_gap_mm=round(gap-.15,6)))
plan.update(routes=routes,vias=vias,failures=failures,description='A2 jointly constructed power, ground returns, charger controls, USB fanout and MCU inner exits',record='projects/nfc-business-card/hardware/records/kicad-v4-option-a2/critical-ipc.json')
(directory/'critical-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(routes=len(routes),vias=len(vias),failures=failures),indent=2))
