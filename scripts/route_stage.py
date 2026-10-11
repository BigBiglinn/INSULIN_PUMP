"""Staged routing helpers (docs/handover/ROUTING_STAGES.md). Each step edits only the nets it is given.

Run with KiCad's Python:
  python.exe -I scripts/route_stage.py hand  SPEC.json                 # explicit tracks/vias, listed removals
  python.exe -I scripts/route_stage.py dsn   OUT.dsn NETS [EXCL_PINS]  # DSN where only NETS are routable
  python.exe -I scripts/route_stage.py merge SES NETS                  # copy only NETS' copper from SES

NETS: comma-separated short net names. EXCL_PINS: comma-separated "REF-PAD" pins dropped from those nets
in the DSN only (keeps a stage local, e.g. U501-28 for FLY_PGOOD); the PCB netlist is never changed.
Freerouting is then run with -inc on every other net class, so it cannot route anything else, and `merge`
copies only the tracks/vias of NETS into the board. Copper on other nets is left exactly as it was.
"""
import json
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from gen_pcb import BOARD, MM, V, fill  # noqa: E402

LAYER = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}


def short(n):
    return n.split("/")[-1]


def netinfo(board, name):
    for full, ni in board.GetNetsByName().items():
        if short(str(full)) == name:
            return ni
    raise KeyError(name)


def hand(spec_path):
    spec = json.load(open(spec_path, encoding="utf8"))
    b = pcbnew.LoadBoard(BOARD)
    for r in spec.get("remove", []):
        x, y = r["via"]
        p = V(x, y)
        vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and short(t.GetNetname()) == r["net"]
                and (t.GetPosition() - p).EuclideanNorm() < MM(0.02)]
        assert len(vias) == 1, f"via {r} not found exactly once"
        stubs = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and short(t.GetNetname()) == r["net"]
                 and ((t.GetStart() - p).EuclideanNorm() < MM(0.02) or (t.GetEnd() - p).EuclideanNorm() < MM(0.02))]
        for t in vias + stubs:
            b.Delete(t)
        print(f"removed {r['net']} via at ({x}, {y}) and {len(stubs)} stub(s)")
    for t in spec.get("tracks", []):
        ni = netinfo(b, t["net"])
        for (x0, y0), (x1, y1) in zip(t["pts"], t["pts"][1:]):
            tr = pcbnew.PCB_TRACK(b)
            tr.SetStart(V(x0, y0))
            tr.SetEnd(V(x1, y1))
            tr.SetWidth(MM(t["w"]))
            tr.SetLayer(LAYER[t["layer"]])
            tr.SetNet(ni)
            b.Add(tr)
    for v in spec.get("vias", []):
        via = pcbnew.PCB_VIA(b)
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetPosition(V(*v["at"]))
        via.SetWidth(MM(v.get("d", 0.6)))
        via.SetDrill(MM(v.get("drill", 0.3)))
        via.SetNet(netinfo(b, v["net"]))
        b.Add(via)
    fill(b)
    pcbnew.SaveBoard(BOARD, b)
    print(f"added {sum(len(t['pts']) - 1 for t in spec.get('tracks', []))} segments, {len(spec.get('vias', []))} vias")


def dsn(out, nets, excl=""):
    nets = set(nets.split(","))
    excl = set(x for x in excl.split(",") if x)
    b = pcbnew.LoadBoard(BOARD)
    for z in list(b.Zones()):                  # outer GND pours left out so the router can use F/B.Cu
        if z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            b.Remove(z)
    assert pcbnew.ExportSpecctraDSN(b, out)
    txt = open(out, encoding="utf8").read()
    lines = txt.split("\n")
    for k, l in enumerate(lines[:-1]):         # inner plane layers as 'power' (see gen_pcb.export_dsn)
        if l.strip() in ("(layer In1.Cu", "(layer In2.Cu"):
            lines[k + 1] = lines[k + 1].replace("(type signal)", "(type power)")
    txt = "\n".join(lines)
    # drop excluded pins from the stage nets (DSN only)
    def fix_net(m):
        body = m.group(0)
        name = short(m.group(1).strip('"'))
        if name in nets:
            for p in excl:
                body = re.sub(r"(?<=[\s(])" + re.escape(p) + r"(?=[\s)])", "", body)
        return body
    txt = re.sub(r'\(net ("[^"]*"|\S+)\s*\n\s*\(pins[^)]*\)', fix_net, txt)
    # move stage nets into their own class STAGE (copy of the class they came from)
    classes = list(re.finditer(r"\(class (\S+)((?:\s+(?:\"[^\"]*\"|[^\s()]+))*)\s*(\(circuit.*?\)\s*\(rule.*?\)\s*\)\s*)\)", txt, re.S))
    stage_members, stage_body, others = [], None, []
    for m in classes:
        members = re.findall(r'"[^"]*"|[^\s()]+', m.group(2))
        keep = [x for x in members if short(x.strip('"')) not in nets]
        moved = [x for x in members if short(x.strip('"')) in nets]
        if moved:
            stage_members += moved
            stage_body = stage_body or m.group(3)
        others.append(m.group(1))
        txt = txt.replace(m.group(0), f"(class {m.group(1)} {' '.join(keep)}\n      {m.group(3)})")
    assert stage_members, "no stage nets found in DSN classes"
    found = {short(x.strip('"')) for x in stage_members}
    assert found == nets, f"stage nets missing from DSN: {nets - found}"
    txt = txt.replace("(class " + others[0], f"(class STAGE {' '.join(stage_members)}\n      {stage_body})\n    (class " + others[0], 1)
    open(out, "w", encoding="utf8").write(txt)
    print("DSN", out, "stage nets:", sorted(found), "ignore classes:", ",".join(others), "excluded pins:", sorted(excl))


def merge(ses, nets):
    nets = set(nets.split(","))
    tmp = pcbnew.LoadBoard(BOARD)
    assert pcbnew.ImportSpecctraSES(tmp, ses)
    b = pcbnew.LoadBoard(BOARD)
    before = sum(1 for t in b.GetTracks() if short(t.GetNetname()) in nets)
    for t in list(b.GetTracks()):              # stage nets: replace with the routed result
        if short(t.GetNetname()) in nets:
            b.Delete(t)
    n = 0
    for t in tmp.GetTracks():
        if short(t.GetNetname()) not in nets:
            continue
        ni = netinfo(b, short(t.GetNetname()))
        if t.Type() == pcbnew.PCB_VIA_T:
            v = pcbnew.PCB_VIA(b)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetPosition(t.GetPosition())
            v.SetWidth(t.GetWidth(pcbnew.F_Cu))
            v.SetDrill(t.GetDrill())
            v.SetNet(ni)
            b.Add(v)
        else:
            c = pcbnew.PCB_TRACK(b)
            c.SetStart(t.GetStart())
            c.SetEnd(t.GetEnd())
            c.SetWidth(t.GetWidth())
            c.SetLayer(t.GetLayer())
            c.SetNet(ni)
            b.Add(c)
        n += 1
    fill(b)
    pcbnew.SaveBoard(BOARD, b)
    print(f"merged {n} items on {sorted(nets)} (replaced {before}); other nets untouched")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "hand":
        hand(sys.argv[2])
    elif cmd == "dsn":
        dsn(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "merge":
        merge(sys.argv[2], sys.argv[3])
