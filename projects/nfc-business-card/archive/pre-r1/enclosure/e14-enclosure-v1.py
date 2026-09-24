"""Generate the first printable enclosure candidate for the E14 NFC card layout.

This is a parametric verification sample.  It is deliberately kept separate from
the E14 PCBA spatial study and does not claim production-ready tolerances.
"""

from pathlib import Path
import json

import FreeCAD as App
import Part


OUT = Path(__file__).resolve().parent
MODEL = OUT / "nfc-card-e14-enclosure-v1.FCStd"
STEP = OUT / "nfc-card-e14-enclosure-v1.step"
BOTTOM_STL = OUT / "nfc-card-e14-bottom-v1.stl"
TOP_STL = OUT / "nfc-card-e14-top-v1.stl"
REPORT = OUT / "nfc-card-e14-enclosure-v1-report.json"

if MODEL.exists() or STEP.exists() or BOTTOM_STL.exists() or TOP_STL.exists() or REPORT.exists():
    raise SystemExit("Existing E14 enclosure output refused; choose a new version instead of overwriting.")


W, H = 84.0, 52.0
CORNER_R = 2.0
OUTER_H = 5.0
BOTTOM_BASE = 0.8
BOTTOM_TOP = 2.4
TOP_START = 2.4
TOP_CAP_BOTTOM = 4.2
WALL = 1.2
CAP = 0.8
PCB_T = 0.8


def rounded_prism(width, height, z0, thickness, radius, x0=0.0, y0=0.0):
    """Make a robust rounded rectangle prism from overlapping boxes and cylinders."""
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
        shape = shape.fuse(Part.makeCylinder(radius, thickness, App.Vector(cx, cy, z0)))
    return shape.removeSplitter()


def add_feature(doc, name, label, shape, role, color, visible=True):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Role", "Evidence")
    obj.Role = role
    obj.addProperty("App::PropertyString", "SourceAndLimits", "Evidence")
    obj.SourceAndLimits = "E14 新电池布局的结构候选；真实器件最大包络、打印公差和装配工艺仍待验证。"
    obj.addProperty("App::PropertyColor", "StudyColor", "Appearance")
    obj.StudyColor = tuple(int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    if App.GuiUp:
        obj.ViewObject.ShapeColor = obj.StudyColor
        obj.ViewObject.Visibility = visible
    return obj


doc = App.newDocument("NfcCardE14EnclosureV1")
doc.Label = "NFC 名片 · E14 可打印外壳验证样件 V1"
doc.Comment = "上下壳、屏幕窗口、按键孔和 USB 开口候选；不是最终生产壳。"

params = doc.addObject("App::FeaturePython", "EnclosureParameters")
params.Label = "E14 外壳参数与证据"
for name, value in (
    ("CardWidth", W), ("CardHeight", H), ("OuterHeight", OUTER_H),
    ("Wall", WALL), ("BottomBase", BOTTOM_BASE), ("CapThickness", CAP),
    ("BottomTop", BOTTOM_TOP), ("TopStart", TOP_START),
    ("TopCapBottom", TOP_CAP_BOTTOM), ("CornerRadius", CORNER_R),
    ("PcbThickness", PCB_T),
):
    params.addProperty("App::PropertyLength", name, "Envelope")
    setattr(params, name, value)
params.addProperty("App::PropertyString", "Status", "Evidence")
params.Status = "E14_ENCLOSURE_V1_PRINTABLE_SAMPLE_NOT_PRODUCTION_RELEASE"
params.addProperty("App::PropertyString", "SplitAndFixing", "Evidence")
params.SplitAndFixing = "上下壳 2.4 mm 分界；当前无卡扣、螺钉柱和胶槽，供首轮装配试样。"

# Bottom shell: a 0.8 mm floor and 1.8 mm surrounding skirt.  A shallow
# underside recess gives the 301230 battery a deliberate relief zone.
bottom_outer = rounded_prism(W, H, 0.0, BOTTOM_TOP, CORNER_R)
bottom_cavity = rounded_prism(W - 2 * WALL, H - 2 * WALL, BOTTOM_BASE,
                              BOTTOM_TOP - BOTTOM_BASE + 0.2, max(0.4, CORNER_R - WALL),
                              WALL, WALL)
bottom_shape = bottom_outer.cut(bottom_cavity)
battery_relief = rounded_prism(32.0, 13.0, -0.1, 0.45, 1.0, 2.0, 37.5)
bottom_shape = bottom_shape.cut(battery_relief).removeSplitter()

# The USB-C opening is cut through the right wall in both halves.  It leaves
# a 1.2 mm rim around the connector envelope in the XY plane.
usb_cut_bottom = Part.makeBox(10.0, 12.5, 1.2, App.Vector(W - 9.5, 25.75, 1.5))
bottom_shape = bottom_shape.cut(usb_cut_bottom).removeSplitter()
bottom = add_feature(doc, "BottomShell", "下壳 · 0.8 mm 底板 + 周边壁", bottom_shape,
                     "print_candidate", "#8FA9C1")
bottom.addProperty("App::PropertyString", "BatteryRelief", "Evidence")
bottom.BatteryRelief = "底面 32 × 13 mm 浅凹槽，覆盖 301230 30 × 12 mm 名义区；不代表完整包体和胶带尺寸。"

# Top shell: a skirt meets the bottom shell at the 2.4 mm split, with a 0.8 mm cap.  The
# screen aperture, three button holes and side USB opening are cut from the
# same solid so each shell is directly printable as a test part.
top_outer = rounded_prism(W, H, TOP_START, OUTER_H - TOP_START, CORNER_R)
top_cavity = rounded_prism(W - 2 * WALL, H - 2 * WALL, TOP_START,
                           TOP_CAP_BOTTOM - TOP_START + 0.05,
                           max(0.4, CORNER_R - WALL), WALL, WALL)
top_shape = top_outer.cut(top_cavity)
screen_window = Part.makeBox(39.0, 33.6, CAP + 0.4, App.Vector(2.2, 1.2, TOP_CAP_BOTTOM - 0.2))
top_shape = top_shape.cut(screen_window)
for x in (40.6, 47.6, 54.6):
    button_hole = Part.makeCylinder(2.0, CAP + 0.4, App.Vector(x, 40.6, TOP_CAP_BOTTOM - 0.2))
    top_shape = top_shape.cut(button_hole)
usb_cut_top = Part.makeBox(10.0, 12.5, 3.6, App.Vector(W - 9.5, 25.75, 2.0))
top_shape = top_shape.cut(usb_cut_top).removeSplitter()
top = add_feature(doc, "TopShell", "上壳 · 屏幕窗口 + 三按键孔 + USB-C 侧开口", top_shape,
                  "print_candidate", "#B9C9DC")
top.addProperty("App::PropertyString", "Openings", "Evidence")
top.Openings = "屏幕窗口 39 × 33.6 mm；按键孔 Ø4 mm × 3；USB 侧开口 12.5 mm 宽。"

# Separate adhesive/ultrasonic-weld-free screen ledge candidate.  It is
# intentionally an independent object until the actual screen glass and FPC
# are measured, so the top shell can be printed without hidden assumptions.
ledge_z = 3.0
ledge_t = 0.8
ledge_parts = [
    Part.makeBox(39.0, 0.8, ledge_t, App.Vector(2.1, 1.3, ledge_z)),
    Part.makeBox(39.0, 0.8, ledge_t, App.Vector(2.1, 34.0, ledge_z)),
    Part.makeBox(0.8, 32.0, ledge_t, App.Vector(1.3, 2.1, ledge_z)),
    Part.makeBox(0.8, 32.0, ledge_t, App.Vector(41.1, 2.1, ledge_z)),
]
screen_ledge = ledge_parts[0]
for part in ledge_parts[1:]:
    screen_ledge = screen_ledge.fuse(part)
screen_ledge = screen_ledge.removeSplitter()
ledge = add_feature(doc, "ScreenLedge", "屏幕支撑台阶候选 · 独立胶接件", screen_ledge,
                    "assembly_candidate", "#D8B477")
ledge.addProperty("App::PropertyString", "Purpose", "Evidence")
ledge.Purpose = "承托屏幕玻璃边缘；屏幕实际厚度、FPC 折弯和胶槽尚未确认。"

# Lightweight references are hidden by default but make the model auditable.
refs = {
    "BoardReference": ("PCB 参考 · 84 × 52 × 0.8 mm",
                        Part.makeBox(81.0, 49.0, PCB_T, App.Vector(1.5, 1.5, 0.9)), "#9BB8AA"),
    "BatteryReference": ("电池参考 · 301230 30 × 12 × 3 mm",
                         Part.makeBox(30.0, 12.0, 3.0, App.Vector(3.0, 38.0, 1.0)), "#E6B96E"),
    "ScreenReference": ("屏幕参考 · 37.4 × 32 × 1.1 mm",
                        Part.makeBox(37.4, 32.0, 1.1, App.Vector(3.0, 2.0, 1.8)), "#C5D5E5"),
    "UsbReference": ("USB-C 参考包络 · 8 × 8.94 × 3.2 mm",
                     Part.makeBox(8.0, 8.94, 3.2, App.Vector(76.0, 27.5, 1.8)), "#AEB9C8"),
    "McuReference": ("主控参考包络 · 8.5 × 6.5 × 2.2 mm",
                     Part.makeBox(8.5, 6.5, 2.2, App.Vector(74.0, 37.0, 1.8)), "#A7C9E5"),
}
for name, (label, shape, color) in refs.items():
    ref = add_feature(doc, name, label, shape, "reference", color, visible=False)
    ref.SourceAndLimits = "E14 空间参考，不是已验证料号包络；隐藏以便单独打印壳体。"

for index, x in enumerate((38.0, 45.0, 52.0), 1):
    shape = Part.makeBox(5.2, 5.2, 1.6, App.Vector(x, 38.0, 1.8))
    ref = add_feature(doc, f"Button{index}Reference", f"SW{index} 参考包络", shape,
                      "reference", "#E4B28F", visible=False)
    ref.SourceAndLimits = "E14 按键本体包络；键帽、行程和弹片未验证。"

# A separate guide solid records the intended USB opening and is hidden from
# normal views; it is useful when comparing plug clearance in a slicer.
usb_guide = add_feature(doc, "UsbOpeningGuide", "USB-C 侧开口检查体",
                        Part.makeBox(10.0, 12.5, 4.0, App.Vector(W - 9.5, 25.75, 1.5)),
                        "reference", "#C4CBD4", visible=False)
usb_guide.SourceAndLimits = "开口检查用，不是壳体实体；插头外壳和插拔受力尚未验证。"


def intersections(first, second):
    return first.Shape.common(second.Shape).Volume


doc.recompute()
objects = [bottom, top, ledge]
invalid = [obj.Name for obj in objects if obj.Shape.isNull() or not obj.Shape.isValid()]
solid_counts = {obj.Name: len(obj.Shape.Solids) for obj in objects}
shell_intersections = []
for first in objects:
    for second in objects:
        if first.Name >= second.Name:
            continue
        volume = intersections(first, second)
        if volume > 1e-6:
            shell_intersections.append({"objects": [first.Name, second.Name], "volume_mm3": round(volume, 6)})

# Reference clearance checks.  The top cap should clear every reference; the
# lower shell should contain the board and battery without intersecting them.
reference_clearance = []
for shell in (bottom, top):
    for name, (_, shape, _) in refs.items():
        volume = shell.Shape.common(shape).Volume
        if volume > 1e-6:
            reference_clearance.append({"shell": shell.Name, "reference": name, "volume_mm3": round(volume, 6)})
for x in (38.0, 45.0, 52.0):
    shape = Part.makeBox(5.2, 5.2, 1.6, App.Vector(x, 38.0, 1.8))
    volume = top.Shape.common(shape).Volume
    if volume > 1e-6:
        reference_clearance.append({"shell": top.Name, "reference": "button", "volume_mm3": round(volume, 6)})

report = {
    "status": "E14_ENCLOSURE_V1_PRINTABLE_SAMPLE_NOT_PRODUCTION_RELEASE",
    "model": MODEL.name,
    "outer_mm": [W, H, OUTER_H],
    "shells": {
        "bottom": {"base_mm": BOTTOM_BASE, "top_mm": BOTTOM_TOP, "wall_mm": WALL},
        "top": {"start_mm": TOP_START, "cap_bottom_mm": TOP_CAP_BOTTOM,
                "cap_mm": CAP, "wall_mm": WALL},
    },
    "openings": {
        "screen_window_mm": [39.0, 33.6],
        "button_holes": {"count": 3, "diameter_mm": 4.0},
        "usb_side_opening_mm": [10.0, 12.5, 3.6],
    },
    "battery_relief_mm": [32.0, 13.0, 0.45],
    "thickness_budget_mm": {
        "outer_target": OUTER_H,
        "bottom_floor_nominal": BOTTOM_BASE,
        "battery_relief_floor": BOTTOM_BASE - 0.35,
        "top_cap": CAP,
        "mcu_to_cap_nominal": TOP_CAP_BOTTOM - (1.8 + 2.2),
    },
    "bounding_boxes_mm": {
        obj.Name: [round(obj.Shape.BoundBox.XMin, 3), round(obj.Shape.BoundBox.YMin, 3),
                   round(obj.Shape.BoundBox.ZMin, 3), round(obj.Shape.BoundBox.XLength, 3),
                   round(obj.Shape.BoundBox.YLength, 3), round(obj.Shape.BoundBox.ZLength, 3)]
        for obj in objects
    },
    "geometry_checks": {
        "invalid_shapes": invalid,
        "shell_solids": solid_counts,
        "shell_intersections": shell_intersections,
        "shell_reference_intersections": reference_clearance,
        "valid": not (invalid or shell_intersections or reference_clearance)
                    and solid_counts["BottomShell"] == 1
                    and solid_counts["TopShell"] == 1
                    and solid_counts["ScreenLedge"] >= 1,
    },
    "limitations": [
        "This is a printable first-pass verification sample, not a production shell.",
        "No snap-fit, screw boss, gasket, adhesive pocket, or confirmed split retention is designed.",
        "Battery relief assumes only a 30 × 12 × 3 mm nominal body; protection board, leads, tape and swelling allowance are unknown.",
        "Screen glass, FPC bend radius, button cap height and USB plug strain relief require physical samples.",
        "The E14 PCB is still unrouted and has no released board outline/edge-cut file.",
        "SLA/FDM wall strength, print shrinkage, hole compensation and finish are unverified.",
        "STL and STEP files here are sample-print outputs; they must not be sent to production without DFM and assembly sign-off.",
    ],
}

if not report["geometry_checks"]["valid"]:
    raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))

doc.recompute()
doc.saveAs(str(MODEL))
Part.export([bottom, top, ledge], str(STEP))

# Mesh export is useful for a local slicer check; it is still marked as a
# sample in the report and intentionally does not include hidden references.
try:
    import Mesh
    Mesh.export([bottom], str(BOTTOM_STL))
    Mesh.export([top], str(TOP_STL))
except Exception as exc:
    report["mesh_export_warning"] = str(exc)

REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({
    "model": str(MODEL),
    "step": str(STEP),
    "bottom_stl": str(BOTTOM_STL),
    "top_stl": str(TOP_STL),
    "report": str(REPORT),
    "geometry_checks": report["geometry_checks"],
}, ensure_ascii=False, indent=2))
