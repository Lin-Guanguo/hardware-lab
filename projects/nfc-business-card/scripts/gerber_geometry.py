"""Read EasyEDA Pro millimetre Gerber flashes; reject unsupported used apertures."""
import re
from shapely.geometry import Point, LineString, Polygon, box


def flashes(text):
    """Read only calibrated pad/via flashes, rejecting unsupported used apertures."""
    assert '%FSLAX26Y26*%' in text and '%MOMM*%' in text
    apertures = {}
    for num, kind, raw in re.findall(r'%ADD(\d+)([A-Za-z]+),([^*]+)\*%', text):
        values = [float(v) for v in raw.split('X')]
        if kind == 'C':
            g = Point(0, 0).buffer(values[0]/2, quad_segs=64)
        elif kind == 'R':
            g = box(-values[0]/2, -values[1]/2, values[0]/2, values[1]/2)
        elif kind == 'O':
            w, h = values
            g = (LineString([(-(w-h)/2, 0), ((w-h)/2, 0)]).buffer(h/2, quad_segs=64)
                 if w >= h else LineString([(0, -(h-w)/2), (0, (h-w)/2)]).buffer(w/2, quad_segs=64))
        elif kind == 'RoundRect':
            radius, x1, y1, x2, y2 = values
            g = Polygon([(x1,y1),(x2,y2),(-x1,-y1),(-x2,-y2)]).convex_hull.buffer(radius/2, quad_segs=64)
        else:
            continue
        apertures[int(num)] = g
    from shapely.affinity import translate
    active = None
    result = []
    for line in text.splitlines():
        select = re.fullmatch(r'G54D(\d+)\*', line)
        if select:
            active = int(select[1])
        flash = re.fullmatch(r'G01X(-?\d+)Y(-?\d+)D03\*', line)
        if flash:
            assert active in apertures, ('Unsupported flash aperture', active)
            x, y = [int(v)/1e6 for v in flash.groups()]
            result.append((x, y, translate(apertures[active], x, y)))
    return result


def positive_regions(text):
    """Read straight, single-contour positive regions used by this stencil export."""
    assert '%FSLAX26Y26*%' in text and '%MOMM*%' in text
    assert '%LPC*%' not in text, 'Clear polarity requires a full compositing parser'
    result = []
    for body in re.findall(r'G36\*\s*(.*?)G37\*', text, re.S):
        commands = [line.strip() for line in body.splitlines() if line.strip()]
        points = []
        for i, command in enumerate(commands):
            match = re.fullmatch(r'G01X(-?\d+)Y(-?\d+)D0([12])\*', command)
            assert match, ('Unsupported region command', command)
            x, y, op = match.groups()
            assert op == ('2' if i == 0 else '1'), 'Multiple contours require compositing'
            points.append((int(x)/1e6, int(y)/1e6))
        assert points[0] == points[-1]
        shape = Polygon(points)
        assert shape.is_valid and shape.area > 0
        result.append((shape.centroid.x, shape.centroid.y, shape))
    return result
