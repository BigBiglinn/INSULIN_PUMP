"""Pure-Python geometry model and *approximate* checker for pump_v2.kicad_pcb (no KiCad needed).

Written on 31 Oct 2026 because kicad-cli/pcbnew could not be run in the cloud session that made
the layout fixes. It is NOT a replacement for KiCad DRC: it re-implements only

  * copper clearance between different nets on each copper layer, using the net-class clearances
    from pump_v2.kicad_pro, the two scoped rules in pump_v2.kicad_dru and the zone clearance,
  * copper-to-board-edge clearance and hole-to-other-net-copper clearance,
  * connectivity (pads, tracks, vias, stored zone fills) and the resulting unconnected-pair count,
  * dangling vias / track ends.

Its results were calibrated against the last real kicad-cli 10.0.3 report (validation/drc) on the
unmodified board before it was used; see validation/logs/layout_fixes_2026-10-31.md.

Usage:  python3 scripts/pcbcheck.py [board.kicad_pcb]
Needs:  shapely >= 2 (pip install shapely)
"""
import fnmatch
import json
import math
import os
import sys
from collections import defaultdict

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely.validation import make_valid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadlib import find, find1, parse, unq  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.path.join(ROOT, "hardware", "kicad")
BOARD = os.path.join(KDIR, "pump_v2.kicad_pcb")
CU = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
EDGE_CLR = 0.3          # min_copper_edge_clearance (kicad_pro)
HOLE_CLR = 0.25         # min_hole_clearance (kicad_pro)
ZONE_CLR = 0.3          # local clearance of every zone (gen_pcb.add_zone)
DRU = {"J703": 0.35, "Q301": 0.127}   # pump_v2.kicad_dru, pad-to-pad inside the footprint only


def f(x):
    return float(x)


def rot(x, y, deg):
    """KiCad rotation (y down, positive = counter-clockwise on screen)."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def shp_rot(g, deg, origin):
    return affinity.rotate(g, -deg, origin=origin) if deg else g


def roundrect(w, h, r):
    r = max(0.0, min(r, min(w, h) / 2 - 1e-6))
    b = box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r)
    return b.buffer(r, quad_segs=8) if r > 0 else box(-w / 2, -h / 2, w / 2, h / 2)


class Item:
    __slots__ = ("kind", "net", "layers", "geom", "ref", "pad", "data", "idx", "hole")

    def __init__(self, kind, net, layers, geom, ref=None, pad=None, data=None, hole=None):
        self.kind, self.net, self.layers, self.geom = kind, net, layers, geom
        self.ref, self.pad, self.data, self.hole = ref, pad, data, hole
        self.idx = -1

    def name(self):
        if self.kind == "pad":
            return f"{self.ref}.{self.pad}"
        return self.kind


class Board:
    def __init__(self, path=BOARD):
        self.path = path
        self.tree = parse(open(path, encoding="utf8").read())[0]
        pro = json.load(open(os.path.join(KDIR, "pump_v2.kicad_pro"), encoding="utf8"))
        ns = pro["net_settings"]
        self.classes = {c["name"]: c for c in ns["classes"]}
        self.patterns = [(p["pattern"], p["netclass"]) for p in ns.get("netclass_patterns") or []]
        self._cls = {}
        self.items = []
        self.footprints = {}
        self.zones = []
        self.edge = None
        self._load()

    # ------------------------------------------------------------------ net classes
    def netclass(self, net):
        if net not in self._cls:
            c = "Default"
            for pat, cl in self.patterns:
                if fnmatch.fnmatchcase(net, pat):
                    c = cl
                    break
            self._cls[net] = c
        return self._cls[net]

    def clearance(self, net):
        return self.classes[self.netclass(net)]["clearance"]

    # ------------------------------------------------------------------ loading
    def _load(self):
        t = self.tree
        xs, ys = [], []
        for gl in find(t, "gr_line"):
            if unq(find1(gl, "layer")[1]) == "Edge.Cuts":
                s, e = find1(gl, "start"), find1(gl, "end")
                xs += [f(s[1]), f(e[1])]
                ys += [f(s[2]), f(e[2])]
        self.edge = box(min(xs), min(ys), max(xs), max(ys))
        for fp in find(t, "footprint"):
            self._load_fp(fp)
        for s in find(t, "segment"):
            st, en = find1(s, "start"), find1(s, "end")
            w = f(find1(s, "width")[1])
            p0, p1 = (f(st[1]), f(st[2])), (f(en[1]), f(en[2]))
            g = LineString([p0, p1]).buffer(w / 2, quad_segs=8) if p0 != p1 else Point(p0).buffer(w / 2)
            self._add(Item("track", unq(find1(s, "net")[1]) if find1(s, "net") else "",
                           (unq(find1(s, "layer")[1]),), g, data={"p0": p0, "p1": p1, "w": w, "node": s}))
        for v in find(t, "via"):
            at = find1(v, "at")
            p = (f(at[1]), f(at[2]))
            d = f(find1(v, "size")[1])
            dr = f(find1(v, "drill")[1])
            self._add(Item("via", unq(find1(v, "net")[1]) if find1(v, "net") else "", CU, Point(p).buffer(d / 2, quad_segs=8),
                           data={"p": p, "d": d, "drill": dr, "node": v}, hole=Point(p).buffer(dr / 2, quad_segs=8)))
        for z in find(t, "zone"):
            net = unq(find1(z, "net")[1])
            lay = unq(find1(z, "layer")[1])
            pr = find1(z, "priority")
            zd = {"net": net, "layer": lay, "name": unq(find1(z, "name")[1]), "prio": int(pr[1]) if pr else 0, "node": z}
            self.zones.append(zd)
            for fpoly in find(z, "filled_polygon"):
                pts = [(f(q[1]), f(q[2])) for q in find(find1(fpoly, "pts"), "xy")]
                g = make_valid(Polygon(pts))
                self._add(Item("zone", net, (lay,), g, data={"zone": zd}))

    def _load_fp(self, fp):
        ref = None
        for p in find(fp, "property"):
            if unq(p[1]) == "Reference":
                ref = unq(p[2])
        at = find1(fp, "at")
        X, Y = f(at[1]), f(at[2])
        R = f(at[3]) if len(at) > 3 else 0.0
        attr = find1(fp, "attr")
        self.footprints[ref] = {"node": fp, "x": X, "y": Y, "rot": R, "dnp": attr is not None and "dnp" in attr,
                                "crtyd": self._courtyard(fp, X, Y, R)}
        for pad in find(fp, "pad"):
            num, kind, shape = unq(pad[1]), pad[2], pad[3]
            pat = find1(pad, "at")
            lx, ly = f(pat[1]), f(pat[2])
            pa = f(pat[3]) if len(pat) > 3 else 0.0
            dx, dy = rot(lx, ly, R)
            cx, cy = X + dx, Y + dy
            sz = find1(pad, "size")
            w, h = f(sz[1]), f(sz[2])
            if shape == "circle":
                g = Point(0, 0).buffer(w / 2, quad_segs=16)
            elif shape == "oval":
                if w > h:
                    g = LineString([(-(w - h) / 2, 0), ((w - h) / 2, 0)]).buffer(h / 2, quad_segs=16)
                elif h > w:
                    g = LineString([(0, -(h - w) / 2), (0, (h - w) / 2)]).buffer(w / 2, quad_segs=16)
                else:
                    g = Point(0, 0).buffer(w / 2, quad_segs=16)
            elif shape == "roundrect":
                rr = find1(pad, "roundrect_rratio")
                g = roundrect(w, h, (f(rr[1]) if rr else 0.25) * min(w, h))
            elif shape == "custom":
                opts = find1(pad, "options")
                anch = find1(opts, "anchor")[1] if opts and find1(opts, "anchor") else "rect"
                parts = [Point(0, 0).buffer(w / 2) if anch == "circle" else box(-w / 2, -h / 2, w / 2, h / 2)]
                prim = find1(pad, "primitives")
                for gp in (prim or []):
                    if not isinstance(gp, list):
                        continue
                    if gp[0] == "gr_poly":
                        parts.append(Polygon([(f(q[1]), f(q[2])) for q in find(find1(gp, "pts"), "xy")]))
                    elif gp[0] == "gr_circle":
                        c, e = find1(gp, "center"), find1(gp, "end")
                        r = math.hypot(f(e[1]) - f(c[1]), f(e[2]) - f(c[2]))
                        parts.append(Point(f(c[1]), f(c[2])).buffer(r, quad_segs=16))
                    elif gp[0] == "gr_rect":
                        s, e = find1(gp, "start"), find1(gp, "end")
                        parts.append(box(f(s[1]), f(s[2]), f(e[1]), f(e[2])))
                g = unary_union(parts)
            else:   # rect / trapezoid fallback
                g = box(-w / 2, -h / 2, w / 2, h / 2)
            g = affinity.translate(shp_rot(g, pa, (0, 0)), cx, cy)
            lays = [unq(x) for x in find1(pad, "layers")[1:]]
            cul = CU if "*.Cu" in lays else tuple(l for l in lays if l in CU)
            hole = None
            dr = find1(pad, "drill")
            if dr is not None and kind in ("thru_hole", "np_thru_hole"):
                if len(dr) > 1 and dr[1] == "oval":
                    a, b = f(dr[2]), f(dr[3])
                    hg = (LineString([(-(a - b) / 2, 0), ((a - b) / 2, 0)]).buffer(b / 2) if a >= b
                          else LineString([(0, -(b - a) / 2), (0, (b - a) / 2)]).buffer(a / 2))
                else:
                    hg = Point(0, 0).buffer(f(dr[1]) / 2, quad_segs=16)
                hole = affinity.translate(shp_rot(hg, pa, (0, 0)), cx, cy)
            netn = find1(pad, "net")
            net = unq(netn[1]) if netn else ""
            if kind == "np_thru_hole":
                cul = ()
            self._add(Item("pad", net, cul, g, ref=ref, pad=num,
                           data={"c": (cx, cy), "kind": kind, "node": pad, "size": (w, h)}, hole=hole))

    @staticmethod
    def _courtyard(fp, X, Y, R):
        """Courtyard as a polygon (bounding box of the F.CrtYd graphics, circles kept round)."""
        pts, circles = [], []
        for g in fp:
            if not isinstance(g, list) or g[0] not in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
                continue
            ly = find1(g, "layer")
            if ly is None or unq(ly[1]) != "F.CrtYd":
                continue
            for key in ("start", "end", "mid", "center"):
                q = find1(g, key)
                if q is not None:
                    pts.append((f(q[1]), f(q[2])))
            if g[0] == "fp_circle":
                c, e = find1(g, "center"), find1(g, "end")
                r = math.hypot(f(e[1]) - f(c[1]), f(e[2]) - f(c[2]))
                circles.append(Point(f(c[1]), f(c[2])).buffer(r, quad_segs=16))
                continue
            pp = find1(g, "pts")
            if pp is not None:
                pts += [(f(q[1]), f(q[2])) for q in find(pp, "xy")]
        if not pts and not circles:
            return None
        parts = list(circles)
        if pts:
            x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
            x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
            parts.append(box(x0, y0, x1, y1))
        g = shp_rot(unary_union(parts), R, (0, 0))
        return affinity.translate(g, X, Y)

    def courtyard_overlaps(self, refs=None):
        out = []
        items = [(r, d["crtyd"]) for r, d in self.footprints.items() if d["crtyd"] is not None]
        for i, (r1, g1) in enumerate(items):
            for r2, g2 in items[i + 1:]:
                if refs is not None and r1 not in refs and r2 not in refs:
                    continue
                if g1.intersection(g2).area > 1e-4:
                    out.append((r1, r2))
        return out

    def _add(self, it):
        it.idx = len(self.items)
        self.items.append(it)

    # ------------------------------------------------------------------ queries
    def pads(self, ref, num=None):
        return [i for i in self.items if i.kind == "pad" and i.ref == ref and (num is None or i.pad == num)]

    def by_layer(self):
        d = defaultdict(list)
        for it in self.items:
            for l in it.layers:
                d[l].append(it)
        return d


# ---------------------------------------------------------------------- connectivity
def connectivity(b):
    parent = list(range(len(b.items)))

    def fnd(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def uni(a, c):
        ra, rc = fnd(a), fnd(c)
        if ra != rc:
            parent[ra] = rc

    for lay, its in b.by_layer().items():
        its = [i for i in its if i.net]
        tree = STRtree([i.geom for i in its])
        for k, it in enumerate(its):
            for j in tree.query(it.geom, predicate="intersects"):
                o = its[j]
                if o.net == it.net and o.idx != it.idx:
                    uni(it.idx, o.idx)
    groups = defaultdict(lambda: defaultdict(list))
    for it in b.items:
        if it.net and (it.kind != "pad" or it.layers):
            groups[it.net][fnd(it.idx)].append(it)
    return groups


def unconnected(b, groups=None):
    """Per net: list of components (each a list of items) when the net has more than one."""
    groups = groups or connectivity(b)
    out = {}
    for net, comps in groups.items():
        real = [c for c in comps.values() if any(i.kind in ("pad", "track", "via") for i in c)]
        if len(real) > 1:
            out[net] = real
    return out


def dangling(b, groups=None):
    """Vias touching nothing else on any layer, and track ends that touch nothing."""
    res = []
    lay = b.by_layer()
    trees = {}
    for l, its in lay.items():
        trees[l] = (STRtree([i.geom for i in its]), its)
    for it in b.items:
        if it.kind == "via":
            touch = 0
            for l in CU:
                tr, its = trees[l]
                for j in tr.query(it.geom, predicate="intersects"):
                    o = its[j]
                    if o.idx != it.idx and o.net == it.net:
                        touch += 1
            if touch == 0 or _only_one_layer(it, trees):
                res.append(("via_dangling", it))
        elif it.kind == "track":
            l = it.layers[0]
            tr, its = trees[l]
            for end in (it.data["p0"], it.data["p1"]):
                pt = Point(end).buffer(1e-3)   # the end point itself must lie in other same-net copper
                hit = [its[j] for j in tr.query(pt, predicate="intersects") if its[j].idx != it.idx and its[j].net == it.net]
                if not hit:
                    res.append(("track_dangling", it, end))
    return res


def _only_one_layer(via, trees):
    layers = set()
    for l in CU:
        tr, its = trees[l]
        for j in tr.query(via.geom, predicate="intersects"):
            o = its[j]
            if o.idx != via.idx and o.net == via.net:
                layers.add(l)
    return len(layers) <= 1


# ---------------------------------------------------------------------- clearance
def required(b, a, c):
    if a.kind == "pad" and c.kind == "pad" and a.ref == c.ref and a.ref in DRU:
        return DRU[a.ref]
    r = max(b.clearance(a.net) if a.net else 0.15, b.clearance(c.net) if c.net else 0.15)
    if a.kind == "zone" or c.kind == "zone":
        r = max(r, ZONE_CLR) - 0.005      # zone fills are approximated polygons (max_error 0.005)
    return r


def clearance_violations(b, only=None, tol=1e-3):
    """Pairs of different-net copper closer than the rule. `only`: set of item idx to check against all."""
    out = []
    for lay, its in b.by_layer().items():
        tree = STRtree([i.geom for i in its])
        for it in its:
            if only is not None and it.idx not in only:
                continue
            for j in tree.query(it.geom.buffer(0.65)):
                o = its[j]
                if o.idx <= it.idx and (only is None or o.idx in only):
                    continue
                if o.idx == it.idx or (o.net == it.net and it.net):
                    continue
                if it.kind == "pad" and o.kind == "pad" and it.ref == o.ref and not it.net and not o.net:
                    continue
                req = required(b, it, o)
                d = it.geom.distance(o.geom)
                if d + tol < req:
                    out.append((lay, it, o, d, req))
    # board edge
    inner = b.edge.buffer(-EDGE_CLR)
    for it in b.items:
        if it.kind in ("pad", "track", "via") and it.layers and (only is None or it.idx in only):
            if not inner.contains(it.geom) and it.geom.difference(inner).area > 1e-6:
                out.append(("edge", it, None, None, EDGE_CLR))
    # hole to other-net copper
    holes = [i for i in b.items if i.hole is not None]
    copper = [i for i in b.items if i.layers]
    tree = STRtree([i.geom for i in copper])
    for h in holes:
        for j in tree.query(h.hole.buffer(HOLE_CLR + 0.05)):
            o = copper[j]
            if o.idx == h.idx or (o.net == h.net and h.net) or (o.kind == "pad" and o.ref == h.ref and h.kind == "pad"):
                continue
            if only is not None and h.idx not in only and o.idx not in only:
                continue
            d = h.hole.distance(o.geom)
            if d + 1e-3 < HOLE_CLR and o.kind != "zone":
                out.append(("hole", h, o, d, HOLE_CLR))
    return out


def short(net):
    return net.split("/")[-1]


def summary(path=BOARD, verbose=True):
    b = Board(path)
    g = connectivity(b)
    un = unconnected(b, g)
    n_pairs = sum(len(v) - 1 for v in un.values())
    cv = clearance_violations(b)
    dg = dangling(b, g)
    if verbose:
        print(f"board: {os.path.relpath(path, ROOT)}")
        print(f"items: {len(b.items)}  footprints: {len(b.footprints)}")
        print(f"unconnected pairs (components-1 per net): {n_pairs} on {len(un)} nets")
        for net in sorted(un, key=short):
            comps = un[net]
            desc = []
            for c in comps:
                pads = sorted(i.name() for i in c if i.kind == "pad")
                desc.append("{" + (",".join(pads[:4]) + ("..." if len(pads) > 4 else "") if pads else
                                   f"{len(c)} track/via items") + "}")
            print(f"  {short(net):14s} {len(comps) - 1}  " + " | ".join(desc))
        print(f"copper clearance / edge / hole violations: {len(cv)}")
        for lay, a, c, d, req in cv[:60]:
            print(f"  {lay:6s} {a.kind}:{a.name()}[{short(a.net)}] vs "
                  f"{(c.kind + ':' + c.name() + '[' + short(c.net) + ']') if c else 'board edge'} "
                  f"d={d if d is None else round(d, 3)} req={req}")
        print(f"dangling: {sum(1 for x in dg if x[0] == 'via_dangling')} vias, "
              f"{sum(1 for x in dg if x[0] == 'track_dangling')} track ends")
        for x in dg:
            it = x[1]
            loc = it.data["p"] if it.kind == "via" else x[2]
            print(f"  {x[0]} {short(it.net)} at ({loc[0]:.2f}, {loc[1]:.2f})")
    return b, un, cv, dg


if __name__ == "__main__":
    summary(sys.argv[1] if len(sys.argv) > 1 else BOARD)


# ---------------------------------------------------------------------- in-memory edits (keep in sync with pcbedit)
def _reindex(b):
    for k, it in enumerate(b.items):
        it.idx = k


def mem_remove(b, items):
    gone = {id(i) for i in items}
    b.items = [i for i in b.items if id(i) not in gone]
    _reindex(b)


def mem_add_track(b, layer, p0, p1, w, net, uid=None):
    g = LineString([p0, p1]).buffer(w / 2, quad_segs=8) if p0 != p1 else Point(p0).buffer(w / 2)
    it = Item("track", net, (layer,), g, data={"p0": p0, "p1": p1, "w": w, "node": ["segment", ["uuid", f'"{uid}"']]})
    b._add(it)
    return it


def mem_add_via(b, p, net, d=0.6, drill=0.3, uid=None):
    it = Item("via", net, CU, Point(p).buffer(d / 2, quad_segs=8),
              data={"p": p, "d": d, "drill": drill, "node": ["via", ["uuid", f'"{uid}"']]},
              hole=Point(p).buffer(drill / 2, quad_segs=8))
    b._add(it)
    return it


def mem_move_fp(b, ref, x, y, rot=None):
    fp = b.footprints[ref]
    r0 = fp["rot"]
    r1 = r0 if rot is None else rot % 360
    d = r1 - r0
    ox, oy = fp["x"], fp["y"]

    def tf(g):
        g = affinity.translate(g, -ox, -oy)
        g = shp_rot(g, d, (0, 0))
        return affinity.translate(g, x, y)
    for k, it in enumerate(b.items):
        if it.kind == "pad" and it.ref == ref:      # replace, never mutate: snapshots share Item objects
            c = tf(Point(it.data["c"]))
            n = Item(it.kind, it.net, it.layers, tf(it.geom), ref=it.ref, pad=it.pad,
                     data=dict(it.data, c=(c.x, c.y)), hole=tf(it.hole) if it.hole is not None else None)
            n.idx = it.idx
            b.items[k] = n
    if fp["crtyd"] is not None:
        fp["crtyd"] = tf(fp["crtyd"])
    fp["x"], fp["y"], fp["rot"] = x, y, r1
