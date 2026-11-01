"""Detailed engineering BOM from scripts/design.py (the same source the schematic is generated from).

Adds to the KiCad BOM: manufacturer, description, package, electrical ratings (ONLY from the datasheets in
docs/datasheets/, otherwise the value-field rating or 'not verified'), selection class, datasheet reference,
availability and substitution notes, and a high-voltage check for every part on a 48 V-class net.

Usage: python3 scripts/gen_bom_full.py  -> docs/bom_full.csv, docs/bom_full_summary.md
Cross-check: the reference list must equal the KiCad BOM export (docs/bom_detailed.csv); the script asserts it.
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVAIL = "not verified (distributor sites unreachable from the design environment)"

# MPN prefix -> (manufacturer, description, datasheet in repo or None, ratings [source], substitution notes)
META = {
    "BQ25188": ("Texas Instruments", "1-cell 1 A linear charger with power path, I2C", "docs/datasheets/bq25188.pdf",
                "VIN_OP 3.6-18 V; ICHG 5-1000 mA; VBATREG 3.5-4.65 V; up to 3 A discharge [DS SLUSFJ3]",
                "No drop-in; YBG land pattern must be checked against the TI package drawing (not in repo PDF)"),
    "TPS62840": ("Texas Instruments", "1.8-6.5 V, 750 mA, 60 nA IQ buck", "docs/datasheets/tps62840.pdf",
                 "VIN 1.8-6.5 V; IOUT 750 mA [DS SLVSEC6D]", "Pin-compatible family members only after VSET re-check"),
    "LM51551": ("Texas Instruments", "Wide-VIN current-mode boost/flyback controller (hiccup option)",
                "docs/datasheets/lm51551.pdf", "VIN 3.5-45 V; VCLTH 93-107 mV; VREF 0.99-1.01 V [DS SNVSB75E]",
                "LM5155 (no hiccup) is NOT equivalent: the hiccup behaviour is part of the fault analysis"),
    "TI CSD16340Q3": ("Texas Instruments", "N-MOSFET 25 V, logic level, SON 3.3x3.3", "docs/datasheets/csd16340q3.pdf",
                      "VDS 25 V; VGS(th) 0.6-1.1 V; EAS 80 mJ [DS]; sim VDS 18.7 V steady, ~25.7 V at current limit",
                      "A 30-40 V part with Qg <= present is preferred (fault-mode VDS margin, see report §27)"),
    "Nexperia PNE20010ER": ("Nexperia", "200 V 1 A hyperfast rectifier, SOD123W", "docs/datasheets/PNE20010ER.pdf",
                            "VR 200 V; IF(AV) 1 A [DS]; sim reverse 89-104 V", "Any >=200 V, >=1 A hyperfast in SOD123W"),
    "Nexperia PMEG10020ELR": ("Nexperia", "100 V 2 A Schottky, SOD123W", "docs/datasheets/pmeg10020elr.pdf",
                              "VR 100 V; IF(AV) 2 A [DS]; sim ~18.5-25.7 V", "Any >=40 V, >=1 A Schottky in SOD123W"),
    "BSS138": ("Nexperia (BSS138P datasheet in repo; 'BSS138' generic)", "N-MOSFET logic level, SOT-23",
               "docs/datasheets/bss138_nexperia.pdf", "VDS 60 V; ID 360 mA; VGS +-20 V [DS BSS138P]",
               "Generic BSS138 from other makers differ (50 V class): fix the MPN to BSS138P"),
    "STM32WBA55": ("STMicroelectronics", "Arm Cortex-M33 MCU with BLE 5.4 radio, UFQFPN48", None,
                   "not verified: ST datasheet not in repo (DS14127 required)", "None - RF design depends on it"),
    "STM32C031": ("STMicroelectronics", "Arm Cortex-M0+ supervisor MCU, LQFP48 (package ASSUMED)", None,
                  "not verified: ST datasheet not in repo", "Package choice open"),
    "MAX3485": ("Analog Devices (Maxim)", "3.3 V RS-485 transceiver, SOIC-8", None,
                "not verified: datasheet not in repo", "Any 3.3 V half-duplex RS-485 with same pinout"),
    "JST SM0": ("JST", "SH 1.0 mm pitch wire-to-board header", None,
                "not verified by JST document; distributor listing 50 V AC/DC, 0.7-1 A [WEB-2ND]",
                "J703 carries 48 V: replace with a >=100 V rated connector (owner decision 5)"),
    "AMASS XT30PW-M": ("AMASS", "XT30 PCB battery connector", None, "not verified (no datasheet in repo)",
                       "Rev B battery connector still open (B.20)"),
    "GCT USB4125": ("GCT", "USB-C power-only receptacle", None, "not verified (no datasheet in repo)", ""),
    "Hirose U.FL-R-SMT-1": ("Hirose", "U.FL coaxial receptacle", None, "not verified (no datasheet in repo)",
                            "Depends on the antenna decision (ST AN5948/AN6373)"),
}
# selections that are made but carry an open owner decision or review item
OPEN_ITEM = {"J703": "Provisional selection", "Q301": None}
HV_NETS = {"+48V_RAW", "+48V_MOT", "FLY_SEC", "FLY_SNUB", "SW48_GATE", "SW48_DRV"}


def meta_for(mpn):
    for k, v in META.items():
        if mpn.startswith(k) or k in mpn:
            return v
    return None


def short(net):
    return net.rsplit("/", 1)[-1]


def selection_class(p):
    if p.dnp:
        return "DNP"
    if OPEN_ITEM.get(p.ref):
        return OPEN_ITEM[p.ref]
    if p.status == "PLACEHOLDER":
        return "Placeholder"
    if p.status == "TBD":
        return "TBD"
    if p.status == "ASSUMED":
        return "Assumption"
    if p.status == "CALC":
        return "Calculated component"
    prov = bool(re.search(r"TBD|ASSUMED|e\.g\.", p.mpn))
    if p.mpn:
        return "Provisional selection" if prov else "Final selection"
    return "Final value, generic part" if p.status == "DECIDED" else "Datasheet value, generic part"


def value_rating(p):
    m = re.findall(r"(\d+(?:\.\d+)?)V\b", p.value)
    parts = []
    if m:
        parts.append(f"{m[-1]} V (value field)")
    if re.search(r"\b\d+(?:\.\d+)?W\b", p.value):
        parts.append(re.search(r"\b(\d+(?:\.\d+)?W)\b", p.value).group(1) + " (value field)")
    return "; ".join(parts)


def hv_check(p):
    nets = {short(n) for n in p.nets.values()}
    hv = nets & HV_NETS
    if not hv:
        return ""
    v = re.findall(r"(\d+(?:\.\d+)?)V\b", p.value)
    lib = p.lib_id.split(":")[1]
    if p.ref.startswith("TP"):
        return ""
    if p.ref.startswith("J"):
        return "48 V on a connector: JST rating not verified by a JST document (U-37, owner decision 5)"
    if lib in ("R",) and p.value.startswith("0R"):
        return "0R jumper: both ends at the rail potential; current rating only"
    if lib in ("R",):
        return f"HV net {','.join(sorted(hv))}: resistor working voltage must be >= 75 V (U-38) - set the MPN"
    if lib.startswith("C") and v:
        ok = float(v[-1]) >= 100
        return f"HV net: {v[-1]} V rating {'OK (>= 100 V, E-06 80 % rule at 55.9 V worst OVP)' if ok else 'INSUFFICIENT'}"
    return f"HV net {','.join(sorted(hv))}: rating per datasheet column"


def main():
    root, sheets = design.build()
    parts = sorted((p for sh in sheets for p in sh.parts if not p.ref.startswith("#")), key=lambda p: (re.sub(r"\d", "", p.ref),
                                                                             int(re.sub(r"\D", "", p.ref) or 0)))
    rows = []
    for p in parts:
        lib = p.lib_id.split(":")[1]
        m = meta_for(p.mpn) if p.mpn else None
        man, desc, ds, rat, sub = m if m else ("generic (not selected)" if lib in ("R", "C", "C_Polarized", "L", "LED")
                                               else "not selected", lib, None, "", "")
        rating = rat or value_rating(p) or "not specified"
        if p.lib_id.startswith("pump_v2:") and not p.mpn:
            desc = p.value
        rows.append({
            "Ref": p.ref, "Value": p.value, "Manufacturer": man, "MPN": p.mpn or "(to select)",
            "Description": desc, "Package": (p.footprint or "").split(":")[-1], "Electrical ratings": rating,
            "Qty": 1, "Design status": p.status, "Selection class": selection_class(p),
            "Datasheet": ds or ("none in repo" if p.mpn else "n/a (generic)"),
            "Availability": AVAIL, "HV check": hv_check(p), "Substitution notes": sub,
            "Sheet": next(sh.name for sh in sheets if p in sh.parts), "Note": p.note})
    out = os.path.join(ROOT, "docs", "bom_full.csv")
    with open(out, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # cross-check against the KiCad export
    kicad = os.path.join(ROOT, "docs", "bom_detailed.csv")
    krefs = {r["Ref"] for r in csv.DictReader(open(kicad, encoding="utf8"))}
    mine = {r["Ref"] for r in rows}
    bom_refs = {r for r in mine if not r.startswith(("TP", "H"))}
    diff = (bom_refs ^ krefs)
    cls = Counter(r["Selection class"] for r in rows)
    by = defaultdict(list)
    for r in rows:
        by[r["Selection class"]].append(r["Ref"])
    hv = [r for r in rows if r["HV check"]]
    L = ["# Detailed BOM - summary", "",
         "Generated by `scripts/gen_bom_full.py` from `scripts/design.py`. Full table: `docs/bom_full.csv` "
         f"({len(rows)} references incl. test points / mounting holes).", "",
         f"Cross-check with the KiCad BOM export `docs/bom_detailed.csv` ({len(krefs)} references, test points and "
         f"mounting holes excluded by KiCad): {'IDENTICAL reference set' if not diff else 'DIFFERENT: ' + ', '.join(sorted(diff))}.",
         "", "Ratings are quoted only from datasheets in `docs/datasheets/` [DS] or from the value field; everything "
         "else is 'not verified'. Availability was not checked (no distributor access).", "",
         "| Selection class | Count | References |", "|---|---|---|"]
    order = ["Final selection", "Final value, generic part", "Datasheet value, generic part", "Provisional selection",
             "Calculated component", "Assumption", "TBD", "Placeholder", "DNP"]
    for k in order + sorted(set(cls) - set(order)):
        if k in cls:
            L.append(f"| {k} | {cls[k]} | {', '.join(by[k])} |")
    L += ["", "## Parts on 48 V-class nets", "", "| Ref | Value | Check |", "|---|---|---|"]
    L += [f"| {r['Ref']} | {r['Value']} | {r['HV check']} |" for r in hv]
    open(os.path.join(ROOT, "docs", "bom_full_summary.md"), "w", encoding="utf8").write("\n".join(L) + "\n")
    print("\n".join(L))
    if diff:
        sys.exit(1)


if __name__ == "__main__":
    main()
