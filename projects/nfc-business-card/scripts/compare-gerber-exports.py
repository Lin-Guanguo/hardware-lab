#!/usr/bin/env python3
"""Compare EasyEDA Gerber exports after unit/precision/header normalization."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

NUMBER=re.compile(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)')

def normalize(text,drill=False):
    lines=text.splitlines();ignored=[]
    if drill:
        return [line for line in lines if line and not line.startswith((';','METRIC,'))],ignored
    match=re.search(r'%FSLAX(\d)(\d)Y(\d)(\d)\*%',text)
    assert match and '%MOMM*%' in text
    assert match[2]==match[4]
    scale=10**int(match[2])
    used=set(re.findall(r'(?:G54)?D(\d+)\*',text))
    definitions=re.findall(r'%ADD(\d+)',text)
    aperture_ids={number:str(i+10) for i,number in enumerate(n for n in definitions if n in used)}
    normalized=[]
    for line in lines:
        if not line or line.startswith(('G04','%FS')):continue
        definition=re.match(r'%ADD(\d+)',line)
        if definition and definition[1] not in used:
            ignored.append(line);continue
        if definition:
            line=re.sub(r'^%ADD\d+', '%ADD'+aperture_ids[definition[1]], line)
        line=re.sub(r'G54D(\d+)\*',lambda m:'G54D'+aperture_ids[m[1]]+'*',line)
        if not line.startswith('%'):
            line=re.sub(r'([XYIJ])(-?\d+)',lambda m:m[1]+format(int(m[2])/scale,'.6f'),line)
        normalized.append(line)
    return normalized,ignored

def compare(left,right,drill=False):
    a,ia=normalize(left,drill);b,ib=normalize(right,drill)
    bad=[];max_delta=0
    if len(a)!=len(b):bad.append({'line_count':[len(a),len(b)]})
    for i,(x,y) in enumerate(zip(a,b)):
        na=list(map(float,NUMBER.findall(x)));nb=list(map(float,NUMBER.findall(y)))
        if NUMBER.sub('#',x)!=NUMBER.sub('#',y) or len(na)!=len(nb):
            bad.append({'line':i,'left':x,'right':y});continue
        delta=max((abs(v-w) for v,w in zip(na,nb)),default=0)
        max_delta=max(max_delta,delta)
        if delta>1.1e-5:bad.append({'line':i,'delta':delta,'left':x,'right':y})
    return {'equivalent_within_export_precision':not bad,'normalized_commands':[len(a),len(b)],
            'max_numeric_delta':max_delta,'unused_aperture_definitions_ignored':[len(ia),len(ib)],'differences':bad[:10]}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('api',type=Path);ap.add_argument('manual',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    report={'api':{'bytes':a.api.stat().st_size,'sha256':hashlib.sha256(a.api.read_bytes()).hexdigest()},'manual':{'bytes':a.manual.stat().st_size,'sha256':hashlib.sha256(a.manual.read_bytes()).hexdigest()},'files':{}}
    with zipfile.ZipFile(a.api) as x,zipfile.ZipFile(a.manual) as y:
        report.update(only_api=sorted(set(x.namelist())-set(y.namelist())),only_manual=sorted(set(y.namelist())-set(x.namelist())))
        for n in sorted(set(x.namelist())&set(y.namelist())):
            left=x.read(n);right=y.read(n)
            if n.startswith('Gerber_') or n.endswith('.DRL'):
                report['files'][n]=compare(left.decode(),right.decode(),n.endswith('.DRL'))
            else:report['files'][n]={'identical_bytes':left==right}
        report['extra_manual_files']={n:{'bytes':len(y.read(n)),'compressed_bytes':y.getinfo(n).compress_size} for n in report['only_manual']}
    report['ok']=all(v.get('equivalent_within_export_precision',v.get('identical_bytes',False)) for v in report['files'].values()) and not report['only_api']
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['ok'] else 1)
