"""Generate an EDA-coordinate enclosure sample for the E14 reconciliation pass.

This variant follows the saved EasyEDA coordinate snapshot: the USB connector
is at the upper board opening, the screen/FPC region is at the lower-left, and
the battery target is at the upper-left. It is a coordination sample, not a
production enclosure.
"""

from pathlib import Path
import json

import FreeCAD as App
import Part
import Mesh


OUT = Path(__file__).resolve().parent
MODEL = OUT / "nfc-card-e14-enclosure-v2-eda-coordinate.FCStd"
STEP = OUT / "nfc-card-e14-enclosure-v2-eda-coordinate.step"
BOTTOM_STL = OUT / "nfc-card-e14-bottom-v2-eda-coordinate.stl"
TOP_STL = OUT / "nfc-card-e14-top-v2-eda-coordinate.stl"
REPORT = OUT / "nfc-card-e14-enclosure-v2-eda-coordinate-report.json"

if any(path.exists() for path in (MODEL, STEP, BOTTOM_STL, TOP_STL, REPORT)):
    raise SystemExit("Existing E14 V2 output refused; choose a new version instead of overwriting.")

W, H = 84.0, 52.0
OUTER_H = 5.0
WALL = 1.2
BOTTOM_BASE = 0.8
SPLIT_Z = 2.2
TOP_CAP_BOTTOM = 4.2
CAP = 0.8
PCB_T = 0.8


def rounded_prism(width, height, z0, thickness, radius, x0=0.0, y0=0.0):
    if radius <= 0:
        return Part.makeBox(width, height, thickness, App.Vector(x0, y0, z0))
    shape = Part.makeBox(width - 2 * radius, height, thickness,
                         App.Vector(x0 + radius, y0, z0))
    shape = shape.fuse(Part.makeBox(width, height - 2 * radius, thickness,
                                    App.Vector(x0, y0 + radius, z0)))
    for cx, cy in ((x0 + radius, y0 + radius),
                   (x0 + width - radius, y0 + radius),
                   (x0 + radius, y0 + height - radius),
                   (x0 + width - radius, y0 + height - radius)):
        shape = shape.fuse(Part.makeCylinder(radius, thickness,
                                             App.Vector(cx, cy, z0)))
    return shape.removeSplitter()


def add_feature(doc, name, label, shape, role, color, visible=True):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Role", "Evidence")
    obj.Role = role
    obj.addProperty("App::PropertyString", "SourceAndLimits", "Evidence")
    obj.SourceAndLimits = "E14 EasyEDA 实际坐标协调样件；真实最大包络、公差和装配方式仍待确认。"
    obj.addProperty("App::PropertyColor", "StudyColor", "Appearance")
    obj.StudyColor = tuple(int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    if App.GuiUp:
        obj.ViewObject.ShapeColor = obj.StudyColor
        obj.ViewObject.Visibility = visible
    return obj


doc = App.newDocument("NfcCardE14EnclosureV2EdaCoordinate")
doc.Label = "NFC 名片 · E14 EDA 坐标外壳协调样件 V2"
doc.Comment = "按 EasyEDA 实际坐标协调 USB、屏幕、FPC、按键和电池；不是生产壳。"

params = doc.addObject("App::FeaturePython", "EnclosureParameters")
params.Label = "E14 V2 外壳参数与证据"
for name, value in (("CardWidth", W), ("CardHeight", H), ("OuterHeight", OUTER_H),
                    ("Wall", WALL), ("BottomBase", BOTTOM_BASE),
                    ("SplitZ", SPLIT_Z), ("TopCapBottom", TOP_CAP_BOTTOM),
                    ("CapThickness", CAP), ("PcbThickness", PCB_T)):
    params.addProperty("App::PropertyLength", name, "Envelope")
    setattr(params, name, value)
params.addProperty("App::PropertyString", "Status", "Evidence")
params.Status = "E14_ENCLOSURE_V2_EDA_COORDINATE_SAMPLE_NOT_PRODUCTION_RELEASE"
params.addProperty("App::PropertyString", "Source", "Evidence")
params.Source = "hardware/e14-eda-snapshot.json; J1≈(49.5,5.5) mm; J2≈(51.5,32.5) mm"

# The actual E14 Layer-11 outline, converted from mil to mm relative to its
# minimum corner. This is deliberately kept as a reference solid because the
# outline is still a release gate.
outline_points = [
    (1.5, 1.5), (1.5, 50.5), (82.5, 50.5), (82.5, 22.5),
    (49.5, 22.5), (49.5, 1.5), (36.6, 1.5), (36.6, 7.3),
    (27.4, 7.3), (27.4, 1.5),
]
wire = Part.makePolygon([App.Vector(x, y, 0.9) for x, y in outline_points] +
                        [App.Vector(*outline_points[0], 0.9)])
board_shape = Part.Face(wire).extrude(App.Vector(0, 0, PCB_T))
board = add_feature(doc, "BoardReference", "E14 实际板框参考（Layer 11）", board_shape,
                    "reference", "#9BB8AA", visible=False)
board.SourceAndLimits = "从 E14 Layer 11 轮廓快照重建；不是已释放板框。"

bottom_outer = rounded_prism(W, H, 0.0, SPLIT_Z, 2.0)
bottom_cavity = rounded_prism(W - 2 * WALL, H - 2 * WALL, BOTTOM_BASE,
                              SPLIT_Z - BOTTOM_BASE + 0.2, 0.8, WALL, WALL)
bottom_shape = bottom_outer.cut(bottom_cavity)

# J1 is on the upper board opening in the saved EDA coordinate view.
usb_opening = Part.makeBox(12.5, 10.5, 2.0, App.Vector(43.25, -0.5, 1.1))
bottom_shape = bottom_shape.cut(usb_opening).removeSplitter()
battery_relief = rounded_prism(32.0, 13.0, -0.1, 0.45, 1.0, 2.0, 1.0)
bottom_shape = bottom_shape.cut(battery_relief).removeSplitter()
bottom = add_feature(doc, "BottomShell", "下壳 · EDA 坐标 USB 上边开口", bottom_shape,
                     "print_candidate", "#8FA9C1")

top_outer = rounded_prism(W, H, SPLIT_Z, OUTER_H - SPLIT_Z, 2.0)
top_cavity = rounded_prism(W - 2 * WALL, H - 2 * WALL, SPLIT_Z,
                           TOP_CAP_BOTTOM - SPLIT_Z + 0.05, 0.8, WALL, WALL)
top_shape = top_outer.cut(top_cavity)
screen_window = Part.makeBox(39.0, 33.6, CAP + 0.4, App.Vector(1.2, 16.2, TOP_CAP_BOTTOM - 0.2))
top_shape = top_shape.cut(screen_window)
for y in (5.0, 11.3, 17.6):
    top_shape = top_shape.cut(Part.makeCylinder(2.0, CAP + 0.4,
                                                App.Vector(38.1, y, TOP_CAP_BOTTOM - 0.2)))
top_shape = top_shape.cut(Part.makeBox(12.5, 10.5, 3.6,
                                       App.Vector(43.25, -0.5, 2.0))).removeSplitter()
top = add_feature(doc, "TopShell", "上壳 · EDA 坐标屏窗 + 按键孔 + USB 上边开口",
                  top_shape, "print_candidate", "#B9C9DC")

# References use the actual EDA coordinate snapshot. They are hidden by
# default, but remain in the file for clearance review.
references = {
    "ScreenReference": ("屏幕机械区参考 · 37.42 × 31.90 mm",
                         Part.makeBox(37.42, 31.90, 1.1, App.Vector(0.5, 17.0, 2.7)), "#C5D5E5"),
    "BatteryReference": ("301230 目标 · 30 × 12 × 3 mm",
                          Part.makeBox(30.0, 12.0, 3.0, App.Vector(3.0, 1.5, 1.0)), "#E6B96E"),
    "UsbReference": ("J1 USB4500 参考 · EDA 中心 49.5,5.5 mm",
                     Part.makeBox(8.0, 8.94, 3.2, App.Vector(45.5, 1.0, 1.8)), "#AEB9C8"),
    "FpcReference": ("J2 FPC 参考 · EDA 中心 51.5,32.5 mm",
                     Part.makeBox(6.8, 16.5, 2.2, App.Vector(48.0, 24.25, 1.8)), "#B8D4C0"),
    "McuReference": ("U1 主控参考 · EDA 中心 76.2,38.1 mm",
                     Part.makeBox(8.5, 6.5, 2.2, App.Vector(72.0, 34.85, 1.8)), "#A7C9E5"),
}
for name, (label, shape, color) in references.items():
    ref = add_feature(doc, name, label, shape, "reference", color, visible=False)
    ref.SourceAndLimits = "E14 快照参考包络；不是已核准料号最大外形。"

for index, y in enumerate((5.0, 11.3, 17.6), 1):
    ref = add_feature(doc, f"Button{index}Reference", f"SW{index} 参考 · EDA y={y:.1f} mm",
                     Part.makeBox(5.2, 5.2, 1.6, App.Vector(35.5, y - 2.6, 2.7)),
                     "reference", "#E4B28F", visible=False)
    ref.SourceAndLimits = "按键本体参考；键帽、行程和弹片未验证。"

doc.recompute()
physical = [bottom, top]
invalid = [o.Name for o in physical if o.Shape.isNull() or not o.Shape.isValid()]
shell_intersections = []
for i, first in enumerate(physical):
    for second in physical[i + 1:]:
        volume = first.Shape.common(second.Shape).Volume
        if volume > 1e-6:
            shell_intersections.append({"objects": [first.Name, second.Name], "volume_mm3": round(volume, 6)})

reference_intersections = []
for shell in physical:
    for name, (_, shape, _) in references.items():
        # The screen is intentionally seated inside the window/cavity; contact
        # with the cap opening is a support condition, not a hard collision.
        if name == "ScreenReference":
            continue
        volume = shell.Shape.common(shape).Volume
        if volume > 1e-6:
            reference_intersections.append({"shell": shell.Name, "reference": name,
                                             "volume_mm3": round(volume, 6)})

report = {
    "status": "E14_ENCLOSURE_V2_EDA_COORDINATE_SAMPLE_NOT_PRODUCTION_RELEASE",
    "outer_mm": [W, H, OUTER_H],
    "usb_opening": {"edge": "y=0 EDA coordinate edge", "bbox_mm": [43.25, -0.5, 12.5, 10.5]},
    "screen_window_mm": [1.2, 16.2, 39.0, 33.6],
    "battery_relief_mm": [2.0, 1.0, 32.0, 13.0, 0.45],
    "geometry_checks": {
        "invalid_shapes": invalid,
        "shell_solids": {o.Name: len(o.Shape.Solids) for o in physical},
        "shell_intersections": shell_intersections,
        "shell_reference_intersections": reference_intersections,
        "valid": not invalid and not shell_intersections and not reference_intersections,
    },
    "limitations": [
        "This is an EDA-coordinate reconciliation sample, not a production enclosure.",
        "The E14 Layer 11 board outline and J1 opening remain a release gate.",
        "The battery is a nominal target without supplier maximum envelope, protection board, leads, tape or swelling allowance.",
        "Screen FPC direction, button caps, USB plug strain relief and wall tolerances require physical samples.",
        "Do not send STEP or STL to production before EDA board outline, routing, DRC, RF and DFM are released.",
    ],
}
assert report["geometry_checks"]["valid"], report
doc.recompute()
doc.saveAs(str(MODEL))
Part.export([bottom, top], str(STEP))
Mesh.export([bottom], str(BOTTOM_STL))
Mesh.export([top], str(TOP_STL))
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"model": str(MODEL), "step": str(STEP), "bottom_stl": str(BOTTOM_STL),
                  "top_stl": str(TOP_STL), "report": str(REPORT),
                  "valid": report["geometry_checks"]["valid"]}, ensure_ascii=False))
