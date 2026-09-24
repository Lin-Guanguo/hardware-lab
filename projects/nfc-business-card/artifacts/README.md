# Local generated artifacts

## 当前确定方案

Tracked sources and vendor files are indexed in the [R1 project README](../README.md). Everything here except this index is local generated data.

- `NFC-Card-R1-prototype.zip`: complete handoff; rebuild with `python3 projects/nfc-business-card/scripts/package-r1.py`.
- `r1-delivery/`: expanded handoff contents; rebuilt with the ZIP.
- `r1-routing/`: snapshots, route experiments and native export scratch files.
- `layout-reset-r3/`: two superseded local EDA routing experiments; the tracked R3 diagnostic source is in `eda/`.
- `archive/pre-r1/`: preserved E-series generated outputs.
- `archive/`: other preserved local checkpoints.

Use `hardware/production/r1/NFC-Card-R1-gerber.zip` for bare PCB fabrication. Do not upload the complete prototype ZIP as Gerber data.
