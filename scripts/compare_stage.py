"""Compare a routing stage against its checkpoint (read-only).

Run with KiCad's Python:
  python.exe -I scripts/compare_stage.py BASE_PCB BASE_DRC_JSON CUR_PCB CUR_DRC_JSON STAGE_NETS

STAGE_NETS: comma-separated short net names the stage was allowed to change (including plane nets
whose stubs it moved). Reports DRC violation counts, every unconnected pair closed or newly opened,
copper changes per net, and flags any change on a net outside STAGE_NETS.
"""
import json
import re
import sys
from collections import Counter

import pcbnew


def short(n):
    return n.split("/")[-1]


def items(b):
    out = set()
    for t in b.GetTracks():
        n = short(t.GetNetname())
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            out.add((n, "via", p.x, p.y, t.GetWidth(pcbnew.F_Cu), t.GetDrill()))
        else:
            s, e = t.GetStart(), t.GetEnd()
            out.add((n, "trk", t.GetLayer(), min((s.x, s.y), (e.x, e.y)), max((s.x, s.y), (e.x, e.y)), t.GetWidth()))
    return out


def pair_key(u):
    def end(d):
        m = re.search(r"Pad (\S+) \[([^\]]*)\] of (\S+)", d)
        if m:
            return f"{m.group(3)}.{m.group(1)}"
        m = re.match(r"(Track|Via) \[([^\]]*)\]", d)
        return f"{m.group(1)}" if m else d[:20]
    a, c = u["items"]
    net = short(re.search(r"\[([^\]]*)\]", a["description"]).group(1))
    return (net, tuple(sorted((end(a["description"]), end(c["description"])))))


def main(base_pcb, base_drc, cur_pcb, cur_drc, stage):
    stage = set(stage.split(","))
    d0, d1 = json.load(open(base_drc, encoding="utf8")), json.load(open(cur_drc, encoding="utf8"))
    c0, c1 = Counter(v["type"] for v in d0["violations"]), Counter(v["type"] for v in d1["violations"])
    print("## DRC violations (checkpoint -> now)")
    for k in sorted(set(c0) | set(c1)):
        print(f"  {k:32s} {c0[k]:4d} -> {c1[k]:4d}{'   CHANGED' if c0[k] != c1[k] else ''}")
    print(f"  unconnected_items                {len(d0['unconnected_items']):4d} -> {len(d1['unconnected_items']):4d}")
    print(f"  schematic parity                 {len(d0.get('schematic_parity', [])):4d} -> {len(d1.get('schematic_parity', [])):4d}")
    for t in ("via_dangling", "track_dangling"):
        a = sorted(v["items"][0]["description"][:60] for v in d0["violations"] if v["type"] == t)
        b = sorted(v["items"][0]["description"][:60] for v in d1["violations"] if v["type"] == t)
        if a != b:
            print(f"  {t} changed: removed {sorted(set(a) - set(b))}, added {sorted(set(b) - set(a))}")
    p0, p1 = Counter(pair_key(u) for u in d0["unconnected_items"]), Counter(pair_key(u) for u in d1["unconnected_items"])
    print("## Unconnected pairs closed")
    for k in sorted(p0 - p1):
        print(f"  {k[0]:12s} {k[1][0]} <-> {k[1][1]}")
    print("## Unconnected pairs that are new or re-paired")
    for k in sorted(p1 - p0):
        print(f"  {k[0]:12s} {k[1][0]} <-> {k[1][1]}")
    i0, i1 = items(pcbnew.LoadBoard(base_pcb)), items(pcbnew.LoadBoard(cur_pcb))
    rem, add = Counter(x[0] for x in i0 - i1), Counter(x[0] for x in i1 - i0)
    print("## Copper changes by net (removed / added items)")
    for n in sorted(set(rem) | set(add)):
        flag = "" if n in stage else "   <-- OUTSIDE STAGE NETS"
        print(f"  {n:12s} -{rem[n]:3d} +{add[n]:3d}{flag}")
    outside = [n for n in set(rem) | set(add) if n not in stage]
    print("nets changed outside the stage list:", sorted(outside) or "none")


if __name__ == "__main__":
    main(*sys.argv[1:6])
