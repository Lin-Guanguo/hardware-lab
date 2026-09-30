#!/usr/bin/env python3
"""Reconcile a closed native EasyEDA import against the frozen D evidence.

The resulting board is a migration diagnostic, not a new routed design.
Refuses to overwrite an existing output directory.
"""
import argparse
import copy
import hashlib
import json
import math
import sys
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from gerber_geometry import flashes, positive_regions
from kicad_sexpr import Quoted as Q, child, children, dumps, parse, prop, read, remove, set_child, walk, write
from v4_paste import rebuild_paste

PROJECT = Path(__file__).resolve().parents[1]
RECORDS = PROJECT / 'hardware/records'
NAME = 'NFC-Card-V4'
LIB = 'NFC_V4'


def uid():
    return Q(str(uuid.uuid4()))


def xy(pad, fp):
    at = child(fp, 'at')
    x, y = map(float, at[1:3])
    angle = math.radians(float(at[3]) if len(at) > 3 else 0)
    px, py = map(float, child(pad, 'at')[1:3])
    return x + px * math.cos(angle) + py * math.sin(angle), y - px * math.sin(angle) + py * math.cos(angle)


def property_value(node, name, value):
    p = prop(node, name)
    if p:
        p[2] = Q(value)
    else:
        node.append(['property', Q(name), Q(value), ['at', '0', '0', '0'],
                     ['layer', Q('F.Fab')], ['hide', 'yes'],
                     ['effects', ['font', ['size', '1', '1']]]])


def normalized_footprint(fp):
    f = copy.deepcopy(fp)
    angle = float(child(f, 'at')[3]) if len(child(f, 'at')) > 3 else 0
    remove(f, 'at', 'uuid', 'path', 'sheetname', 'sheetfile')
    f[:] = [x for x in f if not (isinstance(x, list) and x[0] == 'property' and x[1] not in ('Reference', 'Value'))]
    for item in f:
        if not isinstance(item, list):
            continue
        remove(item, 'uuid', 'net', 'pinfunction', 'pintype')
        at = child(item, 'at')
        if at:
            local_angle = (float(at[3]) if len(at) > 3 else 0) - angle
            at[:] = at[:3] + [str(round((local_angle + 180) % 360 - 180, 6))]
    property_value(f, 'Reference', 'REF**')
    property_value(f, 'Value', str(f[1]).split(':')[-1])
    # Reference placements imported as per-instance annotations are not library geometry.
    for name in ('Reference', 'Value'):
        p = prop(f, name)
        set_child(p, 'at', '0', '-2' if name == 'Reference' else '2', '0')
        set_child(p, 'layer', Q('F.Fab'))
        set_child(p, 'hide', 'yes')
    f.insert(2, ['version', '20260206'])
    f.insert(3, ['generator', Q('pcbnew')])
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-dir', required=True, type=Path)
    ap.add_argument('--d-gerber-dir', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    a = ap.parse_args()
    assert not a.output.exists(), 'Use a fresh candidate directory'
    assert not list(a.import_dir.glob('~*.lck')), 'Close the imported project before reading it'
    snapshot_path = RECORDS / 'board-review-d-snapshot.json'
    assert hashlib.sha256(snapshot_path.read_bytes()).hexdigest() == 'b41283e216670f814a63f064995077f8df891c49a579c98a16db24af93236a0c'
    snapshot = json.loads(snapshot_path.read_text())
    enet = json.loads((RECORDS / 'board-review-d-schematic.enet').read_text())
    parts = {c['props']['Designator']: c for c in enet['components'].values()
             if c['props'].get('Add into BOM') == 'yes' and c['props'].get('Designator')}
    old_pins = {(c['ref'], p['number']): p for c in json.loads((RECORDS / 'board-review-d-pcb-pins.json').read_text()) for p in c['pins']}
    assert len(parts) == 66 and len(old_pins) == 256
    raw = a.import_dir / 'NFC-Card-D-export'
    board = read(raw.with_suffix('.kicad_pcb'))
    set_child(child(board, 'general'), 'thickness', '0.8')
    set_child(child(board, 'setup'), 'pad_to_mask_clearance', '0.05')
    mask = {side: flashes((a.d_gerber_dir / file).read_text()) for side, file in
            [('F', 'Gerber_TopSolderMaskLayer.GTS'), ('B', 'Gerber_BottomSolderMaskLayer.GBS')]}
    footprints = {}
    libraries = {}
    audit = {'source_snapshot_sha256': hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
             'coordinate_transform_mm': {'x': '110 + source_mil * 0.0254', 'y': '130 - source_mil * 0.0254'},
             'part_pins': [], 'standalone_pads': [], 'apertures': [], 'library_variants': [],
             'note': 'Reconciled D geometry for migration and manufacturing diagnostics; not V4 routing.'}
    for fp in children(board, 'footprint'):
        ref = str(prop(fp, 'Reference')[2])
        standalone = not ref
        if standalone:
            px, py = xy(children(fp, 'pad')[0], fp)
            matches = [p for p in snapshot['pads'] if math.dist((p['x'] * .0254, p['y'] * .0254), (px - 110, 130 - py)) < .003]
            assert len(matches) == 1
            src = matches[0]
            source_id = src['id']
            ref = src['number']
            property_value(fp, 'Reference', ref)
            property_value(fp, 'Value', 'PCB contact')
            child(fp, 'layer')[1] = Q('B.Cu' if src['layer'] == 2 else 'F.Cu')
            set_child(fp, 'attr', 'smd', 'exclude_from_pos_files', 'exclude_from_bom')
            # These exposed contacts are deliberately hand-soldered / probed.
            audit['standalone_pads'].append({'ref': ref, 'source_id': source_id, 'source_number': src['number'], 'kicad_pin': '1', 'net': src['net']})
        else:
            assert ref in parts
            for name, source_name in [('Value', 'Name'), ('MPN', 'Manufacturer Part'), ('LCSC', 'Supplier Part'), ('Manufacturer', 'Manufacturer'), ('Manufacturer Part', 'Manufacturer Part')]:
                property_value(fp, name, parts[ref]['props'].get(source_name, ''))
            set_child(fp, 'attr', 'smd')
        # Export contains missing placeholder STEP paths, not usable project models.
        remove(fp, 'model')
        # Imported custom paste polygons can overlap pad-generated paste. Rebuild
        # each opening from the frozen, independently measured D Gerber instead.
        fp[:] = [x for x in fp if not (isinstance(x, list) and x[0].startswith('fp_') and child(x, 'layer') and str(child(x, 'layer')[1]).endswith('.Paste'))]
        for pad in children(fp, 'pad'):
            px, py = xy(pad, fp)
            ox, oy = px - 110, 130 - py
            number = str(pad[1])
            if standalone:
                pad[1] = Q('1')
            else:
                old = old_pins[(ref, number)]
                net = str(child(pad, 'net')[-1]) if child(pad, 'net') else ''
                error = math.dist((ox, oy), (old['x'] * .0254, old['y'] * .0254))
                assert error < .003 and net == old['net'], (ref, number, net, old, error)
                audit['part_pins'].append({'ref': ref, 'pin': number, 'net': net, 'position_error_mm': error})
            side = 'B' if 'B.Cu' in child(pad, 'layers') else 'F'
            m = [g for x, y, g in mask[side] if math.dist((x, y), (ox, oy)) < .003]
            assert len(m) == 1, (ref, number, 'mask', len(m))
            w, h = map(float, child(pad, 'size')[1:3])
            angle = math.radians(float(child(pad, 'at')[3]) if len(child(pad, 'at')) > 3 else 0)
            bw, bh = abs(w * math.cos(angle)) + abs(h * math.sin(angle)), abs(w * math.sin(angle)) + abs(h * math.cos(angle))
            mx = (m[0].bounds[2] - m[0].bounds[0] - bw) / 2
            my = (m[0].bounds[3] - m[0].bounds[1] - bh) / 2
            assert abs(mx - my) < .002, (ref, number, mx, my)
            margin = round((mx + my) / 2, 6)
            set_child(pad, 'solder_mask_margin', str(margin))
            layers = child(pad, 'layers')
            layers[:] = [x for x in layers if not str(x).endswith('.Paste')]
            audit['apertures'].append({'ref': ref, 'pin': str(pad[1]), 'side': side, 'mask_margin_mm': margin})
        # Build libraries from actual board pads, including board-level overrides.
        base = str(fp[1]).split(':')[-1]
        lib = normalized_footprint(fp)
        lib[1] = Q(base)
        signature = dumps(lib)
        if base in libraries and dumps(libraries[base]) != signature:
            base += '_' + ref
            lib[1] = Q(base)
            audit['library_variants'].append(base)
        libraries[base] = lib
        fp[1] = Q(LIB + ':' + base)
        footprints[ref] = fp

    audit['paste_openings'] = rebuild_paste(board, board, a.d_gerber_dir)
    libraries = {}
    for fp in children(board, 'footprint'):
        base = str(fp[1]).split(':')[-1]
        lib = normalized_footprint(fp)
        lib[1] = Q(base)
        libraries[base] = lib

    # Importer maps all rule areas to blanket prohibitions, sometimes on Edge.Cuts.
    board[:] = [x for x in board if not (isinstance(x, list) and x[0] == 'zone' and child(x, 'keepout'))]
    for r in snapshot['regions']:
        numbers = [v for v in r['complexPolygon'] if isinstance(v, (int, float))]
        pts = [(round(110 + x * .0254, 6), round(130 - y * .0254, 6)) for x, y in zip(numbers[::2], numbers[1::2])]
        assert len(pts) == 5 and pts[0] == pts[-1], 'Review non-rectangular rule areas explicitly'
        rules = r['ruleType']
        zone = parse('(zone (net "") (layers "F.Cu") (name "") (hatch edge 0.5) (connect_pads (clearance 0.254)) (min_thickness 0.15) (filled_areas_thickness no) (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) (fill (thermal_gap 0.254) (thermal_bridge_width 0.25)))')
        if r['layer'] == 12:
            child(zone, 'layers').append(Q('B.Cu'))
        child(zone, 'name')[1] = Q('D-' + r['id'])
        zone.append(['uuid', uid()])
        ko = child(zone, 'keepout')
        set_child(ko, 'tracks', 'not_allowed' if 5 in rules else 'allowed')
        set_child(ko, 'vias', 'not_allowed' if 5 in rules else 'allowed')
        set_child(ko, 'pads', 'not_allowed' if 5 in rules else 'allowed')
        set_child(ko, 'footprints', 'not_allowed' if 2 in rules else 'allowed')
        zone.append(['polygon', ['pts', *[['xy', str(x), str(y)] for x, y in pts[:-1]]]])
        board.append(zone)
    for z in children(board, 'zone'):
        if not child(z, 'keepout'):
            set_child(child(z, 'connect_pads'), 'clearance', '0.254')
            remove(z, 'filled_polygon')

    a.output.mkdir(parents=True)
    (a.output / (LIB + '.pretty')).mkdir()
    for name, f in libraries.items():
        write(a.output / (LIB + '.pretty') / (name + '.kicad_mod'), f)

    root = read(raw.with_suffix('.kicad_sch'))
    root_uuid = child(root, 'uuid')[1]
    sheets = {prop(s, 'Sheetfile')[2]: (child(s, 'uuid')[1], prop(s, 'Sheetname')[2]) for s in children(root, 'sheet')}
    symbols = read(a.import_dir / 'NFC-Card-D-easyedapro.kicad_sym')
    # Keep imported electrical types for now; ERC findings remain visible until
    # a separately evidenced pin-type audit is complete.
    used_symbols = set()
    power_index = 0
    for file in a.import_dir.glob('*.kicad_sch'):
        sch = root if file.stem == raw.name else read(file)
        sch[:] = [x for x in sch if not (isinstance(x, list) and x[0] == 'symbol' and str(child(x, 'lib_id')[1]).split(':')[-1] in ('Short-Symbol', 'Drawing-Symbol_A4'))]
        for x in walk(sch, 'project'):
            x[1] = Q(NAME)
        for x in children(sch, 'label'):
            x[0] = 'global_label'
            x.insert(2, ['shape', 'bidirectional'])
        for x in children(sch, 'global_label'):
            if x[1] == 'NFC2_TBD':
                x[1] = Q('NFC1_TBD')
            if not prop(x, 'Intersheetrefs'):
                at = child(x, 'at')
                x.append(['property', Q('Intersheetrefs'), Q('${INTERSHEET_REFS}'),
                          ['at', at[1], at[2], '0'], ['hide', 'yes'],
                          ['effects', ['font', ['size', '1.27', '1.27']]]])
        for s in children(sch, 'symbol'):
            ref = prop(s, 'Reference')[2]
            lib_id = child(s, 'lib_id')
            lib_id[1] = Q(LIB + ':' + str(lib_id[1]).split(':')[-1])
            used_symbols.add(lib_id[1])
            if ref.startswith('#'):
                power_index += 1
                prop(s, 'Reference')[2] = Q(f'#PWR{power_index:03}')
                for r in walk(s, 'reference'):
                    r[1] = prop(s, 'Reference')[2]
                prop(s, 'Footprint')[2] = Q('')
                for tag in ('in_bom', 'on_board', 'in_pos_files'):
                    set_child(s, tag, 'no')
                continue
            assert ref in footprints, ref
            prop(s, 'Footprint')[2] = footprints[ref][1]
            for field in children(s, 'property'):
                if field[1] not in ('Reference', 'Value', 'Footprint'):
                    property_value(footprints[ref], str(field[1]), str(field[2]))
            path = '/' + root_uuid + '/' + sheets[file.name][0] + '/' + child(s, 'uuid')[1]
            set_child(footprints[ref], 'path', Q(path))
            set_child(footprints[ref], 'sheetname', Q(sheets[file.name][1]))
            set_child(footprints[ref], 'sheetfile', Q(file.name))
        for s in children(child(sch, 'lib_symbols'), 'symbol'):
            s[1] = Q(LIB + ':' + str(s[1]).split(':')[-1])
        if file.name.startswith('2_'):
            sch.append(parse('(text "NFC1 / NFC2 share a DC net through the continuous PCB winding. RF matching is unverified. Imported Short-Symbol replaced by explicit net naming." (at 85 137 0) (effects (font (size 1.1 1.1)) (justify left)))'))
            sch[-1].append(['uuid', uid()])
        name = NAME + '.kicad_sch' if file.stem == raw.name else file.name
        write(a.output / name, sch)
    # Standalone contacts are intentional board-only features, absent from SMT.
    # Their individual pin/net mappings are checked independently in the report.
    for item in audit['standalone_pads']:
        set_child(footprints[item['ref']], 'attr', 'smd', 'board_only', 'exclude_from_pos_files', 'exclude_from_bom')
    symbols[:] = [x for x in symbols if not (isinstance(x, list) and x[0] == 'symbol' and LIB + ':' + str(x[1]) not in used_symbols)]
    write(a.output / (LIB + '.kicad_sym'), symbols)
    for table, kind, uri in [('fp-lib-table', 'KiCad', LIB + '.pretty'), ('sym-lib-table', 'KiCad', LIB + '.kicad_sym')]:
        tag = 'fp_lib_table' if table.startswith('fp') else 'sym_lib_table'
        write(a.output / table, parse(f'({tag} (version 7) (lib (name "{LIB}") (type "{kind}") (uri "${{KIPRJMOD}}/{uri}") (options "") (descr "Frozen D import reconciled for V4")))'))
    config = json.loads(raw.with_suffix('.kicad_pro').read_text())
    config['meta']['filename'] = NAME + '.kicad_pro'
    rules = config['board']['design_settings']['rules']
    rules.update(min_clearance=.2, min_track_width=.15, min_copper_edge_clearance=.3,
                 min_via_diameter=.6, min_through_hole_diameter=.3, min_via_annular_width=.15)
    assert not config['board']['design_settings']['drc_exclusions']
    (a.output / (NAME + '.kicad_pro')).write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    (a.output / (NAME + '.kicad_dru')).write_text('(version 1)\n\n# Minimums mirror the frozen D constraint record; no exclusions.\n(rule "D copper clearance" (constraint clearance (min 0.2mm)))\n(rule "D board-edge clearance" (constraint edge_clearance (min 0.3mm)))\n')
    write(a.output / (NAME + '.kicad_pcb'), board)
    netlist = a.output / 'migration-netlist.xml'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(netlist), str(a.output / (NAME + '.kicad_sch'))], check=True)
    xml = ET.parse(netlist).getroot()
    pin_nets = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name'] for net in xml.find('nets') for n in net}
    assert {n.attrib['ref'] for n in xml.find('components')} == set(parts)
    for (ref, number), old in old_pins.items():
        net = pin_nets.get((ref, number), '')
        canonical = '' if net.startswith('unconnected-') else net
        assert canonical == old['net'], (ref, number, old['net'], net)
        pad = next(p for p in children(footprints[ref], 'pad') if p[1] == number)
        if net:
            set_child(pad, 'net', Q(net.replace('/', '{slash}')))
    audit['schematic_pin_network_mismatches'] = 0
    audit['intentional_unconnected_pin_count'] = sum(not p['net'] for p in old_pins.values())
    write(a.output / (NAME + '.kicad_pcb'), board)
    (a.output / 'migration-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(a.output), 'parts': len(parts), 'pins': len(audit['part_pins']), 'contacts': len(audit['standalone_pads']), 'libraries': len(libraries)}))


if __name__ == '__main__':
    main()
