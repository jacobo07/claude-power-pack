#!/usr/bin/env python3
"""Deterministic reconstruction factory, generalised from the KSR lane (t1-campaign modules/recon_fabric/ksr_lane.py +
decomp_work/b8d1db7edd42/code/m2c_producer.py) to any dtk-template binary.

Stages (no model call, no network):
  corpus  : functions of record from config/<GAME>/symbols.txt (or a module's symbols.txt), with size
  lift    : m2c over dtk's own asm (the pinned KSR factory producer and venv), one record per function
  sweep   : each L1 lift -> repair.transform_v5 + toolchain_sd.retype -> typedef prelude -> mwcceppc (the game's
            compiler of record, under wibo) on every flag arm -> objdiff-cli match % against the function's own
            dtk target object
  choose  : one arm per target object (the arm with more matches, provided the other arm holds no exclusive match,
            else FLAGS_SPLIT) -- the KSR certification rule, so no per-function flag cherry-picking
Outputs (out dir): corpus.jsonl, m2c/results.tsv + m2c/c/*.c, sweep.jsonl (one row per lift), summary.json.
A match here is PROVISIONAL_MATCH (objdiff 100% vs the split target object); certification into the product tree
(src unit + configure + ninja report) is a separate step.

usage: factory.py run --repo R --game RMCP01 --out O [--module main|StaticR] [--sample N --seed S] [--threads T]
"""
import argparse, concurrent.futures, glob, hashlib, json, os, random, re, shutil, subprocess, sys, tempfile, time

T1 = "/home/kobii/missions/t1-campaign"
sys.path.insert(0, T1)
from modules.recon_fabric import cv1  # noqa: E402  (read-only reuse)

KSR_TOOLS = "/opt/ksr-decomp"
PRODUCER = "/home/kobii/decomp_work/b8d1db7edd42/code/m2c_producer.py"
PRELUDE_HDR = "/home/kobii/missions/tennis-w11/out/d28/d1d/ctx/tennis_context.h"
SYM = re.compile(r"^\s*(\S+)\s*=\s*\.text:0x([0-9A-Fa-f]+);.*type:function.*size:0x([0-9A-Fa-f]+)")

BASE = ("-nodefaults -align powerpc -enc SJIS -proc gekko -enum int -O4,p -inline auto -fp hardware "
        "-Cpp_exceptions off -RTTI off -func_align 4")
ARMS = {
    "main": {"dol": BASE + " -ipa file -rostr -str noreuse -use_lmw_stmw=on",
             "ksr_sd0": "-proc gekko -RTTI off -Cpp_exceptions off -enum int -use_lmw_stmw on -fp hard -rostr -sdata 0 -sdata2 0 -lang c -nodefaults -O4,p"},
    "StaticR": {"rel": BASE + " -sdata 0 -sdata2 0 -ipa file -rostr -str noreuse -use_lmw_stmw=on",
                "rel_noipa": BASE + " -sdata 0 -sdata2 0 -rostr -use_lmw_stmw=on"},
}


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def corpus(repo, game, module, out, symbols=None):
    p = symbols if symbols else os.path.join(repo, "config", game, "symbols.txt") if module == "main" else \
        next(iter(glob.glob(os.path.join(repo, "config", game, "*", module, "symbols.txt")) +
                  glob.glob(os.path.join(repo, "config", game, module, "symbols.txt"))), None)
    rows = []
    for l in open(p, encoding="utf-8"):
        m = SYM.match(l)
        if m:
            rows.append({"id": "%s:%s" % (module, m.group(2).upper().zfill(8)), "module": module, "kind": "FUNCTION",
                         "name": m.group(1), "start": m.group(2), "size": int(m.group(3), 16)})
    with open(os.path.join(out, "corpus.jsonl"), "w", encoding="utf-8", newline="\n") as w:
        for r in rows:
            w.write(json.dumps(r) + "\n")
    return rows, p


def flat_asm(repo, game, module, out):
    """m2c_producer reads one directory, non-recursively: link every dtk .s into one flat dir."""
    src = os.path.join(repo, "build", game, "asm") if module == "main" else os.path.join(repo, "build", game, module, "asm")
    root = os.path.join(out, "asm_root")
    dst = os.path.join(root, "asm") if module == "main" else os.path.join(root, module, "asm")
    os.makedirs(dst, exist_ok=True)
    n = 0
    for d, _, fs in os.walk(src):
        for f in fs:
            if f.endswith(".s"):
                link = os.path.join(dst, os.path.relpath(os.path.join(d, f), src).replace(os.sep, "__"))
                if not os.path.lexists(link):
                    os.symlink(os.path.join(d, f), link)
                n += 1
    return root, n


def lift(out, root, module, ids):
    mdir = os.path.join(out, "m2c")
    os.makedirs(mdir, exist_ok=True)
    idf = os.path.join(out, "ids.txt")
    open(idf, "w").write("\n".join(ids) + "\n")
    env = dict(os.environ, KSR_DECOMP_TOOLS=KSR_TOOLS)
    r = subprocess.run([os.path.join(KSR_TOOLS, "venv/bin/python"), PRODUCER, os.path.join(out, "corpus.jsonl"), root, mdir,
                        "--module", module, "--ids", idf], env=env, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-2000:]


def target_index(repo, game):
    idx = {}
    paths = set(glob.glob(os.path.join(repo, "build", game, "obj", "**", "*.o"), recursive=True))
    paths |= set(glob.glob(os.path.join(repo, "build", game, "*", "obj", "**", "*.o"), recursive=True))  # module objects (StaticR)
    for p in sorted(paths):
        for nm in cv1.elf_funcs(p):
            idx.setdefault(nm, []).append(p)
    return idx


def prelude():
    return "".join(l for l in open(PRELUDE_HDR, encoding="utf-8")
                   if l.startswith("typedef ") and l.rstrip().endswith(";") and "struct" not in l) + "\n"


def transform(src):
    from modules.recon_fabric import repair, toolchain_sd
    return toolchain_sd.retype(repair.transform_v5(src))


def judge(tc, src, sym, tgt, flags):
    work = tempfile.mkdtemp(prefix="fac-")
    try:
        c, o = os.path.join(work, "fn.c"), os.path.join(work, "fn.o")
        open(c, "w", encoding="utf-8", newline="\n").write(src)
        try:
            rc = subprocess.run([tc["wibo"], tc["mw"]] + flags.split() + ["-c", "fn.c", "-o", "fn.o"], cwd=work,
                                capture_output=True, timeout=90).returncode
        except subprocess.TimeoutExpired:
            rc = -9
        if rc != 0 or not os.path.exists(o) or sym not in cv1.elf_funcs(o):
            return {"compiles": False, "pct": None}
        return {"compiles": True, "pct": cv1.objdiff_pct(tc, tgt, o, sym, work)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def measure(tc, row, mdir, idx, pre, arms):
    p = os.path.join(mdir, "c", row["id"].replace(":", "_") + ".c")
    out = {"id": row["id"], "sym": row["name"], "size": row["size"]}
    objs = idx.get(row["name"]) or []
    if len(objs) != 1:
        out["state"] = "NO_TARGET" if not objs else "TARGET_AMBIGUOUS"
        return out
    out["obj"] = objs[0]
    try:
        src = transform(open(p, encoding="utf-8", errors="replace").read())
    except Exception as e:
        out["state"] = "XF_ERROR:" + type(e).__name__
        return out
    out["state"] = "OK"
    out["arms"] = {a: judge(tc, pre + src, row["name"], objs[0], f) for a, f in arms.items()}
    return out


def choose(rows, arms):
    """KSR rule: one arm per target object; FLAGS_SPLIT objects certify nothing."""
    by_obj = {}
    for r in rows:
        if r.get("state") == "OK":
            by_obj.setdefault(r["obj"], []).append(r)
    names = list(arms)
    matched, split_objs = [], 0
    for obj, rs in by_obj.items():
        win = {a: {r["id"] for r in rs if r["arms"][a]["pct"] == 100.0} for a in names}
        best = max(names, key=lambda a: len(win[a]))
        lost = set().union(*[win[a] for a in names if a != best]) - win[best]
        if lost and win[best]:
            split_objs += 1
            continue
        matched += [(rid, best) for rid in win[best]]
    return matched, split_objs


def run(a):
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    rows, symp = corpus(a.repo, a.game, a.module, a.out, a.symbols)
    pick = rows
    if a.sample:
        pick = random.Random(a.seed).sample(rows, min(a.sample, len(rows)))
    root, nasm = flat_asm(a.repo, a.game, a.module, a.out)
    rc, tail = lift(a.out, root, a.module, [r["id"] for r in pick])
    t_lift = time.time() - t0
    mdir = os.path.join(a.out, "m2c")
    states = {}
    for l in open(os.path.join(mdir, "results.tsv"), encoding="utf-8"):
        p = l.rstrip("\n").split("\t")
        states[p[0]] = p[1]
    l1 = [r for r in pick if states.get(r["id"]) == "L1"]
    tc = cv1.toolchain()
    tc = dict(tc, mw=os.path.join(a.repo, "build/compilers", a.compiler, "mwcceppc.exe"))
    idx = target_index(a.repo, a.game)
    pre = prelude()
    arms = ARMS[a.module]
    t1 = time.time()
    res = []
    with open(os.path.join(a.out, "sweep.jsonl"), "w", encoding="utf-8", newline="\n") as w, \
            concurrent.futures.ThreadPoolExecutor(a.threads) as ex:
        for r in ex.map(lambda row: measure(tc, row, mdir, idx, pre, arms), l1):
            res.append(r)
            w.write(json.dumps(r) + "\n")
            w.flush()
    matched, split_objs = choose(res, arms)
    st = {}
    for s in states.values():
        st[s] = st.get(s, 0) + 1
    per_arm = {k: sum(1 for r in res if r.get("state") == "OK" and r["arms"][k]["pct"] == 100.0) for k in arms}
    comp = sum(1 for r in res if r.get("state") == "OK" and any(x["compiles"] for x in r["arms"].values()))
    near = sum(1 for r in res if r.get("state") == "OK" and any((x["pct"] or 0) >= 90 for x in r["arms"].values())
               and not any(x["pct"] == 100.0 for x in r["arms"].values()))
    summ = {"game": a.game, "module": a.module, "symbols": symp, "symbols_sha256": sha_file(symp), "corpus": len(rows),
            "picked": len(pick), "sample": a.sample, "seed": a.seed, "asm_files": nasm, "lift_rc": rc, "lift_tail": tail[-400:],
            "m2c_states": st, "l1": len(l1), "target_states": {s: sum(1 for r in res if r.get("state") == s) for s in {r.get("state") for r in res}},
            "compiles_any_arm": comp, "match_per_arm": per_arm, "provisional_match_object_consistent": len(matched),
            "flags_split_objects": split_objs, "near_miss_ge90": near,
            "matched_bytes": sum(r["size"] for r in res if (r["id"], None) and r["id"] in {m[0] for m in matched}),
            "seconds_lift": round(t_lift, 1), "seconds_sweep": round(time.time() - t1, 1), "threads": a.threads,
            "arms": arms, "compiler": tc["mw"], "compiler_sha256": sha_file(tc["mw"]), "prelude_sha256": sha_file(PRELUDE_HDR),
            "producer_sha256": sha_file(PRODUCER)}
    json.dump(summ, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    with open(os.path.join(a.out, "matched.tsv"), "w", newline="\n") as w:
        for rid, arm in sorted(matched):
            w.write("%s\t%s\n" % (rid, arm))
    print(json.dumps({k: summ[k] for k in ("picked", "m2c_states", "l1", "target_states", "compiles_any_arm", "match_per_arm",
                                           "provisional_match_object_consistent", "flags_split_objects", "near_miss_ge90",
                                           "seconds_lift", "seconds_sweep", "lift_rc")}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--game", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--module", default="main")
    ap.add_argument("--symbols", default=None)
    ap.add_argument("--compiler", default="Wii/0x4201_127")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--threads", type=int, default=8)
    run(ap.parse_args())
