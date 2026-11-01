"""Correct the BQ25188 (U101) land pattern to TI's YBG0008-C01 drawing (SLUSFJ3 §13.1, pp. 50-52, in
docs/datasheets/bq25188.pdf as vector graphics):
  - 2 x 4 balls, 0.4 mm pitch, A1 top-left (top view)                         [unchanged, was already right]
  - copper pad 0.23 mm diameter (was 0.20 mm, copied from a generic KiCad DSBGA-8)
  - non-solder-mask-defined (TI 'preferred'), mask opening <= metal + 0.05 mm -> solder_mask_margin 0.05
  - paste: 0.25 mm square apertures with R0.05 corners for a 0.1 mm stencil (separate paste-only pads)
  - body D 1.57-1.61 mm, E 1.02-1.06 mm (fab outline 1.04 x 1.59 nominal)
The footprint loses its _UNVERIFIED suffix. Applies the same edit to the library, the symbol default footprint,
the schematic and the placed U101 in the PCB (pads keep their nets and UUIDs; paste apertures get no net).
Usage: python3 scripts/fix_ybg_footprint.py   (idempotent check: refuses to run twice)
"""
import os
import re
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "hardware", "kicad")
OLD, NEW = "TI_YBG0008_DSBGA-8_P0.4mm_UNVERIFIED", "TI_YBG0008_DSBGA-8_P0.4mm"
DESCR_NEW = ("BQ25188 YBG0008-C01 DSBGA-8, 0.4 mm pitch. Verified 1 Nov 2026 against TI SLUSFJ3 13.1 (package outline, "
             "example board layout, example stencil): 0.23 mm NSMD pads, mask +0.05 mm, 0.25 mm square paste R0.05")
NS = uuid.UUID("2b7d0c1e-6f3a-4c55-9a7d-6d0b3e7f1a20")
BALLS = [(r + c, (-0.2 if c == "1" else 0.2), -0.6 + 0.4 * "ABCD".index(r)) for r in "ABCD" for c in "12"]


def paste_pads(nl, ind, ref):
    out = []
    for name, x, y in BALLS:
        u = uuid.uuid5(NS, f"{ref}:paste:{name}")
        out.append(f'{ind}(pad "" smd roundrect{nl}{ind}\t(at {x:g} {y:g}){nl}{ind}\t(size 0.25 0.25){nl}'
                   f'{ind}\t(layers "F.Paste"){nl}{ind}\t(roundrect_rratio 0.2){nl}{ind}\t(uuid "{u}"){nl}{ind})')
    return nl.join(out)


def fix_pads(text, nl, ind, ref):
    n = 0

    def sub(m):
        nonlocal n
        n += 1
        b = m.group(0)
        b = b.replace("(size 0.2 0.2)", "(size 0.23 0.23)")
        b = b.replace('(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "F.Cu" "F.Mask")' + nl + ind + "\t(solder_mask_margin 0.05)")
        return b
    text = re.sub(r'\(pad "[A-D][12]" smd circle.*?' + re.escape(nl + ind) + r'\)', sub, text, flags=re.S)
    assert n == 8, n
    return text


def main():
    lib = os.path.join(K, "pump_v2.pretty")
    src = os.path.join(lib, OLD + ".kicad_mod")
    assert os.path.exists(src), "already applied?"
    t = open(src, "rb").read().decode()
    nl = "\r\n" if "\r\n" in t else "\n"
    t = t.replace(OLD, NEW).replace("TI_YBG0008_UNVERIFIED", "TI_YBG0008")
    t = re.sub(r'\(descr "[^"]*"\)', f'(descr "{DESCR_NEW}")', t, count=1)
    t = t.replace("(start -0.55 -0.8) (end 0.55 0.8)", "(start -0.52 -0.795) (end 0.52 0.795)")
    t = fix_pads(t, nl, "\t", "lib")
    i = t.rindex("\t(embedded_fonts")
    t = t[:i] + paste_pads(nl, "\t", "lib") + nl + t[i:]
    open(os.path.join(lib, NEW + ".kicad_mod"), "wb").write(t.encode())
    os.remove(src)
    for f in ("pump_v2.kicad_sym", "power_input.kicad_sch"):
        p = os.path.join(K, f)
        b = open(p, "rb").read().decode()
        assert OLD in b
        open(p, "wb").write(b.replace(OLD, NEW).encode())
    p = os.path.join(K, "pump_v2.kicad_pcb")
    b = open(p, "rb").read().decode()
    nl = "\r\n" if "\r\n" in b else "\n"
    i = b.index(f'(footprint "pump_v2:{OLD}"')
    j = b.index(nl + "\t)", i) + len(nl + "\t)")           # end of this footprint block
    fp = b[i:j]
    fp = fp.replace(OLD, NEW).replace("TI_YBG0008_UNVERIFIED", "TI_YBG0008")
    fp = re.sub(r'\(descr "[^"]*"\)', f'(descr "{DESCR_NEW}")', fp, count=1)
    fp = fix_pads(fp, nl, "\t\t", "U101")
    k = fp.rindex(nl + "\t\t(embedded_fonts") if (nl + "\t\t(embedded_fonts") in fp else fp.rindex(nl + "\t)")
    fp = fp[:k] + nl + paste_pads(nl, "\t\t", "U101") + fp[k:]
    b = b[:i] + fp + b[j:]
    open(p, "wb").write(b.encode())
    print("U101 footprint corrected:", NEW)


if __name__ == "__main__":
    main()
