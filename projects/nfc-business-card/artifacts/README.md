# Local generated artifacts

## 当前确定方案

当前原生设计与验证入口见 [项目 README](../README.md)。本目录除索引外都是被忽略的本机生成数据；当前没有可投厂版本。

- `kicad-v4-option-a4/`：联合布局、GPIO 映射与显式路径的失败诊断。完整原生项目另存在 `hardware/kicad/v4-option-a4-joint/`；两阶段操作计划、原生报告、独立几何、图片及构造脚本归档于 `hardware/records/kicad-v4-option-a4/`。见 [A4 评审](../hardware/v4-option-a4-review.md)。没有制造包或 A4 DFM，不能把路径模型当作已验证布线。

- `kicad-v4-option-a3/`：从 A2 做有明确对象的局部地修复和有限信号模型，未整板自动重布。TS/PG 原生否决板、局部生成脚本／模型与项目上下文归档在 `hardware/records/kicad-v4-option-a3/local-trials.zip`；接受的增量、地分量图、原生检查和指纹在同目录。[A3 报告](../hardware/v4-option-a3-review.md)包含重建命令；`replay-verified/` 已复现原生 58 DRC／7 未连接及相同铜对象／填铜。没有最终制造包／本版 DFM。

- `kicad-v4-option-a2/`：东西两种 U3 摆放、两次有限整板 DSN/SES、局部供回电和剩余网诊断。永久原生板在 `hardware/kicad/v4-option-a2*`；失败日志／会话及关键原生中间板压缩归档在 `hardware/records/kicad-v4-option-a2/bounded-trials.zip`。最终原生检查、实际填铜图及复现命令见 [A2 报告](../hardware/v4-option-a2-review.md)。没有最终制造包或本版线上 DFM 结果。

- `kicad-v4-option-a/`：方案 A 工具模型诊断、DSN/SES、整板合并及采样消融副本。长期原生板在 `hardware/kicad/v4-option-a*`，关键报告／图和试验 ZIP 在 `hardware/records/kicad-v4-option-a/`；用途、未通过门槛和复核命令见 [A 报告](../hardware/v4-option-a-review.md)。这些文件不是最终制造包。

- `kicad-v4-phase2/`：电气原厂资料的文字／整页渲染、联合路由试验、原生规范化备份和本版诊断导出；重建命令见 [phase2 工程](../hardware/kicad/v4-phase2/README.md)，长期结果见 `hardware/records/kicad-v4-phase2/`。原厂 PDF 仍放在项目 `downloads/`，来源记录在 `docs/download_manifest.json`。

- `kicad-v4/`：原始导入、四次迁移诊断、试布检查及临时导出；重建命令见 [V4 工程](../hardware/kicad/v4/README.md)，长期证据与实际上传文件保存在 `hardware/records/kicad-v4/`。

- `NFC-Card-R1-prototype.zip`: complete handoff; rebuild with `python3 projects/nfc-business-card/scripts/package-r1.py`.
- `r1-delivery/`: expanded handoff contents; rebuilt with the ZIP.
- `board-review-d/`: D 原生操作、路由试验和导出临时文件；长期结果与重建命令见 [D 诊断报告](../hardware/board-review-d.md)，不是制造包。
- `usb-power-return-c/`: USB C 原生 API 操作与诊断文件；长期证据和重建命令见 [C 局部报告](../hardware/usb-power-return-c.md)，不是制造包。
- `r1-routing/`: snapshots, route experiments and native export scratch files.
- `layout-reset-r3/`: two superseded local EDA routing experiments; the tracked R3 diagnostic source is in `eda/`.
- `archive/pre-r1/`: preserved E-series generated outputs.
- `archive/`: other preserved local checkpoints.

`hardware/production/r1/NFC-Card-R1-gerber.zip` 是历史 R1 导出，不是当前可投厂包；完整 prototype ZIP 也不能作为 Gerber 上传。

## V4 全板复盘诊断夹具

`kicad-v4-phase3/j2-witness/` 是只用于核查 J2 北侧六线容量的静态原生几何夹具，MCU 南端有意不接，不是完整候选。使用 `scripts/check-v4-j2-fanout-witness.py` 构造后运行原生 DRC（必须重铺铜），再用 `scripts/summarize-v4-j2-witness.py` 生成小报告。永久记录、全板图、33 份搜索结果索引及冻结备份在 `hardware/records/kicad-v4-phase3/layout-review/`；操作命令与限制见 `hardware/v4-layout-routability-review.md`。本轮不继续批量试路。
