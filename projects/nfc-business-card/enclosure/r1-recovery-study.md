# RESET 与 SWD 接口机械候选评估

## 当前确定方案

**SWD update:** the user accepted nominal generic 5P clip assumptions. The PCB now uses 2.54 mm pitch; see the [implemented five-hole revision](r1-rounded-rear-soft-swd254/README.md) and [current interface contract](../hardware/r1-usb-swd-recovery.md). The SWD dimensions below document the earlier candidate comparison; obtaining exact fixture drawings is no longer a prerequisite. RESET remains a candidate.

2026-09-24：响应 [PCB 恢复接口交接](../hardware/r1-usb-swd-recovery.md#mechanical-handoff--proposals-not-installed-parts)。**隐藏 RESET 的指定区域存在可用机械空间；2.54 mm 五针夹具接口仍待具体夹具图纸。** 本记录是候选评估，不是安装批准或制造版。未修改 PCB、原活动 CAD、圆角候选或打印导出。

## RESET：建议坐标与边界

依据 Alps Alpine [SKSCLBE010 产品页](https://tech.alpsalpine.com/e/products/detail/SKSCLBE010/)、[外形图](https://tech.alpsalpine.com/cms.media/product_detail_fig_sksc_d_31_en_b3efc7326a.gif)及[推荐焊盘图](https://tech.alpsalpine.com/cms.media/product_detail_fig_sksc_d_32_en_8654cb7b67.gif)，该型号带定位柱，3.5 × 3.55 mm 是本体含操作端的平面尺寸，不能代替完整端子包络：端子总宽 4.85 ±0.1 mm，推荐焊盘总宽 5 mm。

高度为安装基准以上 1.25 +0.15/−0.05 mm，按压位置标注为基准以上约 0.7 mm；柱突出安装基准 0.5 ±0.1 mm、直径 0.6 ±0.1 mm、两柱中心距 1.8 ±0.1 mm。推荐两个直径 0.8 +0.05/0 mm 的 PCB 孔。目录称半沉入式，但本次图纸所示向下侵入 PCB 的关键结构是定位柱；不把完整 1.25 mm 本体高度误算进板下 0.32 mm 空间。正式封装仍须 PCB 任务按原厂安装面视图复核，尤其避免镜像。

以下均采用 PCB 正面坐标；外壳底面 Z=0，PCB 顶面 Z≈1.920025 mm：

| 项目 | 候选 |
| --- | --- |
| 平面基准 C | **(80.30, 8.60) mm**；对应外形图距操作端 2.1 mm 的横向中心基准，不等同于 EDA 库默认原点 |
| 朝向 | 操作端朝 +X／右侧，实际按压沿 −X |
| 未按压操作端 | **X=82.40、Y=8.60 mm** |
| 按压轴 | **Y=8.60、Z≈2.620 mm**，实际高度需叠加焊接和装配偏差 |
| 两定位柱／孔候选中心 | **(79.40,8.60)、(81.20,8.60) mm** |
| 推荐焊盘总宽所在区域 | Y=6.10…11.10 mm，位于分配区内；准确焊盘需从原厂图建立 |
| 开关标称顶面 | Z≈3.170 mm |
| 本次保守外包络 | X=78.70…82.55、Y=6.075…11.125、Z=1.920…3.420 mm；包含尺寸公差及假设的 0.10 mm 安装高度余量 |
| 右侧工具孔候选 | 中心 **Y=8.60、Z≈2.620 mm**、沿 X 贯穿侧壁；先以直径 **2.0 mm** 检查，未确定最终孔径 |

FreeCAD 包络核对结果：

- 包络与既有实体无体积干涉，距圆角上壳最小 **0.85 mm**；底部直线装入的保守扫掠与上壳不相交。
- 包络的 PCB 支撑投影完整落在板内。按最长柱 0.6 mm 计算，柱底 Z≈1.320 mm，距板底约 **0.20 mm**，不会突出到板下支撑空间。实际仍需在 PCB 增加两定位孔并检查所有层铜箔避让。
- 工具孔位于右侧直壁区域，避开上下大圆角和 USB 缺口。模拟打孔后上壳仍为有效单实体。
- 假设直径 0.6 mm 的平头工具沿轴线插入，从外侧壁 X=84.6 到未按压操作端约 **2.2 mm**，再按入标称 0.2 mm 行程，到约 **2.4 mm**。该直线工具扫掠与 PCB、现有元件及开孔后的上壳无干涉。

**仍不能直接定版的事项：**0.6 mm 工具和 2 mm 孔是评估假设；大孔不能保证工具自动居中。需要确定工具导向、允许偏心、按压限位及实物回弹，避免工具压到开关外壳或越过行程。原厂按压力 2.2 N 是操作规格，不代表可以任意加力。此处尚未做焊点承力、薄板挠曲、打印公差或用户按压测试。正式采购规格的公差优先于公开目录。

## SWD：2.54 mm 候选的装壳可达性

交接候选五点为 X=65.9206、68.4606、71.0006、73.5406、76.0806，Y=48.4988 mm。**这些坐标未落板、未改底盖。** 当前正式参数仍为单排 3 mm；现有夹具标题不足以确认适配。

- 底盖外面到焊盘平面的名义深度是 **1.12 mm**，由 0.8 mm 底盖和 0.32 mm 板下间距组成。探针自由伸出长度必须再覆盖实际工作压缩量、夹具端面间隙和各项公差，不能只选“针长大于 1.12 mm”。
- 从相邻外壳 Y=52.6 边缘到针轴约 **4.1012 mm**；裸板同侧板边到针轴约 **2.3886 mm**。通用烧录夹的止挡到针轴距离是关键参数。
- 同一夹具需要分别适配 **0.8 mm 裸板**与 **5.8 mm 外壳**，还要考虑保护垫厚度、开合余量和夹持点。夹口不可把夹力直接压到屏幕或功能按键。
- 直径约 1.2 mm 的焊盘，若使用直径 0.6 mm 平头触点，要求触点圆面完整落在焊盘内时，理想中心误差上限仅 **0.3 mm**；实际还要扣掉 PCB／外壳／夹具误差。外壳大孔本身不能充当精确定位。

候选孔径比较（均未批准，现有孔口 R0.08）：

| 通孔直径 | 孔身之间宽度 | 外表面孔口之间宽度 |
| --- | ---: | ---: |
| 2.0 mm | 0.54 mm | **0.38 mm** |
| 1.8 mm | 0.74 mm | 0.58 mm |
| 1.6 mm | 0.94 mm | 0.78 mm |

小孔虽然能留下更多材料，但会减少探针通过及后处理余量；不能在缺少实际针头、针杆尺寸和偏心数据时先缩孔。下一步获取单排五针夹具尺寸图，固定针型、有效伸出、压缩量、止挡位置及夹持方式，再共同确定焊盘和底盖。五点一字排列没有防反插特性，需要针 1 标记或不对称定位。

## 证据与复现

检查脚本：[review-r1-recovery.py](review-r1-recovery.py)。本次测量：[r1-recovery-study.json](r1-recovery-study.json)。脚本从冻结圆角模型读取，生成独立、明确标为包络的候选 FCStd；没有生成 STEP/STL 制造导出。已用非对称盒体标定体积布尔运算，检查干涉、工具可达性、装入路径和源文件 SHA-256 不变。

```sh
NFC_RECOVERY_REVIEW_OUT="$PWD/projects/nfc-business-card/artifacts/recovery-mechanical/rebuild-new" \
PYTHONHOME=/Applications/FreeCAD.app/Contents/Resources \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  projects/nfc-business-card/enclosure/review-r1-recovery.py
```

输出目录必须尚不存在，成功后应存在完整 `report.json`。本次运行输出目录为 `artifacts/recovery-mechanical/candidate-v1/`。几何检查与原厂尺寸图目视阅读已完成；候选 CAD 尚未做 GUI 渲染目视验收，无夹具或实板测试。未运行电气 DRC，因为没有修改 PCB；铜箔、定位孔及天线影响由 PCB 任务继续核对。冻结实体未包含最新电池导线和真实排线，但不据此声明整机装配已通过。
