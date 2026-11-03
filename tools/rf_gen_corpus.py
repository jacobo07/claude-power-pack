#!/usr/bin/env python3
"""Generate the synthetic corpus's derived sources deterministically from fixtures/synthetic/src/{ref,heldout}:
  src/skeleton/<source>   a NON-matching but compiling start point made by applying 1-2 operators to the reference (inverse operators);
  src/mutants/<source>    a compiling semantic mutant (negative control: must never certify);
  heldout.seal.json       sha256 of every held-out source + the manifest, the commitment the release gate checks.
Re-running must reproduce the committed files byte for byte (checked by V-RF-CORPUS-DETERMINISTIC)."""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from modules.reconstruction_factory.core import Factory
from modules.reconstruction_factory.operators import apply_all
from modules.reconstruction_factory.search import score
from modules.reconstruction_factory import om as OM, om_skeleton as OS

MUT = [(r"(?<![\w])(\w+) \+ (\w+)", r"\1 - \2"), (r" < ", " <= "), (r" > ", " >= "), (r" == ", " != "), (r"\* (\d+)", r"* \1 + 1"),
       (r"return (\w+);", r"return \1 + 1;"), (r" \+ (\w+);", r" + \1 + 1;")]


def om_registry(f):
    img = OM.Image(f.adapter, {n: f.target(n) for n in f.project.names() if f.project.functions[n]["lang"] == "cxx"})
    return OM.build_registry(img)


def lifted_skeleton(f, fn, text, reg):
    """Object-Model skeleton: a virtual call is written as the raw vptr/slot call (the lift's form) after one inverse operator."""
    for t1 in [text] + [t for _o, t in apply_all(text)]:
        for lt in OS.method_to_vslot(t1, reg)[:1]:
            s = score(f, fn, lt)
            if s and not s["exact"]:
                return lt
    return None


def skeleton_for(f, fn, text, reg=None):
    if reg is not None and f.project.functions[fn]["lang"] == "cxx" and "->" in text:
        lt = lifted_skeleton(f, fn, text, reg)
        if lt:
            return lt
    first = None
    for o1, t1 in apply_all(text):
        s1 = score(f, fn, t1)
        if not s1:
            continue
        if first is None and not s1["exact"]:
            first = t1
        for o2, t2 in apply_all(t1):
            s2 = score(f, fn, t2)
            if s2 and not s2["exact"] and t2 != text:
                return t2
    return first


def mutant_for(f, fn, text):
    for pat, rep in MUT:
        for m in re.finditer(pat, text):
            t = text[:m.start()] + re.sub(pat, rep, m.group(0), count=1) + text[m.end():]
            s = score(f, fn, t)
            if s and not s["exact"]:
                return t
    return None


def build(root):
    f = Factory(os.path.join(root, "fixtures/synthetic/recon.toml"))
    P = f.project
    out = {"skeleton": {}, "mutants": {}}
    reg = om_registry(f)
    for fn in sorted(P.functions):
        kind = "heldout" if P.functions[fn].get("heldout") else "ref"
        text = f.read_source(fn, kind if kind == "heldout" else "ref")
        src = P.functions[fn]["source"]
        s = skeleton_for(f, fn, text, reg)
        if s:
            out["skeleton"][src] = s
        m = mutant_for(f, fn, text)
        if m:
            out["mutants"][src] = m
    seal = {"schema": 1, "manifest_sha256": hashlib.sha256(open(P.path, "rb").read()).hexdigest(),
            "functions": {fn: hashlib.sha256(open(P.source_path(fn), "rb").read()).hexdigest() for fn in P.names(heldout=True)}}
    f.close()
    return P, out, seal


def main(argv=None):
    P, out, seal = build(ROOT)
    for kind, key in (("skeleton", "skeleton"), ("mutant", "mutants")):
        d = P.source_dir(kind)
        os.makedirs(d, exist_ok=True)
        for src, t in out[key].items():
            with open(os.path.join(d, src), "w", newline="\n") as fh:
                fh.write(t)
    with open(P.p(P.doc["corpus"]["heldout_seal"]), "w", newline="\n") as fh:
        json.dump(seal, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("skeletons %d mutants %d sealed %d" % (len(out["skeleton"]), len(out["mutants"]), len(seal["functions"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
