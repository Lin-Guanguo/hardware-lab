#!/usr/bin/env python3
"""Create and exercise a disposable KiCad IPC fixture, never a product board."""

import argparse
import json
from pathlib import Path
import sys
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["create", "edit", "verify"])
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    directory = args.directory.resolve()
    if not directory.is_relative_to(root / ".cache"):
        parser.error("Fixture directory must be inside this repository's .cache")
    board_path = directory / "ipc-smoke.kicad_pcb"
    marker = directory / "hardware-lab-smoke.json"

    if args.mode == "create":
        directory.mkdir(parents=True, exist_ok=False)
        footprints = []
        for ref, x in [("J1", 5), ("J2", 15)]:
            footprints.append(f'''
  (footprint "SmokePad" (layer "F.Cu") (uuid "{uuid.uuid4()}")
    (at {x} 5)
    (property "Reference" "{ref}" (at 0 -2) (layer "F.SilkS")
      (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "SmokePad" (at 0 2) (layer "F.Fab")
      (effects (font (size 1 1) (thickness 0.15))))
    (attr through_hole)
    (fp_rect (start -1.2 -1.2) (end 1.2 1.2)
      (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
    (pad "1" thru_hole circle (at 0 0) (size 1.6 1.6) (drill 0.8)
      (layers "*.Cu" "*.Mask") (net 1 "TEST")))''')
        board_path.write_text('''(kicad_pcb (version 20241229) (generator "hardware_lab_smoke")
  (general (thickness 1.6)) (paper "A4")
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal)
    (36 "B.SilkS" user "b.silkscreen") (37 "F.SilkS" user "f.silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "b.courtyard") (47 "F.CrtYd" user "f.courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user))
  (setup (pad_to_mask_clearance 0)) (net 0 "") (net 1 "TEST")
  (gr_rect (start 0 0) (end 20 12) (stroke (width 0.05) (type default))
    (fill none) (layer "Edge.Cuts"))
''' + "".join(footprints) + "\n)\n")
        marker.write_text(json.dumps({"board": str(board_path)}, indent=2) + "\n")
        print(board_path)
        return

    if not marker.exists() or json.loads(marker.read_text()) != {"board": str(board_path)}:
        parser.error("Missing or mismatched fixture identity marker")
    from kipy import KiCad
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2
    from kipy.proto.board import BoardLayer

    client = KiCad(client_name="hardware-lab-smoke", timeout_ms=5000)
    board = client.get_board()
    actual = (Path(board.document.project.path) / board.document.board_filename).resolve()
    if actual != board_path:
        parser.error(f"Refusing unexpected board: {actual}")
    footprints = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    if set(footprints) != {"J1", "J2"}:
        raise RuntimeError("Unexpected footprint inventory")
    if args.mode == "edit":
        if board.get_tracks() or board.get_vias():
            raise RuntimeError("Fixture already has routing; create a new fixture")
        commit = board.begin_commit()
        try:
            footprints["J2"].position = Vector2.from_xy_mm(16, 5)
            board.update_items(footprints["J2"])
            net = next(n for n in board.get_nets() if n.name == "TEST")
            tracks = []
            for start, end, layer in [((5, 5), (10, 5), BoardLayer.BL_F_Cu),
                                      ((10, 5), (16, 5), BoardLayer.BL_B_Cu)]:
                track = Track()
                track.start = Vector2.from_xy_mm(*start)
                track.end = Vector2.from_xy_mm(*end)
                track.width = 300000
                track.layer = layer
                track.net = net
                tracks.append(track)
            via = Via()
            via.position = Vector2.from_xy_mm(10, 5)
            via.diameter = 600000
            via.drill_diameter = 300000
            via.net = net
            board.create_items([*tracks, via])
            board.push_commit(commit, "Verify hardware-lab IPC fixture")
        except Exception:
            board.drop_commit(commit)
            raise
        board.save()

    footprints = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    tracks = board.get_tracks()
    vias = board.get_vias()
    expected_tracks = {(5000000, 5000000, 10000000, 5000000, BoardLayer.BL_F_Cu),
                       (10000000, 5000000, 16000000, 5000000, BoardLayer.BL_B_Cu)}
    actual_tracks = {(t.start.x, t.start.y, t.end.x, t.end.y, t.layer) for t in tracks}
    assert footprints["J1"].position == Vector2.from_xy_mm(5, 5)
    assert footprints["J2"].position == Vector2.from_xy_mm(16, 5)
    assert len(tracks) == 2 and actual_tracks == expected_tracks
    assert all(t.width == 300000 and t.net.name == "TEST" for t in tracks)
    assert len(vias) == 1 and vias[0].net.name == "TEST"
    assert vias[0].position == Vector2.from_xy_mm(10, 5)
    assert vias[0].diameter == 600000 and vias[0].drill_diameter == 300000
    print(json.dumps({"ok": True, "mode": args.mode, "board": str(board_path),
                      "version": str(client.get_version()), "footprints": 2,
                      "tracks": 2, "vias": 1}, indent=2))


if __name__ == "__main__":
    main()
