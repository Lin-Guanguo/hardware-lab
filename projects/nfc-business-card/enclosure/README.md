# R1 transparent enclosure

## 当前确定方案

最新研究：[3.0 mm 内腔／4.6 mm 总厚诊断](r1-cavity-3mm-study/README.md)。电池按用户报告的 3.0 mm 输入，现有 USB、主控、FPC 座和按键仍干涉。已记录局部深腔与平整外表的尺寸预算，仅保存诊断 CAD，未导出打印件或替换下述候选。

继续减薄：[内腔 3.6 mm／外厚 5.2 mm 候选](r1-usb-height-5.2/README.md)已生成，三键静止与完整行程检查通过；USB 顶部间隙约 0.11 mm，按键凹位的按压竖向间隙约 0.08 mm。此为紧配合研究，未替换打包版，仍需处理打印公差和可拆底盖。

减薄研究已恢复：[USB 高度约束下的 5.4 mm 候选](r1-usb-height-5.4/README.md)采用键帽底面局部凹位，三键完整运动包络无干涉，USB／3.4 mm 电池上方名义间隙约 0.31／0.30 mm。局部键帽厚 0.6 mm 与原有 0.05 mm 轴向间隙尚未经过打印和回弹验证；可拆固定仍未实现，打包版保持 5.8 mm。

打包用 [r1-clear-5.8](r1-clear-5.8/README.md)也已同步 2.54 mm 五孔：Ø1.60、外孔口 R0.05，CAD、托盘与装配导出、冻结输入和 `r1-mechanical-check.json` 已刷新。仅更新孔位，不代表打包外形已切换为圆角背盖方案。

最新 CAD 基线：[2.54 mm SWD 圆角候选](r1-rounded-rear-soft-swd254/README.md)在 5.8 mm 圆角版上同步五孔坐标，采用 Ø1.60、外孔口 R0.05，最窄表面连桥 0.84 mm。上壳及其余几何不变；通用探针模块的实物试夹待完成。用户希望方便拆卸，下一步优先研究局部支柱、插舌和小螺钉固定；减薄至 5.6 mm 仅是讨论中的目标，尚未改模型。

恢复接口协调：[隐藏 RESET 与 2.54 mm 探针候选评估](r1-recovery-study.md)已给出右侧按压轴和开关区域；保守包络与装入检查通过。SWD 夹具尺寸、底盖小孔和工具导向尚待确定，未修改 PCB 或发布新外壳制造版。

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
