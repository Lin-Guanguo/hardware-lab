# R1 USB firmware update and SWD recovery review

Status: hardware review and USB resistor correction completed; firmware and physical USB/SWD operation are unverified. The five SWD lands now use 2.54 mm pitch for the user-selected single-row 5P clip. The user accepted nominal fit assumptions; detailed clip metrology is not a release gate. No factory programming is requested.

**Recovery decision, 2026-09-24:** the user accepts connecting an SWD programmer for recovery. Retain GND, VDD_3V3/VTref, SWCLK, SWDIO and NRESET; do not add a hidden RESET switch or side access hole for R1. The earlier RESET mechanical study is reference only and is no longer an ordering decision. Routine USB updates/logs remain planned firmware work; standalone button-only recovery with a failed application is not required.

## Implemented hardware correction

R3 and R4 changed from 27 ohm to **0 ohm, UNI-ROYAL 0603WAF0000T5E / C21189**, using the existing R0603 lands and component locations. Schematic and PCB instance procurement fields are synchronized. Nordic states that the nRF52840 USB PHY already includes the series resistors; extra termination is not required. Keeping the two lands permits later measured changes without a layout change. [Nordic verified answer](https://devzone.nordicsemi.com/f/nordic-q-a/94955/resistors-for-d-and-d-), [Nordic signalling discussion](https://devzone.nordicsemi.com/f/nordic-q-a/82014/nrf52840-usb-d-d--impedance-matching/340456).

## Netlist checks

| Function | Current connection / finding |
| --- | --- |
| USB D+ | J1 A6/B6 → USB_DP_CONN / U5 protection → R3 → U1.35 |
| USB D− | J1 A7/B7 → USB_DM_CONN / U5 protection → R4 → U1.34 |
| Type-C detection | CC1 and CC2 each have their own 5.1 kohm Rd to GND; U6 protects these lines. No USB PD or advertised-current detection controller is present. |
| USB supply | J1 VBUS → U1.32 and U2.10; C1 is the local 2.2 µF module VBUS capacitor, C8 is the charger 4.7 µF input capacitor. |
| Module power | U2 SYS → U3 TPS7A0233 → VDD_3V3 → U1 VDD and VDDH. DCCH remains unconnected in normal voltage mode. |
| Charge enable | R7 pulls CHG_CE_N high by default. Firmware must explicitly enable charging and set a battery-appropriate current. |
| Existing recovery input candidate | SW2 / KEY_NEXT_N → U1.4 / P1.11, active low, with a 10 kohm pull-up. Final bootloader board configuration must agree. |
| Reset | U1.40 / P0.18 → TP5 NRESET. There is currently **no physical RESET switch**. Configure both UICR PSELRESET registers during initial SWD programming. |
| VBUS protection limit | U5/U6 protect signal lines; they are not a VBUS clamp. The charger's input protection does not protect the parallel U1 VBUS branch. VBUS hot-plug waveform / ESD protection remains a review and bench item; no surge immunity is claimed. |

USB uses its own VBUS-powered regulator; supplying only VDD_3V3 does not establish USB operation. [Nordic power specification](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/power.html).

The charger's default input limit is 500 mA; its default charge current is 10 mA, and CE is pulled inactive on this PCB. This does not prove compliance with a USB host's pre-enumeration or suspend limits. Both bootloader and application must control their total VBUS load, choose a conservative limit before enumeration, and handle suspend/detach. Do not infer a right to draw 1.5/3 A from the two Rd resistors. Battery charging limits also require the actual pack's specification. [TI BQ25186 data sheet](https://www.ti.com/lit/ds/symlink/bq25186.pdf), [TI default charge current clarification](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1540320/bq25186-spec-check).

## Firmware and recovery contract

1. **First programming:** the user powers the board and uses SWD to program a board-specific bootloader and required configuration. Treat VDD_3V3 as the debugger's target-voltage reference by default; do not simultaneously drive it from an unrelated programmer supply.
2. **Routine update:** evaluate Adafruit nRF52 UF2 with the final framework. NCS/Zephyr is a candidate, not a frozen production port. Confirm bootloader/SoftDevice/MBR layout, application link address, UF2 family identifier, USB identity, LF clock source, button GPIO and flash protection. Do not flash an unrelated board's complete image.
3. **Application failure:** connect the SWD programmer and recover through the retained SWD/NRESET pads. Firmware may additionally support holding SW2 while the programmer asserts NRESET to enter the bootloader, but direct SWD reprogramming remains the fallback. A runtime USB command alone is insufficient when the application cannot start; no standalone hidden RESET is required for R1.
4. **Interrupted application update:** retry through the bootloader if reachable; otherwise recover with SWD. UF2 does not inherently guarantee automatic rollback or a second application image; use an explicitly designed MCUboot / dual-image scheme if that becomes a requirement.
5. **Bootloader / configuration failure:** retain all five SWD signals as the recovery path. Document whether a debugger recovery mass-erase is needed and warn that it removes stored user data. Do not enable debug protection without a deliberate recovery decision.
6. **Logs:** application USB CDC ACM is the candidate console, using bounded/non-blocking buffering and detach handling. UF2 bootloader USB and application USB are separate firmware states. USB logs/update do not provide SWD breakpoints.

A battery keeps the MCU powered when USB is unplugged. USB insertion/removal is therefore not a reliable reset mechanism. [Adafruit bootloader](https://github.com/adafruit/Adafruit_nRF52_Bootloader), [Zephyr UF2 board example](https://docs.zephyrproject.org/latest/boards/adafruit/feather_nrf52840/doc/index.html), [Zephyr CDC ACM](https://docs.zephyrproject.org/latest/services/connectivity/usb/device_next/cdc_acm.html), [Nordic UICR](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/uicr.html).

## Mechanical handoff — proposals, not installed parts

### Hidden RESET — not selected for R1

The following dimensions preserve the earlier study only. The user selected SWD programmer recovery; do not implement this switch or its opening as part of R1 production preparation.

A rear-mounted switch cannot be assumed to fit the current **0.32 mm** PCB-to-rear-cover space. Assess a front-side, side-operated switch with an inconspicuous right-wall tool hole.

Candidate for CAD assessment: **Alps SKSCLBE010**, nominal **3.5 × 3.55 × 1.25 mm**, side push, 0.2 mm travel, 2.2 N force, with guide bosses. The manufacturer drawing must determine the full land/body envelope, boss penetration, actuator datum and tool clearance. [Manufacturer specification](https://tech.alpsalpine.com/e/products/detail/SKSCLBE010/).

The [CAD candidate study](../enclosure/r1-recovery-study.md) found space at front-coordinate datum **C = (80.30, 8.60) mm**, actuator toward +X, pressed toward −X. This datum is defined by the manufacturer drawing, not an EDA library origin. The operating end is at X = 82.40 mm; its axis is approximately outer-case Z = 2.620 mm. The full terminal span is 4.85 ±0.10 mm and recommended land span is 5.00 mm; the body dimensions alone are insufficient.

The conservative body/terminal envelope, including 0.10 mm assumed installation allowance, is **X 78.70…82.55, Y 6.075…11.125, Z 1.920…3.420 mm**. It clears the studied rounded upper case by at least 0.85 mm and passes its insertion sweep. Two locating holes are proposed at (79.40,8.60)/(81.20,8.60) mm, Ø0.80 +0.05/0 mm; the maximum 0.60 mm boss length fits within the 0.80 mm PCB. The final footprint still needs mounting-face/mirroring and all-layer copper checks.

A Ø2.0 mm side access hole was evaluated at Y = 8.60, Z ≈ 2.620 mm. A hypothetical Ø0.6 mm tool travels approximately 2.2 mm to the actuator and 2.4 mm at full nominal travel. **Tool guidance, allowable offset, overtravel stop and physical force/return are unresolved.** This establishes candidate space only. No PCB pads, board holes, switch BOM row or released CAD openings have been added. The study is against the rounded enclosure candidate; it does not modify or release the packaged frozen 5.8 mm shell.

### Five-pin clip

Selected fixture: **绿深旗舰店 / 单排5P探针模块（2.54mm间距）**, from the user's product screenshot on 2026-09-24. No manufacturer model number was shown. The user explicitly accepted adaptation by nominal pitch without waiting for exact needle projection/jaw dimensions. The first illustration labels fixture needle holes as Ø1.5 mm; this does not establish contact-tip diameter. These assumptions remain subject to physical trial fit, not further drawing requests.

The native PCB now has **five rear lands at exactly 100 mil / 2.54 mm pitch**, with the original row centre and Y retained. Coordinates below use the **front PCB coordinate system**, in mm:

| Land | Signal | X | Y | Identification |
| --- | --- | ---: | ---: | --- |
| TP1 | GND | 65.92062 | 48.49876 | Square, pin 1 |
| TP2 | VDD_3V3 / VTref | 68.46062 | 48.49876 | Circle |
| TP3 | SWCLK | 71.00062 | 48.49876 | Circle |
| TP4 | SWDIO | 73.54062 | 48.49876 | Circle |
| TP5 | NRESET | 76.08062 | 48.49876 | Circle |

Land size is approximately **1.20 mm** (native 1.19888 mm). Total first-to-last centre span is **10.16 mm**. TP1's square shape and the individual GND/3V3/CLK/DIO/RST rear labels identify orientation; this is visual identification, not mechanical keying. With PCB +Y upward in a front projection the table runs left to right; looking through the back about the vertical axis reverses that order. Match the square GND end and the actual debugger cable signal labels before connecting. VDD_3V3 is target-voltage reference by default.

Local rear access traces were adjusted without moving components or adding vias. Saved/reopened native DRC is zero; independent copper checks pass. [Applied plan](records/r1-swd-254-plan.json), [saved geometry and preservation checks](records/r1-swd-254-check.json).

CAD uses **Ø1.60 mm holes with an outer R0.05 mm mouth** for the revised access. At 2.54 mm pitch the bore web is 0.94 mm and minimum surface web is **0.84 mm**. The nominal rear face-to-pad depth remains **1.12 mm**. The [rounded rear-cover candidate](../enclosure/r1-rounded-rear-soft-swd254/README.md) documents the five-hole change; the packaged clear case is synchronized separately and checked against these PCB coordinates. Keep the existing 0.8 mm bare board and 5.8 mm enclosure for trial fitting. Probe reach, spring compression, coatings and reliable contact are physical checks, not claimed compatibility measurements.

## Required physical tests

- SWD identify, initial bootloader program, reset pin operation, and recovery after an intentionally invalid application.
- USB A-to-C and C-to-C data cables, both plug orientations; enumeration in bootloader and application; battery-only / USB-only / both-source transitions.
- VBUS hot-plug peaks, 3.3 V stability and source/backfeed behaviour; total pre-enumeration, configured and suspend current; conservative battery charge configuration.
- UF2 update interruption and retry; SWD/NRESET recovery with an invalid application while the battery remains connected. If implemented, test SW2 plus programmer-driven reset as an additional bootloader entry.
- USB log handling with no host, closed terminal and unplugged cable; no display/button task stalls.
- Actual clip registration, electrical contact and non-shorting through the assembled cover.

These are open verification items, not features marked usable.
