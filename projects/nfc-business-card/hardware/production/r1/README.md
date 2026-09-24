# R1 manufacturing exports

## 当前确定方案

Frozen engineering-prototype exports from the [native project](../../../../../eda/NFC-Card-R1.eprj2). These are tracked in Git. Review the [project status](../../../README.md) before ordering; RF and physical fit are not qualified.

| File | Use |
| --- | --- |
| [NFC-Card-R1-gerber.zip](NFC-Card-R1-gerber.zip) | Upload for bare PCB fabrication: copper, masks, silkscreen, paste, outline and drilling |
| [NFC-Card-R1-bom.csv](NFC-Card-R1-bom.csv) | Parts, quantities and designators for PCBA |
| [NFC-Card-R1-cpl.csv](NFC-Card-R1-cpl.csv) | Component placement, side and rotation for PCBA; verify vendor preview |
| [NFC-Card-R1-assembly.pdf](NFC-Card-R1-assembly.pdf) | Human-readable assembly, copper and drilling review |
| [NFC-Card-R1-pcba.step](NFC-Card-R1-pcba.step) | Populated board mechanical model |
| [NFC-Card-R1-project.epro2](NFC-Card-R1-project.epro2) | Portable EasyEDA project backup/import |

The editable `.eprj2` remains in `eda/`; enclosure STL files are in [enclosure/r1-clear-5.8](../../../enclosure/r1-clear-5.8/). The complete `NFC-Card-R1-prototype.zip` is an all-in-one handoff, not a board-fabrication upload.

## Export from the GUI

Open the PCB, then **导出 → PCB 制板文件（Gerber） → check DRC/flying wires → 一键导出 or 自定义配置 → 导出**. See [EasyEDA's official guide](https://prodocs.lceda.cn/cn/pcb/export-pcb-fabrication-file-gerber/). The API calls the same native manufacture-data exporter.

The 2026-09-24 manual download is **141,176 bytes**; the initial API export is **90,588 bytes**. The manual export adds documentation, drill-drawing and top-assembly layers and uses a different coordinate precision. The common manufacturing layers agree within 0.000005 mm after normalization; flying-probe data is identical. [Comparison evidence](../../records/r1-gerber-export-comparison.json). This comparison is tied to those exact hashes; later PCB revisions invalidate equivalence to the old download.
