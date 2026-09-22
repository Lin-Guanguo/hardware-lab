# 电子名片脚本

## 当前确定方案

更新于 **2026-09-22**。当前 CAD 空间研究入口为 [e14-layout-study.py](../enclosure/e14-layout-study.py)，对应 [pcba-e14-battery-layout.FCStd](../enclosure/pcba-e14-battery-layout.FCStd)。它把 301230 标称包体和 E14 分区落到 84 × 52 mm 坐标；基于该空间研究另有 [e14-enclosure-v1.py](../enclosure/e14-enclosure-v1.py) 生成上下壳打印验证样件（[FCStd](../enclosure/nfc-card-e14-enclosure-v1.FCStd)、[STEP](../enclosure/nfc-card-e14-enclosure-v1.step)、上下壳 STL），外包络 5.0 mm，但完整装配与生产公差仍待验证。

新的 PCB 开工入口是 [E15 清理版 PCB 开工记录](../hardware/pcb-e15-clean-layout.md)。E15 图页位于 E14 `.eprj2` 工程内；其审查快照由 [generate-e15-clean-layout-svg.py](generate-e15-clean-layout-svg.py) 从保存后的 E15 数据生成。该脚本只渲染审查图，不修改 EasyEDA 工程。

右侧中部 USB 方向由 [E16 布局方案](../hardware/pcb-e16-usb-right-mid.md) 推进：[plan-e16-right-mid.py](plan-e16-right-mid.py) 用 E15 快照的真实焊盘坐标比较"原布局 / 新方案"的焊盘、模块外形、NFC 保留区和天线净空，输出 [e16-right-mid-plan.json](../hardware/e16-right-mid-plan.json)；[generate-e16-right-mid-svg.py](generate-e16-right-mid-svg.py) 直接读取 [e16-right-mid-snapshot.json](../hardware/e16-right-mid-snapshot.json) 画当前审查图（L 形板框、两键、禁布区与显示包络）。快照用 [eda-export-e16-snapshot.js](eda-export-e16-snapshot.js) 从 E16 图页重新导出，否则图会停在旧状态：

```sh
node projects/nfc-business-card/scripts/eda-exec-wait.mjs \
  projects/nfc-business-card/scripts/eda-export-e16-snapshot.js 60000 > /tmp/snap.json
python3 -c "import json,pathlib;d=json.load(open('/tmp/snap.json'))['result'];p=pathlib.Path('projects/nfc-business-card/hardware/e16-right-mid-snapshot.json');p.write_text(json.dumps(d,indent=1,ensure_ascii=False)+chr(10))"
python3 projects/nfc-business-card/scripts/generate-e16-right-mid-svg.py
```

原理图与 PCB 的一致性用逐引脚比对核实：[eda-export-pcb-pins.js](eda-export-pcb-pins.js) 导出 PCB 焊盘网络，[check-netlist-consistency.py](check-netlist-consistency.py) 与原理图导出的 netlist 做双向差集（当前 55 位号 / 230 引脚 / 0 处差异）：

```sh
node projects/nfc-business-card/scripts/eda-exec-wait.mjs \
  projects/nfc-business-card/scripts/eda-export-pcb-pins.js 60000 > /tmp/pcb-pins.json
python3 projects/nfc-business-card/scripts/check-netlist-consistency.py --sch /tmp/sch-netlist.enet --pcb /tmp/pcb-pins.json
```

外壳样件的着色等轴测图与正视顶视图由 [render-stl-iso.py](render-stl-iso.py) 直接从 STL 生成（不需要 FreeCAD GUI），输出到被忽略的 `artifacts/e16-cad-preview/`：

```sh
python3 projects/nfc-business-card/scripts/render-stl-iso.py
```

[pcb-maze-router.py](pcb-maze-router.py) 是补线阶段用的离线两层迷宫布线器。输入一份几何快照（`pcb_PrimitiveLine` / `pcb_PrimitiveVia` / `pcb_PrimitivePad` 的坐标，单位 mil）和任务表（`[网络, 起点, [目标...]]`，单位 mm），按实际设计规则做障碍扩张后用矢量桶队列 Dijkstra 求路径，输出线段与过孔清单；`--rip` 可先剔除挡路的既有线段，`--pen` 控制拥塞代价让多条线并行挤同一走廊，`--width` 调整线宽。它只写 JSON，改工程由单独的 EasyEDA 脚本完成：

```sh
python3 projects/nfc-business-card/scripts/pcb-maze-router.py --dump snapshot.json --tasks tasks.json --rip rip.json --width 0.15 --pen 40 --out routes.json
```

注意过孔必须 ≥ 7.9 mil 内径 / 11.9 mil 外径，否则既报物理错误又不会被连通性判定接受；DRC 面板是异步的，触发后等待再读，保存重开才得到真实数字。

E14 实际平面图由 [generate-e14-eda-layout-svg.py](generate-e14-eda-layout-svg.py) 从 [e14-eda-snapshot.json](../hardware/e14-eda-snapshot.json) 生成；快照同时保留 [器件/焊盘坐标](../hardware/e14-eda-components-pins.json)，用于核对 EasyEDA 保存重开后的真实板框、机械图元和元件位置。该脚本不会修改 EDA 工程。

外壳坐标协调样件由 [e14-enclosure-v2-eda-coordinate.py](../enclosure/e14-enclosure-v2-eda-coordinate.py) 生成；复核使用 [check-e14-enclosure-v2.py](check-e14-enclosure-v2.py)。V2 将 USB 开口放在 E14 实际 J1 所在的 y=0 边，只用于解决 PCB/外壳坐标关系。

按键已收敛为**两颗**（SW1 y=3.30 / SW3 y=15.10，中心距 11.80 mm，本体间隙 6.60 mm），原第三颗 SW2 已从原理图与 PCB 删除，外壳 V3 只开两个键孔；菜单仍按两键（一级/二级切换）定义。

E14 模型可直接复现：`/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/enclosure/e14-layout-study.py`；几何检查使用 `freecad-study.py check`，视觉检查使用一次 GUI 预览。统一输出到新目录或新文件，保留已有模型；不覆盖其他窗口中的手工或未保存修改。

E14 生产化门槛记录见 [pcb-e14-manufacturing-gates.json](../hardware/pcb-e14-manufacturing-gates.json)。它只记录当前快照和放行条件，不生成制造文件，也不会把未确认的电池尺寸或空间包络当成供应商规格。

门槛检查：

```sh
python3 projects/nfc-business-card/scripts/check-e14-gates.py
```

EDA 最新为 [84 × 52 E6 功能块工程](../hardware/pcb-e6-84x52-blocks.md)。新增 [check-e6-netlist.py](check-e6-netlist.py)，检查 56 元件、234 项原理图引脚与 234 项 PCB 元件焊盘网络；不验证铜线连通、DRC、功耗或 RF：

```sh
python3 projects/nfc-business-card/scripts/check-e6-netlist.py projects/nfc-business-card/hardware/e6-blocks-circuit.enet --pcb projects/nfc-business-card/hardware/pcb-e6-84x52-blocks.json --pcb-netlist projects/nfc-business-card/hardware/e6-blocks-pcb.enet
```

## 常用命令

从仓库根目录运行；环境为本机 FreeCAD 1.1.3 arm64，默认运行时位于 `/Applications/FreeCAD.app/Contents/Resources`。

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/enclosure/e14-layout-study.py
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/enclosure/e14-enclosure-v1.py
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd projects/nfc-business-card/enclosure/e14-enclosure-v2-eda-coordinate.py
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-e14-battery-layout.FCStd
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-e14-battery-layout.FCStd
printf '%s\n' 'exec(open("projects/nfc-business-card/scripts/check-e14-enclosure-v2.py").read())' | /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd --console

python3 projects/nfc-business-card/scripts/freecad-study.py generate --variant e6-84x52-detail
python3 projects/nfc-business-card/scripts/freecad-study.py check projects/nfc-business-card/enclosure/pcba-e6-84x52-detail.FCStd
# Optional: one temporary GUI process, then exit.
python3 projects/nfc-business-card/scripts/freecad-study.py preview projects/nfc-business-card/enclosure/pcba-e6-84x52-detail.FCStd
```

生成命令复现宏中的参数，不会导入已保存模型里的手工修改。[freecad-worker.py](freecad-worker.py) 是内部工作脚本，不直接用系统 Python 启动。完整环境、输出与限制见[软件说明](../docs/software.md#84--52-实际封装细化)。

## 其他检查与历史变体

### 布线空间先行研究

在修改 CAD 或 EasyEDA 之前，可先运行 [routing-space-study.py](routing-space-study.py) 比较长条电池和右下布线区。它只生成忽略的 JSON/SVG，不覆盖模型或工程：

```sh
python3 projects/nfc-business-card/scripts/routing-space-study.py \
  --output-dir projects/nfc-business-card/artifacts/routing-space-study/<new-run>
```

研究结论与限制见[布线空间先行研究](../hardware/routing-space-study.md)。

[check-schematic-netlist.py](check-schematic-netlist.py)核对原 27 元件草案的关键网络，不验证新增 J2/U4/U5、PCB 布线或可制造性：

```sh
python3 projects/nfc-business-card/scripts/check-schematic-netlist.py projects/nfc-business-card/hardware/schematic-draft.enet
```

`baseline`、`e6-302030`、`e6-bottom-usb`、`e6-84x52` 和 `e6-83x51` 保留用于复现旧比较；日常继续当前方案时选择 `e6-84x52-detail`。


### EDA 元件关联复核

`check-e6-netlist.py` 可追加 `--pcb-netlist <PCB 导出的 .enet>`，核对两侧元件集合、Unique ID、封装和引脚网络。与 `--pcb` 的焊盘网络快照检查互补；需从同一工程的正确原理图/PCB 上下文重新导出，不混用旧会话文件。本轮先检出 27 个关联 ID 差异，修正并保存重开后通过。当前功能块副本的复验输入为 `hardware/e6-blocks-circuit.enet`、`hardware/e6-blocks-pcb.enet` 和 `hardware/pcb-e6-84x52-blocks.json`；原 E6 网表与快照保留作历史比较。
