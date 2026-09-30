#!/usr/bin/env python3
"""Build one static geometric counterexample; never run a route search or edit V4."""
import hashlib
import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / 'projects/nfc-business-card'
SOURCE = PROJECT / 'hardware/kicad/v4-phase3'
OUT = PROJECT / 'artifacts/kicad-v4-phase3/j2-witness'
OUT.mkdir(exist_ok=True)
spec = json.loads((SOURCE / 'wholeboard-orthogonal-lanes-spec.json').read_text())
plan = json.loads((SOURCE / 'wholeboard-orthogonal-lanes-spec-plan.json').read_text())
board = pcbnew.LoadBoard(str(ROOT / spec['model_board']))
nets = {n.GetNetname(): n.GetNetCode() for n in board.GetNetsByNetcode().values()}
# Retain native pads, outline, keepouts, NFC, every assigned via and the
# completed local prefix. Exclude ALL six screen fanouts, not only failures.
first = next(i for i, q in enumerate(spec['paths']) if ' to J2.' in q['name'] and q['name'].endswith(' channel'))
prefix = {q['name'] for q in spec['paths'][:first]}
for q in plan['routes']:
    if q['name'] not in prefix:
        continue
    for a, b in zip(q['points'], q['points'][1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(*(round(v * 1e6) for v in a)))
        t.SetEnd(pcbnew.VECTOR2I(*(round(v * 1e6) for v in b)))
        t.SetLayer(pcbnew.F_Cu if q['layer'] == 'F.Cu' else pcbnew.B_Cu)
        t.SetWidth(round(q['width'] * 1e6)); t.SetNetCode(nets[q['net']]); board.Add(t)
for v in spec['vias']:
    t = pcbnew.PCB_VIA(board)
    t.SetPosition(pcbnew.VECTOR2I(*(round(c * 1e6) for c in v['at'])))
    t.SetWidth(600000); t.SetDrill(300000); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    t.SetNetCode(nets[v['net']]); board.Add(t)
# Closed-form nested fanout: each lane turns only at its own endpoint Y.
witness = []
for q in spec['paths']:
    if not (' to J2.' in q['name'] and q['name'].endswith(' north')):
        continue
    a, b = q['through']
    pts = [[a[0], 111.1], [a[0], b[1]], b]
    uuids = []
    for start, end in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(*(round(c * 1e6) for c in start)))
        t.SetEnd(pcbnew.VECTOR2I(*(round(c * 1e6) for c in end)))
        t.SetWidth(150000); t.SetLayer(pcbnew.B_Cu); t.SetNetCode(nets[q['net']]); board.Add(t)
        uuids.append(t.m_Uuid.AsString())
    witness.append({'name': q['name'], 'net': q['net'], 'points': pts, 'uuids': uuids})
path = OUT / 'j2-witness.kicad_pcb'
pcbnew.SaveBoard(str(path), board)
for ext in ('.kicad_pro', '.kicad_dru'):
    (OUT / ('j2-witness' + ext)).write_bytes((SOURCE / ('NFC-Card-V4' + ext)).read_bytes())
record = {'scope': 'Static six-lane B.Cu channel and J2 north fanout ONLY. MCU south approaches removed and NOT proven. No placement changes or candidate adoption.',
          'source_spec': str((SOURCE / 'wholeboard-orthogonal-lanes-spec.json').relative_to(ROOT)),
          'model_sha256': hashlib.sha256((ROOT / spec['model_board']).read_bytes()).hexdigest(),
          'retained_local_request_count': len(prefix), 'witness': witness,
          'route_search_executed': False, 'production_board_modified': False}
(PROJECT / 'hardware/records/kicad-v4-phase3/layout-review/j2-witness.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'board': str(path), 'witness_segments': sum(len(x['uuids']) for x in witness)}))
