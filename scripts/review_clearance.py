"""Read-only geometry review: high-voltage copper against other copper, the board edge and mounting holes,
and whether the plane polygons connect the primary-loop points. Prints measurements only."""
import itertools
import sys

import pcbnew

mm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
b.BuildConnectivity()
HV = ("+48V_RAW", "+48V_MOT", "FLY_SEC", "FLY_SEC_A", "FLY_SEC_B", "FLY_SEC_C", "FLY_SEC_D", "OVP_K")
SW = ("FLY_SW", "FLY_CLAMP", "FLY_SNUB")
short = lambda n: n.split("/")[-1]
LAY = {pcbnew.F_Cu: "F.Cu", pcbnew.In1_Cu: "In1", pcbnew.In2_Cu: "In2", pcbnew.B_Cu: "B.Cu"}


def box(p):
    bb = p.GetBoundingBox()
    return mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())


def gap(a, c):
    dx = max(a[0] - c[2], c[0] - a[2], 0)
    dy = max(a[1] - c[3], c[1] - a[3], 0)
    return (dx * dx + dy * dy) ** 0.5


edge = b.GetBoardEdgesBoundingBox()
ex0, ey0, ex1, ey1 = mm(edge.GetLeft()), mm(edge.GetTop()), mm(edge.GetRight()), mm(edge.GetBottom())
pads = [(f.GetReference(), p.GetNumber(), short(p.GetNetname()), box(p), p) for f in b.GetFootprints() for p in f.Pads()]
holes = [(f.GetReference(), mm(f.GetPosition().x), mm(f.GetPosition().y)) for f in b.GetFootprints() if f.GetReference().startswith("H")]

print("--- pad to pad: lowest gap for each HV/switching net against any different net (pad bounding boxes)")
for name in HV + SW:
    best = None
    for a in pads:
        if a[2] != name:
            continue
        for c in pads:
            if c[2] == name or not c[2]:
                continue
            g = gap(a[3], c[3])
            if best is None or g < best[0]:
                best = (g, f"{a[0]}.{a[1]}", f"{c[0]}.{c[1]} {c[2]}")
    if best:
        print(f"{name:10s} {best[0]:5.2f} mm  {best[1]} <-> {best[2]}")

print("--- HV and switching pads to board edge and mounting holes")
for name in HV + SW:
    mine = [a for a in pads if a[2] == name]
    if not mine:
        continue
    de = min(min(a[3][0] - ex0, a[3][1] - ey0, ex1 - a[3][2], ey1 - a[3][3]) for a in mine)
    dh = min(((max(a[3][0] - hx, hx - a[3][2], 0)) ** 2 + (max(a[3][1] - hy, hy - a[3][3], 0)) ** 2) ** 0.5 - 1.6 for a in mine for _, hx, hy in holes)
    print(f"{name:10s} edge {de:5.2f} mm   nearest M3 hole wall {dh:5.2f} mm")

print("--- T301 pads")
for a in sorted((x for x in pads if x[0] == "T301"), key=lambda x: int(x[1])):
    print(f"  pin {a[1]:>2s} {a[2]:10s} x {a[3][0]:.2f}..{a[3][2]:.2f} y {a[3][1]:.2f}..{a[3][3]:.2f}  edge {ex1 - a[3][2]:.2f}")

print("--- plane continuity")
fills = {}
for z in b.Zones():
    if z.IsOnCopperLayer():
        for lay in z.GetLayerSet().Seq():
            fills.setdefault((short(z.GetNetname()), lay), []).append(z)
pts = {"C302.1": None, "C303.1": None, "T301.3": None, "R305.2": None, "C302.2": None, "C303.2": None}
for r, n, net, bx, p in pads:
    k = f"{r}.{n}"
    if k in pts:
        pts[k] = (net, p.GetPosition())
for k, v in pts.items():
    net, pos = v
    lay = pcbnew.In2_Cu if net == "VBAT" else pcbnew.In1_Cu
    res = []
    for z in fills.get((net, lay), []):
        poly = z.GetFilledPolysList(lay)
        for i in range(poly.OutlineCount()):
            if poly.Outline(i).PointInside(pcbnew.VECTOR2I(pos.x, pos.y)):
                res.append(i)
    print(f"  {k} {net} on {LAY[lay]}: inside island {res}, ({mm(pos.x):.2f}, {mm(pos.y):.2f})")
for net, lay in (("VBAT", pcbnew.In2_Cu), ("GND", pcbnew.In1_Cu)):
    for z in fills.get((net, lay), []):
        poly = z.GetFilledPolysList(lay)
        print(f"  {net} {LAY[lay]} zone islands: {poly.OutlineCount()}, area {[round(mm(mm(abs(poly.Outline(i).Area())))) for i in range(poly.OutlineCount())][:6]} mm2")
