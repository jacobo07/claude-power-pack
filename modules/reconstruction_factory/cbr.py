"""CBR: Reconstruction Birth + Construction Return. Birth: a new project starts from what the engine already knows, with exactly ONE disposition per DISCOVERED input
(the inputs are found by scanning the package and the target manifest - never from a hand-kept list, so an input nobody remembered still gets a row, UNKNOWN at worst).
Return: what the new project taught the engine, handed back as typed items that each carry evidence.
Dispositions: INHERITED (works as-is, proven by a gate), ADAPTED (works after a named change), ALREADY_SATISFIED (the target already has it), NOT_APPLICABLE (the target
lacks the precondition), CONFLICT (the target contradicts an assumption), UNKNOWN (no rule or no proving gate - never a silent drop)."""
import glob
import hashlib
import json
import os

DISPOSITIONS = ("INHERITED", "ADAPTED", "ALREADY_SATISFIED", "NOT_APPLICABLE", "CONFLICT", "UNKNOWN")
RETURN_KINDS = ("NEW_CAPABILITY", "NEGATIVE_KNOWLEDGE", "FAILED_TRANSFER", "NEW_ORACLE", "OBSOLETE_CAPABILITY")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG = os.path.join(ROOT, "modules", "reconstruction_factory")
SUITE = os.path.join(ROOT, "tools", "test_reconstruction_factory.py")
HOME_ADAPTER = "gcc-ppc"            # the adapter the engine's gates were proven under

# module -> (needs, proving gate). needs: None | "cxx" | "heldout" | "variants" | "ppc"
MODULE_RULES = {
    "judge": (None, "V-RF-JUDGE"), "certify": (None, "V-RF-CERT-POSITIVE"), "fingerprint": (None, "V-RF-FINGERPRINT"), "causal_diff": (None, "V-RF-CAUSAL-DIFF"),
    "residual": (None, "V-RF-RESIDUAL"), "search": (None, "V-RF-SEARCH"), "search_plan": (None, "V-RF-PLAN"), "permute": (None, "V-RF-PERMUTE"),
    "operators": (None, "V-RF-SEARCH"), "build_twin": ("variants", "V-RF-BUILD-TWIN"), "om": ("cxx", "V-RF-OM-REGISTRY"), "om_skeleton": ("cxx", "V-RF-OM-DECLS"),
    "nsm": (None, "V-RF-NSM"), "method_graph": (None, "V-RF-METHOD-GRAPH"), "genome": (None, "V-RF-GENOME"), "atoms": (None, "V-RF-ATOMS"), "claims": (None, "V-RF-CLAIMS"),
    "invalidation": (None, "V-RF-INVALIDATION"), "heldout": ("heldout", "V-RF-HELDOUT-RELEASE"), "provenance": ("cxx", "V-RF-PROVENANCE"), "frontier": (None, "V-RF-FRONTIER"),
    "maturity": (None, "V-RF-MATURITY"), "cbr": (None, "V-RF-CBR"),
}
PLUMBING = {"__init__", "core", "elf", "manifest", "toolchain", "gatekit"}      # exercised by every gate; one row each, INHERITED


def discover(project):
    """-> sorted [(kind, id)]: every module in the package, plus the target's adapter, languages, recipes, variants, held-out presence."""
    ins = [("module", os.path.basename(f)[:-3]) for f in glob.glob(os.path.join(PKG, "*.py"))]
    d = project.doc
    ins.append(("adapter", d["toolchain"]["adapter"]))
    ins += [("lang", l) for l in sorted({f["lang"] for f in project.functions.values()})]
    ins += [("recipe", r) for r in sorted(d["toolchain"].get("recipe", {}))]
    ins += [("variant", v) for v in sorted(d["toolchain"].get("variant", {}))]
    if project.names(heldout=True):
        ins.append(("heldout", "sealed"))
    return sorted(set(ins))


def profile(project):
    d = project.doc
    return {"adapter": d["toolchain"]["adapter"], "cxx": any(f["lang"] == "cxx" for f in project.functions.values()),
            "heldout": bool(project.names(heldout=True)), "variants": bool(d["toolchain"].get("variant")),
            "sealed": bool(d["corpus"].get("heldout_seal"))}


def _gate_exists(gate):
    try:
        with open(SUITE, encoding="utf-8") as fh:
            return '@kit.gate("%s"' % gate in fh.read()
    except OSError:
        return False


def _decide(kind, ident, prof, satisfied=()):
    if "%s:%s" % (kind, ident) in satisfied:
        return "ALREADY_SATISFIED", "the target already provides it", ["target:%s:%s" % (kind, ident)]
    if kind == "module":
        if ident in PLUMBING:
            return "INHERITED", "plumbing exercised by every gate", ["modules/reconstruction_factory/%s.py" % ident]
        rule = MODULE_RULES.get(ident)
        if rule is None:
            return "UNKNOWN", "module has no transfer rule", []
        need, gate = rule
        ev = ["modules/reconstruction_factory/%s.py" % ident, gate]
        if need and not prof.get({"ppc": "adapter"}.get(need, need)):
            return "NOT_APPLICABLE", "target lacks precondition %r" % need, ev
        if not _gate_exists(gate):
            return "UNKNOWN", "proving gate %s is not in the suite" % gate, ev
        if need == "heldout" and not prof["sealed"]:
            return "CONFLICT", "target declares held-out functions but no seal", ev
        if prof["adapter"] != HOME_ADAPTER and ident in ("judge", "certify", "om", "om_skeleton", "provenance", "fingerprint", "causal_diff"):
            return "ADAPTED", "byte/disassembly rules proven under %s; target uses %s" % (HOME_ADAPTER, prof["adapter"]), ev
        return "INHERITED", "proven by %s" % gate, ev
    if kind == "adapter":
        if ident == HOME_ADAPTER:
            return "INHERITED", "home adapter", ["modules/reconstruction_factory/toolchain.py"]
        return "UNKNOWN", "adapter %s has never been exercised by a gate" % ident, []
    if kind == "heldout":
        return ("INHERITED", "sealed set present with a seal", ["fixtures/..seal"]) if prof["sealed"] else ("CONFLICT", "held-out without a seal", [])
    if kind == "lang":
        return ("INHERITED", "language covered by corpus controls", ["V-RF-CERT-POSITIVE"]) if ident in ("c", "cxx") else ("UNKNOWN", "language %s has no controls" % ident, [])
    return "INHERITED", "manifest-declared %s is read generically" % kind, ["manifest.py"]


def decide(project, satisfied=()):
    """satisfied: inputs ("kind:id") the target already provides, found by the caller from the target itself."""
    prof = profile(project)
    rows = []
    for kind, ident in discover(project):
        disp, reason, ev = _decide(kind, ident, prof, satisfied)
        rows.append({"input": "%s:%s" % (kind, ident), "disposition": disp, "reason": reason, "evidence": ev})
    return rows


def check_rows(rows, project):
    """-> problems. Exactly one row per discovered input; every disposition is in the closed set; INHERITED/ADAPTED carry evidence; no input is dropped."""
    want = ["%s:%s" % x for x in discover(project)]
    bad = []
    got = [r["input"] for r in rows]
    for i in sorted(set(want) - set(got)):
        bad.append("MISSING:" + i)
    for i in sorted(set(got) - set(want)):
        bad.append("INVENTED:" + i)
    for i in sorted({g for g in got if got.count(g) > 1}):
        bad.append("DUPLICATE:" + i)
    for r in rows:
        if r["disposition"] not in DISPOSITIONS:
            bad.append("BAD_DISPOSITION:" + r["input"])
        if r["disposition"] in ("INHERITED", "ADAPTED") and not r["evidence"]:
            bad.append("NO_EVIDENCE:" + r["input"])
    return bad


def birth(project, satisfied=()):
    rows = decide(project, satisfied)
    bad = check_rows(rows, project)
    if bad:
        raise ValueError("birth refused: " + ",".join(bad))
    counts = {d: sum(1 for r in rows if r["disposition"] == d) for d in DISPOSITIONS}
    return {"rows": rows, "counts": counts, "digest": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()}


def construction_return(items, birth_rows):
    """items: [{kind, subject, evidence:[...], birth_input?}]. A return item with no evidence is refused; FAILED_TRANSFER must point at a birth row that was
    CONFLICT or UNKNOWN (a transfer that was never attempted cannot have failed). -> normalized, digest-stamped record."""
    by = {r["input"]: r for r in birth_rows}
    out = []
    for it in items:
        if it.get("kind") not in RETURN_KINDS:
            raise ValueError("unknown return kind %r" % it.get("kind"))
        if not it.get("evidence"):
            raise ValueError("return item %r has no evidence" % it.get("subject"))
        if it["kind"] == "FAILED_TRANSFER":
            row = by.get(it.get("birth_input"))
            if row is None or row["disposition"] not in ("CONFLICT", "UNKNOWN"):
                raise ValueError("FAILED_TRANSFER must reference a CONFLICT/UNKNOWN birth row, got %r" % it.get("birth_input"))
        out.append({k: it[k] for k in sorted(it)})
    out.sort(key=lambda x: json.dumps(x, sort_keys=True))
    return {"items": out, "digest": hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()}
