# R1 打包用 5.8 mm 外壳

## 当前确定方案

2026-09-24：本目录仍是 `scripts/package-r1.py` 的 `case/` 来源。已将原托盘上的五个 SWD 孔同步为 **2.54 mm 间距、Ø1.60 mm、外孔口 R0.05 mm**；直孔之间保留 0.94 mm，表面孔口之间保留 0.84 mm。完整外观仍是原托盘＋顶盖，用户偏好的[圆角上壳＋背盖候选](../r1-rounded-rear-soft-swd254/README.md)另存，尚未取代打包结构。

五孔采用 PCB 正面坐标 X=65.92062 / 68.46062 / 71.00062 / 73.54062 / 76.08062，Y=48.49876 mm。依次为 GND、VDD_3V3 / VTref、SWCLK、SWDIO、NRESET。PCB TP1 是约 1.20 mm 方形焊盘，其余圆形；外壳五孔均为圆孔，供探针接触焊盘中心，不以孔口显露方形四角作为防反标志。

本轮只改五孔。底盖厚度 0.8 mm、整机厚度 5.8 mm、PCB 支撑、板框、其余接口及 RESET 状态不变。夹具使用用户接受的通用单排 5P 假设，待实物试夹；未验证实际探针直径、伸出量、涂层缩孔和夹持定位。现有电池走线、铁氧体和按键最大行程仍有历史模型限制。

## 更新与检查

- 更新：`e20-clear-assembly.FCStd`、装配 STEP、托盘 STEP/STL、`design-inputs.json` 的 SWD 字段、`e20-clear-report.json` 中托盘相关关系，以及两张预览图。
- 保持：顶盖 STEP/STL、键帽 STL 及所有非托盘对象。
- [局部修改记录](swd-access-report.json)：77 个非托盘对象 BREP 相同；孔区之外体积差为零；FCStd 保存重开通过；托盘 STEP 是有效单实体，装配 STEP 含 254 个有效实体；三份 STL 封闭。装配 STEP 保留零件名称。
- [机械检查](../../hardware/records/r1-mechanical-check.json)：以当前 PCB 快照核对孔轴，记录登记误差、通路、CAD 与 PCB 快照哈希。已刷新。
- GUI 装配／打开视图已重新渲染并目视检查；这不代替实物配合、树脂强度和夹具验证。

修改前确认没有运行中的 FreeCAD，先将原目录备份至 `artifacts/swd-access-packed-backup/12f939067403/`，在 `artifacts/swd-access-packed-v1/` 生成检查，再比对旧文件未被并发修改后替换上述指定文件。本轮结果随当前 PCB／CAD 工作一并保存到仓库检查点。

## 复现

局部修改脚本支持冻结来源和新输出目录，运行时不能覆盖已有输出：

```sh
NFC_SWD_ACCESS_VARIANT=packed \
NFC_SWD_ACCESS_SOURCE="$PWD/projects/nfc-business-card/artifacts/swd-access-packed-backup/12f939067403/e20-clear-assembly.FCStd" \
NFC_SWD_ACCESS_OUT="$PWD/projects/nfc-business-card/artifacts/swd-packed-rebuild" \
PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  projects/nfc-business-card/enclosure/update-r1-swd-access.py

PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  projects/nfc-business-card/scripts/check-r1-case.py
```

完整生成器 `e20-clear-shell.py` 也已支持冻结输入中的 `access_hole_mouth_radius_mm`。局部脚本默认 packed 来源是当前目录，归档重现可显式选择上述旧来源。检查完成 JSON，不能仅看 FreeCAD 退出码。
