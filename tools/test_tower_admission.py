"""V-ADM-* -- admission to a constitutive baseline is a checked property of the chain.

ROADMAP Phase 3 (UCEP-03): an entry enters a baseline generation only with an
admission record judged against evidence, and the chain re-checks that record.
Without it, admission is a convention: `promote` wrote whatever it was handed and a
raw `write_generation` added entries nothing had judged (audit G5). The scope an
entry claims is derived, not declared (audit G6), and an origin that will rot (a
worktree path, a rules pointer file) is refused (audit G15).

Every refusal gate carries a control in which the missing fact exists and the entry
is admitted, so a gate that refused everything could not read as green.

Hermetic: HOME, USERPROFILE and CLAUDE_STATE_DIR point at a temp dir before any
module under `modules/` is imported, every generation is written under a temp root,
and nothing under `vault/tower/baselines` is written. The gate list grows across
plans 03-01..03-04; EXPECTED is a literal enforced by the exit code.

Run: python tools/test_tower_admission.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

_HOME = tempfile.mkdtemp(prefix="tadm-home-")
_SAVED_ENV = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE", "CLAUDE_STATE_DIR")}
os.environ["HOME"] = _HOME
os.environ["USERPROFILE"] = _HOME
os.environ["CLAUDE_STATE_DIR"] = os.path.join(_HOME, ".claude", "state")

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for _p in (_PP_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import ratchet as rt  # noqa: E402

try:
    from modules.tower import admission as adm  # noqa: E402
    _ADM_ERR = None
except Exception as exc:  # noqa: BLE001 -- RED must fail on predicates, never crash
    adm = None
    _ADM_ERR = "%s: %s" % (type(exc).__name__, exc)

_PASS = 0
_FAIL = 0
TMP = tempfile.mkdtemp(prefix="tadm-")
ARCH = "archetype/WORLD_MUTATION"
AUTH = "Owner (V-ADM fixture)"

# Copied verbatim from 03-F0-REFERENCE.md (orchestrator measurement at d61b5c23).
F0 = {
    ("kobiicraft_mode", 0): "1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407",
    ("persistent_state", 0): "bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64",
    ("persistent_state", 1): "0586c6a27eba0fdd3a7793c8e8ed32bd5ab9104cb09085faba7b456af8f315f2",
    ("web_surface", 0): "98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7",
    ("web_surface", 1): "2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1",
    ("wii_homebrew", 0): "2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd",
    ("wii_homebrew", 1): "f255befaed5f66238361f74f47c71523802fab90a05119dfc9198355ac43451a",
}


def check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-44s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-44s %s" % (gate, diagnostic))


def run_gate(name, pred):
    try:
        ok, text = pred()
    except Exception as exc:  # noqa: BLE001 -- a crashing predicate is a FAIL, never a skip
        ok, text = False, "%s: %s" % (type(exc).__name__, exc)
    check(name, ok, text, text)


def attempt(fn):
    """(refusal message or None, other exception text or None, value)."""
    try:
        return None, None, fn()
    except rt.RatchetRefusal as exc:
        return str(exc), None, None
    except Exception as exc:  # noqa: BLE001
        return None, "%s: %s" % (type(exc).__name__, exc), None


def listing(path):
    if not os.path.isdir(path):
        return []
    out = []
    for dirpath, _dirs, files in os.walk(path):
        for f in files:
            out.append(os.path.relpath(os.path.join(dirpath, f), path).replace(os.sep, "/"))
    return sorted(out)


def token(reason):
    return str(reason).split(":", 1)[0].strip()


def evidenced(ident, *, quote=None, gov_dir=None, admission_over=None, **over):
    """A fully evidenced entry: its quote is on line 3 of a governance file it cites."""
    quote = quote or ("Rule %s: every write is read back before it is reported done." % ident)
    gdir = gov_dir or os.path.join(TMP, "gov")
    os.makedirs(gdir, exist_ok=True)
    path = os.path.abspath(os.path.join(gdir, "%s.md" % ident))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# rules\nintro line\n%s\n" % quote)
    claim = {"evidence_ref": "T-UCEP-ADM-FIXTURE-001", "production_evidence_ref": "1b087de0",
             "negative_applicability": ["read-only views that never write state"],
             "counterfactual": "archetype"}
    for k, v in (admission_over or {}).items():
        if v is None:
            claim.pop(k, None)
        else:
            claim[k] = v
    entry = {"id": ident,
             "requirement": "Every write of %s is read back before it is reported done" % ident,
             "why": "a write that was not read back is not evidence", "class": "D",
             "status": "reviewed", "check": "file:README.md",
             "origin": {"file": path, "line": 3, "quote": quote}, "admission": claim}
    entry.update(over)
    return entry


def dump(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def findings(report, kind):
    return [r for r in report.regressions if r.get("kind") == kind]


# --- 03-01 Task 2 ----------------------------------------------------------------

def pred_V_ADM_HERMETIC_HOME():
    ok = Path.home() == Path(_HOME) and os.path.expanduser("~") == _HOME
    return ok, "home=%s expanduser=%s (want %s)" % (Path.home(), os.path.expanduser("~"), _HOME)


def pred_V_ADM_TRACER_ARCHETYPE():
    if adm is None:
        return False, "admission module import failed: %s" % _ADM_ERR
    root = os.path.join(TMP, "tracer")
    e = evidenced("wm-read-back")
    rt.promote(ARCH, [e], reason="tracer", authority=AUTH, root=root)
    problems = []
    if bl.generations(ARCH, root) != [0]:
        problems.append("generations=%s" % bl.generations(ARCH, root))
    doc = bl.load_generation(ARCH, 0, root)
    written = doc["entries"][0]
    claim = e["admission"]
    if "admission" in written:
        problems.append("the claim was stored in the entry")
    recs = doc.get("admissions") or {}
    if set(recs) != {"wm-read-back"}:
        problems.append("admissions keys=%s" % sorted(recs))
    rec = recs.get("wm-read-back") or {}
    want = {"schema": adm.SCHEMA, "verdict": adm.AUTO_ADMITTED,
            "status": adm.STATUS_PROVISIONAL, "origin_status": bl.VERIFIED,
            "derived_scope": bl.SCOPE_ARCHETYPE, "check": written.get("check"),
            "evidence_ref": claim["evidence_ref"],
            "production_evidence_ref": claim["production_evidence_ref"],
            "counterfactual": claim["counterfactual"],
            "negative_applicability": ["read-only views that never write state"],
            "entry_sha256": adm.entry_digest(written)}
    for k, v in want.items():
        if rec.get(k) != v:
            problems.append("record[%s]=%r want %r" % (k, rec.get(k), v))
    if not isinstance(rec.get("admitted_at"), (int, float)):
        problems.append("admitted_at=%r" % rec.get("admitted_at"))
    rep = rt.verify_chain(ARCH, root=root)
    if not rep.ok or rep.regressions:
        problems.append("chain B0: %s" % rep.as_dict())
    scope = bl.propagation_scope(written, doc, root=root)
    if scope != bl.SCOPE_ARCHETYPE:
        problems.append("propagation_scope=%s" % scope)
    rt.promote(ARCH, [evidenced("wm-second")], reason="tracer 2", authority=AUTH, root=root)
    b1 = bl.load_generation(ARCH, 1, root)
    if set(b1.get("admissions") or {}) != {"wm-second"}:
        problems.append("B1 admissions=%s (records only for new entries)"
                        % sorted(b1.get("admissions") or {}))
    rt.revert(ARCH, "wm-read-back", reason="fixture revert", authority=AUTH, root=root)
    b2 = bl.load_generation(ARCH, 2, root)
    if "admissions" in b2:
        problems.append("B2 (revert) carries admissions")
    rep2 = rt.verify_chain(ARCH, root=root)
    if not rep2.ok:
        problems.append("chain B0-B2: %s" % rep2.as_dict())
    return not problems, "; ".join(problems) or (
        "B0 written with an AUTO_ADMITTED archetype record (schema %s), chain ok, scope read "
        "back as archetype; B1 records only wm-second; B2 revert needs none, chain ok"
        % adm.SCHEMA)


def pred_V_ADM_TRACER_REFUSED_ORIGIN():
    if adm is None:
        return False, "admission module import failed: %s" % _ADM_ERR
    root = os.path.join(TMP, "refused")
    b = evidenced("wm-bad")
    bad = dict(b, origin=dict(b["origin"], quote="a sentence that is nowhere in this file"))
    before = listing(root)
    refusal, other, _v = attempt(lambda: rt.promote(ARCH, [bad], reason="bad", authority=AUTH,
                                                    root=root))
    after = listing(root)
    verdict = adm.admit(bad, ARCH)
    problems = []
    if not refusal or not all(s in refusal for s in ("wm-bad", "origin-not-verified",
                                                     "QUOTE_MISSING")):
        problems.append("refusal=%r other=%r" % (refusal, other))
    if before != [] or after != []:
        problems.append("listing before=%s after=%s" % (before, after))
    if verdict.verdict != adm.REFUSED or "origin-not-verified" not in [token(r) for r in
                                                                         verdict.reasons]:
        problems.append("admit=%s %s" % (verdict.verdict, verdict.reasons))
    # Control: the same shape with its quote in place is admitted and written.
    rt.promote(ARCH, [evidenced("wm-good")], reason="good", authority=AUTH, root=root)
    if bl.generations(ARCH, root) != [0]:
        problems.append("control generations=%s" % bl.generations(ARCH, root))
    return not problems, "; ".join(problems) or (
        "unverified quote refused with origin-not-verified/QUOTE_MISSING, nothing written; "
        "control with the quote in place written as B0")


def pred_V_ADM_TRACER_RECORD_INVALID():
    if adm is None:
        return False, "admission module import failed: %s" % _ADM_ERR
    r3 = os.path.join(TMP, "r3")
    rt.promote(ARCH, [evidenced("wm-relocate")], reason="relocate", authority=AUTH, root=r3)
    src = bl.load_generation(ARCH, 0, r3)
    problems = []

    def invalid(fam, root, want_token):
        rep = rt.verify_chain(fam, root=root)
        hits = [f for f in findings(rep, rt.ADMISSION_INVALID) if f.get("id") == "wm-relocate"
                and want_token in [token(x) for x in f.get("reasons") or []]]
        return (not rep.ok) and bool(hits), rep.as_dict()

    r4 = os.path.join(TMP, "r4")
    dump(os.path.join(r4, "fam", "B0.json"), src)
    ok, d = invalid("fam", r4, "record-scope-disagrees-with-location")
    if not ok:
        problems.append("relocated to a family: %s" % d)
    r5 = os.path.join(TMP, "r5")
    dump(os.path.join(r5, ARCH, "B0.json"), src)
    rep5 = rt.verify_chain(ARCH, root=r5)
    if not rep5.ok:
        problems.append("control (same bytes, same location) not ok: %s" % rep5.as_dict())
    r6 = os.path.join(TMP, "r6")
    edited = json.loads(json.dumps(src))
    edited["entries"][0]["requirement"] = "an edited requirement nobody admitted"
    dump(os.path.join(r6, ARCH, "B0.json"), edited)
    ok, d = invalid(ARCH, r6, "record-entry-digest-mismatch")
    if not ok:
        problems.append("edited entry: %s" % d)
    r7 = os.path.join(TMP, "r7")
    pend = json.loads(json.dumps(src))
    pend["admissions"]["wm-relocate"]["verdict"] = "PENDING_OWNER"
    dump(os.path.join(r7, ARCH, "B0.json"), pend)
    ok, d = invalid(ARCH, r7, "record-verdict-not-auto-admitted")
    if not ok:
        problems.append("pending verdict: %s" % d)
    return not problems, "; ".join(problems) or (
        "relocated -> record-scope-disagrees-with-location; edited -> "
        "record-entry-digest-mismatch; PENDING_OWNER -> record-verdict-not-auto-admitted; "
        "control (same bytes at their own location) ok")


def pred_V_ADM_LEGACY_IDENTITY():
    if not hasattr(bl, "LEGACY_GENERATIONS"):
        return False, "baselines has no LEGACY_GENERATIONS"
    problems = []
    if dict(bl.LEGACY_GENERATIONS) != F0:
        problems.append("table != F0: %s" % dict(bl.LEGACY_GENERATIONS))
    for (fam, n), sha in sorted(F0.items()):
        p = os.path.join(bl.BASELINES_DIR, fam, "B%d.json" % n)
        if not os.path.isfile(p) or bl.lf_sha256(p) != sha or not bl.is_grandfathered(fam, n):
            problems.append("real %s/B%d not grandfathered" % (fam, n))
    real = os.path.join(bl.BASELINES_DIR, "web_surface", "B0.json")
    with open(real, "rb") as fh:
        raw = fh.read()
    sha = F0[("web_surface", 0)]

    def put(root, fam, data):
        d = os.path.join(TMP, root, fam)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "B0.json")
        with open(p, "wb") as fh:
            fh.write(data)
        return os.path.join(TMP, root), p

    r, _p = put("legacy", "web_surface", raw)
    if not bl.is_grandfathered("web_surface", 0, root=r):
        problems.append("exact copy not grandfathered")
    crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    r, p = put("legacy_crlf", "web_surface", crlf)
    import hashlib
    with open(p, "rb") as fh:
        raw_sha = hashlib.sha256(fh.read()).hexdigest()
    if bl.lf_sha256(p) != sha or raw_sha == sha or not bl.is_grandfathered("web_surface", 0,
                                                                            root=r):
        problems.append("CRLF copy: lf=%s raw_differs=%s grandfathered=%s" % (
            bl.lf_sha256(p) == sha, raw_sha != sha, bl.is_grandfathered("web_surface", 0,
                                                                        root=r)))
    edit = raw[:-1] + b" " + raw[-1:]
    r, _p = put("legacy_edit", "web_surface", edit)
    if bl.is_grandfathered("web_surface", 0, root=r):
        problems.append("one-byte edit still grandfathered")
    r, _p = put("legacy_other", "other_family", raw)
    if bl.is_grandfathered("other_family", 0, root=r):
        problems.append("same bytes under another family grandfathered")
    if bl.is_grandfathered("web_surface", 2):
        problems.append("web_surface B2 grandfathered")
    try:
        bl.LEGACY_GENERATIONS[("x", 0)] = "y"
        problems.append("the table accepted an assignment")
    except TypeError:
        pass
    return not problems, "; ".join(problems) or (
        "seven pinned identities match the real files; exact and CRLF copies grandfathered "
        "(LF identity), a one-byte edit and another family are not; the table is read-only")


def pred_V_ADM_LIVENESS_DECLARED():
    with open(os.path.join(_PP_ROOT, "vault", "liveness", "reachability_registry.json"),
              encoding="utf-8") as fh:
        reg = json.load(fh)
    row = (reg.get("modules") or {}).get("tower/admission")
    if not row:
        return False, "no tower/admission row"
    note = row.get("note") or ""
    qp = note.split("Owner queue: ", 1)[1].strip() if "Owner queue: " in note else ""
    ok = row.get("class") == "PLANNED" and bool(qp) and os.path.isfile(os.path.join(_PP_ROOT, qp))
    return ok, "class=%s owner_queue=%s exists=%s" % (
        row.get("class"), qp, os.path.isfile(os.path.join(_PP_ROOT, qp)) if qp else False)


GATES = [
    ("V-ADM-HERMETIC-HOME", pred_V_ADM_HERMETIC_HOME),
    ("V-ADM-TRACER-ARCHETYPE", pred_V_ADM_TRACER_ARCHETYPE),
    ("V-ADM-TRACER-REFUSED-ORIGIN", pred_V_ADM_TRACER_REFUSED_ORIGIN),
    ("V-ADM-TRACER-RECORD-INVALID", pred_V_ADM_TRACER_RECORD_INVALID),
    ("V-ADM-LEGACY-IDENTITY", pred_V_ADM_LEGACY_IDENTITY),
    ("V-ADM-LIVENESS-DECLARED", pred_V_ADM_LIVENESS_DECLARED),
]

# A literal, enforced by the exit code: a count that satisfies itself would let a
# dropped gate read as green.
EXPECTED = 6


def main() -> int:
    try:
        print("V-ADM gates")
        for name, pred in GATES:
            run_gate(name, pred)
        print()
        print("TOWER_ADMISSION_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, EXPECTED, EXPECTED))
        return 0 if _FAIL == 0 and _PASS == EXPECTED else 1
    finally:
        for k, v in _SAVED_ENV.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(TMP, ignore_errors=True)
        shutil.rmtree(_HOME, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
