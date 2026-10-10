"""Close short, trivially routable gaps left by the autorouter, then verify with DRC.

For each 'unconnected_items' pair in the DRC report whose two anchor points are < MAX_GAP mm
apart and share a copper layer, add one straight segment. Then run kicad-cli DRC again and
delete every added segment that takes part in any copper violation. Nothing is suppressed.

Run with KiCad's Python:  python.exe scripts/stitch.py <drc_report>
"""
import math
import os
import re
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from gen_pcb import BOARD, MM, V, fill  # noqa: E402

MAX_GAP = 3.0
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
ITEM = re.compile(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)")


def anchors(board, line, x, y):
    """Return list of (x, y, layers) candidate connection points for one report item."""
    m = re.match(r"(?:PTH |SMD )?[Pp]ad (\S+) \[[^\]]*\] of (\S+)", line)
    if m:
        fp = board.FindFootprintByReference(m.group(2))
        for p in fp.Pads():
            if p.GetNumber() == m.group(1):
                pos = p.GetPosition()
                lay = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)]
                return [(pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), lay)]
    m = re.match(r"Track \[([^\]]*)\] on (\S+)", line)
    if m:
        lay = board.GetLayerID(m.group(2))
        out = []
        for t in board.GetTracks():
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == m.group(1) and t.GetLayer() == lay:
                for e in (t.GetStart(), t.GetEnd()):
                    out.append((pcbnew.ToMM(e.x), pcbnew.ToMM(e.y), [lay]))
        return out
    m = re.match(r"Via \[([^\]]*)\]", line)
    if m:
        return [(x, y, [pcbnew.F_Cu, pcbnew.B_Cu])]
    return []


def net_of(line):
    m = re.search(r"\[([^\]]*)\]", line)
    return m.group(1) if m else None


def run_drc(out):
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "report", "--severity-error", "--refill-zones",
                    "--save-board", "-o", out, BOARD], capture_output=True)
    return open(out, encoding="utf8").read()


def main(report):
    txt = open(report, encoding="utf8").read()
    board = pcbnew.LoadBoard(BOARD)
    added = []
    for blk in re.split(r"\n(?=\[)", txt):
        if not blk.startswith("[unconnected_items]"):
            continue
        items = ITEM.findall(blk)
        if len(items) != 2:
            continue
        net = net_of(items[0][2])
        A = anchors(board, items[0][2], float(items[0][0]), float(items[0][1]))
        B = anchors(board, items[1][2], float(items[1][0]), float(items[1][1]))
        best = None
        for ax, ay, al in A:
            for bx, by, bl in B:
                common = [l for l in al if l in bl]
                d = math.hypot(ax - bx, ay - by)
                if common and 0.01 < d < MAX_GAP and (best is None or d < best[0]):
                    best = (d, ax, ay, bx, by, common[0])
        if not best:
            continue
        ni = board.FindNet(net)
        if ni is None:
            continue
        d, ax, ay, bx, by, lay = best
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(ax, ay))
        t.SetEnd(V(bx, by))
        t.SetLayer(lay)
        t.SetWidth(MM(0.2))
        t.SetNet(ni)
        board.Add(t)
        added.append((round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3), net))
    fill(board)
    pcbnew.SaveBoard(BOARD, board)
    print(f"added {len(added)} stitch segments")
    # verify: drop stitches involved in copper violations
    tmp = BOARD + ".stitch.rpt"
    rep = run_drc(tmp)
    bad_pts = set()
    for blk in re.split(r"\n(?=\[)", rep):
        if blk.startswith(("[clearance]", "[shorting_items]", "[tracks_crossing]", "[copper_edge_clearance]",
                           "[hole_clearance]", "[solder_mask_bridge]")):
            for x, y, what in ITEM.findall(blk):
                if what.startswith("Track"):
                    bad_pts.add((round(float(x), 2), round(float(y), 2)))
    board = pcbnew.LoadBoard(BOARD)
    removed = 0
    keys = {(round(a, 2), round(b, 2)) for a, b, c, d, n in added} | {(round(c, 2), round(d, 2)) for a, b, c, d, n in added}
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_TRACE_T:
            continue
        s = (round(pcbnew.ToMM(t.GetStart().x), 2), round(pcbnew.ToMM(t.GetStart().y), 2))
        e = (round(pcbnew.ToMM(t.GetEnd().x), 2), round(pcbnew.ToMM(t.GetEnd().y), 2))
        if (s in keys and e in keys) and (s in bad_pts or e in bad_pts):
            board.Remove(t)
            removed += 1
    fill(board)
    pcbnew.SaveBoard(BOARD, board)
    os.remove(tmp)
    print(f"removed {removed} stitches that caused violations; kept {len(added) - removed}")


if __name__ == "__main__":
    main(sys.argv[1])
