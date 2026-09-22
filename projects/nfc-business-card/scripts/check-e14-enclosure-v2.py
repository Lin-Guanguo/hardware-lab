"""Reopen and validate the E14 EDA-coordinate enclosure sample in FreeCAD."""

from pathlib import Path
import json
import sys

import FreeCAD as App


arg_model = next((arg for arg in sys.argv[1:] if arg.lower().endswith(".fcstd")), None)
model = Path(arg_model) if arg_model else Path(
    "projects/nfc-business-card/enclosure/nfc-card-e14-enclosure-v2-eda-coordinate.FCStd"
)
doc = App.openDocument(str(model.resolve()))
doc.recompute()
shells = [doc.getObject("BottomShell"), doc.getObject("TopShell")]
invalid = [obj.Name for obj in shells if obj is None or obj.Shape.isNull() or not obj.Shape.isValid()]
intersections = []
if all(shells):
    volume = shells[0].Shape.common(shells[1].Shape).Volume
    if volume > 1e-6:
        intersections.append({"objects": [obj.Name for obj in shells], "volume_mm3": volume})
result = {
    "ok": not invalid and not intersections and all(len(obj.Shape.Solids) == 1 for obj in shells),
    "model": str(model),
    "invalid_shapes": invalid,
    "shell_solids": {obj.Name: len(obj.Shape.Solids) for obj in shells if obj},
    "shell_intersections": intersections,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
App.closeDocument(doc.Name)
if not result["ok"]:
    raise SystemExit(1)
