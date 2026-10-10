"""Compare the current PCB against a baseline PCB after a placement-only change (read-only).

Run with KiCad's Python:
  python.exe -I scripts/compare_placement.py BASE_PCB BASE_DRC_JSON CUR_PCB CUR_DRC_JSON MOVES_JSON MOVE_LOG OUT_UNROUTED

Reports (stdout): footprint positions (moved vs. everything else unchanged), copper outside the ripped
nets unchanged, zone outlines unchanged, loop metrics, pad-to-pad clearance margins of moved parts,
DRC violation counts and dangling items before/after. Writes the classified unconnected list to
OUT_UNROUTED. DRC JSON files come from: kicad-cli pcb drc --format json --severity-all --schematic-parity --refill-zones
"""
import json
import math
import os
import re
import sys
from collections import Counter

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from eval_placement import LOOPS, TRACKED, loop_len, mst, pads_by_net, short  # noqa: E402

# Group A: nets whose wiring waits for the ST WBA55 documents (BLOCKER_RESOLUTION_REPORT.md section 1)
PLACEHOLDER = {"HSE_IN", "HSE_OUT", "LSE_IN", "RF_MCU", "WBA_VDD11", "WBA_VDDANA", "WBA_VDDRF", "WBA_VDDRFPA"}
# Group B: net between DNP placeholder parts only (48 V output switch, not designed)
DNP_ONLY = {"SW48_GATE"}
HV = ("+48V_RAW", "+48V_MOT", "FLY_SEC")
mm = pcbnew.ToMM


def fps(b):
    return {f.GetReference(): f for f in b.GetFootprints()}


def track_set(b, skip):
    out = set()
    for t in b.GetTracks():
        n = short(t.GetNetname())
        if n in skip:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            out.add(("via", n, p.x, p.y))
        else:
            s, e = t.GetStart(), t.GetEnd()
            out.add(("trk", n, t.GetLayer(), min((s.x, s.y), (e.x, e.y)), max((s.x, s.y), (e.x, e.y)), t.GetWidth()))
    return out


def zone_set(b):
    out = set()
    for z in b.Zones():
        o = z.Outline()
        pts = tuple((o.CVertex(i).x, o.CVertex(i).y) for i in range(o.TotalVertices()))
        out.add((short(z.GetNetname()), z.GetLayer(), z.GetAssignedPriority(), pts))
    return out


def net_of(desc):
    m = re.search(r"\[([^\]]*)\]", desc)
    return short(m.group(1)) if m else "?"


def classify(drc, ripped):
    groups = {"A": [], "B": [], "C": [], "D": []}
    for u in drc["unconnected_items"]:
        a, c = u["items"][0], u["items"][1]
        n = net_of(a["description"])
        gap = math.dist((a["pos"]["x"], a["pos"]["y"]), (c["pos"]["x"], c["pos"]["y"]))
        k = "A" if n in PLACEHOLDER else "B" if n in DNP_ONLY else "D" if n in ripped else "C"
        groups[k].append((n, gap, a["description"][:70], c["description"][:70]))
    return groups


def pad_margin(b, ref):
    """Smallest edge-to-edge copper gap from ref's pads to any other-net pad (same layer), and the rule."""
    best = None
    lyrs = (pcbnew.F_Cu, pcbnew.B_Cu)
    mine = list(fps(b)[ref].Pads())
    for f in b.GetFootprints():
        for q in f.Pads():
            for p in mine:
                if q is p or (p.GetNetCode() == q.GetNetCode() and p.GetNetCode() > 0) or f.GetReference() == ref and p.GetNumber() == q.GetNumber():
                    continue
                if (p.GetPosition() - q.GetPosition()).EuclideanNorm() > pcbnew.FromMM(12):
                    continue
                for l in lyrs:
                    if p.IsOnLayer(l) and q.IsOnLayer(l):
                        sp, sq = p.GetEffectiveShape(l), q.GetEffectiveShape(l)
                        # binary search the largest clearance at which the shapes do not collide
                        lo, hi = 0, pcbnew.FromMM(3)
                        if sp.Collide(sq, 0):
                            gap = 0
                        elif not sp.Collide(sq, hi):
                            continue
                        else:
                            while hi - lo > pcbnew.FromMM(0.01):
                                mid = (lo + hi) // 2
                                lo, hi = (lo, mid) if sp.Collide(sq, mid) else (mid, hi)
                            gap = lo
                        hv = short(p.GetNetname()).endswith(HV) or short(q.GetNetname()).endswith(HV)
                        rule = 0.6 if hv else 0.2
                        key = mm(gap) - rule
                        if best is None or key < best[0]:
                            best = (key, mm(gap), rule, f"{ref}.{p.GetNumber()}[{short(p.GetNetname())}]",
                                    f"{f.GetReference()}.{q.GetNumber()}[{short(q.GetNetname())}]")
    return best


def main(base_pcb, base_drc, cur_pcb, cur_drc, moves_json, move_log, out_unrouted):
    moves = json.load(open(moves_json, encoding="utf8"))
    log = open(move_log, encoding="utf8").read()
    ripped = set()
    for m in re.finditer(r"\[([^\]]*)\]", "\n".join(l for l in log.splitlines() if "ripped" in l)):
        ripped |= {x.strip().strip("'") for x in m.group(1).split(",") if x.strip()}
    b0, b1 = pcbnew.LoadBoard(base_pcb), pcbnew.LoadBoard(cur_pcb)
    d0, d1 = json.load(open(base_drc, encoding="utf8")), json.load(open(cur_drc, encoding="utf8"))
    f0, f1 = fps(b0), fps(b1)

    print("## 1. Footprint positions")
    for r in moves:
        a, c = f0[r], f1[r]
        print(f"  {r:6s} ({mm(a.GetPosition().x):7.2f},{mm(a.GetPosition().y):7.2f},{a.GetOrientationDegrees():4.0f})"
              f" -> ({mm(c.GetPosition().x):7.2f},{mm(c.GetPosition().y):7.2f},{c.GetOrientationDegrees():4.0f})"
              f"  side {'B' if c.IsFlipped() else 'F'}")
    changed = [r for r in f0 if r not in moves and (f0[r].GetPosition() != f1[r].GetPosition()
               or f0[r].GetOrientationDegrees() != f1[r].GetOrientationDegrees() or f0[r].IsFlipped() != f1[r].IsFlipped())]
    print(f"  footprints not in the move list that changed: {changed or 'none'} (of {len(f0) - len(moves)})")
    print(f"  footprint count {len(f0)} -> {len(f1)}")

    print("## 2. Copper and zones outside the ripped nets")
    s0, s1 = track_set(b0, ripped), track_set(b1, ripped)
    print(f"  ripped nets ({len(ripped)}): {sorted(ripped)}")
    print(f"  items on all other nets: baseline {len(s0)}, now {len(s1)}; removed {len(s0 - s1)}, added {len(s1 - s0)}")
    rem = Counter((x[0], x[1]) for x in s0 - s1)
    add = Counter((x[0], x[1]) for x in s1 - s0)
    print(f"    removed by net: {dict(rem)}")
    print(f"    added by net:   {dict(add)}")
    print(f"  zone outlines identical: {zone_set(b0) == zone_set(b1)}")
    u = f1["U501"]
    box = u.GetBoundingBox(False)
    box.Inflate(pcbnew.FromMM(12))
    def in_box(b):
        return sorted(r for r, f in fps(b).items() if box.Contains(f.GetPosition()))
    print(f"  WBA55 region (U501 bbox + 12 mm): parts inside baseline {len(in_box(b0))}, now {len(in_box(b1))}; "
          f"moved parts now inside: {sorted(set(in_box(b1)) & set(moves)) or 'none'}")
    near = lambda b: {x for x in track_set(b, set()) if x[0] == "via" and box.Contains(pcbnew.VECTOR2I(x[2], x[3]))
                      or x[0] == "trk" and box.Contains(pcbnew.VECTOR2I(*x[3]))}
    n0, n1 = near(b0), near(b1)
    print(f"  copper items starting inside that region: baseline {len(n0)}, now {len(n1)}; removed {len(n0 - n1)} "
          f"(nets {sorted({x[1] for x in n0 - n1})}), added {len(n1 - n0)} (nets {sorted({x[1] for x in n1 - n0})})")

    print("## 3. Loop metrics (straight pad-to-pad, mm) and airwire MST")
    for k, ch in LOOPS.items():
        print(f"  {k:58s} {loop_len(b0, ch):6.1f} -> {loop_len(b1, ch):6.1f}")
    p0, p1 = pads_by_net(b0), pads_by_net(b1)
    t0 = t1 = 0
    for n in TRACKED:
        a, c = mst(p0.get(n, [])), mst(p1.get(n, []))
        t0, t1 = t0 + a, t1 + c
        if abs(a - c) > 0.05:
            print(f"  {n:12s} {a:7.1f} -> {c:7.1f} ({c - a:+.1f})")
    print(f"  TOTAL tracked {t0:.1f} -> {t1:.1f} ({(t1 - t0) / t0 * 100:+.0f} %)")

    print("## 4. Pad-to-pad copper margin of moved parts (gap - rule; rule 0.6 mm if either net is HV48, else 0.2)")
    for r in moves:
        m = pad_margin(b1, r)
        if m:
            print(f"  {r:6s} min gap {m[1]:5.2f} mm (rule {m[2]}) margin {m[0]:+5.2f}  {m[3]} <-> {m[4]}")

    print("## 5. DRC (kicad-cli, --schematic-parity --refill-zones)")
    c0, c1 = Counter(v["type"] for v in d0["violations"]), Counter(v["type"] for v in d1["violations"])
    for k in sorted(set(c0) | set(c1)):
        print(f"  {k:32s} {c0[k]:4d} -> {c1[k]:4d}")
    print(f"  unconnected_items                {len(d0['unconnected_items']):4d} -> {len(d1['unconnected_items']):4d}")
    print(f"  schematic parity issues          {len(d0.get('schematic_parity', [])):4d} -> {len(d1.get('schematic_parity', [])):4d}")
    dang = lambda d: sorted(f"{v['type']}: {v['items'][0]['description'][:60]}" for v in d["violations"] if "dangling" in v["type"])
    print("  dangling before:", *dang(d0), sep="\n    ")
    print("  dangling now:", *dang(d1), sep="\n    ")

    g = classify(d1, ripped)
    g0 = classify(d0, ripped)
    names = {"A": "Placeholder nets awaiting the ST WBA55 documents (unchanged by placement)",
             "B": "Net between DNP placeholder parts only (48 V output switch, M8 not applied)",
             "C": "GENUINE connections still to route, on nets NOT touched by the placement change",
             "D": "Connections OPENED by the placement rip-up (ripped nets), pending the staged re-route"}
    lines = [f"Unrouted connections - kicad-cli 10.0.3 DRC --schematic-parity --refill-zones, branch placement-opt,",
             f"after the approved v2 placement change (validation/placement/moves_applied.json). Board NOT fully connected.",
             f"Total unconnected items: {len(d1['unconnected_items'])} (baseline e8d141c: {len(d0['unconnected_items'])}).",
             "Groups: " + ", ".join(f"{k}={len(g[k])} (baseline {len(g0[k])})" for k in "ABCD"),
             "Baseline D items are the baseline gaps on nets that have since been ripped (they were group C there).",
             "KiCad connectivity includes filled zones, so plane connections are already counted.", ""]
    for k in "ABCD":
        lines.append(f"{k}. {names[k]}: {len(g[k])}")
        for n, gap, a, c in sorted(g[k]):
            lines.append(f"  {n:14s} gap {gap:5.1f} mm : {a}  <->  {c}")
        lines.append("")
    open(out_unrouted, "w", encoding="utf8").write("\n".join(lines))
    print("## 6. Unconnected classification")
    print("  " + lines[3])
    print("  written:", out_unrouted)


if __name__ == "__main__":
    main(*sys.argv[1:8])
