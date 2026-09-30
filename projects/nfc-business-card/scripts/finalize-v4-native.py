#!/usr/bin/env python3
"""Restore invariant library geometry after IPC transforms; preserve trial copper."""
import argparse
import copy
import json
import math
import shutil
from pathlib import Path

from kicad_sexpr import child, children, prop, read, remove, write
from v4_paste import rebuild_paste


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('target', type=Path)
    ap.add_argument('source', type=Path)
    ap.add_argument('d_gerber', type=Path)
    ap.add_argument('record', type=Path)
    a = ap.parse_args()
    target, source = a.target, a.source
    assert not list(target.glob('~*.kicad_pcb.lck')), 'Close PCB Editor before restoring local library geometry'
    board_file = target / 'NFC-Card-V4.kicad_pcb'
    backup = a.record.with_suffix('.before.kicad_pcb')
    assert not backup.exists(), 'Preserve the first diagnostic state'
    shutil.copy2(board_file, backup)
    board, reference = read(board_file), read(source / board_file.name)
    refs = {str(prop(f, 'Reference')[2]): f for f in children(reference, 'footprint')}
    maximum_pad_error = 0
    for fp in children(board, 'footprint'):
        ref = str(prop(fp, 'Reference')[2])
        original = refs[ref]
        oa, na = child(original, 'at'), child(fp, 'at')
        delta = (float(na[3]) if len(na) > 3 else 0) - (float(oa[3]) if len(oa) > 3 else 0)
        originals = {str(p[1]): p for p in children(original, 'pad')}
        for p in children(fp, 'pad'):
            op = originals[str(p[1])]
            old_at, new_at = child(op, 'at'), child(p, 'at')
            error = math.dist(list(map(float, old_at[1:3])), list(map(float, new_at[1:3])))
            assert error < .003, (ref, p[1], error)
            maximum_pad_error = max(maximum_pad_error, error)
            for tag in ('at', 'size', 'drill', 'roundrect_rratio', 'layers', 'solder_mask_margin'):
                remove(p, tag)
                if child(op, tag):
                    p.append(copy.deepcopy(child(op, tag)))
            at = child(p, 'at')
            angle = (float(old_at[3]) if len(old_at) > 3 else 0) + delta
            at[:] = at[:3] + [str(round(angle % 360, 6))]
        # kicad-python 0.8.0 displaced imported arc-based fp_poly graphics when
        # moving/rotating footprints. The original local graphics are invariant.
        fp[:] = [n for n in fp if not (isinstance(n, list) and n[0].startswith('fp_'))]
        fp.extend(copy.deepcopy(n) for n in original if isinstance(n, list) and n[0].startswith('fp_'))
    paste = rebuild_paste(board, reference, a.d_gerber)
    write(board_file, board)
    for file in (source / 'NFC_V4.pretty').glob('*.kicad_mod'):
        shutil.copy2(file, target / 'NFC_V4.pretty' / file.name)
    result = {'maximum_ipc_pad_local_error_mm': maximum_pad_error,
              'restored_graphics_from': str(source), 'paste_openings': len(paste),
              'note': 'Copper geometry is preserved; imported local graphics and exact stencil apertures restored.'}
    a.record.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
