#!/usr/bin/env python3
"""Verify option A preservation and identity without implying a design release."""
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from kicad_sexpr import child, children, prop, read
from v4_geometry import geometry

project = Path(__file__).resolve().parents[1]
repo = project.parents[1]
records = project / 'hardware/records/kicad-v4-option-a'
current = project / 'hardware/kicad/v4-option-a'
original = project / 'hardware/kicad/v4-phase3'
filename = 'NFC-Card-V4.kicad_pcb'
baseline = json.loads((records/'baseline-files.json').read_text())
assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==sha for n,sha in baseline.items())
b,p,o,f = geometry(current/filename)
old,op,oo,of = geometry(original/filename)
assert {n:x['net'] for n,x in p.items()} == {n:x['net'] for n,x in op.items()}
fixed = ['U1','J1','J2','C23','C24','BP','BN','TP1','TP2','TP3','TP4','TP5','SW1','SW2','SW3']
assert all(f[r]==of[r] for r in fixed)
assert {'Q2','Q3','R20','R21','R22','R23','C25'} <= f.keys()
edges = lambda board: [x for x in board if isinstance(x,list) and x[0].startswith('gr_') and child(x,'layer')==['layer','Edge.Cuts']]
assert edges(b)==edges(old)
copper = lambda x: (x['kind'],tuple(x['layers']),x['shape'].wkb_hex)
assert {copper(x) for x in o if x['net']=='NFC1_TBD'} == {copper(x) for x in oo if x['net']=='NFC1_TBD'}
assert float(child(child(b,'general'),'thickness')[1]) == .8
zones = lambda board: {child(z,'name')[1]:z for z in children(board,'zone') if child(z,'keepout')}
for name,z in zones(old).items():
    if name!='D-3f291e373f46901a':
        assert z==zones(b)[name], name
    else:
        new = zones(b)[name]
        assert child(z,'keepout')==child(new,'keepout')
        assert child(z,'layers')==child(new,'layers')
        for a,c in zip(child(child(z,'polygon'),'pts')[1:],child(child(new,'polygon'),'pts')[1:]):
            assert math.isclose(float(c[1])-float(a[1]),3.5,abs_tol=1e-6)
            assert math.isclose(float(c[2]),float(a[2]),abs_tol=1e-6)
parts = lambda board: {prop(x,'Reference')[2]:(prop(x,'MPN')[2],prop(x,'LCSC')[2]) for x in children(board,'footprint') if prop(x,'MPN')}
assert parts(b)==parts(old)
for file in ['fp-lib-table','sym-lib-table']:
    for lib in children(read(current/file),'lib'):
        uri=child(lib,'uri')[1]
        assert uri.startswith('${KIPRJMOD}/')
        assert (current/uri.replace('${KIPRJMOD}/','')).exists()
for footprint in children(b,'footprint'):
    assert (current/'NFC_V4.pretty'/(footprint[1].split(':')[1]+'.kicad_mod')).exists()
for ext in ['kicad_pro','kicad_dru']:
    assert (current/f'NFC-Card-V4.{ext}').read_bytes()==(original/f'NFC-Card-V4.{ext}').read_bytes()
for file in original.glob('*.kicad_sch'):
    assert file.read_bytes()==(current/file.name).read_bytes()
audit = json.loads((project/'hardware/records/kicad-v4/migration-audit.json').read_text())
expected = {(x['ref'],x['pin']):x['net'] for x in audit['part_pins']}
normalize = lambda n: '' if n.startswith('unconnected-') else n
netlist = ET.parse(project/'artifacts/kicad-v4-option-a/netlist.xml')
actual = {(n.attrib['ref'],n.attrib['pin']):normalize(net.attrib['name']) for net in netlist.findall('.//nets/net') for n in net.findall('node') if not n.attrib['ref'].startswith(('XUSB','XDBG'))}
assert expected==actual
new_segments=[x for x in children(b,'segment') if child(x,'net')[-1]!='NFC1_TBD']
for x in new_segments:
    a,c=child(x,'start')[1:],child(x,'end')[1:]
    dx,dy=[abs(float(v)-float(w)) for v,w in zip(a,c)]
    assert min(dx,dy,abs(dx-dy))<.00001
    assert float(child(x,'width')[1])>=.15
for v in children(b,'via'):
    if child(v,'net')[-1]!='NFC1_TBD':
        assert float(child(v,'size')[1])==.6 and float(child(v,'drill')[1])==.3
functional=json.loads((records/'joint-seeded-audit/audit.json').read_text())
ablation=json.loads((records/'sampling-ablation-audit/audit.json').read_text())
isolated=lambda a:sorted(n for n,reaches in a['ground_pad_to_U2_EP'].items() if not reaches)
assert isolated(functional)==isolated(ablation)
assert functional['ground_components_not_reaching_U2_EP']==ablation['ground_components_not_reaching_U2_EP']
drc=json.loads((records/'controls-power-drc.json').read_text())
result={'status':'IDENTITY PASS; OPTION A INTEGRATION GATE FAILED; NOT FOR FABRICATION',
        'preserved_files':len(baseline),'fixed_datums':fixed,'pads':len(p),'part_pins':len(expected),
        'bom_parts':len(parts(b)),'footprints':len(f),'tracks':len(children(b,'segment')),'vias':len(children(b,'via')),
        'pin_networks_unchanged':True,'schematics_bom_rules_and_exclusions_unchanged':True,
        'adc_retained':True,'nfc_copper_and_mechanical_datums_unchanged':True,
        'relative_project_libraries_resolve':True,
        'u5_pour_only_window_translated_mm':[3.5,0],
        'new_traces_H_V_45':True,'trace_min_mm':.15,'new_via_mm':[.6,.3],
        'drc':dict(Counter(x['type'] for x in drc['violations'])),
        'unconnected':len(drc['unconnected_items']),'parity':len(drc['schematic_parity']),
        'sampling_ablation_failed_to_restore_returns':isolated(functional),
        'files':{str(x.relative_to(current)):hashlib.sha256(x.read_bytes()).hexdigest() for x in current.rglob('*') if x.is_file() and not x.name.startswith('~') and x.suffix!='.kicad_prl'}}
(records/'identity-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
