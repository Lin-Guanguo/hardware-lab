#!/usr/bin/env python3
"""Estimate inductance, resistance and tuning for a planar rectangular NFC coil.

The NFC block is still undecided (on-board PCB coil vs a ferrite-backed
sticker/FPC antenna), and the reserved area on the card is small. This script
answers the quantitative part before the bench test: for a given outer size,
trace width/gap and turn count it reports the inductance (modified Wheeler
approximation), the DC resistance of the spiral, the tuning capacitance for
13.56 MHz and the resulting Q.

    python3 scripts/estimate-nfc-coil.py                      # our reserved area
    python3 scripts/estimate-nfc-coil.py --outer 60,40 --turns 4

The numbers are estimates (+/-10-20%): they ignore the ground-plane/ferrite
loading, the mutual coupling to nearby metal and skin/proximity effects, all of
which the physical tuning has to settle. They are good enough to tell whether a
given area can even reach the 1-2 uH that phone-reader antennas normally use.
"""

from __future__ import annotations

import argparse
import math

MU0 = 4 * math.pi * 1e-7          # H/m
RHO_CU = 1.72e-8                  # ohm*m at 20 C
F_NFC = 13.56e6                   # Hz
COPPER_T = 35e-6                  # 1 oz outer layer


def estimate(outer_mm: tuple[float, float], turns: int, width_mm: float, gap_mm: float, thickness_um: float) -> dict:
    a, b = (v / 1000 for v in outer_mm)
    pitch = (width_mm + gap_mm) / 1000
    inner_a = a - 2 * pitch * (turns - 1)
    inner_b = b - 2 * pitch * (turns - 1)
    if inner_a <= 0 or inner_b <= 0:
        raise SystemExit("too many turns for this outer size")

    # modified Wheeler (Mohan) with the mean of the two side lengths
    d_out = (a + b) / 2
    d_in = (inner_a + inner_b) / 2
    d_avg = (d_out + d_in) / 2
    rho = (d_out - d_in) / (d_out + d_in)
    k1, k2 = 2.34, 2.75
    inductance = k1 * MU0 * turns ** 2 * d_avg / (1 + k2 * rho)

    # spiral trace length: every turn is a rectangle that shrinks by one pitch
    length = 0.0
    for i in range(turns):
        la = a - 2 * pitch * i
        lb = b - 2 * pitch * i
        length += 2 * (la + lb)
    width = width_mm / 1000
    thickness = thickness_um * 1e-6
    resistance = RHO_CU * length / (width * thickness)

    capacitance = 1 / ((2 * math.pi * F_NFC) ** 2 * inductance)
    omega = 2 * math.pi * F_NFC
    return {
        "outer_mm": outer_mm,
        "turns": turns,
        "width_mm": width_mm,
        "gap_mm": gap_mm,
        "inner_mm": (round(inner_a * 1000, 2), round(inner_b * 1000, 2)),
        "fill_ratio": round(rho, 3),
        "trace_length_mm": round(length * 1000, 1),
        "inductance_uH": round(inductance * 1e6, 3),
        "resistance_ohm": round(resistance, 2),
        "tuning_cap_pF": round(capacitance * 1e12, 1),
        "q_at_13_56": round(omega * inductance / resistance, 1),
        "copper_um": thickness_um,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outer", default="17,21", help="outer size in mm, e.g. 17,21")
    parser.add_argument("--turns", type=int, nargs="*", default=[3, 4, 5, 6, 8])
    parser.add_argument("--width", type=float, nargs="*", default=[0.15, 0.25])
    parser.add_argument("--gap", type=float, default=0.15)
    parser.add_argument("--copper-um", type=float, default=35.0)
    args = parser.parse_args()

    outer = tuple(float(v) for v in args.outer.split(","))
    print(f"outer {outer[0]} x {outer[1]} mm, gap {args.gap} mm, copper {args.copper_um:.0f} um, 13.56 MHz")
    print(f"{'turns':>5} {'width':>6} {'L uH':>7} {'R ohm':>7} {'C pF':>7} {'Q':>6} {'len mm':>8} {'fill':>5}")
    for width in args.width:
        for turns in args.turns:
            row = estimate(outer, turns, width, args.gap, args.copper_um)
            print(f"{row['turns']:>5} {row['width_mm']:>6.2f} {row['inductance_uH']:>7.3f} {row['resistance_ohm']:>7.2f} "
                  f"{row['tuning_cap_pF']:>7.1f} {row['q_at_13_56']:>6.1f} {row['trace_length_mm']:>8.1f} {row['fill_ratio']:>5.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
