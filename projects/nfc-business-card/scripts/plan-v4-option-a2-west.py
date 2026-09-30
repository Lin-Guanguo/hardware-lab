#!/usr/bin/env python3
"""Jointly validate the west regulator alternative against real USB and control copper."""
import json
from pathlib import Path
from shapely.geometry import LineString,Point
from v4_geometry import geometry

root=Path(__file__).resolve().parents[3]
p=root/'projects/nfc-business-card/hardware/kicad/v4-option-a2-west'
b,pads,objects,refs=geometry(p/'NFC-Card-V4.kicad_pcb')
plan=json.loads((p/'usb-controls-plan.json').read_text())
rs,vs=plan['routes'],plan['vias']
display=json.loads((p.parent/'v4-option-a2/display-power-plan.json').read_text())
rs.extend(r for r in display['routes'] if r['name']!='VBUS at U1')


def t(name,net,pts,w=.25,l='F.Cu'):
    rs.append(dict(name=name,net=net,layer=l,width=w,points=[pads[x]['at'] if isinstance(x,str) else x for x in pts]))


def v(net,*pts):
    vs.extend(dict(net=net,at=x) for x in pts)


# This inherited outer supply path remains explicit, including its width cost.
t('SYS outer group feed','SYS',['C2.1',(179.2,105),(179.2,103.9),(176.9863,101.6863),(173.819,101.6863),(173.5368,101.9685),(173.5368,105.5621),(173.3817,105.7172),(174.5,105.7172),(174.5,107.5),'C4.1'],.15)
t('SYS LDO local inlet','SYS',['C4.1',(174.7,108.2),(174.25,108.65),'U3.1'],.35)
t('SYS LDO enable','SYS',['U3.1',(172.6,108.65),(172.6,106.75),'U3.3'],.15)
t('LDO output bypass','VDD_3V3',['U3.5','C5.1'],.35)
t('LDO MCU branch','VDD_3V3',['U3.5',(169.75,108.9),(169.75,111.35),'C7.1','C6.1'],.35)
t('MCU VDD pad28','VDD_3V3',['C6.1',(171.401,112.899),'U1.28'],.2)
t('MCU VDD pad30','VDD_3V3',[(170.601,112.2),'U1.30'],.2)
t('Display supply departure','VDD_3V3',['C5.1',(168,107.4),(168,102),(167.6,101.6),(167.6,101.4)],.35)
t('Display supply bridge','VDD_3V3',[(167.6,101.4),(179.6,101.4),(183.6,97.4)],.35,'B.Cu')
t('Display supply arrival','VDD_3V3',[(183.6,97.4),'C9.1',(181.65,97.05),'U4.1'],.35)
v('VDD_3V3',(167.6,101.4),(183.6,97.4))
t('VBUS named MCU bypass','USB_VBUS',['C1.1',(169.001,112.401),'U1.32'],.25)

t('C3 explicit local return','GND',['C3.2',(177.1,102.9),(177.6,103.4)],.25)
t('C4 explicit local return','GND',['C4.2',(173.8,107.2),(173.8,106.6)],.25)
t('U3 explicit local return','GND',['U3.2',(170.6,107.7)],.25)
t('C5 explicit local return','GND',['C5.2',(165.5,108.65)],.25)
t('R19 direct return','GND',['R19.2',(171.2535,105.4),(170.6,106.0535),(170.6,107.7)],.25)
t('C2 return','GND',['C2.2',(181.2,106.3),(180.2,107.3)],.25)
t('C8 direct EP return','GND',['C8.2',(179.5,108),'U2.11'],.25)
t('R14 local return','GND',['R14.2',(168.9965,98.3)],.25)
t('U4 local return','GND',['U4.2',(179.2,96.4)],.25)
v('GND',(177.6,103.4),(173.8,106.6),(170.6,107.7),(165.5,108.65),(168.9965,98.3),(179.2,96.4))

gen=[dict(name=r['name'],net=r['net'],layers=[r['layer']],shape=LineString(r['points']).buffer(r['width']/2),kind='track') for r in rs]
gen += [dict(name=str(v),net=v['net'],layers=['F.Cu','B.Cu'],shape=Point(v['at']).buffer(.3),kind='via',at=v['at']) for v in vs]
fail=[]
for r in rs:
    for a,z in zip(r['points'],r['points'][1:]):
        dx,dy=abs(z[0]-a[0]),abs(z[1]-a[1])
        assert min(dx,dy,abs(dx-dy))<1e-5,(r['name'],a,z)
for i,o in enumerate(gen):
    for other in objects+gen[:i]:
        if o['net']!=other['net'] and set(o['layers'])&set(other['layers']):
            gap=o['shape'].distance(other['shape'])
            if gap<.2-1e-5:fail.append(dict(a=o['name'],b=other['name'],gap_mm=round(gap,6)))
    if o['kind']=='via':
        for q in pads.values():
            gap=Point(o['at']).distance(q['shape'])
            if len(q['layers'])==1 and gap<.55-1e-5:fail.append(dict(a=o['name'],b=q['name'],drill_gap_mm=round(gap-.15,6)))
plan.update(routes=rs,vias=vs,failures=fail,description='A2 west regulator and explicit returns coexist with USB fanout and five charger controls',record='projects/nfc-business-card/hardware/records/kicad-v4-option-a2/west-critical-ipc.json')
(p/'critical-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(routes=len(rs),vias=len(vs),failures=fail),indent=2))
