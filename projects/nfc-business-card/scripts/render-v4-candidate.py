#!/usr/bin/env python3
"""Render native pads, copper, filled ground and unchanged assembly courtyards."""
import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely import affinity
from shapely.geometry import box

from kicad_sexpr import child, children, prop
from v4_geometry import geometry, filled_ground

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('board', type=Path)
ap.add_argument('output', type=Path)
ap.add_argument('--limits', nargs=4, type=float, default=[149, 80, 194, 130])
a = ap.parse_args()
b, pads, objects, refs = geometry(a.board)
fig, axs = plt.subplots(1, 2, figsize=(18, 12), constrained_layout=True)
for ax, layer in zip(axs, ['F.Cu', 'B.Cu']):
    ground = filled_ground(b, layer)
    for g in getattr(ground, 'geoms', [ground]):
        if g.is_empty:
            continue
        ax.add_patch(Patch(g.exterior.coords, facecolor='#deecdf', edgecolor='none'))
        for ring in g.interiors:
            ax.add_patch(Patch(ring.coords, facecolor='white', edgecolor='none'))
    for obj in objects:
        if layer not in obj['layers']:
            continue
        g = obj['shape']
        col = '#737f86' if obj['kind'] == 'pad' else ('#bd5350' if layer == 'F.Cu' else '#466fbd')
        if obj['kind'] == 'keepout':
            col = '#d09ac1'
        ax.add_patch(Patch(g.exterior.coords, facecolor=col, alpha=.6 if obj['kind'] == 'keepout' else .9, edgecolor='none'))
    for f in children(b, 'footprint'):
        ref = prop(f, 'Reference')[2]
        x, y, angle = refs[ref]
        for c in children(f, 'fp_rect'):
            if not child(c, 'layer') or child(c, 'layer')[1] != 'F.CrtYd':
                continue
            p, q = [list(map(float, child(c, k)[1:3])) for k in ['start', 'end']]
            g = affinity.translate(affinity.rotate(box(*p, *q), -angle, origin=(0, 0)), x, y)
            ax.plot(*g.exterior.xy, color='#b68454', lw=.55, ls='--')
        ax.text(x, y, ref, ha='center', va='center', fontsize=6, color='#142c46', clip_on=True, bbox={'facecolor':'white','alpha':.75,'edgecolor':'none','pad':.2})
    x0, y0, x1, y1 = a.limits
    ax.set(xlim=(x0, x1), ylim=(y1, y0), aspect='equal', title=f'{a.board.parent.name} / {layer} (top view)', xlabel='KiCad x / mm', ylabel='KiCad y / mm')
    ax.grid(alpha=.15)
a.output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(a.output, dpi=170)
