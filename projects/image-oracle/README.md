# Image Oracle

A camera-driven answer book: capture an image, apply a fixed algorithm, and
display an answer from a local collection. A lava lamp is the default scene;
other subjects can also provide the image.

## Current state

- An ESP32-S3-CAM bundle and experimental components were discussed and selected.
  The bundle was reported purchased; actual hardware and quantities still need
  checking against the shipment.
- No firmware, verified wiring, enclosure model, or hardware test exists in this
  project yet.

## Design decisions to preserve

- The image is the only changing input to answer selection. With the same
  algorithm, processing rules, and answer collection, the same image produces
  the same answer.
- Do not add random seeds, timestamps, or counters to vary the result. A new
  draw means taking a new picture; repeated answers are allowed.
- The intended core hardware is a camera, screen, and five-way button module.
  Other purchased modules are available for experiments, not required features.
- Start with USB power and breadboard experiments. Decide on wiring and an
  enclosure after the functional prototype works and dimensions are measured.
- Keep the lava lamp's original mains supply separate. This project develops
  only the low-voltage electronics.
- AI Passport currently has no documented camera and is a separate project.

## Directory ownership

- `firmware/`: the complete firmware project and reproducible build configuration.
- `hardware/`: the verified BOM, pin assignments, wiring, and any future PCB.
- `enclosure/`: editable mechanical designs and fabrication exports when needed.
- `docs/`: component references, experiments, measurements, and design decisions.

## Next session after delivery

1. Identify the exact development board, camera, display, memory, and included
   modules; resolve the SHT30/DHT11 ordering discrepancy.
2. Obtain the matching vendor example and verify its wiring before importing
   source into `firmware/`.
3. Record a working macOS setup and build workflow. ESP-IDF is the preference;
   if the useful vendor example uses Arduino or PlatformIO, reproduce it first.
4. Test the screen, camera, and button functions incrementally, then implement
   the capture-to-answer flow and verify repeatability for a fixed image.

## Commands

Not established yet. Add verified build, flash, and serial-log commands after
the board and firmware are identified.

## References

- [Original discussion, purchasing notes, and startup plan](../../../CyberMnema/timeline/2026/09/W38/熔岩灯交互装置.20260914.md)
- [Shared inventory](../../docs/inventory.md)
