#!/usr/bin/env python3
"""Reproduce C manufacturing measurements and conditional power calculations."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from shapely.geometry import Point
from gerber_geometry import flashes

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / 'hardware/records'
source = RECORDS / 'usb-power-return-c-snapshot.json'
s = json.loads(source.read_text())
pads = {(c['ref'], p['number']): p for c in s['components'] for p in s['pads'] if p['id'].startswith(c['id'])}
spec = importlib.util.spec_from_file_location('copper', Path(__file__).with_name('check-r1-copper.py'))
copper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(copper)
from zipfile import ZipFile
with ZipFile(RECORDS / 'usb-power-return-c-diagnostic-gerber.zip') as z:
    files = {Path(n).name: z.read(n).decode('utf-8') for n in z.namelist() if n.endswith(('.GTL', '.GTS', '.GTP'))}
gerber = {k: flashes(files[f]) for k, f in [('copper', 'Gerber_TopLayer.GTL'), ('mask', 'Gerber_TopSolderMaskLayer.GTS'), ('paste', 'Gerber_TopPasteMaskLayer.GTP')]}
manufacturing = {}
for ref in ['J2', 'U1', 'U2', 'U3', 'U4']:
    groups = {k: [] for k in gerber}
    for (r, n), p in pads.items():
        if r != ref:
            continue
        xy = (p['x'] * .0254, p['y'] * .0254)
        for kind, shapes in gerber.items():
            matches = [g for x, y, g in shapes if math.dist((x, y), xy) < .002]
            assert len(matches) == 1, (ref, n, kind)
            if kind == 'copper':
                assert max(abs(a-b) for a, b in zip(matches[0].bounds, copper.pad_shape(p).bounds)) < .002
            groups[kind].append((n, matches[0]))
    measurement = {}
    for kind, shapes in groups.items():
        gap, a, b = min((a[1].distance(b[1]), a[0], b[0]) for i, a in enumerate(shapes) for b in shapes[i+1:])
        measurement[kind] = {'apertures': len(shapes), 'minimum_gap_mm': gap, 'pad_pair': [a, b]}
    if ref == 'U2':
        ep = {k: next(g for n, g in v if n == '11') for k, v in groups.items()}
        measurement['exposed_pad'] = {'copper_bounds_mm': ep['copper'].bounds, 'paste_bounds_mm': ep['paste'].bounds, 'paste_area_ratio': ep['paste'].area / ep['copper'].area, 'ti_example_mm': [.85, 1.38], 'ti_example_stencil_mm': .125, 'ti_example_coverage_percent': 88}
    manufacturing[ref] = measurement
nfc = []
shapes, _ = copper.copper(s)
for v in s['vias']:
    if v['net'] != 'NFC1_TBD' or v['diameterMil'] * .0254 > .59:
        continue
    xy = (v['x'] * .0254, v['y'] * .0254)
    hole = Point(xy).buffer(v['holeMil'] * .0254 / 2)
    gap, ref, num = min((hole.distance(copper.pad_shape(p)), r, n) for (r, n), p in pads.items() if p['layer'] in (1, 2))
    foreign_gap = min(Point(xy).buffer(.3).distance(g) for (net, layer), items in shapes.items() if net != v['net'] for g in items)
    nfc.append({'xy_mm': xy, 'outer_mm': v['diameterMil']*.0254, 'drill_mm': v['holeMil']*.0254, 'hole_to_smt_mm': gap, 'nearest_pad': f'{ref}.{num}', 'outer_0p6_foreign_gap_mm': foreign_gap})
# All scenario currents below are sensitivity inputs, not measured load maxima.
scenarios = []
for screen_ma in [50, 100, 150, 200]:
    load = (screen_ma + 25)/1000
    modes = []
    for sys in [3.8, 4.5]:
        charge = .055
        u2 = (5-sys)*(load+charge) + (sys-3.3)*charge
        u3 = (sys-3.3)*load
        modes.append({'sys_v': sys, 'u2_w': u2, 'u3_w': u3, 'sum_w': u2+u3, 'input_ma_without_iq_or_usb_phy': (load+charge)*1000})
    scenarios.append({'screen_ma_assumed': screen_ma, 'mcu_other_ma_assumed': 25, 'rail_ma': load*1000, 'margin_to_200ma': 200-load*1000, 'margin_to_160ma_goal': 160-load*1000, 'battery_c_rate_at_110mah': load/.110, 'battery_fet_drop_mv_at_0p14ohm': load*.14*1000, 'usb_5v_battery_3p3v_charge_55ma_assumed': modes})
# 20 C bulk-copper estimate; connector, ground, cable and temperature omitted.
rho, thickness, plating = 1.724e-5, .035, .020
r_via = rho*.8/(math.pi*.3*plating)
def series(points, width):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))*rho/(width*thickness)
common = series([[76.1492,23.5991],[75.25,23.5991],[74.6,22.9491],[74.6,21.1]],.3)
u1_r = common + series([[74.6,21.1],[73.15,19.65],[60,19.65]],.6) + series([[60,19.65],[60,17.2999],[58.9001,17.2999],[59.0017,17.1983],[59.0017,16.0655]],.3)
u2_r = common + series([[74.6,21.1],[73.15,19.65],[58.1,19.65],[57.755,19.305],[51,19.305]],.6) + series([[51,19.305],[49.5,17.7],[45.1,17.7],[44.7,17.6]],.6) + series([[44.7,17.6],[44.9,17.5006],[44.671,17.5006]],.4) + series([[44.671,17.5006],[44.671,18.5039]],.2) + 2*r_via
# Named pin straight-line distances are placement clues, not routed lengths.
named = [('C9.1','U4.1'),('C10.1','U4.6'),('C10.1','L1.1'),('L1.2','Q1.3'),('Q1.2','R15.1'),('Q1.1','J2.2'),('R15.1','J2.3'),('C14.1','J2.4'),('C22.1','J2.24')]
def xy(label):
    p = pads[tuple(label.split('.'))]
    return (p['x']*.0254, p['y']*.0254)
result = {'baseline': 'USB-Power-Return-C; READ_ONLY_PREPARATION', 'snapshot_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'manufacturing': manufacturing, 'nfc_vias': nfc, 'power_sensitivity_not_ratings': scenarios, 'c_vbus_copper_estimate': {'rho_ohm_mm': rho, 'thickness_mm_assumed': thickness, 'via_plating_mm_assumed': plating, 'u1_path_ohm': u1_r, 'u2_path_ohm': u2_r, 'u2_drop_mv_at_0p3a': u2_r*.3*1000, 'u2_trace_loss_w_at_0p3a': u2_r*.3**2, 'limits': 'Single chosen upper VBUS path, excludes connector/cable/return/temperature; not ampacity or a complete load-flow solution.'}, 'display_named_pin_distances_mm': [{'from': a, 'to': b, 'distance': math.dist(xy(a),xy(b))} for a,b in named], 'limits': ['No power measurement.', 'No complete 3D fit or FPC bend verification.', 'C mask and paste counts do not approve stencil process.', 'NFC feed via expansion needs same-net solderability review and rerouting.']}
(RECORDS/'board-preparation-c.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
