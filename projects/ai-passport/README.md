# AI Passport

Explore the FoloToy AI Passport as a compact, programmable device with a screen,
buttons, battery, and NFC tag.

## Current state

- On 2026-09-16, the user confirmed it had been ordered and planned to start
  after delivery.
- No device inspection, firmware import, toolchain installation, build,
  flashing, or hardware tests have been performed in this project.
- `firmware/` and `docs/` are placeholders for the first development session.

## Interests and constraints

- Start with screen/button interactions and a small useful application.
- Explore selecting a business card, WeChat link, or Xiaohongshu link on screen,
  then opening the selected content on another phone through NFC.
- Prefer low power consumption and a local Mac workflow using shell tools.
- The documented passive NTAG213 does not expose an MCU-side BSP API. Button-
  controlled NFC content switching is a development question, not a verified
  product feature. A fixed URL with a server-controlled destination is another
  possible approach, with different network and app-link constraints.

## Next session after delivery

1. Verify the hardware revision, supplied accessories, stock firmware, and
   recovery method. Check the shipped NFC tag and its write protection.
2. Import the matching official project into `firmware/`, preserving licenses
   and recording the upstream revision in `docs/`.
3. Reproduce its build and record the exact setup, build, flash, and log commands
   below. Follow the imported project's board-specific instructions.
4. Run a minimal screen/button application, then investigate NFC and power use
   as separate experiments.

## Commands

Not established yet. Add only commands verified with this project's source and
toolchain; do not infer them from a generic ESP32-C3 board.

## References

- [Official website](https://ai-passport.folotoy.cn/#diy)
- [Official Codex development guide](https://ai-passport.folotoy.cn/guides/create-a-play-with-codex/)
- [Official firmware installer](https://ai-passport.folotoy.cn/tools/web-flasher/)
- [Official source](https://github.com/FoloToy/ai-passport)
- [Purchase and discussion archive](../../../CyberMnema/timeline/2026/09/W38/AI_Passport.20260916.md)
