#!/usr/bin/env python3
"""Check critical connections in the EasyEDA draft export, not manufacturing readiness."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    args = parser.parse_args()
    data = json.loads(args.netlist.read_text())
    items = list(data["components"].values())
    refs = [c["props"]["Designator"] for c in items]
    errors = []
    if len(set(refs)) != len(refs):
        errors.append("Duplicate designators")
    components = dict(zip(refs, items))
    expected_refs = {"J1", "U1", "U2", "U3", "SW1", "SW2", "SW3"}
    expected_refs |= {f"R{i}" for i in range(1, 13)}
    expected_refs |= {f"C{i}" for i in range(1, 9)}
    if set(refs) != expected_refs:
        errors.append(f"Unexpected populated component set: {sorted(set(refs) ^ expected_refs)}")

    checks = 0

    def require(net, *pins):
        nonlocal checks
        for endpoint in pins:
            ref, pin = endpoint.split(":")
            actual = components.get(ref, {}).get("pinInfoMap", {}).get(pin, {}).get("net")
            checks += 1
            if actual != net:
                errors.append(f"{endpoint}: expected {net!r}, got {actual!r}")

    # Module pin numbers follow Raytac Rev L; charger/LDO follow TI pin tables.
    require("VDD_3V3", "U1:28", "U1:30", "U3:5", "C5:1", "C6:1", "C7:1")
    require("SYS", "U2:1", "U3:1", "U3:3", "C2:1", "C4:1")
    require("USB_VBUS", "J1:A4B9", "J1:B4A9", "U2:10", "U1:32", "C1:1", "C8:1")
    require("BAT_PACK_TBD", "U2:2", "C3:1")
    require("BAT_NTC_TBD", "U2:6")
    require("GND", "U1:1", "U1:2", "U1:15", "U1:33", "U1:55", "U2:5", "U2:11", "U3:2")
    require("GND", "J1:A1B12", "J1:B1A12", "J1:17", "J1:18", "J1:19", "J1:20")
    require("GND", *(f"C{i}:2" for i in range(1, 9)), "R1:2", "R2:2")
    require("USB_CC1", "J1:A5", "R1:1")
    require("USB_CC2", "J1:B5", "R2:1")
    require("USB_DP_CONN", "J1:A6", "J1:B6", "R3:1")
    require("USB_DM_CONN", "J1:A7", "J1:B7", "R4:1")
    require("USB_DP_MCU", "R3:2", "U1:35")
    require("USB_DM_MCU", "R4:2", "U1:34")
    require("CHG_SDA", "U1:19", "U2:7", "R5:2")
    require("CHG_SCL", "U1:16", "U2:8", "R6:2")
    require("CHG_CE_N", "U1:22", "U2:4", "R7:2")
    require("CHG_INT_N", "U1:20", "U2:9", "R8:2")
    require("CHG_PG_N", "U1:21", "U2:3", "R9:2")
    require("VDD_3V3", *(f"R{i}:1" for i in range(5, 13)))
    for i, (net, pin) in enumerate(zip(("KEY_PREV_N", "KEY_NEXT_N", "KEY_OK_N"), (3, 4, 5)), 1):
        # ALPS connects 1-2 and 3-4 internally; these must not bridge power rails.
        require(net, f"U1:{pin}", f"SW{i}:1", f"SW{i}:2", f"R{i + 9}:2")
        require("GND", f"SW{i}:3", f"SW{i}:4")
    for pin, net in {51: "SWDIO", 53: "SWDCLK", 40: "NRESET", 52: "NFC1_TBD", 54: "NFC2_TBD"}.items():
        require(net, f"U1:{pin}")
    for ref, pin in (("U1", "31"), ("U3", "4"), ("J1", "A8"), ("J1", "B8")):
        require("", f"{ref}:{pin}")

    suppliers = Counter(c["props"].get("Supplier Part") for c in items)
    for part, count in {"C23186": 2, "C325726": 2, "C25804": 8}.items():
        if suppliers[part] != count:
            errors.append(f"Wrong resistor selection/count for {part}")
    nets = defaultdict(list)
    for ref, c in components.items():
        for pin, info in c["pinInfoMap"].items():
            if info["net"]:
                nets[info["net"]].append(f"{ref}:{pin}")
    report = {
        "passed": not errors,
        "components": len(items),
        "pin_checks": checks,
        "named_nets": len(nets),
        "single_pin_nets": {net: pins for net, pins in sorted(nets.items()) if len(pins) == 1},
        "errors": errors,
        "scope": "Connectivity only; ESD, RF, display, battery, footprints and physical tests remain open.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
