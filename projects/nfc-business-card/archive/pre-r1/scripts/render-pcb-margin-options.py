#!/usr/bin/env python3
"""Render the current E19 placement and an un-routed margin concept."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon, Rectangle

OUT = Path(__file__).resolve().parents[1] / "enclosure/renders/pcb-margin-options.png"
BOARD = [
    (33.5, 0), (33.5, 15), (0, 15), (0, 52), (84, 52),
    (84, 20.62), (76.704, 20.62), (76.704, 11.38),
    (84, 11.38), (84, 0),
]


def box(ax, x, y, w, h, color, label, edge=None, linestyle="-", alpha=0.7):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=edge or color,
                           linewidth=1.6, linestyle=linestyle, alpha=alpha))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)


def panel(ax, concept):
    ax.add_patch(Polygon(BOARD, closed=True, facecolor="#f4f6f8",
                         edgecolor="#263445", linewidth=2))
    box(ax, 2, 18.3, 37.32, 31.8, "#b9d5e8", "屏幕", alpha=0.45)
    box(ax, 0, 0, 33.5, 15, "#e0e5e9", "电池袋\n（PCB 挖空）", alpha=0.6)
    box(ax, 43.7, 6.2, 5.2, 5.2, "#b4a6ca", "SW2", alpha=0.5)
    box(ax, 76.704, 10.224, 6.5, 11.551, "#e89090", "J1", alpha=0.65)
    if concept:
        box(ax, 57.7, 0.2, 10.6, 15.6, "#80b4d2", "U1 左移 2 mm", alpha=0.65)
        ax.add_patch(Rectangle((57.7, 0.2), 2, 15.6, facecolor="none",
                               edgecolor="#cc7325", linewidth=1.5, hatch="////"))
        box(ax, 60.6, 27.6, 18, 21.3, "#f5d171", "线圈 18 × 21.3\n圈间 0.25", alpha=0.7)
        ax.set_title("余量概念：尚未重布线或测 RF", fontsize=13, pad=12)
        ax.text(40, -5.5, "左移需要复核焊盘与天线禁布区；本体投影内有走线不代表放不下",
                ha="center", fontsize=10, color="#85361f")
    else:
        box(ax, 59.7, 0.2, 10.6, 15.6, "#80b4d2", "U1 现位", alpha=0.75)
        box(ax, 60.6, 27.6, 20.2, 21.3, "#f5d171", "E19 线圈 20.2 × 21.3\n圈间 0.15", alpha=0.75)
        ax.set_title("当前 E19：名义几何", fontsize=13, pad=12)
        ax.text(40, -5.5, "J1 铜到槽边约 0.20 mm；实体到 V7 上壳最小距离约 0.34 mm",
                ha="center", fontsize=10, color="#85361f")
    ax.set_xlim(-3, 87)
    ax.set_ylim(-8, 55)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, 85, 10))
    ax.set_yticks(range(0, 53, 10))
    ax.grid(alpha=0.15)
    ax.set_xlabel("x / mm")
    ax.set_ylabel("y / mm")


def main():
    font_manager.fontManager.addfont("/System/Library/Fonts/Hiragino Sans GB.ttc")
    plt.rcParams["font.family"] = "Hiragino Sans GB"
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), layout="constrained")
    panel(axes[0], False)
    panel(axes[1], True)
    fig.savefig(OUT, dpi=180, facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
