# Hardware Lab

A shared Git repository for personal hardware experiments and small devices.
Each device lives under `projects/` and keeps its own firmware, hardware notes,
dependencies, and build workflow.

## Projects

| Project | Purpose | Latest recorded status |
| --- | --- | --- |
| [AI Passport](projects/ai-passport/README.md) | Explore a compact programmable badge, screen/button interactions, and NFC links | Ordered; waiting for delivery, confirmed 2026-09-16 |
| [Image Oracle](projects/image-oracle/README.md) | Map camera images to answers with a fixed algorithm; a lava lamp is the default scene | Components selected/ordered; physical inventory and development still pending |

## Layout

```text
hardware-lab/
├── README.md
├── AGENTS.md
├── .gitignore
├── docs/
│   └── inventory.md
└── projects/
    ├── ai-passport/
    │   ├── README.md
    │   ├── firmware/
    │   └── docs/
    └── image-oracle/
        ├── README.md
        ├── firmware/
        ├── hardware/
        ├── enclosure/
        └── docs/
```

- `firmware/`: the complete, independently buildable firmware project.
- `docs/`: project-specific references, measurements, and experiment notes.
- `hardware/`: the actual bill of materials, wiring, schematics, and PCB sources.
- `enclosure/`: editable enclosure models and the files used for fabrication.
- Root `docs/`: information shared across projects, starting with the inventory.

Empty directories contain `.gitkeep` so Git preserves the initial layout.
Remove a placeholder when its directory gains real files. Add other directories
only when needed; there is no shared framework or root build system yet.

## Starting work

1. Read [AGENTS.md](AGENTS.md) and the selected project's README.
2. Check the actual device and its documentation before assigning pins or power.
3. Put the firmware in that project's `firmware/` directory and record the exact
   toolchain, dependency versions, and working shell commands in its README.
4. Reproduce a known-good example before changing application behavior.
5. Record what was built, what was tested on hardware, and what remains unknown.

There are no build, flash, or test commands yet. The initial commit establishes
the workspace only. Development is intended for a local Mac using an editor,
shell tools, and AI assistance.

## Repository conventions

- Organize projects by device or purpose, rather than MCU model. Each project
  may use a different toolchain version.
- Keep detailed status and next steps in the project README; the table above is
  only a brief index.
- Commit source code, useful small assets, editable CAD, dependency lockfiles,
  and reproducible configuration. Put temporary firmware exports, captures,
  and measurements in ignored `artifacts/` or `logs/` directories.
- For ESP-IDF, preserve deliberate settings in `sdkconfig.defaults` and any
  required variants; generated `sdkconfig` and build output are ignored.
- When importing upstream code, preserve its license and record its URL,
  revision, and local changes in the project docs. Do not accidentally import
  an embedded `.git` directory. Submodules are not part of the initial layout.
- Prefer English for code, comments, and repository instructions; experiment
  notes can use Chinese when clearer.

Historical discussions and purchasing decisions remain in
[CyberMnema](../CyberMnema/README.md). Link to them rather than copying the full
conversation here. This repository records the actual engineering work.
