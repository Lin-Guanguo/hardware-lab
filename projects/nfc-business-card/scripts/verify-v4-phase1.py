#!/usr/bin/env python3
"""Verify the saved phase-one trial against its frozen migration and route plans."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from kicad_sexpr import child, children, prop, read
from v4_geometry import geometry


def main():
    project = Path(__file__).resolve().parents[1]
    root = project / 'hardware/kicad/v4'
    records = project / 'hardware/records/kicad-v4'
    output = project / 'artifacts/kicad-v4'
    output.mkdir(parents=True, exist_ok=True)
    board, pads, objects, refs = geometry(root / 'NFC-Card-V4.kicad_pcb')
    baseline, old_pads, old_objects, old_refs = geometry(records / 'dfm-diagnostic-02/NFC-Card-V4.kicad_pcb')
    audit = json.loads((records / 'migration-audit.json').read_text())
    normalize = lambda net: '' if net.startswith('unconnected-') else net
    expected = {(n['ref'], n['pin']): n['net'] for n in audit['part_pins']}
    assert all(normalize(pads[ref + '.' + pin]['net']) == net for (ref, pin), net in expected.items())
    assert {k: normalize(v['net']) for k, v in pads.items()} == {k: normalize(v['net']) for k, v in old_pads.items()}
    netlist = output / 'phase1-netlist.xml'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(netlist), str(root / 'NFC-Card-V4.kicad_sch')], check=True)
    actual = {(n.attrib['ref'], n.attrib['pin']): normalize(net.attrib['name']) for net in ET.parse(netlist).findall('.//nets/net') for n in net.findall('node')}
    assert actual == expected, 'Native schematic pin mapping differs from reconciled D'
    plan = json.loads((root / 'reproduce-final-plan.json').read_text())
    moved = set(plan['placements'])
    fixed = set(refs) - moved
    assert all(max(abs(a - b) for a, b in zip(refs[r], old_refs[r])) < .00001 for r in fixed)
    assert all(max(abs(a - b) for a, b in zip(refs[r], plan['placements'][r])) < .00001 for r in moved)
    copper = lambda o: (o['kind'], o['net'], tuple(o['layers']), o['shape'].wkb_hex)
    assert {copper(o) for o in objects if o['net'] == 'NFC1_TBD'} == {copper(o) for o in old_objects if o['net'] == 'NFC1_TBD'}
    edges = lambda tree: [n for n in tree if isinstance(n, list) and n[0].startswith('gr_') and child(n, 'layer') and child(n, 'layer')[1] == 'Edge.Cuts']
    assert edges(board) == edges(baseline)
    # Regenerating the diagnostic assigns fresh zone UUIDs; compare the actual rules.
    keepouts = lambda tree: {child(z, 'name')[1]: [n for n in z if not isinstance(n, list) or n[0] != 'uuid'] for z in children(tree, 'zone') if child(z, 'keepout')}
    assert keepouts(board) == keepouts(baseline)
    assert float(child(child(board, 'general'), 'thickness')[1]) == .8
    assert len(children(board, 'segment')) == 74 + sum(len(r['points']) - 1 for r in plan['routes']) == 174
    assert len(children(board, 'via')) == 6 + len(plan['vias']) == 22
    source = json.loads((project / 'hardware/records/board-review-d-schematic.enet').read_text())
    parts = {c['props']['Designator']: c['props'] for c in source['components'].values() if c['props'].get('Designator')}
    for fp in children(board, 'footprint'):
        ref = prop(fp, 'Reference')[2]
        if ref in parts:
            assert prop(fp, 'MPN')[2] == parts[ref]['Manufacturer Part']
            assert prop(fp, 'LCSC')[2] == parts[ref]['Supplier Part']
        assert (root / 'NFC_V4.pretty' / (fp[1].split(':')[1] + '.kicad_mod')).exists()
    for file in (root / 'fp-lib-table', root / 'sym-lib-table'):
        for lib in children(read(file), 'lib'):
            uri = child(lib, 'uri')[1]
            assert uri.startswith('${KIPRJMOD}/') and (root / uri.replace('${KIPRJMOD}/', '')).exists()
    files = [f for f in root.glob('*.kicad_*') if f.suffix in ('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_dru', '.kicad_sym')]
    files += list((root / 'NFC_V4.pretty').glob('*.kicad_mod')) + [root / 'fp-lib-table', root / 'sym-lib-table']
    result = {'status': 'pass', 'parts': len(parts), 'part_pins': len(expected), 'pads': len(pads),
              'u1_pads': len([n for n in pads if n.startswith('U1.')]), 'pin_network_mismatches': 0,
              'fixed_footprints': sorted(fixed), 'moved_footprints': sorted(moved),
              'nfc_copper_preserved': True, 'edge_cuts_preserved': True, 'keepouts_preserved': len(keepouts(board)),
              'relative_libraries_resolve': True, 'bom_mpn_supplier_matches': len(parts),
              'segments': 174, 'vias': 22, 'new_vias': 16,
              'design_files': {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    (records / 'final-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if not isinstance(v, (list, dict))}))


if __name__ == '__main__':
    main()
