#!/usr/bin/env python3
"""Extract typical DC-bias points from saved public Samsung part pages."""
import argparse
import hashlib
import json
from pathlib import Path

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('directory',type=Path)
ap.add_argument('output',type=Path)
a=ap.parse_args()
rows=[]
for name,nominal,biases in [('CL10A225KO8NNN',2.2,[3.3,4.2,4.5,5]),('CL10A475KO8NNN',4.7,[3.3,4.2,4.5,5]),('CL10A106KP8NNN',10,[3.3,4.5,5])]:
    source=a.directory/(name+'.html')
    data,_=json.JSONDecoder().raw_decode(source.read_text().split('var datasheetData =',1)[1].lstrip())
    d=next(d for d in data if d['graphType']=='DCBias')['selectPartsList'][0]
    assert d['partsName']==name
    pts=sorted((float(q['x']),float(q['y'])) for q in d['chartList'][0]['data'])
    for v in biases:
        lo=max(q for q in pts if q[0]<=v)
        hi=min(q for q in pts if q[0]>=v)
        change=lo[1] if lo[0]==hi[0] else lo[1]+(hi[1]-lo[1])*(v-lo[0])/(hi[0]-lo[0])
        rows.append({'part':name+'C','source':'https://product.samsungsem.com/mlcc/'+name+'.do','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bias_V':v,'typical_change_pct':round(change,3),'typical_C_uF':round(nominal*(1+change/100),3),'temperature_C':d['degC'],'frequency_Hz':d['dsDcFre'],'signal_Vrms':d['dsDcSign'],'guaranteed_minimum':False})
a.output.write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
