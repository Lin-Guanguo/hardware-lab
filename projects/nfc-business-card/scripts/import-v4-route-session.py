#!/usr/bin/env python3
"""Import an SES into an isolated diagnostic, preserving native fixed RF copper."""
import argparse
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pcbnew

from kicad_sexpr import child, children, prop, read, write

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('source', type=Path)
ap.add_argument('session', type=Path)
ap.add_argument('output', type=Path)
ap.add_argument('--preserve-ground', action='store_true')
a = ap.parse_args()
assert 'artifacts' in a.output.resolve().parts
assert not a.output.exists()
shutil.copytree(a.source, a.output, ignore=shutil.ignore_patterns('*.json', '~*'))
filename = 'NFC-Card-V4.kicad_pcb'
b = pcbnew.LoadBoard(str(a.output / filename))
assert pcbnew.ImportSpecctraSES(b, str(a.session))
pcbnew.SaveBoard(str(a.output / filename), b)
before, after = read(a.source / filename), read(a.output / filename)
refs = lambda board: {prop(f, 'Reference')[2]: child(f, 'at') for f in children(board, 'footprint')}
assert refs(before) == refs(after), 'SES changed placement'
preserved_nets={'NFC1_TBD','GND'} if a.preserve_ground else {'NFC1_TBD'}
rf = lambda item: isinstance(item, list) and item[0] in ('segment', 'via') and child(item, 'net')[-1] in preserved_nets
after[:] = [x for x in after if not rf(x)]
after.extend(copy.deepcopy(x) for x in before if rf(x))
write(a.output / filename, after)
record = {'session_sha256': hashlib.sha256(a.session.read_bytes()).hexdigest(),
    'source_sha256': hashlib.sha256((a.source / filename).read_bytes()).hexdigest(),
    'placement_unchanged': True, 'preserved_native_nets': sorted(preserved_nets),
    'native_RF_objects_retained': sum(isinstance(x,list) and x[0] in ('segment','via') and child(x,'net')[-1]=='NFC1_TBD' for x in before),
    'native_preserved_copper_objects':sum(rf(x) for x in before),
    'minimum_non_RF_track_width_mm': min(float(child(x, 'width')[1]) for x in children(after, 'segment') if child(x, 'net')[-1]!='NFC1_TBD')}
(a.output / 'import.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
