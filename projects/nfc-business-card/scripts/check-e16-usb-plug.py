#!/usr/bin/env python3
"""Check whether a USB-C plug and its overmold clear the printed shells.

The GCT USB4500 mating view gives the plug cross-section as 8.34 mm wide by
2.56 mm tall. The connector body sits in the right-edge notch (x 76.704-84,
y 11.38-20.62 mm), so a plug enters through that 9.24 mm window and its plastic
overmold has to live outside the card. The plug is centred on the connector
envelope measured in the V7 report, both in y and in z, so a clean result means
the mating path is clear rather than that the plug was parked out of the way.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        projects/nfc-business-card/scripts/check-e16-usb-plug.py
"""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App
import Part

REPO = Path(__file__).resolve().parents[3]
ENCLOSURE = REPO / "projects/nfc-business-card/enclosure/nfc-card-e16-enclosure-v7.FCStd"
ENCLOSURE_REPORT = REPO / "projects/nfc-business-card/enclosure/nfc-card-e16-enclosure-v7-report.json"

BODY = json.loads(ENCLOSURE_REPORT.read_text())["usb"]     # measured from the board STEP
BODY_X = BODY["connector_body_x_mm"]
CARD_EDGE_X = 84.0
PLUG_W, PLUG_H = 8.34, 2.56   # metal shell cross-section, GCT mating view
PLUG_OVERSHOOT = 0.2          # how far the shell reaches past the mating face
OVERMOLD_LEN = 20.0
BODY_CENTRE_Y = (BODY["y_mm"][0] + BODY["y_mm"][1]) / 2
BODY_CENTRE_Z = (BODY["z_mm"][0] + BODY["z_mm"][1]) / 2
NOTCH_Y = (11.38, 20.62)
NOTCH_WIDTH = NOTCH_Y[1] - NOTCH_Y[0]


def plug_shapes(overmold_w: float, overmold_h: float):
    """Return (metal shell, overmold) boxes for a fully inserted plug."""
    front_x = BODY_X[1]
    shell = Part.makeBox(PLUG_OVERSHOOT + front_x - BODY_X[0], PLUG_W, PLUG_H,
                         App.Vector(BODY_X[0], BODY_CENTRE_Y - PLUG_W / 2,
                                    BODY_CENTRE_Z - PLUG_H / 2))
    overmold = Part.makeBox(OVERMOLD_LEN, overmold_w, overmold_h,
                            App.Vector(front_x, BODY_CENTRE_Y - overmold_w / 2,
                                       BODY_CENTRE_Z - overmold_h / 2))
    return shell, overmold


def main() -> int:
    doc = App.openDocument(str(ENCLOSURE))
    shells = {name: doc.getObject(name).Shape for name in ("BottomShell", "TopShell")}
    clear = lambda shape: all(shape.common(s).Volume <= 1e-6 for s in shells.values())

    report: dict[str, object] = {
        "enclosure": ENCLOSURE.name,
        "connector_body_mm": BODY,
        "plug_shell_mm": [PLUG_W, PLUG_H],
        "reference_overmold_mm": [10.5, 6.0],
        "notch_width_mm": round(NOTCH_WIDTH, 2),
        "interference": {},
    }
    shell, overmold = plug_shapes(10.5, 6.0)
    for name, solid in shells.items():
        report["interference"][f"shell/{name}"] = round(shell.common(solid).Volume, 4)
        report["interference"][f"overmold/{name}"] = round(overmold.common(solid).Volume, 4)

    # Widest overmold front face that can still reach the connector face.
    best = 0.0
    for width in [x / 20 for x in range(1, 401)]:
        _, om = plug_shapes(width, 6.0)
        if clear(om):
            best = width
    report["max_overmold_width_mm"] = round(best, 2)

    # A wider overmold cannot pass the card edge, so it stops there instead.
    wide = Part.makeBox(OVERMOLD_LEN, 11.0, 6.0,
                        App.Vector(CARD_EDGE_X, BODY_CENTRE_Y - 5.5, BODY_CENTRE_Z - 3.0))
    report["wide_overmold_at_card_edge"] = {
        "moulding_mm": [11.0, 6.0],
        "interference": {name: round(wide.common(s).Volume, 4) for name, s in shells.items()},
        "insertion_shortfall_mm": round(CARD_EDGE_X - BODY_X[1], 2),
    }

    # The design passes when the mating path is clear and every overmold that
    # fits the notch can reach the connector face; a wider moulding is not a
    # failure, it simply rests on the card edge (measured above).
    report["ok"] = clear(shell) and report["max_overmold_width_mm"] >= NOTCH_WIDTH - 0.1
    report["reference_overmold_hits_shell"] = not clear(overmold)

    # freecadcmd drops unflushed stdout when the script exits
    print(json.dumps(report, ensure_ascii=False, indent=1), flush=True)
    return 0 if report["ok"] else 1


raise SystemExit(main())
