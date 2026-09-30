#!/usr/bin/env python3
"""Correct DSN overblocking of native pour-only windows, retaining RF exclusion."""
import argparse
import json
from pathlib import Path

from kicad_sexpr import parse, child, children, dumps, Quoted, read

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('source', type=Path)
ap.add_argument('output', type=Path)
ap.add_argument('record', type=Path)
ap.add_argument('--board', type=Path)
a=ap.parse_args()
b=parse(a.source.read_text().replace('(string_quote ")',''))
structure=child(b,'structure')
changes=[]
u5_bounds = (183750,184350)
if a.board:
    z=next(z for z in children(read(a.board),'zone') if child(z,'name') and child(z,'name')[1]=='D-3f291e373f46901a')
    xx=[float(x[1])*1000 for x in child(child(z,'polygon'),'pts')[1:]]
    u5_bounds=(min(xx),max(xx))
for zone in list(children(structure,'keepout')):
    polygon=child(zone,'polygon')
    layer=polygon[1]
    points=list(zip(map(float,polygon[3::2]),map(float,polygon[4::2])))
    x0,x1=min(x for x,y in points),max(x for x,y in points)
    y0,y1=min(-y for x,y in points),max(-y for x,y in points)
    if layer=='Top Layer' and ((abs(x0-u5_bounds[0])<2 and abs(x1-u5_bounds[1])<2) or (185000<x0<185100 and 192800<x1<193000)):
        structure.remove(zone)
        changes.append({'bounds_um':[x0,y0,x1,y1],'action':'Remove DSN track blocker; native rule prohibits pour only (U5/J1)'})
    elif layer=='Top Layer' and x0==110000 and x1==149620:
        for i in range(4,len(polygon),2):
            polygon[i]=str(max(float(polygon[i]),-109600))
        changes.append({'bounds_um':[x0,y0,x1,y1],'action':'Keep RF track exclusion, except F.Cu battery lead exit strip y=109.6..113.0 mm; only BAT/GND may use this strip'})
    elif layer=='Top Layer' and x0==113000 and x1==145000:
        structure.remove(zone)
        changes.append({'bounds_um':[x0,y0,x1,y1],'action':'Remove duplicate RF inner DSN blocker; protected by outer RF region; no native rule changed'})
assert len(changes)==4,changes
a.output.write_text(dumps(b).replace('(parser','(parser\n    (string_quote ")',1)+'\n')
a.record.write_text(json.dumps({'native_board_rules_changed':False,'changes':changes,'postcheck':'Reject any non-BAT/non-GND new copper in RF lead strip. B.Cu RF region and both BLE blockers remain.'},indent=2)+'\n')
