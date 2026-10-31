"""Controlled PCB update from the schematic netlist. Preserves existing routing; never regenerates the board.

Usage: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/pcb_eco.py BOARD.kicad_pcb NETLIST.net PLAN.json LOG.txt

Steps:
  1. Delete footprints that left the schematic, add new ones, replace those whose footprint changed.
  2. Update value, fields, DNP and every pad net from the netlist.
  3. Remove copper of the nets named in PLAN "rip_nets" (redesigned regions).
  4. Remove copper stubs on pads whose net changed, or on parts that move.
  5. Apply PLAN "moves", then cut only the foreign segments that the moved or new pads now hit.
  6. Fan out moved plane-net pads and refill zones.
Every removed item is written to LOG. Nothing is routed here apart from plane fan-out stubs.
"""
import json
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pcb  # noqa: E402

PLANE = ("GND", "VBAT", "+3V3")
mm = pcbnew.ToMM


def short(n):
    return n.split("/")[-1]


def describe(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        return f"via {short(t.GetNetname())} ({mm(p.x):.2f}, {mm(p.y):.2f})"
    s, e = t.GetStart(), t.GetEnd()
    lay = t.GetBoard().GetLayerName(t.GetLayer())
    return f"seg {short(t.GetNetname())} {lay} ({mm(s.x):.2f}, {mm(s.y):.2f})-({mm(e.x):.2f}, {mm(e.y):.2f})"


def touching(board, pos, net, layer=None):
    out = []
    for t in board.GetTracks():
        if t.GetNetCode() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            if t.GetPosition() == pos:
                out.append(t)
        elif t.GetStart() == pos or t.GetEnd() == pos:
            out.append(t)
    return out


def pads_at(board, pos, net):
    return [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetCode() == net and p.HitTest(pos)]


def remove_stub(board, pad, net, log):
    """Remove copper of `net` from this pad back to the first junction, via with other users, or pad."""
    n = 0
    first = [t for t in board.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetCode() == net and pad.IsOnLayer(t.GetLayer())
             and (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()))]
    # a via inside the pad
    first_v = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net and pad.HitTest(t.GetPosition())]
    for v in first_v:
        log.append("  removed " + describe(v))
        board.Delete(v)
        n += 1
    work = list(first)
    while work:
        t = work.pop()
        ends = [t.GetStart(), t.GetEnd()]
        log.append("  removed " + describe(t))
        board.Delete(t)
        n += 1
        for e in ends:
            if pad.HitTest(e):
                continue
            others = touching(board, e, net)
            if pads_at(board, e, net):
                continue
            vias = [x for x in others if x.Type() == pcbnew.PCB_VIA_T]
            segs = [x for x in others if x.Type() != pcbnew.PCB_VIA_T]
            if vias and not segs:
                is_plane = short(vias[0].GetNetname()) in PLANE
                log.append("  removed " + describe(vias[0]) + ("" if is_plane else " (end of stub)"))
                board.Delete(vias[0])
                n += 1
            elif not vias and len(segs) == 1:
                work.append(segs[0])
    return n


def main(board_path, net_path, plan_path, log_path):
    gen_pcb.NETLIST = net_path
    comps, nets = gen_pcb.read_netlist()
    plan = json.load(open(plan_path, encoding="utf8"))
    board = pcbnew.LoadBoard(board_path)
    log = []
    want = {c["ref"]: c for c in comps if c["footprint"]}
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    old_pad_net = {(f.GetReference(), p.GetNumber()): p.GetNetCode() for f in fps.values() for p in f.Pads()}

    # --- rip redesigned nets
    rip = set(plan.get("rip_nets", []))
    dead = [t for t in board.GetTracks() if short(t.GetNetname()) in rip]
    log.append(f"RIP NETS {sorted(rip)}: {len(dead)} items")
    for t in dead:
        log.append("  removed " + describe(t))
        board.Delete(t)

    # --- deleted footprints
    for r in sorted(set(fps) - set(want)):
        log.append(f"DELETE {r} ({fps[r].GetValue()}) at ({mm(fps[r].GetPosition().x):.2f}, {mm(fps[r].GetPosition().y):.2f})")
        for p in fps[r].Pads():
            if p.GetNetCode() > 0:
                remove_stub(board, p, p.GetNetCode(), log)
        board.Delete(fps[r])
        del fps[r]

    # --- stubs on parts that move: before the move, while the old pad geometry is valid
    moves = plan.get("moves", {})
    for r in moves:
        if r in fps:
            log.append(f"STUBS on moving {r}")
            for p in fps[r].Pads():
                if p.GetNetCode() > 0:
                    remove_stub(board, p, p.GetNetCode(), log)

    # --- replace or add footprints
    for r, c in sorted(want.items()):
        lib = fps[r].GetFPID().GetUniStringLibId() if r in fps else None
        if r in fps and lib == c["footprint"]:
            continue
        pos, rot = (fps[r].GetPosition(), fps[r].GetOrientationDegrees()) if r in fps else (gen_pcb.V(150, 90), 0)
        if r in fps:
            log.append(f"REPLACE {r}: {lib} -> {c['footprint']}")
            for p in fps[r].Pads():
                if p.GetNetCode() > 0:
                    remove_stub(board, p, p.GetNetCode(), log)
            board.Delete(fps[r])
        else:
            log.append(f"ADD {r}: {c['footprint']}")
        f = gen_pcb.load_fp(c["footprint"])
        f.SetReference(r)
        f.SetOrientationDegrees(rot)
        f.SetPosition(pos)
        board.Add(f)
        fps[r] = f

    # --- values, fields, identity
    for r, c in want.items():
        f = fps[r]
        if f.GetValue() != c["value"]:
            log.append(f"VALUE {r}: {f.GetValue()} -> {c['value']}")
        f.SetValue(c["value"])
        f.SetPath(pcbnew.KIID_PATH(c["sheet_ts"] + c["ts"]))
        f.SetSheetname(c["props"].get("Sheetname", ""))
        f.SetSheetfile(c["props"].get("Sheetfile", ""))
        f.SetDNP("dnp" in c["props"])
        f.SetExcludedFromBOM("exclude_from_bom" in c["props"])
        for name, val in c["fields"]:
            if name == "Footprint":
                continue
            fld = f.GetField(name) if f.HasField(name) else None
            if fld is None:
                fld = pcbnew.PCB_FIELD(f, pcbnew.FIELD_T_USER, name)
                fld.SetLayer(pcbnew.F_Fab)
                fld.SetVisible(False)
                f.Add(fld)
            fld.SetText(val)

    # --- nets
    info = {}
    for name, _ in nets:
        ni = board.FindNet(name)
        if ni is None or ni.GetNetname() != name:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            log.append(f"NEW NET {short(name)}")
        info[name] = ni
    node_net = {(r, p): name for name, nodes in nets for r, p in nodes}
    changed = []
    for r, f in fps.items():
        for p in f.Pads():
            name = node_net.get((r, p.GetNumber()))
            if name is None:
                if p.GetNumber():
                    p.SetNetCode(0)
                continue
            new = info[name]
            old = old_pad_net.get((r, p.GetNumber()))
            if old is not None and old != new.GetNetCode() and old > 0:
                changed.append((r, p, old, new))
    for r, p, old, new in changed:
        log.append(f"NET CHANGE {r}.{p.GetNumber()} -> {short(new.GetNetname())}")
        remove_stub(board, p, old, log)
    for r, f in fps.items():
        for p in f.Pads():
            name = node_net.get((r, p.GetNumber()))
            if name is not None:
                p.SetNet(info[name])

    # --- moves
    for r, (x, y, rot) in moves.items():
        f = fps[r]
        p0 = f.GetPosition()
        log.append(f"MOVE {r}: ({mm(p0.x):.2f}, {mm(p0.y):.2f}, {f.GetOrientationDegrees():.0f}) -> ({x}, {y}, {rot})")
        f.SetOrientationDegrees(rot)
        f.SetPosition(gen_pcb.V(x, y))
    missing = [r for r in want if fps[r].GetPosition() == gen_pcb.V(150, 90)]
    if missing:
        raise SystemExit("new footprints without a position: " + " ".join(missing))

    # --- foreign copper hit by moved or new pads: cut only the colliding item
    moved = [p for r in moves for p in fps[r].Pads()]
    layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
    hits = {}
    for t in board.GetTracks():
        for p in moved:
            if p.GetNetCode() == t.GetNetCode() and p.GetNetCode() > 0:
                continue
            hv = short(t.GetNetname()) in gen_pcb.HV_SUFFIX or short(p.GetNetname()) in gen_pcb.HV_SUFFIX
            c = pcbnew.FromMM(0.6 if hv else 0.15)
            if any(t.IsOnLayer(lay) and p.IsOnLayer(lay) and t.GetEffectiveShape(lay).Collide(p.GetEffectiveShape(lay), c) for lay in layers):
                hits[t.m_Uuid.AsString()] = (t, p)
                break
    for t, p in hits.values():
        log.append(f"CUT {describe(t)} hit by {p.GetParentFootprint().GetReference()}.{p.GetNumber()}")
        board.Delete(t)

    # --- plane fan-out on moved parts
    only = {f"{r}.{p.GetNumber()}" for r in moves for p in fps[r].Pads() if short(p.GetNetname()) in PLANE}
    only |= {f"{r}.{p.GetNumber()}" for r, c in want.items() for p in fps[r].Pads()
             if short(p.GetNetname()) in PLANE and r in plan.get("fanout_extra", [])}
    only = {o for o in only if o.split(".")[0] not in plan.get("no_fanout", [])}
    left = gen_pcb.fanout(board, only=only, seed_existing=True)
    log.append(f"FANOUT requested {len(only)} pads; not fanned: {sorted(left)}")
    gen_pcb.fill(board)
    pcbnew.SaveBoard(board_path, board)
    open(log_path, "w", encoding="utf8").write("\n".join(log) + "\n")
    print(f"log lines {len(log)}; cuts {len(hits)}; unfanned {sorted(left)}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
