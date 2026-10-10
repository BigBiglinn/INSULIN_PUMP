"""Evaluate a placement proposal WITHOUT touching the project PCB.

Copies the board to OUT_DIR, deletes all tracks/vias there (placement-only view), applies the moves in
MOVES_JSON, saves it, and reports:
  - per-net minimum-spanning-tree airwire length (Euclidean, pad centres) before vs after, for the nets
    touched by the moves and for the tracked group-C nets;
  - named loop metrics for the flyback stage;
  - pad positions of moved parts (to check pin orientation);
Then run kicad-cli DRC on the scratch copy separately to check courtyards / pad clearances.

Run with KiCad's Python:
  python.exe -I scripts/eval_placement.py BOARD MOVES_JSON OUT_DIR
MOVES_JSON: {"REF": [x, y, rot_deg], ...}
"""
import json
import math
import os
import sys

import pcbnew

TRACKED = ["+48V_MOT", "FLY_SS", "FLY_PGOOD", "CON_SUP_TX", "CON_SUP_RX", "CON_MAIN_TX", "ENC_A_S", "ENC_B_S",
           "ENC_A", "ENC_B", "ENC_VCC", "PMD_5V", "VBAT_SENSE", "SW48_GATE", "SW48_DRV", "+48V_RAW", "FLY_SW",
           "FLY_CLAMP", "FLY_SEC", "FLY_SNUB", "FLY_GATE", "FLY_CS", "FLY_FB", "FLY_RT", "FLY_COMP", "FLY_COMP_RC",
           "FLY_EN", "HB_M2S", "HB_S2M", "SUP_VETO", "SUP_PARK", "SUP_SWDIO", "SUP_SWCLK", "SUP_NRST", "LED_SUP"]


def short(n):
    return n.split("/")[-1]


def mm(v):
    return pcbnew.ToMM(v)


def pads_by_net(b):
    out = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            n = short(p.GetNetname())
            if not n or n.startswith("unconnected"):
                continue
            q = p.GetPosition()
            out.setdefault(n, []).append((mm(q.x), mm(q.y), fp.GetReference() + "." + p.GetNumber()))
    return out


def mst(pts):
    pts = list({(round(x, 3), round(y, 3)) for x, y, _ in pts})
    if len(pts) < 2:
        return 0.0
    inside = {0}
    best = {i: math.dist(pts[0], pts[i]) for i in range(1, len(pts))}
    total = 0.0
    while best:
        j = min(best, key=best.get)
        total += best.pop(j)
        inside.add(j)
        for k in best:
            best[k] = min(best[k], math.dist(pts[j], pts[k]))
    return total


def fpmap(b):
    return {fp.GetReference(): fp for fp in b.GetFootprints()}


def pad(b, ref, num):
    for p in fpmap(b)[ref].Pads():
        if p.GetNumber() == num:
            q = p.GetPosition()
            return (mm(q.x), mm(q.y))
    raise KeyError(ref + "." + num)


def loop_len(b, chain):
    pts = [pad(b, r, n) for r, n in chain]
    return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))


LOOPS = {
    # straight-line path lengths between consecutive pads (indicative, not routed length)
    "clamp: Q301.D-D302.A, D302.K-C308, C308.VBAT-T301.1": [("Q301", "5"), ("D302", "2"), ("D302", "1"), ("C308", "1"),
                                                            ("C308", "2"), ("T301", "1")],
    "FLY_SW node: Q301.D-T301.2": [("Q301", "5"), ("T301", "2")],
    "secondary: T301.4-D301.A, D301.K-C309.+, C309.GND-T301.3": [("T301", "4"), ("D301", "2"), ("D301", "1"),
                                                                ("C309", "1"), ("C309", "2"), ("T301", "3")],
    "gate: U301.GATE-Q301.G": [("U301", "3"), ("Q301", "4")],
    "CS: U301.CS-R305.1": [("U301", "5"), ("R305", "1")],
    "VCC cap: U301.VBAT-C304": [("U301", "1"), ("C304", "1")],
    "SS: U301.SS-C305": [("U301", "9"), ("C305", "1")],
    "+48V_MOT: R311.2-J703.2": [("R311", "2"), ("J703", "2")],
    "+48V_MOT: C702.1-J703.2": [("C702", "1"), ("J703", "2")],
}


def report(b):
    nets = pads_by_net(b)
    return {n: mst(nets.get(n, [])) for n in TRACKED}, {k: loop_len(b, v) for k, v in LOOPS.items()}


def main(board, moves_json, out_dir):
    moves = json.load(open(moves_json, encoding="utf8"))
    base = pcbnew.LoadBoard(board)
    m0, l0 = report(base)
    b = pcbnew.LoadBoard(board)
    fps = fpmap(b)
    for ref, (x, y, rot) in moves.items():
        fp = fps[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    for t in list(b.GetTracks()):
        b.Delete(t)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "proposal.kicad_pcb")
    pcbnew.SaveBoard(out, b)
    m1, l1 = report(b)
    print("## airwire MST length (mm), base -> proposal")
    for n in TRACKED:
        if abs(m0[n] - m1[n]) > 0.05:
            print(f"  {n:12s} {m0[n]:7.1f} -> {m1[n]:7.1f}  ({m1[n] - m0[n]:+.1f})")
    print(f"  TOTAL tracked {sum(m0.values()):.1f} -> {sum(m1.values()):.1f}")
    print("## loop path metrics (straight pad-to-pad, mm), base -> proposal")
    for k in LOOPS:
        print(f"  {k:58s} {l0[k]:6.1f} -> {l1[k]:6.1f}")
    print("## moved parts: pads")
    for ref in moves:
        fp = fps[ref]
        print("  " + ref + " " + " ".join(f"{p.GetNumber()}:{short(p.GetNetname())}@({mm(p.GetPosition().x):.2f},{mm(p.GetPosition().y):.2f})"
                                          for p in fp.Pads() if p.GetNumber()))
    print("saved", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
