"""Generate the E16 enclosure sample V5 for the right-mid USB layout.

V5 fixes a defect found by probing the saved V3 solid: V3 built both printed
plates from the L-shaped *board* outline, so the battery bite had no floor and
no ceiling - the cell sat in a 33.5 x 15 mm through-opening - and the rib that
was meant to stiffen the pocket ceiling floated in mid air (TopShell reported
two solids).  The plates now follow the card outline minus the USB notch, and
the 1.0 mm ledge still follows the L-shaped board outline, so the pocket is
closed and only the board-free area keeps its missing ledge.  The report
records the floor and ceiling volumes as a regression check.

V2 fixes two problems recorded in the V1 report:

* the connector body reaches only x = 83.2 mm, not 88.45 mm and not the
  85.3 mm a first reading of the drawing suggested.  The exporter's STEP
  model of J1 measures 76.7 -> 83.2 mm in x (6.5 mm body length, matching
  the GCT catalogue) and 10.22 -> 21.77 mm in y, so the mating face sits
  0.8 mm *inside* the board edge and the card stays 84 mm long.
* the size basis is resolved as a laminate shell: the PCB keeps its 84 x 52
  outline and is the card body, and both shells sit inside that outline with
  a 1.0 mm inboard ledge, so the card's outer size equals the PCB outline.

The height stack keeps the 5.0 mm target by moving the 301230 cell onto the
PCB top face (the board's lower-left band is component-free) and using thin
printed plates.  Battery maximum envelope, adhesive, swelling, key caps,
screen bonding and wall tolerances are still unverified, so this stays a
sample.
"""

from pathlib import Path
import json

import FreeCAD as App
import Part
import Mesh

OUT = Path(__file__).resolve().parent
MODEL = OUT / "nfc-card-e16-enclosure-v5.FCStd"
STEP = OUT / "nfc-card-e16-enclosure-v5.step"
BOTTOM_STL = OUT / "nfc-card-e16-bottom-v5.stl"
TOP_STL = OUT / "nfc-card-e16-top-v5.stl"
CAPS_STL = OUT / "nfc-card-e16-keycaps-v5.stl"
REPORT = OUT / "nfc-card-e16-enclosure-v5-report.json"

if any(path.exists() for path in (MODEL, STEP, BOTTOM_STL, TOP_STL, CAPS_STL, REPORT)):
    raise SystemExit("Existing E16 enclosure V2 output refused; choose a new version instead of overwriting.")

# --- size basis -------------------------------------------------------------
W, H = 84.0, 52.0                 # card outline == PCB outline (laminate)
PLATE_B, GAP_B = 0.4, 0.3         # bottom plate thickness, clearance under PCB
PCB_T = 0.8                       # GCT USB4500 requires a 0.80 mm board
CAV_T = 2.5                       # top cavity: panel + parts, cell now sits in the board bite
PLATE_T = 0.5                     # top bezel plate
OUTER_H = PLATE_B + GAP_B + PCB_T + CAV_T + PLATE_T
PCB_Z0 = PLATE_B + GAP_B
SPLIT_Z = PCB_Z0 + PCB_T
TOP_PLATE_Z0 = SPLIT_Z + CAV_T
RIM = 1.0                         # inboard ledge width
ROUND = 2.0

# L-shape: the lower-left 33.5 x 15 mm battery bite is cut out of the board
BOARD_OUTLINE = [(33.5, 0), (33.5, 15), (0, 15), (0, 52), (84, 52), (84, 20.62),
                 (77.5, 20.62), (77.5, 11.38), (84, 11.38), (84, 0)]
BITE = (0.0, 0.0, 33.5, 15.0)
USB_SLOT_Y = (10.22, 21.77)       # connector body width, measured from the exported STEP
USB_FRONT_X = 83.2                # body front: 0.8 mm inside the board edge (STEP measurement)
USB_BODY_BACK_X = 76.7            # body back edge (6.5 mm body length, matches the GCT catalogue)
USB_BODY_Z = (PCB_Z0, PCB_Z0 + 3.17)
BATTERY = (2.5, 1.5, 30.0, 12.0, 3.0)
# GDEH0154E01: 37.32 (W) x 31.8 (H) x 0.85 (D); active area 27 x 27 with 2.4 mm
# borders on three sides and 7.92 mm on the FPC side (drawing page 5).
SCREEN = (2.0, 18.3, 37.32, 31.8)      # x0, y0, w, h
SCREEN_T = 0.85
SCREEN_ACTIVE = (4.4, 20.7, 27.0, 27.0)  # active area, FPC exits towards +x
SCREEN_Z0 = 3.05                        # clears the tallest part under the panel (1.51 mm above the PCB top)
WINDOW_MARGIN = 0.4
KEY_X, KEY_Y = 38.1, (3.30, 15.10)      # two SKQGABE010 switches, PCB snapshot


def outline_prism(z0, thickness):
    wire = Part.makePolygon([App.Vector(x, y, z0) for x, y in BOARD_OUTLINE] +
                            [App.Vector(*BOARD_OUTLINE[0], z0)])
    return Part.Face(wire).extrude(App.Vector(0, 0, thickness))


# The printed plates cover the whole card except the USB notch; only the ledges
# follow the board outline, which is L-shaped because of the battery bite.
CARD_PLATE_OUTLINE = [(0, 0), (84, 0), (84, 11.38), (77.5, 11.38), (77.5, 20.62),
                      (84, 20.62), (84, 52), (0, 52)]


def plate_prism(z0, thickness):
    wire = Part.makePolygon([App.Vector(x, y, z0) for x, y in CARD_PLATE_OUTLINE] +
                            [App.Vector(*CARD_PLATE_OUTLINE[0], z0)])
    return Part.Face(wire).extrude(App.Vector(0, 0, thickness))


def frame_prism(width, z0, thickness):
    """A 1.0 mm inboard frame that follows the board outline."""
    outer = outline_prism(z0, thickness)
    inner_outline = [(RIM, RIM), (W - RIM, RIM), (W - RIM, H - RIM), (RIM, H - RIM)]
    wire = Part.makePolygon([App.Vector(x, y, z0) for x, y in inner_outline] +
                            [App.Vector(*inner_outline[0], z0)])
    return outer.cut(Part.Face(wire).extrude(App.Vector(0, 0, thickness))).removeSplitter()


def add_feature(doc, name, label, shape, role, color, visible=True):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Role", "Evidence")
    obj.Role = role
    obj.addProperty("App::PropertyString", "SourceAndLimits", "Evidence")
    obj.SourceAndLimits = "E16 右侧中部 USB 协调样件 V2；真实最大包络、公差与装配方式仍待确认。"
    obj.addProperty("App::PropertyColor", "StudyColor", "Appearance")
    obj.StudyColor = tuple(int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    if App.GuiUp:
        obj.ViewObject.ShapeColor = obj.StudyColor
        obj.ViewObject.Visibility = visible
    return obj


doc = App.newDocument("NfcCardE16EnclosureV5")
doc.Label = "NFC 名片 · E16 右侧中部 USB 外壳协调样件 V5"
doc.Comment = "外壳外缘 = PCB 板框（叠层式）；连接器前缘按原厂图纸修正到 x=85.3。"

params = doc.addObject("App::FeaturePython", "EnclosureParameters")
params.Label = "E16 外壳 V5 参数与证据"
for name, value in (("CardWidth", W), ("CardHeight", H), ("OuterHeight", OUTER_H),
                    ("BottomPlate", PLATE_B), ("BottomGap", GAP_B), ("PcbThickness", PCB_T),
                    ("TopCavity", CAV_T), ("TopPlate", PLATE_T), ("PcbZ0", PCB_Z0), ("Ledge", RIM)):
    params.addProperty("App::PropertyLength", name, "Envelope")
    setattr(params, name, value)
params.addProperty("App::PropertyString", "Status", "Evidence")
params.Status = "E16_ENCLOSURE_V5_SAMPLE_NOT_PRODUCTION_RELEASE"
params.addProperty("App::PropertyString", "Source", "Evidence")
params.Source = ("e16-right-mid-snapshot.json; J1 envelope measured from the "
                 "pcb_ManufactureData.get3DFile STEP export; battery target 30 x 12 x 3 mm")

# --- references -------------------------------------------------------------
references = {
    "BoardReference": ("E16 板框参考（Layer 11，右边缘 USB 缺口）",
                       outline_prism(PCB_Z0, PCB_T), "#9BB8AA", False),
    "UsbConnectorReference": ("J1 USB4500 本体 · x 76.42→85.3，高 3.16",
                              Part.makeBox(USB_FRONT_X - USB_BODY_BACK_X, USB_SLOT_Y[1] - USB_SLOT_Y[0],
                                           USB_BODY_Z[1] - USB_BODY_Z[0],
                                           App.Vector(USB_BODY_BACK_X, USB_SLOT_Y[0], USB_BODY_Z[0])),
                              "#AEB9C8", False),
    "ScreenReference": ("GDEH0154E01 · 37.32 × 31.8 × 0.85（有效区 27×27）",
                        Part.makeBox(SCREEN[2], SCREEN[3], SCREEN_T,
                                     App.Vector(SCREEN[0], SCREEN[1], SCREEN_Z0)), "#C5D5E5", False),
    "BatteryReference": ("301230 目标 · 30 × 12 × 3 mm（坐在外壳底板上，位于板框缺口内）",
                         Part.makeBox(BATTERY[2], BATTERY[3], BATTERY[4],
                                      App.Vector(BATTERY[0], BATTERY[1], PLATE_B)), "#E6B96E", False),
    "McuReference": ("U1 MDBT50Q 参考 · 10.5 × 15.5 mm，天线朝下",
                     Part.makeBox(10.5, 15.5, 2.2, App.Vector(59.75, 0.25, SPLIT_Z)), "#A7C9E5", False),
    "FpcReference": ("J2 FPC 参考", Part.makeBox(6.8, 16.5, 2.2, App.Vector(48.0, 24.25, SPLIT_Z)),
                     "#B8D4C0", False),
}
for index, y in enumerate((3.30, 15.10), 1):
    references[f"Button{index}Reference"] = (
        f"SW{index} 参考 · y={y:.2f} mm",
        Part.makeBox(5.2, 5.2, 1.5, App.Vector(35.5, y - 2.6, SPLIT_Z)), "#E4B28F", False)

# --- bottom shell -----------------------------------------------------------
bottom_shape = plate_prism(0.0, PLATE_B)
bottom_shape = bottom_shape.fuse(frame_prism(W, PLATE_B, GAP_B)).removeSplitter()
# the connector body dips below the PCB plane, so relieve the plate under it
relief = Part.makeBox(USB_FRONT_X - (USB_BODY_BACK_X - 0.4), USB_SLOT_Y[1] - USB_SLOT_Y[0],
                      GAP_B + PLATE_B + 0.2, App.Vector(USB_BODY_BACK_X - 0.4, USB_SLOT_Y[0], -0.1))
bottom_shape = bottom_shape.cut(relief).removeSplitter()
# the bite has no board, so no ledge should stand inside the battery pocket
bite_cut = Part.makeBox(BITE[2]-BITE[0], BITE[3]-BITE[1], TOP_PLATE_Z0 - PLATE_B,
                        App.Vector(BITE[0], BITE[1], PLATE_B))
bottom_shape = bottom_shape.cut(bite_cut).removeSplitter()
bottom = add_feature(doc, "BottomShell", "下壳 · 电池挖空 + 右边缘 USB 让位", bottom_shape, "print_candidate", "#8FA9C1")

# --- top shell --------------------------------------------------------------
top_shape = plate_prism(TOP_PLATE_Z0, PLATE_T)
top_shape = top_shape.fuse(frame_prism(W, SPLIT_Z, CAV_T)).removeSplitter()

# ribs so the 0.5 mm top plate never bridges an open span unsupported.
# they run under the plate at z 3.6-4.0, above every part (tallest 3.01) and
# clear of the panel (y >= 18.3), the FPC (x 47.5-55.5) and U1 (x 59.75-70.25).
RIBS = [
    (41.0, 16.4, 47.0, 17.2),   # band between the bite and the screen, east of the key caps
    (42.6, 0.5, 43.4, 15.5),    # strip east of the keys
    (1.0, 7.1, 33.0, 7.9),      # across the battery pocket ceiling
]
for (x0, y0, x1, y1) in RIBS:
    top_shape = top_shape.fuse(Part.makeBox(x1-x0, y1-y0, TOP_PLATE_Z0 - 3.6,
                                            App.Vector(x0, y0, 3.6)))
top_shape = top_shape.removeSplitter()
# the connector shell clamps over the board flange, so the ledge stops beside it
top_shape = top_shape.cut(Part.makeBox(8.5, USB_SLOT_Y[1] - USB_SLOT_Y[0] + 0.2, CAV_T + 0.4,
                                       App.Vector(76.0, USB_SLOT_Y[0] - 0.1, SPLIT_Z - 0.2))).removeSplitter()
# antenna end of the MCU reaches the bottom edge, so the ledge is interrupted there
top_shape = top_shape.cut(Part.makeBox(10.9, RIM + 0.2, CAV_T,
                                       App.Vector(59.55, -0.1, SPLIT_Z))).removeSplitter()
# the first key body reaches within 0.7 mm of the bottom edge, so relieve the ledge there
top_shape = top_shape.cut(Part.makeBox(6.3, RIM + 0.2, CAV_T + 0.4,
                                       App.Vector(35.0, -0.1, SPLIT_Z))).removeSplitter()
# bezel boss over the panel border, then the window over the active area
boss = Part.makeBox(SCREEN[2], SCREEN[3], TOP_PLATE_Z0 - (SCREEN_Z0 + SCREEN_T),
                    App.Vector(SCREEN[0], SCREEN[1], SCREEN_Z0 + SCREEN_T))
top_shape = top_shape.fuse(boss).removeSplitter()
top_shape = top_shape.cut(Part.makeBox(SCREEN_ACTIVE[2] + 2 * WINDOW_MARGIN, SCREEN_ACTIVE[3] + 2 * WINDOW_MARGIN,
                                       PLATE_T + 1.2,
                                       App.Vector(SCREEN_ACTIVE[0] - WINDOW_MARGIN, SCREEN_ACTIVE[1] - WINDOW_MARGIN,
                                                  SCREEN_Z0 + SCREEN_T - 0.2)))
for y in KEY_Y:
    top_shape = top_shape.cut(Part.makeCylinder(2.3, PLATE_T + 0.4,
                                                App.Vector(KEY_X, y, TOP_PLATE_Z0 - 0.2)))
top_shape = top_shape.removeSplitter()
top = add_feature(doc, "TopShell", "上壳 · 屏窗 + 两键孔", top_shape, "print_candidate", "#B9C9DC")

top_shape = top_shape.cut(bite_cut).removeSplitter()

# --- key caps ---------------------------------------------------------------
# SKQGABE010 is 5.2 x 5.2 x 1.5 mm (Alps drawing No.1) and travels 0.25 mm, so
# its stem top sits at z = 3.0 mm - 1.0 mm below the 0.5 mm top plate. The cap
# is a flush puck that rides in the 4.6 mm hole and reaches the stem with a
# boss; the hole locates it so it needs neither a flange nor a stem socket
# (a flange would collide with the top-shell rib at y 16.4-17.2).
CAP_DISC_R, CAP_BOSS_R = 2.1, 1.6
SWITCH_TOP_Z = SPLIT_Z + 1.5
CAP_BOSS_BOTTOM_Z = SWITCH_TOP_Z + 0.05
caps = []
for index, y in enumerate(KEY_Y, 1):
    disc = Part.makeCylinder(CAP_DISC_R, PLATE_T, App.Vector(KEY_X, y, TOP_PLATE_Z0))
    boss = Part.makeCylinder(CAP_BOSS_R, TOP_PLATE_Z0 - CAP_BOSS_BOTTOM_Z,
                             App.Vector(KEY_X, y, CAP_BOSS_BOTTOM_Z))
    cap_shape = disc.fuse(boss).removeSplitter()
    caps.append(add_feature(doc, f"KeyCap{index}", f"键帽 {index} · 齐平按键 + 行程柱", cap_shape,
                            "print_candidate", "#F0C7A0"))

for name, (label, shape, color, visible) in references.items():
    ref = add_feature(doc, name, label, shape, "reference", color, visible)
    ref.SourceAndLimits = "E16 快照 / 原厂图纸参考包络；不是已核准料号最大外形。"

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
skip = ("ScreenReference", "UsbConnectorReference", "McuReference", "FpcReference", "BoardReference")
for shell in physical:
    for name, (_, shape, _, _) in references.items():
        if name in skip:
            continue
        volume = shell.Shape.common(shape).Volume
        if volume > 1e-6:
            reference_intersections.append({"shell": shell.Name, "reference": name, "volume_mm3": round(volume, 6)})
connector = references["UsbConnectorReference"][1]
contact = {o.Name: round(o.Shape.common(connector).Volume, 6) for o in physical}

# Key caps: flush face, travel to the switch stem, retained by the flange.
cap_solids = {cap.Name: len(cap.Shape.Solids) for cap in caps}
cap_shell_contact = {}
for cap in caps:
    for shell in physical:
        cap_shell_contact[f"{cap.Name}/{shell.Name}"] = round(cap.Shape.common(shell.Shape).Volume, 6)
cap_pair = round(caps[0].Shape.common(caps[1].Shape).Volume, 6) if len(caps) > 1 else None
pressed = []
for cap, y in zip(caps, KEY_Y):
    moved = cap.Shape.translated(App.Vector(0, 0, -0.25))      # full switch travel
    # body minus the stem travel: the cap must never push the switch past 0.25 mm
    body = Part.makeBox(5.2, 5.2, 1.25, App.Vector(35.5, y - 2.6, SPLIT_Z))
    pressed.append({
        "cap": cap.Name,
        "shell_mm3": round(sum(moved.common(s.Shape).Volume for s in physical), 6),
        "switch_body_mm3": round(moved.common(body).Volume, 6),
    })
keys = {
    "cap_solids": cap_solids,
    "cap_to_shell_mm3": cap_shell_contact,
    "cap_pair_intersection_mm3": cap_pair,
    "stem_top_z_mm": SWITCH_TOP_Z,
    "cap_boss_bottom_z_mm": round(CAP_BOSS_BOTTOM_Z, 3),
    "travel_mm": 0.25,
    "pressed": pressed,
}

# The battery pocket must stay closed: a floor under the cell and a ceiling
# above it. V3 shipped both as L-shaped plates, so the pocket was a through
# opening and the pocket rib floated as an extra top-shell solid.
bite_xy = Part.makeBox(BITE[2] - BITE[0], BITE[3] - BITE[1], PLATE_B, App.Vector(BITE[0], BITE[1], 0.0))
ceiling_z = Part.makeBox(BITE[2] - BITE[0], BITE[3] - BITE[1], PLATE_T,
                         App.Vector(BITE[0], BITE[1], TOP_PLATE_Z0))
pocket = {
    "floor_mm3": round(bottom.Shape.common(bite_xy).Volume, 3),
    "floor_expected_mm3": round((BITE[2] - BITE[0]) * (BITE[3] - BITE[1]) * PLATE_B, 3),
    "ceiling_mm3": round(top.Shape.common(ceiling_z).Volume, 3),
    "ceiling_expected_mm3": round((BITE[2] - BITE[0]) * (BITE[3] - BITE[1]) * PLATE_T, 3),
}
solids = {o.Name: len(o.Shape.Solids) for o in physical}

findings = []
if solids.get("BottomShell") != 1 or solids.get("TopShell") != 1:
    findings.append(f"a shell is not a single solid: {solids}")
if pocket["floor_mm3"] < pocket["floor_expected_mm3"] - 0.5:
    findings.append(f"battery pocket has no floor under the cell: {pocket['floor_mm3']} mm3")
if pocket["ceiling_mm3"] < pocket["ceiling_expected_mm3"] - 0.5:
    findings.append(f"battery pocket has no ceiling above the cell: {pocket['ceiling_mm3']} mm3")
if any(v > 1e-6 for v in contact.values()):
    findings.append("USB connector body still touches the shell")
for name, count in cap_solids.items():
    if count != 1:
        findings.append(f"{name} is not a single solid: {count}")
for key, volume in cap_shell_contact.items():
    if volume > 0.01:                       # the flange face may touch the plate face
        findings.append(f"key cap touches a shell: {key} {volume} mm3")
if cap_pair:
    findings.append(f"key caps intersect each other: {cap_pair} mm3")
for item in pressed:
    if item["shell_mm3"] > 0.01:
        findings.append(f"{item['cap']} hits a shell when pressed: {item['shell_mm3']} mm3")
    if item["switch_body_mm3"] > 1e-6:
        findings.append(f"{item['cap']} drives the switch body past its travel: {item['switch_body_mm3']} mm3")
for item in reference_intersections:
    findings.append(f"{item['reference']} intersects {item['shell']} by {item['volume_mm3']} mm3")

report = {
    "status": "E16_ENCLOSURE_V5_SAMPLE_NOT_PRODUCTION_RELEASE",
    "outer_mm": [W, H, round(OUTER_H, 3)],
    "battery_bite_mm": list(BITE),
    "size_basis": {
        "structure": "laminate: L-shaped PCB outline is the card outline, shells carry a 1.0 mm inboard ledge, battery sits on the bottom plate inside the bite",
        "card_outline_mm": [W, H],
        "pcb_outline_mm": [W, H],
        "connector_front_x_mm": USB_FRONT_X,
        "connector_overhang_past_card_mm": round(USB_FRONT_X - W, 2),
        "overall_length_with_connector_mm": USB_FRONT_X,
        "business_card_reference_mm": [85.6, 54.0],
    },
    "height_stack_mm": {"bottom_plate": PLATE_B, "under_pcb_clearance": GAP_B, "pcb": PCB_T,
                        "top_cavity": CAV_T, "top_plate": PLATE_T, "total": round(OUTER_H, 3)},
    "usb": {"connector_body_x_mm": [USB_BODY_BACK_X, USB_FRONT_X], "y_mm": list(USB_SLOT_Y),
            "z_mm": [round(USB_BODY_Z[0], 3), round(USB_BODY_Z[1], 3)],
            "note": "connector sits in the board notch; the shells follow the notch so no wall slot is cut"},
    "top_shell_ribs_mm": RIBS,
    "key_caps": keys,
    "screen": {
        "module_mm": [SCREEN[2], SCREEN[3], SCREEN_T],
        "module_origin_mm": [SCREEN[0], SCREEN[1], SCREEN_Z0],
        "active_area_mm": [SCREEN_ACTIVE[0], SCREEN_ACTIVE[1], SCREEN_ACTIVE[2], SCREEN_ACTIVE[3]],
        "window_mm": [SCREEN_ACTIVE[0] - WINDOW_MARGIN, SCREEN_ACTIVE[1] - WINDOW_MARGIN,
                      SCREEN_ACTIVE[2] + 2 * WINDOW_MARGIN, SCREEN_ACTIVE[3] + 2 * WINDOW_MARGIN],
        "source": "GDEH0154E01 mechanical drawing: 37.32 x 31.8 x 0.85, 27x27 active with 2.4 mm borders",
    },
    "button_holes_y_mm": [3.30, 15.10],
    "geometry_checks": {
        "invalid_shapes": invalid,
        "shell_solids": solids,
        "pocket_mm3": pocket,
        "shell_intersections": shell_intersections,
        "shell_reference_intersections": reference_intersections,
        "connector_shell_contact_mm3": contact,
        "findings": findings,
        "valid": not invalid and not findings and not shell_intersections
        and all(v <= 1e-6 for v in contact.values()),
    },
    "limitations": [
        "Coordination sample only; not a production enclosure.",
        "Battery is placed on the PCB top face as a 30 x 12 x 3 mm nominal target; supplier maximum, adhesive, swelling and lead bend are unverified.",
        "The 5.0 mm stack needs 0.4/0.5 mm printed plates; a thicker plate or a bigger cell pushes the card past 5.0 mm.",
        "Connector envelope (x 76.7-83.2, y 10.22-21.77, z 0-3.17 over the board) is measured from the STEP export of the saved board, so the mating face sits 0.8 mm inside the board edge; confirm against the part in hand.",
        "Key caps, screen bonding, USB plug strain relief, ledge bonding and wall tolerances need physical samples.",
        "The panel sits 1.51 mm above the PCB top (measured from the STEP export of the tallest part under the panel), so assembly needs a foam/gasket between the panel back and the components to press it against the bezel.",
    ],
}
assert report["geometry_checks"]["valid"], report
doc.recompute()
doc.saveAs(str(MODEL))
Part.export([bottom, top], str(STEP))
Mesh.export([bottom], str(BOTTOM_STL))
Mesh.export([top], str(TOP_STL))
Mesh.export(caps, str(CAPS_STL))
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"model": str(MODEL), "valid": report["geometry_checks"]["valid"],
                  "outer": report["outer_mm"], "contact": contact, "findings": findings}, ensure_ascii=False))
