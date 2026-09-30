#!/usr/bin/env python3
"""Remove import-only dangling wire stubs, requiring an identical pin netlist."""
import json
import math
import copy
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from kicad_sexpr import child, children, read, write


def main():
    project = Path(__file__).resolve().parents[1]
    target = project / 'hardware/kicad/v4'
    output = project / 'artifacts/kicad-v4'
    root = target / 'NFC-Card-V4.kicad_sch'
    assert not list(target.glob('~*.lck')), 'Close KiCad before schematic edits'
    report = output / 'stub-erc-before.json'
    subprocess.run(['kicad-cli', 'sch', 'erc', '--format', 'json', '-o', str(report), str(root)], check=True)
    violations = [v for s in json.loads(report.read_text())['sheets'] for v in s['violations']]
    ids = {i['uuid']: i['pos'] for v in violations if v['type'] == 'unconnected_wire_endpoint' for i in v['items']}
    originals = {p: p.read_text() for p in target.glob('*.kicad_sch')}

    def netlist(name):
        file = output / name
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(file), str(root)], check=True)
        tree = ET.parse(file)
        return {(n.attrib['ref'], n.attrib['pin']): net.attrib['name'] for net in tree.findall('.//nets/net') for n in net.findall('node')}

    before = netlist('stubs-before.xml')
    removed = []
    try:
        for p in originals:
            schema = read(p)
            stubs = [n for n in schema if isinstance(n, list) and n[0] == 'wire' and child(n, 'uuid')[1] in ids]
            for wire in stubs:
                points = child(wire, 'pts')[1:]
                a, b = [tuple(map(float, xy[1:3])) for xy in points]
                labels = [tuple(map(float, child(l, 'at')[1:3])) for l in children(schema, 'global_label')]
                on_wire = [p for p in labels if abs(math.dist(a, p) + math.dist(p, b) - math.dist(a, b)) < 1e-5]
                assert len(on_wire) == 1
                reported = ids[child(wire, 'uuid')[1]]
                # This KiCad build reports ERC positions at 1/100 native scale.
                candidates = [(scale, i) for scale in (1, 100) for i, pt in enumerate((a, b)) if math.dist(pt, (reported['x'] * scale, reported['y'] * scale)) < 1e-5]
                assert len(candidates) == 1
                removed.append({'sheet': p.name, 'wire_uuid': child(wire, 'uuid')[1], 'before': copy.deepcopy(child(wire, 'pts')), 'trim_to_label': on_wire[0]})
                index = candidates[0][1]
                if math.dist(on_wire[0], (a, b)[1 - index]) < 1e-5:
                    schema.remove(wire)
                else:
                    points[index][1:3] = [str(v) for v in on_wire[0]]
            if stubs:
                write(p, schema)
        after = netlist('stubs-after.xml')
        assert before == after, 'Pin connectivity changed; restoring original sheets'
    except Exception:
        for p, text in originals.items():
            p.write_text(text)
        raise
    result = {'removed': removed, 'identical_pin_netlist': True, 'pins_in_netlist': len(before)}
    (project / 'hardware/records/kicad-v4/schematic-stubs.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'removed': len(removed), 'pins': len(before), 'identical': True}))


if __name__ == '__main__':
    main()
