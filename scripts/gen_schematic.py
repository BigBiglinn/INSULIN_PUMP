"""Write the hierarchical KiCad 10 schematic for Piezo Insulin Pump v2 from design.py.

Every pin gets a short wire stub and a net label (local label if the net lives on one
sheet, global label if it crosses sheets). UUIDs are deterministic (uuid5) so that
re-running the generator keeps schematic <-> PCB links stable.

Usage:  python gen_schematic.py
"""
import json
import os
import uuid
from collections import defaultdict

import design
from kicadlib import PROJECT_DIR, dump, get_symbol, symbol_pins, symbol_property

PROJECT = "pump_v2"
NS = uuid.UUID("6b1c3d8e-2f57-4a8e-9a0e-0d8a5f1c2b70")
G = 2.54
STUB = 2.54
DATE = "2026-10-10"
REV = "B-draft-handover"


def uid(*key):
    return str(uuid.uuid5(NS, ":".join(key)))


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def snap(v, g=G):
    return round(round(v / g) * g, 4)


def label_len(net, glob):
    return len(net) * 1.1 + (5.0 if glob else 2.0)


OUT_DIR = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # schematic outward direction per lib pin angle
LBL_ANG = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}


class Placed:
    def __init__(self, part, glob_nets):
        self.part = part
        self.lib_id = part.lib_id
        pins = symbol_pins(part.lib_id)
        # choose unit 1 (or 0 for unit-less symbols)
        self.pins = [p for p in pins if p["unit"] in (0, 1)]
        xs, ys = [], []
        self.body = [1e9, 1e9, -1e9, -1e9]
        for p in self.pins:
            dx, dy = OUT_DIR[p["angle"]]
            sx, sy = p["x"], -p["y"]            # schematic coords relative to origin
            # inner end of pin -> body extent
            ix, iy = sx - dx * p["length"], sy - dy * p["length"]
            self.body = [min(self.body[0], ix), min(self.body[1], iy), max(self.body[2], ix), max(self.body[3], iy)]
            net = part.nets.get(p["number"])
            ext = 0
            if net:
                ext = STUB + label_len(net, net in glob_nets)
            xs += [sx, sx + dx * ext]
            ys += [sy, sy + dy * ext]
        if not self.pins:
            self.body = [-2.54, -2.54, 2.54, 2.54]
            xs, ys = [-2.54, 2.54], [-2.54, 2.54]
        bx0, by0, bx1, by1 = self.body
        if bx1 - bx0 < 2.6:                     # 2-pin vertical part: widen for text
            self.body = [bx0 - 1.3, by0, bx1 + 1.3, by1]
        if by1 - by0 < 2.6:
            self.body = [self.body[0], by0 - 1.3, self.body[2], by1 + 1.3]
        self.vertical2 = (len(self.pins) <= 2 and all(p["angle"] in (90, 270) for p in self.pins))
        txt_w = 14.0 if self.vertical2 else 0
        self.bbox = [min(xs + [self.body[0]]) - 1.0, min(ys + [self.body[1]]) - 6.0,
                     max(xs + [self.body[2]]) + 1.0 + txt_w, max(ys + [self.body[3]]) + 6.0]
        self.x = self.y = 0.0


def layout(placed, top, width):
    x0, cx, cy, row_h = 15.0, 15.0, top, 0.0
    for p in placed:
        w = p.bbox[2] - p.bbox[0]
        h = p.bbox[3] - p.bbox[1]
        if cx + w > x0 + width and cx > x0:
            cx = x0
            cy += row_h + 4.0
            row_h = 0.0
        p.x = snap(cx - p.bbox[0] + G / 2, G)
        p.y = snap(cy - p.bbox[1] + G / 2, G)
        cx += w + 5.0
        row_h = max(row_h, h)
    return cy + row_h


def paper_for(height_needed, width_used):
    if height_needed < 270 and width_used <= 400:
        return "A3", 420, 297
    if height_needed < 395:
        return "A2", 594, 420
    return "A1", 841, 594


def eff(size=1.27, justify=None, hide=False):
    j = f" (justify {justify})" if justify else ""
    h = " (hide yes)" if hide else ""
    return f"(effects (font (size {size:g} {size:g})){j}{h})"


def symbol_block(pl, path, project_root_uuid):
    p = pl.part
    lines = []
    fp = p.footprint if p.footprint is not None else (symbol_property(p.lib_id, "Footprint") or "")
    is_virtual = p.ref.startswith("#")
    mech = p.lib_id in ("Mechanical:MountingHole", "Connector:TestPoint")
    in_bom = "no" if (is_virtual or mech) else "yes"
    on_board = "no" if is_virtual else "yes"
    sid = uid("sym", p.ref)
    lines.append(f'\t(symbol\n\t\t(lib_id {q(p.lib_id)})\n\t\t(at {pl.x:g} {pl.y:g} 0)\n\t\t(unit 1)')
    lines.append(f'\t\t(exclude_from_sim no)\n\t\t(in_bom {in_bom})\n\t\t(on_board {on_board})\n'
                 f'\t\t(dnp {"yes" if p.dnp else "no"})\n\t\t(uuid "{sid}")')
    bx0, by0, bx1, by1 = pl.body
    if pl.vertical2:
        rpos = (pl.x + bx1 + 1.27, pl.y - 1.27, "left")
        vpos = (pl.x + bx1 + 1.27, pl.y + 1.27, "left")
        spos = (pl.x + bx1 + 1.27, pl.y + 3.5, "left")
    else:
        rpos = (pl.x + (bx0 + bx1) / 2, pl.y + by0 - 1.8, None)
        vpos = (pl.x + (bx0 + bx1) / 2, pl.y + by1 + 1.8, None)
        spos = (pl.x + (bx0 + bx1) / 2, pl.y + by1 + 4.0, None)
    show_status = p.status in ("TBD", "PLACEHOLDER")
    props = [
        ("Reference", p.ref, rpos, False, 1.27),
        ("Value", p.value, vpos, False, 1.27),
        ("Footprint", fp, (pl.x, pl.y, None), True, 1.27),
        ("Datasheet", symbol_property(p.lib_id, "Datasheet") or "", (pl.x, pl.y, None), True, 1.27),
        ("Description", symbol_property(p.lib_id, "Description") or "", (pl.x, pl.y, None), True, 1.27),
        ("MPN", p.mpn, (pl.x, pl.y, None), True, 1.27),
        ("Status", p.status, spos, not show_status, 1.0),
        ("Note", p.note, (pl.x, pl.y, None), True, 1.27),
    ]
    for name, val, (x, y, j), hide, size in props:
        if is_virtual and name in ("MPN", "Status", "Note"):
            continue
        lines.append(f'\t\t(property {q(name)} {q(val)}\n\t\t\t(at {x:g} {y:g} 0)\n\t\t\t{eff(size, j, hide)}\n\t\t)')
    for pin in pl.pins:
        lines.append(f'\t\t(pin {q(pin["number"])}\n\t\t\t(uuid "{uid("pin", p.ref, pin["number"])}")\n\t\t)')
    lines.append(f'\t\t(instances\n\t\t\t(project {q(PROJECT)}\n\t\t\t\t(path {q(path)}\n'
                 f'\t\t\t\t\t(reference {q(p.ref)})\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
    return "\n".join(lines)


def connections(pl, glob_nets, sheet_key):
    out = []
    seen = set()
    for pin in pl.pins:
        px, py = pl.x + pin["x"], pl.y - pin["y"]
        px, py = round(px, 4), round(py, 4)
        num = pin["number"]
        if num in pl.part.nc:
            out.append(f'\t(no_connect\n\t\t(at {px:g} {py:g})\n\t\t(uuid "{uid("nc", pl.part.ref, num)}")\n\t)')
            continue
        net = pl.part.nets.get(num)
        if not net:
            continue
        if (px, py) in seen:
            continue
        seen.add((px, py))
        dx, dy = OUT_DIR[pin["angle"]]
        lx, ly = round(px + dx * STUB, 4), round(py + dy * STUB, 4)
        out.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {px:g} {py:g}) (xy {lx:g} {ly:g})\n\t\t)\n'
                   f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
                   f'\t\t(uuid "{uid("w", pl.part.ref, num)}")\n\t)')
        ang = LBL_ANG[(dx, dy)]
        just = "left" if ang in (0, 90) else "right"
        lid = uid("lbl", pl.part.ref, num)
        if net in glob_nets:
            out.append(f'\t(global_label {q(net)}\n\t\t(shape passive)\n\t\t(at {lx:g} {ly:g} {ang})\n'
                       f'\t\t(fields_autoplaced yes)\n\t\t{eff(1.27, just)}\n\t\t(uuid "{lid}")\n'
                       f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {lx:g} {ly:g} 0)\n'
                       f'\t\t\t{eff(1.27, None, True)}\n\t\t)\n\t)')
        else:
            out.append(f'\t(label {q(net)}\n\t\t(at {lx:g} {ly:g} {ang})\n\t\t(fields_autoplaced yes)\n'
                       f'\t\t{eff(1.27, just + " bottom")}\n\t\t(uuid "{lid}")\n\t)')
    return out


def title_block(title, page_comment):
    return (f'\t(title_block\n\t\t(title {q(title)})\n\t\t(date {q(DATE)})\n\t\t(rev {q(REV)})\n'
            f'\t\t(company "Piezo Insulin Pump v2 - BENCH ONLY (water/saline), never on a person or animal")\n'
            f'\t\t(comment 1 "NOT fabrication-approved. Contains TBD / PLACEHOLDER parts - see Status field and docs/handover")\n'
            f'\t\t(comment 2 "ERC/DRC clean status does not prove electrical correctness")\n'
            f'\t\t(comment 3 {q(page_comment)})\n\t)')


def lib_symbols_block(lib_ids):
    parts = []
    for lid in sorted(lib_ids):
        parts.append(dump(get_symbol(lid), 2))
    return "\t(lib_symbols\n" + "\n".join(parts) + "\n\t)"


def text_note(txt, x, y, key, size=1.5):
    return (f'\t(text {q(txt)}\n\t\t(exclude_from_sim no)\n\t\t(at {x:g} {y:g} 0)\n'
            f'\t\t{eff(size, "left top")}\n\t\t(uuid "{uid("txt", key)}")\n\t)')


def write_sheet(sheet, path, glob_nets, file_uuid, extra_items=(), page_comment=""):
    placed = [Placed(p, glob_nets) for p in sheet.parts]
    note_lines = sum(n.count("\n") + 1 for n in sheet.notes)
    top = 22.0 + note_lines * 2.6 + (6 if sheet.notes else 0)
    width = 390.0
    h = layout(placed, top, width)
    paper, pw, ph = paper_for(h, width)
    if paper != "A3":
        width = pw - 30
        h = layout(placed, top, width)
        paper, pw, ph = paper_for(h, width)
    # overlapping pins with different nets would be a silent short - refuse
    for pl in placed:
        pos = {}
        for pin in pl.pins:
            k = (round(pin["x"], 3), round(pin["y"], 3))
            n = pl.part.nets.get(pin["number"], "NC" if pin["number"] in pl.part.nc else None)
            if k in pos and pos[k] != n and None not in (n, pos[k]):
                raise RuntimeError(f"{pl.part.ref}: stacked pins at {k} on different nets {pos[k]} / {n}")
            pos[k] = n
    body = [f'(kicad_sch\n\t(version 20250610)\n\t(generator "pump_v2_gen")\n\t(generator_version "10.0")\n'
            f'\t(uuid "{file_uuid}")\n\t(paper "{paper}")',
            title_block(sheet.title, page_comment),
            lib_symbols_block({pl.lib_id for pl in placed})]
    y = 20.0
    for i, n in enumerate(sheet.notes):
        body.append(text_note(n, 15, y, sheet.file + str(i)))
        y += (n.count("\n") + 1) * 2.6 + 2
    for item in extra_items:
        body.append(item)
    for pl in placed:
        body.extend(connections(pl, glob_nets, sheet.file))
    for pl in placed:
        body.append(symbol_block(pl, path, None))
    return body, placed


def main():
    root, sheets = design.build()
    os.makedirs(PROJECT_DIR, exist_ok=True)
    # nets crossing sheets -> global
    where = defaultdict(set)
    for sh in [root] + sheets:
        for p in sh.parts:
            for n in p.nets.values():
                where[n].add(sh.file)
    glob_nets = {n for n, s in where.items() if len(s) > 1}
    root_uuid = uid("sheetfile", root.file)
    sheet_uuids = {sh.file: uid("sheet", sh.file) for sh in sheets}

    # ---- sub-sheets
    for i, sh in enumerate(sheets):
        path = f"/{root_uuid}/{sheet_uuids[sh.file]}"
        body, _ = write_sheet(sh, path, glob_nets, uid("sheetfile", sh.file), page_comment=f"Sheet {i + 2}: {sh.name}")
        body.append("\t(embedded_fonts no)\n)")
        with open(os.path.join(PROJECT_DIR, sh.file), "w", encoding="utf8", newline="\n") as f:
            f.write("\n".join(body) + "\n")

    # ---- root sheet: sheet symbols + mechanical parts + notes
    items = []
    bw, bh = 70.0, 20.0
    for i, sh in enumerate(sheets):
        col, row = i % 4, i // 4
        x, y = 20 + col * (bw + 25), 95 + row * (bh + 25)
        su = sheet_uuids[sh.file]
        items.append(
            f'\t(sheet\n\t\t(at {x:g} {y:g})\n\t\t(size {bw:g} {bh:g})\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n'
            f'\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n\t\t(uuid "{su}")\n'
            f'\t\t(property "Sheetname" {q(sh.name)}\n\t\t\t(at {x:g} {y - 0.7:g} 0)\n\t\t\t{eff(1.5, "left bottom")}\n\t\t)\n'
            f'\t\t(property "Sheetfile" {q(sh.file)}\n\t\t\t(at {x:g} {y + bh + 0.6:g} 0)\n\t\t\t{eff(1.27, "left top")}\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project {q(PROJECT)}\n\t\t\t\t(path "/{root_uuid}"\n\t\t\t\t\t(page "{i + 2}")\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        items.append(text_note(sh.title, x + 2, y + 4, "sheetdesc" + sh.file, 1.27))
    body, placed = write_sheet(root, f"/{root_uuid}", glob_nets, root_uuid, extra_items=items,
                               page_comment="Root: hierarchy, mounting, disclaimers")
    # move root mechanical parts below the sheet blocks
    body.append(f'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)')
    txt = "\n".join(body) + "\n"
    with open(os.path.join(PROJECT_DIR, root.file), "w", encoding="utf8", newline="\n") as f:
        f.write(txt)

    write_project_files(root_uuid, sheets, sheet_uuids)
    print("schematic written:", root.file, "+", len(sheets), "sheets;", sum(len(s.parts) for s in [root] + sheets), "parts;",
          len(glob_nets), "global nets")


HV_NETS = ["+48V_RAW", "+48V_MOT", "FLY_SEC", "SW48_GATE", "SW48_DRV"]
PWR_NETS = ["VBAT", "VBAT_RAW", "VBAT_FUSED", "FLY_SW", "FLY_CS", "FLY_CLAMP", "BUCK_SW", "VBUS_CHG", "+3V3", "GND"]
RF_NETS = ["RF_MCU", "RF_ANT"]


def netclass(name, clearance, track, via_d=0.6, via_drill=0.3, prio=0, color="rgba(0, 0, 0, 0.000)"):
    return {"bus_width": 12, "clearance": clearance, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": name, "pcb_color": color, "priority": prio, "schematic_color": "rgba(0, 0, 0, 0.000)",
            "track_width": track, "tuning_profile": "", "via_diameter": via_d, "via_drill": via_drill, "wire_width": 6}


def write_project_files(root_uuid, sheets, sheet_uuids):
    pro_path = os.path.join(PROJECT_DIR, PROJECT + ".kicad_pro")
    pro = {}
    if os.path.exists(pro_path):
        with open(pro_path, encoding="utf8") as f:
            pro = json.load(f)
    pro["meta"] = {"filename": PROJECT + ".kicad_pro", "version": 3}
    pro["sheets"] = [[root_uuid, "Root"]] + [[sheet_uuids[s.file], s.name] for s in sheets]
    pro["net_settings"] = {
        "classes": [
            netclass("Default", 0.15, 0.2, prio=2147483647),
            netclass("HV48", 0.6, 0.4, prio=0, color="rgb(255, 0, 0)"),
            netclass("PWR", 0.2, 0.6, via_d=0.7, via_drill=0.35, prio=1, color="rgb(255, 153, 0)"),
            netclass("RF", 0.2, 0.3, prio=2, color="rgb(0, 194, 255)"),
        ],
        "meta": {"version": 5},
        "netclass_assignments": None,
        "netclass_patterns": ([{"netclass": "HV48", "pattern": n} for n in HV_NETS] +
                              [{"netclass": "PWR", "pattern": n} for n in PWR_NETS] +
                              [{"netclass": "RF", "pattern": n} for n in RF_NETS]),
    }
    erc = pro.setdefault("erc", {})
    erc.setdefault("erc_exclusions", [])
    with open(pro_path, "w", encoding="utf8") as f:
        json.dump(pro, f, indent=2)
    with open(os.path.join(PROJECT_DIR, "sym-lib-table"), "w", encoding="utf8") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "pump_v2")(type "KiCad")(uri "${KIPRJMOD}/pump_v2.kicad_sym")'
                '(options "")(descr "Piezo Insulin Pump v2 project symbols"))\n)\n')
    with open(os.path.join(PROJECT_DIR, "fp-lib-table"), "w", encoding="utf8") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "pump_v2")(type "KiCad")(uri "${KIPRJMOD}/pump_v2.pretty")'
                '(options "")(descr "Piezo Insulin Pump v2 project footprints and placeholders"))\n)\n')


if __name__ == "__main__":
    main()
