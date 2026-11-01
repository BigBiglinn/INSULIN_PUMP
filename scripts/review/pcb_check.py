"""Independent PCB checker (reviewer's own code). Reads the .kicad_pcb S-expression directly.
Checks: copper connectivity islands per net, different-net copper overlap (shorts), clearance by
net class, track widths per net, pad-net parity against scripts/design.py, board outline, placement."""
import sys, math, json, re, collections
import os; HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); sys.path.insert(0, HERE)
from sexp import parse, find
from shapely.geometry import Polygon, Point, LineString, box
from shapely import affinity
from shapely.ops import unary_union
from shapely.strtree import STRtree

PCB = os.path.join(ROOT, 'hardware/kicad/') + 'pump_v2.kicad_pcb'
PRO = os.path.join(ROOT, 'hardware/kicad/') + 'pump_v2.kicad_pro'
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
t = parse(open(PCB).read())

def kv(n, key):
    for c in n:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None

def short(net):
    return net.split('/')[-1] if net else ''

# ---------------- items
items = []  # dict(layer, geom, net, kind, ref)
pads = []
for fp in [c for c in t if isinstance(c, list) and c and c[0] == 'footprint']:
    at = kv(fp, 'at'); fx, fy = float(at[1]), float(at[2]); frot = float(at[3]) if len(at) > 3 else 0.0
    ref = [p[2] for p in fp if isinstance(p, list) and p[0] == 'property' and p[1] == 'Reference'][0]
    fplayer = kv(fp, 'layer')[1]
    attr = kv(fp, 'attr')
    dnp = bool(attr and 'dnp' in attr)
    for pd in [c for c in fp if isinstance(c, list) and c and c[0] == 'pad']:
        num, ptype, shape = pd[1], pd[2], pd[3]
        pat = kv(pd, 'at'); px, py = float(pat[1]), float(pat[2]); prot = float(pat[3]) if len(pat) > 3 else 0.0
        sz = kv(pd, 'size'); w, h = float(sz[1]), float(sz[2])
        lay = kv(pd, 'layers')[1:]
        netn = kv(pd, 'net'); net = netn[1] if netn else ''
        th = math.radians(frot)
        X = fx + px * math.cos(th) + py * math.sin(th)
        Y = fy - px * math.sin(th) + py * math.cos(th)
        if shape == 'circle':
            g = Point(X, Y).buffer(w / 2, 16)
        elif shape == 'oval':
            r = min(w, h) / 2
            L = LineString([(-(w / 2 - r), 0), (w / 2 - r, 0)]) if w >= h else LineString([(0, -(h / 2 - r)), (0, h / 2 - r)])
            g = L.buffer(r, 16) if L.length > 0 else Point(0, 0).buffer(r, 16)
            g = affinity.translate(affinity.rotate(g, -prot, origin=(0, 0)), X, Y)
        else:  # rect, roundrect, trapezoid, custom (approx by size box)
            rr = kv(pd, 'roundrect_rratio')
            g = box(-w / 2, -h / 2, w / 2, h / 2)
            if shape == 'roundrect' and rr:
                r = float(rr[1]) * min(w, h)
                g = box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, 8) if r > 0 else g
            g = affinity.translate(affinity.rotate(g, -prot, origin=(0, 0)), X, Y)
        cul = []
        for l in lay:
            if l == '*.Cu':
                cul = CU[:]
            elif l in CU:
                cul.append(l)
        if ptype == 'np_thru_hole':
            cul = [] if not netn else cul
        pads.append(dict(ref=ref, num=num, net=net, xy=(X, Y), layers=cul, dnp=dnp, fplayer=fplayer, type=ptype, w=w, h=h))
        for l in cul:
            items.append(dict(layer=l, geom=g, net=net, kind='pad', ref=f'{ref}.{num}', dnp=dnp))

tracks = []
for sg in [c for c in t if isinstance(c, list) and c and c[0] in ('segment', 'arc')]:
    s = kv(sg, 'start'); e = kv(sg, 'end'); w = float(kv(sg, 'width')[1]); l = kv(sg, 'layer')[1]; net = kv(sg, 'net')[1]
    pts = [(float(s[1]), float(s[2]))]
    if sg[0] == 'arc':
        m = kv(sg, 'mid'); pts.append((float(m[1]), float(m[2])))
    pts.append((float(e[1]), float(e[2])))
    g = LineString(pts).buffer(w / 2, 8)
    tracks.append(dict(net=net, layer=l, w=w, len=LineString(pts).length, pts=pts))
    items.append(dict(layer=l, geom=g, net=net, kind='track', ref=f'trk@{pts[0][0]:.2f},{pts[0][1]:.2f}', dnp=False))
vias = []
for v in [c for c in t if isinstance(c, list) and c and c[0] == 'via']:
    a = kv(v, 'at'); x, y = float(a[1]), float(a[2]); d = float(kv(v, 'size')[1]); net = kv(v, 'net')[1]
    vias.append(dict(xy=(x, y), net=net, d=d))
    for l in CU:
        items.append(dict(layer=l, geom=Point(x, y).buffer(d / 2, 12), net=net, kind='via', ref=f'via@{x:.2f},{y:.2f}', dnp=False))
zones = []
for z in [c for c in t if isinstance(c, list) and c and c[0] == 'zone']:
    net = kv(z, 'net')[1] if kv(z, 'net') else ''
    for fpoly in find(z, 'filled_polygon'):
        l = kv(fpoly, 'layer')[1]
        pts = [(float(p[1]), float(p[2])) for p in kv(fpoly, 'pts')[1:] if p[0] == 'xy']
        g = Polygon(pts).buffer(0)
        zones.append(dict(net=net, layer=l, area=g.area))
        items.append(dict(layer=l, geom=g, net=net, kind='zone', ref=f'zone:{short(net)}:{l}', dnp=False))

# ---------------- board outline
edge = []
for g in [c for c in t if isinstance(c, list) and c and c[0].startswith('gr_')]:
    if kv(g, 'layer') and kv(g, 'layer')[1] == 'Edge.Cuts':
        if g[0] == 'gr_rect':
            s, e = kv(g, 'start'), kv(g, 'end'); edge.append(('rect', float(s[1]), float(s[2]), float(e[1]), float(e[2])))
        else:
            edge.append((g[0],))
print('BOARD OUTLINE:', edge)

# ---------------- connectivity
parent = list(range(len(items)))
def fnd(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
def uni(a, b):
    ra, rb = fnd(a), fnd(b)
    if ra != rb: parent[ra] = rb
bylayer = collections.defaultdict(list)
for i, it in enumerate(items):
    bylayer[it['layer']].append(i)
shorts = []
for l, idx in bylayer.items():
    geoms = [items[i]['geom'] for i in idx]
    tree = STRtree(geoms)
    for k, i in enumerate(idx):
        for j in tree.query(geoms[k], predicate='intersects'):
            jj = idx[j]
            if jj <= i: continue
            a, b = items[i], items[jj]
            if a['net'] == b['net'] and a['net']:
                uni(i, jj)
            elif a['net'] != b['net']:
                inter = a['geom'].intersection(b['geom']).area
                if inter > 1e-4 and not (a['kind'] == 'zone' and b['kind'] == 'zone'):
                    shorts.append((l, a['ref'], short(a['net']), b['ref'], short(b['net']), round(inter, 4)))
# vias & TH pads join layers: same geometry on all layers -> union by ref key
key = collections.defaultdict(list)
for i, it in enumerate(items):
    if it['kind'] in ('via',) or (it['kind'] == 'pad'):
        key[(it['kind'], it['ref'], it['net'])].append(i)
for v in key.values():
    for i in v[1:]: uni(v[0], i)

islands = collections.defaultdict(lambda: collections.defaultdict(list))
for i, it in enumerate(items):
    if it['kind'] == 'pad' and it['net']:
        islands[it['net']][fnd(i)].append(it['ref'])
unrouted = {}
for net, isl in islands.items():
    groups = [sorted(set(v)) for v in isl.values()]
    if len(groups) > 1:
        unrouted[net] = groups
print('\n=== SHORTS (different-net copper overlap) :', len(shorts))
for s in shorts[:40]: print('  ', s)
print('\n=== NETS WITH MORE THAN ONE COPPER ISLAND (unrouted):', len(unrouted), 'nets,',
      sum(len(g) - 1 for g in unrouted.values()), 'missing connections')
for net, g in sorted(unrouted.items()):
    allp = [p for grp in g for p in grp]
    dnpflag = all(any(pp['dnp'] for pp in pads if f"{pp['ref']}.{pp['num']}" == r) for r in allp)
    print(f'  {short(net):16s} islands={len(g)}  ' + ' | '.join(','.join(x) for x in g)[:300])

# ---------------- net classes & clearance
pro = json.load(open(PRO))
cls = {c['name']: c for c in pro['net_settings']['classes']}
pats = pro['net_settings'].get('netclass_patterns', [])
def netclass(net):
    for p in pats:
        rx = '^' + re.escape(p['pattern']).replace('\\*', '.*') + '$'
        if re.match(rx, net): return p['netclass']
    return 'Default'
def clr(net):
    return cls[netclass(net)]['clearance']
print('\n=== CLEARANCE VIOLATIONS (net-class clearance, own geometry; DRU exceptions for J703/Q301 applied)')
viol = []
for l, idx in bylayer.items():
    geoms = [items[i]['geom'] for i in idx]
    tree = STRtree(geoms)
    for k, i in enumerate(idx):
        a = items[i]
        need_a = clr(a['net'])
        for j in tree.query(geoms[k].buffer(0.6)):
            jj = idx[j]
            if jj <= i: continue
            b = items[jj]
            if a['net'] == b['net'] or not a['net'] or not b['net']: continue
            need = max(need_a, clr(b['net']))
            ra, rb = a['ref'].split('.')[0], b['ref'].split('.')[0]
            if ra == rb == 'J703': need = 0.35
            if ra == rb == 'Q301': need = 0.127
            d = a['geom'].distance(b['geom'])
            if d < need - 1e-3:
                viol.append((round(d, 3), need, l, a['ref'], short(a['net']), b['ref'], short(b['net'])))
viol.sort()
print('  count:', len(viol))
for v in viol[:60]: print('  ', v)

# nets that by voltage should be HV but are not in HV48
print('\n=== NET CLASS ASSIGNMENT')
allnets = sorted(set(p['net'] for p in pads if p['net']))
for n in allnets:
    if any(k in n for k in ['48V', 'FLY_SEC', 'FLY_SNUB', 'SW48', 'FLY_SW', 'FLY_CLAMP', 'VBAT', 'FLY_CS', 'RF_', 'GND']):
        print(f'  {n:34s} -> {netclass(n)}')

# ---------------- track widths on power nets
print('\n=== TRACK WIDTH SUMMARY (min/max width, total length) for current-carrying nets')
tw = collections.defaultdict(list)
for tr in tracks: tw[tr['net']].append(tr)
for n in sorted(tw):
    if any(k in short(n) for k in ['VBAT', 'FLY_SW', 'FLY_CS', 'GND', '48V', 'FLY_SEC', 'BUCK_SW', '+3V3', 'FLY_CLAMP', 'FLY_GATE']):
        ws = [x['w'] for x in tw[n]]
        print(f'  {short(n):14s} n={len(ws):3d} min={min(ws):.2f} max={max(ws):.2f} len={sum(x["len"] for x in tw[n]):.1f}mm  narrow(<0.5mm) len={sum(x["len"] for x in tw[n] if x["w"]<0.5):.1f}mm')
print('\n=== ZONES')
for z in zones: print('  ', short(z['net']), z['layer'], round(z['area'], 1), 'mm2')

json.dump(dict(pads=[{k: v for k, v in p.items()} for p in pads]), open(os.devnull, 'w'))
