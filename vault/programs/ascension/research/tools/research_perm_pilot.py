#!/usr/bin/env python3
"""Permuter pilot (pane 5a77ca0e, 2026-11-20). Pre-registered: sample = up to 30 REGALLOC_ONLY + 20 INSDEL near misses
(sweep pct >= 95) from research/nearmiss.v1.jsonl (wp-vs2, tn-vs2); budget 300 s permuter wall each (-j 2);
SUCCESS = a permuter output that OUR compile + objdiff scores 100.0 (the permuter's own score is not evidence).
Writes only /home/kobii/agora/factory/research/perm/."""
import concurrent.futures as cf, glob, json, os, random, shutil, subprocess, sys, tempfile
sys.path.insert(0, "/home/kobii/missions/t1-campaign"); sys.path.insert(0, "/home/kobii/agora/factory"); sys.path.insert(0, "/home/kobii/agora/factory/typegen")
from modules.recon_fabric import cv1
import factory_vs2 as V
F = "/home/kobii/agora/factory"; R = F + "/research"; P = R + "/perm"
PERM = "/home/kobii/tools/decomp-permuter"; PY = "/home/kobii/tools/permuter-venv/bin/python"
RUNS = {"wp-vs2": (F + "/typegen/wp-vs2-full", F + "/wp-repo/build/compilers/Wii/1.1/mwcceppc.exe"),
        "tn-vs2": (F + "/typegen/tn-vs2-full", None)}
TC = cv1.toolchain()
OD = "powerpc-linux-gnu-objdump -dr -EB -mpowerpc -M broadway"
WALL = 300


def compiler(run):
    return json.load(open(run + "/summary.json"))["compiler"]


def verify(src_c, row, flags, mw):
    w = tempfile.mkdtemp(prefix="pv-")
    try:
        shutil.copy(src_c, w + "/fn.c")
        r = subprocess.run([TC["wibo"], mw] + flags.split() + ["-c", "fn.c", "-o", "fn.o"], cwd=w, capture_output=True, timeout=90)
        if r.returncode != 0:
            return None
        return cv1.objdiff_pct(dict(TC, mw=mw), row["obj"], w + "/fn.o", row["sym"], w)
    finally:
        shutil.rmtree(w, ignore_errors=True)


def one(job):
    tag, a, row = job
    run, _ = RUNS[tag]
    mw = compiler(run)
    flags = V.ARMS["main"][a["arm"]]
    d = os.path.join(P, a["id"].replace(":", "_"))
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    raw = V.prelude() + V.transform(open(f"{run}/m2c/c/{a['id'].replace(':', '_')}.c", errors="replace").read())
    open(d + "/raw.c", "w").write(raw)
    pp = subprocess.run(["cpp", "-P", "-undef", "-nostdinc", d + "/raw.c"], capture_output=True, text=True)
    if pp.returncode != 0:
        return {**a, "res": "CPP_FAIL", "why": pp.stderr[-200:]}
    open(d + "/base.c", "w").write(pp.stdout)
    shutil.copy(row["obj"], d + "/target.o")
    # wibo scans its working directory on every file lookup: a compile in a crowded dir costs 25 s instead of 0.02 s
    # (measured 2026-11-20, /tmp with 735,445 entries). Each candidate compiles in its own empty dir, removed after.
    open(d + "/compile.sh", "w").write(
        "#!/bin/bash\nW=$(mktemp -d /home/kobii/agora/factory/research/pw/c.XXXXXX) || exit 1\n"
        "cp \"$1\" \"$W/fn.c\" && (cd \"$W\" && " + f"{TC['wibo']} {mw} {flags}" + " -c fn.c -o fn.o) && mv \"$W/fn.o\" \"$3\"\n"
        "rc=$?; rm -rf \"$W\"; rm -f \"$1\"; exit $rc\n")
    os.chmod(d + "/compile.sh", 0o755)
    open(d + "/settings.toml", "w").write(f'func_name = "{row["sym"]}"\ncompiler_type = "mwcc"\n'
                                          f'objdump_command = "{OD} --disassemble={row["sym"]}"\n')
    base_pct = verify(d + "/base.c", row, flags, mw)
    try:
        r = subprocess.run(["timeout", str(WALL), PY, PERM + "/permuter.py", d, "--stop-on-zero", "-j", "2", "--best-only"],
                           cwd=PERM, capture_output=True, text=True)
        tail = (r.stdout + r.stderr)[-300:]
    except Exception as e:  # noqa: BLE001
        return {**a, "res": "PERM_ERR", "why": str(e)}
    best = None
    for o in sorted(glob.glob(d + "/output-*/source.c")):
        pct = verify(o, row, flags, mw)
        if pct is not None and (best is None or pct > best):
            best = pct
    res = "MATCH" if best == 100.0 else "IMPROVED" if best is not None and base_pct is not None and best > base_pct else "NONE"
    return {**a, "res": res, "base_pct": base_pct, "best_pct": best, "outputs": len(glob.glob(d + "/output-*")), "tail": tail}


def main():
    rows = {}
    for tag, (run, _) in RUNS.items():
        for l in open(run + "/sweep.jsonl"):
            x = json.loads(l); rows[(tag, x["id"])] = x
    at = [json.loads(l) for l in open(R + "/nearmiss.v1.jsonl")]
    at = [x for x in at if x.get("run") in RUNS and x.get("sweep_pct", 0) >= 95 and x.get("cls") in ("REGALLOC_ONLY", "INSDEL")]
    random.seed(20261120)
    reg = [x for x in at if x["cls"] == "REGALLOC_ONLY"]; ins = [x for x in at if x["cls"] == "INSDEL"]
    pick = random.sample(reg, min(30, len(reg))) + random.sample(ins, min(20, len(ins)))
    os.makedirs(P, exist_ok=True)
    jobs = [(x["run"], x, rows[(x["run"], x["id"])]) for x in pick]
    print("pilot", len(jobs), "functions", flush=True)
    with open(R + "/perm_pilot.jsonl", "w") as w, cf.ThreadPoolExecutor(8) as ex:
        for res in ex.map(one, jobs):
            w.write(json.dumps(res) + "\n"); w.flush()
    print("PERM_PILOT_DONE", flush=True)


if __name__ == "__main__":
    main()
