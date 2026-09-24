# 3.0 mm 内腔研究

## 当前确定方案

2026-09-24：按用户反馈“电池最厚处可以卡入 3 mm”，将 **3.0 mm 电池厚度**作为本次研究输入。它是用户观察，不是全寿命最大尺寸；不依靠挤压电池闭合外壳。目标为主体内腔 3.0 mm，前后各 0.8 mm 时总厚 **4.6 mm**，保留圆角及背面内移接缝方向。

**当前器件、安装层和键帽不能直接装进均匀的 3.0 mm 内腔。** 已生成诊断 CAD，静态和按键运动均发现干涉，因此未导出打印 STEP/STL。下一步需要选择局部加厚，或联动修改支承、壁厚和按键结构；本研究没有修改 PCB 或替换 5.8 mm 打包版。

## 高度预算

基准是底盖内表面；沿用 0.32 mm PET/胶安装层、0.80 mm PCB。下列值尚未叠加打印误差、器件公差和装配余量。模型名义值与最大值分别标明。

| 区域 | 当前需要的高度 | 对 3.0 mm 内腔的缺口 | 依据 |
| --- | --- | --- | --- |
| 电池 | 3.00 + 0.10 胶 = 3.10 mm | 0.10 mm | 用户报告的厚度；胶层沿用假设 |
| USB-C | 3.490 mm | 0.490 mm | 当前安装层及库模型 |
| 主控 | 0.32 + 0.80 + 2.20 = 3.32 mm | 0.32 mm | 沿用器件最大高度 |
| 屏幕 FPC 座 | 3.130 mm | 0.130 mm | 当前安装层及库模型；不含排线折弯 |
| 当前凹底键帽 | 约 3.52 mm 才达到按压零竖向间隙 | 0.52 mm | 0.45 mm 规格行程上界加约 0.05 mm 接触间隙 |

USB4500 官方标注 **3.16 mm profile、0.80 mm offset、Mid Mount**，与当前库模型约 3.17 mm 接近。中沉安装已经利用了 PCB 厚度；不能再把 0.8 mm 从连接器整体高度里扣一次。即使完全取消 0.32 mm 安装层，现有连接器仍超过 3.0 mm。[GCT 产品页](https://gct.co/connector/usb4500)

屏幕区域另有问题：按最大屏厚 1.0 mm 计算，屏幕后方与 0.25 mm 铁氧体的间隔仍有约 **0.47 mm**，但与假设高出 PCB 1.0 mm 的焊点/线头重叠约 **0.18 mm**。这是尺寸链计算，未建立真实焊点和走线实体，不能当作实际碰撞测量。

## 两条结构路线

### 主体 3.0 mm，局部加高

保留当前 PCB 安装位置和 0.8 mm 面板，在高器件处增加内腔；外部可考虑连续圆滑过渡。以下统一增加 **0.15 mm 试算余量**，它不是供应商认可的打印公差，也不代表所有按键配合方向已有足够间隙。

| 局部区域 | 内腔估算 | 对应外厚估算 |
| --- | --- | --- |
| USB-C | 3.64 mm | 5.24 mm |
| 主控 | 3.47 mm | 5.07 mm |
| FPC 座 | 3.28 mm | 4.88 mm |
| 当前键帽运动区 | 3.67 mm | 5.27 mm |

电池区按 3.0 电池 + 0.1 胶 + 0.1 试算间隙，需要 3.2 mm。可以研究底盖内侧局部沉槽 0.2 mm，但会使该处底盖从 0.8 减至 0.6 mm，局部内腔也实际变成 3.2 mm，强度与电池长期尺寸仍需验证。

这条路线只是主体薄，最大厚度仍约 **5.3 mm**。表中是包络预算，尚未生成无干涉的局部凸起实体，也未检查过渡曲面、局部薄壁及装入路径。不能宣称它比 5.2 mm 平整候选的最大厚度更小。

### 外表平整，目标总厚 4.6 mm

保持目前底盖及 PCB 高度，只挖上壳内侧，USB 上方壁厚仅剩 **4.6 − 4.290 = 0.310 mm**；再留 0.15 mm 顶部间隙，只剩 **0.160 mm**。这不能作为现有透明树脂方案已可制造的依据。

更有意义的研究方向是同时下沉 PCB、在底盖内侧做局部凹位，并重新设计键帽或更换低矮开关。不过 0.32 mm 安装层是实体 PET 和胶，不能直接当作空隙删除；下沉还会改变 USB 开口、SWD 探针深度和底部绝缘。若进一步更换 USB、主控封装或板厚，则需要 PCB 任务重新核对电气、板框及装配基准。目前没有确认满足严格 3.0 mm 整体内腔的替代 USB 型号。

因此本次结论是：**严格均匀 3.0 mm 内腔不兼容当前配置；主体 3.0 mm 加局部深腔有明确尺寸预算；平整 4.6 mm 外壳仍需结构与器件联动，尚未证明可制造。**

## 检查与文件

- [原始计算报告](report.json)：静态上壳与 USB、主控、FPC 座、电池相交；三个键帽与固定开关体在运动中相交，第二键还触及 R8。报告中的 `retained_rear_brep_equal: false` 是序列化字串比较未通过，未据此声称底盖几何已验证不变。
- [按键尺寸剖面](key-section.png)：已视觉检查，展示 3.8、3.6、3.0 mm 内腔。蓝色实心为完整检查行程位置，虚线为静止位置；省略圆角、端子和移动触点，仅用于解释尺寸关系。
- 诊断模型位于 `../../artifacts/usb-height-3mm-cavity-v1/rear-cover-study.FCStd`，原始源文件哈希未变，诊断模型保存重开后各零件有效。实体有效不代表装配无干涉。
- [建模脚本](../study-r1-usb-height.py)与[剖面脚本](../render-r1-key-section.py)可复现；按键移动/固定区域仍沿用半径 1.4 mm 分界假设，未经实物验证。
- 行程依据：[ALPS SKQGAB 规格](https://tech.alpsalpine.com/cms.media/SKQGAB_KQG_719_EN_cc4e10226e.pdf#page=3)。0.45 mm 是规格上界检查输入，不是建议强压到该行程。

从仓库根目录运行，输出目录必须不存在：

```sh
NFC_USB_HEIGHT_MM=4.6 NFC_USB_BATTERY_MM=3.0 \
NFC_USB_HEIGHT_OUT="$PWD/projects/nfc-business-card/artifacts/usb-height-3mm-cavity-v2" \
PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
projects/nfc-business-card/enclosure/study-r1-usb-height.py

NFC_USB_HEIGHT_OUT="$PWD/projects/nfc-business-card/artifacts/usb-height-3mm-cavity-v2" \
python3 projects/nfc-business-card/enclosure/render-r1-key-section.py
```

本次 v1 已完成上述 FreeCAD 检查与独立剖面绘制，报告状态为 `INTERFERENCES_FOUND_DIAGNOSTIC_ONLY_NO_PRINT_EXPORTS`。没有进行打印、强度、回弹或实物装配验证。
