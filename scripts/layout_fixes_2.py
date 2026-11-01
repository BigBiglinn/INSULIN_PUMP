"""Layout-only fixes, session 2 (1 Nov 2026), applied on top of commit ab69cdf.

  1. Dead-end stub clean-up with the corrected end-point test (pcbcheck.dangling now requires the
     track END POINT to lie in other same-net copper, as KiCad does; the 31 Oct version accepted a
     0.09 mm proximity and missed 3 dangling track ends).
  2. ENC_VCC   JP701.2 -> C701.1 / J705.3 group.
  3. ENC_I     J705.1 -> D709.1 / R710.2 group.
  4. RS485     R714 (DNP 120 R termination, value/status unchanged) moved from the PMD401 resistor row
               to beside J704/U701; its 20 mm RS485_A stub removed; RS485_A and RS485_B joined there.
  5. +3V3      R302.2 (FLY_PGOOD pull-up) group -> main +3V3 network.
  6. Zone fills re-clipped around every new / moved item.

No schematic, value, footprint or net change. Results are pcbcheck.py results, NOT kicad-cli.
Usage: python3 scripts/layout_fixes_2.py [--src BOARD] [--out BOARD] [--log FILE]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout_fixes as LF  # noqa: E402
from pcbcheck import BOARD, connectivity, dangling, short, unconnected  # noqa: E402
from pcbedit import Session, uuid_of  # noqa: E402

log = LF.log


def pairs(S):
    return sum(len(v) - 1 for v in unconnected(S.b).values())


def group_of(S, ref, num):
    return LF.comp_split(S, ref, num)


def step_rs485(S):
    """Move R714 next to J704 and connect both bus lines there."""
    b = S.b
    # the RS485_A run that only feeds R714.1 (R714.1 -> down x=185.7 -> under U701 -> U701.6)
    r714a = b.pads("R714", "1")[0]
    a_net = r714a.net
    chain = []
    frontier = [r714a]
    seen = {id(r714a)}
    u7016 = b.pads("U701", "6")[0]
    while frontier:
        cur = frontier.pop()
        for o in b.items:
            if id(o) in seen or o.net != a_net or o.kind not in ("track",):
                continue
            if o.geom.intersects(cur.geom) and set(o.layers) & set(cur.layers):
                seen.add(id(o))
                if o.geom.intersects(u7016.geom):      # stop at the transceiver pin
                    chain.append(o)
                    continue
                chain.append(o)
                frontier.append(o)
    log(f"step RS485: removing the {len(chain)}-segment RS485_A stub R714.1 -> U701.6 "
        f"({sum(o.geom.length / 2 for o in chain):.0f} mm of copper outline/2)")
    S.remove(chain, "RS485_A stub to old R714 position")
    best = None
    snap = S.snapshot()
    for rot in (90, 270, 0, 180):
        for x in [196.0 + 0.5 * i for i in range(14)]:
            for y in [124.0 + 0.5 * i for i in range(22)]:
                S.restore(snap)
                S.move("R714", x, y, rot)
                if S.b.courtyard_overlaps({"R714"}):
                    continue
                ok = True
                for p in S.b.pads("R714"):
                    for o in S.b.items:
                        if o.kind == "zone" or o.net == p.net or (o.kind == "pad" and o.ref == "R714"):
                            continue
                        if set(o.layers) & set(p.layers) and p.geom.distance(o.geom) < 0.35:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    continue
                pa, pb = S.b.pads("R714", "1")[0], S.b.pads("R714", "2")[0]
                ga, _ = group_of(S, "U701", "6")
                gb, _ = group_of(S, "U701", "7")
                d = min(pa.geom.distance(i.geom) for i in ga if i.kind != "zone") + \
                    min(pb.geom.distance(i.geom) for i in gb if i.kind != "zone") + 0.05 * abs(x - 203)
                if best is None or d < best[0]:
                    best = (d, x, y, rot)
    S.restore(snap)
    if best is None:
        log("  R714: no free position next to J704/U701 - RS485_B left unconnected")
        return
    _, x, y, rot = best
    S.move("R714", x, y, rot)
    log(f"  R714 -> ({x:.2f}, {y:.2f}, {rot} deg) between U701 and J704 (DNP, value 120R unchanged)")
    W = (186, 120, 208, 136)
    a, rest = group_of(S, "R714", "1")
    LF.routed(S, "RS485_A (R714.1 -> U701.6/J704.3)", a, rest, win=W)
    a, rest = group_of(S, "R714", "2")
    LF.routed(S, "RS485_B (R714.2 -> U701.7/J704.2)", a, rest, win=W)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=BOARD)
    ap.add_argument("--out", default=BOARD)
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    S = Session(a.src)
    base = {uuid_of(i) for i in S.b.items if i.kind in ("track", "via")}
    log(f"start: {pairs(S)} unconnected pairs, {len(dangling(S.b))} dangling items (corrected test)")
    LF.step_prune_dangling(S)
    log(f"  -> {pairs(S)} unconnected pairs, {len(dangling(S.b))} dangling")

    a_, rest = group_of(S, "JP701", "2")
    LF.routed(S, "ENC_VCC (JP701.2 -> C701.1/J705.3)", a_, rest, w=0.25, win=(166, 100.5, 192, 112))
    log(f"  -> {pairs(S)} unconnected pairs")
    a_, rest = group_of(S, "J705", "1")
    LF.routed(S, "ENC_I (J705.1 -> D709.1/R710.2)", a_, rest, win=(170, 100.5, 209.5, 146))
    log(f"  -> {pairs(S)} unconnected pairs")
    step_rs485(S)
    log(f"  -> {pairs(S)} unconnected pairs")
    a_, rest = group_of(S, "R302", "2")
    LF.routed(S, "+3V3 (R302.2 -> +3V3 network)", a_, rest, w=0.25, win=(140, 140, 172, 172))
    log(f"  -> {pairs(S)} unconnected pairs")

    LF.step_prune_dangling(S)          # anything the reroutes left behind
    moved = ["R714"]
    LF.place_ref(S, "R714")
    stats = S.t.reclip_zones(lambda b, it: (it.kind in ("track", "via") and uuid_of(it) not in base)
                             or (it.kind == "pad" and it.ref in moved))
    for x in stats:
        log("  zone re-clip: " + x)
    S.t.save(a.out)
    log(f"end: {pairs(S)} unconnected pairs, {len(dangling(S.b))} dangling; saved {a.out}")
    if a.log:
        open(a.log, "w", encoding="utf8", newline="\r\n").write("\n".join(LF.LOG) + "\n")


if __name__ == "__main__":
    main()
