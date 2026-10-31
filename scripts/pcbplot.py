"""Plot a window of pump_v2.kicad_pcb copper (F.Cu red, B.Cu blue, pads labelled) for layout review.

Usage: python3 scripts/pcbplot.py x0 y0 x1 y1 out.png [board] [--zones] [--hl NET,NET]
Read-only. Needs shapely and matplotlib.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from shapely.geometry import box  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbcheck import BOARD, Board, short  # noqa: E402

COL = {"F.Cu": "#d03030", "B.Cu": "#3050d0", "In1.Cu": "#30a030", "In2.Cu": "#c09020"}


def draw(ax, g, **kw):
    geoms = getattr(g, "geoms", [g])
    for p in geoms:
        if p.geom_type == "Polygon":
            x, y = p.exterior.xy
            ax.fill(x, y, **kw)
            for h in p.interiors:
                hx, hy = h.xy
                ax.fill(hx, hy, color="white")
        elif hasattr(p, "geoms"):
            draw(ax, p, **kw)


def plot(x0, y0, x1, y1, out, path=BOARD, zones=False, hl=()):
    b = Board(path)
    win = box(x0, y0, x1, y1)
    fig, ax = plt.subplots(figsize=(14, 14 * (y1 - y0) / (x1 - x0)))
    if zones:
        for it in b.items:
            if it.kind == "zone" and it.layers[0] in ("F.Cu", "B.Cu") and it.geom.intersects(win):
                draw(ax, it.geom.intersection(win), color=COL[it.layers[0]], alpha=0.06)
    for lay in ("B.Cu", "F.Cu"):
        for it in b.items:
            if it.kind in ("track",) and it.layers[0] == lay and it.geom.intersects(win):
                h = short(it.net) in hl
                draw(ax, it.geom, color="orange" if h else COL[lay], alpha=0.9 if h else 0.45)
    for it in b.items:
        if it.kind == "pad" and it.geom.intersects(win):
            h = short(it.net) in hl
            draw(ax, it.geom, color="orange" if h else ("#888" if it.layers != ("F.Cu",) else "#c06060"), alpha=0.85)
            cx, cy = it.data["c"]
            ax.text(cx, cy, f"{it.ref}.{it.pad}\n{short(it.net)[:10]}", fontsize=5, ha="center", va="center")
        elif it.kind == "via" and it.geom.intersects(win):
            h = short(it.net) in hl
            draw(ax, it.geom, color="orange" if h else "#444", alpha=0.9)
            ax.text(*it.data["p"], short(it.net)[:8], fontsize=4, color="purple")
    for ref, fp in b.footprints.items():
        if x0 <= fp["x"] <= x1 and y0 <= fp["y"] <= y1:
            ax.text(fp["x"], fp["y"] - 0.9, ref, fontsize=8, color="black", weight="bold", ha="center")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    ax.set_xticks(range(int(x0), int(x1) + 1, 2))
    ax.set_yticks(range(int(y0), int(y1) + 1, 2))
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out, dpi=110)


if __name__ == "__main__":
    a = sys.argv[1:]
    zones = "--zones" in a
    hl = ()
    if "--hl" in a:
        hl = tuple(a[a.index("--hl") + 1].split(","))
        a = a[:a.index("--hl")] + a[a.index("--hl") + 2:]
    a = [x for x in a if x != "--zones"]
    plot(float(a[0]), float(a[1]), float(a[2]), float(a[3]), a[4], a[5] if len(a) > 5 else BOARD, zones, hl)
