# NFC Card V4 phase2 — KiCad

## 当前确定方案

本目录是 2026-09-29 的第二阶段独立候选。打开 [NFC-Card-V4.kicad_pro](NFC-Card-V4.kicad_pro)，PCB、根页及四张子页、符号／封装库、项目配置与规则齐备，库路径使用 `${KIPRJMOD}`。第一阶段 [../v4/](../v4/README.md)冻结保留，不能覆盖。完整结论见 [第二阶段报告](../../kicad-v4-phase2.md)。

当前 315 段／59 孔，ERC 0、DRC 41、未连接 49、原理图一致性问题 0。屏幕六信号、USB 数据及关键供电、显示完整电源网络同版共存；SCK／USB 返回和 SWD 入口未通过，**不得据此展开整板详细布线或投厂**。所有器件料号、电池采样、机械／天线基准保留。

PCB 与五张原理图均完成原生保存、关闭、重开和再保存核对，见 [PCB 记录](../../records/kicad-v4-phase2/reopen.json)及 [原理图记录](../../records/kicad-v4-phase2/schematic-reopen.json)。

[设计输入](../../v4-design-inputs.md)、[原生与独立检查](../../records/kicad-v4-phase2/final-validation.json)、[本版国内 PCB/SMT DFM](../../records/kicad-v4-phase2/dfm-final/README.md)为接手依据。本目录 `*-spec.json`／`*-plan.json` 是连贯阶段和拒绝试验记录，部分含 `failures` 或已被后续方案替代，**不能依文件名字母顺序逐个应用**。`swd-service-spec-plan.json` 是未应用的失败方案。

## 可复现检查

从仓库根目录运行；命令只适用于当前工程，不更改第三版或第一阶段。使用已安装 KiCad 10.0.6、kicad-python 0.8.0，不重新安装／升级。

```bash
python3 tools/kicad/health.py
python3 projects/nfc-business-card/scripts/verify-v4-phase2.py
kicad-cli sch erc --format json --exit-code-violations \
  -o projects/nfc-business-card/artifacts/kicad-v4-phase2/recheck-erc.json \
  projects/nfc-business-card/hardware/kicad/v4-phase2/NFC-Card-V4.kicad_sch
kicad-cli pcb drc --format json --schematic-parity --refill-zones --exit-code-violations \
  -o projects/nfc-business-card/artifacts/kicad-v4-phase2/recheck-drc.json \
  projects/nfc-business-card/hardware/kicad/v4-phase2/NFC-Card-V4.kicad_pcb
python3 projects/nfc-business-card/scripts/audit-v4-phase2.py \
  projects/nfc-business-card/hardware/kicad/v4-phase2/NFC-Card-V4.kicad_pcb \
  projects/nfc-business-card/artifacts/kicad-v4-phase2/recheck-geometry
kicad-cli sch export pdf \
  -o projects/nfc-business-card/artifacts/kicad-v4-phase2/recheck-schematic.pdf \
  projects/nfc-business-card/hardware/kicad/v4-phase2/NFC-Card-V4.kicad_sch
```

DRC 带 `--exit-code-violations` 时预期非零，必须读取 JSON 分类，不能声称通过。`--refill-zones` 在本命令中只更新检查内存，未加 `--save-board`，不会覆盖已开 PCB 的磁盘文件。`verify-v4-phase2.py` 通过的是身份、逐引脚网络、冻结输入和约束，输出仍明确 `design_release: NOT PASSED`。

`audit-v4-phase2.py` 使用保存的实际填铜，输出四张顶底层图、命名路径、地连接、局部回流宽度敏感性和对面地缺口。铜中心线统计不含器件内部路径；铺铜不加入线长，不把 `null` 地线路径当断网。不是电磁或热仿真。

## 同版制造诊断导出

输出目录必须不存在；重复运行时选新的目录，不能覆盖已有上传包。

```bash
python3 projects/nfc-business-card/scripts/export-kicad-dfm.py \
  projects/nfc-business-card/hardware/kicad/v4-phase2/NFC-Card-V4.kicad_pcb \
  projects/nfc-business-card/artifacts/kicad-v4-phase2/dfm-recheck \
  --archive-name NFC-V4-phase2-diagnostic-gerber.zip
```

脚本核对 66 位号／料号、BOM/CPL 集合，并绑定同一 PCB SHA；其当前冻结料号检查会拒绝未经同步处理的换料。导出不运行在线检查；按 [本次实际上传流程](../../records/kicad-v4-phase2/dfm-final/README.md)重新上传后才有新版 DFM 结果。

## 后续原生编辑的限制

先检查磁盘文件和 GUI 未保存状态，按 [工具工作流](../../../../../tools/kicad/README.md)自检 IPC 实例并核对绝对路径。`apply-v4-ipc.py` 拒绝有失败项的路由计划，使用原生事务、重铺铜和保存；不要把失败计划中部分成功的线提取出来逐条强行应用。

本版已遇到 kicad-python 0.8.0 对导入封装内圆弧／图形旋转的持久化差异。移动后检查封装库几何；必要时**关闭 PCB Editor 后**用 `finalize-v4-native.py` 从未变的项目库／D 锡膏来源恢复局部几何，再原生打开重铺铜检查。不能在编辑器中有未保存变更时直接改原生文本。[最后恢复记录](../../records/kicad-v4-phase2/native-restoration-final.json)保留了本次实际输入路径与数量。

下一次重点是共同重分配 MCU 西北入口的 SCK、USB、SWD、去耦与地，见报告的两个具体方向；当前原生文件是可比较的局部候选，不是后续必须锁死的走线约束。
