#!/usr/bin/env python3
"""Apply an explicit placement/routing experiment to the open V4 board via IPC."""
import argparse
import json
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via
from kipy.geometry import Angle, Vector2
from kipy.proto.board import BoardLayer


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('plan', type=Path)
    a = ap.parse_args()
    plan = json.loads(a.plan.read_text())
    assert not plan.get('failures'), 'Resolve rejected paths or transitions before applying a plan'
    root = Path(__file__).resolve().parents[3]
    expected = (root / plan['board']).resolve()
    assert expected.is_relative_to(root / 'projects/nfc-business-card/hardware/kicad')
    board = KiCad(client_name='hardware-lab-v4', timeout_ms=15000).get_board()
    actual = (Path(board.document.project.path) / board.document.board_filename).resolve()
    assert actual == expected, (actual, expected)
    before = {'tracks': len(board.get_tracks()), 'vias': len(board.get_vias())}
    fps = {f.reference_field.text.value: f for f in board.get_footprints()}
    assert {'Q2', 'Q3', 'R20', 'R21', 'R22', 'R23', 'C25'}.issubset(fps)
    nets = {n.name: n for n in board.get_nets()}
    commit = board.begin_commit()
    try:
        if plan.get('clear_non_nfc_routing'):
            assert before['tracks'] == 912 and before['vias'] == 198, 'Expected untouched D routing for this one-time reset'
            board.remove_items([x for x in [*board.get_tracks(), *board.get_vias()] if x.net.name != 'NFC1_TBD'])
        for ref, (x, y, angle) in plan.get('placements', {}).items():
            f = fps[ref]
            f.orientation = Angle.from_degrees(angle)
            f.position = Vector2.from_xy_mm(x, y)
            board.update_items(f)
        if plan.get('remove_trial_ids'):
            from kipy.proto.common.types import KIID
            board.remove_items_by_id([KIID(value=x) for x in plan['remove_trial_ids']])
        objects = []
        for line in plan.get('routes', []):
            for start, end in zip(line['points'], line['points'][1:]):
                t = Track()
                t.start = Vector2.from_xy_mm(*start)
                t.end = Vector2.from_xy_mm(*end)
                t.width = round(line['width'] * 1e6)
                t.layer = BoardLayer.BL_F_Cu if line['layer'] == 'F.Cu' else BoardLayer.BL_B_Cu
                t.net = nets[line['net']]
                objects.append(t)
        for hole in plan.get('vias', []):
            v = Via()
            v.position = Vector2.from_xy_mm(*hole['at'])
            v.diameter = 600000
            v.drill_diameter = 300000
            v.net = nets[hole['net']]
            objects.append(v)
        created = board.create_items(objects) if objects else []
        board.push_commit(commit, plan['description'])
    except Exception:
        board.drop_commit(commit)
        raise
    board.refill_zones()
    board.save()
    result = {'plan': str(a.plan), 'board': str(expected), 'before': before,
              'after': {'tracks': len(board.get_tracks()), 'vias': len(board.get_vias())},
              'created_ids': [x.id.value for x in created]}
    output = root / plan['record']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
