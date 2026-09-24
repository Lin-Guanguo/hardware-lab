import copy
import hashlib
import json
from itertools import combinations
from pathlib import Path

root = Path(__file__).resolve().parent
project = root.parents[1]
base = json.loads((project / 'hardware/pcb-bottom-usb.json').read_text())['plan']
geometry = json.loads((project / 'artifacts/bottom-usb/pad-geometry.json').read_text())


def overlap(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 1e-5 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-5


def inside(x, y, polygon):
    result = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        if abs((bx-ax)*(y-ay)-(by-ay)*(x-ax)) < 1e-5 and min(ax,bx)-1e-5 <= x <= max(ax,bx)+1e-5 and min(ay,by)-1e-5 <= y <= max(ay,by)+1e-5:
            return True
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            result = not result
    return result


result = {'status': 'OFFLINE_COMPARISON_EDA_UNCHANGED', 'variants': {},
          'limits': 'Pad and body bounding boxes from the 27-component Bottom-USB snapshot. No new EDA DRC, routing, true courtyard, mask, slot clearance, RF, bend or manufacturing validation.'}
for size, delta in [('84x52', 2), ('83x51', 3)]:
    report = json.loads((root / f'{size}-final/pcba-layout-report.json').read_text())
    boxes = {r['name']: r for r in report['components']}
    plan = copy.deepcopy(base)
    plan.pop('project_uuid'); plan.pop('pcb_uuid'); plan.pop('changed_placements_mm_deg')
    plan['card_mm'] = report['card_mm']
    for ref in ('SW1', 'SW2', 'SW3'):
        plan['placements'][ref][0] -= delta
    plan['board_outline_mm'] = [[1.5,1.5],[27.38,1.5],[27.38,7.3],[36.62,7.3],[36.62,1.5],
                                 [51.5-delta,1.5],[51.5-delta,22.5],[84.5-delta,22.5],
                                 [84.5-delta,52.5-delta],[1.5,52.5-delta]]
    for key, name in [('battery_mm', 'BatteryTarget'), ('nfc_reserve_mm', 'NfcReserve')]:
        row = boxes[name]
        plan[key] = row['position_mm'][:2] + row['size_mm'][:2]
    transformed = copy.deepcopy(geometry)
    for kind in ('pads', 'bodies'):
        for item in transformed[kind]:
            if item['ref'].startswith('SW'):
                item['bounds_mm'][0] -= delta
                item['bounds_mm'][2] -= delta
                for corner in item.get('corners', []):
                    corner[0] -= delta
    pads, bodies = transformed['pads'], transformed['bodies']
    x,y,w,h = plan['nfc_reserve_mm']; nfc = [x,y,x+w,y+h]
    outside = [f"{p['ref']}:{p['pin']}" for p in pads if not all(inside(x,y,plan['board_outline_mm']) for x,y in p['corners'])]
    pad_hits = [(p['ref'],q['ref']) for p,q in combinations(pads,2) if p['ref'] != q['ref'] and overlap(p['bounds_mm'],q['bounds_mm'])]
    body_hits = [(p['ref'],q['ref']) for p,q in combinations(bodies,2) if p['ref'] != q['ref'] and overlap(p['bounds_mm'],q['bounds_mm'])]
    nfc_hits = [p['ref'] for p in pads + bodies if overlap(p['bounds_mm'],nfc)]
    board_min_clearance = (51.5-delta) - max(p['bounds_mm'][2] for p in pads if p['ref'].startswith('SW'))
    check = {'component_count': len(plan['placements']), 'pad_count': len(pads),
             'pad_corners_outside_board': outside, 'inter_component_pad_bbox_overlaps': pad_hits,
             'component_body_bbox_overlaps': body_hits, 'pad_or_body_overlaps_nfc_reserve': nfc_hits,
             'button_pad_bbox_to_battery_cut_mm': round(board_min_clearance, 4)}
    assert not any([outside,pad_hits,body_hits,nfc_hits]), check
    (root / f'{size}-pad-geometry.json').write_text(json.dumps(transformed,indent=2)+'\n')
    result['variants'][size] = {'plan': plan, 'footprint_check': check,
                              'freecad_geometry': json.loads((root/f'{size}-final/geometry-check.json').read_text()),
                              'comparison': report['card_envelope_comparison']}
originals = json.loads((root/'original-hashes.json').read_text())
changed = [name for name,value in originals.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest() != value]
assert not changed, changed
result['original_files_unchanged'] = list(originals)
(root/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for name, data in result['variants'].items():
    print(name, json.dumps(data['footprint_check']))
print('Original CAD and EDA hashes unchanged:',len(originals))
