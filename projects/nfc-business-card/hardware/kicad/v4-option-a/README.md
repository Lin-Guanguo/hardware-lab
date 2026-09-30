# NFC V4 方案 A 局部验证工程

## 当前确定方案

完整功能方案 A 的摆放及五充电控制／BAT／BN 静态验证板，**不是整板或制造候选**。原生入口：[项目](NFC-Card-V4.kicad_pro)、[PCB](NFC-Card-V4.kicad_pcb)、[原理图](NFC-Card-V4.kicad_sch)。项目库使用相对路径。

136 段／22 孔（含原始 NFC 74 段／6 孔），ERC 0、parity 0、DRC 55、98 未连接。完整采样功能保留；双层 0.8 mm、固定机械／天线基准未变。五控制已同版连接，BAT 支路已实际布出；其余区域未接完，供回电不能据此宣告通过。

完整结论、顶底层图、实际路径比较、失败门槛和复现命令见 [方案 A 报告](../../v4-option-a-review.md)。[整板合并失败工程](../v4-option-a-integration-rejected/README.md)另存，不能与本板各自已连接的部分拼成验收通过。电池采样删减没有改善主要失败返回，本工程不删除采样。

本目录的 JSON 是实施计划／诊断记录，不是制造文件。`controls-plan.json` 不能重复追加到已执行同批连接的 PCB。D、phase1、phase2 和 phase3 冻结对照均保留。
