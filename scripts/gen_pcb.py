"""Build the Piezo Insulin Pump v2 Rev B handover PCB from the KiCad netlist.

Run with KiCad's bundled Python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/gen_pcb.py place     # board, placement, zones
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/gen_pcb.py dsn       # export Specctra DSN
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/gen_pcb.py ses FILE  # import routed SES, refill

Board rules here are GENERIC 4-layer values (not a specific fab's rule file, OPEN B.7).
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from kicadlib import FP_DIR, PROJECT_DIR, find, find1, parse, unq  # noqa: E402

BOARD = os.path.join(PROJECT_DIR, "pump_v2.kicad_pcb")
NETLIST = os.path.join(PROJECT_DIR, "pump_v2.net")
MM = pcbnew.FromMM

# Board outline (mm, KiCad page coordinates). 110 x 85 mm chosen to fit the parts;
# board size is not fixed in the requirements (OPEN B.6).
X0, Y0, BW, BH = 100.0, 100.0, 110.0, 85.0
X1, Y1 = X0 + BW, Y0 + BH


import time
_T0 = time.time()


def log(msg):
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# ----------------------------------------------------------------- netlist
def read_netlist():
    t = parse(open(NETLIST, encoding="utf8").read())[0]
    comps = []
    for c in find(find1(t, "components"), "comp"):
        props = {}
        for p in find(c, "property"):
            name = unq(find1(p, "name")[1])
            v = find1(p, "value")
            props[name] = unq(v[1]) if v else ""
        fields = []
        fl = find1(c, "fields")
        if fl:
            for f in find(fl, "field"):
                name = unq(find1(f, "name")[1])
                toks = [x for x in f[1:] if not isinstance(x, list)]
                val = unq(toks[0]) if toks else ""
                fields.append((name, val))
        sp = find1(c, "sheetpath")
        comps.append({
            "ref": unq(find1(c, "ref")[1]), "value": unq(find1(c, "value")[1]),
            "footprint": unq(find1(c, "footprint")[1]) if find1(c, "footprint") else "",
            "sheet_ts": unq(find1(sp, "tstamps")[1]), "sheet_name": unq(find1(sp, "names")[1]),
            "ts": unq(find1(c, "tstamps")[1]), "props": props, "fields": fields,
        })
    nets = []
    for n in find(find1(t, "nets"), "net"):
        nodes = [(unq(find1(x, "ref")[1]), unq(find1(x, "pin")[1])) for x in find(n, "node")]
        nets.append((unq(find1(n, "name")[1]), nodes))
    return comps, nets


def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    if lib == "pump_v2":
        path = os.path.join(PROJECT_DIR, "pump_v2.pretty")
    else:
        path = os.path.join(FP_DIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found: " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ----------------------------------------------------------------- placement
# Explicit positions for anchor parts: (x, y, rotation_deg, side) ; side "F" only.
# Functional zones (P-03 proposed, used as a sensible default): 48 V stage bottom-right,
# PMD401 connectors right edge, MCUs centre, battery/charger left edge, RF at top edge.
ANCHORS = {
    # power input - left edge (connectors face -x)
    "J103": (0, 115.0, None), "U101": (118.0, 113.0, 0),
    "J102": (0, 138.0, None),
    "J101": (0, 160.0, None), "F101": (123.0, 160.0, 90),
    # 3V3 buck
    "U201": (122.0, 140.0, 0), "L201": (125.5, 140.0, 90),
    # main MCU (U.FL at top edge)
    "U501": (148.0, 119.0, 0), "J501": (148.0, 103.5, 0),
    "J502": (134.0, 107.0, 0), "J503": (163.0, 104.5, 90),
    # supervisor
    "U601": (150.0, 160.0, 0), "J601": (137.0, 169.0, 0),
    # kill path
    "Q401": (172.0, 136.0, 0),
    # PMD401 & encoder - right edge, connectors face +x
    "J701": (0, 112.0, None), "J702": (0, 121.0, None), "J704": (0, 130.0, None),
    "J705": (0, 139.0, None), "J703": (0, 148.0, None), "U701": (192.0, 130.0, 0),
    "C702": (199.0, 164.0, 0),
    # 48 V flyback - bottom right
    "T301": (180.0, 158.0, 0), "Q301": (170.0, 165.0, 0), "U301": (171.0, 152.0, 0),
    "D301": (190.0, 152.0, 0), "C311": (186.0, 170.0, 0), "C301": (162.0, 170.0, 0),
    "R305": (174.0, 172.0, 0),
    # mounting holes
    "H901": (X0 + 3.5, Y0 + 3.5, 0), "H902": (X1 - 3.5, Y0 + 3.5, 0),
    "H903": (X0 + 3.5, Y1 - 3.5, 0), "H904": (X1 - 3.5, Y1 - 3.5, 0),
}
EDGE_FACING = {"J701": "+x", "J702": "+x", "J703": "+x", "J704": "+x", "J705": "+x",
               "J101": "-x", "J102": "-x", "J103": "-x"}

# Region (x0, y0, x1, y1) where the remaining parts of each sheet are packed.
REGIONS = {
    "/Power input & charger/": (109.0, 122.0, 131.0, 132.0),
    "/3V3 buck/": (117.0, 145.0, 131.0, 152.0),
    "/Main MCU STM32WBA55/": (130.0, 129.0, 168.0, 143.0),
    "/Supervisor STM32C031/": (156.0, 152.0, 164.0, 158.0),
    "/Kill path (fail-off)/": (166.0, 126.0, 184.0, 140.0),
    "/PMD401 & encoder interface/": (168.0, 101.5, 199.0, 123.0),
    "/48V flyback/": (156.0, 141.0, 186.0, 149.5),
}
# Overflow regions used when the first region is full
REGIONS2 = {
    "/48V flyback/": (156.0, 176.0, 207.0, 184.0),
    "/Supervisor STM32C031/": (140.0, 176.0, 155.0, 184.0),
}
# Small support parts that should hug their IC instead of the region
NEAR = {
    "U501": ["C501", "C502", "C503", "C504", "C505", "C506", "C507", "C508", "L501", "C509", "Y501"],
    "U601": ["C601", "C602", "C603", "C604"],
    "U101": ["C101", "C102", "C103", "R101"],
    "U201": ["R201", "C201", "C202"],
    "U301": ["C304", "R301", "C305", "R302", "R303", "C306", "C307", "R307", "R308"],
}


def courtyard_bbox(fp):
    """Courtyard bounding box (falls back to the body bbox without text)."""
    try:
        fp.BuildCourtyardCaches()
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0:
            bb = cy.BBox()
            if 0 < bb.GetWidth() < MM(200) and 0 < bb.GetHeight() < MM(200):
                return bb
    except Exception:
        pass
    return fp.GetBoundingBox(False)


def size_mm(fp):
    bb = courtyard_bbox(fp)
    return pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())


def place_at(fp, x, y, rot):
    fp.SetOrientationDegrees(rot or 0)
    # position so that the courtyard centre lands on (x, y)
    fp.SetPosition(V(0, 0))
    bb = courtyard_bbox(fp)
    cx, cy = pcbnew.ToMM(bb.GetCenter().x), pcbnew.ToMM(bb.GetCenter().y)
    fp.SetPosition(V(x - cx, y - cy))


def face_edge(fp, direction):
    """Rotate an edge connector so its body (mating side) points to the given board edge.

    Heuristic: mating direction = F.Fab bbox centre minus centroid of numbered pads.
    Orientation is therefore DERIVED, not verified against connector drawings.
    """
    fp.SetOrientationDegrees(0)
    fp.SetPosition(V(0, 0))
    pads = [p for p in fp.Pads() if p.GetNumber() not in ("", "MP", "SH")] or list(fp.Pads())
    px = sum(p.GetPosition().x for p in pads) / len(pads)
    py = sum(p.GetPosition().y for p in pads) / len(pads)
    fab = None
    for item in fp.GraphicalItems():
        if item.GetLayer() == pcbnew.F_Fab:
            b = item.GetBoundingBox()
            if fab is None:
                fab = [b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()]
            else:
                fab = [min(fab[0], b.GetLeft()), min(fab[1], b.GetTop()), max(fab[2], b.GetRight()), max(fab[3], b.GetBottom())]
    if fab:
        c = pcbnew.VECTOR2I(int((fab[0] + fab[2]) / 2), int((fab[1] + fab[3]) / 2))
    else:
        c = fp.GetBoundingBox(False).GetCenter()
    ang = math.degrees(math.atan2(-(c.y - py), c.x - px))   # 0 = +x, 90 = up (-y)
    want = {"+x": 0, "-x": 180, "-y": 90, "+y": -90}[direction]
    fp.SetOrientationDegrees((want - ang) % 360)


def pack(fps, region, occupied, region2=None):
    """First-fit: for each part scan a 0.5 mm grid in region, then region2."""
    regions = [region] + ([region2] if region2 else [])
    gap = 0.5
    for fp in fps:
        fp.SetOrientationDegrees(0)
        w, h = size_mm(fp)
        spot = None
        for (x0, y0, x1, y1) in regions:
            y = y0
            while spot is None and y + h <= y1:
                x = x0
                while x + w <= x1:
                    r = (x, y, x + w, y + h)
                    if not any(not (r[2] + gap <= o[0] or r[0] - gap >= o[2] or r[3] + gap <= o[1] or r[1] - gap >= o[3])
                               for o in occupied):
                        spot = r
                        break
                    x += 0.5
                y += 0.5
            if spot:
                break
        if spot is None:
            print("WARNING no space for", fp.GetReference(), "in", regions)
            continue
        place_at(fp, (spot[0] + spot[2]) / 2, (spot[1] + spot[3]) / 2, 0)
        occupied.append(spot)


def occ_rect(fp):
    bb = courtyard_bbox(fp)
    return (pcbnew.ToMM(bb.GetLeft()) - 0.3, pcbnew.ToMM(bb.GetTop()) - 0.3,
            pcbnew.ToMM(bb.GetRight()) + 0.3, pcbnew.ToMM(bb.GetBottom()) + 0.3)


def near_pack(anchor, parts, occupied):
    """Ring-pack support parts around an anchor footprint."""
    ab = occ_rect(anchor)
    ring = 0
    todo = list(parts)
    while todo and ring < 12:
        x0, y0, x1, y1 = ab[0] - 1.2 - 2.2 * ring, ab[1] - 1.2 - 2.2 * ring, ab[2] + 1.2 + 2.2 * ring, ab[3] + 1.2 + 2.2 * ring
        cand = []
        step = 1.0
        x = x0
        while x <= x1:
            cand += [(x, y0), (x, y1)]
            x += step
        y = y0
        while y <= y1:
            cand += [(x0, y), (x1, y)]
            y += step
        rest = []
        for fp in todo:
            fp.SetOrientationDegrees(0)
            w, h = size_mm(fp)
            ok = False
            for (cx, cy) in cand:
                rect = (cx - w / 2 - 0.6, cy - h / 2 - 0.6, cx + w / 2 + 0.6, cy + h / 2 + 0.6)
                if rect[0] < X0 + 1 or rect[1] < Y0 + 1 or rect[2] > X1 - 1 or rect[3] > Y1 - 1:
                    continue
                if any(not (rect[2] <= o[0] or rect[0] >= o[2] or rect[3] <= o[1] or rect[1] >= o[3]) for o in occupied):
                    continue
                place_at(fp, cx, cy, 0)
                occupied.append(rect)
                ok = True
                break
            if not ok:
                rest.append(fp)
        todo = rest
        ring += 1
    return todo


# ----------------------------------------------------------------- board build
def setup_board(board):
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_MinClearance = MM(0.15)
    ds.m_ViasMinSize = MM(0.5)
    ds.m_ViasMinAnnularWidth = MM(0.1)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.m_HoleClearance = MM(0.25)
    ds.m_HoleToHoleMin = MM(0.25)
    ds.m_SilkClearance = MM(0.0)
    tb = board.GetTitleBlock()
    tb.SetTitle("Piezo Insulin Pump v2 - Rev B HANDOVER PROTOTYPE (not fab-approved)")
    tb.SetRevision("B-draft-handover")
    tb.SetDate("2026-10-10")
    tb.SetComment(0, "BENCH ONLY - water/saline - never on a person or animal")
    tb.SetComment(1, "Generic 4-layer rules; replace with the fab's rule file (OPEN B.7)")
    # outline
    pts = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(*pts[i]))
        seg.SetEnd(V(*pts[(i + 1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.1))
        board.Add(seg)


def add_text(board, txt, x, y, layer, size=1.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(size * 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def add_zone(board, net, layer, poly, prio=0, clearance=0.3, name=""):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD solid, THT thermal
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetIsFilled(False)
    if name:
        z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in poly:
        o.Append(MM(x), MM(y))
    board.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ----------------------------------------------------------------- plane fan-out
def _pad_box(pad, grow=0.0):
    bb = pad.GetBoundingBox()
    return (pcbnew.ToMM(bb.GetLeft()) - grow, pcbnew.ToMM(bb.GetTop()) - grow,
            pcbnew.ToMM(bb.GetRight()) + grow, pcbnew.ToMM(bb.GetBottom()) + grow)


def _seg_hits_box(x0, y0, x1, y1, b, steps=12):
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i / steps
        y = y0 + (y1 - y0) * i / steps
        if b[0] <= x <= b[2] and b[1] <= y <= b[3]:
            return True
    return False


HV_SUFFIX = ("+48V_RAW", "+48V_MOT", "FLY_SEC")


def _seg_pt_dist(x0, y0, x1, y1, px, py):
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L2))
    return math.hypot(x0 + u * dx - px, y0 + u * dy - py)


def fanout(board, plane_nets=("GND", "VBAT", "+3V3"), via_d=0.6, drill=0.3, clr=0.25, trk=0.3):
    """Stub + via from every SMD pad of a plane net to its inner plane (only where that plane
    actually lies under the pad). Exposed pads get a via in their centre."""
    zones = {}
    for z in board.Zones():
        if z.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            zones.setdefault(z.GetNetname(), []).append(z)
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    boxes = [(p, _pad_box(p)) for p in pads if p.GetNumber() != "" or p.GetNetname() != ""]
    vias = []
    stubs = []
    done, skipped = 0, []
    for fp in board.GetFootprints():
        fc = fp.GetPosition()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net not in plane_nets or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            pos = pad.GetPosition()
            if not any(z.Outline().Contains(pcbnew.VECTOR2I(pos.x, pos.y)) for z in zones.get(net, [])):
                skipped.append(f"{fp.GetReference()}.{pad.GetNumber()}")
                continue
            px, py = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
            sx, sy = pcbnew.ToMM(pad.GetBoundingBox().GetWidth()), pcbnew.ToMM(pad.GetBoundingBox().GetHeight())
            cands = []
            if sx >= 1.6 and sy >= 1.6:                      # exposed / large pad: via inside it
                cands.append((px, py))
            dx, dy = px - pcbnew.ToMM(fc.x), py - pcbnew.ToMM(fc.y)
            n = math.hypot(dx, dy)
            dirs = []
            if n > 0.05:
                ux, uy = dx / n, dy / n
                dirs = [(ux, uy), (-uy, ux), (uy, -ux), (-ux, -uy)]
            dirs += [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)]
            for d in (0.6, 0.9, 1.2, 1.6, 2.0, 2.6):
                for ux, uy in dirs:
                    ext = abs(ux) * sx / 2 + abs(uy) * sy / 2
                    cands.append((px + ux * (ext + d), py + uy * (ext + d)))
            r = via_d / 2 + clr
            for (vx, vy) in cands:
                if vx < X0 + 1 or vy < Y0 + 1 or vx > X1 - 1 or vy > Y1 - 1:
                    continue
                vb = (vx - r, vy - r, vx + r, vy + r)
                bad = False
                for q, b in boxes:
                    same = q.GetNetname() == net
                    if q.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) and not (vb[2] < b[0] - 0.25 or vb[0] > b[2] + 0.25 or vb[3] < b[1] - 0.25 or vb[1] > b[3] + 0.25):
                        bad = True; break                    # keep clear of every drilled pad
                    if same:
                        continue
                    hv = q.GetNetname().endswith(HV_SUFFIX)
                    extra = 0.4 if hv else 0.0             # HV48 needs 0.6 mm
                    if not (vb[2] < b[0] - extra or vb[0] > b[2] + extra or vb[3] < b[1] - extra or vb[1] > b[3] + extra):
                        bad = True; break
                    w2 = min(trk, sx, sy) / 2 + (0.65 if hv else 0.16)   # half track + clearance
                    if _seg_hits_box(px, py, vx, vy, (b[0] - w2, b[1] - w2, b[2] + w2, b[3] + w2), steps=24):
                        bad = True; break
                wt = min(trk, sx, sy)
                if not bad:
                    for (a0, b0, a1, b1, nn, ww) in stubs:
                        if nn == net:
                            continue
                        if _seg_pt_dist(a0, b0, a1, b1, vx, vy) < via_d / 2 + ww / 2 + 0.2 or                                 _seg_pt_dist(px, py, vx, vy, a1, b1) < via_d / 2 + wt / 2 + 0.2 or                                 min(_seg_pt_dist(px, py, vx, vy, a0, b0), _seg_pt_dist(a0, b0, a1, b1, px, py)) < wt / 2 + ww / 2 + 0.2:
                            bad = True; break
                if bad or any(math.hypot(vx - a, vy - b_) < via_d + clr for a, b_, nn in vias if nn != net)                         or any(math.hypot(vx - a, vy - b_) < via_d + 0.15 for a, b_, nn in vias if nn == net):
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetPosition(V(vx, vy))
                v.SetWidth(MM(via_d))
                v.SetDrill(MM(drill))
                v.SetNet(pad.GetNet())
                board.Add(v)
                if (vx, vy) != (px, py):
                    tr = pcbnew.PCB_TRACK(board)
                    tr.SetStart(V(px, py))
                    tr.SetEnd(V(vx, vy))
                    tr.SetWidth(MM(min(trk, sx, sy)))
                    tr.SetLayer(pcbnew.F_Cu)
                    tr.SetNet(pad.GetNet())
                    board.Add(tr)
                vias.append((vx, vy, net))
                stubs.append((px, py, vx, vy, net, wt))
                done += 1
                break
            else:
                skipped.append(f"{fp.GetReference()}.{pad.GetNumber()}(no room)")
    log(f"fan-out: {done} pads connected to planes; {len(skipped)} left for the router")
    return skipped


def build():
    comps, nets = read_netlist()
    log("netlist read")
    board = pcbnew.NewBoard(BOARD)
    setup_board(board)
    fps = {}
    for c in comps:
        if not c["footprint"]:
            print("no footprint:", c["ref"])
            continue
        fp = load_fp(c["footprint"])
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        sheet_ts = c["sheet_ts"] if c["sheet_ts"] != "/" else "/"
        fp.SetPath(pcbnew.KIID_PATH(sheet_ts + c["ts"]))
        fp.SetSheetname(c["props"].get("Sheetname", ""))
        fp.SetSheetfile(c["props"].get("Sheetfile", ""))
        fp.SetDNP("dnp" in c["props"])
        fp.SetExcludedFromBOM("exclude_from_bom" in c["props"])
        for fname, fval in c["fields"]:
            if fname == "Footprint":
                continue
            f = fp.GetField(fname) if fp.HasField(fname) else None
            if f is None:
                f = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, fname)
                f.SetLayer(pcbnew.F_Fab)
                f.SetVisible(False)
                fp.Add(f)
            f.SetText(fval)
        board.Add(fp)
        fps[c["ref"]] = (fp, c)
    log("footprints loaded")
    # nets
    netinfo = {}
    for name, nodes in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
        for ref, pin in nodes:
            if ref not in fps:
                continue
            for pad in fps[ref][0].Pads():
                if pad.GetNumber() == pin:
                    pad.SetNet(ni)
    log("nets assigned")
    # placement
    occupied = []
    for ref, a in ANCHORS.items():
        fp = fps[ref][0]
        if ref in EDGE_FACING:
            face_edge(fp, EDGE_FACING[ref])
            bb = courtyard_bbox(fp)
            w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            if EDGE_FACING[ref] == "+x":
                x = X1 - w / 2 - 0.2   # body flush with right edge
            else:
                x = X0 + w / 2 + 0.2   # body flush with left edge
            rot = fp.GetOrientationDegrees()
            place_at(fp, x, a[1], rot)
        else:
            place_at(fp, a[0], a[1], a[2])
        occupied.append(occ_rect(fp))
    log("anchors placed")
    leftover = []
    for anchor, refs in NEAR.items():
        left = near_pack(fps[anchor][0], [fps[r][0] for r in refs], occupied)
        leftover += left
        log("near-packed " + anchor)
    placed = set(ANCHORS) | {r for v in NEAR.values() for r in v}
    by_sheet = {}
    for ref, (fp, c) in fps.items():
        if ref in placed:
            continue
        by_sheet.setdefault(c["sheet_name"], []).append(fp)
    for sheet, items in by_sheet.items():
        items.sort(key=lambda f: -size_mm(f)[0] * size_mm(f)[1])
        pack(items, REGIONS[sheet], occupied, REGIONS2.get(sheet))
    log("regions packed")
    for fp in leftover:
        print("could not ring-place:", fp.GetReference())
    # zones: L2 solid GND; L3 split VBAT / +3V3; outer layers GND pour
    gnd, vbat, v33 = netinfo["GND"], netinfo["VBAT"], netinfo["+3V3"]
    inset = 0.5
    full = rect(X0 + inset, Y0 + inset, X1 - inset, Y1 - inset)
    add_zone(board, gnd, pcbnew.In1_Cu, full, 0, 0.3, "GND_L2")
    add_zone(board, gnd, pcbnew.F_Cu, full, 0, 0.3, "GND_TOP")
    add_zone(board, gnd, pcbnew.B_Cu, full, 0, 0.3, "GND_BOT")
    # L3 split: VBAT under the battery strip (x < 116) and the 48 V block (x > 155, y > 140.5),
    # joined by a band along the bottom edge; +3V3 everywhere else (both MCUs, buck output, pull-ups).
    vb_poly = [(X0 + inset, Y0 + inset), (116.0, Y0 + inset), (116.0, 177.0), (155.0, 177.0), (155.0, 140.5),
               (X1 - inset, 140.5), (X1 - inset, Y1 - inset), (X0 + inset, Y1 - inset)]
    add_zone(board, vbat, pcbnew.In2_Cu, vb_poly, 2, 0.3, "VBAT_L3")
    add_zone(board, v33, pcbnew.In2_Cu, full, 1, 0.3, "3V3_L3")
    # silkscreen warnings
    add_text(board, "PIEZO INSULIN PUMP v2 REV B - HANDOVER PROTOTYPE, NOT FAB-APPROVED", 112.0, 182.0, pcbnew.B_SilkS, 1.0)
    add_text(board, "BENCH ONLY - WATER/SALINE - NEVER ON A PERSON OR ANIMAL", 112.0, 180.0, pcbnew.B_SilkS, 1.0)
    add_text(board, "48V ZONE", 192.0, 145.0, pcbnew.F_SilkS, 1.5)
    fill(board)
    left = fanout(board)
    with open(os.path.join(PROJECT_DIR, "..", "..", "validation", "logs", "fanout_unconnected.txt"), "w") as f:
        f.write("Plane-net SMD pads NOT fanned out to a plane (left for the router):\n" + "\n".join(left) + "\n")
    log("zones added; filling")
    fill(board)
    log("filled")
    pcbnew.SaveBoard(BOARD, board)
    print("board saved:", BOARD, len(fps), "footprints,", len(nets), "nets")


def fill(board):
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def export_dsn(out):
    """Outer-layer GND pours are left out of the DSN so the router can use F.Cu/B.Cu."""
    board = pcbnew.LoadBoard(BOARD)
    for z in list(board.Zones()):
        if z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            board.Remove(z)
    ok = pcbnew.ExportSpecctraDSN(board, out)
    # Inner layers carry only planes: declare them 'power' so the router treats the plane
    # polygons as planes that vias may pierce (as 'signal' they block every via).
    import re
    txt = open(out, encoding="utf8").read()
    for lyr in ("In1.Cu", "In2.Cu"):
        lines_ = txt.split(chr(10))
        for k_, l_ in enumerate(lines_[:-1]):
            if l_.strip() == "(layer " + lyr:
                lines_[k_ + 1] = lines_[k_ + 1].replace("(type signal)", "(type power)")
        txt = chr(10).join(lines_)
    open(out, "w", encoding="utf8").write(txt)
    print("DSN export:", ok, out)


def remove_dangling(board, rounds=1):
    """Delete vias and track segments with an unconnected end (autorouter leftovers)."""
    removed = 0
    for _ in range(rounds):
        board.BuildConnectivity()
        conn = board.GetConnectivity()
        dead = []
        for tr in board.GetTracks():
            if tr.Type() == pcbnew.PCB_VIA_T:
                if len(conn.GetConnectedItems(tr)) < 2 and not any(
                        z.GetNetCode() == tr.GetNetCode() and z.IsOnLayer(lyr) and z.HitTestFilledArea(lyr, tr.GetPosition())
                        for z in board.Zones() for lyr in (pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.F_Cu, pcbnew.B_Cu)):
                    dead.append(tr)
            elif conn.TestTrackEndpointDangling(tr, False):
                dead.append(tr)
        if not dead:
            break
        for d in dead:
            board.Remove(d)
        removed += len(dead)
    log(f"removed {removed} dangling vias/segments")


def import_ses(ses):
    board = pcbnew.LoadBoard(BOARD)
    ok = pcbnew.ImportSpecctraSES(board, ses)
    print("SES import:", ok)
    fill(board)
    try:
        remove_dangling(board)
    except Exception as e:          # cleanup is best-effort; never lose the imported routing
        log("dangling cleanup skipped: " + repr(e))
    pcbnew.SaveBoard(BOARD, board)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "place"
    if cmd == "place":
        build()
    elif cmd == "dsn":
        export_dsn(sys.argv[2])
    elif cmd == "ses":
        import_ses(sys.argv[2])
    elif cmd == "fill":
        b = pcbnew.LoadBoard(BOARD)
        fill(b)
        pcbnew.SaveBoard(BOARD, b)
