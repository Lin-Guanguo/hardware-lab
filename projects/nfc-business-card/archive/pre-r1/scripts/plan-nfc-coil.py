#!/usr/bin/env python3
"""Emit the planned E16 NFC antenna coil, its feeds and the crossover as JSON.

The geometry is the one recorded in
hardware/pcb-e16-usb-right-mid.md#线圈候选设计已算好并离线校验等实验拍板:
a 6-turn rectangular spiral in the reserve area, 0.25 mm copper / 0.15 mm gap,
fed from the two bottom-layer landing pads with the inner terminal brought out
on the top layer. Nothing here touches EasyEDA; it only writes a route file that
check-proposed-route.py can verify against the live snapshot.

    python3 scripts/plan-nfc-coil.py                        # print JSON
    python3 scripts/plan-nfc-coil.py --write                # -> hardware/e16-nfc-coil-plan.json
    python3 scripts/plan-nfc-coil.py --write --turns 5

Landing pads: NFC1 (68.00, 23.00) and NFC2 (71.40, 23.00), 1.5 x 1.5 mm squares
on the bottom layer. The coil is one continuous conductor between them, so it
needs either an antenna component or a merged net before it is drawn.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PROJECT = REPO / "projects/nfc-business-card"
DEFAULT_OUT = PROJECT / "hardware/e16-nfc-coil-plan.json"

# Outer turn centre line, 0.5 mm inside the keep-away-limited usable area.
X0, X1, Y0, Y1 = 60.60, 71.00, 27.60, 48.90
PITCH = 0.40          # width 0.25 + gap 0.15
PAD_NFC1 = (68.00, 23.00)
PAD_NFC2 = (71.40, 23.00)
LAYER_COIL = 2
LAYER_CROSSOVER = 1
VIA_D, VIA_HOLE = 0.30, 0.20


def spiral(turns: int) -> list[tuple[float, float]]:
    """Rectangular spiral, outer turn first, ending on the innermost ring."""
    points = [(PAD_NFC1[0], Y0), (X0, Y0)]
    for k in range(turns):
        x0, x1 = X0 + k * PITCH, X1 - k * PITCH
        y0, y1 = Y0 + k * PITCH, Y1 - k * PITCH
        points += [(x0, y1), (x1, y1), (x1, y0 + PITCH)]
        if k < turns - 1:
            points.append((x0 + PITCH, y0 + PITCH))
    return [(round(x, 3), round(y, 3)) for x, y in points]


def build(turns: int) -> dict:
    coil = spiral(turns)
    inner = coil[-1]
    crossover = [
        inner,
        (inner[0], 25.60),
        (70.20, 24.40),
        (PAD_NFC2[0], 24.40),
    ]
    return {
        "name": "E16 NFC coil plan",
        "note": (
            "Planned copper, not drawn yet. Needs the reserve region relaxed from ruleType "
            "[2,6,5,7] to [2,6,7] (drop NO_WIRES) and a netlist decision: merge NFC1_TBD/"
            "NFC2_TBD, or add an antenna component whose footprint carries this copper."
        ),
        "keepouts": [
            {"name": "NFC reserve", "x0": 60.0, "y0": 24.0, "x1": 82.0, "y1": 50.0},
            {"name": "U1 antenna", "x0": 59.7, "y0": 0.2, "x1": 70.3, "y1": 2.5},
        ],
        "ignore_nets": ["NFC1_TBD", "NFC2_TBD"],
        "tracks": [
            {"net": "NFC_COIL", "layer": LAYER_COIL, "width_mm": 0.25, "points": coil},
            {"net": "NFC_COIL", "layer": LAYER_COIL, "width_mm": 0.25,
             "points": [PAD_NFC1, coil[0]]},
            {"net": "NFC_COIL", "layer": LAYER_CROSSOVER, "width_mm": 0.25,
             "points": [(round(x, 3), round(y, 3)) for x, y in crossover]},
            {"net": "NFC_COIL", "layer": LAYER_COIL, "width_mm": 0.25,
             "points": [(round(PAD_NFC2[0], 3), 24.40), PAD_NFC2]},
        ],
        "vias": [
            {"net": "NFC_COIL", "x": inner[0], "y": inner[1], "diameter_mm": VIA_D, "hole_mm": VIA_HOLE},
            {"net": "NFC_COIL", "x": PAD_NFC2[0], "y": 24.40, "diameter_mm": VIA_D, "hole_mm": VIA_HOLE},
        ],
        "turns": turns,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--turns", type=int, default=6, help="spiral turns (default 6 -> 1.12 uH)")
    parser.add_argument("--write", action="store_true", help=f"write {DEFAULT_OUT.relative_to(REPO)}")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    plan = build(args.turns)
    text = json.dumps(plan, ensure_ascii=False, indent=1) + "\n"
    if args.write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        length = sum(
            ((p[1][0] - p[0][0]) ** 2 + (p[1][1] - p[0][1]) ** 2) ** 0.5
            for track in plan["tracks"]
            for p in zip(track["points"], track["points"][1:])
        )
        print(f"wrote {args.out.relative_to(REPO)}: {args.turns} turns, "
              f"{sum(len(t['points']) - 1 for t in plan['tracks'])} segments, {length:.1f} mm of copper")
        print("verify with: python3 scripts/check-proposed-route.py --route "
              f"{args.out.relative_to(REPO)}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
