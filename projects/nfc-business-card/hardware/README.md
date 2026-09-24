# R1 hardware

## 当前确定方案

Use the [R1 native project](../../../eda/NFC-Card-R1.eprj2) and [current project index](../README.md). The uncommitted antenna/CC2 revision is complete; [C1 placement and USB stitching findings](pcb-r1-review.md) remain for discussion before ordering.

| Files | Purpose |
| --- | --- |
| [production/r1/](production/r1/README.md) | Frozen vendor exports and portable project |
| [pcb-r1-delivery.md](pcb-r1-delivery.md) | Current engineering report and checks |
| [r1-design.json](r1-design.json) | Coordinated dimensional inputs |
| [records/r1-validation.json](records/r1-validation.json) | Consolidated verification; other `r1-*` files hold inputs and detailed evidence |
| [candidate-bom.md](candidate-bom.md), [component-options.md](component-options.md) | Component selection rationale; the exported BOM is authoritative for R1 |
| [battery-purchase-candidates.json](battery-purchase-candidates.json) | Purchased battery candidates and measurement uncertainty |
| [Historical hardware](../archive/pre-r1/hardware/) | E-series snapshots, placement studies and old manufacturing gates |

The native project is editable design data. Gerber describes board artwork and drilling; it does not contain the complete editable design, firmware or enclosure.
