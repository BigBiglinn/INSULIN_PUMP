"""Reviewer's schematic netlist extraction: pin endpoints -> wire stubs -> labels, compared with scripts/design.py.
Also lists pins that are neither connected nor carry a no-connect flag."""
import sys, os, glob, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from sexp import parse, find
import design

def kv(n, k):
    for c in n:
        if isinstance(c, list) and c and c[0] == k:
            return c

root, sheets = design.build()
want = {(p.ref, pin): net for s in [root] + sheets for p in s.parts for pin, net in p.nets.items()}
got = {}; ncflags = collections.Counter()
for f in glob.glob(os.path.join(ROOT, 'hardware/kicad/*.kicad_sch')):
    t = parse(open(f).read())
    libs = {}
    ls = kv(t, 'lib_symbols')
    for sym in (ls[1:] if ls else []):
        pins = {}
        for p in find(sym, 'pin'):
            if len(p) > 2 and isinstance(p[1], str):
                at, num = kv(p, 'at'), kv(p, 'number')
                if at and num: pins[num[1]] = (float(at[1]), float(at[2]))
        libs[sym[1]] = pins
    pts = {}
    for w in [c for c in t if isinstance(c, list) and c and c[0] == 'wire']:
        xy = [(round(float(q[1]), 3), round(float(q[2]), 3)) for q in kv(w, 'pts')[1:]]
        pts.setdefault(xy[0], []).append(xy[1]); pts.setdefault(xy[1], []).append(xy[0])
    labels = {}
    for l in [c for c in t if isinstance(c, list) and c and c[0] in ('label', 'global_label', 'hierarchical_label')]:
        at = kv(l, 'at'); labels[(round(float(at[1]), 3), round(float(at[2]), 3))] = l[1]
    ncs = {(round(float(kv(n, 'at')[1]), 3), round(float(kv(n, 'at')[2]), 3)) for n in t if isinstance(n, list) and n and n[0] == 'no_connect'}
    for s in [c for c in t if isinstance(c, list) and c and c[0] == 'symbol' and kv(c, 'lib_id')]:
        lib = kv(s, 'lib_id')[1]; at = kv(s, 'at'); sx, sy = float(at[1]), float(at[2]); rot = float(at[3]) if len(at) > 3 else 0
        mir = kv(s, 'mirror')
        inst = find(s, 'reference')
        ref = inst[0][1] if inst else [p[2] for p in s if isinstance(p, list) and p[0] == 'property' and p[1] == 'Reference'][0]
        for num, (px, py) in libs.get(lib, {}).items():
            if mir and mir[1] == 'x': py = -py
            if mir and mir[1] == 'y': px = -px
            a = math.radians(rot); rx = px * math.cos(a) - py * math.sin(a); ry = px * math.sin(a) + py * math.cos(a)
            P = (round(sx + rx, 3), round(sy - ry, 3))
            if P in ncs: ncflags[ref] += 1; got[(ref, num)] = '<NC>'; continue
            if P in labels: got[(ref, num)] = labels[P]; continue
            ends = pts.get(P)
            if not ends: got[(ref, num)] = None; continue
            nets = {labels.get(e) for e in ends}
            got[(ref, num)] = nets.pop() if len(nets) == 1 else str(nets)
bad = [(k, n, got.get(k)) for k, n in want.items() if got.get(k) != n and not k[0].startswith('#')]
dangling = [k for k, v in got.items() if v is None and not k[0].startswith('#')]
print('pins compared:', len(want), ' mismatches vs design.py:', len(bad))
for b in bad: print('  ', b)
print('pins with neither a connection nor a no-connect flag:', len(dangling), dangling)
print('no-connect flags per part:', dict(ncflags))
