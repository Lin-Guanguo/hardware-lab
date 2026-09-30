#!/usr/bin/env python3
"""Export one saved candidate to domestic JLC DFM files, never place an order."""
import argparse
import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from kicad_sexpr import children, prop, read


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--archive-name', default='NFC-V4-migration-diagnostic-gerber.zip')
    a = ap.parse_args()
    assert a.board.is_file() and not a.output.exists()
    a.output.mkdir(parents=True)
    gerbers = a.output / 'gerber'
    gerbers.mkdir()
    commands = [
        ['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts', '--use-drill-file-origin', '--precision', '6', '-o', str(gerbers), str(a.board)],
        ['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin', 'plot', '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'route', '--excellon-separate-th', '--generate-report', '--report-path', str(a.output / 'drill-report.txt'), '-o', str(gerbers), str(a.board)],
        ['kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '--use-drill-file-origin', '--exclude-dnp', '-o', str(a.output / 'kicad-pos.csv'), str(a.board)],
    ]
    fingerprint = hashlib.sha256(a.board.read_bytes()).hexdigest()
    for command in commands:
        subprocess.run(command, check=True)
    assert hashlib.sha256(a.board.read_bytes()).hexdigest() == fingerprint
    board = read(a.board)
    parts = {prop(f, 'Reference')[2]: f for f in children(board, 'footprint') if prop(f, 'MPN')}
    source = json.loads((Path(__file__).resolve().parents[1] / 'hardware/records/board-review-d-schematic.enet').read_text())
    source = {c['props']['Designator']: c['props'] for c in source['components'].values() if c['props'].get('Designator')}
    pos = list(csv.DictReader((a.output / 'kicad-pos.csv').open()))
    assert {r['Ref'] for r in pos} == set(parts), 'SMT BOM and position references differ'
    groups = {}
    cpl = []
    for row in pos:
        ref = row['Ref']
        f = parts[ref]
        mpn, supplier = prop(f, 'MPN')[2], prop(f, 'LCSC')[2]
        assert (mpn, supplier) == (source[ref]['Manufacturer Part'], source[ref]['Supplier Part'])
        package = source[ref]['Supplier Footprint']
        comment = source[ref]['Name']
        key = (comment, package, supplier)
        groups.setdefault(key, []).append(ref)
        cpl.append({'Designator': ref, 'Footprint': package, 'Mid X': row['PosX'], 'Mid Y': row['PosY'],
                    'Layer': {'top': 'T', 'bottom': 'B'}[row['Side']],
                    'Rotation': f"{float(row['Rot']) % 360:.3f}", 'Comment': comment})
    bom = [{'Comment': key[0], 'Designator': ','.join(refs), 'Footprint': key[1], 'Quantity': len(refs), '嘉立创元件编号': key[2]} for key, refs in groups.items()]
    for name, rows in [('BOM.csv', bom), ('CPL.csv', cpl)]:
        with (a.output / name).open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    assert Path(a.archive_name).name == a.archive_name and a.archive_name.endswith('.zip')
    with zipfile.ZipFile(a.output / a.archive_name, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(gerbers.iterdir()):
            z.write(p, p.name)
    manifest = {'board_sha256': fingerprint, 'board': str(a.board), 'purpose': 'Migration/manufacturing diagnostic only; not for fabrication',
                'origin_mm': [110, 130], 'units': 'mm', 'side_mapping': {'top': 'T', 'bottom': 'B'},
                'rotation_conversion': 'KiCad degrees modulo 360; no unverified vendor-specific offsets applied',
                'bom_groups': len(bom), 'placed_parts': len(pos), 'commands': commands,
                'format_source': 'https://www.jlc.com/portal/server_guide_48022.html',
                'format_source_updated': '2026-08-11',
                'files': {str(p.relative_to(a.output)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.output.rglob('*')) if p.is_file()}}
    (a.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'bom_groups': len(bom), 'parts': len(pos), 'board_sha256': fingerprint}))


if __name__ == '__main__':
    main()
