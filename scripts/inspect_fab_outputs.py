"""Inspect Gerber X2 / Excellon files produced by kicad-cli (used by the CI export dry run).
Prints, per file: file function, coordinate format, number of apertures, number of draw/flash operations and
the X/Y extents; for drill files the tool table and hits per tool. Usage: python3 inspect_fab_outputs.py <dir>
"""
import os
import re
import sys


def gerber(path):
    t = open(path, encoding="utf8", errors="replace").read()
    fn = re.search(r"%TF\.FileFunction,([^*]*)\*%", t)
    fs = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", t)
    unit = "mm" if "%MOMM*%" in t else ("inch" if "%MOIN*%" in t else "?")
    dec = int(fs.group(2)) if fs else 6
    xs, ys = [], []
    for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0?([123])\*", t):
        xs.append(int(m.group(1)) / 10 ** dec)
        ys.append(int(m.group(2)) / 10 ** dec)
    ap = len(re.findall(r"%ADD\d+", t))
    ops = len(re.findall(r"D0?[123]\*", t))
    ext = f"X {min(xs):.2f}..{max(xs):.2f}  Y {min(ys):.2f}..{max(ys):.2f} {unit}" if xs else "no coordinates"
    return f"{fn.group(1) if fn else '?':38s} apertures {ap:4d}  ops {ops:6d}  {ext}"


def drill(path):
    t = open(path, encoding="utf8", errors="replace").read()
    tools = dict(re.findall(r"^T(\d+)C([\d.]+)", t, re.M))
    hits, cur = {}, None
    for line in t.splitlines():
        m = re.match(r"^T(\d+)$", line)
        if m:
            cur = m.group(1)
        elif cur and re.match(r"^X-?[\d.]+Y-?[\d.]+", line):
            hits[cur] = hits.get(cur, 0) + 1
    unit = "mm" if "METRIC" in t else "inch"
    return "tools: " + ", ".join(f"T{k} {v} {unit} x{hits.get(k, 0)}" for k, v in tools.items()) + \
           f"  total hits {sum(hits.values())}"


def main(d):
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        size = os.path.getsize(p)
        if f.endswith((".drl",)):
            print(f"{f:45s} {size:8d} B  {drill(p)}")
        elif f.endswith((".gbr", ".gtl", ".gbl", ".g1", ".g2", ".gto", ".gbo", ".gts", ".gbs", ".gtp", ".gbp", ".gm1")):
            print(f"{f:45s} {size:8d} B  {gerber(p)}")
        else:
            print(f"{f:45s} {size:8d} B")


if __name__ == "__main__":
    main(sys.argv[1])
