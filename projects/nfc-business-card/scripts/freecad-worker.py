"""FreeCAD-only worker; launched through freecad-study.py, not system Python."""

import json
import os
from pathlib import Path
import runpy
import traceback

import FreeCAD as App
import Part


job = json.loads(Path(os.environ["NFC_CARD_FREECAD_JOB"]).read_text())
output = Path(job["output"])


def check_geometry(doc):
    doc.recompute()
    shapes = [obj for obj in doc.Objects if hasattr(obj, "Shape")]
    invalid = [obj.Name for obj in shapes if obj.Shape.isNull() or not obj.Shape.isValid()]
    physical = [obj for obj in shapes if getattr(obj, "Role", None) == "component"]
    physical.append(doc.BoardEnvelope)
    collisions = []
    for i, first in enumerate(physical):
        for second in physical[i + 1:]:
            if first.Shape.common(second.Shape).Volume > 1e-6:
                collisions.append([first.Name, second.Name])
    params = doc.StudyParameters
    cavity = Part.makeBox(float(params.CardWidth) - 1.6, float(params.CardHeight) - 1.6,
                          float(params.CardThickness - params.FrontWall - params.BackWall),
                          App.Vector(0.8, 0.8, float(params.BackWall)))
    outside = [obj.Name for obj in physical if obj.Name != "UsbBody"
               and obj.Shape.cut(cavity).Volume > 1e-6]
    nfc = doc.NfcReserve.Shape.BoundBox
    conflicts = []
    nfc_checked = physical + [obj for obj in shapes if getattr(obj, "KeepOutsideNfc", False)]
    for obj in nfc_checked:
        bounds = obj.Shape.BoundBox
        if obj.Name != "BoardEnvelope" and min(bounds.XMax, nfc.XMax) > max(bounds.XMin, nfc.XMin) \
                and min(bounds.YMax, nfc.YMax) > max(bounds.YMin, nfc.YMin):
            conflicts.append(obj.Name)
    clearance_conflicts = []
    for zone in shapes:
        if not getattr(zone, "CheckPhysicalClearance", False):
            continue
        for obj in physical:
            if obj.Name == "BoardEnvelope" or obj.Name in zone.AllowedComponents:
                continue
            if zone.Shape.common(obj.Shape).Volume > 1e-6:
                clearance_conflicts.append([zone.Name, obj.Name])
    board_solids = len(doc.BoardEnvelope.Shape.Solids)
    report = {"valid": not (invalid or collisions or outside or conflicts or clearance_conflicts) and board_solids == 1,
              "shape_count": len(shapes), "invalid_shapes": invalid,
              "physical_collisions": collisions, "outside_cavity_excluding_usb": outside,
              "components_over_nfc": conflicts, "board_connected_solids": board_solids,
              "reserved_space_conflicts": clearance_conflicts,
              "limits": "PCBA envelope study only; fixed 0.8 mm side-wall assumption; no routing, RF, FPC or DFM validation."}
    (output / "geometry-check.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["valid"]:
        raise ValueError("Geometry check failed; see geometry-check.json")
    return report


def render_preview(index=0):
    try:
        view = Gui.activeDocument().activeView()
        if index == 0 and abs(view.getCameraOrientation().Angle) < 0.1:
            raise RuntimeError("Isometric-view camera did not settle")
        name = ("isometric.png", "top.png")[index]
        Gui.updateGui()
        view.redraw()
        view.saveImage(str(output / name), 1600, 1000, "White")
        picture = QtGui.QImage(str(output / name))
        colors = {picture.pixel(x, y) for x in range(0, picture.width(), 20)
                  for y in range(0, picture.height(), 20)}
        if picture.isNull() or len(colors) < 5:
            raise RuntimeError(f"Preview appears blank: {name}")
        if index == 0:
            doc.saveAs(str(output / "pcba-layout-view.FCStd"))
            view.viewTop()
            view.fitAll()
            # Let the camera animation and OpenGL frame complete before capture.
            QtCore.QTimer.singleShot(1500, lambda: render_preview(1))
            return
        if abs(view.getCameraOrientation().Angle) > 1e-6:
            raise RuntimeError("Top-view camera did not settle")
        result = {"ok": True, "geometry": geometry, "rendered": ["isometric.png", "top.png"],
                  "visual_review": "Pending human or agent inspection; rendering alone is not visual approval."}
    except Exception:
        result = {"ok": False, "error": traceback.format_exc()}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    App.closeDocument(doc.Name)
    QtWidgets.QApplication.instance().quit()


def prepare_preview():
    App.setActiveDocument(doc.Name)
    view = Gui.activeDocument().activeView()
    view.viewAxonometric()
    view.fitAll()
    QtCore.QTimer.singleShot(1500, render_preview)


try:
    if job["action"] == "generate":
        os.environ["NFC_CARD_LAYOUT_OUTPUT"] = str(output)
        os.environ["NFC_CARD_LAYOUT_VARIANT"] = job.get("variant", "baseline")
        generated = runpy.run_path(str(Path(job["project"]) / "enclosure/pcba-layout.FCMacro"))
        App.closeDocument(generated["doc"].Name)
        model = output / "pcba-layout.FCStd"
    else:
        model = Path(job["model"])
    doc = App.openDocument(str(model))
    geometry = check_geometry(doc)
    if job["action"] == "generate":
        solids = [obj for obj in doc.Objects if getattr(obj, "Role", None) == "component"]
        Part.export(solids + [doc.BoardEnvelope], str(output / "pcba-envelopes.step"))
    if job["action"] == "preview":
        import FreeCADGui as Gui
        from PySide import QtCore, QtGui, QtWidgets

        for obj in doc.Objects:
            if hasattr(obj, "Shape"):
                obj.ViewObject.Visibility = True
            if hasattr(obj, "StudyColor"):
                obj.ViewObject.ShapeColor = obj.StudyColor
            if getattr(obj, "Role", None) == "reserve":
                obj.ViewObject.Transparency = 65
        doc.FrontPlane.ViewObject.Visibility = False
        doc.OuterEnvelope.ViewObject.DisplayMode = "Wireframe"
        # Startup can restore a saved camera after the macro has returned.
        QtCore.QTimer.singleShot(1500, prepare_preview)
    else:
        (output / "result.json").write_text(json.dumps({"ok": True, "geometry": geometry}, indent=2) + "\n")
        App.closeDocument(doc.Name)
except Exception:
    (output / "result.json").write_text(json.dumps({"ok": False, "error": traceback.format_exc()}, indent=2) + "\n")
    if App.GuiUp:
        from PySide import QtCore, QtWidgets
        QtCore.QTimer.singleShot(0, QtWidgets.QApplication.instance().quit)
