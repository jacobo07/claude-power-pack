"""Zero-model dossier for the C1 lease (CP50 run plan: build decomp/bench.py + per-cohort packet + drill; nothing sent).

Run: python vault/programs/cognitive-economy/gen3/recon-reforecast/build_c1_dossier.py
Writes C1-DOSSIER.md next to this file: the verbatim source (AST-extracted, with line numbers) of the arm-A pipeline of
decomp Phase 5 (baseline.py / transaction.py / match.py / m2c_producer.py / g0_freeze.py), the capsule_build / custody /
repatriate APIs bench.py must build capsules through (GAP-3), the G0_FREEZE.json schema (keys only, plus the coherence
anchor recomputed live), ROADMAP Phase 7, REFORECAST section 3, the 05-04 arm-A design and the P7G0 G0 policy text.
Any piece the extractor cannot find is printed as UNKNOWN.
"""
import ast
import hashlib
import json
import os
import sys

WT = r"C:\Users\User\Apps\recon_work\wt_keosdtk_home"
DEC = os.path.join(WT, "tools", "wros", "binary", "decomp")
G = os.path.join(DEC, "gex44")
RF = os.path.join(WT, ".planning", "workstreams", "recon-factory")
G0_DIR = os.path.join(RF, "phases", "07-g0-freeze")
P504 = os.path.join(WT, ".planning", "workstreams", "decomp", "phases", "05-matching-transaction-free-baseline",
                    "05-04-PLAN.md")
DF = r"C:\Users\User\Apps\recon_work\decomp_factory"
VAULT_DF = os.path.join(WT, ".ksr_vault", "reconstruction", "decomp_factory")
HERE = os.path.dirname(os.path.abspath(__file__))
P7G0 = os.path.join(HERE, "P7G0-DOSSIER.md")
REFORECAST = os.path.join(HERE, "REFORECAST.md")
OUT = os.path.join(HERE, "C1-DOSSIER.md")
ANCHOR_DRAW, ANCHOR_HOLD = "0f2ecb37", "7bf4c5f5"

# file -> (full-body names, signature-only names). "<consts>" = every top-level assignment before the first def.
# A signature-only name may also be a top-level constant; its assignment line is printed.
SPEC = {
    os.path.join(DEC, "baseline.py"): (["<consts>", "cut_points", "stratum_of", "allocate", "population", "draw",
                                         "check_draw_frozen", "main"], ["prelude", "arms_block", "load_inputs",
                                                                       "validate_draw", "reproduce"]),
    os.path.join(DEC, "transaction.py"): (["<consts>", "failure_class", "agreement", "unit_map", "_check_cost", "Writer",
                                            "start_run", "not_run", "no_candidate", "attempt", "tally",
                                            "require_complete"], ["verify_chain", "repair_tail", "main"]),
    os.path.join(DEC, "match.py"): (["compile_obj", "verdict_of", "run", "target_of"], ["elf", "judge", "main"]),
    os.path.join(DEC, "m2c_producer.py"): ([], ["admit", "main"]),
    os.path.join(DEC, "g0_freeze.py"): (["<consts>", "freeze"], ["*"]),
    os.path.join(G, "capsule_build.py"): (["default_inputs", "build"], ["resolve_units", "resolve_targets",
                                                                        "_stage_and_seal", "verify_current", "build_aa",
                                                                        "main"]),
    os.path.join(G, "custody.py"): ([], ["*"]),
    os.path.join(G, "repatriate.py"): ([], ["*"]),
}
# Named by 05-04-PLAN Task 1 as the arm-A runner; 05-04 never ran, so these are expected ABSENT. Probed, never assumed.
PLANNED_ARM_A = ["PRESET_ORDER", "VERDICT_RANK", "best_of", "wilson", "build_candidates", "resolve_targets",
                 "run_slice", "summarise", "check_cells"]


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_lines(p):
    with open(p, encoding="utf-8") as f:
        return f.read().splitlines()


def top_names(tree):
    defs, consts = {}, {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            defs[n.name] = n
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = n
    return defs, consts


def extract(path, full, sigs):
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    defs, consts = top_names(tree)
    out, missing = [], []
    first_def = next((n.lineno for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))), len(lines))
    for name in full:
        if name == "<consts>":
            body = [ln for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.lineno < first_def
                    for ln in lines[n.lineno - 1:n.end_lineno]]
            out += ["", "#### constants (top-level assignments before the first def)", "```python"] + body + ["```"]
        elif name in defs:
            n = defs[name]
            out += ["", "#### %s (line %d)" % (name, n.lineno), "```python"] + lines[n.lineno - 1:n.end_lineno] + ["```"]
        else:
            out.append("- `%s`: UNKNOWN (not a top-level def/class in this file)" % name)
            missing.append(name)
    wanted = sorted(defs, key=lambda k: defs[k].lineno) if "*" in sigs else sigs
    for name in wanted:
        if name in full:
            continue
        if name in defs:
            n = defs[name]
            doc = ast.get_docstring(n) or ""
            out.append("- `%s` (line %d) -- %s" % (lines[n.lineno - 1].strip(), n.lineno,
                                                    doc.splitlines()[0] if doc else "no docstring"))
        elif name in consts:
            n = consts[name]
            out.append("- constant (line %d): `%s`" % (n.lineno, " ".join(l.strip() for l in lines[n.lineno - 1:n.end_lineno])))
        else:
            out.append("- `%s`: UNKNOWN (not found)" % name)
            missing.append(name)
    return out, missing


def key_schema(obj, prefix="", depth=0, out=None):
    """Keys and types only, never values. Lists show their length and the schema of their first element."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k in obj:
            v = obj[k]
            kind = type(v).__name__ + ("[%d]" % len(v) if isinstance(v, (list, dict)) else "")
            out.append("%s- `%s%s`: %s" % ("  " * depth, prefix, k, kind))
            if isinstance(v, dict) and depth < 3:
                key_schema(v, "", depth + 1, out)
            elif isinstance(v, list) and v and isinstance(v[0], dict) and depth < 3:
                out.append("%s  (element 0 keys)" % ("  " * depth))
                key_schema(v[0], "", depth + 1, out)
    return out


def id_lists(obj, path="$"):
    """Every list of census ids (rows carrying census_id, or bare id strings), with its JSON path (anchor recompute)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from id_lists(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        if obj and all(isinstance(e, dict) and "census_id" in e for e in obj):
            yield path, [e["census_id"] for e in obj]
        elif obj and all(isinstance(e, str) and ":" in e for e in obj):   # G0_HOLDOUT stores bare census ids
            yield path, obj
        else:
            for i, e in enumerate(obj[:1]):
                yield from id_lists(e, "%s[%d]" % (path, i))


def ids_sha(ids):
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def section(lines, start_pred, stop_pred):
    i = next((n for n, ln in enumerate(lines) if start_pred(ln)), None)
    if i is None:
        return None
    j = next((n for n in range(i + 1, len(lines)) if stop_pred(lines[n])), len(lines))
    return lines[i:j]


def listing(p):
    if not os.path.isdir(p):
        return "ABSENT (no such directory)"
    names = sorted(os.listdir(p))
    return "%d entries%s" % (len(names), (": " + ", ".join(names[:10])) if names else " (empty)")


def main():
    unknown = []
    freeze_p, hold_p = os.path.join(G0_DIR, "G0_FREEZE.json"), os.path.join(G0_DIR, "G0_HOLDOUT.json")
    roadmap_p = os.path.join(RF, "ROADMAP.md")
    body = ["# C1 dossier (zero-model, generated by build_c1_dossier.py)", "",
            "Everything below is copied or computed from a named source. Read this file only. UNKNOWN = not found on"
            " disk by the extractor; never fill it in by guessing.", "", "## Inputs (sha256)"]
    for p in list(SPEC) + [freeze_p, hold_p, roadmap_p, P504, P7G0, REFORECAST]:
        body.append("- `%s` sha256 `%s`" % (p, sha(p)) if os.path.isfile(p) else "- `%s` UNKNOWN (missing)" % p)
        if not os.path.isfile(p):
            unknown.append(p)

    # Measured facts (live, this run).
    bench = os.path.join(DEC, "bench.py")
    btx = os.path.join(VAULT_DF, "BASELINE_TRANSACTIONS.jsonl")
    bdraw = os.path.join(VAULT_DF, "BASELINE_DRAW.json")
    body += ["", "## Measured facts (this run)",
             "- `%s` exists: %s (C1 creates it)." % (bench, os.path.isfile(bench)),
             "- `%s\\baseline`: %s (arm A has never run)." % (DF, listing(os.path.join(DF, "baseline"))),
             "- `%s` exists: %s (05-04 precondition: no rows yet)." % (btx, os.path.isfile(btx))]
    if os.path.isfile(bdraw):
        bd = json.load(open(bdraw, encoding="utf-8"))
        body.append("- frozen n=165 baseline draw `%s`: schema %s, n=%d, arms %s." % (
            bdraw, bd.get("schema"), len(bd.get("ids", [])), bd.get("arms", "UNKNOWN") if not isinstance(
                bd.get("arms"), (list, dict)) else [a.get("name", a) if isinstance(a, dict) else a for a in bd["arms"]]))
    else:
        body.append("- frozen n=165 baseline draw: UNKNOWN (missing %s)" % bdraw)
        unknown.append(bdraw)

    # G0_FREEZE schema + coherence anchor.
    body += ["", "## G0_FREEZE.json schema (keys and types only, no values)"]
    if os.path.isfile(freeze_p):
        fz = json.load(open(freeze_p, encoding="utf-8"))
        body += key_schema(fz)
        body += ["", "### Coherence anchor (recomputed: sha256 of the newline-joined sorted census_ids)"]
        found = list(id_lists(fz))
        for path, rows in found:
            s = ids_sha(rows)
            body.append("- `%s` n=%d sorted-id sha256 %s -- anchor %s %s" % (
                path, len(rows), s, ANCHOR_DRAW, "MATCH" if s.startswith(ANCHOR_DRAW) else "no match"))
        if not found:
            body.append("- UNKNOWN: no list of census_id rows found in G0_FREEZE.json")
            unknown.append("G0_FREEZE census_id list")
    if os.path.isfile(hold_p):
        hd = json.load(open(hold_p, encoding="utf-8"))
        for path, rows in id_lists(hd):
            s = ids_sha(rows)
            body.append("- holdout `%s` n=%d sorted-id sha256 %s -- anchor %s %s (bench.py must NEVER read this file"
                        " before checkpoint 300)" % (path, len(rows), s, ANCHOR_HOLD,
                                                     "MATCH" if s.startswith(ANCHOR_HOLD) else "no match"))

    # ROADMAP Phase 7 verbatim.
    rm = section(read_lines(roadmap_p), lambda l: l.startswith("### Phase 7:"),
                 lambda l: l.startswith("### Phase ") or l.startswith("## ")) if os.path.isfile(roadmap_p) else None
    body += ["", "## ROADMAP Phase 7 (verbatim)"] + (rm or ["UNKNOWN (no '### Phase 7:' heading)"])
    if rm is None:
        unknown.append("ROADMAP Phase 7")

    # REFORECAST section 3 verbatim (CP50 amendments a-d).
    rf = section(read_lines(REFORECAST), lambda l: l.startswith("## 3."), lambda l: l.startswith("## ")) \
        if os.path.isfile(REFORECAST) else None
    body += ["", "## REFORECAST section 3 (verbatim; amendment (d) = the per-function record fields)"] + (rf or ["UNKNOWN"])
    if rf is None:
        unknown.append("REFORECAST section 3")

    # P7G0 policy text verbatim.
    pg = section(read_lines(P7G0), lambda l: l.startswith("## G0 policy v1"), lambda l: l.startswith("## ")) \
        if os.path.isfile(P7G0) else None
    body += ["", "## P7G0-DOSSIER G0 policy v1 (verbatim; item 7 is the preregistration)"] + (pg or ["UNKNOWN"])
    if pg is None:
        unknown.append("P7G0 G0 policy v1")

    # 05-04 arm-A design (the runner that was planned, never built).
    p4 = section(read_lines(P504), lambda l: l.lstrip().startswith("<action>"), lambda l: l.lstrip().startswith("</action>")) \
        if os.path.isfile(P504) else None
    body += ["", "## decomp 05-04-PLAN Task 1 action (verbatim; the arm-A runner design, NEVER executed)"] + (p4 or ["UNKNOWN"])
    if p4 is None:
        unknown.append("05-04 Task 1 action")

    # Planned arm-A runner names: probe baseline.py for each.
    src = open(os.path.join(DEC, "baseline.py"), encoding="utf-8").read()
    defs, consts = top_names(ast.parse(src))
    body += ["", "## Planned arm-A runner names in baseline.py (05-04 Task 1) -- probed"]
    for name in PLANNED_ARM_A:
        n = defs.get(name) or consts.get(name)
        body.append("- `%s`: %s" % (name, "present (line %d)" % n.lineno if n else "UNKNOWN (absent on disk)"))

    # Verbatim extracts.
    missing_all = []
    for path, (full, sigs) in SPEC.items():
        if not os.path.isfile(path):
            body += ["", "## %s: UNKNOWN (file missing)" % os.path.relpath(path, WT)]
            missing_all.append(os.path.basename(path))
            continue
        part, missing = extract(path, full, sigs)
        missing_all += ["%s:%s" % (os.path.basename(path), m) for m in missing]
        body += ["", "## %s (verbatim extracts)" % os.path.relpath(path, WT)] + part
    body += ["", "Not found by the extractor (UNKNOWN): %s" % ((missing_all + unknown) or "none")]

    text = "\n".join(body) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    absent = [n for n in PLANNED_ARM_A if n not in defs and n not in consts]
    print("C1-DOSSIER chars=%d est_tokens=%d unknown=%s planned_arm_a_absent=%d/%d"
          % (len(text), len(text) // 4, missing_all + unknown, len(absent), len(PLANNED_ARM_A)))
    return 0 if not (missing_all or unknown) else 1


if __name__ == "__main__":
    sys.exit(main())
