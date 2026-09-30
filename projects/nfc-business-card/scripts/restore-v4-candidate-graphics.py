#!/usr/bin/env python3
"""Restore invariant local pad, graphic and paste geometry after IPC placement."""
import argparse
import copy
import json
from pathlib import Path

from kicad_sexpr import child, children, prop, read, remove, write

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('candidate', type=Path)
ap.add_argument('source', type=Path)
ap.add_argument('record', type=Path)
a = ap.parse_args()
assert not list(a.candidate.parent.glob('~*.kicad_pcb.lck')), 'Close the candidate editor first'
b, s = read(a.candidate), read(a.source)
refs = {prop(f, 'Reference')[2]: f for f in children(s, 'footprint')}
restored = []
for f in children(b, 'footprint'):
    ref = prop(f, 'Reference')[2]
    original = refs[ref]
    at, old_at = child(f, 'at'), child(original, 'at')
    delta = (float(at[3]) if len(at) > 3 else 0) - (float(old_at[3]) if len(old_at) > 3 else 0)
    for pad in children(f, 'pad'):
        old = next(x for x in children(original, 'pad') if x[1] == pad[1])
        for tag in ('at', 'size', 'drill', 'roundrect_rratio', 'layers', 'solder_mask_margin'):
            remove(pad, tag)
            if child(old, tag):
                pad.append(copy.deepcopy(child(old, tag)))
        pa = child(pad, 'at')
        pa[:] = pa[:3] + [str(((float(pa[3]) if len(pa) > 3 else 0) + delta) % 360)]
    f[:] = [x for x in f if not (isinstance(x, list) and x[0].startswith('fp_'))]
    f.extend(copy.deepcopy(x) for x in original if isinstance(x, list) and x[0].startswith('fp_'))
    restored.append(ref)
# This inherited restriction belongs to U5, not to the connector/antenna datum.
u5 = next(f for f in children(b, 'footprint') if prop(f, 'Reference')[2] == 'U5')
delta_xy = [float(x) - float(y) for x, y in zip(child(u5, 'at')[1:3], child(refs['U5'], 'at')[1:3])]
for z in children(b, 'zone'):
    if child(z, 'name') and child(z, 'name')[1] == 'D-3f291e373f46901a':
        original = next(x for x in children(s, 'zone') if child(x, 'name') == child(z, 'name'))
        for xy, old in zip(child(child(z, 'polygon'), 'pts')[1:], child(child(original, 'polygon'), 'pts')[1:]):
            xy[1:] = [str(float(v) + d) for v, d in zip(old[1:], delta_xy)]
write(a.candidate, b)
a.record.write_text(json.dumps({'source': str(a.source), 'restored_footprints': restored,
    'local_pad_graphics_paste_preserved': True, 'u5_no_pour_translation_mm': delta_xy}, indent=2) + '\n')
