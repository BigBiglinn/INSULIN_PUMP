"""DRC-verified point-to-point routing for selected unconnected nets.

For each 'unconnected_items' pair of a target net in a DRC report, try candidate paths in order
(straight on F.Cu; L-shapes on F.Cu; L-shapes on B.Cu with a via at each SMD end). After each
candidate, kicad-cli DRC is run; the candidate is kept only if the number of copper violations
(clearance, shorting, tracks crossing, hole/edge clearance) does not increase and the pair is
connected. Nothing is suppressed - rejected candidates are deleted.

Run with KiCad's Python:
  python.exe scripts/hand_route.py <drc_report> NET [NET ...]
"""
import math
import os
import re
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from gen_pcb import BOARD, MM, V, fill, log  # noqa: E402

KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
ITEM = re.compile(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)")
BAD = ("[clearance]", "[shorting_items]", "[tracks_crossing]", "[hole_clearance]", "[copper_edge_clearance]")
WIDTH = {"+48V_MOT": 0.4, "+48V_RAW": 0.4}


def drc(tmp):
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "report", "--severity-error", "--refill-zones",
                    "-o", tmp, BOARD], capture_output=True)
    txt = open(tmp, encoding="utf8").read()
    blocks = re.split(r"\n(?=\[)", txt)
    bad = sum(1 for b in blocks if b.startswith(BAD))
    pairs = [b for b in blocks if b.startswith("[unconnected_items]")]
    return bad, pairs


def short(net):
    return net.split("/")[-1]


def anchors(board, line, x, y):
    m = re.match(r"(?:PTH |SMD )?[Pp]ad (\S+) \[[^\]]*\] of (\S+)", line)
    if m:
        fp = board.FindFootprintByReference(m.group(2))
        for p in fp.Pads():
            if p.GetNumber() == m.group(1):
                pos = p.GetPosition()
                smd = p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
                return [(pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), "F" if smd else "TH")]
    m = re.match(r"Track \[([^\]]*)\] on (\S+)", line)
    if m:
        lay = "F" if m.group(2) == "F.Cu" else "B"
        out = []
        for t in board.GetTracks():
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == m.group(1):
                for e in (t.GetStart(), t.GetEnd()):
                    ex, ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
                    if math.hypot(ex - x, ey - y) < 6:
                        out.append((ex, ey, lay))
        return out
    if line.startswith("Via"):
        return [(x, y, "TH")]
    return []


def add_track(board, net, pts, layer, w):
    items = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(x0, y0))
        t.SetEnd(V(x1, y1))
        t.SetLayer(layer)
        t.SetWidth(MM(w))
        t.SetNet(net)
        board.Add(t)
        items.append(t)
    return items


def add_via(board, net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetPosition(V(x, y))
    v.SetWidth(MM(0.6))
    v.SetDrill(MM(0.3))
    v.SetNet(net)
    board.Add(v)
    return v


def candidates(a, b):
    (ax, ay, al), (bx, by, bl) = a, b
    c = []
    if al in ("F", "TH") and bl in ("F", "TH"):
        c.append(("F", [(ax, ay), (bx, by)], False))
        c.append(("F", [(ax, ay), (bx, ay), (bx, by)], False))
        c.append(("F", [(ax, ay), (ax, by), (bx, by)], False))
    if al in ("B", "TH") and bl in ("B", "TH"):
        c.append(("B", [(ax, ay), (bx, ay), (bx, by)], False))
        c.append(("B", [(ax, ay), (ax, by), (bx, by)], False))
    # B.Cu with vias at SMD ends
    c.append(("B", [(ax, ay), (bx, ay), (bx, by)], True))
    c.append(("B", [(ax, ay), (ax, by), (bx, by)], True))
    return c


def main(report, nets):
    tmp = BOARD + ".hr.rpt"
    base_bad, _ = drc(tmp)
    log(f"baseline copper violations: {base_bad}")
    txt = open(report, encoding="utf8").read()
    done = 0
    for blk in re.split(r"\n(?=\[)", txt):
        if not blk.startswith("[unconnected_items]"):
            continue
        items = ITEM.findall(blk)
        if len(items) != 2:
            continue
        m = re.search(r"\[([^\]]*)\]", items[0][2])
        if not m or short(m.group(1)) not in nets or items[0][2].startswith("Zone"):
            continue
        netname = m.group(1)
        board = pcbnew.LoadBoard(BOARD)
        A = anchors(board, items[0][2], float(items[0][0]), float(items[0][1]))
        B = anchors(board, items[1][2], float(items[1][0]), float(items[1][1]))
        if not A or not B:
            log(f"skip {netname}: no anchors")
            continue
        a, b = min(((p, q) for p in A for q in B), key=lambda pq: math.hypot(pq[0][0] - pq[1][0], pq[0][1] - pq[1][1]))
        _, pairs0 = drc(tmp)
        before = sum(1 for p in pairs0 if "[" + netname + "]" in p)
        ok = False
        for lay, pts, vias in candidates(a, b):
            board = pcbnew.LoadBoard(BOARD)
            ni = board.FindNet(netname)
            w = WIDTH.get(short(netname), 0.25)
            layer = pcbnew.F_Cu if lay == "F" else pcbnew.B_Cu
            add_track(board, ni, pts, layer, w)
            if vias:
                for (x, y, l) in (a, b):
                    if l == "F":
                        add_via(board, ni, x, y)
            fill(board)
            pcbnew.SaveBoard(BOARD, board)
            bad, pairs = drc(tmp)
            after = sum(1 for p in pairs if "[" + netname + "]" in p)
            if bad <= base_bad and after < before:
                log(f"routed {netname}: {lay}{' +vias' if vias else ''} {pts}")
                ok = True
                done += 1
                break
            restore()               # reject candidate: back to the last accepted board
        if not ok:
            log(f"could not route {netname} pair without new violations")
        snapshot()
    os.remove(tmp)
    log(f"hand-routed {done} connections")


_BK = BOARD + ".hrbak"


def snapshot():
    import shutil
    shutil.copyfile(BOARD, _BK)


def restore():
    import shutil
    shutil.copyfile(_BK, BOARD)


if __name__ == "__main__":
    snapshot()
    main(sys.argv[1], set(sys.argv[2:]))
    if os.path.exists(_BK):
        os.remove(_BK)
