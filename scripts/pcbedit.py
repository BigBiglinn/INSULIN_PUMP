"""Surgical text edits of pump_v2.kicad_pcb without KiCad (31 Oct 2026 layout fixes).

Operations: move a footprint (translation only, rotation kept), delete tracks/vias by uuid,
add tracks/vias, and re-clip the stored zone fills around new or moved copper.

Zone fills: KiCad stores *fractured* fill polygons. This module only ever REMOVES fill copper
(clearance cut-outs around new/moved other-net items and SMD pads, thermal reliefs for moved
same-net through-hole pads, and removal of islands that lose every connection). It never adds
copper, so areas vacated by moved parts stay empty until the zones are refilled in KiCad
(press B, or kicad-cli pcb drc --refill-zones as in scripts/run_checks.sh). Refilling is REQUIRED
before any KiCad DRC result or any output is trusted.
"""
import math
import re
import uuid

from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union
from shapely.validation import make_valid

from pcbcheck import ZONE_CLR, Board

FMT = "{:.4f}"


def num(v):
    s = FMT.format(v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def new_uuid():
    return str(uuid.uuid4())


class PcbText:
    def __init__(self, path):
        self.path = path
        self.txt = open(path, encoding="utf8").read()
        self.nl = "\r\n" if b"\r\n" in open(path, "rb").read(4096) else "\n"   # keep the file's line endings
        self.log = []

    def save(self, path=None):
        open(path or self.path, "w", encoding="utf8", newline=self.nl).write(self.txt)

    def board(self):
        import os
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix=".kicad_pcb")
        os.close(fd)
        open(tmp, "w", encoding="utf8").write(self.txt)
        b = Board(tmp)
        os.remove(tmp)
        return b

    # ----------------------------------------------------------------- blocks
    def _block_at(self, start):
        """Return end index (exclusive) of the s-expression starting at start ('(')."""
        depth, i, n, ins = 0, start, len(self.txt), False
        t = self.txt
        while i < n:
            c = t[i]
            if ins:
                if c == "\\":
                    i += 2
                    continue
                if c == '"':
                    ins = False
            elif c == '"':
                ins = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise ValueError("unbalanced")

    def footprint_span(self, ref):
        m = re.search(r'\n\t\(footprint "[^"]*"\n(?:(?!\n\t\(footprint ).)*?\(property "Reference" "' + re.escape(ref) + '"',
                      self.txt, re.S)
        if not m:
            raise KeyError(ref)
        s = m.start() + 1
        return s, self._block_at(s)

    def move_fp(self, ref, x, y, rot=None):
        """Move a footprint; optional new absolute rotation (pad and text angles follow, as KiCad stores
        them absolute)."""
        s, e = self.footprint_span(ref)
        blk = self.txt[s:e]
        m = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)((?: [-\d.]+)?)\)", blk)
        old = (float(m.group(1)), float(m.group(2)))
        r0 = float(m.group(3)) if m.group(3).strip() else 0.0
        r1 = r0 if rot is None else float(rot) % 360
        nb = blk[:m.start()] + f"\n\t\t(at {num(x)} {num(y)}{'' if r1 == 0 else ' ' + num(r1)})" + blk[m.end():]
        if r1 != r0:
            d = r1 - r0

            def fix(mm):
                a = ((float(mm.group(3)) if mm.group(3) else 0.0) + d) % 360
                return f"{mm.group(1)}(at {mm.group(2)}{'' if abs(a) < 1e-9 else ' ' + num(a)})"
            # pad and property/text positions are one indentation level deeper than the footprint 'at'
            nb = re.sub(r"(\n\t\t\t)\(at ([-\d.]+ [-\d.]+)(?: ([-\d.]+))?\)", fix, nb)
        self.txt = self.txt[:s] + nb + self.txt[e:]
        self.log.append(f"move {ref}: ({old[0]:.3f}, {old[1]:.3f}, {r0:g}) -> ({x:.3f}, {y:.3f}, {r1:g})")
        return old

    def set_fp_text(self, ref, prop, x, y, angle=None):
        """Move a footprint property text (footprint-relative coordinates)."""
        s, e = self.footprint_span(ref)
        blk = self.txt[s:e]
        m = re.search(r'\(property "' + re.escape(prop) + r'" "[^"]*"\n\t\t\t\(at ([-\d.]+) ([-\d.]+)((?: [-\d.]+)?)\)', blk)
        a = m.group(3) if angle is None else f" {num(angle)}"
        nb = blk[:m.start(1) - 4] + f"(at {num(x)} {num(y)}{a})" + blk[m.end():]
        self.txt = self.txt[:s] + nb + self.txt[e:]
        self.log.append(f"silk {ref}.{prop} -> rel ({x}, {y})")

    def delete_uuid(self, u, what=""):
        m = re.search(r'\n\t\((segment|via|arc)\n(?:(?!\n\t\().)*?\(uuid "' + re.escape(u) + r'"\)\n\t\)', self.txt, re.S)
        if not m:
            raise KeyError(u)
        self.txt = self.txt[:m.start()] + self.txt[m.end():]
        self.log.append(f"delete {m.group(1)} {what} {u}")

    def _insert_items(self, block):
        k = self.txt.index("\n\t(zone\n")
        self.txt = self.txt[:k] + block + self.txt[k:]

    def add_segment(self, layer, p0, p1, w, net):
        u = new_uuid()
        self._insert_items(f'\n\t(segment\n\t\t(start {num(p0[0])} {num(p0[1])})\n\t\t(end {num(p1[0])} {num(p1[1])})\n'
                           f'\t\t(width {num(w)})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)')
        self.log.append(f"add segment {net.split('/')[-1]} {layer} ({p0[0]:.3f},{p0[1]:.3f})-({p1[0]:.3f},{p1[1]:.3f}) w{w}")
        return u

    def add_via(self, p, net, size=0.6, drill=0.3):
        u = new_uuid()
        self._insert_items(f'\n\t(via\n\t\t(at {num(p[0])} {num(p[1])})\n\t\t(size {num(size)})\n\t\t(drill {num(drill)})\n'
                           f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)')
        self.log.append(f"add via {net.split('/')[-1]} ({p[0]:.3f},{p[1]:.3f}) {size}/{drill}")
        return u

    def gr_text_mirror(self, text):
        """Mirror a B.SilkS gr_text (adds 'mirror' to its justify)."""
        m = re.search(r'\(gr_text "' + re.escape(text) + r'"\n(?:(?!\n\t\().)*?\(justify ([^)]*)\)', self.txt, re.S)
        j = m.group(1)
        if "mirror" not in j.split():
            self.txt = self.txt[:m.start(1)] + j + " mirror" + self.txt[m.end(1):]
            self.log.append(f"mirror B.SilkS text '{text[:30]}...'")

    # ----------------------------------------------------------------- zones
    def reclip_zones(self, changed_idx_fn):
        """Re-clip every zone fill against copper items selected by changed_idx_fn(board, item)."""
        b = self.board()
        changed = [it for it in b.items if it.kind != "zone" and it.layers and changed_idx_fn(b, it)]
        zspans = []
        for m in re.finditer(r"\n\t\(zone\n", self.txt):
            s = m.start() + 1
            zspans.append((s, self._block_at(s)))
        new_txt = self.txt
        stats = []
        for s, e in reversed(zspans):
            blk = self.txt[s:e]
            net = re.search(r'\(net "([^"]*)"\)', blk).group(1)
            layer = re.search(r'\n\t\t\(layer "([^"]*)"\)', blk).group(1)
            fills = [it for it in b.items if it.kind == "zone" and it.layers[0] == layer and it.data["zone"]["net"] == net
                     and it.data["zone"]["name"] == re.search(r'\(name "([^"]*)"\)', blk).group(1)]
            cut, add = [], []
            for it in changed:
                if layer not in it.layers:
                    continue
                if it.net != net or not it.net:
                    clr = max(ZONE_CLR, b.clearance(it.net) if it.net else 0.15, b.clearance(net)) + 0.01
                    cut.append(it.geom.buffer(clr, quad_segs=8))
                elif it.kind == "pad" and it.data["kind"] == "smd":
                    cut.append(it.geom.buffer(ZONE_CLR + 0.01, quad_segs=8))
                elif it.kind == "pad" and it.data["kind"] == "thru_hole":
                    # thermal relief (gap 0.3, 4 spokes 0.35 wide), as the zone settings ask
                    cut.append(it.geom.buffer(ZONE_CLR, quad_segs=8))
                    cx, cy = it.data["c"]
                    r = max(it.data["size"]) / 2 + ZONE_CLR + 0.05
                    add.append(unary_union([box(cx - r, cy - 0.175, cx + r, cy + 0.175),
                                            box(cx - 0.175, cy - r, cx + 0.175, cy + r)]))
            if not cut:
                continue
            cutu = unary_union(cut)
            other_cut = unary_union([c for c in cut if not any(c.intersects(a) for a in add)]) if add else None
            pieces = []
            for fz in fills:
                g = fz.geom
                ng = g.difference(cutu)
                for spokes in add:
                    if g.intersects(spokes):
                        sp = spokes.intersection(g)
                        if other_cut is not None and not other_cut.is_empty:
                            sp = sp.difference(other_cut)
                        ng = ng.union(sp)
                ng = make_valid(ng).buffer(-0.1, quad_segs=4).buffer(0.1, quad_segs=4)  # min_thickness 0.2
                for p in getattr(ng, "geoms", [ng]):
                    if p.geom_type == "Polygon" and p.area > 0.05:
                        pieces.append(p)
            # island removal: keep pieces touching a same-net non-zone item on this layer
            same = [it.geom for it in b.items if it.net == net and it.kind != "zone" and layer in it.layers]
            sameu = unary_union(same)
            kept = [p for p in pieces if p.intersects(sameu)]
            stats.append(f"{layer} {net}: {len(fills)} fill polygons -> {len(kept)} ({len(pieces) - len(kept)} islands dropped)")
            nb = re.sub(r"\n\t\t\(filled_polygon\n.*?\n\t\t\)(?=\n)", "", blk, flags=re.S)
            k = nb.rindex("\n\t)")
            nb = nb[:k] + "".join(_fp_text(layer, p) for p in kept) + nb[k:]
            new_txt = new_txt[:s] + nb + new_txt[e:]
        self.txt = new_txt
        self.log += ["reclip " + x for x in stats]
        return stats


def _fp_text(layer, poly):
    pts = fracture(poly)
    lines = []
    for i in range(0, len(pts), 5):
        lines.append("\t\t\t\t" + " ".join(f"(xy {num(x)} {num(y)})" for x, y in pts[i:i + 5]))
    return f'\n\t\t(filled_polygon\n\t\t\t(layer "{layer}")\n\t\t\t(pts\n' + "\n".join(lines) + "\n\t\t\t)\n\t\t)"


def fracture(poly):
    """Polygon with holes -> single ring with zero-width bridges (KiCad's fractured form).
    Holes are bridged leftwards from their leftmost vertex, in order of that x."""
    ext = list(poly.exterior.coords)[:-1]
    holes = sorted((list(h.coords)[:-1] for h in poly.interiors), key=lambda r: min(p[0] for p in r))
    ring = ext[:]
    for h in holes:
        k = min(range(len(h)), key=lambda i: (h[i][0], h[i][1]))
        hx, hy = h[k]
        best = None
        n = len(ring)
        for i in range(n):
            (ax, ay), (bx, by) = ring[i], ring[(i + 1) % n]
            if (ay - hy) * (by - hy) > 0 or ay == by:
                if ay == by == hy and min(ax, bx) < hx:
                    xi = max(ax, bx) if max(ax, bx) < hx else None
                    if xi is not None and (best is None or xi > best[0]):
                        best = (xi, i, (xi, hy))
                continue
            t = (hy - ay) / (by - ay)
            xi = ax + t * (bx - ax)
            if xi < hx - 1e-9 and (best is None or xi > best[0]):
                best = (xi, i, (xi, hy))
        if best is None:
            continue
        _, i, p = best
        hr = h[k:] + h[:k] + [h[k]]
        ring = ring[:i + 1] + [p] + hr + [p] + ring[i + 1:]
    return ring


def uuid_of(it):
    for x in it.data["node"]:
        if isinstance(x, list) and x and x[0] == "uuid":
            return x[1].strip('"')
    return None


class Session:
    """Keeps the PCB text and the in-memory geometry model in step, so routing can see every edit."""

    def __init__(self, path):
        from pcbcheck import Board
        self.t = PcbText(path)
        self.b = Board(path)

    def move(self, ref, x, y, rot=None):
        from pcbcheck import mem_move_fp
        self.t.move_fp(ref, x, y, rot)
        mem_move_fp(self.b, ref, x, y, rot)

    def remove(self, items, why=""):
        from pcbcheck import mem_remove, short
        for it in items:
            self.t.delete_uuid(uuid_of(it), f"{short(it.net)} {why}")
        mem_remove(self.b, items)

    def seg(self, layer, p0, p1, w, net):
        from pcbcheck import mem_add_track
        u = self.t.add_segment(layer, p0, p1, w, net)
        return mem_add_track(self.b, layer, p0, p1, w, net, u)

    def via(self, p, net, d=0.6, drill=0.3):
        from pcbcheck import mem_add_via
        u = self.t.add_via(p, net, d, drill)
        return mem_add_via(self.b, p, net, d, drill, u)

    def apply_route(self, r, net, w, via=(0.6, 0.3)):
        out = [self.seg(L, p0, p1, w, net) for L, p0, p1 in r[0]]
        out += [self.via(p, net, *via) for p in r[1]]
        return out

    def snapshot(self):
        import copy
        return (self.t.txt, list(self.t.log), copy.copy(self.b.items), copy.deepcopy(
            {k: {kk: vv for kk, vv in v.items() if kk != "node"} for k, v in self.b.footprints.items()}))

    def restore(self, snap):
        from pcbcheck import _reindex
        self.t.txt, self.t.log, items, fps = snap[0], list(snap[1]), snap[2], snap[3]
        self.b.items = list(items)
        _reindex(self.b)
        for k, v in fps.items():
            self.b.footprints[k].update(v)
