# R1 progress

## 当前确定方案

2026-09-24: checkpoint `ccf9f92` is committed. The [subsequent antenna/layout review](../hardware/pcb-r1-review.md) and battery-pad changes are saved in a new checkpoint at the user's request, alongside the separate enclosure studies.

| Work | Status / next step |
| --- | --- |
| Source and file organization | R1 active files indexed; E-series history archived; manufacturing outputs tracked |
| Existing electrical checks | Saved/reopened native DRC 0; 58 components, 238 schematic pins matched; copper connectivity and winding cut proof pass |
| Screen protrusion perimeter | Corrected: no pours through the three exposed board edges; selected top B pads/routes are a narrow recorded exception |
| Coil appearance and edge offsets | Complete: five turns, 45° chamfers, equal 3 mm centreline offsets |
| Broader layout review | Review complete; CC2 branch corrected, exports refreshed. **C1 placement needs correction before ordering; USB return stitching remains an optimization.** |
| Enclosure | Nominal fit and meshes pass; physical assembly unverified |
| Packaging optimization | [Height handoff](../enclosure/r1-height-handoff.md) records regional heights and key motion. User deferred thickness/button process; active case remains 5.8 mm. |
| Battery B pads | Applied at (32.5,18.7)/(35.5,18.7) mm for upper-right lead exit; native DRC and copper checks pass. Frozen CAD wire/ferrite service volumes need later revision. |
| Redundant vias | Removed BAT/CC2/3V3 single-layer vias and one dead stub; all remaining vias contact copper on both faces. Audit rejects an injected redundant via. |
| RF and bring-up | User/agent must test the assembled board; provisional 220 pF tuning capacitors |
| Battery | User measures protected pack and wires; nominal 31 × 12 × 3 mm |

No order placed. [Historical progress and experiments](../archive/pre-r1/readmes/projects/nfc-business-card/docs/progress.md) retain earlier findings and resolutions.
