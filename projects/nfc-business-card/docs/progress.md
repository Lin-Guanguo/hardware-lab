# R1 progress

## 当前确定方案

2026-09-24: the [R1 checkpoint](../README.md) freezes the routed PCB and coordinated 5.8 mm clear enclosure before antenna optimization.

| Work | Status / next step |
| --- | --- |
| Source and file organization | R1 active files indexed; E-series history archived; manufacturing outputs tracked |
| Existing electrical checks | Saved/reopened native DRC 0; 58 components, 238 schematic pins matched; copper connectivity and winding cut proof pass |
| Screen protrusion perimeter | **Open finding:** residual GND outside the old rectangular keepout; remove in the next PCB revision |
| Coil appearance and edge offsets | Next revision: 45° chamfers and equal spacing to the three exposed board edges |
| Broader layout review | Recheck using `pcb-methodology` and applicable upstream rules; refresh downstream exports |
| Enclosure | Nominal fit and meshes pass; physical assembly unverified |
| RF and bring-up | User/agent must test the assembled board; provisional 220 pF tuning capacitors |
| Battery | User measures protected pack and wires; nominal 31 × 12 × 3 mm |

No order placed. [Historical progress and experiments](../archive/pre-r1/readmes/projects/nfc-business-card/docs/progress.md) retain earlier findings and resolutions.
