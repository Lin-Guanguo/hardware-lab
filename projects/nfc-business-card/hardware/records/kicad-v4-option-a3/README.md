# A3 局部修复证据

## 当前确定方案

本目录对应 [A3 报告](../../v4-option-a3-review.md)与 [原生工程](../../kicad/v4-option-a3-local/README.md)。全部地焊盘连通，整板仍有 7 项信号未连接；不是制造放行记录。

- `baseline-ground/`、`final-ground/`：保存的原生填铜＋明线构成的地分量、所有承载焊盘、边界相邻对象及全板／局部图。相邻不是单一根因证明。
- `*-drc.json`、`*-ipc.json`：各局部阶段的原生检查与实际操作。`ts-pg-*` 是原生填铜失败后撤回的方案，不属于最终候选。
- `display-returns/`、`final-audit/`：最终同版局部返回、命名路径、独立铜间距与投影参考地诊断。投影缺口和腐蚀探针不能独立宣告回流通过。
- `local-access.json`：连续几何区分当前固定铜的物理阻挡与网格／通道限制；不是全板面积不足证明。
- `new-ground-via-contact.json`：十颗新增地孔的两面实际填铜接触。
- `final-erc.json`、`final-drc.json`、`identity-check.json`、`reopen-check.json`、`preserved-comparisons.json`：重开后 ERC 0、parity 0、DRC 58、7 未连接，以及旧对照／原生信息保留。
- `local-trials.zip`／`local-trials-manifest.json`：未应用的局部模型、生成脚本、TS/PG 否决 PCB、计划与一致的项目配置／库。模型不是完整候选；原生失败板复查需使用随包项目上下文。
- `accepted-native-delta.json`／`replay-check.json`：仅本轮保留的原生对象增量；由 A2 在新目录重建并重铺铜的结果已复现，铜对象及填铜完全一致。

最终图为 `top-bottom.png`、`critical-top-bottom.png`。本目录没有 A3 最终制造包／国内 PCB 或 SMT DFM 报告，旧版本 DFM 不覆盖本版。
