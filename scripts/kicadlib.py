"""Minimal KiCad S-expression helpers used by the Piezo Insulin Pump v2 generators.

Reads symbols from the installed KiCad 10 libraries (or the project library),
flattens derived ("extends") symbols, and reports pin connection points so the
schematic generator can attach labels exactly at pin ends.
"""
import os
import re

KICAD_SHARE = r"C:\Program Files\KiCad\10.0\share\kicad"
SYM_DIR = os.path.join(KICAD_SHARE, "symbols")
FP_DIR = os.path.join(KICAD_SHARE, "footprints")
PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "hardware", "kicad"))


# ---------------------------------------------------------------- s-expr parse
def tokenize(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "(" or c == ")":
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j:j + 2])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            yield ('"' + "".join(buf) + '"')
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            yield text[i:j]
            i = j


def parse(text):
    stack = [[]]
    for tok in tokenize(text):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok)
    return stack[0]


def unq(s):
    return s[1:-1] if isinstance(s, str) and s.startswith('"') else s


def dump(node, indent=0):
    """Serialise a parsed node back to KiCad-style text."""
    if not isinstance(node, list):
        return node
    pad = "\t" * indent
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return pad + "(" + " ".join(node) + ")"
    out = pad + "(" + " ".join(x for x in node if not isinstance(x, list))
    parts = [out]
    for x in node:
        if isinstance(x, list):
            parts.append(dump(x, indent + 1))
    return "\n".join(parts) + "\n" + pad + ")"


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None


# ---------------------------------------------------------------- libraries
_lib_cache = {}


def lib_path(lib):
    p = os.path.join(SYM_DIR, lib + ".kicad_sym")
    if os.path.exists(p):
        return p
    p = os.path.join(PROJECT_DIR, lib + ".kicad_sym")
    if os.path.exists(p):
        return p
    raise FileNotFoundError(lib)


def load_lib(lib):
    if lib not in _lib_cache:
        with open(lib_path(lib), encoding="utf8") as f:
            tree = parse(f.read())[0]
        syms = {unq(s[1]): s for s in find(tree, "symbol")}
        _lib_cache[lib] = syms
    return _lib_cache[lib]


def _rename_units(node, old, new):
    for x in node:
        if isinstance(x, list) and x and x[0] == "symbol":
            nm = unq(x[1])
            if nm.startswith(old + "_"):
                x[1] = '"' + new + nm[len(old):] + '"'


def get_symbol(lib_id):
    """Return a deep-copied, flattened symbol node named 'lib:name'."""
    import copy
    lib, name = lib_id.split(":", 1)
    syms = load_lib(lib)
    sym = copy.deepcopy(syms[name])
    ext = find1(sym, "extends")
    if ext is not None:
        parent = copy.deepcopy(get_symbol(lib + ":" + unq(ext[1])))
        pname = unq(ext[1])
        # child properties override parent properties
        child_props = {unq(p[1]): p for p in find(sym, "property")}
        newnode = []
        for x in parent:
            if isinstance(x, list) and x and x[0] == "property" and unq(x[1]) in child_props:
                newnode.append(child_props.pop(unq(x[1])))
            else:
                newnode.append(x)
        # insert remaining child-only properties after the last property
        idx = max(i for i, x in enumerate(newnode) if isinstance(x, list) and x and x[0] == "property")
        for p in child_props.values():
            idx += 1
            newnode.insert(idx, p)
        _rename_units(newnode, pname.split(":")[-1], name)
        sym = newnode
    sym[1] = '"' + lib_id + '"'
    return sym


def symbol_pins(lib_id):
    """List of dicts: number, name, type, x, y (lib coords, Y up), angle, length, unit."""
    sym = get_symbol(lib_id)
    short = lib_id.split(":", 1)[1]
    pins = []
    for unit in find(sym, "symbol"):
        uname = unq(unit[1])
        m = re.match(re.escape(short) + r"_(\d+)_(\d+)$", uname)
        unit_no = int(m.group(1)) if m else 0
        for p in find(unit, "pin"):
            at = find1(p, "at")
            pins.append({
                "type": p[1],
                "name": unq(find1(p, "name")[1]),
                "number": unq(find1(p, "number")[1]),
                "x": float(at[1]), "y": float(at[2]),
                "angle": int(float(at[3])) if len(at) > 3 else 0,
                "length": float(find1(p, "length")[1]),
                "unit": unit_no,
                "hidden": "hide" in p,
            })
    return pins


def symbol_property(lib_id, prop):
    sym = get_symbol(lib_id)
    for p in find(sym, "property"):
        if unq(p[1]) == prop:
            return unq(p[2])
    return None


if __name__ == "__main__":
    import sys
    for lid in sys.argv[1:]:
        print("==", lid, "FP:", symbol_property(lid, "Footprint"))
        for p in symbol_pins(lid):
            print("   ", p["number"], p["name"], p["type"], p["x"], p["y"], p["angle"], "unit", p["unit"])
