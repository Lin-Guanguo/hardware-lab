#!/usr/bin/env python3
"""Generate a planning overlay from immutable R21 and enclosure evidence."""

import csv
import hashlib
import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon, Rectangle

from pour_geometry import MIL, parse_path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/nfc-business-card"
RECORDS = PROJECT / "hardware/records"
PREFIX = "pcb-restart-plan-2026-09-28"
sources = {
    "project": ROOT / "eda/NFC-Card-R1-Layout-Reset-R21-USB-CC2.eprj2",
    "snapshot": RECORDS / "r1-layout-reset-r21-routed-snapshot.json",
    "pins": RECORDS / "r1-layout-reset-r21-pcb-pins.json",
    "bom": PROJECT / "hardware/production/r1-layout-reset-r21/NFC-Card-R1-Layout-Reset-R21-USB-CC2-bom.csv",
    "enclosure_report": PROJECT / "enclosure/r1-usb-fit-4.8/report.json",
    "u1_overlay": RECORDS / "r1-layout-reset-r21-u1-official-overlay.json",
}
hashes = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in sources.items()}
manufacturing = json.loads((RECORDS / "r1-layout-reset-r21-manufacturing.json").read_text())
for key in ("project", "snapshot", "bom"):
    assert hashes[key] == manufacturing[f"{key}_sha256"], key
snapshot = json.loads(sources["snapshot"].read_text())
pins = json.loads(sources["pins"].read_text())
enclosure = json.loads(sources["enclosure_report"].read_text())
u1 = json.loads(sources["u1_overlay"].read_text())
assert hashes["pins"] == u1["source_sha256"]["r21_pins_sha256"]
with sources["bom"].open(encoding="utf-16") as stream:
    bom = list(csv.DictReader(stream, delimiter="\t"))
refs = {c["ref"] for c in snapshot["components"]}
assert refs == {c["ref"] for c in pins}
assert refs == {ref for row in bom for ref in row["Designator"].split(",")}
assert len(refs) == sum(int(row["Quantity"]) for row in bom) == 66
with sqlite3.connect(f"file:{sources['project']}?mode=ro", uri=True) as db:
    assert db.execute("PRAGMA quick_check").fetchone() == ("ok",)
    project_uuid, project_name = db.execute("SELECT uuid, name FROM projects").fetchone()

components = {c["ref"]: c for c in snapshot["components"]}
outline = next(p for p in snapshot["polylines"] if p["layer"] == 11)
board = parse_path(outline["polygon"]["polygon"], MIL)
board_bounds = [min(p[0] for p in board), min(p[1] for p in board),
                max(p[0] for p in board), max(p[1] for p in board)]
assert abs(board_bounds[2] - board_bounds[0] - 81.8) < .002
assert abs(board_bounds[3] - board_bounds[1] - 49.8) < .002

# These are search windows, not placements, courtyards, or proven free space.
zones = [
    {"id": "A", "label": "主控＋去耦", "bounds_mm": [55, 1.1, 71, 20.5], "color": "#6da7d2"},
    {"id": "B", "label": "充电＋稳压", "bounds_mm": [40.5, 17.5, 58.5, 26], "color": "#e6bc63"},
    {"id": "C", "label": "USB＋保护", "bounds_mm": [70, 20, 82.9, 32], "color": "#d68774"},
    {"id": "D", "label": "屏幕电源", "bounds_mm": [59, 32, 80.5, 46.5], "color": "#83baa0"},
    {"id": "E", "label": "电池采样", "bounds_mm": [73, 7, 81, 18.5], "color": "#b59dce"},
]
fixed = {
    "battery_gauge_xyzwhd_mm": enclosure["battery_reserved_box_mm"],
    "screen_max_xywh_mm": [1.95, 18.25, 37.42, 31.9],
    "screen_source": "enclosure/build-r1-usb-fit.py: screen_max",
    "screen_nfc_exclusion_xyxy_mm": [0, 17, 39.62, 52],
    "keys_xy_mm": {ref: [components[ref][k] * MIL for k in ("x", "y")]
                   for ref in ("SW1", "SW2", "SW3")},
    "j2_reference_xy_mm": [components["J2"][k] * MIL for k in ("x", "y")],
    "usb_axis_y_mm": 26,
    "testpoints_xy_mm": {p["number"]: [p["x"] * MIL, p["y"] * MIL]
                         for p in snapshot["pads"] if p["number"].startswith("TP")},
}
power = []
for load_ma in (100, 160, 200):
    for sys_v in (3.8, 4.5):
        loss = (sys_v - 3.3) * load_ma / 1000
        power.append({"sys_v": sys_v, "load_ma": load_ma, "ldo_loss_w": round(loss, 4),
                      "jedec_temperature_rise_proxy_c": round(loss * 181.9, 2)})
report = {
    "status": "PLANNING_DRAFT_NOT_A_NATIVE_PCB_CANDIDATE",
    "sources": {k: {"path": str(v.relative_to(ROOT)), "sha256": hashes[k]} for k, v in sources.items()},
    "baseline": {"project_uuid": project_uuid, "project_name": project_name,
                 "pcb_uuid": snapshot["document"]["uuid"], "components": len(refs),
                 "pins": sum(len(c["pins"]) for c in pins), "bom_groups": len(bom),
                 "vias": len(snapshot["vias"]), "board_bounds_mm": board_bounds,
                 "sqlite_quick_check": "ok", "live_state_checked": False},
    "retained_mechanical_anchors": fixed,
    "user_reported_battery": {
        "date": "2026-09-28", "received": True, "model": "301030", "thickness_mm": 3,
        "capacity_original_text": "110毫安", "provisional_capacity_mah": 110,
        "capacity_unit_verified": False, "rated_charge_current_ma": None,
        "rated_discharge_current_ma": None, "complete_pack_length_width_mm": None,
    },
    "proposed_search_windows": zones,
    "ldo_sensitivity_cases": power,
    "limits": [
        "R21 electrical source only; no new same-candidate schematic export or pin-map check.",
        "R21 straight outline is contextual; USB mid-mount cutout is deliberately not generated.",
        "Front and back layers use the same top-view projection, not a mirrored rear photograph.",
        "Search windows are proposed allocations, not verified available area or component placements.",
        "Display maximum is an old CAD gauge; FPC insertion, bend and assembly tolerance remain open.",
        "The 4.8 mm enclosure report uses an older USB4500 assembly, not synchronized R21 CAD.",
        "Power cases are sensitivity calculations, not measured current or a thermal qualification.",
    ],
}
(RECORDS / f"{PREFIX}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

font_path = "/System/Library/Fonts/STHeiti Light.ttc"
font_manager.fontManager.addfont(font_path)
font_name = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams.update({"font.family": font_name, "axes.unicode_minus": False, "font.size": 10})
fig, axes = plt.subplots(1, 2, figsize=(15, 6.7), layout="constrained")
for ax in axes:
    ax.add_patch(Rectangle((-.6, -.6), 85.2, 53.2, fc="#f8f8f6", ec="#bec4c6", ls="--"))
    ax.add_patch(Polygon(board, fc="#eef4ef", ec="#324e46", lw=1.5))
    ax.add_patch(Rectangle((1.5, 1.5), 32.5, 14, fc="#f0dfaa", ec="#b69953"))
    ax.text(17.75, 8.5, "电池空腔量规 32.5 × 14 mm\n301030 已到货，厚 3 mm", ha="center", va="center", fontsize=9)
    ax.set(xlim=(-2, 87), ylim=(55, -3), aspect="equal", xlabel="x / mm", ylabel="y / mm")
    ax.grid(alpha=.1)

ax = axes[0]
ax.set_title("正面：第一轮分区搜索范围", loc="left", pad=16, fontweight="bold")
ax.add_patch(Rectangle((1.95, 18.25), 37.42, 31.9, fc="#d4dfe4", ec="#7994a1"))
ax.text(20.66, 34, "屏幕最大尺寸量规\n37.42 × 31.9 mm\nFPC 实物折弯仍待核对", ha="center", va="center")
for zone in zones:
    x0, y0, x1, y1 = zone["bounds_mm"]
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fc=zone["color"], ec=zone["color"], alpha=.5))
    label = f"{zone['id']}\n{zone['label']}" if zone["id"] != "E" else "E\n电池\n采样"
    ax.text((x0+x1)/2, (y0+y1)/2, label, ha="center", va="center", fontsize=9)
for ref, (x, y) in fixed["keys_xy_mm"].items():
    ax.add_patch(Circle((x, y), 3.4, fill=False, ec="#49545a"))
    ax.text(x, y, ref, fontsize=8, ha="center", va="center")
x, y = fixed["j2_reference_xy_mm"]
ax.plot([x, x], [26.96, 41.56], color="#374955", lw=5)
ax.text(x-1.2, y, "J2 现有基准", rotation=90, ha="right", va="center", fontsize=8)
ax.plot([83, 86], [26, 26], color="#b15b47", lw=2)
ax.text(86.3, 26, "USB\ny=26", va="center", fontsize=8)
ax.annotate("USB 信号预留通道", xy=(63, 23.7), xytext=(60.5, 29), fontsize=8,
            ha="center", arrowprops={"arrowstyle": "->", "color": "#677781"})
ax.plot([70, 63, 58.4], [23.7, 23.7, 20.5], color="#677781", ls="--", lw=1.5)

ax = axes[1]
ax.set_title("背面层：同一俯视投影（未镜像）", loc="left", pad=16, fontweight="bold")
ax.add_patch(Rectangle((0, 17), 39.62, 35, fc="#edf2f6", ec="#859bb1", ls="--"))
for line in snapshot["lines"]:
    if line["net"] == "NFC1_TBD" and line["layer"] == 2:
        ax.plot([line["x1"] * MIL, line["x2"] * MIL],
                [line["y1"] * MIL, line["y2"] * MIL], color="#a47837", lw=.65)
ax.text(20, 34, "保留 NFC 线圈／左侧净空\n电池引线仅沿已记录通道\n线圈调谐留样板验证", ha="center", va="center", fontsize=9)
for bounds in (u1["official_main_keepout_bounds_mm"], u1["official_top_extra_keepout_bounds_mm"]):
    x0, y0, x1, y1 = bounds
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fc="#e8d5d8", ec="#a36475", hatch="//"))
ax.text(63, 9, "旧 BLE 净空仅作对照\n随新 U1 位置重新推导", ha="center", va="center", fontsize=8)
for ref, (x, y) in fixed["testpoints_xy_mm"].items():
    ax.add_patch(Circle((x, y), .6, fc="#c49b47"))
ax.text(71, 45.5, "五点 SWD／NRESET\n触点和外壳孔先保留", ha="center", va="center", fontsize=9)
ax.text(61, 29, "底面优先保障连续回流\n局部换层后核地连接\n不以过孔数单独评判", ha="center", va="center", color="#536d63")

fig.suptitle("0.8 mm 中沉 PCB：先分区、试关键通道，再完成整板", fontsize=17, fontweight="bold")
fig.supxlabel("彩色框是待试摆的空间分配；未生成 USB 缺口、器件新坐标或工艺边。图中板框来自 R21，不能用于制造。", fontsize=10)
fig.savefig(RECORDS / f"{PREFIX}.png", dpi=180)
plt.close(fig)
assert all(hashlib.sha256(path.read_bytes()).hexdigest() == hashes[key] for key, path in sources.items())
print(json.dumps({"status": report["status"], "baseline": report["baseline"], "outputs": [f"{PREFIX}.json", f"{PREFIX}.png"]}, ensure_ascii=False))
