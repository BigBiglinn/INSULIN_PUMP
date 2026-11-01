"""Silkscreen cleanup, driven by the DRC report: move colliding reference fields to a free spot.

Run with KiCad's Python: python.exe -I scripts/pcb_silk.py DRC.json
A reference with no free spot within reach goes to the fab layer, so it stays in the assembly drawing.
Footprint outlines stay exactly as in the library.
No copper is touched.
"""
import json
import math
import os
import re
import sys

import numpy as np
import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_pcb import BOARD, MM, V, fill  # noqa: E402

mm = pcbnew.ToMM
SILK = {pcbnew.F_SilkS: pcbnew.F_Cu, pcbnew.B_SilkS: pcbnew.B_Cu}
FAB = {pcbnew.F_SilkS: pcbnew.F_Fab, pcbnew.B_SilkS: pcbnew.B_Fab}


def box(item, m=0.0):
    b = item.GetBoundingBox()
    return [mm(b.GetLeft()) - m, mm(b.GetTop()) - m, mm(b.GetRight()) + m, mm(b.GetBottom()) + m]


def shape_rects(g, m=0.08):
    """Small rectangles along a silk line, circle or arc, so a large outline does not block its inside."""
    t = g.GetShape()
    if t == pcbnew.SHAPE_T_SEGMENT:
        a, e = g.GetStart(), g.GetEnd()
        pts = [(mm(a.x), mm(a.y)), (mm(e.x), mm(e.y))]
        n = max(1, int(math.dist(*pts) / 0.3))
        pts = [(pts[0][0] + (pts[1][0] - pts[0][0]) * k / n, pts[0][1] + (pts[1][1] - pts[0][1]) * k / n) for k in range(n + 1)]
    elif t == pcbnew.SHAPE_T_CIRCLE:
        c = g.GetCenter()
        r = mm(g.GetRadius())
        n = max(8, int(2 * math.pi * r / 0.3))
        pts = [(mm(c.x) + r * math.cos(2 * math.pi * k / n), mm(c.y) + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    else:
        return [box(g, m)]
    return [[x - 0.15 - m, y - 0.15 - m, x + 0.15 + m, y + 0.15 + m] for x, y in pts]


def place_board_text(b, obs, lim):
    """Move the 48 V label to free silk near its block; mirror the back-side notes so they read correctly."""
    for g in b.GetDrawings():                    # RF mask opening stops short of the J501 outline
        if g.GetLayer() == pcbnew.F_Mask and abs(mm(g.GetStart().y) - 104.7) < 0.01:
            g.SetStart(V(mm(g.GetStart().x), 105.05))
    for g in b.GetDrawings():
        if g.Type() == pcbnew.PCB_TEXT_T and g.GetLayer() == pcbnew.B_SilkS and not g.IsMirrored():
            right = box(g)[2]
            g.SetMirrored(True)
            g.SetPosition(V(right, mm(g.GetPosition().y)))
    for g in b.GetDrawings():
        if g.Type() == pcbnew.PCB_TEXT_T and g.GetText() == "48V ZONE":
            old = box(g, 0.2)
            o = obs[pcbnew.F_SilkS]
            o = o[~((o[:, 0] == old[0] + 0.1) & (o[:, 1] == old[1] + 0.1))]
            for size in (1.5, 1.0):
                g.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
                g.SetTextThickness(MM(size * 0.15))
                for rad in np.arange(0, 30, 0.25):
                    for k in range(max(8, int(rad * 8))):
                        a = 2 * math.pi * k / max(8, int(rad * 8))
                        g.SetPosition(V(float(192 + rad * math.cos(a)), float(145 + rad * math.sin(a))))
                        q = box(g, 0.15)
                        if q[0] > lim[0] and q[1] > lim[1] and q[2] < lim[2] and q[3] < lim[3] and not np.any(
                                (o[:, 0] < q[2]) & (o[:, 2] > q[0]) & (o[:, 1] < q[3]) & (o[:, 3] > q[1])):
                            print("48V ZONE at", q)
                            obs[pcbnew.F_SilkS] = np.vstack([obs[pcbnew.F_SilkS], q])
                            return


def main(drc_path):
    drc = json.load(open(drc_path, encoding="utf8"))
    bad = set()
    for v in drc["violations"]:
        if v["type"].startswith("silk"):
            for i in v["items"]:
                m = re.match(r"Reference field of (\S+)", i["description"])
                if m:
                    bad.add(m.group(1))
    b = pcbnew.LoadBoard(BOARD)
    edge = b.GetBoardEdgesBoundingBox()
    X0, Y0, X1, Y1 = mm(edge.GetLeft()) + 0.5, mm(edge.GetTop()) + 0.5, mm(edge.GetRight()) - 0.5, mm(edge.GetBottom()) - 0.5
    obs = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            for s, c in SILK.items():
                if p.IsOnLayer(c) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    obs[s].append(box(p, 0.15))
        for g in fp.GraphicalItems():
            if g.GetLayer() in obs and g.Type() == pcbnew.PCB_SHAPE_T:
                obs[g.GetLayer()] += shape_rects(g)
        r = fp.Reference()
        if r.GetLayer() in obs and fp.GetReference() not in bad and r.IsVisible():
            obs[r.GetLayer()].append(box(r, 0.1))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y, d = mm(t.GetPosition().x), mm(t.GetPosition().y), 0.45
            for s in obs:
                obs[s].append([x - d, y - d, x + d, y + d])
    for g in b.GetDrawings():
        if g.GetLayer() in obs:
            obs[g.GetLayer()].append(box(g, 0.1))
        elif g.GetLayer() == pcbnew.F_Mask:
            obs[pcbnew.F_SilkS].append(box(g, 0.15))
    obs = {k: np.array(v, float) for k, v in obs.items()}
    place_board_text(b, obs, (X0, Y0, X1, Y1))
    placed = fab = 0
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        if ref not in bad:
            continue
        r = fp.Reference()
        s = r.GetLayer()
        if s not in obs:
            continue
        c = fp.GetPosition()
        cx, cy = mm(c.x), mm(c.y)
        best = None
        for size, width in ((1.0, 0.15), (0.8, 0.12)):
            r.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
            r.SetTextThickness(MM(width))
            for rad in np.arange(0.5, 9.0, 0.25):
                for k in range(max(8, int(rad * 10))):
                    a = 2 * math.pi * k / max(8, int(rad * 10))
                    x, y = float(cx + rad * math.cos(a)), float(cy + rad * math.sin(a))
                    for ang in (0, 90):
                        r.SetTextAngleDegrees(ang)
                        r.SetPosition(V(x, y))
                        q = box(r, 0.1)
                        if q[0] < X0 or q[1] < Y0 or q[2] > X1 or q[3] > Y1:
                            continue
                        o = obs[s]
                        if not np.any((o[:, 0] < q[2]) & (o[:, 2] > q[0]) & (o[:, 1] < q[3]) & (o[:, 3] > q[1])):
                            best = (x, y, ang, q)
                            break
                    if best:
                        break
                if best:
                    break
            if best:
                break
        if best:
            r.SetTextAngleDegrees(best[2])
            r.SetPosition(V(best[0], best[1]))
            obs[s] = np.vstack([obs[s], best[3]])
            placed += 1
        else:
            r.SetLayer(FAB[s])
            fab += 1
            print("to fab layer:", ref)
    print(f"references moved {placed}, to fab layer {fab}, of {len(bad)} flagged")
    pcbnew.SaveBoard(BOARD, b)


if __name__ == "__main__":
    main(sys.argv[1])
