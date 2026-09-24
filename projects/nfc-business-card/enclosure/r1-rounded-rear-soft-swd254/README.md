# R1 圆角外壳：2.54 mm SWD 访问孔

## 当前确定方案

2026-09-24：在[更圆润的 5.8 mm 候选](../r1-rounded-rear-soft/README.md)上，仅调整底盖五个 SWD 访问孔。这是后续 CAD 的最新基线；旧候选保留。用户选择绿深旗舰店「单排 5P 探针模块（2.54 mm 间距）」，接受先按通用间距设计、实物试夹，未将夹具截图的“1.5 mm 针孔”当成针尖直径。

外形仍为 85.2 × 53.2 × 5.8 mm，圆角、上壳、键帽和其他接口保持原几何。尚未加入可拆底盖固定结构，也未合并 RESET 候选。当前模型不是整机制造批准文件。

## 访问孔尺寸

坐标沿用 PCB 正面 XY；从背面看左右会翻转。

| 信号 | X / mm | Y / mm |
| --- | ---: | ---: |
| GND | 65.92062 | 48.49876 |
| VDD_3V3 / VTref | 68.46062 | 48.49876 |
| SWCLK | 71.00062 | 48.49876 |
| SWDIO | 73.54062 | 48.49876 |
| NRESET | 76.08062 | 48.49876 |

- 中心距 **2.54 mm**，底盖厚度 **0.8 mm**。
- 直孔 **Ø1.60 mm**；外侧孔口 **R0.05 mm**，表面入口约 **Ø1.70 mm**。
- 相邻直孔间材料宽 **0.94 mm**；外侧孔口最窄名义连桥 **0.84 mm**。相比直接沿用 Ø2.0＋R0.08 的 0.38 mm，保留更多材料。
- 外侧底面至 PCB 焊盘面的名义深度 **1.12 mm**；探针需要另有工作压缩量。

Ø1.60 与 R0.05 是本轮选定的名义设计值，不是供应商对 0.8 mm 透明树脂的精度或强度承诺。孔径大于约 Ø1.20 mm 焊盘，但不代表任意 2.54 mm 夹具都能穿壳接触；后处理缩孔、针尖尺寸、夹持和定位在实物试夹时验证。R0.05 为名义去锐边，不要求打印后保持可计量的精确微小圆弧。

## 文件与验证

- [完整候选 FCStd](rear-cover-study.FCStd)：继承原装配参考体，仅底盖访问孔改变。PCB 参考体不含调试焊盘铜，孔坐标按 PCB 任务交接输入。
- [底盖 STEP](rear.step)、[底盖 STL](rear.stl)：本轮重新导出。
- [两件壳体 STEP](rear-cover-study.step)：包含原上壳和新底盖，供装配评审。
- [上壳 STL](upper.stl)：从原候选原样复制；键帽未重新导出。
- [检查报告](report.json)：保存重开、STEP 实体、STL 封闭、局部改动范围、孔轴和示例探针通路检查。
- [背面预览](rear-iso.png)：颜色用于观察外形，不代表透明材料效果。

本轮检查通过：FCStd 保存后重开为有效单实体底盖；底盖 STEP 为 1 个有效实体，两壳 STEP 为 2 个有效实体；两份 STL 均封闭。五孔轴匹配交接坐标，孔区之外的体积差为零，其余对象 BREP 序列化完全相同。已目视检查正背面 GUI 渲染。脚本经 `python3 -m py_compile`，索引改动经 `git diff --check`。

检查不代表实物夹具适配认证。底盖固定、大面翘曲、涂层配合和按键间隙仍遵循原候选的[工艺限制](../r1-rounded-rear-soft/manufacturing-review.md)；旧电池导线/铁氧体参考体也未在本轮刷新。

## 重建

输出目录必须不存在：

```sh
NFC_SWD_ACCESS_OUT="$PWD/projects/nfc-business-card/artifacts/swd-access-rebuild" \
PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  projects/nfc-business-card/enclosure/update-r1-swd-access.py
```

检查最终 `report.json`，不能只看退出码。预览复用 `preview-r1-rear-cover.FCMacro`，以 `NFC_REAR_STUDY_OUT` 指向输出目录，`NFC_REAR_DISPLAY_MODE=Shaded`；GUI 用独立配置且不保存几何。
