"""Render the E16 enclosure STLs to a shaded isometric PNG (no GUI needed)."""
import math, struct
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path('/Users/linguanguo/dev/hardware-lab/projects/nfc-business-card/enclosure')
OUT = Path('/Users/linguanguo/dev/hardware-lab/projects/nfc-business-card/artifacts/e16-cad-preview')
OUT.mkdir(parents=True, exist_ok=True)


def read_stl(path):
    data = path.read_bytes()
    tris = []
    if data[:5] == b'solid' and b'facet' in data[:200]:
        # ascii stl
        verts = []
        for line in data.decode('ascii', 'ignore').splitlines():
            line = line.strip()
            if line.startswith('vertex'):
                verts.append(tuple(float(v) for v in line.split()[1:4]))
                if len(verts) == 3:
                    tris.append(tuple(verts)); verts = []
    else:
        count = struct.unpack('<I', data[80:84])[0]
        off = 84
        for _ in range(count):
            vals = struct.unpack('<12fH', data[off:off+50])
            off += 50
            tris.append(((vals[3], vals[4], vals[5]), (vals[6], vals[7], vals[8]), (vals[9], vals[10], vals[11])))
    return tris


def project(p, scale, ox, oy):
    x, y, z = p
    # isometric-ish: 30 degrees around Z, 25 degrees elevation
    a, e = math.radians(35), math.radians(28)
    xr = x*math.cos(a) - y*math.sin(a)
    yr = x*math.sin(a) + y*math.cos(a)
    sx = xr
    sy = yr*math.sin(e) - z*math.cos(e)
    return (ox + sx*scale, oy + sy*scale)


def render(path, color, draw_on, scale, ox, oy, center=False):
    tris = read_stl(path)
    if center:
        xs = [p[i] for t in tris for p in t for i in (0,)]
        ys = [p[1] for t in tris for p in t]
        zs = [p[2] for t in tris for p in t]
        cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
        tris = [tuple((p[0] - cx, p[1] - cy, p[2] - cz) for p in t) for t in tris]
    shade = []
    for t in tris:
        (x1,y1,z1),(x2,y2,z2),(x3,y3,z3) = t
        ux, uy, uz = x2-x1, y2-y1, z2-z1
        vx, vy, vz = x3-x1, y3-y1, z3-z1
        nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        n = math.sqrt(nx*nx+ny*ny+nz*nz) or 1
        lum = max(0.25, min(1.0, 0.45 + 0.55*abs(nz/n)))
        depth = (z1+z2+z3)/3
        shade.append((depth, lum, t))
    shade.sort(key=lambda s: s[0])
    for depth, lum, t in shade:
        pts = [project(p, scale, ox, oy) for p in t]
        c = tuple(int(ch*lum) for ch in color)
        draw_on.polygon(pts, fill=c)


img = Image.new('RGB', (1500, 700), 'white')
d = ImageDraw.Draw(img)
render(BASE/'nfc-card-e16-bottom-v5.stl', (120, 150, 185), d, 6.2, 400, 300)
render(BASE/'nfc-card-e16-top-v5.stl', (150, 178, 210), d, 6.2, 1010, 300)
render(BASE/'nfc-card-e16-keycaps-v5.stl', (240, 186, 150), d, 26.0, 780, 545, center=True)
d.text((40, 30), 'E16 enclosure V5 - bottom, top and key caps, shaded isometric from STL', fill=(30, 45, 65))
d.text((40, 55), 'outer 84 x 52 x 4.5, L-shaped PCB with the 33.5 x 15 battery bite', fill=(80, 95, 115))
d.text((40, 78), 'top: screen window + two key holes; caps ride flush in the holes and press the SKQGABE010 stems', fill=(80, 95, 115))
d.text((520, 660), 'key caps x2 (scale 26x): 4.2 mm puck riding in the 4.6 mm hole, 1.45 mm tall', fill=(150, 110, 80))
img.save(OUT/'e16-enclosure-v5-iso.png')
print('saved', OUT/'e16-enclosure-v5-iso.png')


def render_top(path, color, draw_on, scale, ox, oy):
    """Orthographic top view: x to the right, y up the image, shaded by normal z."""
    tris = read_stl(path)
    shade = []
    for t in tris:
        (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = t
        ux, uy, uz = x2 - x1, y2 - y1, z2 - z1
        vx, vy, vz = x3 - x1, y3 - y1, z3 - z1
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
        lum = max(0.3, min(1.0, 0.5 + 0.5 * abs(nz / n)))
        shade.append(((z1 + z2 + z3) / 3, lum, t))
    shade.sort(key=lambda s: s[0])
    for _, lum, t in shade:
        pts = [(ox + p[0] * scale, oy - p[1] * scale) for p in t]
        draw_on.polygon(pts, fill=tuple(int(ch * lum) for ch in color))


top = Image.new('RGB', (1500, 620), 'white')
td = ImageDraw.Draw(top)
SCALE, TOX, TOY = 9.6, 250, 598.0
render_top(BASE / 'nfc-card-e16-top-v5.stl', (150, 178, 210), td, SCALE, TOX, TOY)


def tpt(x, y):
    return (TOX + x * SCALE, TOY - y * SCALE)


def trect(x0, y0, x1, y1):
    return [tpt(x0, y1), tpt(x1, y0)]


td.rectangle(trect(0, 0, 84, 52), outline=(120, 135, 155), width=2)
td.rectangle(trect(0, 0, 33.5, 15), outline=(150, 162, 178))
td.text(tpt(4, 1.2), 'battery pocket 33.5 x 15 (closed floor + ceiling)', fill=(110, 125, 145))
td.rectangle(trect(4.0, 20.3, 31.8, 48.1), outline=(20, 110, 100), width=2)
td.text(tpt(5.5, 24.0), 'screen window 27.8 x 27.8', fill=(20, 110, 100))
for label, y in [('KEY 1 (flush cap)', 3.3), ('KEY 2 (flush cap)', 15.1)]:
    cx, cy = tpt(38.1, y)
    td.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=(217, 119, 6), width=2)
    td.text((cx + 26, cy - 6), f'{label}  y={y:.1f}', fill=(180, 90, 0))
td.text((40, 30), 'E16 enclosure V5 - top shell seen from the front face (orthographic)', fill=(30, 45, 65))
td.text((40, 55), 'two key holes on x = 38.1 at y = 3.3 / 15.1 mm, flush printed caps; screen window x 4.0-31.8, y 20.3-48.1', fill=(80, 95, 115))
td.text((40, 78), 'the battery bite is a closed pocket: 0.4 mm printed floor below, 0.5 mm ceiling above', fill=(80, 95, 115))
top.save(OUT / 'e16-enclosure-v5-top.png')
print('saved', OUT / 'e16-enclosure-v5-top.png')
