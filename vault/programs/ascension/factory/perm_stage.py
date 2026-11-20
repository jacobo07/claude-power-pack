#!/usr/bin/env python3
"""Permuter stage of the factory lane (Owner 2026-11-20 "go ahead, iterate ... maximise", pane 5a77ca0e).
Each tick: from the ledger, take the K best untried near misses (NEAR99/NEAR95, target_ok=1, binary in a configured
lane), run decomp-permuter on each with every compile in its own empty working dir (wibo's cost scales with the cwd's
entries), verify the best output with OUR compile + objdiff, and append verified 100% matches to
stages/perm-<BIN>-<module>/ (corpus/sweep/m2c/matched.tsv/summary), which the factory lane carves and gates like any
run. Every try is recorded in stages/perm_tried.jsonl so nothing is permuted twice. 0 tokens.
usage: perm_stage.py tick [--k 16] [--jobs 4] [--wall 300] | init"""
import argparse, concurrent.futures as cf, glob, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
F = "/home/kobii/agora/factory"
sys.path.insert(0, "/home/kobii/missions/t1-campaign"); sys.path.insert(0, F); sys.path.insert(0, F + "/typegen")
from modules.recon_fabric import cv1  # noqa: E402
import factory as B, factory_vs2 as V  # noqa: E402
PROD = {"factory": B, "factory_vs2": V}
ST = F + "/stages"; TRIED = ST + "/perm_tried.jsonl"; WORK = ST + "/permwork"; PW = ST + "/pw"
PERM = "/home/kobii/tools/decomp-permuter"; PY = "/home/kobii/tools/permuter-venv/bin/python"
OD = "powerpc-linux-gnu-objdump -dr -EB -mpowerpc -M broadway"
READY = os.path.expanduser("~/.claude/state/factory-lane.ready")
TC = cv1.toolchain()


def lane_binaries():
    out = {}
    for ln in json.load(open(F + "/lanes_factory.json")):
        out.setdefault(ln["binary"], ln["game"])
    return out


def stage_dir(b, module):
    return f"{ST}/perm-{b}-{module}"


def init_stage(b, game, module, compiler):
    d = stage_dir(b, module)
    os.makedirs(d + "/m2c/c", exist_ok=True)
    for n in ("corpus.jsonl", "sweep.jsonl", "matched.tsv"):
        open(os.path.join(d, n), "a").close()
    sp = d + "/summary.json"
    if not os.path.exists(sp):
        json.dump({"game": game, "module": module, "compiler": compiler, "producer": "factory_perm",
                   "note": "permuter stage; rows are verified objdiff 100.0 only"}, open(sp, "w"))
    return d


def verify(src_c, obj, sym, flags, mw):
    w = tempfile.mkdtemp(prefix="pv-", dir=PW)
    try:
        shutil.copy(src_c, w + "/fn.c")
        r = subprocess.run([TC["wibo"], mw] + flags.split() + ["-c", "fn.c", "-o", "fn.o"], cwd=w, capture_output=True, timeout=90)
        if r.returncode != 0:
            return None
        return cv1.objdiff_pct(dict(TC, mw=mw), obj, w + "/fn.o", sym, w)
    finally:
        shutil.rmtree(w, ignore_errors=True)


def one(c, wall):
    fid, binary, module, name, size, run, producer, arm, compiler, pct, obj = c
    P = PROD[producer]
    flags = P.ARMS[module][arm]
    d = os.path.join(WORK, fid.replace(":", "_"))
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    rid = fid.split(":", 1)[1]
    raw = P.prelude() + P.transform(open(f"{F}/{run}/m2c/c/{rid.replace(':', '_')}.c", errors="replace").read())
    open(d + "/raw.c", "w").write(raw)
    pp = subprocess.run(["cpp", "-P", "-undef", "-nostdinc", d + "/raw.c"], capture_output=True, text=True)
    if pp.returncode != 0:
        return {"fid": fid, "res": "CPP_FAIL"}
    open(d + "/base.c", "w").write(pp.stdout)
    shutil.copy(obj, d + "/target.o")
    open(d + "/compile.sh", "w").write(
        f"#!/bin/bash\nW=$(mktemp -d {PW}/c.XXXXXX) || exit 1\n"
        "cp \"$1\" \"$W/fn.c\" && (cd \"$W\" && " + f"{TC['wibo']} {compiler} {flags}" + " -c fn.c -o fn.o) && mv \"$W/fn.o\" \"$3\"\n"
        "rc=$?; rm -rf \"$W\"; rm -f \"$1\"; exit $rc\n")
    os.chmod(d + "/compile.sh", 0o755)
    open(d + "/settings.toml", "w").write(f'func_name = "{name}"\ncompiler_type = "mwcc"\n'
                                          f'objdump_command = "{OD} --disassemble={name}"\n')
    base = verify(d + "/base.c", obj, name, flags, compiler)
    env = dict(os.environ, TMPDIR=PW)
    subprocess.run(["timeout", str(wall), PY, PERM + "/permuter.py", d, "--stop-on-zero", "-j", "2", "--best-only"],
                   cwd=PERM, capture_output=True, text=True, env=env)
    best, best_src = None, None
    for o in sorted(glob.glob(d + "/output-*/source.c")):
        p = verify(o, obj, name, flags, compiler)
        if p is not None and (best is None or p > best):
            best, best_src = p, o
    res = "MATCH" if best == 100.0 else "IMPROVED" if best is not None and base is not None and best > base else "NONE"
    out = {"fid": fid, "binary": binary, "module": module, "name": name, "size": size, "run": run, "producer": producer,
           "arm": arm, "compiler": compiler, "target_obj": obj, "sweep_pct": pct, "base_pct": base, "best_pct": best,
           "res": res, "ts": time.time()}
    if best_src:
        keep = f"{ST}/perm_sources/{fid.replace(':', '_')}.c"
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.copy(best_src, keep)
        out["best_source"] = keep
    shutil.rmtree(d, ignore_errors=True)
    return out


def publish(r, game):
    """A verified 100% joins its stage run; the factory lane carves and gates it (the arbiter is the lane build)."""
    d = init_stage(r["binary"], game, r["module"], r["compiler"])
    rid = r["fid"].split(":", 1)[1]
    shutil.copy(r["best_source"], f"{d}/m2c/c/{rid.replace(':', '_')}.c")
    arm = f"{r['producer']}.{r['arm']}"
    with open(d + "/corpus.jsonl", "a") as w:
        w.write(json.dumps({"id": rid, "module": r["module"], "kind": "FUNCTION", "name": r["name"],
                            "start": rid.split(":")[1], "size": r["size"]}) + "\n")
    with open(d + "/sweep.jsonl", "a") as w:
        w.write(json.dumps({"id": rid, "sym": r["name"], "size": r["size"], "obj": r["target_obj"], "state": "OK",
                            "arms": {arm: {"compiles": True, "pct": 100.0}}}) + "\n")
    with open(d + "/matched.tsv", "a") as w:
        w.write(f"{rid}\t{arm}\n")


def tick(k, jobs, wall):
    if not os.path.exists(READY):
        print("kill switch absent: no-op"); return
    os.makedirs(PW, exist_ok=True); os.makedirs(WORK, exist_ok=True)
    bins = lane_binaries()
    tried = {json.loads(l)["fid"] for l in open(TRIED)} if os.path.exists(TRIED) else set()
    c = sqlite3.connect(F + "/ledger/ledger.db")
    cert = {r[0] for r in c.execute("SELECT fid FROM cert")}
    matched = {r[0] for r in c.execute("SELECT fid FROM attempt WHERE state='MATCH'")}
    q = ("SELECT a.fid, f.binary, f.module, f.name, f.size, a.run, a.producer, a.arm, a.compiler, a.pct, a.target_obj "
         "FROM attempt a JOIN function f USING(fid) WHERE a.target_ok=1 AND a.state IN ('NEAR99','NEAR95') "
         "AND a.producer IN ('factory','factory_vs2') ORDER BY a.pct DESC, f.size ASC")
    picks, seen = [], set()
    for row in c.execute(q):
        fid = row[0]
        if fid in seen or fid in tried or fid in cert or fid in matched or row[1] not in bins:
            continue
        if not os.path.exists(row[10]) or not os.path.exists(row[8]):
            continue
        seen.add(fid); picks.append(row)
        if len(picks) >= k:
            break
    print(f"{time.strftime('%FT%TZ', time.gmtime())} perm tick: {len(picks)} picks", flush=True)
    with cf.ThreadPoolExecutor(jobs) as ex:
        for r in ex.map(lambda p: one(p, wall), picks):
            with open(TRIED, "a") as w:
                w.write(json.dumps(r) + "\n")
            if r.get("res") == "MATCH":
                publish(r, bins[r["binary"]])
            print(f"  {r['fid']} {r.get('res')} {r.get('base_pct')} -> {r.get('best_pct')}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tick", "init"])
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--wall", type=int, default=300)
    a = ap.parse_args()
    if a.cmd == "init":
        for ln in json.load(open(F + "/lanes_factory.json")):
            for r in ln["runs"]:
                if r["run"].startswith("stages/perm-"):
                    mod = r["run"].rsplit("-", 1)[1]
                    init_stage(ln["binary"], ln["game"], mod, r["compiler_path"])
                    print("init", r["run"])
        return
    tick(a.k, a.jobs, a.wall)


if __name__ == "__main__":
    main()
