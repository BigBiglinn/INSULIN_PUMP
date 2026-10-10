"""Read-only: for each unconnected pair in the DRC JSON, list foreign copper crossing the straight
corridor between its endpoints on F.Cu/B.Cu. Does not modify the board.

Run with KiCad's Python:  python.exe -I scripts/unrouted_corridors.py > validation/logs/unrouted_corridors.txt
"""
import json, math, os, sys
import pcbnew
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, "hardware", "kicad", "pump_v2.kicad_pcb")
DRC = os.path.join(ROOT, "validation", "drc", "pump_v2-drc.json")
b = pcbnew.LoadBoard(BOARD)
d = json.load(open(DRC, encoding="utf8"))

def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def seg_seg(a, b_, c, d_):
    # min distance between two segments (sampled, adequate for reporting)
    n = 20
    best = 1e9
    for i in range(n + 1):
        t = i / n
        px, py = a[0] + (b_[0] - a[0]) * t, a[1] + (b_[1] - a[1]) * t
        best = min(best, seg_dist(px, py, *c, *d_))
        px, py = c[0] + (d_[0] - c[0]) * t, c[1] + (d_[1] - c[1]) * t
        best = min(best, seg_dist(px, py, *a, *b_))
    return best

mm = pcbnew.ToMM
for u in d["unconnected_items"]:
    it = u["items"]
    desc = it[0]["description"]
    net = desc[desc.find("[") + 1:desc.find("]")]
    A = (it[0]["pos"]["x"], it[0]["pos"]["y"]); B = (it[1]["pos"]["x"], it[1]["pos"]["y"])
    corr = 0.6
    res = {}
    for lay, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
        hits = Counter()
        for t in b.GetTracks():
            if t.GetNetname() == net:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                p = t.GetPosition()
                if seg_dist(mm(p.x), mm(p.y), *A, *B) < corr:
                    hits["via:" + (t.GetNetname().split("/")[-1] or "-")] += 1
            elif t.IsOnLayer(lid):
                s, e = t.GetStart(), t.GetEnd()
                if seg_seg(A, B, (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))) < corr + mm(t.GetWidth()) / 2:
                    hits["trk:" + (t.GetNetname().split("/")[-1] or "-")] += 1
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == net or not p.IsOnLayer(lid):
                    continue
                q = p.GetPosition()
                r = max(mm(p.GetSize(lid).x), mm(p.GetSize(lid).y)) / 2
                if seg_dist(mm(q.x), mm(q.y), *A, *B) < corr + r:
                    hits["pad:" + fp.GetReference()] += 1
        res[lay] = hits
    print(f"== {net.split('/')[-1]}  {desc[:60]}  ->  {it[1]['description'][:60]}")
    print(f"   A=({A[0]:.1f},{A[1]:.1f}) B=({B[0]:.1f},{B[1]:.1f}) len={math.hypot(A[0]-B[0],A[1]-B[1]):.1f}")
    for lay in ("F", "B"):
        h = res[lay]
        pads = sorted({k[4:] for k in h if k.startswith("pad:")})
        trks = sorted({k[4:] for k in h if k.startswith("trk:")})
        vias = sum(v for k, v in h.items() if k.startswith("via:"))
        print(f"   {lay}.Cu: pads of {pads[:12]}{'...' if len(pads)>12 else ''}; tracks of {len(trks)} nets {trks[:10]}; vias {vias}")
