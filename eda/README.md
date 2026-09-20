# EDA 工程

整个 hardware-lab 的原始 `.eprj2` 工程直接保存在此目录，不使用工程文件符号链接，也不再按项目嵌套。

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
| `AI-API-Smoke-Test.eprj2` | `nfc-business-card` 的工具链验证 | 本机临时测试，不入 Git；导出包、截图与网表留在该项目的 `artifacts/eda-smoke-test/` |

正式工程以项目名或用途命名，并从所属项目 README 关联。本地测试工程不会随 Git 克隆恢复，当前验证结果见[软件说明](../projects/nfc-business-card/docs/software.md)。

## Git 管理

正式 `.eprj2` 应作为设计源文件纳入 Git，但它是 SQLite 二进制数据库，Git 的常规文本差异与自动合并不适用。每次提交前先保存并关闭工程；同一个工程避免并行修改，发生冲突时在 EDA 中核对并整合设计。

仓库忽略当前临时测试工程及 `-journal`、`-wal`、`-shm` 文件，不会整体忽略 `.eprj2`。忽略 SQLite 日志不能代替正常保存关闭；正式提交应包含已完整落盘的主数据库。需要评审电路变化时，可在设计节点配合导出的原理图、网表或 BOM。
