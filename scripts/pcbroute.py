"""Grid maze router (A*) used for the 31 Oct 2026 layout fixes, pure Python + shapely + numpy.

It routes ONE connection between two existing copper groups of the same net, on F.Cu and/or B.Cu,
with optional through vias, keeping every other-net copper item at the net-class clearance
(pump_v2.kicad_pro) plus a safety margin for grid discretisation. Copper pours on F.Cu/B.Cu and the
inner planes are not treated as obstacles because layout_fixes.py re-clips their stored fills
around every new item afterwards. Results are always re-checked with pcbcheck.clearance_violations.
"""
import heapq
import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from pcbcheck import CU, EDGE_CLR, HOLE_CLR, ZONE_CLR

SIG = ("F.Cu", "B.Cu")
NO_VIA_UNDER = ("U101", "U201", "U301", "U501")
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def _req(b, net, other):
    r = max(b.clearance(net), b.clearance(other.net) if other.net else 0.15)
    if other.kind == "pad" and other.ref == "J703" and net.endswith("+48V_MOT"):
        r = max(r, 0.6)
    return r


def route(b, net, src, dst, win, grid=0.05, w=0.2, layers=SIG, via=(0.6, 0.3), via_cost=4.0,
          bend_cost=0.3, margin=None, extra=(), ignore=(), keepout=None, layer_cost=None):
    """src/dst: lists of Items (same net) to connect. win: (x0, y0, x1, y1).
    extra: list of (layer, geometry) additional obstacles already carrying their own clearance.
    ignore: item indices to treat as absent (ripped up). Returns (segments, vias) or None."""
    net = src[0].net if src and src[0].net else net      # always the full hierarchical name
    if win is None:                                      # bounding box of both ends + 3 mm
        bx = unary_union([i.geom for i in list(src) + list(dst) if i.kind != "zone"]).bounds
        e = b.edge.bounds
        win = (max(e[0], math.floor((bx[0] - 3) / grid) * grid), max(e[1], math.floor((bx[1] - 3) / grid) * grid),
               min(e[2], bx[2] + 3), min(e[3], bx[3] + 3))
    margin = grid * 0.75 if margin is None else margin
    x0, y0, x1, y1 = win
    nx, ny = int(round((x1 - x0) / grid)) + 1, int(round((y1 - y0) / grid)) + 1
    xs = x0 + np.arange(nx) * grid
    ys = y0 + np.arange(ny) * grid
    X, Y = np.meshgrid(xs, ys)          # [iy, ix]
    wb = box(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    edge_in = b.edge.buffer(-(EDGE_CLR + w / 2 + margin))
    ignore = set(ignore)
    others = [i for i in b.items if i.idx not in ignore and i.kind != "zone" and i.layers
              and (i.net != net or not net) and i.geom.intersects(wb)]
    free = {}
    for L in layers:
        obs = [o.geom.buffer(_req(b, net, o) + w / 2 + margin, quad_segs=6) for o in others if L in o.layers]
        obs += [g for (l, g) in extra if l == L]
        if keepout is not None:
            obs.append(keepout)
        u = unary_union(obs) if obs else None
        m = shapely.contains_xy(edge_in, X, Y)
        if u is not None:
            m &= ~shapely.contains_xy(u, X, Y)
        free[L] = m
    vr = via[0] / 2
    vfree = None
    if via and len(layers) > 1:
        obs = [o.geom.buffer(_req(b, net, o) + vr + margin, quad_segs=6) for o in others]
        obs += [o.hole.buffer(HOLE_CLR + via[1] / 2 + margin) for o in b.items
                if o.hole is not None and o.idx not in ignore and o.geom.intersects(wb)]
        obs += [g for (l, g) in extra]
        # no via-in-pad: keep vias 0.1 mm off every SMD pad, own net included
        obs += [o.geom.buffer(vr + 0.1 + margin) for o in b.items if o.kind == "pad" and o.net == net
                and o.data["kind"] == "smd" and o.geom.intersects(wb)]
        # no vias under packages with an exposed pad or solder bumps (WCSP/QFN/WSON/SON); vias under
        # the body of the leaded LQFP (U601) are allowed, as the original routing already used
        obs += [fp["crtyd"].buffer(margin) for r, fp in b.footprints.items()
                if r in NO_VIA_UNDER and fp["crtyd"] is not None and fp["crtyd"].intersects(wb)]
        if keepout is not None:
            obs.append(keepout)
        u = unary_union(obs)
        vfree = shapely.contains_xy(b.edge.buffer(-(EDGE_CLR + vr + margin)), X, Y) & ~shapely.contains_xy(u, X, Y)
    li = {L: k for k, L in enumerate(layers)}

    def cells_in(items):
        out = set()
        for it in items:
            for L in layers:
                if L in it.layers:
                    g = it.geom.buffer(-min(w / 2, 0.05)) if it.kind != "zone" else it.geom
                    if g.is_empty:
                        g = it.geom
                    m = shapely.contains_xy(g, X, Y) & free[L]
                    for iy, ix in zip(*np.nonzero(m)):
                        out.add((li[L], int(ix), int(iy)))
        return out

    S, T = cells_in(src), cells_in(dst)
    if not S or not T:
        return None
    tx = np.array([c[1] for c in T])
    ty = np.array([c[2] for c in T])
    tcx, tcy = tx.mean(), ty.mean()

    def h(ix, iy):
        return math.hypot(ix - tcx, iy - tcy) * 0.98 - max(np.ptp(tx), np.ptp(ty))

    lcost = layer_cost or {}
    openq = []
    best = {}
    prev = {}
    for c in S:
        best[(c, -1)] = 0.0
        heapq.heappush(openq, (h(c[1], c[2]), 0.0, c, -1))
    goal = None
    nL = len(layers)
    while openq:
        f, g, c, d = heapq.heappop(openq)
        if best.get((c, d), 1e18) < g:
            continue
        if c in T:
            goal = (c, d)
            break
        L, ix, iy = c
        for k, (dx, dy) in enumerate(DIRS):
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx < nx and 0 <= jy < ny) or not free[layers[L]][jy, jx]:
                continue
            if dx and dy and not (free[layers[L]][iy, jx] or free[layers[L]][jy, ix]):
                continue
            step = 1.41421356 if dx and dy else 1.0
            ng = g + step * (1 + lcost.get(layers[L], 0)) + (bend_cost / grid if d not in (-1, -2, k) else 0)
            nc = (L, jx, jy)
            if ng < best.get((nc, k), 1e18):
                best[(nc, k)] = ng
                prev[(nc, k)] = (c, d)
                heapq.heappush(openq, (ng + h(jx, jy), ng, nc, k))
        if vfree is not None and vfree[iy, ix]:
            for L2 in range(nL):
                if L2 == L or not free[layers[L2]][iy, ix]:
                    continue
                nc = (L2, ix, iy)
                ng = g + via_cost / grid          # via_cost is in mm of equivalent track
                if ng < best.get((nc, -2), 1e18):
                    best[(nc, -2)] = ng
                    prev[(nc, -2)] = (c, d)
                    heapq.heappush(openq, (ng + h(ix, iy), ng, nc, -2))
    if goal is None:
        return None
    path = []
    s = goal
    while s in prev:
        path.append(s[0])
        s = prev[s]
    path.append(s[0])
    path.reverse()
    # convert to segments / vias
    segs, vias = [], []
    run = [path[0]]
    for c in path[1:]:
        if c[0] != run[-1][0]:
            segs.append((layers[run[0][0]], run))
            vias.append((float(xs[c[1]]), float(ys[c[2]])))
            run = [c]
        else:
            run.append(c)
    segs.append((layers[run[0][0]], run))
    out = []
    for L, cells in segs:
        pts = [(float(xs[c[1]]), float(ys[c[2]])) for c in cells]
        out += [(L, p0, p1) for p0, p1 in _simplify(pts)]
    return out, vias


def _simplify(pts):
    if len(pts) < 2:
        return []
    res = [pts[0]]
    for p in pts[1:]:
        if len(res) >= 2:
            a, b_ = res[-2], res[-1]
            d1 = (round((b_[0] - a[0]) * 1e4), round((b_[1] - a[1]) * 1e4))
            d2 = (round((p[0] - b_[0]) * 1e4), round((p[1] - b_[1]) * 1e4))
            if d1[0] * d2[1] == d1[1] * d2[0] and d1[0] * d2[0] + d1[1] * d2[1] > 0:
                res[-1] = p
                continue
        if p != res[-1]:
            res.append(p)
    return list(zip(res, res[1:]))
