# KiCad → 国内嘉立创制造诊断 02

## 当前确定方案

此目录冻结实际上传国内嘉立创 **DFMP2609280906** 的文件和源 PCB。它保留 D 旧铜，只验证迁移／制造文件解释，**不能下单，也不是 V4 新布局**。完整发现见 [阶段报告](../../../kicad-v4-phase1.md#国内嘉立创文件衔接)。

`NFC-Card-V4.kicad_pcb` 是可独立打开的诊断 PCB，旁边配置／规则用于复核导出；本目录不是完整原理图工程。用于继续设计的完整原生工程在 [v4/](../../../kicad/v4/README.md)。

| 文件 | 用途 |
| --- | --- |
| `NFC-V4-migration-diagnostic-gerber.zip` | 实际上传的 9 层 Gerber＋PTH/空 NPTH 钻孔，含 4 个 USB 镀铜槽 |
| `BOM.csv` / `CPL.csv` | 同板 29 组／66 件、国内表头与坐标约定 |
| `kicad-pos.csv` | 转换前原生贴装坐标，便于核对角度／板面 |
| `drill-report.txt` | 198 圆孔＋4 镀铜槽、0 非镀铜孔 |
| `manifest.json` | 原始导出路径、CLI 参数、源板与所有导出文件 SHA-256 |

源板 SHA-256 为 `3cbff44048c720afc1d90cb3384e71c46ff072c8f25d7ad9833a02f6f6c38c28`。manifest 中的 `artifacts/` 是导出时路径，本目录保存字节相同的源板和上传文件。重新导出时日期／ZIP 时间戳会变化，应给新批次生成新 manifest，而非要求文件哈希永远相同。

从仓库根运行以下命令可从保存的诊断 PCB 重建一个新输出目录：

```sh
python3 projects/nfc-business-card/scripts/export-kicad-dfm.py projects/nfc-business-card/hardware/records/kicad-v4/dfm-diagnostic-02/NFC-Card-V4.kicad_pcb projects/nfc-business-card/artifacts/kicad-v4/dfm-REPEAT
```

导出工具不会上传、付款或生成订单。后续在国内网页选择 Gerber ZIP，再在同一任务中上传 BOM/CPL，检查板厚、层、缺口、槽、器件匹配与方向，执行 PCB 和 SMT DFM，保存原始结果并回到对应 KiCad 源板修改。当前已上传批次不能被新导出文件静默替代。
