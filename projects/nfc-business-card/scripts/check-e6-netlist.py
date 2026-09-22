#!/usr/bin/env python3
"""Verify the E6 schematic against the earlier circuit and reviewed pin tables."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--pcb", type=Path)
    parser.add_argument("--pcb-netlist", type=Path)
    args = parser.parse_args()
    hardware = Path(__file__).resolve().parents[1] / "hardware"
    data = json.loads(args.netlist.read_text())
    items = list(data["components"].values())
    components = {c["props"]["Designator"]: c for c in items}
    baseline = json.loads((hardware / "schematic-draft.enet").read_text())
    expected = {
        c["props"]["Designator"]: {p: v["net"] for p, v in c["pinInfoMap"].items()}
        for c in baseline["components"].values()
    }
    expected.update({
        "J2": dict(zip(map(str, range(1, 27)), [
            "", "EPD_GDR", "EPD_RESE", "EPD_VDDL", "EPD_VSPL1", "", "",
            "EPD_BS0", "EPD_BUSY_TBD", "EPD_RESET_N_TBD", "EPD_DC_TBD",
            "EPD_CS_N_TBD", "EPD_SCK_TBD", "EPD_MOSI_TBD", "EPD_VDD",
            "EPD_VSPL2", "GND", "EPD_VSNL1", "EPD_VSNL2", "EPD_VSPH",
            "EPD_VGH", "EPD_VSNH", "EPD_VGL", "EPD_VCOM", "", "",
        ])),
        "U4": {"1": "VDD_3V3", "2": "GND", "3": "EPD_EN_TBD", "4": "",
               "5": "EPD_VDD", "6": "EPD_VDD"},
        "U5": {"1": "USB_DP_CONN", "2": "USB_DM_CONN", "3": "GND"},
        "U6": {"1": "USB_CC1", "2": "USB_CC2", "3": "GND"},
        "Q1": {"1": "EPD_GDR", "2": "EPD_RESE", "3": "EPD_SW"},
    })
    # MBR0530: pin 1 cathode, pin 2 anode; D3 generates the negative rail.
    pairs = {
        "L1": ("EPD_VDD", "EPD_SW"),
        "D1": ("EPD_VPH", "EPD_SW"), "D2": ("GND", "EPD_PUMP"),
        "D3": ("EPD_PUMP", "EPD_VGL"),
        "R13": ("EPD_EN_TBD", "GND"), "R14": ("EPD_GDR", "GND"),
        "R15": ("EPD_RESE", "GND"), "R16": ("EPD_VPH", "EPD_VGH"),
        "R17": ("EPD_BS0", "GND"), "R18": ("EPD_VDD", "EPD_BUSY_TBD"),
        "C9": ("VDD_3V3", "GND"), "C10": ("EPD_VDD", "GND"),
        "C11": ("EPD_SW", "EPD_PUMP"), "C12": ("EPD_VPH", "GND"),
        "C13": ("EPD_VGL", "GND"),
    }
    for i, net in enumerate([
        "EPD_VDDL", "EPD_VSPL1", "EPD_VSPL2", "EPD_VSNL1", "EPD_VSNL2",
        "EPD_VSPH", "EPD_VSNH", "EPD_VGL", "EPD_VCOM",
    ], 14):
        pairs[f"C{i}"] = (net, "GND")
    expected.update({ref: dict(zip(("1", "2"), nets)) for ref, nets in pairs.items()})
    errors = []
    if len(items) != len(components) or set(components) != set(expected):
        errors.append("Duplicate or unexpected component designators")
    checks = 0
    for ref, pins in expected.items():
        actual = components.get(ref, {}).get("pinInfoMap", {})
        for pin, net in pins.items():
            checks += 1
            if actual.get(pin, {}).get("net") != net:
                errors.append(f"{ref}:{pin}: expected {net!r}, got {actual.get(pin)}")
    for i in range(9, 23):
        props = components.get(f"C{i}", {}).get("props", {})
        value, voltage = ("4.7uF", "25V") if i in (14, 15, 19) else ("1uF", "50V")
        for key, want in (("Value", value), ("Voltage Rating", voltage),
                          ("Temperature Coefficient", "X7R")):
            if props.get(key) != want:
                errors.append(f"C{i}: {key} must be {want}, got {props.get(key)}")
    pcb_checks = 0
    if args.pcb:
        pcb = json.loads(args.pcb.read_text())
        pcb = pcb.get("result", pcb)
        actual = {c["ref"]: c for c in pcb["components"]}
        if set(actual) != set(components) or len(actual) != len(pcb["components"]):
            errors.append("PCB component set differs from schematic")
        for ref, pins in expected.items():
            for pad in actual.get(ref, {}).get("pads", []):
                pcb_checks += 1
                if pad["net"] != pins.get(pad["padNumber"]):
                    errors.append(f"PCB {ref}:{pad['padNumber']} has wrong net {pad['net']}")
            if {p['padNumber'] for p in actual.get(ref, {}).get('pads', [])} != set(pins):
                errors.append(f"PCB {ref} pin set differs from schematic")
    association_checks = 0
    if args.pcb_netlist:
        pcb_items = json.loads(args.pcb_netlist.read_text())["components"]
        by_ref = {c["props"]["Designator"]: c for c in pcb_items.values()}
        if len(by_ref) != len(pcb_items) or set(by_ref) != set(components):
            errors.append("PCB netlist component set differs from schematic")
        for ref, schematic in components.items():
            candidate = by_ref.get(ref, {})
            for key in ("Unique ID", "Footprint"):
                association_checks += 1
                want = schematic["props"].get(key)
                got = candidate.get("props", {}).get(key)
                if not want or got != want:
                    errors.append(f"PCB {ref}: {key} expected {want!r}, got {got!r}")
            pins = {p: v["net"] for p, v in schematic["pinInfoMap"].items()}
            pads = {p: v["net"] for p, v in candidate.get("pinInfoMap", {}).items()}
            if pins != pads:
                errors.append(f"PCB {ref}: exported pin/net map differs from schematic")
    print(json.dumps({
        "passed": not errors, "components": len(components), "schematic_pin_checks": checks,
        "pcb_pad_checks": pcb_checks, "errors": errors,
        "pcb_association_checks": association_checks,
        "scope": "Assigned pin nets, selected E6 capacitors and optional PCB associations; not DRC, routing quality, RF, power or physical validation.",
    }, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
