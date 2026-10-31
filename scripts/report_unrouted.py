"""Write the unconnected-pair list of a board, grouped like validation/logs/unrouted_nets.txt (31 Oct 2026).

The numbers come from pcbcheck.py (pure-Python connectivity, calibrated on the 10 Oct kicad-cli run), NOT
from kicad-cli. Usage: python3 scripts/report_unrouted.py BOARD OUT.txt
"""
import math
import sys

from pcbcheck import Board, connectivity, short, unconnected

GROUP_A = {"HSE_IN", "HSE_OUT", "LSE_IN", "RF_MCU", "WBA_VDD11", "WBA_VDDANA", "WBA_VDDRF", "WBA_VDDRFPA"}
GROUP_B = {"SW48_GATE"}


def main(board, out):
    b = Board(board)
    un = unconnected(b, connectivity(b))
    rows = {"A": [], "B": [], "C": []}
    for net, comps in un.items():
        sn = short(net)
        # pair every component with its nearest other component (spanning-tree style, len-1 pairs)
        done = [comps[0]]
        rest = comps[1:]
        while rest:
            best = None
            for c in rest:
                for d in done:
                    dist = min(i.geom.distance(j.geom) for i in c for j in d if i.kind != "zone" and j.kind != "zone")
                    if best is None or dist < best[0]:
                        best = (dist, c, d)
            dist, c, d = best

            def name(cc):
                pads = sorted(i.name() for i in cc if i.kind == "pad")
                return ",".join(pads) if pads else f"track/via group ({len(cc)} items)"
            g = "A" if sn in GROUP_A else "B" if sn in GROUP_B else "C"
            rows[g].append(f"  {sn:14s} gap {dist:5.1f} mm : {name(c)}  <->  {name(d)}")
            done.append(c)
            rest.remove(c)
    n = sum(len(v) for v in rows.values())
    with open(out, "w", encoding="utf8", newline="\r\n") as f:
        f.write("Unconnected connections - pcbcheck.py (pure Python, NOT kicad-cli), 31 Oct 2026 layout fixes\n")
        f.write(f"Board: {board}\nTotal unconnected pairs: {n}. Zone connectivity uses the stored (re-clipped) fills;\n")
        f.write("refill zones in KiCad and run kicad-cli DRC to confirm.\n\n")
        f.write(f"A. Placeholder nets awaiting the ST datasheet (WBA55 supply/clock/RF): {len(rows['A'])}\n")
        f.write("\n".join(sorted(rows["A"])) + "\n\n")
        f.write(f"B. Net between DNP placeholder parts only (48 V output switch, not designed): {len(rows['B'])}\n")
        f.write("\n".join(sorted(rows["B"])) + "\n\n")
        f.write(f"C. GENUINE functional connections still to be routed (board is NOT fully connected): {len(rows['C'])}\n")
        f.write("\n".join(sorted(rows["C"])) + "\n")
    print(open(out, encoding="utf8").read())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
