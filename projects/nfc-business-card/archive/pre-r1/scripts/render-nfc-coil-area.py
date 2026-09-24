#!/usr/bin/env python3
"""Render the current NFC winding and the larger E19 candidate."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

PROJECT = Path(__file__).resolve().parents[1]
CURRENT = PROJECT / "hardware/e16-nfc-coil-plan.json"
EXPANDED = PROJECT / "hardware/nfc-expanded-five-turn-study.json"
OUTPUT = PROJECT / "enclosure/renders/nfc-coil-area-comparison.png"


def render(ax, plan, title, color):
    ax.add_patch(Rectangle((60, 24), 22, 26, color="#e7f2f8", zorder=0))
    ax.add_patch(Rectangle((60, 24), 22, 26, fill=False, edgecolor="#7ea9bf", linewidth=1.5))
    ax.add_patch(Rectangle((76.704, 10.224), 6.5, 11.551, color="#60656a", zorder=1))
    ax.plot([76.704, 83.204], [26.775, 26.775], color="#b04a42", linestyle=":", linewidth=1.5)
    for index, track in enumerate(plan["tracks"][:4]):
        points = track["points"]
        ax.plot([point[0] for point in points], [point[1] for point in points],
                color=color if index != 2 else "#d28b2e", linewidth=2.1,
                linestyle="--" if index == 2 else "-", solid_capstyle="round")
    for x in (66.5, 73.0):
        ax.add_patch(Rectangle((x - 0.8, 22.2), 1.6, 0.8,
                               facecolor="#34495e", edgecolor="white", linewidth=0.7))
    ax.text(77.5, 19.5, "USB metal", color="white", fontsize=9, rotation=90)
    ax.text(60.2, 50.5, "NFC reserve 22 × 26 mm", color="#4e7489", fontsize=9)
    ax.set(xlim=(57.5, 84.5), ylim=(18, 52), title=title, xlabel="Board X (mm)", ylabel="Board Y (mm)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.15)


def main():
    current = json.loads(CURRENT.read_text())
    expanded = json.loads(EXPANDED.read_text())
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 7.2), sharey=True, constrained_layout=True)
    render(axes[0], current, "E18 current · 6 turns · 10.4 × 21.3 mm", "#2d639a")
    render(axes[1], expanded, "E19 candidate · 5 turns · 20.2 × 21.3 mm", "#207a62")
    fig.suptitle("NFC coil area comparison — geometry only, RF performance unmeasured", fontsize=12)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=160)
    fig.savefig(OUTPUT.with_suffix(".svg"))
    print(OUTPUT)


if __name__ == "__main__":
    main()
