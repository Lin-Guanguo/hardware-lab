# NFC 名片 V4 KiCad 工程

## 当前确定方案

这是第四版的**迁移与关键区实际试布候选，不可制造**。完整结论、未完成项、回流图及国内 DFM 见 [阶段报告](../../kicad-v4-phase1.md)。先联合解决 VBUS／屏幕通道、参考地和电源输入，再决定整板详细设计。

用 KiCad 10.0.6 打开 [NFC-Card-V4.kicad_pro](NFC-Card-V4.kicad_pro)。项目包含根原理图和四张子页、PCB、规则、配置、符号库与 71 个使用中的封装变体；`fp-lib-table` / `sym-lib-table` 均用 `${KIPRJMOD}`，无需外部个人库。没有已验证的完整 STEP 装配模型。

保存重开已核对：66 个 BOM 位号、256 器件引脚、10 个板上触点，174 段铜线／22 个过孔；83 个未连接项是实际未完成。原理图／PCB parity 0、ERC 6、DRC 94，没有新增排除规则。

## 文件与证据

| 入口 | 用途 |
| --- | --- |
| `NFC-Card-V4.kicad_sch`、`1_…` 至 `4_…` | 全局标签连接的四页原理图；根页是导航 |
| `NFC-Card-V4.kicad_pcb` | 新试布，仅沿用 D 的 NFC 铜线；不是 D 全铜转换板 |
| `NFC-Card-V4.kicad_pro`、`.kicad_dru` | 双层／0.8 mm 与实际 DRC 规则 |
| `NFC_V4.kicad_sym`、`NFC_V4.pretty/` | 项目符号／封装；按实例保留非对称锡膏和开窗差异 |
| `placement-*.json`、`*-routing-spec*.json` | 本次各阶段决策／实际接受的几何；历史删除 UUID 不可直接用于新副本 |
| `reproduce-final-plan.json` | 从未清线的迁移基线，一次重放最终 38 个摆位、54 条路径／16 孔；目标是独立 `v4-replay/` |
| [最终验证](../../records/kicad-v4/final-validation.json)、[重开](../../records/kicad-v4/reopen.json) | 每个设计文件指纹、引脚与固定几何核对 |
| [制造诊断包](../../records/kicad-v4/dfm-diagnostic-02/README.md) | 含 D 旧铜的独立链路诊断，不能用于证明本试布的 DFM |

## 检查命令

从仓库根目录运行，使用已安装的 Python 几何库及现有 KiCad 工具链，不重新安装：

```sh
python3 tools/kicad/health.py
python3 projects/nfc-business-card/scripts/verify-v4-phase1.py
python3 projects/nfc-business-card/scripts/audit-v4-trial.py
```

后两条写入阶段验证记录和四张实际铜／地图片；它们针对当前冻结的第一阶段候选，不是任意新板的通用放行器。执行 ERC/DRC 的完整命令与预期非零结果在阶段报告中。

## 迁移与重放

实际导入顺序：KiCad Manager → File → Import Non-KiCad Project → EasyEDA Pro，选择 [D 交换文件](../../records/kicad-v4/NFC-Card-D-export.epro)，保存到全新的 `artifacts/kicad-v4/migration/native-import/`。导入后的基名为 `NFC-Card-D-export`，导入库为 `NFC-Card-D-easyedapro`；不要把 `.eprj2` 数据库送入这个入口。原始导入曾有跨页网络、禁铜区域与开口差异，必须再运行重建。

把 [D Gerber ZIP](../../records/board-review-d-diagnostic-gerber.zip)解压到新的 `artifacts/kicad-v4/migration/d-gerber/`。以下输出目录必须尚不存在；当前本机这些阶段已做过，不要覆盖它们：

```sh
python3 projects/nfc-business-card/scripts/migrate-v4-kicad.py --import-dir projects/nfc-business-card/artifacts/kicad-v4/migration/native-import --d-gerber-dir projects/nfc-business-card/artifacts/kicad-v4/migration/d-gerber --output projects/nfc-business-card/artifacts/kicad-v4/reconciled-d-REPLAY
python3 projects/nfc-business-card/scripts/prepare-v4-trial.py projects/nfc-business-card/artifacts/kicad-v4/reconciled-d-REPLAY projects/nfc-business-card/hardware/kicad/v4-replay
```

在 KiCad 打开 `v4-replay/NFC-Card-V4.kicad_pro` 及其 PCB Editor，再执行：

```sh
python3 tools/kicad/health.py --ipc --board /Users/linguanguo/dev/hardware-lab/projects/nfc-business-card/hardware/kicad/v4-replay/NFC-Card-V4.kicad_pcb
.cache/kicad-venv/bin/python projects/nfc-business-card/scripts/apply-v4-ipc.py projects/nfc-business-card/hardware/kicad/v4/reproduce-final-plan.json
```

脚本核对完整目标路径，只允许从 912 段／198 孔的未清线 D 基线执行首次清线，保留 NFC。关闭 PCB Editor，再恢复 IPC 可能扰动的导入封装局部图形：

```sh
python3 projects/nfc-business-card/scripts/finalize-v4-native.py projects/nfc-business-card/hardware/kicad/v4-replay projects/nfc-business-card/artifacts/kicad-v4/reconciled-d-REPLAY projects/nfc-business-card/artifacts/kicad-v4/migration/d-gerber projects/nfc-business-card/artifacts/kicad-v4/replay-finalize.json
```

最终原理图另外做了无连接线尾修复、原生 GUI 元数据规范化和根页排版；这些不改变网络。`clean-v4-schematic-stubs.py` 是本次固定目标、先后网表相同才保留的修复脚本，不能不改目标便拿去操作 replay。新副本必须独立开、保存、关、重开，执行 ERC/DRC/parity；不能把当前工程的验证计数移植给新副本。

上述聚合重放计划已和保存板的摆位及铜段／过孔数量核对；实际分阶段 IPC 操作及最终原生板已经验证，聚合计划未另开一次 GUI 全程重演，不宣称独立重演也已通过。

## 制造导出

仅在已保存、重新检查的同一版本导出。以下可用于当前未完成候选的**新诊断**；不会自动上传，更不能下单：

```sh
python3 projects/nfc-business-card/scripts/export-kicad-dfm.py projects/nfc-business-card/hardware/kicad/v4/NFC-Card-V4.kicad_pcb projects/nfc-business-card/artifacts/kicad-v4/dfm-NEW
```

输出同版 Gerber/钻孔 ZIP、BOM.csv、CPL.csv、原生位置表、钻孔报告和 SHA-256 manifest。脚本坚持冻结 D 的 66 件料号；以后若获授权改选型，必须先更新相应源数据／对账，不跳过断言。国内页面每次检查都需核对 0.8 mm 板厚和工艺字段，查看层、槽、关键器件方向及检查细目。
