#!/usr/bin/env python3
"""Construct the complete charger-control bundle, without grid search or locked escapes."""
import json
from pathlib import Path

from shapely.geometry import LineString, Point
from v4_geometry import geometry

root = Path(__file__).resolve().parents[3]
project = root / 'projects/nfc-business-card'
board_path = project / 'hardware/kicad/v4-option-a/NFC-Card-V4.kicad_pcb'
_, pads, objects, _ = geometry(board_path)
routes, vias = [], []


def trace(name, net, layer, points, width=.15):
    pts = [pads[p]['at'] if isinstance(p, str) else p for p in points]
    for p, q in zip(pts, pts[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        assert min(dx, dy, abs(dx - dy)) < .00001, (name, p, q)
    routes.append({'name': name, 'net': net, 'layer': layer, 'width': width, 'points': pts})


def via(net, *positions):
    vias.extend({'net': net, 'at': p} for p in positions)


trace('SDA charger exit', 'CHG_SDA', 'F.Cu', ['U2.7', (176.6,109.7), (176,110.3)])
trace('SDA local bridge', 'CHG_SDA', 'B.Cu', [(176,110.3), (175.4,110.9), (175.4,115.701), (175.001,116.1)])
trace('SDA MCU inner pad', 'CHG_SDA', 'F.Cu', [(175.001,116.1), 'U1.19'])
trace('SDA pullup branch', 'CHG_SDA', 'F.Cu', ['U1.19', (179.1125,114.834), 'R5.2'])
via('CHG_SDA', (176,110.3), (175.001,116.1))

# The 1 um x offset is inside the source pad, avoiding a meaningless 1 um diagonal.
trace('SCL direct local link', 'CHG_SCL', 'F.Cu', [(177.001,109.05), 'U1.16'])
trace('SCL pullup bridge', 'CHG_SCL', 'B.Cu', [(177.001,112.2), (178.6,113.799), (178.6,116)])
trace('SCL pullup contact', 'CHG_SCL', 'F.Cu', [(178.6,116), 'R6.2'])
via('CHG_SCL', (177.001,112.2), (178.6,116))

trace('INT charger exit', 'CHG_INT_N', 'F.Cu', ['U2.9', (177.4,109.7), (178.1,110.4)])
trace('INT crossing over SCL', 'CHG_INT_N', 'B.Cu', [(178.1,110.4), (177.4,110.4), (176.2,111.6)])
trace('INT MCU outer pad', 'CHG_INT_N', 'F.Cu', [(176.2,111.6), (175.401,112.399), (174.601,112.399), 'U1.20'])
trace('INT pullup branch', 'CHG_INT_N', 'B.Cu', [(178.1,110.4), (179.7,112), (179.7,116.6), (178.6,117.7)])
trace('INT pullup contact', 'CHG_INT_N', 'F.Cu', [(178.6,117.7), 'R8.2'])
via('CHG_INT_N', (178.1,110.4), (176.2,111.6), (178.6,117.7))

trace('PG north exit', 'CHG_PG_N', 'F.Cu', ['U2.3', (177,105.5)])
trace('PG local west bridge', 'CHG_PG_N', 'B.Cu', [(177,105.5), (176.7,105.8), (172.8,105.8), (172.8,114.899), (174.201,116.3)])
trace('PG MCU inner pad', 'CHG_PG_N', 'F.Cu', [(174.201,116.3), 'U1.21'])
trace('PG pullup branch', 'CHG_PG_N', 'B.Cu', [(174.201,116.3), (174.201,118.8), (178,118.8), (178.6,119.4)])
trace('PG pullup contact', 'CHG_PG_N', 'F.Cu', [(178.6,119.4), 'R9.2'])
via('CHG_PG_N', (177,105.5), (174.201,116.3), (178.6,119.4))

trace('CE north exit', 'CHG_CE_N', 'F.Cu', ['U2.4', (176.6,106.3), (175.5,106.3), (175.25,106.55)])
trace('CE local bridge', 'CHG_CE_N', 'B.Cu', [(175.25,106.55), (175.25,109.5), (173.801,110.949), (173.801,112.5)])
trace('CE MCU outer pad', 'CHG_CE_N', 'F.Cu', [(173.801,112.5), 'U1.22'])
trace('CE north pullup', 'CHG_CE_N', 'F.Cu', [(175.25,106.55), (175.25,103.2965), 'R7.2'])
via('CHG_CE_N', (175.25,106.55), (173.801,112.5))

trace('BAT pin pitch neck', 'BAT_PACK_TBD', 'F.Cu', ['U2.2', (177.4,106.3), (177.8,105.9)])
trace('BAT local capacitor', 'BAT_PACK_TBD', 'F.Cu', [(177.8,105.9), (177.8,104.8), (177.3,104.3), 'C3.1'], .35)
trace('BAT paired lead exit', 'BAT_PACK_TBD', 'F.Cu', ['BP.1', (142.5,110.05), (161.85,110.05), (165.9,106)], .5)
trace('BAT upper bridge', 'BAT_PACK_TBD', 'B.Cu', [(165.9,106), (169.2,102.7), (175.7,102.7), (177.3,104.3)], .5)
via('BAT_PACK_TBD', (165.9,106), (177.3,104.3))
trace('SYS pin pitch neck', 'SYS', 'F.Cu', ['U2.1', (178.5,106.25)])
trace('SYS local capacitor', 'SYS', 'F.Cu', [(178.5,106.25), (179.2,106.25), 'C2.1'], .35)
trace('BN paired lead exit', 'GND', 'F.Cu', ['BN.1', (163.1005,111.3005), (167.15,107.251)], .5)
via('GND', (167.15,107.251), (178.6,108))
trace('U2 EP local ground', 'GND', 'F.Cu', ['U2.11', (178.6,108)], .35)
trace('U2 pin 5 ground', 'GND', 'F.Cu', ['U2.5', (176.2,107.5), (176.7,108), 'U2.11'])

generated = [dict(name=r['name'],net=r['net'],layers=[r['layer']],shape=LineString(r['points']).buffer(r['width']/2),kind='track') for r in routes]
generated += [dict(name=v['net']+' via '+str(v['at']),net=v['net'],layers=['F.Cu','B.Cu'],shape=Point(v['at']).buffer(.3),kind='via',at=v['at']) for v in vias]
failures=[]
for i, obj in enumerate(generated):
    for other in objects + generated[:i]:
        if obj['net'] != other['net'] and set(obj['layers']) & set(other['layers']):
            gap=obj['shape'].distance(other['shape'])
            if gap < .2 - .00001:
                failures.append({'a':obj['name'],'b':other['name'],'gap_mm':gap})
    if obj['kind']=='via':
        for pad in pads.values():
            gap=Point(obj['at']).distance(pad['shape'])
            if len(pad['layers'])==1 and gap < .55 - .00001:
                failures.append({'a':obj['name'],'b':pad['name'],'smd_to_drill_gap_mm':gap-.15})
plan={'board':str(board_path.relative_to(root)),'description':'Option A jointly planned charger controls, local paths and all pullup branches','record':str((project/'hardware/records/kicad-v4-option-a/controls-ipc.json').relative_to(root)), 'routes':routes,'vias':vias,'failures':failures}
(board_path.parent/'controls-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps({'routes':len(routes),'vias':len(vias),'failures':failures},indent=2))
