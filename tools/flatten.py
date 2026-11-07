"""Flatten the board's exported SVG (masks, strokes, transforms) into one filled outline."""
import re
import sys
import xml.etree.ElementTree as ET

from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from svgelements import Matrix, Move, Path

NS = "{http://www.w3.org/2000/svg}"
STEP = 0.08  # curve sampling step, in the element's own units scaled to the 108 grid


def subpath_points(d, scale):
    out = []
    for sub in Path(d).as_subpaths():
        pts, closed = [], False
        for seg in sub:
            if isinstance(seg, Move):
                pts.append((seg.end.x, seg.end.y))
                continue
            if type(seg).__name__ == "Close":
                closed = True
                continue
            length = seg.length(error=1e-3) * scale
            n = max(1, int(length / STEP)) if type(seg).__name__ != "Line" else 1
            for i in range(1, n + 1):
                p = seg.point(i / n)
                pts.append((p.x, p.y))
        if len(pts) > 1:
            out.append((pts, closed))
    return out


def to_shapely(m):
    return [m.a, m.c, m.b, m.d, m.e, m.f]


def element_geom(el, m, st):
    tag = el.tag.replace(NS, "")
    if tag == "rect":
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        w, h = float(el.get("width")), float(el.get("height"))
        d = f"M{x} {y}H{x + w}V{y + h}H{x}Z"
    else:
        d = el.get("d")
    scale = (abs(m.a * m.d - m.b * m.c)) ** 0.5
    subs = subpath_points(d, scale)
    geoms = []
    if st["fill"] != "none":
        polys = [Polygon(p).buffer(0) for p, _ in subs if len(p) >= 3]
        if st["fill-rule"] == "evenodd":
            g = Polygon()
            for p in polys:
                g = g.symmetric_difference(p)
        else:
            g = unary_union(polys)
        geoms.append((st["fill"], g))
    if st["stroke"] != "none":
        w = float(st["stroke-width"])
        cap = {"butt": "flat", "round": "round", "square": "square"}[st["stroke-linecap"]]
        join = {"miter": "mitre", "round": "round", "bevel": "bevel"}[st["stroke-linejoin"]]
        parts = []
        for p, closed in subs:
            line = LineString(p + [p[0]] if closed else p)
            parts.append(line.buffer(w / 2, cap_style=cap, join_style=join, mitre_limit=4, quad_segs=24))
        geoms.append((st["stroke"], unary_union(parts)))
    return [(c, affinity.affine_transform(g, to_shapely(m))) for c, g in geoms]


def render(el, m, st, masks, sink):
    """Paint el into sink: a list of (color, geometry) in document order."""
    tag = el.tag.replace(NS, "")
    if tag in ("defs", "mask"):
        return
    own = el.get("transform")
    m = Matrix(own) * m if own else m
    st = dict(st)
    for k in ("fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "fill-rule"):
        if el.get(k) is not None:
            st[k] = el.get(k)
    mask_ref = el.get("mask")
    local = []
    if tag in ("path", "rect"):
        local = element_geom(el, m, st)
    else:
        for child in el:
            render(child, m, st, masks, local)
    if mask_ref:
        region = masks[re.search(r"#([^)]+)", mask_ref).group(1)]
        local = [(c, g.intersection(region)) for c, g in local]
    sink.extend(local)


def paint(items):
    g = Polygon()
    for color, geom in items:
        if color.lower() in ("#000", "#000000"):
            g = g.difference(geom)
        else:
            g = g.union(geom)
    return g


def path_data(g):
    polys = getattr(g, "geoms", [g])
    out = []
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)[:-1]
            out.append("M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in c) + "Z")
    return "".join(out)


def flatten(svg_file):
    root = ET.parse(svg_file).getroot()
    base = {"fill": "#000", "stroke": "none", "stroke-width": "1", "stroke-linecap": "butt",
            "stroke-linejoin": "miter", "fill-rule": "nonzero"}
    masks = {}
    for mk in root.iter(NS + "mask"):
        items = []
        for child in mk:
            render(child, Matrix(), base, masks, items)
        masks[mk.get("id")] = paint(items)
    items = []
    for child in root:
        render(child, Matrix(), {**base, "fill": "#fff"}, masks, items)
    # In the page everything outside masks is one color, so every painted item adds.
    g = unary_union([geom for _, geom in items])
    return g.simplify(0.01)


if __name__ == "__main__":
    g = flatten(sys.argv[1])
    print(g.bounds, file=sys.stderr)
    print(path_data(g))
