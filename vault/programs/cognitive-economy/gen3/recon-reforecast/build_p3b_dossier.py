"""Zero-model dossier for the P3b-1 lease (recon-factory Phase 3b: capital promotion of the 289 MATCH donors).

Run: python vault/programs/cognitive-economy/gen3/recon-reforecast/build_p3b_dossier.py
Writes P3B-DOSSIER.md next to this file. P3b-1 builds a donor capsule, a LOCAL src_bundle assembler, the registry
write, bundle-driven promote() and a revalidate-impact report, so the dossier carries the exact source of every
function it calls, extracted by AST (never paraphrased), plus the real shape of a returned GEX44 receipt. Anything the
extractor cannot find is written UNKNOWN and the builder exits 1.
"""
import ast
import hashlib
import json
import os
import re
import sys

WT = r"C:\Users\User\Apps\recon_work\wt_keosdtk_home"
DECOMP = os.path.join(WT, "tools", "wros", "binary", "decomp")
GEX = os.path.join(DECOMP, "gex44")
REGISTRY = r"C:\Users\User\Apps\recon_work\decomp_factory\levels\evidence\src_registry.json"
SRC_BUNDLES = r"C:\Users\User\Apps\recon_work\decomp_factory\levels\evidence\src_bundles"
LEVELS = r"C:\Users\User\Apps\recon_work\decomp_factory\levels\levels.jsonl"
DONORS = r"C:\Users\User\Apps\recon_work\match_accel_factory\donors\DONORS.jsonl"
AA_JOB = r"C:\Users\User\Apps\recon_work\recon_factory\gex44\returns\ksrmb-20261009-090602"
AA_RESULT = os.path.join(WT, ".planning", "workstreams", "recon-factory", "phases", "02-oracle-parity-s1",
                         "02-AA-RESULT.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "P3B-DOSSIER.md")

# (file, names). "Cls.meth" extracts one method; a bare class name extracts the whole class.
WANT = [
    (os.path.join(GEX, "stage.py"),
     ["RF_PHASE_JOB_CAPS", "RF_CURRENT_PHASE", "REPRODUCE_BUDGET_S", "PAYLOAD_CEILING_BYTES", "resolve_capsule", "build",
      "main"]),
    (os.path.join(DECOMP, "levels.py"),
     ["PINNED_COMPILER_SHA256", "canonical", "SRC_BUNDLE_KEYS", "verify_src_bundle", "_src_unbacked", "src_intake", "check_src", "promote", "seed_src",
      "inputs_for", "current_fingerprints", "revalidate", "load_store", "_cmd_promote", "_cmd_seed_src",
      "Store.__init__", "Store._load_src_registry", "Store.src_bundle", "Store.src_entry", "Store.src_text",
      "Store.words"]),
    (os.path.join(DECOMP, "oracle_parity.py"), ["verdict_class", "Judge", "aa_returned", "aa_gate_verdict"]),
    (os.path.join(GEX, "reproduce.py"),
     ["DONOR_TARGET", "LOCAL_LEDGER", "LOCAL_OBJ_DIR", "is_aa_capsule", "build_units", "select_units", "judge_tree",
      "load_job"]),
    (os.path.join(GEX, "capsule_build.py"), ["SCHEMAS", "default_inputs", "resolve_units", "build", "build_aa"]),
    (os.path.join(GEX, "custody.py"),
     ["CAPSULE_CEILING_BYTES", "current_capsule", "validate_capsule_manifest", "build_manifest", "verify_manifest", "judge_receipt"]),
    (os.path.join(DECOMP, "ledger.py"), ["REQUIRED", "decomp_registered", "export", "append"]),
]
# SRC_BUNDLE_KEYS is a tuple in the source; every other name above is a def, class or constant.


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def extract(path, names):
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    got = {}

    def span(node):
        return node.lineno, lines[node.lineno - 1:node.end_lineno]

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            got[node.name] = span(node)
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                key = node.name + "." + getattr(m, "name", "")
                if isinstance(m, ast.FunctionDef) and key in names:
                    got[key] = span(m)
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if getattr(t, "id", None) in names:
                    got[t.id] = span(node)
    return got, [n for n in names if n not in got]


def receipt_shape(job_dir):
    """Key paths of the real returned receipt and one unit; values only for identity fields."""
    rp = os.path.join(job_dir, "run", "receipt.json")
    if not os.path.isfile(rp):
        return ["- receipt: UNKNOWN (no %s)" % rp]
    r = json.load(open(rp, encoding="utf-8"))
    units = (r.get("results") or {}).get("units") or []
    out = ["- path `%s` sha256 `%s`" % (rp, sha(rp)),
           "- top-level keys: %s" % sorted(r),
           "- schema %r, job_id %r, mode %r, verdict %r, reason_code %r" % (
               r.get("schema"), r.get("job_id"), r.get("mode"), r.get("verdict"), r.get("reason_code")),
           "- host: %s" % json.dumps(r.get("host")),
           "- started_at %r ended_at %r" % (r.get("started_at"), r.get("ended_at")),
           "- measured keys: %s" % sorted(r.get("measured") or {}),
           "- measured.runner: %s" % json.dumps((r.get("measured") or {}).get("runner")),
           "- custody keys: %s" % sorted(r.get("custody") or {}),
           "- capsule: %s" % json.dumps(r.get("capsule"))[:400],
           "- results keys: %s; units %d" % (sorted(r.get("results") or {}), len(units))]
    if units:
        u = units[0]
        out.append("- units[0] keys: %s" % sorted(u))
        out.append("- units[0] (verbatim, first 1200 chars): `%s`" % json.dumps(u)[:1200])
    for name in ("produced_utc", "host_plane", "runner_lib_sha256"):
        out.append("- receipt field `%s`: %s" % (name, "present" if name in r else "ABSENT at top level"))
    return out


def main():
    missing = {}
    sections = []
    inputs = []
    for path, names in WANT:
        if not os.path.isfile(path):
            missing[path] = names
            continue
        inputs.append(path)
        got, miss = extract(path, names)
        if miss:
            missing[path] = miss
        for n in names:
            if n in got:
                ln, body = got[n]
                sections += ["", "### %s :: %s (line %d)" % (os.path.basename(path), n, ln), "```python"] + body + ["```"]

    reg = json.load(open(REGISTRY, encoding="utf-8"))
    lv = {r["id"]: r for r in jsonl(LEVELS)}
    proven = sorted(i for i, r in lv.items() if r["dimensions"]["SRC"]["verdict"] == "PROVEN")
    donors = jsonl(DONORS)
    match = [d for d in donors if d.get("best") == "MATCH"]
    bundles = sorted(os.listdir(SRC_BUNDLES)) if os.path.isdir(SRC_BUNDLES) else None
    stage = os.path.join(GEX, "stage.py")
    phase = "UNKNOWN"
    if os.path.isfile(stage):
        m = re.search(r"^RF_CURRENT_PHASE\s*=\s*(.+)$", open(stage, encoding="utf-8").read(), re.M)
        phase = m.group(1).strip() if m else "UNKNOWN (no RF_CURRENT_PHASE line in stage.py)"

    intake = "UNKNOWN"
    try:
        sys.path.insert(0, DECOMP)
        import levels  # noqa: E402  (src_intake is a dry run: it writes nothing)
        rep = levels.src_intake()
        intake = json.dumps({k: v for k, v in rep.items() if not isinstance(v, list)})[:800]
    except Exception as e:  # recorded, never swallowed: the dossier says why the oracle is missing
        intake = "UNKNOWN (src_intake raised %s: %s)" % (type(e).__name__, e)

    aa = "UNKNOWN (no %s)" % AA_RESULT
    if os.path.isfile(AA_RESULT):
        a = json.load(open(AA_RESULT, encoding="utf-8"))
        aa = "sha256 `%s`; keys %s" % (sha(AA_RESULT), sorted(a) if isinstance(a, dict) else type(a).__name__)

    out = ["# P3b dossier (zero-model, generated by build_p3b_dossier.py)", "",
           "Everything below is copied or computed from a named source. Read this file only. UNKNOWN = not found;"
           " a worker that needs an UNKNOWN stops and reports, never guesses.", "", "## Inputs (sha256)"]
    for p in inputs + [REGISTRY, LEVELS, DONORS]:
        out.append("- `%s` sha256 `%s`" % (p, sha(p)))

    out += ["", "## Facts that shape 3b",
            "- levels.jsonl: %d rows, SRC PROVEN %d: %s." % (len(lv), len(proven), proven),
            "- src_registry.json schema %r, %d rows: %s." % (reg.get("schema"), len(reg["rows"]),
                                                            sorted(r["id"] for r in reg["rows"])),
            "- src_bundles dir: %s." % ("ABSENT" if bundles is None else "%d files %s" % (len(bundles), bundles[:10])),
            "- DONORS.jsonl: %d rows, best=MATCH %d." % (len(donors), len(match)),
            "- stage.py RF_CURRENT_PHASE = %s (RESUMPTION: set to 3 only at the first 3b send)." % phase,
            "- src_intake() dry run, live (scalar fields): %s" % intake,
            "- Admissible A/A return (P2b job 3, judge runner_lib 7377ff0f): `%s`." % AA_JOB,
            "- 02-AA-RESULT.json: %s" % aa,
            "- Standing decision (P3B-RESUMPTION): assemble `ksr.decomp.src_bundle/1` LOCALLY from the returned object,"
            " the receipt, the local split-judge verdict (oracle_parity) and the receipt objdiff pct. runner_lib.py is"
            " NOT edited (a new revision voids the C5 judge identity). A bundle field with no local source is written"
            " UNKNOWN and the worker stops.",
            "", "## Real returned receipt shape (ksr.match_receipt/1, job ksrmb-20261009-090602)"]
    out += receipt_shape(AA_JOB)

    out += ["", "## Source the 3b worker calls (verbatim, AST-extracted; line numbers as of the sha above)"] + sections
    out += ["", "## UNKNOWN (not found by the extractor)"]
    out += ["- `%s`: %s" % (p, n) for p, n in missing.items()] or ["- none"]

    body = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    n_missing = sum(len(v) for v in missing.values())
    print("P3B-DOSSIER chars=%d est_tokens=%d proven=%d registry=%d match_donors=%d bundles=%s phase=%s missing=%d"
          % (len(body), len(body) // 4, len(proven), len(reg["rows"]), len(match),
             "ABSENT" if bundles is None else len(bundles), phase, n_missing))
    return 0 if not n_missing else 1


if __name__ == "__main__":
    sys.exit(main())
