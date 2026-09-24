# R1 transparent enclosure

## 当前确定方案

The [current R1](../README.md) uses two transparent printed halves and three printed keys. Overall size is **85.2 × 53.2 × 5.8 mm**; panels are 0.8 mm, perimeter walls 1.2 mm. The display aperture is open and there are no internal crossbeams. Nominal CAD fit passes; printing, flex insertion, battery fit and adhesive closure still need physical validation.

| File | Purpose |
| --- | --- |
| [Assembly FCStd](r1-clear-5.8/e20-clear-assembly.FCStd) | Editable FreeCAD document |
| [Assembly STEP](r1-clear-5.8/e20-clear-assembly.step) | Complete mechanical assembly for review; not the file to print as one solid |
| [Tray STL](r1-clear-5.8/e20-clear-tray.stl) | Print the lower enclosure, dimensions in mm |
| [Lid STL](r1-clear-5.8/e20-clear-lid.stl) | Print the upper enclosure |
| [Keys STL](r1-clear-5.8/e20-clear-keys.stl) | Print all three separate keys |
| [Tray STEP](r1-clear-5.8/e20-clear-tray.step), [lid STEP](r1-clear-5.8/e20-clear-lid.step) | Solid part exports |
| [Geometry report](r1-clear-5.8/e20-clear-report.json) | Nominal intersections and clearances |
| [Assembly preview](r1-clear-5.8/e20-clear-assembled-iso.png), [open preview](r1-clear-5.8/e20-clear-open-iso.png) | Visual review |
| [Actual copper](renders/r1-routed-front-rear.png) | PCB front/rear review |
| [Generator](e20-clear-shell.py), [preview macro](e20-clear-preview.FCMacro) | Rebuild from `hardware/r1-design.json`; filenames retain their E20 origin |

[Mechanical check](../hardware/records/r1-mechanical-check.json): rear debug access is aligned, supports remain on the board, and print meshes are closed. These checks do not certify resin tolerances or strength. [Historical models](../archive/pre-r1/enclosure/) are preserved separately.
