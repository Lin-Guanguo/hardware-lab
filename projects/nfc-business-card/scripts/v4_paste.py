"""Preserve exact D paste openings, including asymmetric notched polygons."""
import math
import uuid

from gerber_geometry import flashes, positive_regions
from kicad_sexpr import Quoted as Q, child, children, prop


def rebuild_paste(board, reference, directory):
    targets = {str(prop(f, 'Reference')[2]): f for f in children(board, 'footprint')}
    candidates = []
    for f in children(reference, 'footprint'):
        ref = str(prop(f, 'Reference')[2])
        at = child(f, 'at')
        x, y = map(float, at[1:3])
        a = math.radians(float(at[3]) if len(at) > 3 else 0)
        for pad in children(f, 'pad'):
            px, py = map(float, child(pad, 'at')[1:3])
            gx, gy = x + px * math.cos(a) + py * math.sin(a), y - px * math.sin(a) + py * math.cos(a)
            side = 'B' if 'B.Cu' in child(pad, 'layers') else 'F'
            candidates.append((ref, str(pad[1]), side, gx - 110, 130 - gy, x, y, a))
    for f in targets.values():
        f[:] = [n for n in f if not (isinstance(n, list) and n[0].startswith('fp_') and child(n, 'layer') and str(child(n, 'layer')[1]).endswith('.Paste'))]
        for p in children(f, 'pad'):
            layers = child(p, 'layers')
            layers[:] = [l for l in layers if not str(l).endswith('.Paste')]
    audit = []
    for side, filename in [('F', 'Gerber_TopPasteMaskLayer.GTP'), ('B', 'Gerber_BottomPasteMaskLayer.GBP')]:
        text = (directory / filename).read_text()
        openings = flashes(text) + positive_regions(text)
        for _, _, g in openings:
            bounds = g.bounds
            center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
            matches = [p for p in candidates if p[2] == side and math.dist(center, p[3:5]) < .15]
            assert len(matches) == 1, ('Ambiguous paste opening', side, center, len(matches))
            ref, pin, _, _, _, x, y, a = matches[0]
            assert not g.interiors, 'Review split/hollow apertures explicitly'
            pts = []
            for px, py in list(g.exterior.coords)[:-1]:
                dx, dy = 110 + px - x, 130 - py - y
                pts.append(['xy', str(round(dx * math.cos(a) - dy * math.sin(a), 6)), str(round(dx * math.sin(a) + dy * math.cos(a), 6))])
            targets[ref].append(['fp_poly', ['pts', *pts], ['stroke', ['width', '0'], ['type', 'solid']], ['fill', 'solid'], ['layer', Q(side + '.Paste')], ['uuid', Q(str(uuid.uuid4()))]])
            audit.append({'ref': ref, 'pin': pin, 'side': side, 'area_mm2': g.area, 'vertices': len(pts), 'source_bbox_center': center})
    assert len({(r['ref'], r['pin'], r['side']) for r in audit}) == len(audit)
    return audit
