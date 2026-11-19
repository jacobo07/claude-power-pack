#!/usr/bin/env python3
"""F2 of vault/specs/ascension-reconstruction-factory.md: turn a factory run's PROVISIONAL_MATCH rows into source units of a
dtk-template repo, so the repo's own `ninja build/<GAME>/report.json` counts them.

Per target object with >= 1 match (main module only in this version):
  - unit: the object's split unit when it has one (skipped if a source file already exists: never overwrite a human
    source), else a new split `factory/<auto object>.c` covering exactly that auto object's .text range;
  - source: built greedily in address order. A function is kept only if, after adding it, EVERY function already in the
    unit still compiles to the same bytes as its standalone (matched) compile (`cv1.func_hash`): -inline auto / -ipa
    file can inline one function into another once they share a file. A final objdiff pass re-checks each kept
    function at 100% against the target object, and drops the unit if any is not;
  - declaration: `Object(NonMatching, unit, cflags=[the object's chosen arm, -lang c])`.
Writes only inside --repo (a scratch clone). Prints a JSON summary; writes <run>/materialized.jsonl.

usage: materialize.py --run RUN --repo SCRATCH --game RMCP01 [--compiler Wii/0x4201_127] [--limit-objects N]
"""
import argparse, glob, json, os, re, shutil, struct, subprocess, sys, tempfile

sys.path.insert(0, "/home/kobii/missions/t1-campaign")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.recon_fabric import cv1  # noqa: E402
import factory as F  # noqa: E402

AUTO = re.compile(r"^auto_(\d+)_([0-9A-Fa-f]{8})_text$")


def text_size(obj):
    """.text section size of an ELF32 big-endian object."""
    b = open(obj, "rb").read()
    shoff, = struct.unpack(">I", b[32:36])
    shentsize, shnum, shstrndx = struct.unpack(">HHH", b[46:52])
    sec = [struct.unpack(">IIIIIIIIII", b[shoff + i * shentsize: shoff + (i + 1) * shentsize]) for i in range(shnum)]
    stro = sec[shstrndx][4]
    for s in sec:
        nm = b[stro + s[0]: b.index(b"\0", stro + s[0])].decode()
        if nm == ".text":
            return s[5]
    return None


def flag_items(flags):
    """'-sdata 0 -O4,p' -> ['-sdata 0', '-O4,p'] (configure.py cflags list form)."""
    out = []
    for t in flags.split():
        if t.startswith("-") or not out:
            out.append(t)
        else:
            out[-1] += " " + t
    return out


def compile_hashes(tc, src, flags, syms):
    work = tempfile.mkdtemp(prefix="mat-")
    try:
        c, o = os.path.join(work, "fn.c"), os.path.join(work, "fn.o")
        open(c, "w", encoding="utf-8", newline="\n").write(src)
        r = subprocess.run([tc["wibo"], tc["mw"]] + flags.split() + ["-c", "fn.c", "-o", "fn.o"], cwd=work,
                           capture_output=True, timeout=180)
        if r.returncode != 0 or not os.path.exists(o):
            return None, None
        keep = os.path.join(tempfile.gettempdir(), "mat-last-%d.o" % os.getpid())
        shutil.copy(o, keep)
        return {s: cv1.func_hash(o, s) for s in syms}, keep
    except subprocess.TimeoutExpired:
        return None, None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def build_unit(tc, pre, items, flags, target):
    """items: [(sym, src)] in address order -> (kept syms, source text, final object path) or ([], None, None)."""
    solo = {}
    for sym, src in items:
        h, _ = compile_hashes(tc, pre + src, flags, [sym])
        if h and h.get(sym):
            solo[sym] = h[sym]
    kept, body = [], []
    for sym, src in items:
        if sym not in solo:
            continue
        h, _ = compile_hashes(tc, pre + "\n".join(body + [src]), flags, [s for s, _ in kept] + [sym])
        if h and all(h.get(s) == solo[s] for s in [s for s, _ in kept] + [sym]):
            kept.append((sym, src))
            body.append(src)
    if not kept:
        return [], None, None
    text = pre + "\n".join(body) + "\n"
    h, obj = compile_hashes(tc, text, flags, [s for s, _ in kept])
    work = tempfile.mkdtemp(prefix="matv-")
    try:
        final = [s for s, _ in kept if cv1.objdiff_pct(tc, target, obj, s, work) == 100.0]
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if len(final) != len(kept):  # never ship a unit whose combined object is not what was measured
        return [], None, None
    return final, text, obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--game", required=True)
    ap.add_argument("--compiler", default="Wii/0x4201_127")
    ap.add_argument("--limit-objects", type=int, default=0)
    a = ap.parse_args()
    obj_root = os.path.join(a.repo, "build", a.game, "obj")
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(a.run, "sweep.jsonl"))}
    corp = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(a.run, "corpus.jsonl"))}
    arms = F.ARMS[corp[next(iter(corp))]["module"]]
    by_obj = {}
    for l in open(os.path.join(a.run, "matched.tsv")):
        if l.strip():
            rid, arm = l.split()
            by_obj.setdefault(rows[rid]["obj"], {"arm": arm, "ids": []})["ids"].append(rid)
    splits_p = os.path.join(a.repo, "config", a.game, "splits.txt")
    splits = open(splits_p, encoding="utf-8").read()
    units = set(re.findall(r"^(\S+):\s*$", splits, re.M))
    cfg_p = os.path.join(a.repo, "configure.py")
    cfg = open(cfg_p, encoding="utf-8").read()
    tc = dict(cv1.toolchain(), mw=os.path.join(a.repo, "build/compilers", a.compiler, "mwcceppc.exe"))
    pre = F.prelude()
    new_splits, new_objs, log, n_fn = [], [], [], 0
    objs = sorted(by_obj)
    if a.limit_objects:
        objs = objs[:a.limit_objects]
    for obj in objs:
        info = by_obj[obj]
        rel = obj.split("/build/%s/obj/" % a.game, 1)[1][:-2]
        m = AUTO.match(os.path.basename(rel))
        if m:
            unit = "factory/%s.c" % rel
        else:
            unit = next((u for u in units if os.path.splitext(u)[0] == rel), None)
            if not unit or os.path.exists(os.path.join(a.repo, "src", unit)) or ('Object(NonMatching, "%s")' % unit) not in cfg:
                log.append({"obj": rel, "skip": "no unit / source exists / not a bare NonMatching object"})
                continue
        flags = arms[info["arm"]] + ("" if unit.endswith(".c") else " -lang c")
        items = []
        for rid in sorted(info["ids"], key=lambda r: int(r.split(":")[1], 16)):
            p = os.path.join(a.run, "m2c", "c", rid.replace(":", "_") + ".c")
            try:
                items.append((corp[rid]["name"], F.transform(open(p, encoding="utf-8", errors="replace").read())))
            except Exception as e:  # recorded, never silent: the function is offered but not built
                log.append({"obj": rel, "fn": rid, "transform_error": type(e).__name__})
        kept, text, _ = build_unit(tc, pre, items, flags, obj)
        log.append({"obj": rel, "unit": unit, "arm": info["arm"], "matched": len(info["ids"]), "kept": len(kept)})
        if not kept:
            continue
        dst = os.path.join(a.repo, "src", unit)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8", newline="\n").write(
            "/* factory (vault/specs/ascension-reconstruction-factory.md): m2c lifts, objdiff 100%% per function, arm %s */\n%s"
            % (info["arm"], text))
        items_cfg = ", ".join(json.dumps(x) for x in flag_items(flags))
        decl = 'Object(NonMatching, "%s", cflags=[%s])' % (unit, items_cfg)
        if m:
            start = int(m.group(2), 16)
            new_splits.append("%s:\n\t.text       start:0x%08X end:0x%08X\n" % (unit, start, start + text_size(obj)))
            new_objs.append(decl)
        else:
            cfg = cfg.replace('Object(NonMatching, "%s")' % unit, decl, 1)
        n_fn += len(kept)
    if new_splits:
        open(splits_p, "a", encoding="utf-8", newline="\n").write("\n" + "\n".join(new_splits))
        lib = ('    {\n        "lib": "Factory",\n        "mw_version": "%s",\n        "cflags": cflags_base,\n'
               '        "progress_category": "game",\n        "src_dir": "src",\n        "objects": [\n%s\n        ],\n    },\n'
               % (a.compiler, "\n".join("            %s," % d for d in new_objs)))
        cfg = cfg.replace("config.libs = [\n", "config.libs = [\n" + lib, 1)
    open(cfg_p, "w", encoding="utf-8", newline="\n").write(cfg)
    with open(os.path.join(a.run, "materialized.jsonl"), "w", newline="\n") as w:
        for r in log:
            w.write(json.dumps(r) + "\n")
    print(json.dumps({"objects": len(objs), "units_written": sum(1 for r in log if r.get("kept")),
                      "functions_kept": n_fn, "functions_offered": sum(len(by_obj[o]["ids"]) for o in objs),
                      "new_splits": len(new_splits), "skipped": sum(1 for r in log if "skip" in r)}))


if __name__ == "__main__":
    main()
