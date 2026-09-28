---
name: kicad-workflow
description: 在本仓库安装、自检和操作 KiCad，运行原生 ERC/DRC、制造导出与 KiCad 文件分析。处理 .kicad_pcb/.kicad_sch 或明确的 KiCad 任务时使用；嘉立创 EDA 项目继续用 easyeda-api，不自动迁移。
---

# KiCad 工具工作流

## 入口与范围

先读 [工具说明](../../../tools/kicad/README.md) 获取本机验证版本、命令和边界。从仓库根目录运行命令；运行时在被忽略的 `.cache/kicad-venv/`，不使用全局 pip。硬件设计判断仍用 [pcb-methodology](../pcb-methodology/SKILL.md)，工具通过不代表电气、机械或制造放行。

NFC 名片本轮仍以嘉立创 EDA 为编辑来源；KiCad 已准备不等于项目已迁移。操作前核对用户选定的工程和当前磁盘/未保存状态。

## 原生操作

1. `python3 tools/kicad/health.py` 检查 CLI、Python 绑定和参考上游。需要编辑时加 `--ipc --board /absolute/path/board.kicad_pcb`，确认 GUI 中的工程身份。
2. KiCad 10 用官方 `kicad-python`（导入名 `kipy`）编辑 PCB。IPC 必须有运行中的 PCB Editor 和启用的 API；不要假设原理图、任意交互布线器动作或 KiCad 11 接口在 10 中可用。
3. 写操作先核对完整文件路径，再以 `begin_commit` / `push_commit` 组织一个连贯修改；失败用 `drop_commit`。读取当前对象与网络，不跨实例缓存对象或臆造网络编号。API 几何长度采用 nm，可用 `Vector2.from_xy_mm` 转换。
4. 保存后重新打开，复读几何、引脚网络和规则。GUI 内存结果、API 成功返回或文件哈希变化均不能单独代替重开验证。
5. 用 `kicad-cli` 做检查和导出。先读当前版本的 `--help`；PCB/原理图成套存在时启用一致性检查，更新铺铜后再导出。DRC 的非零退出码须结合 JSON 判读，不能把所有失败都当作“有违规”。

不要在编辑器打开且有未保存改动时直接改原生文本文件。新候选另存并保留原件；`.kicad_pro`、规则、项目库与原理图一起维护，单个 PCB 文件不包含全部设计意图。

## 补充分析

`upstreams/kicad-happy` 已固定在 Git 子模块中；通过本 skill 按需调用分析器，不执行上游的全局安装指令，不默认加载全部采购、仿真或下单工作流。

- 提取 PCB 几何：`python3 upstreams/kicad-happy/skills/kicad/scripts/analyze_pcb.py BOARD --full --output REPORT.json`。
- 原理图分析：同目录 `analyze_schematic.py`；EMC 入口为 `upstreams/kicad-happy/skills/emc/scripts/analyze_emc.py`。先读相应 `--help` 和 [上游分析说明](../../../upstreams/kicad-happy/skills/kicad/SKILL.md) / [EMC 说明](../../../upstreams/kicad-happy/skills/emc/SKILL.md)。
- 单项分析或安装自检不是完整设计评审。完整评审时读上游 report-generation 说明并报告实际覆盖与缺口。分析器发现须回查原始图元/原厂资料；不能将统计和启发式推断替代原生 DRC 或实测。
- 输出写入任务的 `artifacts/`；需要长期引用的小报告搬到 `hardware/records/`。不要在子模块内生成输出或修改上游。

## 初次使用与制造

独立工具样例使用 `tools/kicad/smoke-test.py`，命令与结果见工具说明。样例会明确拒绝编辑非测试路径，不对产品板运行。

迁移先逐引脚核对网表、器件/封装与短接结构，再验证板框、禁铜区、阻焊/锡膏和坐标方向。制造文件从同一保存版本生成，BOM/CPL 与料号、位号、正反面和旋转对账；国内嘉立创以国内规则及实际订单审核为准。NFC 项目的迁移清单见 [备用调研](../../../projects/nfc-business-card/docs/kicad-fallback-research-2026-09-28.md)。
