#!/usr/bin/env python3
"""F6 twin transfer (vault/specs/ascension-reconstruction-factory.md, Owner "y" 2026-11-21, pane 3581ade8).

An unmatched function f of lane L whose reloc-masked body equals a function d MATCHED in another lane D (pareto
shared_bodies.json) takes d's one-function source unit, with every symbol d's code references renamed to the symbol f
references at the same relocation site. It counts only at objdiff 100% against L's OWN target object.

Rename logic adapted from Ketbome/decomp-skills `dk.py cmd_twins` (MIT, (c) Ketbome): an ordered symbol signature,
a zip rename map refused when one donor symbol would map two ways, and simultaneous renaming. Ported from MIPS/splat
(jal, %hi/%lo) to PowerPC dtk objects: relocation sites read with objdump -r, paired by offset inside the function,
and required to agree in offset, type and addend.

`measure` (the pilot) compiles each candidate in a private empty cwd and writes only <out>/twin_<L>.jsonl plus a
summary; it never touches a lane repo. Carving and the lane gate are F5's steps, run later on a scratch clone.

usage: twin.py measure --lane WSR [--limit N] [--out DIR]
"""
import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile, time

T1 = "/home/kobii/missions/t1-campaign"
sys.path.insert(0, T1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.recon_fabric import cv1  # noqa: E402
import factory as F  # noqa: E402

FACTORY = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(FACTORY, "pareto", "shared_bodies.json")
OBJDUMP = "/usr/bin/powerpc-linux-gnu-objdump"
COMPILERS = "/home/kobii/wsr-decomp/build/compilers"  # holds every Wii/GC mwcceppc version the lanes use
LANES = {  # repo, game, the lane's own compiler (lanes_factory.json)
    "WSR": ("/home/kobii/wsr-decomp", "RZTP01", "Wii/1.0"),
    "MKW": ("/home/kobii/missions/mkw-decomp", "RMCP01", "Wii/0x4201_127"),
    "WIIPARTY": ("/home/kobii/missions/wiiparty-decomp", "SUPP01", "Wii/1.1"),
}
VAL_RE = re.compile(r"^(?P<base>.+?)(?P<add>[+-]0x[0-9a-fA-F]+)?$")
SYM_RE = re.compile(r"^(?P<val>[0-9a-fA-F]{8})\s(?P<flags>.{7})\s(?P<sec>\S+)\s+(?P<size>[0-9a-fA-F]{8})\s+"
                    r"(?:\.(?:hidden|protected|internal)\s+)?(?P<name>\S+)$")


def matched(repo, game):
    r = json.load(open(os.path.join(repo, "build", game, "report.json")))
    return {f.get("name") for u in r["units"] for f in u.get("functions") or [] if f.get("fuzzy_match_percent") == 100}


def donor_units(repo):
    """{symbol: (path, cflags list, mw_version or None)} for every one-function factory unit in configure.py."""
    cfg = open(os.path.join(repo, "configure.py"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'Object\(\s*\w+\s*,\s*"(factory[\w-]*/([^"/]+)\.c)"\s*,\s*cflags=\[(.*?)\]\s*(?:,\s*mw_version="([^"]+)")?', cfg):
        path = os.path.join(repo, "src", m.group(1))
        if os.path.exists(path):
            lib_ver = None
            head = cfg[:m.start()]
            j = head.rfind('"mw_version":')
            if j >= 0:
                lv = re.match(r'"mw_version":\s*"([^"]+)"', head[j:])
                lib_ver = lv.group(1) if lv else None
            out[m.group(2)] = (path, re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(3)), m.group(4) or lib_ver)
    return out


_SYMS, _RELS = {}, {}


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=120).stdout


def symtab(obj):
    if obj not in _SYMS:
        t = {}
        for ln in _run([OBJDUMP, "-t", obj]).splitlines():
            # "VALUE FLAGS(7) SECTION\tSIZE [.hidden|.protected|.internal] NAME"
            m = SYM_RE.match(ln)
            if m and "F" in m.group("flags"):
                t[m.group("name")] = (m.group("sec"), int(m.group("val"), 16), int(m.group("size"), 16))
        _SYMS[obj] = t
    return _SYMS[obj]


def relocs(obj, sym):
    """[(offset in function, type, base symbol, addend)] or None when sym is not a function of obj."""
    s = symtab(obj).get(sym)
    if not s:
        return None
    sec, val, size = s
    key = (obj, sec)
    if key not in _RELS:
        rows = []
        for ln in _run([OBJDUMP, "-r", "-j", sec, obj]).splitlines():
            p = ln.split()
            if len(p) == 3 and re.fullmatch(r"[0-9a-fA-F]{8}", p[0]):
                m = VAL_RE.match(p[2])
                rows.append((int(p[0], 16), p[1], m.group("base"), int(m.group("add") or "0", 16)))
        _RELS[key] = rows
    return [(o - val, t, b, a) for o, t, b, a in _RELS[key] if val <= o < val + size]


def rename_map(rd, rf, d, f):
    """D-symbol -> L-symbol from relocation pairs, or a refusal state."""
    if len(rd) != len(rf):
        return None, "RELOC_COUNT_DIFF"
    mp = {d: f}
    for (od, td, bd, ad), (of, tf, bf, af) in zip(rd, rf):
        if (od, td, ad) != (of, tf, af):
            return None, "RELOC_SHAPE_DIFF"
        if bd.startswith(".") or bf.startswith("."):  # section-relative: nothing to rename, must agree as is
            if bd != bf:
                return None, "RELOC_SECTION_DIFF"
            continue
        if mp.setdefault(bd, bf) != bf:
            return None, "RENAME_UNRESOLVED"
    return {a: b for a, b in mp.items() if a != b}, None


def apply_rename(src, mp):
    if not mp:
        return src
    pat = re.compile(r"(?<![\w$@.])(" + "|".join(re.escape(a) for a in sorted(mp, key=len, reverse=True)) + r")(?![\w$@])")
    return pat.sub(lambda m: mp[m.group(1)], src)


def compile_match(tc, mw, src, flags, sym, target):
    work = tempfile.mkdtemp(prefix="twin-")
    try:
        open(os.path.join(work, "fn.c"), "w", encoding="utf-8", newline="\n").write(src)
        try:
            rc = subprocess.run([tc["wibo"], mw] + flags + ["-c", "fn.c", "-o", "fn.o"], cwd=work,
                                capture_output=True, timeout=90).returncode
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        o = os.path.join(work, "fn.o")
        if rc != 0 or not os.path.exists(o) or sym not in cv1.elf_funcs(o):
            return "NO_COMPILE"
        pct = cv1.objdiff_pct(tc, target, o, sym, work)
        return "MATCH" if pct == 100.0 else "NO_MATCH"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def flag_tokens(items):
    out = []
    for it in items:
        out += it.split()
    return out


def measure(a):
    t0 = time.time()
    repo, game, own_ver = LANES[a.lane]
    idx = json.load(open(IDX))
    M = {k: matched(v[0], v[1]) for k, v in LANES.items()}
    units = {k: donor_units(v[0]) for k, v in LANES.items() if k != a.lane}
    tix = {k: F.target_index(v[0], v[1]) for k, v in LANES.items()}
    tc = dict(cv1.toolchain())
    out, seen = [], set()
    for v in idx.values():
        mine = [n for g, n, _ in v if g == a.lane and n not in M[a.lane]]
        donors = [(g, n) for g, n, _ in v if g != a.lane and g in units and n in M[g] and n in units[g]]
        for f in mine:
            if f in seen or not donors:
                continue
            seen.add(f)
            row = {"fn": f, "lane": a.lane}
            # a name dtk placed in several objects (TARGET_AMBIGUOUS): try each object that really holds it as a
            # function; only objdiff 100% against one of them counts (port_ksr does the same)
            fts = [t for t in tix[a.lane].get(f) or [] if relocs(t, f) is not None]
            st = None if fts else "NO_TARGET"
            for g, d in donors if fts else []:
                dts = [t for t in tix[g].get(d) or [] if relocs(t, d) is not None]
                if not dts:
                    st = st or "DONOR_NO_TARGET"
                    continue
                path, cflags, dver = units[g][d]
                raw = open(path, encoding="utf-8", errors="replace").read()
                for dt in dts:
                    for ft in fts:
                        mp, why = rename_map(relocs(dt, d), relocs(ft, f), d, f)
                        if why:
                            if st not in ("NO_COMPILE", "NO_MATCH", "TIMEOUT"):  # a compile outcome outranks it
                                st = why
                            continue
                        src = apply_rename(raw, mp)
                        for ver in dict.fromkeys([dver, own_ver]):
                            if not ver:
                                continue
                            st = compile_match(tc, os.path.join(COMPILERS, ver, "mwcceppc.exe"), src,
                                               flag_tokens(cflags), f, ft)
                            if st == "MATCH":
                                row.update(donor_game=g, donor=d, mw_version=ver, cflags=cflags, renames=len(mp),
                                           target=ft, n_targets=len(fts))
                                break
                        if st == "MATCH":
                            break
                    if st == "MATCH":
                        break
                if st == "MATCH":
                    break
            row["state"] = st
            out.append(row)
            if a.limit and len(out) >= a.limit:
                break
        if a.limit and len(out) >= a.limit:
            break
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, f"twin_{a.lane}.jsonl"), "w", newline="\n") as w:
        for r in out:
            w.write(json.dumps(r) + "\n")
    summary = {"lane": a.lane, "candidates": len(out), "states": dict(collections.Counter(r["state"] for r in out)),
               "wall_s": round(time.time() - t0, 1)}
    json.dump(summary, open(os.path.join(a.out, f"twin_{a.lane}.summary.json"), "w"), indent=1)
    print(json.dumps(summary))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("measure")
    m.add_argument("--lane", required=True, choices=sorted(LANES))
    m.add_argument("--limit", type=int, default=0)
    m.add_argument("--out", default=os.path.join(FACTORY, "twin"))
    a = ap.parse_args()
    measure(a)


if __name__ == "__main__":
    main()
