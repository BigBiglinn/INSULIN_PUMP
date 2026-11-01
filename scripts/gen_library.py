"""Generate the project symbol and footprint library for Piezo Insulin Pump v2.

Pin numbers and names come from the datasheets in docs/datasheets:
  LM51551   TI SNVSB75E Table 7-1, WSON-12 (DSS), EP = pad 13 (KiCad footprint numbering)
  BQ25188   TI SLUSFJ3 Table 5-1, DSBGA-8 (YBG) balls A1..D2
  TPS62840  TI SLVSEC6D Pin Functions, SON-8 (DLC)
Placeholder parts (flyback FET, transformer, output switch) carry no datasheet
claims; their pinout only matches the placeholder footprint.
"""
import os
import re

from kicadlib import FP_DIR, PROJECT_DIR

LIB = "pump_v2"
F = '(effects (font (size 1.27 1.27)))'
FH = '(effects (font (size 1.27 1.27)) (hide yes))'


def pin(typ, x, y, ang, name, num, length=2.54):
    return (f'\t\t\t(pin {typ} line (at {x:g} {y:g} {ang}) (length {length:g})\n'
            f'\t\t\t\t(name "{name}" {F})\n\t\t\t\t(number "{num}" {F})\n\t\t\t)')


def box_symbol(name, ref, value, footprint, datasheet, desc, left, right, top=(), bottom=(),
               width=15.24, extra_props=()):
    """left/right/top/bottom: lists of (number, name, type) or None for a gap."""
    rows = max(len(left), len(right), 1)
    h = (rows + 1) * 2.54
    half_w = round(width / 2 / 2.54) * 2.54
    top_y = round(h / 2 / 2.54) * 2.54
    bot_y = top_y - (rows + 1) * 2.54
    pins = []
    for i, p in enumerate(left):
        if p:
            pins.append(pin(p[2], -half_w - 2.54, top_y - (i + 1) * 2.54, 0, p[1], p[0]))
    for i, p in enumerate(right):
        if p:
            pins.append(pin(p[2], half_w + 2.54, top_y - (i + 1) * 2.54, 180, p[1], p[0]))
    n = len(top)
    for i, p in enumerate(top):
        if p:
            x = (i - (n - 1) / 2) * 2.54
            pins.append(pin(p[2], x, top_y + 2.54, 270, p[1], p[0]))
    n = len(bottom)
    for i, p in enumerate(bottom):
        if p:
            x = (i - (n - 1) / 2) * 2.54
            pins.append(pin(p[2], x, bot_y - 2.54, 90, p[1], p[0]))
    props = [("Reference", ref, False, top_y + 5.08), ("Value", value, False, bot_y - 5.08),
             ("Footprint", footprint, True, 0), ("Datasheet", datasheet, True, 0),
             ("Description", desc, True, 0)] + [(k, v, True, 0) for k, v in extra_props]
    ptxt = "\n".join(
        f'\t\t(property "{k}" "{v}" (at 0 {y:g} 0) {FH if hide else F})' for k, v, hide, y in props)
    return f'''\t(symbol "{name}"
\t\t(pin_names (offset 1.016))
\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)
{ptxt}
\t\t(symbol "{name}_0_1"
\t\t\t(rectangle (start {-half_w:g} {top_y:g}) (end {half_w:g} {bot_y:g})
\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))
\t\t)
\t\t(symbol "{name}_1_1"
{chr(10).join(pins)}
\t\t)
\t\t(embedded_fonts no)
\t)'''


def mosfet_symbol(name, value, footprint, desc, pchan, gate_nums, source_nums, drain_nums):
    """Simple box-style MOSFET with numbered pins (stacked pins share a name)."""
    left = [(n, "G", "input") for n in gate_nums]
    right = [(n, "D", "passive") for n in drain_nums] + [None] + [(n, "S", "passive") for n in source_nums]
    return box_symbol(name, "Q", value, footprint, "", desc, left, right, width=10.16)


def symbols():
    out = []
    out.append(box_symbol(
        "LM51551", "U", "LM51551DSSR", "Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65",
        "https://www.ti.com/lit/ds/symlink/lm51551.pdf",
        "Boost/SEPIC/flyback controller, hiccup OCP, WSON-12 (TI SNVSB75E)",
        left=[("1", "BIAS", "power_in"), ("2", "VCC", "passive"), ("12", "UVLO/EN/SYNC", "input"),
              ("10", "RT", "passive"), ("9", "SS", "passive"), ("11", "PGOOD", "open_collector")],
        right=[("3", "GATE", "output"), ("5", "CS", "input"), ("8", "FB", "input"),
               ("6", "COMP", "passive"), ("4", "PGND", "power_in"), ("7", "AGND", "power_in")],
        bottom=[("13", "EP", "passive")], width=20.32,
        extra_props=[("MPN", "LM51551DSSR")]))
    out.append(box_symbol(
        "BQ25188", "U", "BQ25188YBGR", "pump_v2:TI_YBG0008_DSBGA-8_P0.4mm",
        "https://www.ti.com/lit/ds/symlink/bq25188.pdf",
        "I2C 1-cell 1 A linear charger with power path, DSBGA-8 (TI SLUSFJ3)",
        left=[("A2", "IN", "power_in"), ("B1", "SCL", "input"), ("C1", "SDA", "bidirectional"),
              ("A1", "~{INT}", "open_collector"), ("D1", "TS/MR", "bidirectional")],
        right=[("B2", "SYS", "power_out"), ("C2", "BAT", "passive"), None, None, ("D2", "GND", "power_in")],
        width=17.78, extra_props=[("MPN", "BQ25188YBGR")]))
    out.append(box_symbol(
        "TPS62840DLC", "U", "TPS62840DLCR", "Package_SON:Texas_VSON-HR-8_1.5x2mm_P0.5mm",
        "https://www.ti.com/lit/ds/symlink/tps62840.pdf",
        "750 mA ultra-low-Iq step-down, VSET-programmed, SON-8 DLC (TI SLVSEC6D)",
        left=[("2", "VIN", "power_in"), ("4", "EN", "input"), ("3", "MODE", "input"),
              ("6", "STOP", "input"), ("5", "VSET", "passive")],
        right=[("7", "SW", "power_out"), ("8", "VOS", "input"), None, None, ("1", "GND", "power_in")],
        width=15.24, extra_props=[("MPN", "TPS62840DLCR")]))
    # placeholders ------------------------------------------------------
    out.append(mosfet_symbol(
        "Q_NMOS_TDSON8_TBD", "NMOS_TBD", "Package_TO_SOT_SMD:TDSON-8-1",
        "PLACEHOLDER flyback switch, logic-level N-MOSFET, part and package TBD",
        False, ["4"], ["1", "2", "3"], ["5"]))
    out.append(mosfet_symbol(
        "Q_PMOS_SOT23_TBD", "PMOS_TBD", "Package_TO_SOT_SMD:SOT-23",
        "PLACEHOLDER high-side P-MOSFET (>=100 V class), part and package TBD",
        True, ["1"], ["2"], ["3"]))
    out.append(mosfet_symbol(
        "CSD16340Q3", "CSD16340Q3", "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET",
        "TI CSD16340Q3 25 V N-channel NexFET, SON 3.3x3.3 (pins 1-3 S, 4 G, 5-8 D = pad 5)",
        False, ["4"], ["1", "2", "3"], ["5"]))
    out.append(mosfet_symbol(
        "Q_NMOS_SOT23_TBD", "NMOS_TBD", "Package_TO_SOT_SMD:SOT-23",
        "PLACEHOLDER level-shift N-MOSFET (>=100 V class), part and package TBD",
        False, ["1"], ["2"], ["3"]))
    out.append(box_symbol(
        "XFMR_FLYBACK_TBD", "T", "XFMR_TBD", "pump_v2:XFMR_PLACEHOLDER_4P", "",
        "PLACEHOLDER flyback transformer, part number / turns ratio TBD (OPEN B.16)",
        left=[("1", "P_DOT", "passive"), None, ("2", "P", "passive")],
        right=[("3", "S_DOT", "passive"), None, ("4", "S", "passive")], width=10.16))
    return out


def write_symbol_lib():
    os.makedirs(PROJECT_DIR, exist_ok=True)
    txt = ('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "pump_v2_gen")\n'
           '\t(generator_version "10.0")\n' + "\n".join(symbols()) + "\n)\n")
    with open(os.path.join(PROJECT_DIR, LIB + ".kicad_sym"), "w", encoding="utf8") as f:
        f.write(txt)


# ---------------------------------------------------------------- footprints
def fp_header(name, descr, attr="smd"):
    return [f'(footprint "{name}"', '\t(version 20241229)', '\t(generator "pump_v2_gen")',
            '\t(layer "F.Cu")', f'\t(descr "{descr}")', f'\t(attr {attr})']


def fp_prop(name, value, x, y, layer, hide=False):
    h = " (hide yes)" if hide else ""
    return (f'\t(property "{name}" "{value}" (at {x:g} {y:g} 0) (layer "{layer}"){h}\n'
            f'\t\t(effects (font (size 1 1) (thickness 0.15))))')


def fp_rect(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_rect (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) '
            f'(stroke (width {w:g}) (type solid)) (fill no) (layer "{layer}"))')


def write_xfmr_placeholder(d):
    s = 6.0
    lines = fp_header("XFMR_PLACEHOLDER_4P",
                      "PLACEHOLDER 12x12 mm flyback transformer outline. NOT a real land pattern: "
                      "replace once the transformer part is chosen (OPEN B.16)")
    lines += [fp_prop("Reference", "REF**", 0, -s - 1.5, "F.SilkS"),
              fp_prop("Value", "XFMR_PLACEHOLDER_4P", 0, s + 1.5, "F.Fab"),
              fp_rect(-s, -s, s, s, "F.Fab", 0.1), fp_rect(-s - 0.25, -s - 0.25, s + 0.25, s + 0.25, "F.CrtYd", 0.05),
              fp_rect(-s - 0.12, -s - 0.12, s + 0.12, s + 0.12, "F.SilkS", 0.12),
              '\t(fp_text user "PLACEHOLDER" (at 0 0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
              '\t(fp_circle (center -4.5 -1.2) (end -4.2 -1.2) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))']
    pads = {"1": (-4.5, -3.5), "2": (-4.5, 3.5), "3": (4.5, -3.5), "4": (4.5, 3.5)}
    for n, (x, y) in pads.items():
        lines.append(f'\t(pad "{n}" smd rect (at {x:g} {y:g}) (size 2.5 2.5) (layers "F.Cu" "F.Paste" "F.Mask"))')
    lines += ["\t(embedded_fonts no)", ")"]
    with open(os.path.join(d, "XFMR_PLACEHOLDER_4P.kicad_mod"), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def write_ybg_placeholder(d):
    """BQ25188 YBG0008-C01 land pattern, explicit geometry from TI SLUSFJ3 13.1 (pp. 50-52 of
    docs/datasheets/bq25188.pdf; drawings are vector graphics, read by rendering the pages, 1 Nov 2026):
    2 x 4 balls, 0.4 mm pitch, A1 top-left; 0.23 mm copper, non-solder-mask-defined (mask +0.05 mm max);
    paste 0.25 mm square, R0.05, 0.1 mm stencil; body D 1.57-1.61 mm, E 1.02-1.06 mm.
    (Function name kept for history; the footprint is no longer a placeholder.)
    """
    import uuid
    ns = uuid.UUID("2b7d0c1e-6f3a-4c55-9a7d-6d0b3e7f1a20")
    name = "TI_YBG0008_DSBGA-8_P0.4mm"
    w, h = 1.04 / 2, 1.59 / 2
    lines = fp_header(name, "BQ25188 YBG0008-C01 DSBGA-8, 0.4 mm pitch. Verified 1 Nov 2026 against TI SLUSFJ3 13.1 "
                            "(package outline, example board layout, example stencil): 0.23 mm NSMD pads, mask +0.05 mm, "
                            "0.25 mm square paste R0.05")
    lines += [fp_prop("Reference", "REF**", 0, -1.8, "F.SilkS"),
              fp_prop("Value", "TI_YBG0008", 0, 1.8, "F.Fab"),
              fp_rect(-w, -h, w, h, "F.Fab", 0.1), fp_rect(-0.8, -1.05, 0.8, 1.05, "F.CrtYd", 0.05),
              '\t(fp_line (start -0.67 -0.92) (end -0.25 -0.92) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
              '\t(fp_line (start -0.67 -0.92) (end -0.67 -0.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))']
    balls = [(r + c, -0.2 if c == "1" else 0.2, -0.6 + 0.4 * "ABCD".index(r)) for r in "ABCD" for c in "12"]
    for n, x, y in balls:
        lines.append(f'\t(pad "{n}" smd circle (at {x:g} {y:g}) (size 0.23 0.23) (property pad_prop_bga) '
                     f'(layers "F.Cu" "F.Mask") (solder_mask_margin 0.05) (uuid "{uuid.uuid5(ns, "lib:" + n)}"))')
    for n, x, y in balls:
        lines.append(f'\t(pad "" smd roundrect (at {x:g} {y:g}) (size 0.25 0.25) (layers "F.Paste") '
                     f'(roundrect_rratio 0.2) (uuid "{uuid.uuid5(ns, "lib:paste:" + n)}"))')
    lines += ["\t(embedded_fonts no)", ")"]
    with open(os.path.join(d, name + ".kicad_mod"), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


def write_footprints():
    d = os.path.join(PROJECT_DIR, LIB + ".pretty")
    os.makedirs(d, exist_ok=True)
    write_xfmr_placeholder(d)
    write_ybg_placeholder(d)


if __name__ == "__main__":
    write_symbol_lib()
    write_footprints()
    print("library written to", PROJECT_DIR)
