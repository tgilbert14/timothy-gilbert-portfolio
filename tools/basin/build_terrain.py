"""Build the terrain files for basin/ (the landscape view).

Downloads public elevation tiles (Mapzen Terrain Tiles on AWS, "terrarium" encoding),
crops a detailed sheet around Tucson and a wide low-detail sheet around it, and writes
lossless WebP heightmaps plus meta.json with the site and label coordinates.

Run from the repo root:
    uv run --with numpy --with pillow python tools/basin/build_terrain.py basin

Tiles are cached in tools/basin/.tiles (git-ignored). Output: height.webp, far.webp, meta.json.
"""
import json
import math
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

TILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
CACHE = Path(__file__).parent / ".tiles"

# detailed sheet: west, south, east, north
INNER = (-111.30, 31.62, -110.45, 32.55)
OUTER = (-112.65, 30.55, -109.15, 33.65)

PLACES = [  # name, lat, lon, search radius in pixels for the true summit (0 = use the point as given)
    ("Mount Lemmon", 32.4430, -110.7885, 10), ("Mount Wrightson", 31.6959, -110.8484, 10),
    ("Mica Mountain", 32.2206, -110.5445, 10), ("Rincon Peak", 32.1195, -110.5215, 10), ("Wasson Peak", 32.2737, -111.1468, 10),
    ("Arizona Stadium", 32.2288, -110.9488, 0), ("SRER", 31.9107, -110.8355, 0), ("Downtown Tucson", 32.2217, -110.9698, 0),
    ("Santa Catalina", 32.40, -110.72, 0), ("Rincon", 32.17, -110.55, 0), ("Santa Rita", 31.76, -110.83, 0),
    ("Tucson Mts", 32.24, -111.14, 0), ("Sierrita", 31.87, -111.17, 0), ("Tortolita", 32.49, -111.07, 0),
]


def fx(lon):
    return (lon + 180) / 360


def fy(lat):
    return (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2


def tile(z, x, y):
    CACHE.mkdir(exist_ok=True)
    p = CACHE / f"{z}-{x}-{y}.png"
    if not p.exists():
        urllib.request.urlretrieve(TILES.format(z=z, x=x, y=y), p)
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def sheet(z, bbox, out_w):
    w, s, e, n = bbox
    size = 2 ** z * 256
    px0, px1 = round(fx(w) * size), round(fx(e) * size)
    py0, py1 = round(fy(n) * size), round(fy(s) * size)
    x0, x1, y0, y1 = px0 // 256, (px1 - 1) // 256, py0 // 256, (py1 - 1) // 256
    mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), dtype=np.float32)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = tile(z, x, y)
    crop = mos[py0 - y0 * 256:py1 - y0 * 256, px0 - x0 * 256:px1 - x0 * 256]
    h, wpx = crop.shape
    out_h = round(h * out_w / wpx)
    a = np.asarray(Image.fromarray(crop, mode="F").resize((out_w, out_h), Image.LANCZOS))
    info = dict(w=out_w, h=out_h, fx0=px0 / size, fx1=px1 / size, fy0=py0 / size, fy1=py1 / size)
    return a, info


def encode(a, info, step, path):
    lo = float(np.floor(a.min()))
    q = np.round((a - lo) / step).astype(np.uint16)
    rgb = np.zeros(q.shape + (3,), dtype=np.uint8)
    rgb[..., 0] = q >> 8
    rgb[..., 1] = q & 255
    Image.fromarray(rgb).save(path, lossless=True, quality=100, method=6)
    info.update(lo=lo, step=step)


def main(out):
    out = Path(out)
    w, s, e, n = INNER
    a, inner = sheet(11, INNER, 1200)
    inner["metersPerPixel"] = 40075016.686 * math.cos(math.radians((n + s) / 2)) * (inner["fx1"] - inner["fx0"]) / inner["w"]
    b, outer = sheet(9, OUTER, 1024)
    points = []
    for name, lat, lon, r in PLACES:
        u = (fx(lon) - inner["fx0"]) / (inner["fx1"] - inner["fx0"])
        v = (fy(lat) - inner["fy0"]) / (inner["fy1"] - inner["fy0"])
        i, j = round(u * inner["w"]), round(v * inner["h"])
        win = a[max(0, j - r):j + r + 1, max(0, i - r):i + r + 1]
        jj, ii = np.unravel_index(win.argmax(), win.shape)
        points.append(dict(name=name, u=u, v=v, elev=float(a[j, i]),
                           peak_u=(max(0, i - r) + ii) / inner["w"], peak_v=(max(0, j - r) + jj) / inner["h"], peak_elev=float(win.max())))
    encode(a, inner, 0.125, out / "height.webp")
    encode(b, outer, 0.5, out / "far.webp")
    (out / "meta.json").write_text(json.dumps(dict(inner=inner, outer=outer, bbox=[w, s, e, n], points=points), indent=1))
    for p in points[:5]:
        print(f'{p["name"]}: {p["peak_elev"]:.0f} m')


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "basin")
