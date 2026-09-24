# R1 transparent enclosure

## 当前确定方案

最新 [制造工艺评审](r1-rounded-rear-soft/manufacturing-review.md)记录 SLA 透明材料平台、薄板与配合风险和 SWD 烧录准备；五个孔按用户确认保留。几何检查通过不代表打印与装配已验收。

同日圆角加强：[更圆润的候选](r1-rounded-rear-soft/README.md)将正面／背面／俯视四角分别增至 R1.2／R0.7／R3.2 mm，外尺寸保持不变；几何与装入检查通过。背面五孔是 SWD 调试探针通道，本次保留。后续仍需验证底盖定位、胶接与打印公差。

2026-09-24 外观方向更新：采用**正面＋侧壁一体、背面嵌入独立底盖，外露边缘圆角**。[圆角与背面接缝候选](r1-rounded-rear-study/README.md)保持 85.2 × 53.2 × 5.8 mm；接缝距外轮廓约 1.33 mm，PCB 对上壳的直线装入检查通过。竖向胶接与底盖定位尚未验证，未替换以下现有模型，也未批准下单。下一步确认固定结构与打印公差，并验证真实排线和装配步骤。

The [current R1](../README.md) uses two transparent printed halves and three printed keys. Overall size is **85.2 × 53.2 × 5.8 mm**; panels are 0.8 mm, perimeter walls 1.2 mm. The display aperture is open and there are no internal crossbeams. Nominal CAD fit passes; printing, flex insertion, battery fit and adhesive closure still need physical validation.

The [thickness/key study](../hardware/r1-packaging-study.md) compares 5.8–5.2 mm using the switch specification's upper travel bound. The existing generator's 0.30 mm key check covers only the earlier nominal-motion assumption. Thickness/button manufacturing is deferred to a separate discussion; no thinner CAD release has been selected or generated. The [height handoff](r1-height-handoff.md) records regional stacks, cap motion and the new battery B solder/ferrite arrangement.

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

The antenna/CC2/battery-pad revision retains component placement and shell geometry. [Mechanical reuse check](../hardware/records/r1-cad-reuse-check.json) compares the two STEP exports; the original CAD build inputs remain preserved inside `r1-clear-5.8/design-inputs.json`. Current electrical dimensions are in `hardware/r1-design.json`. **The frozen CAD still contains the old long wire corridor and 0.20 mm ferrite body; it does not validate the new B-pad wiring or accepted 0.25 mm sheet.** Update the local service bodies and sheet notch in the next mechanical iteration.
