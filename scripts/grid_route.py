"""Deterministic two-layer grid router for ONE net connection at a time (read-only on the board).

It is not an autorouter for the board: it routes a single named connection between two given points,
treating ALL existing copper (pads, tracks, vias of other nets) as fixed obstacles inflated by the
rule clearance plus a margin, the board edge, owner keep-out rectangles, and extra "avoid-net" margins
(for example RF lines on every layer). The result is printed as an explicit route-spec fragment
(tracks/vias JSON for scripts/route_stage.py hand), which is then applied, DRC-checked and reviewed.

Run with KiCad's Python:
  python.exe -I scripts/grid_route.py REQUEST.json OUT.json
REQUEST: {"grid": 0.1, "clr": 0.18, "hv_clr": 0.65, "via_cost": 40,
          "keepout": [[x0, y0, x1, y1], ...], "avoid_nets": {"RF_ANT": 1.0},
          "routes": [{"net": "ENC_B", "w": 0.2, "from": [x, y, "F"], "to": [x, y, "F"], "why": "..."}]}
Routes in one request are routed in order; each finished route becomes an obstacle for the next
(other nets) and is a free path for later routes of the same net.
"""
import heapq
import json
import math
import os
import sys

import numpy as np
import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from gen_pcb import BOARD, X0, X1, Y0, Y1  # noqa: E402

HV = ("+48V_RAW", "+48V_MOT", "FLY_SEC")
mm = pcbnew.ToMM


def short(n):
    return n.split("/")[-1]


class Grid:
    def __init__(self, g):
        self.g = g
        self.nx = int(round((X1 - X0) / g)) + 1
        self.ny = int(round((Y1 - Y0) / g)) + 1
        self.xs = X0 + np.arange(self.nx) * g
        self.ys = Y0 + np.arange(self.ny) * g

    def idx(self, x, y):
        return int(round((x - X0) / self.g)), int(round((y - Y0) / self.g))

    def pt(self, i, j):
        return X0 + i * self.g, Y0 + j * self.g

    def window(self, x0, y0, x1, y1):
        i0 = max(0, int(math.floor((x0 - X0) / self.g)))
        i1 = min(self.nx - 1, int(math.ceil((x1 - X0) / self.g)))
        j0 = max(0, int(math.floor((y0 - Y0) / self.g)))
        j1 = min(self.ny - 1, int(math.ceil((y1 - Y0) / self.g)))
        return i0, i1, j0, j1


def mark_capsule(grid, m, ax, ay, bx, by, r):
    i0, i1, j0, j1 = grid.window(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r)
    if i1 < i0 or j1 < j0:
        return
    X, Y = np.meshgrid(grid.xs[i0:i1 + 1], grid.ys[j0:j1 + 1], indexing="ij")
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.zeros_like(X) if L == 0 else np.clip(((X - ax) * dx + (Y - ay) * dy) / L, 0, 1)
    d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
    m[i0:i1 + 1, j0:j1 + 1] |= d < r


def mark_rect(grid, m, x0, y0, x1, y1, r):
    i0, i1, j0, j1 = grid.window(x0 - r, y0 - r, x1 + r, y1 + r)
    if i1 < i0 or j1 < j0:
        return
    X, Y = np.meshgrid(grid.xs[i0:i1 + 1], grid.ys[j0:j1 + 1], indexing="ij")
    dx = np.maximum(0, np.maximum(x0 - X, X - x1))
    dy = np.maximum(0, np.maximum(y0 - Y, Y - y1))
    d = np.hypot(dx, dy)
    m[i0:i1 + 1, j0:j1 + 1] |= (d < r) if r > 0 else (d <= 0)   # r = 0: keep-out rectangle itself


def build_obstacles(b, grid, net, w, req, extra_tracks):
    """Return per-layer track-blocked maps and a via-blocked map for routing `net` with width w."""
    clr, hv = req.get("clr", 0.18), req.get("hv_clr", 0.65)
    avoid = req.get("avoid_nets", {})
    vr = 0.3                                        # via radius (0.6 mm via)
    T = {"F": np.zeros((grid.nx, grid.ny), bool), "B": np.zeros((grid.nx, grid.ny), bool)}
    VIA = np.zeros((grid.nx, grid.ny), bool)
    lyr = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}

    def c_for(other):
        return hv if short(other).endswith(HV) else clr

    for fp in b.GetFootprints():
        for p in fp.Pads():
            pn = short(p.GetNetname())
            bb = p.GetBoundingBox()
            x0, y0, x1, y1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            same = pn == net and pn != ""
            c = c_for(pn)
            for L in ("F", "B"):
                if p.IsOnLayer(lyr[L]) or th:
                    if not same:
                        mark_rect(grid, T[L], x0, y0, x1, y1, c + w / 2)
            if not same or not th:                  # no via in any foreign pad, nor in an own SMD pad
                if p.IsOnLayer(lyr["F"]) or p.IsOnLayer(lyr["B"]) or th:
                    mark_rect(grid, VIA, x0, y0, x1, y1, (c if not same else 0.05) + vr)
    items = []
    for t in b.GetTracks():
        n = short(t.GetNetname())
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            items.append((n, "via", mm(q.x), mm(q.y), mm(q.x), mm(q.y), mm(t.GetWidth(pcbnew.F_Cu)) / 2, None))
        else:
            a, e = t.GetStart(), t.GetEnd()
            L = "F" if t.GetLayer() == pcbnew.F_Cu else "B" if t.GetLayer() == pcbnew.B_Cu else None
            items.append((n, "trk", mm(a.x), mm(a.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2, L))
    items += extra_tracks
    for n, kind, ax, ay, bx, by, hw, L in items:
        if n == net:
            continue
        c = c_for(n)
        if kind == "via":
            for LL in ("F", "B"):
                mark_capsule(grid, T[LL], ax, ay, bx, by, hw + c + w / 2)
            mark_capsule(grid, VIA, ax, ay, bx, by, hw + max(c, 0.25) + vr)
        elif L:
            mark_capsule(grid, T[L], ax, ay, bx, by, hw + c + w / 2)
            mark_capsule(grid, VIA, ax, ay, bx, by, hw + c + vr)
        if n in avoid:                               # extra margin on every layer (e.g. RF lines)
            for LL in ("F", "B"):
                mark_capsule(grid, T[LL], ax, ay, bx, by, hw + avoid[n])
            mark_capsule(grid, VIA, ax, ay, bx, by, hw + avoid[n])
    for (x0, y0, x1, y1) in req.get("keepout", []):
        for LL in ("F", "B"):
            mark_rect(grid, T[LL], x0, y0, x1, y1, 0)
        mark_rect(grid, VIA, x0, y0, x1, y1, 0)
    edge = 0.3 + w / 2                               # board edge clearance
    for m, e in ((T["F"], edge), (T["B"], edge), (VIA, 0.3 + vr)):
        k = int(math.ceil(e / grid.g))
        m[:k, :] = m[-k:, :] = True
        m[:, :k] = m[:, -k:] = True
    return T, VIA


def astar(grid, T, VIA, s, t, via_cost):
    (si, sj, sl), (ti, tj, tl) = s, t
    Ls = ("F", "B")
    blocked = {0: T["F"], 1: T["B"]}
    for (i, j, l) in (s, t):
        blocked[l][i, j] = False                     # endpoints sit on own pads
    INF = 1e18
    gs = {}
    start = (si, sj, sl)
    gs[start] = 0.0
    prev = {}
    h = lambda i, j: (max(abs(i - ti), abs(j - tj)) + (math.sqrt(2) - 1) * min(abs(i - ti), abs(j - tj)))
    pq = [(h(si, sj), 0.0, start, None)]
    moves = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
             (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))]
    goal = (ti, tj, tl)
    n = 0
    while pq:
        f, g, cur, d = heapq.heappop(pq)
        if g > gs.get(cur, INF) + 1e-9:
            continue
        if cur == goal:
            break
        n += 1
        if n > 6_000_000:
            return None, n
        i, j, l = cur
        for di, dj, c in moves:
            ni, nj = i + di, j + dj
            if not (0 <= ni < grid.nx and 0 <= nj < grid.ny) or blocked[l][ni, nj]:
                continue
            if di and dj and (blocked[l][i + di, j] or blocked[l][i, j + dj]):
                continue                             # no corner cutting
            turn = 0.0 if d is None or d == (di, dj) else 0.4
            nk = (ni, nj, l)
            ng = g + c + turn
            if ng < gs.get(nk, INF) - 1e-9:
                gs[nk] = ng
                prev[nk] = cur
                heapq.heappush(pq, (ng + h(ni, nj), ng, nk, (di, dj)))
        if not VIA[i, j]:
            nk = (i, j, 1 - l)
            ng = g + via_cost
            if ng < gs.get(nk, INF) - 1e-9:
                gs[nk] = ng
                prev[nk] = cur
                heapq.heappush(pq, (ng + h(i, j), ng, nk, None))
    if goal not in prev and goal != start:
        return None, n
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return path[::-1], n


def to_spec(grid, path, net, w, why, s_xy, t_xy):
    tracks, vias, run = [], [], []
    layer = path[0][2]

    def flush(run, layer):
        if len(run) < 2:
            return
        pts = [run[0]]
        for k in range(1, len(run) - 1):
            a, b_, c = pts[-1], run[k], run[k + 1]
            if (b_[0] - a[0]) * (c[1] - b_[1]) != (b_[1] - a[1]) * (c[0] - b_[0]):
                pts.append(b_)
        pts.append(run[-1])
        tracks.append({"net": net, "layer": "FB"[layer], "w": w,
                       "pts": [[round(grid.pt(i, j)[0], 3), round(grid.pt(i, j)[1], 3)] for i, j in pts], "why": why})

    for (i, j, l) in path:
        if l != layer:
            flush(run, layer)
            x, y = grid.pt(i, j)
            vias.append({"net": net, "at": [round(x, 3), round(y, 3)]})
            run, layer = [(i, j)], l
        else:
            run.append((i, j))
    flush(run, layer)
    # snap the first/last vertex exactly onto the requested endpoints (pad centres)
    if tracks:
        tracks[0]["pts"][0] = [s_xy[0], s_xy[1]]
        tracks[-1]["pts"][-1] = [t_xy[0], t_xy[1]]
    return tracks, vias


def main(req_path, out_path):
    req = json.load(open(req_path, encoding="utf8"))
    b = pcbnew.LoadBoard(BOARD)
    grid = Grid(req.get("grid", 0.1))
    spec = {"tracks": [], "vias": []}
    extra = []
    for r in req["routes"]:
        net, w = r["net"], r["w"]
        T, VIA = build_obstacles(b, grid, net, w, req, extra)
        (sx, sy, sl), (tx, ty, tl) = r["from"], r["to"]
        s = (*grid.idx(sx, sy), "FB".index(sl))
        t = (*grid.idx(tx, ty), "FB".index(tl))
        path, n = astar(grid, T, VIA, s, t, req.get("via_cost", 40))
        if path is None:
            print(f"NO ROUTE {net} {r['from']} -> {r['to']} (expanded {n})")
            spec.setdefault("failed", []).append(r)
            continue
        tr, vi = to_spec(grid, path, net, w, r.get("why", ""), (sx, sy), (tx, ty))
        L = sum(math.dist(a, c) for t_ in tr for a, c in zip(t_["pts"], t_["pts"][1:]))
        print(f"routed {net}: {L:.1f} mm, {len(vi)} vias, {sum(len(t_['pts']) - 1 for t_ in tr)} segments (expanded {n})")
        spec["tracks"] += tr
        spec["vias"] += vi
        for t_ in tr:                               # later routes see this copper as an obstacle
            for a, c in zip(t_["pts"], t_["pts"][1:]):
                extra.append((net, "trk", a[0], a[1], c[0], c[1], w / 2, t_["layer"]))
        for v in vi:
            extra.append((net, "via", v["at"][0], v["at"][1], v["at"][0], v["at"][1], 0.3, None))
    json.dump(spec, open(out_path, "w", encoding="utf8"), indent=1)
    print("written", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
