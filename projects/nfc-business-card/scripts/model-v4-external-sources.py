#!/usr/bin/env python3
"""Model the external USB source and SWD probe without adding PCB components."""
import argparse
import copy
import json
import uuid
from pathlib import Path

from kicad_sexpr import Quoted as Q, child, children, parse, prop, read, write


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('project', type=Path)
    args = ap.parse_args()
    path = args.project / 'NFC-Card-V4.kicad_sch'
    assert not list(args.project.glob('~*.kicad_sch.lck'))
    root = read(path)
    assert not children(root, 'symbol'), 'External models already present or root changed'
    lib = read(args.project / 'NFC_V4.kicad_sym')
    uid = str(child(root, 'uuid')[1])
    definitions = [
        ('ExternalUSBSource', 'XUSB1', 40.64, 142.24, [('VBUS', 'power_out', 'USB_VBUS'), ('GND', 'power_out', 'GND')]),
        ('ExternalSWDProbe', 'XDBG1', 116.84, 142.24, [('VTREF', 'power_in', 'VDD_3V3'), ('GND', 'power_in', 'GND'), ('SWDIO', 'bidirectional', 'SWDIO'), ('SWDCLK', 'output', 'SWDCLK'), ('RESET_N', 'open_collector', 'NRESET')]),
    ]
    records = []
    for name, ref, x, y, pins in definitions:
        definition = parse(f'''(symbol "{name}"
          (pin_names (offset 0.508)) (exclude_from_sim yes) (in_bom no) (on_board no)
          (property "Reference" "X" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
          (property "Value" "{name}" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
          (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
          (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
          (symbol "{name}_0_1" (rectangle (start -12.7 2.54) (end 12.7 {-5.08 * (len(pins)-1)-2.54}) (stroke (width 0.254) (type default)) (fill (type background)))))''')
        body = ['symbol', Q(name + '_1_1')]
        instance_id = str(uuid.uuid4())
        instance = parse(f'''(symbol (lib_id "NFC_V4:{name}") (at {x} {y} 0) (unit 1)
          (exclude_from_sim yes) (in_bom no) (on_board no) (dnp no)
          (uuid "{instance_id}")
          (property "Reference" "{ref}" (at {x} {y-7.62} 0) (effects (font (size 1.27 1.27))))
          (property "Value" "{name}" (at {x} {y-5.08} 0) (effects (font (size 1.27 1.27))))
          (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))
          (instances (project "NFC-Card-V4" (path "/{uid}" (reference "{ref}") (unit 1)))))''')
        for i, (pin_name, kind, net) in enumerate(pins):
            body.append(parse(f'''(pin {kind} line (at 17.78 {-5.08*i} 180) (length 5.08)
              (name "{pin_name}" (effects (font (size 1.27 1.27))))
              (number "{i+1}" (effects (font (size 1.27 1.27)))))'''))
            instance.append(['pin', Q(str(i+1)), ['uuid', Q(str(uuid.uuid4()))]])
            root.append(parse(f'''(global_label "{net}" (shape bidirectional) (at {x+17.78} {y+5.08*i} 0)
              (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uuid.uuid4()}")
              (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x+17.78} {y+5.08*i} 0) (effects (font (size 1.27 1.27)) (hide yes))))'''))
        definition.append(body)
        lib.append(copy.deepcopy(definition))
        definition[1] = Q('NFC_V4:' + name)
        child(root, 'lib_symbols').append(definition)
        root.append(instance)
        records.append({'reference': ref, 'on_board': False, 'in_bom': False, 'pins': pins})
    root.append(parse(f'''(text "External equipment only: USB host powers J1 VBUS/GND. SWD probe connects TP1-TP5; VTREF is an input.\nThese symbols assert source topology, not voltage protection, USB compliance, or simultaneous attachment."
      (at 25 193 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uuid.uuid4()}"))'''))
    child(child(root, 'title_block'), 'title')[1] = Q('NFC Card V4 - phase 2 routing candidate')
    child(child(root, 'title_block'), 'comment')[2] = Q('NOT FOR FABRICATION - See kicad-v4-phase2.md')
    write(path, root)
    write(args.project / 'NFC_V4.kicad_sym', lib)
    (args.project / 'external-source-model.json').write_text(json.dumps(records, indent=2)+'\n')


if __name__ == '__main__':
    main()
