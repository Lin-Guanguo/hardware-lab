#!/usr/bin/env python3
"""Construct and independently check the A2 supply and local return skeleton."""
import json
from pathlib import Path

from shapely.geometry import LineString, Point
from v4_geometry import geometry

root = Path(__file__).resolve().parents[3]
project = root / 'projects/nfc-business-card'
target = project / 'hardware/kicad/v4-option-a2-expanded-rejected/NFC-Card-V4.kicad_pcb'
_, pads, objects, _ = geometry(target)
routes, vias = [], []


def trace(name, net, layer, points, width=.35):
    points = [pads[p]['at'] if isinstance(p, str) else p for p in points]
    for p, q in zip(points, points[1:]):
        dx, dy = abs(q[0]-p[0]), abs(q[1]-p[1])
        assert min(dx, dy, abs(dx-dy)) < .00001, (name, p, q)
    routes.append(dict(name=name, net=net, layer=layer, width=width, points=points))


def via(net, *points):
    vias.extend(dict(net=net, at=p) for p in points)


trace('BAT pin neck', 'BAT_PACK_TBD', 'F.Cu', ['U2.2', (177.4,106.2)], .15)
trace('BAT direct local capacitor', 'BAT_PACK_TBD', 'F.Cu', [(177.4,106.2), 'C3.1'])
trace('BAT lead', 'BAT_PACK_TBD', 'F.Cu', ['BP.1',(142.5,110.05),(161.85,110.05),(165.9,106)], .5)
trace('BAT paired supply bridge', 'BAT_PACK_TBD', 'B.Cu', [(165.9,106),(169.2,102.7),(173.8,102.7),(176.4,105.3)], .5)
trace('BAT capacitor entrance', 'BAT_PACK_TBD', 'F.Cu', [(176.4,105.3),'C3.1'])
via('BAT_PACK_TBD',(165.9,106),(176.4,105.3))

trace('SYS pin neck', 'SYS', 'F.Cu', ['U2.1',(178.5,106.25)], .15)
trace('SYS capacitor', 'SYS', 'F.Cu', [(178.5,106.25),(179.2,106.25),'C2.1'])
trace('SYS input spine', 'SYS', 'F.Cu', ['C4.1',(181.7,103.4),(182.55,102.55),'U3.1'])
trace('SYS source transition','SYS','F.Cu',['C2.1',(179.2,104.5),(178.7,104)],.35)
trace('SYS input bridge','SYS','B.Cu',[(178.7,104),(182.2,104),(182.7,104.5)],.35)
trace('SYS bridge capacitor contact','SYS','F.Cu',[(182.7,104.5),'C4.1'],.35)
trace('SYS enable strap','SYS','F.Cu',['U3.3',(184.45,102.6)],.15)
trace('SYS enable local bridge','SYS','B.Cu',[(184.45,102.6),(183.8,103.25),(182.7,104.35),(182.7,104.5)],.15)
via('SYS',(178.7,104),(182.7,104.5),(184.45,102.6))

trace('LDO output to local display decoupling', 'VDD_3V3', 'F.Cu', ['C5.1',(180.1,100.9),(179.2,100),(179.2,98.4),(181,98.4),'C9.1'])
trace('LDO output capacitor', 'VDD_3V3', 'F.Cu', ['U3.5',(182.55,100),(181.65,100.9),'C5.1'])
trace('Display load switch supply', 'VDD_3V3', 'F.Cu', ['C9.1',(181.65,97.05),'U4.1'])
trace('MCU rail departure', 'VDD_3V3', 'F.Cu', [(179.2,100),(177.8,101.4),(177.8,101.9)])
trace('MCU rail backbone', 'VDD_3V3', 'B.Cu', [(177.8,101.9),(177.8,106.2),(174.3,109.7),(172.5,109.7)], .5)
trace('MCU C6 feed', 'VDD_3V3', 'F.Cu', [(172.5,109.7),'C6.1'], .35)
trace('MCU C7 feed', 'VDD_3V3', 'F.Cu', [(172.5,109.7),'C7.1'], .35)
trace('MCU VDD pad 30', 'VDD_3V3', 'F.Cu', ['C7.1',(168.8,111.399),(170.601,113.2),'U1.30'], .2)
trace('MCU VDD pad 28', 'VDD_3V3', 'F.Cu', ['C6.1',(172.5,112.101),(171.401,113.2),'U1.28'], .2)
via('VDD_3V3',(177.8,101.9),(172.5,109.7))

trace('BN paired lead', 'GND', 'F.Cu', ['BN.1',(163.1005,111.3005),(167.15,107.251)], .5)
trace('BN return backbone', 'GND', 'F.Cu', [(167.15,107.251),(175.551,107.251),(176.3,108),'U2.11'], .5)
trace('U2 exposed pad to return', 'GND', 'F.Cu', ['U2.11',(178.6,108)], .35)
trace('U2 pad 5 to EP', 'GND', 'F.Cu', ['U2.5',(176.2,107.5),(176.7,108),'U2.11'], .15)
via('GND',(167.15,107.251),(178.6,108))
trace('BAT capacitor local return', 'GND', 'F.Cu', ['C3.2',(176.4,103.9)], .25)

via('GND',(176.4,103.9))
trace('SYS capacitor local return', 'GND', 'F.Cu', ['C2.2',(180.6,106.9),'C8.2'], .25)
trace('IN capacitor local return', 'GND', 'F.Cu', ['C8.2',(179.5,108),'U2.11'], .25)

trace('LDO local input return', 'GND', 'F.Cu', ['U3.2',(183.5,102.6)], .25)
trace('LDO return via exit', 'GND', 'F.Cu', ['C4.2',(180.3,102.4)], .25)
trace('LDO input capacitor return','GND','F.Cu',['C4.2',(180.3,104.7),'C2.2'],.25)
trace('LDO output return', 'GND', 'F.Cu', ['C5.2',(180,99.5)], .25)
trace('LDO capacitor return bridge', 'GND', 'B.Cu', [(180,99.5),(181.7,101.2),(183.5,101.2),(183.5,102.6)], .35)
trace('LDO ground reference bridge','GND','B.Cu',[(180.3,102.4),(181.5,101.2),(181.7,101.2)],.35)
via('GND',(180.3,102.4),(180,99.5),(183.5,102.6))
for name, point in [('C1.2',(165.2,112.2)),('C6.2',(171.1,112.3)),('R14.2',(168.9965,98.3))]:
    trace(name+' local return','GND','F.Cu',[name,point],.25)
    via('GND',point)
trace('C7 ground into return spine','GND','F.Cu',['C7.2',(168.8,107.251)],.35)
trace('TS resistor local return', 'GND', 'F.Cu', ['R19.2',(173.2535,107.251)], .25)
trace('MCU decoupling return spine','GND','B.Cu',[(165.2,112.2),(171,112.2),(171.1,112.3),(171.1,108.3)],.35)
trace('MCU return into charger ground','GND','F.Cu',[(171.1,108.3),(171.1,107.251)],.35)
via('GND',(171.1,108.3))

generated = [dict(name=r['name'],net=r['net'],layers=[r['layer']],shape=LineString(r['points']).buffer(r['width']/2),kind='track') for r in routes]
generated += [dict(name=v['net']+' via '+str(v['at']),net=v['net'],layers=['F.Cu','B.Cu'],shape=Point(v['at']).buffer(.3),kind='via',at=v['at']) for v in vias]
failures=[]
for i, obj in enumerate(generated):
    for other in objects + generated[:i]:
        if obj['net'] != other['net'] and set(obj['layers']) & set(other['layers']):
            gap=obj['shape'].distance(other['shape'])
            if gap < .2-.00001:
                failures.append(dict(a=obj['name'], b=other['name'], gap_mm=round(gap,6)))
    if obj['kind']=='via':
        for pad in pads.values():
            gap=Point(obj['at']).distance(pad['shape'])
            if len(pad['layers'])==1 and gap < .55-.00001:
                failures.append(dict(a=obj['name'],b=pad['name'],smd_to_drill_gap_mm=round(gap-.15,6)))
plan=dict(board=str(target.relative_to(root)),description='A2 supply and explicit local return skeleton before signal integration',record=str((project/'hardware/records/kicad-v4-option-a2/power-ipc.json').relative_to(root)),routes=routes,vias=vias,failures=failures)
(target.parent/'power-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(routes=len(routes),vias=len(vias),failures=failures),indent=2))
