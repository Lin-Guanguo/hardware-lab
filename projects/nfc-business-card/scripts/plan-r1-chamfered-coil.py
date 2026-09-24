#!/usr/bin/env python3
"""Generate the five-turn R1 coil with equal exposed-edge offsets."""
import argparse
import json
import math
from pathlib import Path
from shapely.geometry import LineString

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args()
points=[[36.3,27],[34,27]]
turns=[]
for i in range(5):
    offset=.5*i
    left,right,bottom,top=4.1+offset,34-offset,20.3+offset,47.9-offset
    # Parallel offset of x+y=constant diagonal edges: preserve .5 mm normal pitch.
    chamfer=2.2-offset*(2-math.sqrt(2))
    y=27.5+offset
    points.extend([[right,bottom+chamfer],[right-chamfer,bottom],[left+chamfer,bottom],
                   [left,bottom+chamfer],[left,top-chamfer],[left+chamfer,top],
                   [right-chamfer,top],[right,top-chamfer],[right,y]])
    turns.append({'rect_mm':[left,bottom,right,top],'chamfer_leg_mm':chamfer})
    if i<4:points.append([right-.5,y])
points.append([31.4,29.5])
segments=[LineString([p,q]) for p,q in zip(points,points[1:])]
clearance=min(a.distance(b)-.25 for i,a in enumerate(segments) for j,b in enumerate(segments) if j>i+1)
assert clearance>=.25-1e-8
plan={'name':'R1 five-turn 45-degree coil; three exposed straight edges at 3 mm centreline offset',
      'tracks':[{'net':'NFC1_TBD','layer':2,'width_mm':.25,'points':points}],
      'vias':[],'turns':turns,'preserved_crossover_vias_mm':[[31.4,29.5],[35.3,30]],
      'outer_centerline_edge_offsets_mm':{'left':3,'bottom':3,'top':3},
      'outer_copper_edge_offsets_mm':{'left':2.875,'bottom':2.875,'top':2.875},
      'minimum_nonadjacent_trace_space_mm':clearance,'scope':'Geometry only; RF requires assembled measurement.'}
a.output.write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps({'segments':len(segments),'min_space_mm':clearance,'length_mm':sum(s.length for s in segments)}))
