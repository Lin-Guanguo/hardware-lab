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


def render(path, color, draw_on, scale, ox, oy):
    tris = read_stl(path)
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


img = Image.new('RGB', (1500, 620), 'white')
d = ImageDraw.Draw(img)
render(BASE/'nfc-card-e16-bottom-v3.stl', (120, 150, 185), d, 6.2, 400, 300)
render(BASE/'nfc-card-e16-top-v3.stl', (150, 178, 210), d, 6.2, 1010, 300)
d.text((40, 30), 'E16 enclosure V3 - bottom (left) and top (right), shaded isometric from STL', fill=(30, 45, 65))
d.text((40, 55), 'outer 84 x 52 x 4.5, L-shaped PCB with the 33.5 x 15 battery bite', fill=(80, 95, 115))
d.text((40, 78), 'top: screen window + three key holes; the bite is open so the cell rests on the bottom plate', fill=(80, 95, 115))
img.save(OUT/'e16-enclosure-v3-iso.png')
print('saved', OUT/'e16-enclosure-v3-iso.png')
