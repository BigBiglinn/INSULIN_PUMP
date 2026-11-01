"""Extract the kicad-cli reports and BOMs that .github/workflows/kicad-checks.yml prints between
=====BEGIN/END ...===== markers from a saved job log, and write them into validation/ and docs/.
Usage: python3 scripts/archive_ci_log.py <job-log-file>   (prints a summary)
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(path):
    raw = open(path, encoding="utf8").read()
    try:
        d = json.loads(raw)
        txt = d.get("logs_content") or d.get("content") or raw
    except Exception:
        txt = raw
    lines = [re.sub(r"^\S+Z ", "", l) for l in txt.split("\n")]

    def grab(name):
        a = [i for i, l in enumerate(lines) if l == f"=====BEGIN {name}====="][-1]
        b = [i for i, l in enumerate(lines) if l == f"=====END {name}====="][-1]
        return "\n".join(lines[a + 1:b]).strip("\n") + "\n"
    out = {"validation/erc/pump_v2-erc.rpt": (grab("ERC REPORT"), "\r\n"),
           "validation/drc/pump_v2-drc.rpt": (grab("DRC REPORT"), "\r\n"),
           "docs/bom.csv": (grab("BOM"), "\n"), "docs/bom_detailed.csv": (grab("BOM DETAILED"), "\n")}
    for rel, (t, nl) in out.items():
        open(os.path.join(ROOT, rel), "w", encoding="utf8", newline="").write(t.replace("\n", nl))
    erc, drc = out["validation/erc/pump_v2-erc.rpt"][0], out["validation/drc/pump_v2-drc.rpt"][0]
    print("ERC", dict(Counter(re.findall(r"^\[(\w+)\]", erc, re.M))))
    print("DRC", dict(Counter(re.findall(r"^\[(\w+)\]", drc, re.M))))
    print("\n".join(re.findall(r"^\*\* Found.*", drc, re.M)))
    ver = [l for l in lines if re.fullmatch(r"\d+\.\d+\.\d+", l.strip())]
    print("kicad-cli version lines:", ver[:2])


if __name__ == "__main__":
    main(sys.argv[1])
