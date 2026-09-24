"""Inspect native body geometry in the saved E20B assembly; run in FreeCAD."""
import json
import os
from itertools import combinations
from pathlib import Path
import FreeCAD as App

ROOT=Path(__file__).resolve().parents[1]
revision=os.environ.get('NFC_BODY_REVIEW_REV','e20b')
assembly=Path(os.environ.get('NFC_E20_OUT',str(ROOT/'enclosure/e20b-functional-5.8')))
doc=App.openDocument(str(assembly/'e20-clear-assembly.FCStd'))
parts={o.Name.removeprefix('Component_'):o.Shape for o in doc.Objects if o.Name.startswith('Component_')}
bounds={r:{'min_mm':[s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin],
           'max_mm':[s.BoundBox.XMax,s.BoundBox.YMax,s.BoundBox.ZMax]} for r,s in parts.items()}
close=[]
for a,b in combinations(parts,2):
    ba,bb=parts[a].BoundBox,parts[b].BoundBox
    # Expanded boxes limit costly solid checks to actual neighbours.
    if ba.XMax+.8<bb.XMin or bb.XMax+.8<ba.XMin or ba.YMax+.8<bb.YMin or bb.YMax+.8<ba.YMin:continue
    distance=parts[a].distToShape(parts[b])[0]
    if distance<.8:
        close.append({'a':a,'b':b,'clearance_mm':distance,'intersection_mm3':parts[a].common(parts[b]).Volume})
fpc=doc.getObject('FPCServiceVolume').Shape
fpc_hits={r:s.common(fpc).Volume for r,s in parts.items() if s.BoundBox.intersect(fpc.BoundBox)}
report={'status':'NOMINAL_NATIVE_BODY_GEOMETRY','components':len(parts),'nearby_pairs':sorted(close,key=lambda p:p['clearance_mm']),
        'component_intersections':[p for p in close if p['intersection_mm3']>1e-6],
        'open_lid_fpc_service_intersections_mm3':{r:v for r,v in fpc_hits.items() if v>1e-6},
        'limits':['Native library models are not supplier maximum envelopes.','Assembly service volume is not the folded flex geometry.']}
(ROOT/f'hardware/records/{revision}-body-bounds.json').write_text(json.dumps(bounds,indent=2)+'\n')
(ROOT/f'hardware/records/{revision}-body-fit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
