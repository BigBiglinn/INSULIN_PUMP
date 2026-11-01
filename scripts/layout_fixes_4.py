"""Layout step 4 (1 Nov 2026): BQ25188 (U101) escapes, after the U101 land pattern was verified against TI
YBG0008-C01 (scripts/fix_ybg_footprint.py, commit 02cb895).

  1. Rip up the 4 local I2C_SCL escape segments of U101.B1 (they boxed in ball C1).
  2. Route, in this order (found by trying all orders on a scratch copy): I2C_SDA from C1, I2C_SCL from B1,
     CHG_INT_N from A1. 0.15 mm tracks (board minimum; logic signals, I2C at <= 400 kHz).
  3. VBAT_FUSED from C2 (charger BAT pin, charge current): tried at 0.25 mm, then 0.2 mm; routed only if a
     route exists, and its width is reported (current capacity is checked in the report, not assumed).
  4. Zones re-clipped. No schematic, value, footprint or net change.
Usage: python3 scripts/layout_fixes_4.py [--src BOARD] [--out BOARD] [--log FILE]
"""
import argparse
import os
import sys

from shapely.geometry import box

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout_fixes as LF  # noqa: E402
from pcbcheck import BOARD, dangling, unconnected  # noqa: E402
from pcbedit import Session, uuid_of  # noqa: E402

log = LF.log


def pairs(S):
    return sum(len(v) - 1 for v in unconnected(S.b).values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=BOARD)
    ap.add_argument("--out", default=BOARD)
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    S = Session(a.src)
    base = {uuid_of(i) for i in S.b.items if i.kind in ("track", "via")}
    log(f"start: {pairs(S)} unconnected pairs")
    win = box(116.2, 112.0, 119.0, 118.7)
    scl = [i for i in S.b.items if i.kind in ("track", "via") and i.net.endswith("I2C_SCL") and i.geom.intersects(win)]
    log(f"rip-up: {len(scl)} I2C_SCL escape items at U101.B1")
    S.remove(scl, "U101.B1 I2C_SCL escape (re-routed below)")
    W = (104, 104, 150, 135)
    for name, num, w in (("I2C_SDA (U101.C1)", "C1", 0.15), ("I2C_SCL (U101.B1)", "B1", 0.15),
                         ("CHG_INT_N (U101.A1)", "A1", 0.15)):
        src, rest = LF.comp_split(S, "U101", num)
        LF.routed(S, name, src, rest, w=w, win=W)
        log(f"  -> {pairs(S)} unconnected pairs")
    for w in (0.25, 0.2):
        src, rest = LF.comp_split(S, "U101", "C2")
        if LF.routed(S, f"VBAT_FUSED (U101.C2) at {w} mm", src, rest, w=w, win=(104, 104, 130, 125)):
            break
    log(f"  -> {pairs(S)} unconnected pairs")
    LF.step_prune_dangling(S)
    stats = S.t.reclip_zones(lambda b, it: it.kind in ("track", "via") and uuid_of(it) not in base)
    for x in stats:
        log("  zone re-clip: " + x)
    S.t.save(a.out)
    log(f"end: {pairs(S)} unconnected pairs, {len(dangling(S.b))} dangling; saved {a.out}")
    if a.log:
        open(a.log, "w", encoding="utf8", newline="\r\n").write("\n".join(LF.LOG) + "\n")


if __name__ == "__main__":
    main()
