# 按 USB 安装包络定厚：4.8 mm CAD 候选

## 当前确定方案

2026-09-24 用户确认按 USB 设计厚度，电池适配由用户处理。本候选保持正面＋侧壁一体、独立内嵌底盖、背面内移接缝及原外轮廓圆角，外尺寸 **85.2 × 53.2 × 4.8 mm**。主体内腔 **3.2 mm**，USB 处内侧局部加深，外表不增加凸包。

用户随后确认**停止继续减薄，以主体内腔 3.2 mm／总厚 4.8 mm 为后续设计基准**。这是选定的设计目标，不是电池与 USB 的已验证物理极限，也不是制造验收。下一重点是独立按钮的防脱、导向、手感和加工方式；保留现有电气开关，当前 0.4 mm 挡边仍是待验证结构。

这是已经建模的工程候选，尚未完成打印、装配和底盖固定验证。电池仓只说明可用空间，不给电池施加预压，也不把用户自行适配的电池标为已通过。

## 配合尺寸

| 项目 | 候选尺寸／状态 |
| --- | --- |
| 主体前后面板 | 各 0.8 mm |
| PCB 安装层 | 0.12 mm，较旧版降低 0.20 mm；材料与固定方法未定 |
| USB 占高 | 约 3.29 mm，包含当前假设的安装层 |
| USB 上方避空深度 | 约 0.19 mm |
| USB 当地内腔 | 约 3.39 mm；顶部名义间隙 0.10 mm |
| USB 当地上壁 | 约 0.61 mm，未做强度／打印验证 |
| USB 侧边缺口 | 保留原 X/Y；原缺口贯穿高度，已经覆盖下沉后的连接器 |
| 主控最大高度上方余量 | 约 0.08 mm |
| FPC 座上方余量 | 约 0.27 mm，不含真实排线折弯 |
| 三个独立键帽 | 外露 Ø4 mm、挡边 Ø6.8×0.4 mm、压柱 Ø2.6 mm |
| 按键完整行程余量 | 固定开关体上方约 0.08 mm；工艺及回弹未验证 |
| SWD 五孔 | 原 Ø1.60／2.54 mm 孔位；PCB 背面触点距外底面约 0.92 mm |
| 电池预留长方体 | **32.5 × 14 × 3.2 mm**，不含胶、导线或膨胀余量的分配 |

电池长方体以原位置 X/Y=(1.5,1.5)、Z=0.8 mm 为起点。它是验证空腔的量规，不代表推荐购买同样大的电池；用户需在该空间内安排实际电池和固定。电池厚度不再驱动外壳增厚。

## 文件与验证

- [CAD 装配候选](rear-cover-study.FCStd)
- [五个制造零件的 STEP 组合](parts.step)：上壳、底盖、三颗键帽为独立实体，不作为一件整体打印。
- 单件 STEP/STL：`RoundedUpperShell`、`InsetRearCover`、`ClearKey1`、`ClearKey2`、`ClearKey3`。
- [几何报告](report.json)：候选壳体/键帽有效，保存重开有效，STEP 单实体和 STL 封闭检查通过；静态壳体、最大屏幕包络、保守主控包络、PCB/元件直线装入和电池预留空间完成名义干涉检查。
- [正面预览](front-iso.png)、[背面预览](rear-iso.png)已视觉检查：圆角、平整前面、内移后盖接缝和五个探针孔保留；预览采用不透明配色区分几何，不预测透明树脂效果。
- 三键扫掠复用已验证的[薄键帽报告](../r1-thin-key-report.json)。本次上壳只在 USB 区减少材料，键帽及 PCB 相对位置不变。

源库 USB 的 BREP 已知无效。本次采用覆盖其全部外形的保守长方体检查避空与装入，不依赖该无效实体的布尔结果。最大尺寸仍需供应商图纸公差及实物核对。

**制造边界：**0.12 mm 安装层、0.4 mm 键帽挡边、0.61 mm 局部上壁均需选材与加工验证；0.05 mm 轴向初始间隙及 0.08 mm 按压余量不构成完整打印公差预算。键帽可单独加工，未确认兼容现货型号。底盖防脱/可拆固定、真实 FPC/焊点/导线、回弹、RF 及完整装配顺序尚未验证，因此没有替换打包版或批准下单。

## 按钮打印可行性核对

2026-09-24 查询嘉立创 3D 官方说明：透明 [8001 材料](https://jlc3dp.com/help/article/photosensitive-8001-resin)推荐壁厚 >0.8 mm，标称公差 ±0.2 mm 或 0.3%；默认打磨及喷油。[SLA 工艺页](https://jlc3dp.com/3d-printing/stereolithography)列出装配间隙 0.2 mm、运动间隙 0.5 mm 的通用建议。上述是平台通用指南，不是本零件已经获批的公差或强度保证。

本候选键帽防脱挡边 0.4 mm、静止轴向间隙约 0.05 mm、按到底的名义余量约 0.08 mm，不能据“CAD 无碰撞”宣称普通透明 SLA 能稳定生产。外露小帽、外壳导向孔和内侧捕获结构可以作为打印设计方向，但需要重新分配防脱结构及公差；不能直接把挡边加厚，否则会吃掉开关行程。可评估把较厚的限位耳移到开关侧边空区，或采用独立限位件，必须重新检查旁边元件、装入顺序与薄壳剩余壁厚，尚未选定或建模。

键帽整体高度也低于平台通用小件尺寸门槛，需核对接单方式；[连接小件指南](https://jlc3dp.com/help/article/connected-parts-printing-guide)允许用连接结构合并小件，但要求连接处厚度 >1.5 mm，不能随意把细支撑条视为符合接单规则。宜先做单键与局部导向孔的配合样件，核对成型、清理、涂层和回弹；目前没有下单。

## 可复现命令

先用[薄键帽脚本](../study-r1-thin-key.py)生成独立局部输入，然后用[本候选生成器](../build-r1-usb-fit.py)集成；两个输出目录都必须不存在。从仓库根目录运行：

```sh
NFC_THIN_KEY_OUT="$PWD/projects/nfc-business-card/artifacts/thin-key-rebuild" \
PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
projects/nfc-business-card/enclosure/study-r1-thin-key.py

NFC_THIN_KEY_SOURCE="$PWD/projects/nfc-business-card/artifacts/thin-key-rebuild/thin-key-study.FCStd" \
NFC_USB_FIT_OUT="$PWD/projects/nfc-business-card/artifacts/usb-fit-rebuild" \
PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
projects/nfc-business-card/enclosure/build-r1-usb-fit.py
```

几何结果以最终 `report.json` 为准。运行 `python3 -m py_compile` 检查脚本语法。视觉预览使用现有 `preview-r1-rear-cover.FCMacro`，独立 GUI 配置，不保存原模型。
