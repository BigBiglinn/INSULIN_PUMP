"""Approximate front-silkscreen geometry for pump_v2.kicad_pcb (31 Oct 2026, no KiCad available).

Silk lines/shapes are exact (stroke buffered); text is approximated by a rectangle
(width = characters x 0.85 x font width + thickness, height = font height + thickness), so the
overlap counts are ESTIMATES, used only to choose reference-text positions for moved parts and to
compare before/after. Only KiCad's DRC can confirm silkscreen results.
"""
import math
import re
import sys

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

from kicadlib import find, find1, parse, unq

CHAR_W = 0.85


def rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def text_box(txt, x, y, ang, sx, sy, th, justify=""):
    w = len(txt) * sx * CHAR_W + th
    h = sy + th
    if "left" in justify.split():
        g = box(0, -h / 2, w, h / 2)
    elif "right" in justify.split():
        g = box(-w, -h / 2, 0, h / 2)
    else:
        g = box(-w / 2, -h / 2, w / 2, h / 2)
    g = affinity.rotate(g, -ang, origin=(0, 0)) if ang else g
    return affinity.translate(g, x, y)


def load(path, layer="F.SilkS"):
    t = parse(open(path, encoding="utf8").read())[0]
    items = []      # (owner, kind, geom)
    masks = []      # (owner, geom)
    edge = None
    xs, ys = [], []
    for gl in find(t, "gr_line"):
        if unq(find1(gl, "layer")[1]) == "Edge.Cuts":
            s, e = find1(gl, "start"), find1(gl, "end")
            xs += [float(s[1]), float(e[1])]
            ys += [float(s[2]), float(e[2])]
    edge = box(min(xs), min(ys), max(xs), max(ys))
    for fp in find(t, "footprint"):
        ref = next(unq(p[2]) for p in find(fp, "property") if unq(p[1]) == "Reference")
        at = find1(fp, "at")
        X, Y, R = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0

        def P(q):
            dx, dy = rot(float(q[1]), float(q[2]), R)
            return X + dx, Y + dy
        for g in fp:
            if not isinstance(g, list):
                continue
            if g[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
                ly = find1(g, "layer")
                if ly is None or unq(ly[1]) != layer:
                    continue
                st = find1(g, "stroke")
                w = float(find1(st, "width")[1]) if st else 0.12
                if g[0] == "fp_line":
                    geo = LineString([P(find1(g, "start")), P(find1(g, "end"))]).buffer(w / 2)
                elif g[0] == "fp_rect":
                    a, c = P(find1(g, "start")), P(find1(g, "end"))
                    geo = box(min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1])).exterior.buffer(w / 2)
                elif g[0] == "fp_circle":
                    c, e = P(find1(g, "center")), P(find1(g, "end"))
                    geo = Point(c).buffer(math.dist(c, e)).exterior.buffer(w / 2)
                elif g[0] == "fp_arc":
                    geo = LineString([P(find1(g, "start")), P(find1(g, "mid")), P(find1(g, "end"))]).buffer(w / 2)
                else:
                    pts = [P(q) for q in find(find1(g, "pts"), "xy")]
                    geo = Polygon(pts).buffer(w / 2) if len(pts) > 2 else None
                if geo is not None:
                    items.append((ref, "line", geo))
            elif g[0] == "property" and unq(g[1]) in ("Reference", "Value"):
                ly = find1(g, "layer")
                if ly is None or unq(ly[1]) != layer or find1(g, "hide") is not None:
                    continue
                pat = find1(g, "at")
                dx, dy = rot(float(pat[1]), float(pat[2]), R)
                ang = float(pat[3]) if len(pat) > 3 else 0.0
                fo = find1(find1(g, "effects"), "font")
                sz = find1(fo, "size")
                th = find1(fo, "thickness")
                j = find1(find1(g, "effects"), "justify")
                items.append((ref, "ref", text_box(unq(g[2]), X + dx, Y + dy, ang, float(sz[1]), float(sz[2]),
                                                   float(th[1]) if th else 0.15, " ".join(j[1:]) if j else "")))
            elif g[0] == "pad":
                lays = [unq(x) for x in find1(g, "layers")[1:]]
                if "F.Mask" in lays or "*.Mask" in lays:
                    pat = find1(g, "at")
                    dx, dy = rot(float(pat[1]), float(pat[2]), R)
                    sz = find1(g, "size")
                    w, h = float(sz[1]), float(sz[2])
                    pa = float(pat[3]) if len(pat) > 3 else 0.0
                    shp = Point(0, 0).buffer(w / 2) if g[3] in ("circle",) else box(-w / 2, -h / 2, w / 2, h / 2)
                    shp = affinity.rotate(shp, -pa, origin=(0, 0)) if pa else shp
                    masks.append((ref, affinity.translate(shp, X + dx, Y + dy)))
    for gt in find(t, "gr_text"):
        if unq(find1(gt, "layer")[1]) != layer:
            continue
        pat = find1(gt, "at")
        fo = find1(find1(gt, "effects"), "font")
        sz = find1(fo, "size")
        j = find1(find1(gt, "effects"), "justify")
        items.append(("board", "text", text_box(unq(gt[1]), float(pat[1]), float(pat[2]),
                                               float(pat[3]) if len(pat) > 3 else 0.0, float(sz[1]), float(sz[2]),
                                               float(find1(fo, "thickness")[1]), " ".join(j[1:]) if j else "")))
    return items, masks, edge


def problems(items, masks, edge, refs=None):
    """Estimated (silk_overlap between different owners, silk_over_copper, silk_edge) lists."""
    ov, oc, ed = [], [], []
    tree = STRtree([g for _, _, g in items])
    for i, (o1, k1, g1) in enumerate(items):
        for j in tree.query(g1, predicate="intersects"):
            if j <= i:
                continue
            o2, k2, g2 = items[j]
            if o1 == o2 or (refs is not None and o1 not in refs and o2 not in refs):
                continue
            if g1.intersection(g2).area > 1e-4:
                ov.append((o1, k1, o2, k2))
    mt = STRtree([g for _, g in masks])
    for o1, k1, g1 in items:
        if refs is not None and o1 not in refs:
            continue
        for j in mt.query(g1, predicate="intersects"):
            o2, g2 = masks[j]
            if g1.intersection(g2).area > 1e-4:
                oc.append((o1, k1, o2))
        if not edge.buffer(-0.01).contains(g1):
            ed.append((o1, k1))
    return ov, oc, ed


if __name__ == "__main__":
    it, m, e = load(sys.argv[1])
    ov, oc, ed = problems(it, m, e)
    print(f"estimated: silk overlaps {len(ov)}, silk over copper {len(oc)}, silk at edge {len(ed)}")
    for x in ed:
        print("  edge:", x)
