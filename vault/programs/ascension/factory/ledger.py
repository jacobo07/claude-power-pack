#!/usr/bin/env python3
"""Ascension per-function ledger, D43 step 1 (PP vault/specs/ascension-function-ledger.md). Observation only.
usage: ledger.py build | report [--json] | fn <fid|name> | selftest"""
import collections, glob, hashlib, json, os, re, sqlite3, struct, sys

F = "/home/kobii/agora/factory"
H = "/home/kobii/agora/ascension-autopilot"
DB = F + "/ledger/ledger.db"


def funcs(path):
    """ELF function symbols -> [(name, size, reloc-masked sha1[:16])]. Copied from factory/pareto/pareto.py funcs()
    (that module runs its census at import time, so it cannot be imported)."""
    b = open(path, "rb").read()
    if b[:4] != b"\x7fELF":
        return []
    shoff = struct.unpack(">I", b[32:36])[0]
    shentsize, shnum = struct.unpack(">HH", b[46:50])
    sh = [struct.unpack(">10I", b[shoff + i * shentsize:shoff + i * shentsize + 40]) for i in range(shnum)]
    symtab = next((s for s in sh if s[1] == 2), None)
    if not symtab:
        return []
    strs = sh[symtab[6]]
    sb = b[strs[4]:strs[4] + strs[5]]
    relo = collections.defaultdict(set)
    for s in sh:
        if s[1] == 4:
            for k in range(s[5] // 12):
                relo[s[7]].add(struct.unpack(">I", b[s[4] + k * 12:s[4] + k * 12 + 4])[0] & ~3)
    out = []
    for i in range(symtab[5] // 16):
        n, v, sz, info, _, shn = struct.unpack(">IIIBBH", b[symtab[4] + i * 16:symtab[4] + i * 16 + 16])
        if info & 0xF != 2 or not shn or shn >= len(sh) or sz == 0:
            continue
        sec = sh[shn]
        body = bytearray(b[sec[4] + v:sec[4] + v + sz])
        for off in relo.get(shn, ()):
            if v <= off < v + sz:
                o = off - v
                body[o] &= 0xFC
                body[o + 1:o + 4] = b"\0\0\0"
        out.append((sb[n:sb.index(b"\0", n)].decode("latin1"), sz, hashlib.sha1(bytes(body)).hexdigest()[:16]))
    return out

GAME2BIN = {"RMCP01": "RMCP01", "RZTP01": "RZTP01", "SUPP01": "SUPP01", "TENNIS": "TENNIS", "FIFA": "FIFA"}
LANE2BIN = {"MKW": "RMCP01", "MKWLIB": "RMCP01", "WSR": "RZTP01", "KSR": "RZTP01", "WIIPARTY": "SUPP01",
            "TENNIS": "TENNIS", "FIFA": "FIFA", "FIFATC": "FIFA"}
ORDER = ["CERT", "MATCH", "NEAR99", "NEAR95", "NEAR90", "COMPILES", "NO_COMPILE", "LIFT_FAIL", "TARGET_AMBIGUOUS",
         "NO_TARGET", "XF_ERROR", "UNATTEMPTED"]
RANK = {s: i for i, s in enumerate(ORDER)}
FN_ADDR = re.compile(r"^fn_([0-9A-Fa-f]{8})$")


def band(p):
    return "MATCH" if p == 100 else "NEAR99" if p >= 99 else "NEAR95" if p >= 95 else "NEAR90" if p >= 90 else "COMPILES"


def runs():
    out, unmapped = [], []
    for sw in sorted(glob.glob(F + "/*/sweep.jsonl") + glob.glob(F + "/*/*/sweep.jsonl")):
        d = os.path.dirname(sw)
        if "/perfn/" in d or d.endswith("-perfn"):
            continue  # views (symlinks) of another run: counting them twice would double every attempt
        try:
            s = json.load(open(d + "/summary.json"))
        except (OSError, ValueError):
            unmapped.append((d, "no summary.json")); continue
        b = GAME2BIN.get(s.get("game"))
        if not b:
            unmapped.append((d, f"game {s.get('game')!r}")); continue
        prod = "factory_vs2" if "/typegen/" in d and "vs2" in os.path.basename(d) else \
               "factory_vs" if "/typegen/" in d else "factory"
        out.append({"dir": d, "run": os.path.relpath(d, F), "binary": b, "module": s.get("module") or "main",
                    "producer": prod, "compiler": s.get("compiler")})
    return out, unmapped


def build():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    tmp = DB + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    c = sqlite3.connect(tmp)
    c.executescript("""
    CREATE TABLE function(fid TEXT PRIMARY KEY, binary TEXT, module TEXT, addr TEXT, name TEXT, size INT, masked TEXT);
    CREATE TABLE attempt(fid TEXT, run TEXT, producer TEXT, arm TEXT, compiler TEXT, state TEXT, compiles INT, pct REAL,
                         target_obj TEXT, target_sha256 TEXT, target_ok INT, padded INT);
    CREATE TABLE lift(fid TEXT, run TEXT, m2c_state TEXT);
    CREATE TABLE cert(fid TEXT, lane TEXT, source TEXT, padded INT);
    CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);""")
    rs, unmapped = runs()
    objcache = {}

    def obj(p):
        if p not in objcache:
            try:
                sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
                objcache[p] = (sha, {n: (sz, h) for n, sz, h in funcs(p)})
            except OSError:
                objcache[p] = (None, {})
        return objcache[p]

    fns, names = {}, collections.defaultdict(dict)
    for r in rs:
        for row in map(json.loads, open(r["dir"] + "/corpus.jsonl")):
            fid = f"{r['binary']}:{row['id']}"
            if fid not in fns:
                fns[fid] = [r["binary"], row["module"], row["start"].upper().zfill(8), row["name"], row["size"], None]
            names[r["binary"]].setdefault(row["name"], set()).add(fid)
        mres = os.path.join(r["dir"], "m2c", "results.tsv")
        if os.path.exists(mres):
            c.executemany("INSERT INTO lift VALUES(?,?,?)", [(f"{r['binary']}:{l.split()[0]}", r["run"], l.split()[1])
                                                            for l in open(mres) if l.strip()])
        rows = []
        for x in map(json.loads, open(r["dir"] + "/sweep.jsonl")):
            fid = f"{r['binary']}:{x['id']}"
            st = x.get("state")
            if st != "OK":
                rows.append((fid, r["run"], r["producer"], None, r["compiler"], (st or "?").split(":")[0], 0, None,
                             None, None, None, None))
                continue
            sha, syms = obj(x["obj"])
            ok = 1 if x["sym"] in syms else 0
            if ok and fns.get(fid) and fns[fid][5] is None:
                fns[fid][5] = syms[x["sym"]][1]
            for arm, a in x["arms"].items():
                if not a.get("compiles"):
                    s, p = "NO_COMPILE", None
                else:
                    p = a.get("pct") or 0.0
                    s = band(p) if ok else "COMPILES"
                rows.append((fid, r["run"], r["producer"], arm, r["compiler"], s, int(bool(a.get("compiles"))), p,
                             x["obj"], sha, ok, None))
        c.executemany("INSERT INTO attempt VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    c.executemany("INSERT INTO function VALUES(?,?,?,?,?,?,?)", [(k, *v) for k, v in fns.items()])
    unc = collections.Counter()
    by_addr = collections.defaultdict(set)
    for k, v in fns.items():
        by_addr[(v[0], v[2])].add(k)
    for snap in sorted(glob.glob(H + "/match/*.json")):
        lane = os.path.basename(snap)[:-5]
        b = LANE2BIN.get(lane)
        if not b:
            unc[f"{lane}:unknown lane"] += 1; continue
        rows = []
        for e in json.load(open(snap)):
            fn = e.split("::", 1)[-1]
            hit = names[b].get(fn, set())
            if not hit:
                m = FN_ADDR.match(fn)
                hit = by_addr.get((b, m.group(1).upper()), set()) if m else set()
            if len(hit) != 1:
                unc[f"{lane}:{'ambiguous' if hit else 'unmapped'}"] += 1; continue
            rows.append((next(iter(hit)), lane, "match_snapshot", None))
        c.executemany("INSERT INTO cert VALUES(?,?,?,?)", rows)
    c.executemany("INSERT INTO meta VALUES(?,?)", [("unmapped_runs", json.dumps(unmapped)), ("cert_unmapped", json.dumps(unc)),
                                                    ("runs", json.dumps([r["run"] for r in rs]))])
    c.commit(); c.close()
    os.replace(tmp, DB)
    print(json.dumps({"runs": len(rs), "unmapped_runs": unmapped, "functions": len(fns), "objects_hashed": len(objcache),
                      "cert_unmapped": unc}))


def states(c):
    best = {}
    for fid, s in c.execute("SELECT fid, state FROM attempt"):
        if fid not in best or RANK.get(s, 99) < RANK[best[fid]]:
            best[fid] = s if s in RANK else "XF_ERROR"
    for (fid,) in c.execute("SELECT fid FROM lift WHERE m2c_state != 'L1'"):
        if fid not in best:
            best[fid] = "LIFT_FAIL"
    for (fid,) in c.execute("SELECT fid FROM cert"):
        best[fid] = "CERT"
    return best


def report(as_json=False):
    c = sqlite3.connect(DB)
    best = states(c)
    out = {}
    for b, n, nb in c.execute("SELECT binary, count(*), sum(size) FROM function GROUP BY binary"):
        st, by = collections.Counter(), collections.Counter()
        for fid, size in c.execute("SELECT fid, size FROM function WHERE binary=?", (b,)):
            s = best.get(fid, "UNATTEMPTED"); st[s] += 1; by[s] += size
        tried = dict(c.execute("SELECT producer || '/' || coalesce(arm,'-'), count(DISTINCT fid) FROM attempt a "
                               "JOIN function f USING(fid) WHERE f.binary=? GROUP BY 1", (b,)).fetchall())
        drift = c.execute("SELECT count(DISTINCT fid) FROM attempt JOIN function USING(fid) WHERE binary=? AND target_ok=0",
                          (b,)).fetchone()[0]
        out[b] = {"functions": n, "bytes": nb, "states": {k: st[k] for k in ORDER if st[k]},
                  "bytes_pct": {k: round(100 * by[k] / nb, 1) for k in ORDER if by[k]},
                  "remaining_bytes": nb - by["CERT"], "target_drift_fns": drift, "tried": tried}
    meta = dict(c.execute("SELECT k, v FROM meta"))
    out["_meta"] = {k: json.loads(v) for k, v in meta.items() if k != "runs"}
    if as_json:
        print(json.dumps(out, indent=1, sort_keys=True)); return
    for b, d in out.items():
        if b == "_meta":
            continue
        print(f"{b}: {d['functions']} fns, {d['bytes']} B, remaining {d['remaining_bytes']} B, target drift {d['target_drift_fns']}")
        print("   states:", d["states"]); print("   bytes%:", d["bytes_pct"])
    print("meta:", out["_meta"])


def fn(key):
    c = sqlite3.connect(DB)
    fids = [r[0] for r in c.execute("SELECT fid FROM function WHERE fid=? OR name=?", (key, key))]
    for f in fids:
        print(c.execute("SELECT * FROM function WHERE fid=?", (f,)).fetchone())
        for r in c.execute("SELECT run, producer, arm, state, pct, target_ok FROM attempt WHERE fid=? ORDER BY run", (f,)):
            print("  ", r)
        print("   lift:", c.execute("SELECT run, m2c_state FROM lift WHERE fid=?", (f,)).fetchall())
        print("   cert:", c.execute("SELECT lane, source FROM cert WHERE fid=?", (f,)).fetchall())


def selftest():
    """AC (d): an attempt whose target lacks the symbol cannot raise the state above COMPILES (both poles)."""
    c = sqlite3.connect(":memory:")
    c.executescript("CREATE TABLE attempt(fid, run, producer, arm, compiler, state, compiles, pct, target_obj, target_sha256,"
                    " target_ok, padded); CREATE TABLE lift(fid, run, m2c_state); CREATE TABLE cert(fid, lane, source, padded);")
    ok = True
    for tok, want in ((1, "MATCH"), (0, "COMPILES")):
        c.execute("DELETE FROM attempt")
        s = band(100.0) if tok else "COMPILES"
        c.execute("INSERT INTO attempt VALUES('B:main:1','r','p','dol','m',?,1,100.0,'o','h',?,NULL)", (s, tok))
        got = states(c)["B:main:1"]
        print(("PASS" if got == want else "FAIL"), f"target_ok={tok} -> {got}")
        ok &= got == want
    sys.exit(0 if ok else 1)


def progress():
    """Append one sample per lane (certified fns/bytes from the MATCH snapshots, provisional matches, permuter-stage
    counters) to ledger/progress.jsonl and print the rate since the previous sample: the speed instrument."""
    c = sqlite3.connect(DB)
    size = dict(c.execute("SELECT fid, size FROM function"))
    sample = {"ts": __import__("time").time(), "lanes": {}}
    for lane, b in LANE2BIN.items():
        fids = [r[0] for r in c.execute("SELECT fid FROM cert WHERE lane=?", (lane,))]
        if not fids and not os.path.exists(f"{H}/match/{lane}.json"):
            continue
        tot, totb = c.execute("SELECT count(*), sum(size) FROM function WHERE binary=?", (b,)).fetchone()
        sample["lanes"][lane] = {"cert": len(fids), "cert_bytes": sum(size.get(f, 0) for f in fids), "fns": tot, "bytes": totb}
    tp = F + "/stages/perm_tried.jsonl"
    if os.path.exists(tp):
        rs = [json.loads(l) for l in open(tp)]
        sample["perm"] = {"tried": len(rs), "match": sum(r.get("res") == "MATCH" for r in rs),
                          "improved": sum(r.get("res") == "IMPROVED" for r in rs)}
    pp = F + "/ledger/progress.jsonl"
    prev = None
    if os.path.exists(pp):
        lines = open(pp).read().splitlines()
        prev = json.loads(lines[-1]) if lines else None
    with open(pp, "a") as w:
        w.write(json.dumps(sample) + "\n")
    hrs = (sample["ts"] - prev["ts"]) / 3600 if prev else None
    for lane, d in sample["lanes"].items():
        p = (prev or {}).get("lanes", {}).get(lane, {})
        rate = f", +{d['cert'] - p.get('cert', 0)} in {hrs:.2f} h" if hrs else ""
        print(f"{lane}: {d['cert']}/{d['fns']} fns ({100 * d['cert'] / d['fns']:.1f}%), "
              f"{100 * d['cert_bytes'] / d['bytes']:.2f}% bytes{rate}")
    print("perm:", sample.get("perm"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"build": build, "report": lambda: report("--json" in sys.argv), "fn": lambda: fn(sys.argv[2]),
     "selftest": selftest, "progress": progress}[cmd]()
