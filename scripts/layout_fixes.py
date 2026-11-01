"""Layout-only fixes of 31 Oct 2026 for pump_v2.kicad_pcb (no schematic, part or value changes).

Applies, in order, to the board at the checkpoint tag `checkpoint/pre-layout-fixes-2026-10-31`:
  1. +48V_MOT: R311.2 -> J703.2 on F.Cu and C702.1 -> that route on B.Cu (HV48 0.4 mm track).
  2. U301 soft-start: C305 moved north of U301; FLY_SS routed pin 9 -> C305.1; AGND pin 7 tied to the
     exposed pad (SNVSB75E 10.5.1); FLY_FB / FLY_RT / FLY_PGOOD escapes re-routed to make room.
  3. TP302 moved from the J703 area onto the FLY_PGOOD trace beside U301/R302.
  4. Router-found connections (pcbroute.py, deterministic A*), each accepted only with zero
     clearance violations: see ROUTES below.
  5. J503 console header and dangling via / track clean-up, silkscreen fixes.
  6. Stored zone fills re-clipped around every new or moved item (fills must be refilled in KiCad).

Every step is checked with pcbcheck.py (an approximation of KiCad DRC calibrated on the baseline).
KiCad's own DRC/ERC could NOT be run in the session that produced this (see the handover notes).

Usage: python3 scripts/layout_fixes.py [--out PATH] [--only N]
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import box  # noqa: E402

from pcbcheck import BOARD, clearance_violations, short, unconnected  # noqa: E402
from pcbedit import Session  # noqa: E402
from pcbroute import route  # noqa: E402

LOG = []


def log(msg):
    LOG.append(msg)
    print(msg, flush=True)


def netname(S, sn):
    return next(i.net for i in S.b.items if short(i.net) == sn)


def check_new(S, items, what):
    idx = {i.idx for i in items}
    cv = [v for v in clearance_violations(S.b, only=idx)
          if not ((v[2] is not None and v[2].kind == "zone") or v[1].kind == "zone")]
    if cv:
        for v in cv:
            log(f"  VIOLATION {what}: {v[1].name()}[{short(v[1].net)}] vs "
                f"{v[2].name() if v[2] else 'edge'}[{short(v[2].net) if v[2] else ''}] d={v[3]} req={v[4]}")
        raise SystemExit(f"step '{what}' introduced clearance violations; nothing saved")
    return min_clear(S, items)


def min_clear(S, items):
    best = (9e9, None, None)
    for it in items:
        for o in S.b.items:
            if o.kind == "zone" or o.net == it.net or not set(o.layers) & set(it.layers):
                continue
            if o.kind == "pad" and it.kind == "pad" and o.ref == it.ref:
                continue
            d = it.geom.distance(o.geom)
            if d < best[0]:
                best = (d, it, o)
    return best


def path(S, layer, pts, w, net, out):
    for p0, p1 in zip(pts, pts[1:]):
        out.append(S.seg(layer, p0, p1, w, net))


def move_pad_to(S, ref, x, y, rot=None):
    """Move a footprint so that its (first) pad centre lands on (x, y)."""
    fp = S.b.footprints[ref]
    if rot is not None and rot != fp["rot"]:
        S.move(ref, fp["x"], fp["y"], rot)
        fp = S.b.footprints[ref]
    p = S.b.pads(ref)[0]
    S.move(ref, x - (p.data["c"][0] - fp["x"]), y - (p.data["c"][1] - fp["y"]))


# ----------------------------------------------------------------------------- step 1
def step_48v(S):
    net = "+48V_MOT"
    new = []
    # F.Cu from R311.2 north of D302, down the clear x=200 corridor, entering J703.2 from above so the
    # track end stays >= 0.6 mm (HV48) from the J703.1 GND pad.
    path(S, "F.Cu", [(192.2875, 142.175), (193.95, 140.5), (200.0, 140.5), (200.0, 146.0), (200.6, 146.6),
                     (203.6, 146.6), (204.2, 147.25)], 0.4, net, new)
    # B.Cu from the C702.1 through-hole pad to a via on the vertical above
    path(S, "B.Cu", [(200.0, 145.2), (200.0, 160.5), (196.4987, 164.0)], 0.4, net, new)
    new.append(S.via((200.0, 145.2), net))
    d = check_new(S, new, "+48V_MOT")
    log(f"step 1 +48V_MOT: {len(new)} items, min clearance {d[0]:.3f} mm ({d[1].name()} to {d[2].name()} "
        f"[{short(d[2].net)}]; HV48 rule 0.6 mm)")
    return new


# ----------------------------------------------------------------------------- step 2
def step_soft_start(S):
    b = S.b
    zone = box(164.6, 150.9, 167.0, 155.3)
    rip = [i for i in b.items if i.kind in ("track", "via") and short(i.net) in ("FLY_RT", "FLY_FB", "FLY_PGOOD", "GND")
           and i.geom.intersects(zone) and not (short(i.net) == "GND" and i.kind == "via" and i.data["p"][0] < 165)]
    c305 = [p.geom for p in b.pads("C305")]
    stub = [i for i in b.items if i.kind == "track" and any(i.geom.intersects(g) for g in c305)]
    rip += stub + [i for i in b.items if i.kind == "via" and short(i.net) == "GND"
                   and any(i.geom.intersects(s_.geom) for s_ in stub)]
    log(f"step 2 soft-start: ripped {len(rip)} items (U301 east escapes of FLY_RT/FLY_FB/FLY_PGOOD, AGND via, "
        f"C305 GND stub+via)")
    S.remove(rip, "rip-up for FLY_SS")
    S.move("C305", 164.75, 149.4, 180)
    SS, FB, RT, PG = (netname(S, n) for n in ("FLY_SS", "FLY_FB", "FLY_RT", "FLY_PGOOD"))
    new = []
    path(S, "F.Cu", [(164.95, 153.25), (164.3, 153.25)], 0.25, "GND", new)        # AGND pin 7 -> EP
    path(S, "F.Cu", [(164.95, 152.25), (165.65, 152.25)], 0.2, SS, new)
    new.append(S.via((165.65, 152.25), SS, 0.5, 0.3))
    path(S, "B.Cu", [(165.65, 152.25), (166.5, 151.4), (166.5, 149.4)], 0.2, SS, new)
    new.append(S.via((166.5, 149.4), SS, 0.5, 0.3))
    path(S, "F.Cu", [(166.5, 149.4), (165.525, 149.4)], 0.2, SS, new)
    path(S, "F.Cu", [(163.975, 149.4), (162.9, 149.4)], 0.25, "GND", new)         # CSS ground
    new.append(S.via((162.9, 149.4), "GND"))
    path(S, "F.Cu", [(164.95, 152.75), (165.45, 152.75), (165.45, 154.2), (165.145, 154.505), (163.056, 154.505)],
         0.2, FB, new)
    path(S, "F.Cu", [(164.95, 151.75), (166.15, 151.75), (166.15, 154.55), (165.843, 154.857), (160.618, 154.857)],
         0.2, RT, new)
    path(S, "F.Cu", [(164.95, 151.25), (166.5, 151.25), (166.5, 154.85), (166.141, 155.209), (165.266, 155.209),
                     (162.98, 157.495)], 0.2, PG, new)
    if S.b.courtyard_overlaps({"C305"}):
        raise SystemExit("C305 courtyard overlap")
    d = check_new(S, new + S.b.pads("C305"), "soft-start")
    log(f"step 2: C305 -> (164.75, 149.4, 180 deg); {len(new)} items; min clearance {d[0]:.3f} mm "
        f"({d[1].name()} to {d[2].name()})")
    return new


# ----------------------------------------------------------------------------- step 3
def step_tp302(S):
    PG = netname(S, "FLY_PGOOD")
    move_pad_to(S, "TP302", 165.75, 155.75)
    new = [S.seg("F.Cu", (165.75, 155.75), (165.75, 155.209), 0.2, PG)]
    if S.b.courtyard_overlaps({"TP302"}):
        raise SystemExit("TP302 courtyard overlap")
    d = check_new(S, new + S.b.pads("TP302"), "TP302")
    log(f"step 3 TP302 -> pad at (165.75, 155.75) on the FLY_PGOOD trace; min clearance {d[0]:.3f} mm")
    return new


# ----------------------------------------------------------------------------- router steps
def comp_split(S, pad_ref, pad_num):
    from pcbcheck import connectivity
    p = S.b.pads(pad_ref, pad_num)[0]
    comps = list(connectivity(S.b)[p.net].values())
    for c in comps:
        if any(i is p for i in c):
            return c, [x for cc in comps if cc is not c for x in cc]
    return [p], []


def routed(S, name, src, dst, win=None, w=0.2, via_cost=6.0, grid=0.05, layers=("F.Cu", "B.Cu")):
    r = route(S.b, None, src, dst, win, grid=grid, w=w, layers=layers, via_cost=via_cost)
    if r is None:
        log(f"  {name}: NO ROUTE found (left unconnected)")
        return None
    snap = S.snapshot()
    new = S.apply_route(r, src[0].net, w)
    idx = {i.idx for i in new}
    cv = [v for v in clearance_violations(S.b, only=idx)
          if not ((v[2] is not None and v[2].kind == "zone") or v[1].kind == "zone")]
    if cv:
        S.restore(snap)
        log(f"  {name}: route rejected ({len(cv)} clearance violations) - left unconnected")
        return None
    L = sum(math.dist(a, c) for _, a, c in r[0])
    d = min_clear(S, new)
    log(f"  {name}: routed {L:.1f} mm, {len(r[1])} vias, min clearance {d[0]:.3f} mm ({short(d[2].net)})")
    return new


# ----------------------------------------------------------------------------- step: dangling clean-up
def step_prune_dangling(S):
    """Leaf-prune the dead-end autorouter stubs that end in a dangling via or track: inside each copper
    group that contains a dangling item, repeatedly delete tracks/vias touching at most one other
    same-net item. Pads and zone fills are never removed, so no connection is lost."""
    from shapely.strtree import STRtree
    from pcbcheck import connectivity, dangling
    removed = []
    for _ in range(3):
        dg = dangling(S.b)
        if not dg:
            break
        groups = connectivity(S.b)
        comp_of = {}
        for net, cs in groups.items():
            for c in cs.values():
                for i in c:
                    comp_of[id(i)] = c
        targets = []
        for x in dg:
            c = comp_of.get(id(x[1]))
            if c is not None and all(c is not t for t in targets):
                targets.append(c)
        kill = []
        for c in targets:
            alive = list(c)
            while True:
                tree = STRtree([i.geom for i in alive])
                drop = []
                for i in alive:
                    if i.kind not in ("track", "via"):
                        continue
                    nb = set()
                    for j in tree.query(i.geom, predicate="intersects"):
                        o = alive[j]
                        if o is not i and set(o.layers) & set(i.layers):
                            nb.add(id(o))
                    if i.kind == "track" and len(nb) >= 1:
                        # a track needs something at BOTH ends
                        ends = 0
                        for e in (i.data["p0"], i.data["p1"]):
                            from shapely.geometry import Point
                            pe = Point(e).buffer(1e-3)   # end point must lie in other same-net copper
                            if any(alive[j] is not i and pe.intersects(alive[j].geom) and set(alive[j].layers) & set(i.layers)
                                   for j in tree.query(pe)):
                                ends += 1
                        if ends < 2:
                            drop.append(i)
                    elif i.kind == "via":
                        lays = set()
                        for j in tree.query(i.geom, predicate="intersects"):
                            o = alive[j]
                            if o is not i:
                                lays |= set(o.layers) & set(i.layers)
                        if len(lays) <= 1:
                            drop.append(i)
                    elif not nb:
                        drop.append(i)
                if not drop:
                    break
                kill += drop
                alive = [i for i in alive if all(i is not d for d in drop)]
        if not kill:
            break
        for k in kill:
            loc = k.data["p"] if k.kind == "via" else (k.data["p0"], k.data["p1"])
            removed.append(f"{short(k.net)} {k.kind} {loc}")
        S.remove(kill, "dead-end stub")
    log(f"step dangling clean-up: removed {len(removed)} dead-end items")
    for r in removed:
        log("    " + r)
    return removed


# ----------------------------------------------------------------------------- step: silkscreen
def _silk_model(S):
    import tempfile
    import pcbsilk
    fd, tmp = tempfile.mkstemp(suffix=".kicad_pcb")
    os.close(fd)
    S.t.save(tmp)
    items, masks, edge = pcbsilk.load(tmp)
    os.remove(tmp)
    return items, masks, edge


def place_ref(S, ref, prefer=None):
    """Choose a reference-text position clear of other silk, of every pad opening (+0.1 mm) and of the
    board edge (0.3 mm), using a conservative text box (pcbsilk, height x1.3). Text angle is kept."""
    import pcbsilk
    from pcbcheck import rot as krot
    items, masks, edge = _silk_model(S)
    fp = S.b.footprints[ref]
    X, Y, R = fp["x"], fp["y"], fp["rot"]
    s, e = S.t.footprint_span(ref)
    import re
    m = re.search(r'\(property "Reference" "([^"]*)"\n\t\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', S.t.txt[s:e])
    txt, ang = m.group(1), float(m.group(4) or 0) % 360
    if ang >= 180:                      # keep text upright (a 180 deg part rotation turns it upside down)
        ang -= 180
    others = [g for (o, k, g) in items if not (o == ref and k == "ref")]
    own_lines = [g for (o, k, g) in items if o == ref and k == "line"]
    mk = [g.buffer(0.1) for (o, g) in masks]
    inner = edge.buffer(-0.3)
    cy = fp["crtyd"]
    best = None
    cands = []
    bx = cy.bounds
    for dx in [i * 0.25 for i in range(-24, 25)]:
        for dy in [i * 0.25 for i in range(-24, 25)]:
            cands.append((X + dx, Y + dy))
    for (x, y) in cands:
        g = pcbsilk.text_box(txt, x, y, ang, 1.0, 1.3, 0.15)
        if not inner.contains(g) or any(g.intersects(o) for o in others) or any(g.intersects(o) for o in mk):
            continue
        d = cy.distance(g) + (0 if prefer is None else 0.3 * math.dist((x, y), prefer))
        if best is None or d < best[0]:
            best = (d, x, y)
    if best is None:
        log(f"  silk {ref}: no clear position found, reference left where it was")
        return False
    lx, ly = krot(best[1] - X, best[2] - Y, -R)
    S.t.set_fp_text(ref, "Reference", round(lx, 3), round(ly, 3), ang)
    log(f"  silk {ref}: reference text -> ({best[1]:.2f}, {best[2]:.2f})")
    return True


def step_silk(S, refs):
    import re
    for txt in ("BENCH ONLY - WATER/SALINE - NEVER ON A PERSON OR ANIMAL",
                "PIEZO INSULIN PUMP v2 REV B - HANDOVER PROTOTYPE, NOT FAB-APPROVED"):
        m = re.search(r'\(gr_text "' + re.escape(txt) + r'"\n\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', S.t.txt)
        y = m.group(2)
        S.t.txt = S.t.txt[:m.start(1)] + "155" + S.t.txt[m.end(1):]           # centre of the board
        k = S.t.txt.index('(gr_text "' + txt + '"')
        e = S.t.txt.index("(justify left)", k)
        S.t.txt = S.t.txt[:e] + "(justify mirror)" + S.t.txt[e + len("(justify left)"):]
        log(f"  silk: B.SilkS text '{txt[:24]}...' mirrored, centred at x=155, y={y} (wording unchanged)")
    for r in refs:
        place_ref(S, r)


def step_console(S):
    """Move J503 (4-pin console header: GND, CON_MAIN_TX, CON_SUP_TX, CON_SUP_RX) from the top edge to the
    free area between the two MCUs, then route its three signal nets."""
    mtx = [i for i in S.b.items if i.kind == "track" and short(i.net) == "CON_MAIN_TX" and i.layers[0] == "B.Cu"]
    S.remove(mtx, "CON_MAIN_TX run to the old J503 position")
    log(f"step console: ripped {len(mtx)} B.Cu segments of CON_MAIN_TX (U501-side escape and via kept)")
    S.move("J503", 133.5, 147.5)
    if S.b.courtyard_overlaps({"J503"}):
        raise SystemExit("J503 courtyard overlap")
    d = check_new(S, S.b.pads("J503"), "J503 placement")
    log(f"  J503 -> pin 1 at (133.5, 147.5), same orientation; pad min clearance {d[0]:.3f} mm")
    W = (128, 140, 162, 168)
    for ref, num, name, win in (("U601", "32", "CON_SUP_RX", W), ("U601", "29", "CON_SUP_TX", W),
                                ("U501", "4", "CON_MAIN_TX", (126, 108, 160, 152))):
        a, rest = comp_split(S, ref, num)
        routed(S, name, a, rest, win=win)


def step_signals(S):
    a, rest = comp_split(S, "R711", "1")
    routed(S, "ENC_A_S (R711.1 -> U601.17 PA6)", a, rest)
    a, rest = comp_split(S, "U501", "28")
    routed(S, "FLY_PGOOD (U501.28 PA12 -> U301/R302/TP302)", a, rest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=BOARD)
    ap.add_argument("--src", default=BOARD)
    ap.add_argument("--only", type=int, default=99)
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    from pcbcheck import Board, dangling
    from pcbedit import uuid_of
    S = Session(a.src)
    base_uuids = {uuid_of(i) for i in S.b.items if i.kind in ("track", "via")}
    u0 = unconnected(S.b)
    log(f"baseline: {sum(len(v) - 1 for v in u0.values())} unconnected pairs, {len(dangling(S.b))} dangling items")
    steps = [step_48v, step_soft_start, step_tp302, step_prune_dangling, step_console, step_signals]
    for k, st in enumerate(steps, 1):
        if k > a.only:
            break
        st(S)
        u = unconnected(S.b)
        log(f"  -> {sum(len(v) - 1 for v in u.values())} unconnected pairs")
    moved = ["C305", "TP302", "J503"]
    # U301 and R302 references are re-placed because the moved C305/TP302 now sit on them
    step_silk(S, ["J501", "J102", "D704"] + moved + ["U301", "R302"])
    stats = S.t.reclip_zones(lambda b, it: (it.kind in ("track", "via") and uuid_of(it) not in base_uuids)
                             or (it.kind == "pad" and it.ref in moved))
    for x in stats:
        log("  zone re-clip: " + x)
    S.t.save(a.out)
    log(f"saved {a.out}")
    if a.log:
        open(a.log, "w", encoding="utf8").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
