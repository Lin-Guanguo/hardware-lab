---
description: artifacts 目录索引：哪些是本机产物、哪些已归档、哪些证据已经进 git
last_updated: 2026-09-23
---

# artifacts 目录索引

本目录放**本机产物**：脚本输出、导出包、渲染图和历史阶段的工作目录。按仓库约定（`.gitignore` 里的 `**/artifacts/**`）这里的东西**默认不进 Git**，唯一例外是本文件——它负责说明这里有什么。

需要长期保留、文档会链接的证据**不放这里**，而是放在受版本管理的目录里：

| 证据类型 | 位置 |
| --- | --- |
| EDA 阶段的重开/DRC/网表记录、检查脚本、`.enet` | [hardware/records/](../hardware/records/) |
| 外壳模型、几何报告、STEP/STL | [enclosure/](../enclosure/) |
| 外壳渲染图册（V2–V7 等轴测/顶视） | [enclosure/renders/](../enclosure/renders/) |
| 打印件网格体检报告 | [enclosure/nfc-card-e16-print-meshes-report.json](../enclosure/nfc-card-e16-print-meshes-report.json) |

## 当前目录（E16 设计相关）

| 目录 | 内容 | 怎么重建 |
| --- | --- | --- |
| `manufacture/` | 当前制造包：Gerber zip、BOM、贴装坐标、装配 PDF、`manifest.json`（含 sha256）。**验证用，不是下单文件** | `scripts/eda-export-e16-manufacture.js` 导出 → 从 `~/Downloads/.cn.lceda.pro.*` 拷进来 → `python3 scripts/check-e16-manufacture.py` |
| `review/` | `pcba-e16-right-mid.png`：审查图的 PNG 预览（便于聊天/看图工具显示） | 权威图是受管理的 [enclosure/pcba-e16-right-mid.svg](../enclosure/pcba-e16-right-mid.svg)，PNG 由它渲染 |
| `studies/routing-space/{initial,v2}/` | 长条电池 vs 右下布线区的研究输出（JSON + SVG） | `python3 scripts/routing-space-study.py --output-dir projects/nfc-business-card/artifacts/studies/routing-space/<new-run>` |
| `archive/` | 2026-09-20/21 各阶段（E6–E13、compact/USB/datasheet 研究、EDA 冒烟测试与早期 FreeCAD 运行）的整块产物 | 只读留档，仅供追溯；命名保持当年原样 |

## 规则（给以后的人/AI）

1. **新产物进这里，整块过期就进 `archive/`**，命名用"用途"而不是"第几版"：当前设计是 E16，但目录不叫 `e16-*`——版本信息放在文件名里（`NFC-E16-gerber.zip`、`e16-enclosure-v7-iso.png`），这样下一版不用改名。
2. **只移动、不删除**历史产物；确认没用再删，删之前先在提交信息里写清楚。
3. **能重建的东西不进来**：`__pycache__`、`*.pyc`、临时导出（`~/Downloads/.cn.lceda.pro.*`）、运行日志（仓库根 `logs/`）都按 `.gitignore` 忽略或随手清掉，需要时脚本会重建。
4. **要长期引用就先搬进受管理的目录**（见上表），再在文档里链接——文档不要长期指向 `artifacts/` 里的文件，因为它不进 Git。
5. `archive/` 里的大块产物（几百 MB 的 EDA 画布 JSON、`.eprj2` 副本、PNG 集）如果确认历史价值不大，可以整体删除；删除前先看[E16 记录](../hardware/pcb-e16-usb-right-mid.md)与各阶段文档有没有引用。

## 已归档的阶段目录

`archive/` 下目前有：`bottom-usb`、`compact-detail`、`compact-layout`、`datasheet-review`、`datasheet-text`、`e6-circuit`、`eda-block-layout`、`eda-clean`、`eda-draft`、`eda-persistence-review`、`eda-prelayout`、`eda-routing`、`eda-routing-close`、`eda-routing-refine`、`eda-smoke-test`、`freecad`、`freecad-e6-302030`、`freecad-workflow-validation`、`gdeh0154e01-research`、`routing-space-study`（旧名）、`screen-interface`、`usb-block`、`usb-clearance-review`，以及三个散落文件（`layout-study-freecad.png`、`pcba-layout-preview.png`、`run-pcba-layout.py`）。

其中被文档引用的**单个小文件**已经搬进 `hardware/records/`、`enclosure/`、`enclosure/renders/`，所以这份索引里的路径与本机现状一致；`archive/` 剩下的是每阶段的大块输出。
