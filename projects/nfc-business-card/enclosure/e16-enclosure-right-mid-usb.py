"""Generate an E16-coordinate enclosure sample for the right-mid USB layout.

The USB-C receptacle moved to the middle of the right board edge.  This sample
follows the E16 EasyEDA coordinates: right-wall slot for the connector, screen
window shifted up to clear the button column, three evenly spaced keys, and a
reference for the connector body that overhangs the board edge.
It is a coordination sample, not a production enclosure.
"""

from pathlib import Path
import json

import FreeCAD as App
import Part
import Mesh

OUT = Path(__file__).resolve().parent
MODEL = OUT / "nfc-card-e16-enclosure-v1.FCStd"
STEP = OUT / "nfc-card-e16-enclosure-v1.step"
BOTTOM_STL = OUT / "nfc-card-e16-bottom-v1.stl"
TOP_STL = OUT / "nfc-card-e16-top-v1.stl"
REPORT = OUT / "nfc-card-e16-enclosure-v1-report.json"

if any(path.exists() for path in (MODEL, STEP, BOTTOM_STL, TOP_STL, REPORT)):
    raise SystemExit("Existing E16 enclosure output refused; choose a new version instead of overwriting.")

W, H = 84.0, 52.0
OUTER_H = 5.0
WALL = 1.2
BOTTOM_BASE = 0.8
SPLIT_Z = 2.2
TOP_CAP_BOTTOM = 4.2
CAP = 0.8
PCB_T = 0.8
PCB_Z0 = 1.7

# E16 board outline and USB slot, straight from the saved sheet (mm).
BOARD_OUTLINE = [(0, 0), (0, 52), (84, 52), (84, 20.62), (77.5, 20.62),
                 (77.5, 11.38), (84, 11.38), (84, 0)]
USB_SLOT_Y = (10.38, 21.62)      # J1 shell span across the row
USB_SLOT_Z = (PCB_Z0 - 1.25, PCB_Z0 + PCB_T + 1.2)
USB_OVERHANG_X = 88.45           # connector body reaches this far past x = 84


def rounded_prism(width, height, z0, thickness, radius, x0=0.0, y0=0.0):
    if radius <= 0:
        return Part.makeBox(width, height, thickness, App.Vector(x0, y0, z0))
    shape = Part.makeBox(width - 2 * radius, height, thickness, App.Vector(x0 + radius, y0, z0))
    shape = shape.fuse(Part.makeBox(width, height - 2 * radius, thickness, App.Vector(x0, y0 + radius, z0)))
    for cx, cy in ((x0 + radius, y0 + radius), (x0 + width - radius, y0 + radius),
                   (x0 + radius, y0 + height - radius), (x0 + width - radius, y0 + height - radius)):
        shape = shape.fuse(Part.makeCylinder(radius, thickness, App.Vector(cx, cy, z0)))
    return shape.removeSplitter()


def add_feature(doc, name, label, shape, role, color, visible=True):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Role", "Evidence")
    obj.Role = role
    obj.addProperty("App::PropertyString", "SourceAndLimits", "Evidence")
    obj.SourceAndLimits = "E16 右侧中部 USB 坐标协调样件；真实最大包络、公差与装配方式仍待确认。"
    obj.addProperty("App::PropertyColor", "StudyColor", "Appearance")
    obj.StudyColor = tuple(int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    if App.GuiUp:
        obj.ViewObject.ShapeColor = obj.StudyColor
        obj.ViewObject.Visibility = visible
    return obj


doc = App.newDocument("NfcCardE16EnclosureV1")
doc.Label = "NFC 名片 · E16 右侧中部 USB 外壳协调样件 V1"
doc.Comment = "按 E16 落盘坐标协调右壁 USB 开口、三键与屏窗；不是生产壳。"

params = doc.addObject("App::FeaturePython", "EnclosureParameters")
params.Label = "E16 外壳参数与证据"
for name, value in (("CardWidth", W), ("CardHeight", H), ("OuterHeight", OUTER_H),
                    ("Wall", WALL), ("BottomBase", BOTTOM_BASE), ("SplitZ", SPLIT_Z),
                    ("TopCapBottom", TOP_CAP_BOTTOM), ("CapThickness", CAP),
                    ("PcbThickness", PCB_T), ("PcbZ0", PCB_Z0)):
    params.addProperty("App::PropertyLength", name, "Envelope")
    setattr(params, name, value)
params.addProperty("App::PropertyString", "Status", "Evidence")
params.Status = "E16_ENCLOSURE_V1_SAMPLE_NOT_PRODUCTION_RELEASE"
params.addProperty("App::PropertyString", "Source", "Evidence")
params.Source = "e16-right-mid-snapshot.json; J1=(78.5,16.0) mm; keys y=3.3/9.2/15.1 mm"

# Board reference: the saved E16 outline. Kept as a solid because the outline
# and the cavity size basis are still a release gate.
wire = Part.makePolygon([App.Vector(x, y, PCB_Z0) for x, y in BOARD_OUTLINE] +
                        [App.Vector(*BOARD_OUTLINE[0], PCB_Z0)])
board = add_feature(doc, "BoardReference", "E16 板框参考（Layer 11，右边缘缺口）",
                    Part.Face(wire).extrude(App.Vector(0, 0, PCB_T)),
                    "reference", "#9BB8AA", visible=False)
board.SourceAndLimits = "按 E16 Layer 11 快照重建；84 × 52 是 PCB 板框还是外壳外缘仍未定。"

# Bottom shell with the right-wall USB slot.
bottom_shape = rounded_prism(W, H, 0.0, SPLIT_Z, 2.0)
bottom_shape = bottom_shape.cut(rounded_prism(W - 2 * WALL, H - 2 * WALL, BOTTOM_BASE,
                                              SPLIT_Z - BOTTOM_BASE + 0.2, 0.8, WALL, WALL))
usb_slot = Part.makeBox(USB_OVERHANG_X - (W - WALL - 0.3),
                        USB_SLOT_Y[1] - USB_SLOT_Y[0],
                        USB_SLOT_Z[1] - USB_SLOT_Z[0],
                        App.Vector(W - WALL - 0.3, USB_SLOT_Y[0], USB_SLOT_Z[0]))
bottom_shape = bottom_shape.cut(usb_slot).removeSplitter()
bottom_shape = bottom_shape.cut(rounded_prism(32.0, 13.0, -0.1, 0.45, 1.0, 2.0, 1.0)).removeSplitter()
# the connector body dips below the PCB plane, so the floor under it is relieved
connector_relief = Part.makeBox(W - WALL - 0.3 - 75.9, USB_SLOT_Y[1] - USB_SLOT_Y[0],
                                (PCB_Z0 - 0.75) + 0.1,
                                App.Vector(75.9, USB_SLOT_Y[0], -0.1))
bottom_shape = bottom_shape.cut(connector_relief).removeSplitter()
bottom = add_feature(doc, "BottomShell", "下壳 · 右壁 USB 开口", bottom_shape,
                     "print_candidate", "#8FA9C1")

# Top shell: screen window moved up 1.30 mm, three evenly spaced key holes.
top_shape = rounded_prism(W, H, SPLIT_Z, OUTER_H - SPLIT_Z, 2.0)
top_shape = top_shape.cut(rounded_prism(W - 2 * WALL, H - 2 * WALL, SPLIT_Z,
                                        TOP_CAP_BOTTOM - SPLIT_Z + 0.05, 0.8, WALL, WALL))
top_shape = top_shape.cut(Part.makeBox(39.0, 33.6, CAP + 0.4, App.Vector(1.2, 17.5, TOP_CAP_BOTTOM - 0.2)))
for y in (3.30, 9.20, 15.10):
    top_shape = top_shape.cut(Part.makeCylinder(2.0, CAP + 0.4, App.Vector(38.1, y, TOP_CAP_BOTTOM - 0.2)))
top_shape = top_shape.cut(Part.makeBox(USB_OVERHANG_X - (W - WALL - 0.3),
                                       USB_SLOT_Y[1] - USB_SLOT_Y[0],
                                       USB_SLOT_Z[1] - USB_SLOT_Z[0],
                                       App.Vector(W - WALL - 0.3, USB_SLOT_Y[0], USB_SLOT_Z[0]))).removeSplitter()
top = add_feature(doc, "TopShell", "上壳 · 屏窗 + 三键孔 + 右壁 USB 开口", top_shape,
                  "print_candidate", "#B9C9DC")

# Component references in E16 coordinates.
references = {
    "UsbConnectorReference": ("J1 USB4500 本体 + 板外外伸（x 84→88.45）",
                              Part.makeBox(USB_OVERHANG_X - 76.42, 11.24, 3.16,
                                           App.Vector(76.42, 10.38, PCB_Z0 - 1.2)), "#AEB9C8"),
    "ScreenReference": ("屏幕机械区参考 · 37.42 × 31.90 mm",
                        Part.makeBox(37.42, 31.90, 1.1, App.Vector(2.0, 18.3, PCB_Z0 + PCB_T)), "#C5D5E5"),
    "BatteryReference": ("301230 目标 · 30 × 12 × 3 mm",
                         Part.makeBox(30.0, 12.0, 3.0, App.Vector(3.0, 1.5, PCB_Z0 - 0.3)), "#E6B96E"),
    "McuReference": ("U1 MDBT50Q 参考 · 10.5 × 15.5 mm，天线朝下",
                     Part.makeBox(10.5, 15.5, 2.2, App.Vector(59.75, 0.25, PCB_Z0 + PCB_T)), "#A7C9E5"),
    "FpcReference": ("J2 FPC 参考", Part.makeBox(6.8, 16.5, 2.2, App.Vector(48.0, 24.25, PCB_Z0 + PCB_T)), "#B8D4C0"),
}
for name, (label, shape, color) in references.items():
    ref = add_feature(doc, name, label, shape, "reference", color, visible=False)
    ref.SourceAndLimits = "E16 快照参考包络；不是已核准料号最大外形。"

for index, y in enumerate((3.30, 9.20, 15.10), 1):
    ref = add_feature(doc, f"Button{index}Reference", f"SW{index} 参考 · y={y:.2f} mm",
                      Part.makeBox(5.2, 5.2, 1.6, App.Vector(35.5, y - 2.6, PCB_Z0 + PCB_T)),
                      "reference", "#E4B28F", visible=False)
    ref.SourceAndLimits = "按键本体参考；键帽、行程与弹片未验证。"

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
        if name in ("ScreenReference", "UsbConnectorReference", "McuReference", "FpcReference"):
            continue  # these sit inside the cavity or pass through the intended slot
        volume = shell.Shape.common(shape).Volume
        if volume > 1e-6:
            reference_intersections.append({"shell": shell.Name, "reference": name, "volume_mm3": round(volume, 6)})

# The connector body must pass through the wall slot without touching the shell.
connector = references["UsbConnectorReference"][1]
connector_shell_contact = {o.Name: round(o.Shape.common(connector).Volume, 6) for o in physical}
findings = []
for item in reference_intersections:
    findings.append(f"{item['reference']} intersects {item['shell']} by {item['volume_mm3']} mm3 (check the height budget)")
if any(v > 1e-6 for v in connector_shell_contact.values()):
    findings.append("USB connector body still touches the shell; the wall slot needs a bigger opening")

report = {
    "status": "E16_ENCLOSURE_V1_SAMPLE_NOT_PRODUCTION_RELEASE",
    "outer_mm": [W, H, OUTER_H],
    "usb_slot": {"edge": "x=84 right wall", "y_mm": list(USB_SLOT_Y), "z_mm": list(USB_SLOT_Z),
                 "through_x_mm": [W - WALL - 0.3, USB_OVERHANG_X]},
    "screen_window_mm": [1.2, 17.5, 39.0, 33.6],
    "button_holes_y_mm": [3.30, 9.20, 15.10],
    "geometry_checks": {
        "invalid_shapes": invalid,
        "shell_solids": {o.Name: len(o.Shape.Solids) for o in physical},
        "shell_intersections": shell_intersections,
        "shell_reference_intersections": reference_intersections,
        "connector_shell_contact_mm3": connector_shell_contact,
        "findings": findings,
        "valid": not invalid and not shell_intersections
                 and all(v <= 1e-6 for v in connector_shell_contact.values()),
    },
    "limitations": [
        "Coordination sample only; not a production enclosure.",
        "Size basis unresolved: the saved board is 84 x 52 mm while the shell cavity is 81.6 x 49.6 mm.",
        "Connector body reaches x = 88.45 mm, so the plug envelope extends past the 84 mm card length.",
        "Battery uses a nominal target without supplier maximum envelope, leads, tape or swelling allowance.",
        "Key caps, screen bonding, USB plug strain relief and wall tolerances need physical samples.",
    ],
}
assert report["geometry_checks"]["valid"], report
doc.recompute()
doc.saveAs(str(MODEL))
Part.export([bottom, top], str(STEP))
Mesh.export([bottom], str(BOTTOM_STL))
Mesh.export([top], str(TOP_STL))
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"model": str(MODEL), "valid": report["geometry_checks"]["valid"],
                  "contact": connector_shell_contact}, ensure_ascii=False))
