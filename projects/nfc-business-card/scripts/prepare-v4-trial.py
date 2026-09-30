#!/usr/bin/env python3
"""Create a self-contained V4 candidate and audit symbol pin electrical types."""
import argparse
import copy
import json
import shutil
import uuid
from pathlib import Path

from kicad_sexpr import Quoted as Q, child, children, prop, read, remove, walk, write


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('output', type=Path)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    for p in a.source.iterdir():
        if p.suffix in ('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_sym', '.kicad_dru') or p.name in ('fp-lib-table', 'sym-lib-table'):
            shutil.copy2(p, a.output / p.name)
        elif p.suffix == '.pretty':
            shutil.copytree(p, a.output / p.name)
    schemas = {p: read(p) for p in a.output.glob('*.kicad_sch')}
    by_name = {}
    for sch in schemas.values():
        for sym in children(sch, 'symbol'):
            by_name[str(child(sym, 'lib_id')[1]).split(':')[-1]] = prop(sym, 'Reference')[2]
    # Types follow TI pin-function tables and Raytac's module pin table.
    # BAT is bidirectional power, and TS/MR is an analog bidirectional interface.
    maps = {
        'U2': dict(zip(map(str, range(1, 12)), ['power_out', 'passive', 'open_collector', 'input', 'power_in', 'bidirectional', 'bidirectional', 'bidirectional', 'open_collector', 'power_in', 'power_in'])),
        'U3': {'1': 'power_in', '2': 'power_in', '3': 'input', '4': 'no_connect', '5': 'power_out'},
        'U4': {'1': 'power_in', '2': 'power_in', '3': 'input', '4': 'no_connect', '5': 'passive', '6': 'power_out'},
    }
    library = read(a.output / 'NFC_V4.kicad_sym')
    definitions = {}
    audit = []
    for sch in schemas.values():
        cache = child(sch, 'lib_symbols')
        cache[:] = [cache[0]] + [s for s in children(cache, 'symbol') if str(s[1]).split(':')[-1] in by_name]
        for definition in children(cache, 'symbol'):
            name = str(definition[1]).split(':')[-1]
            ref = by_name[name]
            for pin in walk(definition, 'pin'):
                number, pin_name = child(pin, 'number')[1], child(pin, 'name')[1]
                old = pin[1]
                if ref in maps:
                    pin[1] = maps[ref][number]
                elif ref == 'U1':
                    if number in ('1', '2', '15', '33', '55', '28', '30', '32'):
                        pin[1] = 'power_in'
                    elif number == '53':
                        pin[1] = 'input'
                    elif number == '31':
                        pin[1] = 'passive'
                    else:
                        pin[1] = 'bidirectional'
                elif ref.startswith(('R', 'C', 'L', 'D', 'J', 'SW')) or ref in ('U5', 'U6'):
                    pin[1] = 'passive'
                elif ref.startswith('Q'):
                    # A transistor primitive has no logic-output drive model.
                    pin[1] = 'passive'
                audit.append({'symbol': name, 'pin': number, 'name': pin_name, 'imported': old, 'type': pin[1]})
            if prop(definition, 'Footprint'):
                prop(definition, 'Footprint')[2] = Q('')
            definitions[name] = copy.deepcopy(definition)
            definitions[name][1] = Q(name)
        for sym in children(sch, 'symbol'):
            if prop(sym, 'Reference')[2] == 'J1':
                for y in ('59.69', '74.93'):
                    sch.append(['no_connect', ['at', '53.34', y], ['uuid', Q(str(uuid.uuid4()))]])
    # Use the actual cached symbol geometry, including the corrected USB mapping.
    library[:] = [x for x in library if not (isinstance(x, list) and x[0] == 'symbol')]
    library.extend(definitions.values())
    write(a.output / 'NFC_V4.kicad_sym', library)
    for p, sch in schemas.items():
        write(p, sch)
    (a.output / 'symbol-type-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print(a.output)


if __name__ == '__main__':
    main()
