#!/usr/bin/env python3
"""Check preserved inputs and pin identity; never equate this with layout release."""
import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from kicad_sexpr import child, children, prop, read
from v4_geometry import geometry


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage', choices=['v4-phase2','v4-phase3'], default='v4-phase2')
    args=ap.parse_args()
    project=Path(__file__).resolve().parents[1]
    root=project/'hardware/kicad'/args.stage
    records=project/'hardware/records'/('kicad-'+args.stage)
    artifacts=project/'artifacts'/('kicad-'+args.stage)
    phase1=json.loads((project/'hardware/records/kicad-v4-phase2/phase1-baseline.json').read_text())
    repo=project.parents[1]
    assert all(hashlib.sha256((repo/phase1['source']/n).read_bytes()).hexdigest()==sha for n,sha in phase1['files'].items())
    if args.stage=='v4-phase3':
        phase2=json.loads((records/'phase2-baseline.json').read_text())
        assert all(hashlib.sha256((repo/phase2['source']/n).read_bytes()).hexdigest()==sha for n,sha in phase2['files'].items())
    d_file=repo/'eda/NFC-Card-R2-Board-Review-D.eprj2'
    assert hashlib.sha256(d_file.read_bytes()).hexdigest()=='1ba5a615cd051b29c45f9aaca5ccaa6c15dc469eadf2e713c6bea9a0d9569783'
    board,pads,objects,refs=geometry(root/'NFC-Card-V4.kicad_pcb')
    old,old_pads,old_objects,old_refs=geometry(project/'hardware/kicad/v4/NFC-Card-V4.kicad_pcb')
    normalize=lambda n: '' if n.startswith('unconnected-') else n
    assert {n:normalize(p['net']) for n,p in pads.items()}=={n:normalize(p['net']) for n,p in old_pads.items()}
    audit=json.loads((project/'hardware/records/kicad-v4/migration-audit.json').read_text())
    expected={(n['ref'],n['pin']):n['net'] for n in audit['part_pins']}
    netlist=artifacts/(args.stage+'-netlist.xml')
    subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(netlist),str(root/'NFC-Card-V4.kicad_sch')],check=True)
    actual={(n.attrib['ref'],n.attrib['pin']):normalize(net.attrib['name']) for net in ET.parse(netlist).findall('.//nets/net') for n in net.findall('node') if not n.attrib['ref'].startswith(('XUSB','XDBG'))}
    assert actual==expected
    fixed=['U1','J1','J2','C23','C24','BP','BN','TP1','TP2','TP3','TP4','TP5','SW1','SW2','SW3']
    for ref in fixed:
        assert ref in refs and refs[ref]==old_refs[ref],ref
    assert {'Q2','Q3','R20','R21','R22','R23','C25'}.issubset(refs)
    copper=lambda o:(o['kind'],o['net'],tuple(o['layers']),o['shape'].wkb_hex)
    assert {copper(o) for o in objects if o['net']=='NFC1_TBD'}=={copper(o) for o in old_objects if o['net']=='NFC1_TBD'}
    edges=lambda t:[n for n in t if isinstance(n,list) and n[0].startswith('gr_') and child(n,'layer') and child(n,'layer')[1]=='Edge.Cuts']
    assert edges(board)==edges(old)
    keepouts=lambda t:{child(z,'name')[1]:[n for n in z if not isinstance(n,list) or n[0]!='uuid'] for z in children(t,'zone') if child(z,'keepout')}
    assert keepouts(board)==keepouts(old)
    assert float(child(child(board,'general'),'thickness')[1])==.8
    parts={}
    for fp in children(board,'footprint'):
        ref=prop(fp,'Reference')[2]
        assert (root/'NFC_V4.pretty'/(fp[1].split(':')[1]+'.kicad_mod')).exists()
        if prop(fp,'MPN'):parts[ref]=[prop(fp,'MPN')[2],prop(fp,'LCSC')[2]]
    oldparts={prop(f,'Reference')[2]:[prop(f,'MPN')[2],prop(f,'LCSC')[2]] for f in children(old,'footprint') if prop(f,'MPN')}
    assert parts==oldparts
    for file in [root/'fp-lib-table',root/'sym-lib-table']:
        for lib in children(read(file),'lib'):
            uri=child(lib,'uri')[1]
            assert uri.startswith('${KIPRJMOD}/') and (root/uri.replace('${KIPRJMOD}/','')).exists()
    # Preserve all numeric rules, severities, exclusions and stackup settings.
    pro=json.loads((root/'NFC-Card-V4.kicad_pro').read_text());oldpro=json.loads((project/'hardware/kicad/v4/NFC-Card-V4.kicad_pro').read_text())
    for key in ['rules','rule_severities','drc_exclusions']:
        assert pro['board']['design_settings'].get(key)==oldpro['board']['design_settings'].get(key),key
    assert (root/'NFC-Card-V4.kicad_dru').read_bytes()==(project/'hardware/kicad/v4/NFC-Card-V4.kicad_dru').read_bytes()
    files=[f for f in root.glob('*.kicad_*') if f.suffix in ('.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym')]+list((root/'NFC_V4.pretty').glob('*.kicad_mod'))+[root/'fp-lib-table',root/'sym-lib-table']
    result={'identity_and_constraints':'pass','design_release':'NOT PASSED: routing/return, input and DFM gates remain open','phase1_files_preserved':len(phase1['files']),'d_preserved':True,'part_pins':len(expected),'pads':len(pads),'u1_pads':len([n for n in pads if n.startswith('U1.')]),'bom_parts':len(parts),'native_footprints':len(refs),'segments':len(children(board,'segment')),'vias':len(children(board,'via')),'fixed_datums':fixed,'adc_retained':True,'keepouts_preserved':len(keepouts(board)),'nfc_copper_preserved':True,'rules_and_exclusions_unchanged':True,'relative_libraries_resolve':True,'files':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (records/'final-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))},indent=2))


if __name__=='__main__':main()
