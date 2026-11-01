"""Move the right board edge and the plane outlines that follow it. Usage: pcb_outline.py BOARD OLD_X NEW_X"""
import sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
old, new = pcbnew.FromMM(float(sys.argv[2])), pcbnew.FromMM(float(sys.argv[3]))
n = 0
for d in b.GetDrawings():
    if d.GetLayer() != pcbnew.Edge_Cuts:
        continue
    s, e = d.GetStart(), d.GetEnd()
    if abs(s.x - old) < 200000:
        d.SetStart(pcbnew.VECTOR2I(new, s.y)); n += 1
    if abs(e.x - old) < 200000:
        d.SetEnd(pcbnew.VECTOR2I(new, e.y)); n += 1
z_n = 0
for z in b.Zones():
    o = z.Outline()
    for i in range(o.TotalVertices()):
        v = o.CVertex(i)
        if abs(v.x - old) < 500000:
            o.SetVertex(i, pcbnew.VECTOR2I(new, v.y)); z_n += 1
print("edge points", n, "zone vertices", z_n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
