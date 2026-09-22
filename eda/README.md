# EDA 工程

整个 hardware-lab 的原始 `.eprj2` 工程直接保存在此目录，不使用工程文件符号链接，也不再按项目嵌套。

## 当前确定方案

电子名片当前使用 **[NFC-Business-Card-84x52-E14-Battery-Layout.eprj2](NFC-Business-Card-84x52-E14-Battery-Layout.eprj2)**（2026-09-22）内的 **E15 Clean Layout - New Battery** 图页，作为新电池尺寸的主布局候选。E15 清除了 E14 的历史 PCB 图元，保存快照为 56 个元件、242 个焊盘、0 铜线、0 过孔；E15 尚未关联原理图 Board，也尚未冻结最终板框和 USB 开口，不能生产。E14 原布局、E13 自动布线副本、E9/E7 无铜基线、E8/E10/E11 对照均保留。

E9 是 E14 的复制基线，屏幕升压/供电开关及 USB 数据/CC ESD 等器件均保留；E14 在此基础上调整了电池、NFC、USB/充电和主控空间关系。E9 的 CC 受控试线和数据扇出缺口仍见[USB 局部排布评审](../projects/nfc-business-card/hardware/pcb-e9-usb-local.md)。

仍按含壳 84 × 52 mm、优先薄度和至少两键继续。最新 [FreeCAD](../projects/nfc-business-card/enclosure/pcba-e6-84x52-detail.FCStd)尚未同步本版实际插座/外围，不能据此认定完整装配通过。原始工程直接存放在本目录，客户端只登记 `hardware-lab/eda/`，不使用工程符号链接。

## 客户端配置

1. 保存并关闭当前打开的工程。
2. 在 **设置 → 客户端 → 数据路径 → 离线工程路径** 中移除原来的 `projects/nfc-business-card/artifacts/eda-smoke-test/` 路径，添加本目录：

   ```text
   /Users/linguanguo/dev/hardware-lab/eda
   ```

3. 应用设置并按提示重启，随后从左侧“所有工程”的新目录打开工程。

2026-09-20 用户保存并退出 EDA 后，已将测试工程原文件移入本目录；迁移前后 SHA-256 一致，SQLite `PRAGMA quick_check` 均通过。客户端设置由用户操作，新路径的显示与打开结果待用户确认。后续直接在此目录保存新工程，必要时右键目录刷新。

本机专业版 3.2.203 的工程扫描实现只枚举所登记目录的直接子项，因此不直接登记仓库根目录来搜索深层工程。客户端路径设置说明见[官方文档](https://prodocs.lceda.cn/cn/faq/client/)。

## 工程与维护

| 工程文件 | 所属项目 | 状态 |
| --- | --- | --- |
| [NFC-Business-Card-84x52-E14-Battery-Layout.eprj2](NFC-Business-Card-84x52-E14-Battery-Layout.eprj2) | `nfc-business-card` | 当前新电池尺寸主布局候选；56 元件、0 铜线/过孔，保存重开通过；网络、板框和 RF 未完成，不能生产 |
| [NFC-Business-Card-84x52-E13-Routing.eprj2](NFC-Business-Card-84x52-E13-Routing.eprj2) | `nfc-business-card` | E14 之前的自动布线对照；仅作走线实验，不是当前主布局 |
| [NFC-Business-Card-84x52-E7-Placement.eprj2](NFC-Business-Card-84x52-E7-Placement.eprj2) | `nfc-business-card` | 当前无铜布局评审；56 元件、242 焊盘，保存重开通过；先验收关键通道，不能生产 |
| [NFC-Business-Card-84x52-E8-USB-Left.eprj2](NFC-Business-Card-84x52-E8-USB-Left.eprj2) | `nfc-business-card` | E7 的 USB/CC 小组左移约 2.5 mm 的失败候选；板框缺口固定孔冲突，保留作对照，不能生产；[评审记录](../projects/nfc-business-card/hardware/pcb-e8-usb-left.md) |
| [NFC-Business-Card-84x52-E9-USB-Local-Compact.eprj2](NFC-Business-Card-84x52-E9-USB-Local-Compact.eprj2) | `nfc-business-card` | E14 的复制基线；USB/CC 局部排布评审保留，当前不再作为主布局；[评审记录](../projects/nfc-business-card/hardware/pcb-e9-usb-local.md) |
| [NFC-Business-Card-84x52-E10-Button-Right.eprj2](NFC-Business-Card-84x52-E10-Button-Right.eprj2) | `nfc-business-card` | E9 的按键右移对照；DRC 与 E9 相同但按键网络更长，不采用；[对照记录](../projects/nfc-business-card/hardware/pcb-e10-button-right.md) |
| [NFC-Business-Card-84x52-E11-Data-Fanout.eprj2](NFC-Business-Card-84x52-E11-Data-Fanout.eprj2) | `nfc-business-card` | E9 的 USB 数据扇出对照；两轮错开通孔仍有局部间距冲突，试线已清除，保存重开为干净布局；[评审记录](../projects/nfc-business-card/hardware/pcb-e11-data-fanout.md) |
| [NFC-Business-Card-84x52-E6-Blocks.eprj2](NFC-Business-Card-84x52-E6-Blocks.eprj2) | `nfc-business-card` | 当前功能块重排试布线；56 元件、242 焊盘，58 条 DRC，未达到制造条件 |
| [NFC-Business-Card-84x52-E6.eprj2](NFC-Business-Card-84x52-E6.eprj2) | `nfc-business-card` | 重排前 E6 比较版；67 条 DRC，原文件保留 |
| `AI-API-Smoke-Test.eprj2` | `nfc-business-card` 的工具链验证 | 本机临时测试，不入 Git；导出包、截图与网表留在该项目的 `artifacts/eda-smoke-test/` |
| [NFC-Business-Card.eprj2](NFC-Business-Card.eprj2) | `nfc-business-card` | 三页原理图及 `E6-302030 试布线 - 未完成`；已保存重开和核对网表，PCB DRC 剩 41 条；[试布线记录](../projects/nfc-business-card/hardware/pcb-routing.md) |
| [NFC-Business-Card-Bottom-USB.eprj2](NFC-Business-Card-Bottom-USB.eprj2) | `nfc-business-card` | 独立新方案：电池靠右、USB 下长边，三键竖排；保存重开通过，尚未布线；[排布与验证](../projects/nfc-business-card/hardware/pcb-bottom-usb.md) |
| [NFC-Business-Card-84x52.eprj2](NFC-Business-Card-84x52.eprj2) | `nfc-business-card` | 当前紧凑方案；30 元件、188 焊盘，保存重开通过；未布线，134 条 DRC；[候选与验证边界](../projects/nfc-business-card/hardware/pcb-84x52.md) |

正式工程以项目名或用途命名，并从所属项目 README 关联。本地测试工程不会随 Git 克隆恢复，当前验证结果见[软件说明](../projects/nfc-business-card/docs/software.md)。

## Git 管理

正式 `.eprj2` 应作为设计源文件纳入 Git，但它是 SQLite 二进制数据库，Git 的常规文本差异与自动合并不适用。每次提交前先保存并关闭工程；同一个工程避免并行修改，发生冲突时在 EDA 中核对并整合设计。

仓库忽略当前临时测试工程及 `-journal`、`-wal`、`-shm` 文件，不会整体忽略 `.eprj2`。忽略 SQLite 日志不能代替正常保存关闭；正式提交应包含已完整落盘的主数据库。需要评审电路变化时，可在设计节点配合导出的原理图、网表或 BOM。
