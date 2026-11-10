"""Build the trail and city files for basin/ (the landscape view) from OpenStreetMap.

Reads basin/meta.json and basin/height.webp (made by build_terrain.py), queries the public
Overpass API for trails, main roads, buildings and rail, and writes:
    basin/trails.json   the Arizona Trail, The Loop and a chosen list of named trails
    basin/city.json     main roads, tall or large buildings, rail and the streetcar

Run from the repo root, after build_terrain.py:
    uv run --with numpy --with pillow python tools/basin/build_places.py basin

Responses are cached in tools/basin/.osm (git-ignored). Data (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

CACHE = Path(__file__).parent / ".osm"
HOSTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
         "https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
BB = "31.62,-111.30,32.55,-110.45"          # the detailed sheet
CITY = "32.200,-111.010,32.250,-110.930"    # downtown, the university, A Mountain
QUERIES = {
    "routes": f'[out:json][timeout:120];relation["route"~"hiking|foot|bicycle"]({BB});out geom;',
    "paths": f'[out:json][timeout:180];way["highway"~"path|footway|track|cycleway"]["name"]({BB});out geom;',
    "extras": f'[out:json][timeout:120];way["highway"]["name"~"Tumamoc Hill|Sentinel Peak"]({CITY});out geom;',
    "roads": f'[out:json][timeout:180];way["highway"~"^(motorway|trunk|primary|secondary)$"]({BB});out geom;',
    "buildings": f'[out:json][timeout:180];(way["building"]({CITY});relation["building"]({CITY}););out geom;',
    "rail": f'[out:json][timeout:120];(way["railway"~"rail|tram"]({CITY});relation["route"="tram"]({CITY}););out geom;',
    "streets": f'[out:json][timeout:180];way["highway"~"^(tertiary|residential|unclassified|living_street)$"]({CITY});out geom;',
    "green": f'[out:json][timeout:180];(way["leisure"~"^(park|pitch|golf_course|garden)$"]({CITY});way["landuse"~"^(grass|cemetery|recreation_ground)$"]({CITY});relation["leisure"~"^(park|golf_course)$"]({CITY}););out geom;',
    "water": f'[out:json][timeout:120];way["waterway"~"^(river|stream)$"]({BB});out geom;',
}

# name shown on the map, pattern matched against OpenStreetMap way names
TRAILS = [
    ("Old Baldy Trail", r"^Old Baldy Trail|^Super Trail/Old Baldy"), ("Super Trail", r"^Super Trail #134"),
    ("Florida Canyon Trail", r"^Florida Canyon Trail"), ("Crest Trail", r"^Crest Trail"),
    ("Finger Rock Trail", r"^Finger Rock Trail"), ("Pima Canyon Trail", r"^Pima Canyon Trail"), ("Pontatoc Trail", r"^Pontatoc Trail"),
    ("Ventana Canyon Trail", r"^Ventana Trail"), ("Esperero Trail", r"^Esperero Trail"), ("Phoneline Trail", r"^Phoneline Trail"),
    ("Blackett's Ridge", r"^Blackett"), ("Sabino Canyon Trail", r"^Sabino Canyon Trail"), ("West Fork Sabino Trail", r"^West Fork Sabino"),
    ("Bear Canyon Trail", r"^Bear Canyon Trail"), ("Romero Canyon Trail", r"^Romero (Trail|Canyon Trail)"),
    ("Mount Lemmon Trail", r"^Mount Lemmon Trail"), ("Wilderness of Rocks", r"^Wilderness of Rocks"), ("Marshall Gulch Trail", r"^Marshall Gulch"),
    ("Aspen Trail", r"^Aspen Trail"), ("Butterfly Trail", r"^Butterfly Trail"), ("Box Camp Trail", r"^Box Camp"),
    ("Samaniego Ridge Trail", r"^Samaniego Ridge"), ("Sutherland Trail", r"^Sutherland Trail"), ("Cañada del Oro Trail", r"^Cañada del Oro #4"),
    ("50-Year Trail", r"^50[- ]Year Trail"), ("Linda Vista Trail", r"^Linda Vista"), ("Bug Springs Trail", r"^Bug Springs Trail"),
    ("Molino Basin Trail", r"^Molino Basin"), ("La Milagrosa", r"^La Milagrosa"), ("Agua Caliente Hill Trail", r"^Agua Caliente Hill"),
    ("Tanque Verde Ridge Trail", r"^Tanque Verde Ridge"), ("Douglas Spring Trail", r"^Douglas Spring"), ("Cactus Forest Trail", r"^Cactus Forest Trail"),
    ("Rincon Peak Trail", r"^Rincon Peak Trail"), ("Miller Creek Trail", r"^Miller Creek Trail"), ("Turkey Creek Trail", r"^Turkey Creek Trail"),
    ("Hugh Norris Trail", r"^Hugh Norris Trail$"), ("King Canyon Trail", r"^King Canyon Trail"), ("Sweetwater Trail", r"^Sweetwater Trail"),
    ("Yetman Trail", r"^Yetman Trail"), ("Starr Pass Trail", r"^Starr Pass Trail"), ("Brown Mountain Trail", r"^Brown Mountain Trail"),
    ("Wild Burro Trail", r"^Wild Burro"), ("Tumamoc Hill", r"^Tumamoc Hill"),
]

# Heights in metres for well-known downtown buildings that carry no height in OpenStreetMap.
# These are estimates from floor counts, not surveyed figures.
HEIGHTS = {
    "TEP Headquarters": 44, "Pima County Superior Court": 40, "Tucson City Hall": 40, "Federal Building": 32,
    "Evo A. DeConcini United States Courthouse": 30, "State of Arizona Governmental Offices": 30, "AC Hotel": 30,
    "Qwest Corporation": 26, "Tucson Convention Center": 18, "Linda Ronstadt Music Hall": 20, "Leo Rich Theater": 14,
    "Pima County Courthouse": 12, "Saint Augustine Cathedral": 16, "The Historic Hotel Congress": 11, "Rialto Building": 12,
    "McKale Memorial Center": 26, "Old Main": 12, "Hotel Tucson City Center, Ascend Hotel Collection": 20, "Ramada Tucson": 12,
}


def fetch(name):
    CACHE.mkdir(exist_ok=True)
    p = CACHE / f"{name}.json"
    if p.exists():
        return json.loads(p.read_text())["elements"]
    wait = 5
    for attempt in range(12):
        host = HOSTS[attempt % len(HOSTS)]
        try:
            req = urllib.request.Request(host, data=urllib.parse.urlencode({"data": QUERIES[name]}).encode(),
                                         headers={"User-Agent": "terrain-build-script/1.0"})
            raw = urllib.request.urlopen(req, timeout=200).read()
            data = json.loads(raw)
            if "elements" in data:
                p.write_bytes(raw)
                return data["elements"]
        except Exception as err:  # busy servers answer with HTML; try the next one
            print(name, "retry", host, str(err)[:70])
        time.sleep(wait)
        wait = min(wait * 2, 60)
    raise SystemExit(f"could not fetch {name}")


def metres(a, b):
    return math.hypot((a[0] - b[0]) * 111_200, (a[1] - b[1]) * 111_200 * math.cos(math.radians(a[0])))


def length(line):
    return sum(metres(a, b) for a, b in zip(line, line[1:]))


def chain(lines):
    """Join ways that share an end point into longer lines."""
    lines = [list(l) for l in lines if len(l) > 1]
    out = []
    while lines:
        cur = lines.pop(0)
        grew = True
        while grew:
            grew = False
            for i, l in enumerate(lines):
                if metres(cur[-1], l[0]) < 12: cur += l[1:]
                elif metres(cur[-1], l[-1]) < 12: cur += l[-2::-1]
                elif metres(cur[0], l[-1]) < 12: cur = l[:-1] + cur
                elif metres(cur[0], l[0]) < 12: cur = l[:0:-1] + cur
                else: continue
                lines.pop(i); grew = True
                break
        out.append(cur)
    return out


def simplify(line, tol):
    """Douglas-Peucker, tolerance in metres."""
    if len(line) < 3:
        return line
    k0 = math.cos(math.radians(line[0][0])) * 111_200
    P = [(p[1] * k0, p[0] * 111_200) for p in line]
    keep = [False] * len(P)
    keep[0] = keep[-1] = True
    stack = [(0, len(P) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = P[a]; bx, by = P[b]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1e-9
        best, at = 0, None
        for i in range(a + 1, b):
            d = abs((P[i][0] - ax) * dy - (P[i][1] - ay) * dx) / n
            if d > best: best, at = d, i
        if at is not None and best > tol:
            keep[at] = True
            stack += [(a, at), (at, b)]
    return [p for p, k in zip(line, keep) if k]


def main(out):
    out = Path(out)
    meta = json.loads((out / "meta.json").read_text())
    inner = meta["inner"]
    w, s, e, n = meta["bbox"]
    img = np.asarray(Image.open(out / "height.webp").convert("RGB")).astype(np.float64)
    elev = inner["lo"] + (img[..., 0] * 256 + img[..., 1]) * inner["step"]

    def uv(lat, lon):
        fx = (lon + 180) / 360
        fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
        return (fx - inner["fx0"]) / (inner["fx1"] - inner["fx0"]), (fy - inner["fy0"]) / (inner["fy1"] - inner["fy0"])

    def height(p):
        u, v = uv(*p)
        return float(elev[min(inner["h"] - 1, max(0, round(v * (inner["h"] - 1)))), min(inner["w"] - 1, max(0, round(u * (inner["w"] - 1))))])

    def inside(p, pad=0.0):
        return s + pad < p[0] < n - pad and w + pad < p[1] < e - pad

    def clip(line):
        """Split a line where it leaves the sheet."""
        parts, cur = [], []
        for p in line:
            if inside(p): cur.append(p)
            elif cur: parts.append(cur); cur = []
        if cur: parts.append(cur)
        return [c for c in parts if len(c) > 1]

    def pack(line):
        flat = []
        for p in line:
            u, v = uv(*p)
            flat += [round(u * 65535), round(v * 65535)]
        return flat

    def geom(el):
        return [(g["lat"], g["lon"]) for g in el.get("geometry", []) if g]

    def trail(name, kind, lines, tol=18, note=None):
        lines = [c for l in chain(lines) for c in clip(l)]
        lines = [l for l in lines if length(l) > 250]
        if not lines:
            print("  no geometry for", name); return None
        hs = [height(p) for l in lines for p in l]
        t = dict(n=name, k=kind, mi=round(sum(length(l) for l in lines) / 1609.344, 1),
                 lo=round(min(hs) * 3.28084 / 10) * 10, hi=round(max(hs) * 3.28084 / 10) * 10,
                 lines=[pack(simplify(l, tol)) for l in sorted(lines, key=length, reverse=True)])
        if note: t["note"] = note
        return t

    # ---- trails
    routes = {el["tags"].get("name"): el for el in fetch("routes")}
    paths = fetch("paths") + fetch("extras")
    members = lambda rel: [geom(m) for m in rel["members"] if m["type"] == "way" and m.get("geometry")]
    trails = [
        trail("Arizona Trail", "azt", members(routes["Arizona Trail"]), 22, "800 miles, Mexico to Utah"),
        trail("The Loop", "loop", members(routes["The Loop"]), 14, "Paved, car-free, around the city"),
    ]
    for name, pat in TRAILS:
        rx = re.compile(pat)
        trails.append(trail(name, "trail", [geom(el) for el in paths if rx.search(el["tags"].get("name", ""))]))
    trails = [t for t in trails if t]
    (out / "trails.json").write_text(json.dumps(dict(source="OpenStreetMap contributors (ODbL)", trails=trails), separators=(",", ":")))
    for t in trails:
        print(f'{t["n"]}: {t["mi"]} mi, {t["lo"]} to {t["hi"]} ft, {sum(len(l) for l in t["lines"]) // 2} points')
    print("trails.json", (out / "trails.json").stat().st_size, "bytes")

    # ---- city: main roads over the whole sheet; buildings, rail and streetcar around downtown
    rank = dict(motorway=0, trunk=0, primary=1, secondary=2)
    roads = []
    for el in fetch("roads"):
        for part in clip(geom(el)):
            roads.append([rank[el["tags"]["highway"]]] + pack(simplify(part, 12)))
    rail, tram = [], []
    for el in fetch("rail"):
        if el["type"] == "way" and el["tags"].get("railway") in ("rail", "tram") and not el["tags"].get("service"):
            (tram if el["tags"]["railway"] == "tram" else rail).append(geom(el))
    rail = [pack(simplify(l, 6)) for l in chain(rail) if length(l) > 150]
    tram = [pack(simplify(l, 3)) for l in chain(tram) if length(l) > 60]

    cs, cw, cn, ce = [float(x) for x in CITY.split(",")]
    (u0, v0), (u1, v1) = uv(cn, cw), uv(cs, ce)
    Q = 20000

    def ring(el):
        if el["type"] == "way":
            return geom(el)
        outers = chain([geom(m) for m in el["members"] if m.get("role") == "outer" and m.get("geometry")])
        return max(outers, key=len) if outers else []

    def area(r):
        k = math.cos(math.radians(32.22)) * 111_200
        P = [(p[1] * k, p[0] * 111_200) for p in r]
        return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(P, P[1:] + P[:1]))) / 2

    def tall(tags, a, key):
        """Height in metres: the tagged height, else floors, else a guess from the kind and size of building."""
        if tags.get("name") in HEIGHTS: return HEIGHTS[tags["name"]]
        try:
            if "height" in tags: return float(str(tags["height"]).split()[0])
            if "building:levels" in tags: return float(tags["building:levels"]) * 3.6 + 1
        except ValueError:
            pass
        kind, jit = tags.get("building"), (key * 2654435761 % 1000) / 1000
        if kind in ("house", "terrace", "static_caravan", "garage", "shed", "carport", "roof"): return 3.2 + 1.6 * jit
        if kind in ("apartments", "residential", "hotel", "dormitory"): return 9 + 3 * jit
        if kind in ("university", "school", "office", "public", "parking", "courthouse", "cathedral", "church"): return 10 + 5 * jit
        return (3.8 if a < 1500 else 7) + 2 * jit

    builds = []
    for el in fetch("buildings"):
        if el["id"] == 9099645: continue   # Arizona Stadium: mapped as one solid outline; the page builds its bowl by hand instead
        r = ring(el)
        if len(r) < 4: continue
        a, tags = area(r), el.get("tags", {})
        h = tall(tags, a, el["id"])
        if a < 120 and h < 8: continue
        r = simplify(r[:-1] if r[0] == r[-1] else r, 1.2)
        if len(r) < 3: continue
        row, px, py = [round(h * 10), 0 if tags.get("building") in ("house", "terrace") else 1], 0, 0
        for lat, lon in r:
            u, v = uv(lat, lon)
            x, y = round((u - u0) / (u1 - u0) * Q), round((v - v0) / (v1 - v0) * Q)
            row += [x - px, y - py]; px, py = x, y
        builds.append(row)
    builds.sort(key=lambda b: -b[0])

    # ---- the fabric between the buildings: side streets, green space, washes, and trees
    def enc(line):
        """Delta-encoded in the city frame, like the buildings."""
        row, px, py = [], 0, 0
        for lat, lon in line:
            u, v = uv(lat, lon)
            x, y = round((u - u0) / (u1 - u0) * Q), round((v - v0) / (v1 - v0) * Q)
            if row and x == px and y == py: continue
            row += [x - px, y - py]; px, py = x, y
        return row

    streets = []
    for el in fetch("streets"):
        l = simplify(geom(el), 2.5)
        if length(l) > 40: streets.append([0 if el["tags"]["highway"] == "tertiary" else 1] + enc(l))
    streets.sort(key=lambda s: s[0])
    KIND = dict(park=0, garden=0, grass=0, recreation_ground=0, pitch=1, golf_course=2, cemetery=3)
    green, shade = [], []
    for el in fetch("green"):
        r, tags = ring(el), el.get("tags", {})
        if len(r) < 4 or area(r) < 400: continue
        k = KIND.get(tags.get("leisure") or tags.get("landuse"), 0)
        r = simplify(r[:-1] if r[0] == r[-1] else r, 2)
        if len(r) < 3: continue
        green.append([k] + enc(r))
        if k != 1: shade.append(r)
    green.sort(key=lambda g: g[0] == 1)   # pitches drawn over the parks they sit in
    washes = []
    for l in chain([geom(el) for el in fetch("water") if el["tags"].get("waterway") == "river"]):
        for part in clip(l):
            if length(part) > 800: washes.append(pack(simplify(part, 15)))

    # trees are not mapped one by one, so they are scattered: in parks, and in the yards around buildings, never on a roof or a street
    W, H = 2500, 1850   # about 3 m a pixel
    px = lambda line: [((uv(a, b)[0] - u0) / (u1 - u0) * W, (uv(a, b)[1] - v0) / (v1 - v0) * H) for a, b in line]
    from PIL import ImageDraw, ImageFilter
    built, park = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(built)
    for el in fetch("buildings"):
        r = ring(el)
        if len(r) >= 3: d.polygon(px(r), fill=255)
    yard = np.asarray(built.filter(ImageFilter.MaxFilter(17))) > 0
    d = ImageDraw.Draw(built)
    for el in fetch("streets") + [e for e in fetch("roads")]:
        g = px(geom(el))
        if len(g) > 1: d.line(g, fill=255, width=4)
    blocked = np.asarray(built.filter(ImageFilter.MaxFilter(3))) > 0
    d = ImageDraw.Draw(park)
    for r in shade: d.polygon(px(r), fill=255)
    for g in green:
        if g[0] == 1:   # keep the playing fields clear
            pts, x, y = [], 0, 0
            for i in range(1, len(g), 2):
                x += g[i]; y += g[i + 1]; pts.append((x / Q * W, y / Q * H))
            d.polygon(pts, fill=0)
    inpark = np.asarray(park) > 0
    rng = np.random.default_rng(14)
    trees = []
    for mask, want in ((inpark & ~blocked, 3200), (yard & ~blocked & ~inpark, 6200)):
        cells = np.argwhere(mask)
        for j, i in cells[rng.choice(len(cells), size=min(want, len(cells)), replace=False)]:
            trees += [round((i + rng.random()) / W * Q), round((j + rng.random()) / H * Q)]
    city = dict(source="OpenStreetMap contributors (ODbL)", box=[u0, v0, u1, v1], q=Q, buildings=builds, roads=roads, rail=rail, tram=tram,
                streets=streets, green=green, washes=washes, trees=trees)
    (out / "city.json").write_text(json.dumps(city, separators=(",", ":")))
    print(f"city.json {(out / 'city.json').stat().st_size} bytes: {len(builds)} buildings, {len(roads)} road pieces, {len(rail)} rail, {len(tram)} streetcar")
    print(f"  {len(streets)} side streets, {len(green)} green spaces, {len(washes)} wash pieces, {len(trees) // 2} scattered trees")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "basin")
