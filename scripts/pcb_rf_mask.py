"""Open the solder mask over the RF lines (AN5948 sec.7.6; Z0 was calculated for bare copper)."""
import sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
M = pcbnew.FromMM
for (x0, y0, x1, y1) in ((150.89, 104.7, 151.41, 111.2), (150.95, 113.5, 151.35, 114.7)):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetFilled(True)
    s.SetStart(pcbnew.VECTOR2I(M(x0), M(y0)))
    s.SetEnd(pcbnew.VECTOR2I(M(x1), M(y1)))
    s.SetLayer(pcbnew.F_Mask)
    s.SetWidth(0)
    b.Add(s)
pcbnew.SaveBoard(sys.argv[1], b)
print("mask openings added")
