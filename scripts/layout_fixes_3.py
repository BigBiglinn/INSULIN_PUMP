"""Layout-only fixes, session 3 (1 Nov 2026), applied on top of commit 7cc348e.

  1. ENC_I_M     U501.48 -> R710.1 (encoder index to the main MCU, through the existing R710 series resistor)
  2. VBAT_SENSE  R107.2/C104.1/R108.1 divider node -> U501.14 (main-MCU battery ADC input)
  3. Zone fills re-clipped around the new copper.

Both nets were classified "routable immediately" in FINAL_ENGINEERING_REVIEW_2026-11-01 §3. They pass near
U501, whose fan-out may be redone once the ST documents arrive; they are short and can be re-routed then.
No schematic, value, footprint or net change. Results are pcbcheck.py results, NOT kicad-cli (CI runs that).
Usage: python3 scripts/layout_fixes_3.py [--src BOARD] [--out BOARD] [--log FILE]
"""
import argparse
import os
import sys

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
    log(f"start: {pairs(S)} unconnected pairs, {len(dangling(S.b))} dangling items")
    for name, ref, num in (("ENC_I_M (U501.48 -> R710.1)", "U501", "48"),
                           ("VBAT_SENSE (U501.14 -> R107/R108/C104 divider)", "U501", "14")):
        src, rest = LF.comp_split(S, ref, num)
        LF.routed(S, name, src, rest)
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
