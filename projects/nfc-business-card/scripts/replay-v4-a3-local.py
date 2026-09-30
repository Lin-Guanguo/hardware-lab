#!/usr/bin/env python3
"""Reproduce the accepted A3 delta in a new project directory and run native DRC."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from kicad_sexpr import child, parse, read, write

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('output', type=Path)
a = ap.parse_args()
project = Path(__file__).resolve().parents[1]
repo = project.parents[1]
delta = json.loads((project/'hardware/records/kicad-v4-option-a3/accepted-native-delta.json').read_text())
source = repo/delta['source']
assert hashlib.sha256(source.read_bytes()).hexdigest() == delta['source_sha256']
assert not a.output.exists(), 'Use a new directory; comparisons and existing work must not be overwritten'
a.output.mkdir(parents=True)
for p in source.parent.iterdir():
    if p.suffix in ['.kicad_pro', '.kicad_dru', '.kicad_sch', '.kicad_sym'] or p.name in ['fp-lib-table', 'sym-lib-table']:
        shutil.copy2(p, a.output/p.name)
    elif p.suffix == '.pretty':
        shutil.copytree(p, a.output/p.name)
board = read(source)
items = [parse(x) for x in delta['replace_items']]
replacements = {child(x, 'uuid')[1]: x for x in items}
remove = set(delta['remove_ids']) | replacements.keys()
board[:] = [x for x in board if not (isinstance(x, list) and x[0] in ['segment', 'via', 'footprint'] and child(x, 'uuid')[1] in remove)]
board.extend(items)
target = a.output/source.name
write(target, board)
subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '--format', 'json',
                '--schematic-parity', '-o', str(a.output/'drc.json'), str(target)], check=True)
result = json.loads((a.output/'drc.json').read_text())
assert len(result['unconnected_items']) == 7
assert not result['schematic_parity']
assert len(result['violations']) == 58
print('Replayed A3: 58 DRC, 7 unconnected, parity 0; not a manufacturing release')
