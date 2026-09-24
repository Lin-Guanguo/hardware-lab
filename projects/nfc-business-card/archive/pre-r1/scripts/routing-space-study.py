"""Generate a 2-D routing-space study without changing CAD or EasyEDA projects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CARD = (84.0, 52.0)
BOARD = (1.5, 1.5, 82.5, 50.5)
SCREEN = (2.0, 18.5, 37.42, 31.9)
FPC_ROUTE = (39.42, 26.2, 15.48, 16.5)
NFC = (60.0, 24.0, 22.0, 26.0)
# Approximate envelope occupied by the current left-bottom U1 placement and its
# BLE antenna keep-out. It is included only to expose the trade-off: a battery
# starting at x=2 mm requires U1 to move to the right block.
LEFT_MCU_ANTENNA_ZONE = (2.5, 1.5, 23.0, 16.5)

# These are planning envelopes, not manufacturing clearances. They are deliberately
# larger than the bare footprints so the study can reject a cramped floorplan early.
USB_BLOCK = (22.0, 15.0)
USB_PLUS_MCU_BLOCK = (40.0, 16.5)

CANDIDATES = [
    {"name": "301030", "capacity_mAh": 100, "length": 30.0, "width": 10.0, "thickness": 3.0},
    {"name": "301230", "capacity_mAh": 110, "length": 30.0, "width": 12.0, "thickness": 3.0},
    {"name": "301423", "capacity_mAh": 100, "length": 24.0, "width": 14.0, "thickness": 3.0},
    {"name": "301525", "capacity_mAh": 90, "length": 25.0, "width": 15.0, "thickness": 3.0},
]


def overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return max(0.0, min(ax + aw, bx + bw) - max(ax, bx)) * max(
        0.0, min(ay + ah, by + bh) - max(ay, by)
    )


def study() -> dict:
    result = {
        "card_mm": CARD,
        "board_inner_mm": BOARD,
        "fixed_regions": {
            "screen": SCREEN,
            "fpc_route": FPC_ROUTE,
            "nfc": NFC,
            "current_left_mcu_and_ble_keepout": LEFT_MCU_ANTENNA_ZONE,
        },
        "planning_envelopes_mm": {
            "usb_power_block": USB_BLOCK,
            "usb_plus_mcu_and_controls": USB_PLUS_MCU_BLOCK,
            "note": "Planning envelopes only; they must be validated in EasyEDA with the final stack-up and footprints.",
        },
        "candidates": [],
    }
    for candidate in CANDIDATES:
        # Put the battery at the lower-left, below the display. Keep 2 mm from the
        # right edge of its nominal envelope before starting the routing block.
        battery = (2.0, 2.0, candidate["length"], candidate["width"])
        route_x = battery[0] + battery[2] + 2.0
        route_y = 2.0
        route_w = BOARD[2] - route_x
        route_h = 18.5 - route_y
        fixed_overlaps = {
            name: overlap(battery, box)
            for name, box in result["fixed_regions"].items()
        }
        result["candidates"].append(
            {
                **candidate,
                "battery_bbox_mm": battery,
                "right_lower_route_bbox_mm": (route_x, route_y, route_w, route_h),
                "right_lower_route_area_mm2": round(route_w * route_h, 2),
                "fits_usb_power_envelope": route_w >= USB_BLOCK[0] and route_h >= USB_BLOCK[1],
                "fits_usb_plus_mcu_envelope": route_w >= USB_PLUS_MCU_BLOCK[0] and route_h >= USB_PLUS_MCU_BLOCK[1],
                "overlap_with_fixed_regions_mm2": fixed_overlaps,
                "requires_mcu_move_to_right_block": fixed_overlaps["current_left_mcu_and_ble_keepout"] > 0,
            }
        )
    result["conclusion"] = {
        "minimum_height_fixed_by_screen_mm": 16.5,
        "preferred_partition": "screen upper-left, battery lower-left, NFC upper-right, USB/MCU/power lower-right",
        "why": [
            "The screen and its FPC corridor stay unchanged.",
            "The NFC reserve is not consumed by the battery.",
            "A long battery creates a continuous lower-right block instead of the former narrow battery/USB bridge.",
            "The MCU must be placed in the right block only after checking its BLE antenna keep-out and orientation.",
        ],
        "next_gate": "Place the real EasyEDA footprints in the lower-right block and test USB escape before generating a new FreeCAD model.",
    }
    return result


def svg(result: dict) -> str:
    scale = 12.0
    margin = 36
    width = int(CARD[0] * scale + margin * 2)
    row_h = 64
    height = int(len(result["candidates"]) * row_h + 120)

    def rect(box, fill, stroke="#334155", dash=""):
        x, y, w, h = box
        attrs = f'x="{margin + x * scale:.1f}" y="{margin + y * scale:.1f}" width="{w * scale:.1f}" height="{h * scale:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"'
        if dash:
            attrs += f' stroke-dasharray="{dash}"'
        return f"<rect {attrs}/>"

    def label(x, y, text, size=11, fill="#0f172a"):
        return f'<text x="{margin + x * scale:.1f}" y="{margin + y * scale:.1f}" font-size="{size}" fill="{fill}">{text}</text>'

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append('<style>text{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}</style>')
    parts.append('<text x="36" y="24" font-size="16" fill="#0f172a">84 × 52 routing-space study — no CAD/EDA mutation</text>')
    for index, candidate in enumerate(result["candidates"]):
        yoff = index * row_h + 42
        parts.append(f'<g transform="translate(0,{yoff})">')
        parts.append(rect((0, 0, CARD[0], CARD[1]), "#f8fafc", "#475569"))
        # Fixed regions.
        parts.append(rect(SCREEN, "#dbeafe", "#2563eb"))
        parts.append(rect(FPC_ROUTE, "#ede9fe", "#7c3aed", "5 3"))
        parts.append(rect(NFC, "#ccfbf1", "#0f766e", "5 3"))
        parts.append(rect(candidate["battery_bbox_mm"], "#fed7aa", "#c2410c"))
        parts.append(rect(candidate["right_lower_route_bbox_mm"], "#dcfce7", "#15803d", "4 3"))
        parts.append(label(1, -2, f'{candidate["name"]} · {candidate["length"]:.0f} × {candidate["width"]:.0f} × {candidate["thickness"]:.0f} mm · seller capacity {candidate["capacity_mAh"]} mAh', 12))
        parts.append(label(4, 34, "屏幕", 10, "#1d4ed8"))
        parts.append(label(41, 34, "FPC", 9, "#6d28d9"))
        parts.append(label(63, 36, "NFC", 10, "#0f766e"))
        bx, by, bw, bh = candidate["battery_bbox_mm"]
        parts.append(label(bx + 1, by + bh / 2 + 1, "电池", 9, "#9a3412"))
        rx, ry, rw, rh = candidate["right_lower_route_bbox_mm"]
        parts.append(label(rx + 1, ry + 7, f"右下自由区 {rw:.1f} × {rh:.1f}", 9, "#166534"))
        parts.append(label(0, 56, "绿色虚线只是布线规划包络；最终仍需真实封装、天线净空和 DRC 验证", 9, "#475569"))
        parts.append('</g>')
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    result = study()
    (args.output_dir / "routing-space-study.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (args.output_dir / "routing-space-study.svg").write_text(svg(result))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
