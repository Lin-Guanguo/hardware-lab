#!/usr/bin/env python3
"""Require both NFCT terminals to connect only through the complete R1 spiral."""
import argparse
import copy
import json
import runpy
from pathlib import Path

COPPER = runpy.run_path(str(Path(__file__).with_name('check-r1-copper.py')))

def check(s):
    cuts = [i for i,t in enumerate(s['lines']) if t['net']=='NFC1_TBD' and t['layer']==2
            and abs(t['x1']*.0254-4.1)<.03 and abs(t['x2']*.0254-4.1)<.03
            and abs(min(t['y1'],t['y2'])*.0254-22.5)<.03
            and abs(max(t['y1'],t['y2'])*.0254-45.7)<.03]
    assert len(cuts)==1, 'Expected one outer-loop cut segment'
    before = COPPER['audit'](s)['groups']['NFC1_TBD']
    after = COPPER['audit'](s, cuts[0])['groups']['NFC1_TBD']
    expected = [set(['52@(59.25,6.66)','1@(55.90,8.00)','NFC2@(36.30,30.00)']),
                set(['54@(59.25,5.86)','1@(55.90,6.00)','NFC1@(36.30,27.00)'])]
    matches = [[i for i,g in enumerate(after) if e.issubset(g)] for e in expected]
    ok = len(before)==1 and len(after)==2 and all(len(m)==1 for m in matches) and matches[0]!=matches[1]
    return {'ok':ok,'connected_groups_before_cut':len(before),'groups_after_cut':after,'cut_line_index':cuts[0],
            'scope':'Copper topology only; this does not establish RF resonance or read range.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--output',type=Path)
    a=ap.parse_args();s=json.loads(a.snapshot.read_text());r=check(s)
    # A deliberately injected bypass must invalidate the proof.
    bad=copy.deepcopy(s);bad['lines'].append({'net':'NFC1_TBD','layer':1,'x1':55.9/.0254,'y1':6/.0254,'x2':55.9/.0254,'y2':8/.0254,'widthMil':.25/.0254})
    r['bypass_negative_control_passed']=not check(bad)['ok'];r['ok'] &= r['bypass_negative_control_passed']
    text=json.dumps(r,indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text);raise SystemExit(0 if r['ok'] else 1)
