#!/usr/bin/env python3
"""F2 (carve route) of vault/specs/ascension-reconstruction-factory.md: one source unit PER FUNCTION for factory matches
that live in dtk auto-split objects, the same shape as the MKW lane's own `auto_tu/<fn>.cpp` carve (S112M, S151M).
One function per unit = exactly the context the factory measured it in (single-function fn.c), so no cross-function
inlining can change its bytes.

For each matched function whose target object is `auto_*`:
  split   : `factory/<sym>.c` with `.text start:<addr> end:<addr+size>` (main: config/<GAME>/splits.txt;
            a module: config/<GAME>/module/splits.txt)
  source  : src/factory/<sym>.c = typedef prelude + the transformed m2c lift (the measured source, byte for byte)
  object  : `Object(NonMatching, "factory/<sym>.c", cflags=[<the object's chosen arm>])`: NonMatching links the
            original bytes, so the binary's sha1 cannot change; the report still scores the function.
Writes only inside --repo (a scratch clone). <run>/carved.jsonl lists every unit written.

usage: carve.py --run RUN --repo SCRATCH --game RMCP01 [--compiler Wii/0x4201_127] [--limit N]
"""
import argparse, json, os, re, sys

sys.path.insert(0, "/home/kobii/missions/t1-campaign")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib  # noqa: E402
# --producer selects the run's producer module (prelude + transform + ARMS): factory (base) or factory_vs2
# (typegen/, m2c --valid-syntax + macros); a run must be carved with the producer that swept it.
_pp = argparse.ArgumentParser(add_help=False)
_pp.add_argument("--producer", default="factory")
_PROD = _pp.parse_known_args()[0].producer  # review F4: also accepts --producer=X
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "typegen"))
F = importlib.import_module(_PROD)  # noqa: E402

SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def flag_items(flags):
    out = []
    for t in flags.split():
        if t.startswith("-") or not out:
            out.append(t)
        else:
            out[-1] += " " + t
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--game", required=True)
    ap.add_argument("--compiler", default="Wii/0x4201_127")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--producer", default="factory")
    ap.add_argument("--lib", default="Factory")
    a = ap.parse_args()
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(a.run, "sweep.jsonl"))}
    corp = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(a.run, "corpus.jsonl"))}
    module = corp[next(iter(corp))]["module"]
    arms = F.ARMS[module]
    picks = []
    for l in open(os.path.join(a.run, "matched.tsv")):
        if not l.strip():
            continue
        rid, arm = l.split()
        if os.path.basename(rows[rid]["obj"]).startswith("auto_") and SAFE.match(corp[rid]["name"]):
            picks.append((rid, arm))
    picks.sort(key=lambda x: int(x[0].split(":")[1], 16))
    if a.limit:
        picks = picks[:a.limit]
    splits_p = os.path.join(a.repo, "config", a.game, "splits.txt" if module == "main" else "module/splits.txt")
    have = set(re.findall(r"^(\S+):\s*$", open(splits_p, encoding="utf-8").read(), re.M))
    cfg_p = os.path.join(a.repo, "configure.py")
    cfg = open(cfg_p, encoding="utf-8").read()
    pre = F.prelude()
    splits, decls, out = [], [], []
    for rid, arm in picks:
        c = corp[rid]
        unit = "factory/%s.c" % c["name"]
        if unit in have:
            continue
        have.add(unit)  # review F3: two picks with one name in a batch must not emit the unit twice
        src = F.transform(open(os.path.join(a.run, "m2c", "c", rid.replace(":", "_") + ".c"), encoding="utf-8", errors="replace").read())
        dst = os.path.join(a.repo, "src", unit)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8", newline="\n").write(pre + src)
        start = int(c["start"], 16)
        splits.append("%s:\n\t.text       start:0x%08X end:0x%08X\n" % (unit, start, start + c["size"]))
        decls.append('Object(NonMatching, "%s", cflags=[%s])' % (unit, ", ".join(json.dumps(x) for x in flag_items(arms[arm]))))
        out.append({"id": rid, "unit": unit, "arm": arm, "size": c["size"]})
    if not out:
        print(json.dumps({"carved": 0}))
        return
    open(splits_p, "a", encoding="utf-8", newline="\n").write("\n" + "\n".join(splits))
    body = "\n".join("            %s," % d for d in decls)
    if module == "main":
        lib = ('    {\n        "lib": "%s",\n        "mw_version": "%s",\n        "cflags": cflags_base,\n'
               '        "progress_category": "game",\n        "src_dir": "src",\n        "objects": [\n%s\n        ],\n    },\n'
               % (a.lib, a.compiler, body))
        assert "config.libs = [\n" in cfg
        cfg = cfg.replace("config.libs = [\n", "config.libs = [\n" + lib, 1)
    else:
        anchor = '"lib": "%s",' % module
        i = cfg.index(anchor)
        j = cfg.index('"objects": [', i) + len('"objects": [')
        cfg = cfg[:j] + "\n" + body + cfg[j:]
    open(cfg_p, "w", encoding="utf-8", newline="\n").write(cfg)
    with open(os.path.join(a.run, "carved.jsonl"), "a", newline="\n") as w:
        for r in out:
            w.write(json.dumps(r) + "\n")
    print(json.dumps({"module": module, "carved": len(out), "bytes": sum(r["size"] for r in out)}))


if __name__ == "__main__":
    main()
