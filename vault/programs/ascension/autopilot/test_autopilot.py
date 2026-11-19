#!/usr/bin/env python3
"""Gate for the Ascension Autopilot (V-AP-*). Runs against a scratch HOME/STATE_DIR with fake mission records; never
touches real missions (gm/judge/plan are stubbed). Ends with a mutation drill: each guard disabled must turn tests red.
Every refusal asserts its specific label; every guard has an admitting twin so a refuse-everything mutant also dies."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp(prefix="ap-test-"))
os.environ.update(AP_HOME=str(tmp / "home"), AP_STATE_DIR=str(tmp / "state"), AP_OWNER_TS="2026-11-11T00:00:00.000Z",
                  AP_PP=os.environ.get("AP_PP") or str(HERE.parents[3]))  # GEX44 install: AP_PP = the PP clone
(tmp / "home").mkdir()
(tmp / "state").mkdir()
(tmp / "cwd").mkdir()


def load():
    spec = importlib.util.spec_from_file_location("ap", HERE / "autopilot.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.design_lever = lambda *a, **k: None  # never a real model call from the gate; the SYNTH checks stub their own
    return m


GOOD = ["Phase 1: K1 freeze cohort (cap 3M): commit pool before draw; gate tools/test_k1.py with planted mutants",
        "Phase 2: K2 run (cap 10M): add 40 functions certified via certify.decide of the existing profile; gate tools/test_k2.py",
        "Phase 3: K3 checkpoint (cap 2M): re-run gates, write the checkpoint file stating new canonical certificates "
        "per profile by function identity, CHECKPOINT_COMPLETE"]
PROFILE_OK = ["Phase 1: P1 new additive profile (cap 5M): independent target oracle on original DOL bytes; frozen pilot "
              "committed before the draw; pre/post controls; A2 negatives; historical receipts byte-identical; separate counters",
              "Phase 2: P2 checkpoint (cap 2M): gates"]
results = []


def _scratch_repo() -> dict:
    """c0 = history before the generation (the base): an old criteria file, old receipts (5 CERTIFIED), an old gate and
    an old result. c1 freezes a criteria file; c2 writes data (result json, receipts, gates, held-out); c3 is docs-only
    (.md and .html); c4 re-touches the old result file only."""
    import subprocess
    d = tmp / "prod"
    (d / "tools").mkdir(parents=True)
    git = os.environ.get("CPP_GIT_EXE") or "git"

    def g(*a):
        r = subprocess.run([git, "-C", str(d), *a], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    def commit(msg):
        g("add", "-A")
        g("commit", "-qm", msg)
        return g("rev-parse", "HEAD")
    g("init", "-q")
    g("config", "user.email", "t@example.invalid")
    g("config", "user.name", "t")
    g("config", "commit.gpgsign", "false")
    (d / "old_crit.md").write_text("H: old hypothesis\n")
    (d / "old_rec.jsonl").write_text("".join(f'{{"id": "o{i}", "verdict": "CERTIFIED"}}\n' for i in range(5)))
    (d / "old_result.json").write_text('{"verdict": "REFUTED"}\n')
    (d / "tools" / "test_old.py").write_text("import sys\nsys.exit(0)\n")
    c0 = commit("history")
    (d / "crit.md").write_text("H: segments are contiguous; rule frozen\n")
    c1 = commit("freeze")
    (d / "result.json").write_text('{"verdict": "SUPPORTED"}\n')
    (d / "empty.json").write_text("{}\n")
    rows = [f'{{"id": "f{i}", "verdict": "CERTIFIED"}}' for i in range(3)]
    rows += ['{"id": "f0", "verdict": "CERTIFIED"}', '{"id": "u1", "verdict": "UNCERTIFIED"}', "# CERTIFIED header"]
    (d / "rec.jsonl").write_text("\n".join(rows) + "\n")
    with open(d / "old_rec.jsonl", "a") as f:
        f.write('{"id": "o9", "verdict": "CERTIFIED"}\n')
    (d / "heldout.json").write_text('{"exact": 12}\n')
    (d / "tools" / "test_g.py").write_text("import sys\nsys.exit(0)\n")
    (d / "tools" / "test_red.py").write_text("import sys\nsys.exit(1)\n")
    c2 = commit("result")
    # multi-line, so only the data/code allowlist (not the emptiness check) can refuse these as results
    (d / "notes.md").write_text("verdict, SUPPORTED\nwe learned a lot, really\n")
    (d / "report.html").write_text("<p>verdict SUPPORTED</p>\n<p>we learned a lot</p>\n")
    c3 = commit("docs")
    (d / "old_result.json").write_text('{"verdict": "REFUTED", "again": 1}\n')
    c4 = commit("retouch old result")
    return {"dir": d, "c0": c0, "c1": c1, "c2": c2, "c3": c3, "c4": c4}


REPO = _scratch_repo()


def check(name, cond):
    results.append((name, bool(cond)))


def refuses(ap, phases, label, command="", extra=()):
    return any(label in b for b in ap.policy_check(phases, command, list(extra)))


def run_all(ap):
    results.clear()
    # ---- policy: admits
    check("V-AP-POLICY-ADMITS-GOOD", ap.policy_check(GOOD, "", ["Title", "cert1-ksr receipts 8,687 unchanged"]) == [])
    check("V-AP-POLICY-ADMITS-PROFILE-WITH-ALL-CONDITIONS", ap.policy_check(PROFILE_OK, "") == [])
    check("V-AP-POLICY-ADMITS-FRESH-HALF-M", ap.policy_check(
        ["Phase 1: a (cap 3M): fresh 0.5M model pilot", "Phase 2: b (cap 1M): y"], "") == [])
    # ---- policy: forbidden acts, each with its label (the review's bypasses included)
    for label, line, want in [
            ("push", "then git push the branch", "push"), ("pushes", "the worker pushes the branch", "push"),
            ("merge", "merge the 582 into the headline counter", "merge counters"),
            ("revoke", "revoke contradicted certificates", "revocation"), ("revokes", "it revokes 3 certs", "revocation"),
            ("R2", "open R2 for the ctx", "R2"), ("r2-lower", "open r2 now", "R2"), ("R-2", "open R-2 now", "R2"),
            ("H2", "rebuild H2", "H2"), ("certifier", "modify certify.py to admit arm choice", "certifier"),
            ("update-certify", "update certify.py thresholds", "certifier"),
            ("add-rule", "add a rule to cert_cxx.py", "certifier"),
            ("passive", "cert1 receipts will be rewritten", "certifier"),
            ("canon", "change the canonical ctx headers", "certifier"), ("paid", "use paid API for speed", "paid"),
            ("budget", "raise the budget to 40M", "budget"),
            ("zero-width", "then p​ush the branch", "invisible"), ("homoglyph", "then рush it", "non-ASCII"),
            ("fresh-raw", "fresh 2,000,000 tokens for a pilot", "fresh"), ("fresh-k", "fresh 1500k tokens", "fresh")]:
        bad = GOOD[:2] + [GOOD[2] + "; " + line]
        check(f"V-AP-POLICY-REFUSES-{label.upper()}", refuses(ap, bad, want))
    # 2026-11-18 Owner rulings OR-1/OR-3 (pane 08cba76c): canonical headers are admitted (gated by the build and MATCH);
    # the canonical ctx (V-AP-POLICY-REFUSES-CANON above) stays refused; the packet names the rulings
    check("V-AP-POLICY-OR3-HEADERS-ADMITTED",
          ap.policy_check(GOOD[:2] + [GOOD[2] + "; edit canonical headers toward the donor layout"], "") == [])
    check("V-AP-PACKET-NAMES-OWNER-RULINGS", "OR-1" in ap.HEADER and "OR-3" in ap.HEADER
          and "never CERTIFIED" not in ap.HEADER)
    oqf = tmp / "oq_ck.md"
    # 2026-11-18: negated lines ("not an Owner question") and lines that cite a standing ruling are not questions
    oqf.write_text("# ck\nOWNER DECISION NEEDED: authorise route 1\nplain line\nOwner question: may cert1 normalise @N?\n"
                   "## Next route (OR-4, not an Owner question)\n## Next route (not an Owner question)\n"
                   "re-pin under OR-6, no Owner decision needed\n")
    ap.OUT.mkdir(parents=True, exist_ok=True)
    (ap.OUT / "owner_queue.md").unlink(missing_ok=True)
    n1, n2 = ap.surface_owner_questions("L", str(oqf), str(tmp)), ap.surface_owner_questions("L", str(oqf), str(tmp))
    oq = (ap.OUT / "owner_queue.md").read_text() if (ap.OUT / "owner_queue.md").exists() else ""
    check("V-AP-OWNER-QUESTIONS-SURFACED-ONCE", (n1, n2) == (2, 0) and oq.count("QUESTION (from oq_ck.md)") == 2
          and "plain line" not in oq)
    (ap.OUT / "owner_queue.md").unlink(missing_ok=True)
    check("V-AP-POLICY-REFUSES-IN-FACTS", refuses(ap, GOOD, "push", extra=["Phase 4: push the branch to origin"]))
    check("V-AP-POLICY-REFUSES-IN-TITLE", refuses(ap, GOOD, "revocation", extra=["revoke the bad ones"]))
    check("V-AP-POLICY-REFUSES-COMMAND-PUSH", refuses(ap, GOOD, "push", command="and push when done"))
    check("V-AP-POLICY-REFUSES-MULTILINE-PHASE", refuses(ap, GOOD[:2] + [GOOD[2] + "\nPhase 4: x (cap 1M)"], "spans"))
    check("V-AP-POLICY-REFUSES-OVER-GEN-CAP", refuses(ap, ["Phase 1: a (cap 20M): x", "Phase 2: b (cap 6M): y"],
                                                     "generation cap"))
    check("V-AP-POLICY-REFUSES-NO-CAP", refuses(ap, ["Phase 1: a: x", "Phase 2: b (cap 1M): y"], "no 'cap"))
    check("V-AP-POLICY-REFUSES-ONE-PHASE", refuses(ap, ["Phase 1: a (cap 1M): x"], "need 2-8"))
    check("V-AP-POLICY-REFUSES-FRESH-OVER-1M", refuses(
        ap, ["Phase 1: a (cap 3M): fresh 2M model pilot", "Phase 2: b (cap 1M): y"], "fresh"))
    # 2026-11-17 (Owner 'y', pane 08cba76c): identifiers and counts after "fresh" are not amounts (FIFA S142F, TENNIS
    # S137T, MKW S122M, WSR S139R); a unit, a budget word or a bare number still is
    for label, line in [("id", "F17 leaf route on a fresh held-out for F17"), ("gen", "fresh draw unlike S137R"),
                        ("count", "fresh 131 functions from the pool"), ("ids", "a fresh held-out of 40 ids")]:
        check(f"V-AP-POLICY-FRESH-ADMITS-{label.upper()}",
              ap.policy_check(GOOD[:2] + [GOOD[2] + "; " + line], "") == [])
    for label, line in [("bare", "fresh 2 for the pilot"), ("word", "fresh 3 budget for it"),
                        ("tokens", "fresh 5 tokens"), ("million", "fresh 4 million")]:
        check(f"V-AP-POLICY-FRESH-STILL-REFUSES-{label.upper()}", refuses(ap, GOOD[:2] + [GOOD[2] + "; " + line], "fresh"))
    # ---- profile conditions: each missing one refused; negation and other-line placement do not satisfy
    for cond, repl in [("oracle", ("oracle", "zzz")), ("DOL", ("DOL", "zzz")), ("frozen pilot", ("frozen pilot", "pilot")),
                       ("controls", ("controls", "zzz")), ("A2 negatives", ("A2 negatives", "zzz")),
                       ("receipts byte-identical", ("receipts byte-identical", "zzz")),
                       ("separate counters", ("separate counters", "zzz"))]:
        line = PROFILE_OK[0].replace(*repl)
        check(f"V-AP-PROFILE-NEEDS-{cond.upper().replace(' ', '-')}", refuses(ap, [line, PROFILE_OK[1]], "S26C"))
    neg = ("Phase 1: P7 new profile (cap 5M): no independent oracle; original DOL not used; frozen pilot skipped; "
           "pre/post controls later; A2 negatives unknown; historical receipts unchanged?; separate counters")
    check("V-AP-PROFILE-NEGATION-DOES-NOT-SATISFY", refuses(ap, [neg, PROFILE_OK[1]], "S26C"))
    check("V-AP-PROFILE-DEFINE-TRIGGERS", refuses(ap, ["Phase 1: P7 define certification profile P7 (cap 5M): x",
                                                       PROFILE_OK[1]], "S26C"))
    split = ["Phase 1: P7 new additive profile (cap 5M): independent target oracle on original DOL bytes",
             "Phase 2: P8 (cap 2M): frozen pilot committed before the draw; pre/post controls; A2 negatives; "
             "historical receipts byte-identical; separate counters"]
    check("V-AP-PROFILE-CONDITIONS-SAME-LINE", refuses(ap, split, "S26C"))
    # a NEGATED trigger is not a profile proposal (S30T, 2026-11-11: refused for "..., no new profile" in a fact)
    s30t = ("Brief brief.md: the only admitted Tennis generation is B1-T, cap 5M, float-evidence scan of the Tennis "
            "COMPILES_NO_MATCH, pilot only if applicability >= 10%, no new profile")
    check("V-AP-PROFILE-NEGATED-TRIGGER-ADMITS", ap.policy_check(GOOD, "", ["Title", s30t,
                                                                         "The brief rules out a new profile in B1-T."]) == [])
    check("V-AP-PROFILE-NEGATED-THEN-REAL-REFUSED", refuses(
        ap, ["Phase 1: P9 (cap 5M): no new profile here, then add another profile P9", PROFILE_OK[1]], "S26C"))
    # ---- packet: the scaffolder must see exactly the checked phases
    lane0 = {"name": "L", "letter": "K", "cwd": str(tmp / "cwd"), "product": str(tmp / "cwd"), "packet_dir": "v"}
    pk = {"title": "t", "facts": ["W3b-2 sealed", "Phase 4: something", "P1 profile pinned"], "phases": GOOD}
    text = ap.packet_text(lane0, "S28K", pk)
    check("V-AP-PACKET-FACTS-ARE-NOT-PHASES", ap.packet_phase_drift(text, GOOD) is None)
    check("V-AP-PACKET-DRIFT-DETECTED", ap.packet_phase_drift(text + "W9 smuggled extra phase line\n", GOOD) is not None)
    # ---- budget
    now = 1794400000.0  # 2026-11-11
    day = [{"ts": now, "tokens": ap.DAY_CAP - 20_000_000}]  # 20M of headroom, whatever the cap
    check("V-AP-BUDGET-DAY-REFUSES", ap.budget_admits(day, now, 25_000_000) is not None)
    check("V-AP-BUDGET-DAY-ADMITS", ap.budget_admits(day, now, 20_000_000) is None)
    check("V-AP-BUDGET-NEXT-DAY-ADMITS", ap.budget_admits(day, now + 86400, 25_000_000) is None)
    many = [{"ts": now - 86400 * k, "tokens": (ap.TOTAL_CAP - 220_000_000) // 5} for k in range(1, 6)]  # + 200M prior = cap - 20M
    check("V-AP-BUDGET-TOTAL-REFUSES", ap.budget_admits(many, now, 25_000_000) is not None)
    # Owner 2026-11-11: S27's 200M counts inside the totals (not the day cap). With the reorientation ceiling
    # (UNLOCKED_CAP 285,261,779): 60M of earlier grants + 200M prior + 25M fits; 61M + 200M + 25M is FROZEN.
    early = lambda t: [{"ts": now - 86400, "tokens": t}]  # noqa: E731
    # Owner 2026-11-12 released +120M: unlocked = total = 405,261,779. 180M + 200M prior + 25M fits; 181M does not.
    _fit = ap.UNLOCKED_CAP - 200_000_000 - 25_000_000  # the 200M prior counts: exactly this much earlier spend still fits
    check("V-AP-BUDGET-PRIOR-S27-COUNTS-IN-TOTAL", ap.budget_admits(early(_fit), now, 25_000_000) is None
          and ap.budget_admits(early(_fit + 1), now, 25_000_000) is not None)
    check("V-AP-BUDGET-OWNER-4700M", ap.UNLOCKED_CAP == 4_700_000_000 and ap.TOTAL_CAP == 4_700_000_000
          and ap.DAY_CAP == 500_000_000)  # Owner 2026-11-16 'Day cap 500M and total +1B' (was 3.7B / 250M)
    _keep_u = ap.UNLOCKED_CAP; ap.UNLOCKED_CAP = 285_261_779  # the FROZEN mechanism itself still works
    check("V-AP-BUDGET-FROZEN-MECHANISM", str(ap.budget_admits(early(61_000_000), now, 25_000_000)).startswith("FROZEN"))
    check("V-AP-BUDGET-PRIOR-NOT-IN-DAY", ap.spend_totals([], now) == (200_000_000, 0))
    check("V-AP-BUDGET-FROZEN-IS-OWNERS", "only the Owner releases" in str(ap.budget_admits(early(61_000_000), now,
                                                                                         25_000_000)))
    ap.UNLOCKED_CAP = _keep_u
    keep = ap.UNLOCKED_CAP
    ap.UNLOCKED_CAP = 10 ** 12  # the 400M total must still bind on its own
    check("V-AP-BUDGET-TOTAL-BINDS-ABOVE-UNLOCK", str(ap.budget_admits(many, now, 25_000_000)).startswith("total"))
    ap.UNLOCKED_CAP = keep
    check("V-AP-BUDGET-WALL-REFUSES", ap.budget_admits([], 1796083200.0, 1) is not None)  # 2026-12-01
    check("V-AP-UNMEASURED-CALL-BOOKS-RESERVE", ap.call_tokens(None) == (2_000_000, False)
          and ap.call_tokens(1234) == (1234, True))
    # ---- verdict parsing
    check("V-AP-LASTJSON", ap.last_json('blah {"a": {"b": 1}} more {"verdict": "AGREE", "x": [1, {"y": 2}]}')
          == {"verdict": "AGREE", "x": [1, {"y": 2}]})
    check("V-AP-LASTJSON-FENCED", ap.last_json('x\n```json\n{"verdict": "DISAGREE"}\n```\n') == {"verdict": "DISAGREE"})
    check("V-AP-LASTJSON-NO-FALLBACK", ap.last_json('quoted {"verdict": "AGREE"} then {"verdict": "AGREE", "last": "a"b"}')
          is None)
    check("V-AP-LASTJSON-TRAILING-TEXT", ap.last_json('{"verdict": "AGREE"} and some words after') is None)
    full = {"verdict": "AGREE", "protected_ok": True, "gates": [{"cmd": "x", "rc": 0}]}
    check("V-AP-AGREE-SUPPORTED", ap.agree_supported(full))
    check("V-AP-AGREE-NEEDS-PROTECTED", not ap.agree_supported(dict(full, protected_ok=False)))
    check("V-AP-AGREE-NEEDS-GATES-RC0", not ap.agree_supported(dict(full, gates=[{"cmd": "x", "rc": 1}]))
          and not ap.agree_supported(dict(full, gates=[])) and not ap.agree_supported(dict(full, gates=[{"rc": None}])))
    sg = [{"cmd": "timeout 600 python3 tools/test_new.py", "rc": 0},
          {"cmd": "timeout 600 python3 tools/test_old.py", "rc": 1, "superseded_by_certs": 2}]
    sup = dict(full, new_canonical_certs=2, gates=sg)
    check("V-AP-AGREE-SUPERSEDED-ADMITTED", ap.agree_supported(sup))
    check("V-AP-AGREE-SUPERSEDED-COUNT-BOUNDED", not ap.agree_supported(dict(sup, new_canonical_certs=1))
          and ap.agree_supported(dict(sup, new_canonical_certs=3))
          and not ap.agree_supported(dict(sup, new_canonical_certs=0))
          and not ap.agree_supported(dict(sup, gates=[sg[0], dict(sg[1], superseded_by_certs=None)])))
    check("V-AP-AGREE-SUPERSEDED-NEEDS-AN-RC0", not ap.agree_supported(dict(sup, gates=[sg[1]])))
    # 2026-11-18 (KSR S169K): the pinned gate's delta accumulates over generations: 9 accepted, then 43 more = 52
    cum = dict(full, new_canonical_certs=43, gates=[sg[0], dict(sg[1], superseded_by_certs=52)])
    pri = {"tools/test_old.py": 9}
    check("V-AP-SUPERSEDED-CUMULATIVE", ap.agree_supported(cum, pri) and not ap.agree_supported(cum)
          and not ap.agree_supported(dict(cum, gates=[sg[0], dict(sg[1], superseded_by_certs=9)]), pri)
          and not ap.agree_supported(dict(cum, gates=[sg[0], dict(sg[1], superseded_by_certs=53)]), pri)
          and not ap.agree_supported(cum, {"tools/test_other.py": 9}))
    # (KSR S171K): 38 new certificates, 10 of them from the pinned pool: 62 = 52 + 10
    check("V-AP-SUPERSEDED-PARTIAL-POOL", ap.agree_supported(dict(full, new_canonical_certs=38, gates=[
        sg[0], dict(sg[1], superseded_by_certs=62)]), {"tools/test_old.py": 52}))
    check("V-AP-SUPERSEDED-RECORDED", ap.superseded_record(cum, pri) == {"tools/test_old.py": 52}
          and ap.superseded_record(sup) == {"tools/test_old.py": 2} and ap.superseded_record(full, pri) == pri)
    check("V-AP-JUDGE-TOOLS-NO-BARE-PREFIX", not any(t in ap.JUDGE_TOOLS for t in ("Bash(python3:*)", "Bash(timeout:*)")))
    # ---- protected identities read by the autopilot itself
    pf = tmp / "receipts.jsonl"
    pf.write_text("a\nb\n")
    import hashlib
    h = hashlib.sha256(pf.read_bytes()).hexdigest()[:8]
    check("V-AP-PROTECTED-OK", ap.protected_check({"protected": [{"path": str(pf), "sha256_prefix": h, "lines": 2}]}) is None)
    check("V-AP-PROTECTED-CHANGED", ap.protected_check({"protected": [{"path": str(pf), "sha256_prefix": "00000000"}]})
          is not None)
    check("V-AP-PROTECTED-MISSING", ap.protected_check({"protected": [{"path": str(tmp / "nope"), "sha256_prefix": h}]})
          is not None)

    # ---- progress taxonomy: verified in a real scratch git repo, never taken from the judge's text
    # base = c0: everything in c0 is history (Woz veto 2026-11-11: history is not progress).
    P, prod = REPO, str(REPO["dir"])
    inf = {"hypothesis_file": "crit.md", "freeze_commit": P["c1"], "result_file": "result.json",
           "result_commit": P["c2"], "verdict": "SUPPORTED", "positive_control": True}
    cls = lambda v, base=P["c0"]: ap.classify_progress(v, prod, base)[0]  # noqa: E731
    info = lambda **k: {"information": dict(inf, **k)}  # noqa: E731
    check("V-AP-PROGRESS-INFO-VERIFIED", cls(info()) == "INFORMATION")
    check("V-AP-PROGRESS-INFO-SHORT-SHAS", cls(info(freeze_commit=P["c1"][:8], result_commit=P["c2"][:8])) == "INFORMATION")
    check("V-AP-PROGRESS-INFO-RESULT-BEFORE-FREEZE", cls(info(freeze_commit=P["c2"], result_commit=P["c1"])) == "NONE")
    check("V-AP-PROGRESS-INFO-RESULT-ALREADY-AT-FREEZE",
          cls(info(freeze_commit=P["c2"], result_commit=P["c3"])) == "NONE")
    check("V-AP-PROGRESS-INFO-DOCS-ONLY", cls(info(result_file="notes.md", result_commit=P["c3"])) == "NONE"
          and cls(info(result_file="report.html", result_commit=P["c3"])) == "NONE")
    check("V-AP-PROGRESS-INFO-UNDETERMINED", cls(info(verdict="UNDETERMINED")) == "NONE")
    check("V-AP-PROGRESS-INFO-NO-CONTROL", cls(info(positive_control=False)) == "NONE")
    check("V-AP-PROGRESS-INFO-OLD-HYPOTHESIS", cls(info(hypothesis_file="old_crit.md")) == "NONE")
    check("V-AP-PROGRESS-INFO-FREEZE-BEFORE-WINDOW", cls(info(freeze_commit=P["c0"])) == "NONE")
    check("V-AP-PROGRESS-INFO-EMPTY-RESULT", cls(info(result_file="empty.json")) == "NONE")
    check("V-AP-PROGRESS-INFO-OLD-RESULT-RETOUCHED",
          cls(info(hypothesis_file="notes.md", freeze_commit=P["c3"], result_file="old_result.json",
                   result_commit=P["c4"])) == "NONE")
    check("V-AP-PROGRESS-INFO-STALE-WINDOW", cls(info(), base=P["c2"]) == "NONE")
    check("V-AP-PROGRESS-NO-BASE-IS-NONE", ap.classify_progress(info(), prod, None)[0] == "NONE")
    rec = [{"path": "rec.jsonl", "commit": P["c2"]}]
    certv = lambda n, r=rec: {"new_canonical_certs": n, "cert_receipts": r}  # noqa: E731
    check("V-AP-PROGRESS-CERT-VERIFIED", cls(certv(3)) == "CERT")
    check("V-AP-PROGRESS-CERT-DUP-UNCERTIFIED-HEADER-NOT-COUNTED", cls(certv(4)) == "NONE")
    check("V-AP-PROGRESS-CERT-DUPLICATE-POINTER-NOT-COUNTED", cls(certv(4, rec + rec)) == "NONE")
    old = [{"path": "old_rec.jsonl", "commit": P["c2"]}]
    check("V-AP-PROGRESS-CERT-COUNTS-ADDED-ROWS-ONLY", cls(certv(1, old)) == "CERT" and cls(certv(2, old)) == "NONE")
    check("V-AP-PROGRESS-CERT-STALE-WINDOW", cls(certv(3), base=P["c2"]) == "NONE")
    check("V-AP-PROGRESS-CERT-NO-RECEIPTS", cls({"new_canonical_certs": 3}) == "NONE")
    check("V-AP-PROGRESS-CERT-PROSE-RECEIPTS", cls(certv(1, [{"path": "notes.md", "commit": P["c3"]}])) == "NONE")
    cap = {"gate": "tools/test_g.py", "commit": P["c2"], "heldout_file": "heldout.json", "mutant_rc": 1,
           "heldout_before": 10, "heldout_after": 12}
    capv = lambda **k: {"validated_capability": True, "capability": dict(cap, **k)}  # noqa: E731
    check("V-AP-PROGRESS-CAPABILITY-VERIFIED", cls(capv()) == "CAPABILITY")
    check("V-AP-PROGRESS-CAPABILITY-OLD-GATE", cls(capv(gate="tools/test_old.py")) == "NONE")
    check("V-AP-PROGRESS-CAPABILITY-STALE-WINDOW", cls(capv(), base=P["c2"]) == "NONE")
    check("V-AP-PROGRESS-CAPABILITY-NO-HELDOUT-DATA", cls(capv(heldout_file="")) == "NONE"
          and cls(capv(heldout_file="old_crit.md")) == "NONE")
    check("V-AP-PROGRESS-CAPABILITY-MUTANT-GREEN", cls(capv(mutant_rc=0)) == "NONE")
    check("V-AP-PROGRESS-CAPABILITY-NO-CHANGE", cls(capv(heldout_after=10)) == "NONE")
    check("V-AP-PROGRESS-CAPABILITY-GATE-RED-ON-RERUN", cls(capv(gate="tools/test_red.py")) == "NONE")
    check("V-AP-PROGRESS-CAPABILITY-DOCS-COMMIT", cls(capv(gate="notes.md", commit=P["c3"])) == "NONE")
    gpath = P["dir"] / "tools" / "test_g.py"
    keep_gate = gpath.read_bytes()
    try:
        gpath.write_text("import sys\nsys.exit(0)  # edited after the cited commit\n")
        check("V-AP-PROGRESS-CAPABILITY-RUNS-CITED-BLOB-ONLY", cls(capv()) == "NONE")
    finally:
        gpath.write_bytes(keep_gate)
    check("V-AP-PROGRESS-NOTHING-CLAIMED", ap.classify_progress({}, prod, P["c0"]) == ("NONE", ""))
    # ---- MATCH (SPEC-match-exploit.md, Owner 2026-11-17): objdiff progress measured by the autopilot itself
    mrep = tmp / "mrep"
    mrep.mkdir(exist_ok=True)

    def write_rep(at100):
        (mrep / "report.json").write_text(json.dumps({"units": [{"name": "u1", "functions": [
            {"name": n, "fuzzy_match_percent": 100.0 if n in at100 else 50.0} for n in ("a", "b", "c")]}]}))
    mlane = {"name": "MLANE", "match_report": {"cmd": ["true"], "path": "report.json"}}
    msnap = ap.OUT / "match" / "MLANE.json"
    msnap.unlink(missing_ok=True)
    write_rep({"a"})
    c, n = ap.classify_progress({}, str(mrep), P["c0"], mlane)
    check("V-MATCH-SEEDS-WITHOUT-CLAIM", c == "NONE" and "seeded" in n and json.loads(msnap.read_text()) == ["u1::a"])
    write_rep({"a", "b"})
    c, n = ap.classify_progress({}, str(mrep), P["c0"], mlane)
    check("V-MATCH-CREDITED", c == "MATCH" and "+1" in n and json.loads(msnap.read_text()) == ["u1::a", "u1::b"])
    write_rep({"b", "c"})
    c, n = ap.classify_progress({}, str(mrep), P["c0"], mlane)
    check("V-MATCH-REGRESSION-REFUSED", c == "NONE" and "u1::a" in n
          and json.loads(msnap.read_text()) == ["u1::a", "u1::b"])
    write_rep({"a", "b", "c"})  # 2026-11-18 (MKW S151M): new matches counted against the snapshot, which is not moved
    check("V-MATCH-NEW-COUNTED", ap.match_new(mlane, str(mrep)) == (1, None)
          and json.loads(msnap.read_text()) == ["u1::a", "u1::b"] and ap.match_new({"name": "X"}, str(mrep))[0] == 0)
    c, n = ap.classify_progress({}, str(mrep), P["c0"], dict(mlane, match_report={"cmd": ["false"], "path": "report.json"}))
    check("V-MATCH-BUILD-FAIL-NO-CLAIM", c == "NONE" and "rc=" in n)
    check("V-MATCH-NOT-CONFIGURED", ap.classify_progress({}, str(mrep), P["c0"], {"name": "MLANE"}) == ("NONE", ""))
    # 2026-11-18 (MKW S151M held 6.7 h): a tracked file the report build dirties is restored; a dirty one stays
    gdir = Path(tempfile.mkdtemp(prefix="mgit-", dir=tmp))  # fresh per run: the mutation drill re-runs this body
    for a in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(gdir), *a], check=True)
    (gdir / "splits.txt").write_text("a\n")
    (gdir / "mine.txt").write_text("m\n")
    subprocess.run(["git", "-C", str(gdir), "add", "."], check=True)
    subprocess.run(["git", "-C", str(gdir), "commit", "-qm", "c"], check=True)
    (gdir / "mine.txt").write_text("worker edit\n")
    (gdir / "report.json").write_text(json.dumps({"units": []}))
    glane = {"name": "MGIT", "match_report": {"cmd": ["sh", "-c", "echo b >> splits.txt"], "path": "report.json"}}
    cur, why = ap.match_at100(glane, str(gdir))
    check("V-MATCH-BUILD-LEAVES-TREE-CLEAN", cur == set() and why is None
          and (gdir / "splits.txt").read_text() == "a\n" and (gdir / "mine.txt").read_text() == "worker edit\n")
    # 2026-11-19 (MKW S191M, FIFA S196F held ~6 h): a tracked file the judge's gate runs dirty is restored too
    keep_rc = ap.run_claude

    def judge_dirties(*a, **k):
        (gdir / "splits.txt").write_text("gate rewrote me\n")
        return {"ok": True, "result": '{"verdict": "AGREE"}', "tokens": 1}
    ap.run_claude = judge_dirties
    jp = Path(ap.HOME) / "judge_prompt.md"
    made_jp = not jp.exists()
    if made_jp:
        jp.write_text("judge {CHECKPOINT} in {PRODUCT}")
    try:
        jv = ap.judge({"name": "MGIT", "cwd": str(gdir)}, "ck.md", str(gdir))
    finally:
        ap.run_claude = keep_rc
        if made_jp:
            jp.unlink()
    check("V-AP-JUDGE-LEAVES-TREE-CLEAN", jv.get("verdict") == "AGREE"
          and (gdir / "splits.txt").read_text() == "a\n" and (gdir / "mine.txt").read_text() == "worker edit\n")
    # 2026-11-18 (KSR S168K): a superseded gate stands only if it predates the generation and the certificates verify
    sdir = Path(tempfile.mkdtemp(prefix="sgit-", dir=tmp))

    def sgit(*a):
        return subprocess.run(["git", "-C", str(sdir), *a], check=True, capture_output=True, text=True).stdout.strip()
    for a in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        sgit(*a)
    (sdir / "tools").mkdir()
    (sdir / "tools" / "test_old.py").write_text("print(1)\n")
    sgit("add", ".")
    sgit("commit", "-qm", "base")
    s0 = sgit("rev-parse", "HEAD")
    (sdir / "tools" / "test_new.py").write_text("print(2)\n")
    (sdir / "receipts.jsonl").write_text('{"id": "f1", "verdict": "CERTIFIED"}\n{"id": "f2", "verdict": "CERTIFIED"}\n')
    sgit("add", ".")
    sgit("commit", "-qm", "gen")
    s1 = sgit("rev-parse", "HEAD")
    sv = dict(sup, cert_receipts=[{"path": "receipts.jsonl", "commit": s1}])
    check("V-AP-SUPERSEDED-OK-PROVEN", ap.superseded_ok(sv, str(sdir), s0) is None)
    check("V-AP-SUPERSEDED-NOT-THIS-GENERATIONS-GATE", isinstance(ap.superseded_ok(dict(sv, gates=[
        sg[1], dict(sg[0], rc=1, superseded_by_certs=2)]), str(sdir), s0), str))
    check("V-AP-SUPERSEDED-NEEDS-VERIFIED-CERTS", isinstance(ap.superseded_ok(dict(
        sv, new_canonical_certs=3, gates=[sg[0], dict(sg[1], superseded_by_certs=3)]), str(sdir), s0), str)
          and isinstance(ap.superseded_ok(dict(sv, cert_receipts=[]), str(sdir), s0), str))
    check("V-AP-SUPERSEDED-ABSENT-NO-CHECK", ap.superseded_ok(dict(full, new_canonical_certs=2), str(sdir), None) is None)
    # 2026-11-18 (MKW S151M): a pool that shrank on build matches; bounded by the functions newly at 100%
    mg = {"cmd": "timeout 600 python3 tools/test_old.py", "rc": 1, "superseded_by_matches": 3}
    vmt = dict(full, new_canonical_certs=0, gates=[sg[0], mg])
    check("V-AP-AGREE-MATCH-SUPERSEDED-ADMITTED", ap.agree_supported(vmt)
          and not ap.agree_supported(dict(vmt, gates=[sg[0], dict(mg, superseded_by_matches=0)]))
          and not ap.agree_supported(dict(vmt, gates=[sg[0], dict(mg, superseded_by_matches=3)]), {"m:tools/test_old.py": 3}))
    keep_mn = ap.match_new
    ap.match_new = lambda lane, p: (5, None)
    check("V-AP-MATCH-SUPERSEDED-BOUNDED", ap.superseded_ok(vmt, str(sdir), s0) is None
          and isinstance(ap.superseded_ok(dict(vmt, gates=[sg[0], dict(mg, superseded_by_matches=6)]), str(sdir), s0), str)
          and ap.superseded_ok(dict(vmt, gates=[sg[0], dict(mg, superseded_by_matches=6)]), str(sdir), s0,
                               {"m:tools/test_old.py": 4}) is None)
    ap.match_new = lambda lane, p: (0, "no report")
    check("V-AP-MATCH-SUPERSEDED-NEEDS-MATCHES", isinstance(ap.superseded_ok(vmt, str(sdir), s0), str))
    ap.match_new = keep_mn
    check("V-AP-MATCH-SUPERSEDED-RECORDED", ap.superseded_record(vmt) == {"m:tools/test_old.py": 3})
    # 2026-11-18 (KSR S173K): this generation's own gate, written before the receipts that turned it red
    (sdir / "tools" / "test_mid.py").write_text("print(4)\n")
    sgit("add", ".")
    sgit("commit", "-qm", "gen gate pins the pool")
    with open(sdir / "receipts.jsonl", "a") as fh:
        fh.write('{"id": "f3", "verdict": "CERTIFIED"}\n')
    sgit("commit", "-qam", "more certs")
    s3 = sgit("rev-parse", "HEAD")
    vown = dict(full, new_canonical_certs=3, cert_receipts=[{"path": "receipts.jsonl", "commit": s3}],
                gates=[sg[0], {"cmd": "timeout 600 python3 tools/test_mid.py", "rc": 1, "superseded_by_certs": 1}])
    check("V-AP-SUPERSEDED-OWN-GATE-BEFORE-RECEIPTS", ap.superseded_ok(vown, str(sdir), s0) is None)
    (sdir / "tools" / "test_mid.py").write_text("print(5)\n")
    sgit("commit", "-qam", "gate edited after the receipts")
    check("V-AP-SUPERSEDED-OWN-GATE-TOUCHED-AFTER-REFUSED", isinstance(ap.superseded_ok(vown, str(sdir), s0), str))
    # 2026-11-18 (KSR S171K): the mission's head is a control-repo commit the product lacks -> the product's HEAD
    (sdir / "evidence").mkdir()
    (sdir / "evidence" / "checkpoint_x.md").write_text("x\n")
    sgit("add", ".")
    sgit("commit", "-qm", "checkpoint")
    check("V-AP-TERMINAL-CHECKPOINT-PRODUCT-HEAD", ap.terminal_checkpoint(
        {"base": s0}, str(sdir), {"binding": {"head": "f" * 40}}) == "evidence/checkpoint_x.md")
    # 2026-11-18 (FIFA S170F): a gate the judge excludes must predate the generation and be unchanged by it
    xo = {"cmd": "timeout 600 python3 tools/test_old.py", "why": "needs arguments"}
    check("V-AP-EXCLUDED-OLD-UNCHANGED-OK", ap.excluded_ok(dict(full, excluded_gates=[xo]), str(sdir), s0) is None
          and ap.excluded_ok(full, str(sdir), s0) is None)
    check("V-AP-EXCLUDED-REFUSED", all(isinstance(ap.excluded_ok(dict(full, excluded_gates=x), str(sdir), b), str) for x, b in (
        ([dict(xo, cmd="timeout 600 python3 tools/test_new.py")], s0), (["tools/test_old.py"], s0), ([xo], None))))
    (sdir / "tools" / "test_old.py").write_text("print(3)\n")
    sgit("commit", "-qam", "gen edits the old gate")
    check("V-AP-EXCLUDED-CHANGED-REFUSED", isinstance(ap.excluded_ok(dict(full, excluded_gates=[xo]), str(sdir), s0), str))

    # ---- lane transitions with stubs
    lanes = [dict(lane0, mission="m-aaaaaaaaaaaa")]
    rec = {"mission_id": "m-aaaaaaaaaaaa", "state": "RUNNING", "owner_hold": {"kind": "checkpoint", "set_at": 1,
           "evidence": str(tmp / "ck.md")}}
    recp = tmp / "state" / "gsd-mission-m-aaaaaaaaaaaa.json"
    calls, fail_on = [], set()

    def gm_stub(*a, **k):
        calls.append(a)
        return (1, "refused") if a[0] in fail_on else (0, '"mission_id": "m-bbbbbbbbbbbb"')
    ap.gm = gm_stub
    sh_out = {"dirty": ""}
    ap.sh = lambda cmd, **k: (0, sh_out["dirty"] if "status" in cmd else "")
    ap.mission_spend = lambda m: 1
    ap.write_packet = lambda lane, name, text: Path(lane["cwd"]) / "v" / f"{name}.md"
    good_judge = lambda *a: dict(full, new_canonical_certs=3, validated_capability=False, _tokens=5)  # noqa: E731
    good_plan = lambda *a: {"title": "t", "facts": [], "phases": GOOD, "_tokens": 7}  # noqa: E731

    def fresh(set_at):
        for f in ("state.json", "ledger.jsonl", "owner_queue.md", "digest.md", "autopilot.log", "OFF"):
            (tmp / "home" / f).unlink(missing_ok=True)
        calls.clear()
        fail_on.clear()
        sh_out["dirty"] = ""
        rec["owner_hold"]["set_at"] = set_at
        rec["state"] = "RUNNING"
        recp.write_text(json.dumps(rec))
        ap.judge, ap.plan = good_judge, good_plan
        (tmp / "home" / "EVO_OFF").write_text("")  # the pre-EVO suite runs with EVO off; the EVO section turns it on
        return {}

    def ledger():
        p = tmp / "home" / "ledger.jsonl"
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    st = fresh(2)
    ap.judge = lambda *a: {"verdict": "DISAGREE", "notes": "x", "_tokens": 5}
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-DISAGREE-PARKS", st["lanes"]["L"]["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    st = fresh(3)
    ap.judge = lambda *a: {"verdict": "AGREE", "new_canonical_certs": 3, "_tokens": 5}  # no gates, no protected_ok
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-UNSUPPORTED-AGREE-PARKS", st["lanes"]["L"]["status"] == "PARKED" and not calls)
    # 2026-11-18 (KSR S168K): a superseded gate reaches the autopilot's own git check on the real judge path; with no
    # generation base it cannot be proven older than the generation, so the AGREE does not stand
    st = fresh(4)
    ap.judge = lambda *a: dict(full, new_canonical_certs=3, _tokens=5, gates=[
        {"cmd": "timeout 600 python3 tools/test_new.py", "rc": 0},
        {"cmd": "timeout 600 python3 tools/test_old.py", "rc": 1, "superseded_by_certs": 3}])
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-SUPERSEDED-CHECKED-ON-JUDGE-PATH", st["lanes"]["L"]["status"] == "PARKED" and not calls
          and "superseded" in (tmp / "home" / "digest.md").read_text())
    # Owner envelope on one lane (2026-11-13, 300M for KSR): what the ledger booked for the lane since it opened + the
    # next caps must fit; other lanes and earlier rows do not count; no envelope = no limit; an exhausted one parks.
    envl = dict(lanes[0], envelope={"tokens": 300_000_000, "since": 1000, "note": "t"})
    erows = [{"lane": "L", "ts": 2000, "tokens": 280_000_000}, {"lane": "L", "ts": 500, "tokens": 90_000_000},
             {"lane": "T", "ts": 2000, "tokens": 90_000_000}]
    check("V-AP-ENVELOPE-ADMITS-INSIDE", ap.envelope_admits(envl, erows, 20_000_000) is None)
    check("V-AP-ENVELOPE-REFUSES-OVER", ap.envelope_admits(envl, erows, 20_000_001) is not None)
    check("V-AP-ENVELOPE-ABSENT-ADMITS", ap.envelope_admits(lanes[0], erows, 10**12) is None)
    st = fresh(63)
    ap.lane_tick(st, dict(lanes[0], envelope={"tokens": 1, "since": 0, "note": "t"}), False)
    check("V-AP-ENVELOPE-PARKS-BEFORE-ARM", st["lanes"]["L"]["status"] == "PARKED"
          and st["lanes"]["L"].get("park_kind") == "envelope" and not any(c[0] == "arm" for c in calls))
    # Cost-hold top-up (Owner 2026-11-13 "sí"): inside an envelope naming its Owner turn, only while the generation
    # registers certificates, at most MAX_TOPUPS per generation, once per hold; otherwise one Owner-queue line.
    keep_sh2, keep_hold, keep_auth = ap.sh, dict(rec["owner_hold"]), rec.get("authority_tokens")
    prog = {"rc": 1}
    ap.sh = lambda cmd, **k: (prog["rc"], "") if "diff" in cmd else (0, sh_out["dirty"] if "status" in cmd else "")
    envt = {"tokens": 300_000_000, "since": 0, "note": "t", "owner_turn": "s:2026-11-13T11:17"}

    def cost_run(set_at, lane_env=envt, topups=0, rc=1, ls_extra=None):
        st = fresh(set_at)
        prog["rc"] = rc
        rec["owner_hold"] = {"kind": "cost", "set_at": set_at, "reason": "cost breaker"}
        rec["authority_tokens"] = 23_500_000
        recp.write_text(json.dumps(rec))
        st["lanes"] = {"L": dict({"status": "RUNNING", "gen": "S37K", "base": "b0", "topups": topups, "blank": 0,
                                  "arm_fails": 0, "mission": "m-aaaaaaaaaaaa"}, **(ls_extra or {}))}
        ln = dict(lanes[0], envelope=lane_env) if lane_env else lanes[0]
        ap.lane_tick(st, ln, False)
        return st, ln
    auth_calls = lambda: [c for c in calls if c[0] == "authority"]  # noqa: E731
    q_text = lambda: (tmp / "home" / "owner_queue.md").read_text() if (tmp / "home" / "owner_queue.md").exists() else ""  # noqa: E731
    st, ln = cost_run(70)
    a = auth_calls()
    check("V-AP-TOPUP-INSIDE-ENVELOPE", len(a) == 1 and a[0][a[0].index("--tokens") + 1] == "29500000"
          and any(c[0] == "release" for c in calls) and st["lanes"]["L"]["topups"] == 1
          and sum(r["tokens"] for r in ledger() if r["kind"] == "auto_topup") == 6_000_000)
    calls.clear()
    ap.lane_tick(st, ln, False)
    check("V-AP-TOPUP-ONCE-PER-HOLD", not auth_calls())
    cost_run(71, rc=0)
    check("V-AP-TOPUP-NEEDS-CERTIFICATES", not auth_calls() and "no certificate registered" in q_text())
    cost_run(72, topups=2)
    check("V-AP-TOPUP-CAPPED-PER-GENERATION", not auth_calls() and "max 2" in q_text())
    cost_run(73, lane_env=dict(envt, tokens=1))
    check("V-AP-TOPUP-ENVELOPE-FULL", not auth_calls() and "envelope" in q_text())
    cost_run(74, lane_env=None)
    check("V-AP-TOPUP-NEEDS-OWNER-ENVELOPE", not auth_calls() and "no Owner envelope" in q_text())
    # Spec ascension-autopilot-stall-fixes (Owner "y" 2026-11-16). F1: no certificate, but >= 1 new commit on the
    # generation branch AND a cost_mark after the last top-up -> one top-up booked basis=progress. F2: < 1.5 h of wall
    # left -> the same authority act extends the wall. F4: a halt with commits and no checkpoint is continued once.
    pc = {"n": "0"}
    ap.sh = lambda cmd, **k: ((prog["rc"], "") if "diff" in cmd else (0, pc["n"]) if "rev-list" in cmd
                              else (0, sh_out["dirty"] if "status" in cmd else ""))

    def prog_run(set_at, commits="2", mark_at=500.0, created=None, **kw):
        pc["n"] = commits
        rec.update(binding={"root": str(tmp / "no-tree"), "head": "c" * 40, "branch": "s1/work"}, cost_mark={"at": mark_at},
                   created_at=created if created is not None else __import__("time").time(), max_hours=16.0)
        return cost_run(set_at, rc=0, **kw)
    st, ln = prog_run(90)
    a = auth_calls()
    tops = [r for r in ledger() if r["kind"] == "auto_topup"]
    check("V-AP-TOPUP-PROGRESS", len(a) == 1 and "--extend-hours" not in a[0] and len(tops) == 1
          and tops[0].get("basis", "").startswith("proven progress") and st["lanes"]["L"].get("topup_head") == "c" * 40
          and any(c[0] == "release" for c in calls))
    prog_run(91, commits="0")
    check("V-AP-TOPUP-NOPROGRESS", not auth_calls() and "no proven progress" in q_text())
    prog_run(92, mark_at=0)
    check("V-AP-TOPUP-FP-ONLY", not auth_calls())
    prog_run(93, ls_extra={"topup_at": 1000.0})
    check("V-AP-TOPUP-PROGRESS-SINCE-LAST", not auth_calls())
    prog_run(94, lane_env=dict(envt, tokens=1))
    check("V-AP-TOPUP-PROGRESS-ENVELOPE", not auth_calls() and "envelope" in q_text())
    prog_run(95, created=__import__("time").time() - 15 * 3600)
    a = auth_calls()
    check("V-AP-TOPUP-AGE", len(a) == 1 and "--extend-hours" in a[0] and a[0][a[0].index("--extend-hours") + 1] == "4"
          and [r.get("extend_hours") for r in ledger() if r["kind"] == "auto_topup"] == [4.0])
    # 2026-11-16 S77M: an unbound mission (no worktree binding) works in its work_dir; that HEAD is the generation head
    keep_sh3 = ap.sh
    ap.sh = lambda cmd, **k: (0, "f" * 40) if "rev-parse" in cmd else keep_sh3(cmd, **k)
    pc["n"] = "6"
    rec.pop("binding", None)
    rec.update(cost_mark={"at": 500.0}, created_at=__import__("time").time(), max_hours=16.0, work_dir=str(tmp))
    st, ln = cost_run(88, rc=0)
    tops = [r for r in ledger() if r["kind"] == "auto_topup"]
    check("V-AP-TOPUP-PROGRESS-UNBOUND", len(auth_calls()) == 1 and len(tops) == 1
          and tops[0].get("basis", "").startswith("proven progress") and st["lanes"]["L"].get("topup_head") == "f" * 40)
    ap.sh = keep_sh3
    for k in ("cost_mark", "created_at", "max_hours", "work_dir"):
        rec.pop(k, None)
    hdirs = []
    ffc = {"r": (True, "fast-forwarded the product"), "heads": []}
    keep_ff = ap.evolve.ff_to  # real git is driven in the EVO block below; here only the decision is under test
    ap.evolve.ff_to = lambda p, h, d=False: ffc["heads"].append(h) or ffc["r"]

    def halt_run(set_at, commits="5", ls_extra=None, reason="owner dead and budget: older than 16.0 h", dirty=""):
        st = fresh(set_at)
        pc["n"] = commits
        sh_out["dirty"] = dirty
        ap.plan = lambda *a: hdirs.append(a[5]) or good_plan()
        rec.update(state="HALTED", reason=reason,
                   binding={"root": str(tmp / "no-tree"), "head": "d" * 40, "branch": "s9/work"})
        recp.write_text(json.dumps(rec))
        st["lanes"] = {"L": dict({"status": "RUNNING", "gen": "S90L", "base": "b0", "blank": 0, "arm_fails": 0,
                                  "mission": "m-aaaaaaaaaaaa", "planned_from": {
                                      "checkpoint": str(tmp / "ck.md"), "verdict": {"verdict": "AGREE", "notes": "k"}}},
                                 **(ls_extra or {}))}
        ap.lane_tick(st, lanes[0], False)
        return st["lanes"]["L"]
    L1 = halt_run(96)
    check("V-AP-HALT-CONTINUE", any(c[0] == "arm" for c in calls) and L1.get("continued_from") == "m-aaaaaaaaaaaa"
          and L1["status"] == "RUNNING" and any(r["kind"] == "halt_continue" for r in ledger())
          and "CONTINUATION" in hdirs[-1] and "s9/work" in hdirs[-1]
          and (L1.get("planned_from") or {}).get("checkpoint") == str(tmp / "ck.md"))
    L1 = halt_run(97, ls_extra={"continued_from": "m-older"})
    check("V-AP-HALT-CONTINUE-ONCE", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    L1 = halt_run(98, commits="0")
    check("V-AP-HALT-NOCOMMIT", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    L1 = halt_run(99, ls_extra={"planned_from": None})
    check("V-AP-HALT-NO-JUDGMENT-PARKS", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    # review 2026-11-16: M1 an explicit close is the Owner's stop; M2 the one continuation survives a failed arm
    L1 = halt_run(100, reason="owner close (HALTED): Owner stops this lane")
    check("V-AP-HALT-OWNER-CLOSE-PARKS", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    L1 = halt_run(101, dirty=" M .planning/STATE.md")
    check("V-AP-HALT-RETRY-KEEPS-ONCE", not any(c[0] == "arm" for c in calls) and "continued_from" not in L1
          and L1["status"] == "RUNNING" and L1.get("arm_fails") == 1)
    L1 = halt_run(102, ls_extra={"pending_plan": {"for": "continue:m-aaaaaaaaaaaa", "verdict": {"verdict": "AGREE"},
                                                  "bad": ["EVO RESEARCH: caps 13,000,000 > research generation cap"]}})
    check("V-AP-HALT-REPLAN-TOLD-WHY", any(c[0] == "arm" for c in calls) and "AUTOPILOT POLICY REFUSED" in hdirs[-1]
          and "caps 13,000,000" in hdirs[-1] and "CONTINUATION" in hdirs[-1])
    # 2026-11-18 (FIFA S146F): un-parked to WAITING after a refused continuation, the lane re-parked at once in silence,
    # because only a RUNNING lane was continued; the kept continuation plan now resumes, and nothing else does
    L1 = halt_run(105, ls_extra={"status": "WAITING", "pending_plan": {
        "for": "continue:m-aaaaaaaaaaaa", "verdict": {"verdict": "AGREE"}, "bad": ["lane research budget exceeded"]}})
    check("V-AP-HALT-UNPARKED-CONTINUATION-RESUMES", any(c[0] == "arm" for c in calls) and L1["status"] == "RUNNING"
          and "lane research budget exceeded" in hdirs[-1])
    L1 = halt_run(106, ls_extra={"status": "WAITING"})
    check("V-AP-HALT-WAITING-WITHOUT-PLAN-PARKS", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    # 2026-11-18 (MKW S151M): INCONCLUSIVE on a checkpoint its worker marked not final is continued once, then parks
    udirs = []

    hold_now = rec["owner_hold"]  # a cost hold here (the top-up block restores the checkpoint hold later)

    def unfinished_run(set_at, final=False, ls_extra=None):
        rec["owner_hold"] = dict(keep_hold)
        st = fresh(set_at)
        rec.update(state="RUNNING", reason="")
        recp.write_text(json.dumps(rec))
        udirs.clear()
        ap.judge = lambda *a: {"verdict": "INCONCLUSIVE", "checkpoint_final": final, "notes": "own gate red, interim",
                               "_tokens": 5}
        ap.plan = lambda *a: udirs.append(a[5]) or good_plan()
        st["lanes"] = {"L": dict({"status": "RUNNING", "gen": "S90L", "base": "b0", "blank": 0, "arm_fails": 0,
                                  "mission": "m-aaaaaaaaaaaa", "planned_from": {
                                      "checkpoint": str(tmp / "ck.md"), "verdict": {"verdict": "AGREE", "notes": "k"}}},
                                 **(ls_extra or {}))}
        ap.lane_tick(st, lanes[0], False)
        return st["lanes"]["L"]
    L1 = unfinished_run(107)
    check("V-AP-UNFINISHED-CONTINUES", any(c[0] == "arm" for c in calls) and L1["status"] == "RUNNING"
          and L1.get("unfinished_streak") == 1 and udirs and "not final" in udirs[-1] and "own gate red" in udirs[-1]
          and any(r["kind"] == "unfinished_continue" for r in ledger()))
    L1 = unfinished_run(108, ls_extra={"unfinished_streak": 1})
    check("V-AP-UNFINISHED-ONCE-THEN-PARKS", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    L1 = unfinished_run(109, final=True)
    check("V-AP-UNFINISHED-FINAL-PARKS", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    rec["owner_hold"] = hold_now
    recp.write_text(json.dumps(rec))
    # 2026-11-18 (FIFA S170F, MKW S151M): a mission settled HALTED (authority spent) with its checkpoint committed on
    # the branch is judged from that checkpoint when the lane is un-parked, instead of parking at once
    keep_cfb = ap.checkpoint_from_branch
    ap.checkpoint_from_branch = lambda p, b, h: str(tmp / "ck.md")
    L1 = halt_run(110, ls_extra={"status": "WAITING"})
    check("V-AP-TERMINAL-CHECKPOINT-JUDGED", any(c[0] == "arm" for c in calls) and L1["status"] == "RUNNING"
          and any(r["kind"] == "judge" for r in ledger()))
    # 2026-11-19 (FIFATC S118C): a halted worker on a stale side branch; discovery parks on its old checkpoint, but a
    # kept judgment that names its own checkpoint is planned from that one, never discovered nor judged
    keep_disc, keep_en = ap.evolve.discover_checkpoint, ap.evolve.enabled
    ap.evolve.discover_checkpoint = lambda *a, **k: ("PARK", "not a fast-forward of the product HEAD")
    ap.evolve.enabled = lambda home: True  # discovery runs only under EVO
    L1 = halt_run(111, ls_extra={"status": "WAITING", "pending_plan": {
        "for": "m-aaaaaaaaaaaa:terminal", "checkpoint": str(tmp / "redo.md"), "verdict": {"verdict": "AGREE"},
        "directive": "REDO from main"}})
    check("V-AP-KEPT-JUDGMENT-NAMES-ITS-CHECKPOINT", any(c[0] == "arm" for c in calls) and L1["status"] == "RUNNING"
          and (L1.get("planned_from") or {}).get("checkpoint") == str(tmp / "redo.md") and "REDO from main" in hdirs[-1]
          and not any(r["kind"] == "judge" for r in ledger()))
    L1 = halt_run(112, ls_extra={"status": "WAITING", "pending_plan": {
        "for": "m-aaaaaaaaaaaa:terminal", "verdict": {"verdict": "AGREE"}, "directive": "no checkpoint named"}})
    check("V-AP-KEPT-JUDGMENT-WITHOUT-CHECKPOINT-STILL-DISCOVERS", L1["status"] == "PARKED"
          and not any(c[0] == "arm" for c in calls))
    ap.evolve.discover_checkpoint, ap.evolve.enabled = keep_disc, keep_en
    ap.checkpoint_from_branch = keep_cfb
    # F4b (2026-11-16): the product is fast-forwarded to the halted head BEFORE the arm; refused -> park, told why
    ffc["heads"].clear()
    halt_run(103)
    check("V-AP-HALT-FF-BEFORE-ARM", ffc["heads"] == ["d" * 40] and any(c[0] == "arm" for c in calls)
          and "fast-forwarded to that commit" in hdirs[-1] and "never commit in the old work tree" in hdirs[-1])
    ffc["r"] = (False, "the branch head dddd is not a fast-forward of the product HEAD eeee")
    L1 = halt_run(104)
    check("V-AP-HALT-FF-REFUSED-PARKS", L1["status"] == "PARKED" and not any(c[0] == "arm" for c in calls)
          and "not a fast-forward" in q_text() and "continued_from" not in L1)
    ap.evolve.ff_to = keep_ff
    # F6 + F2b (2026-11-16): a RUNNING mission with no hold. Launch held >= 30 min -> one Owner line per mission and
    # reason (S71F/S69T sat 8 h unseen). < 1.5 h of wall with work on the branch -> one extension inside the envelope,
    # no token change (S65M halted on age at 07:45 with 3 commits); refused by gsd_mission -> the Owner is told first.
    def watch_run(reason="launch held: cwd not aligned with work_dir (diverged): x", held_s=3600, age_h=2.0,
                  commits="2", st=None, fail=(), env=envt, spent=1_000_000, wall=None, state="RUNNING", blocker=None):
        if st is None:
            rec["owner_hold"] = {"set_at": 0}
            st = fresh(0)
            st["lanes"] = {"L": {"status": "RUNNING", "gen": "S91L", "base": "b0", "blank": 0, "arm_fails": 0,
                                 "mission": "m-aaaaaaaaaaaa"}}
        calls.clear()
        fail_on.update(fail)
        pc["n"] = commits
        now = __import__("time").time()
        rec.pop("blocker", None)
        if blocker is not None:
            rec["blocker"] = dict({"at": now - held_s}, **blocker)  # a given `at` is the same blocker again
        rec.update(state=state, owner_hold=None, reason=reason, updated_at=now - held_s,
                   created_at=now - age_h * 3600, max_hours=16.0, authority_tokens=10_000_000,
                   cost_mark={"tokens": spent, "at": now},
                   binding={"root": str(tmp / "no-tree"), "head": "e" * 40, "branch": "s91/work"})
        recp.write_text(json.dumps(rec))
        keep_wall = ap.WALL
        ap.WALL = wall or __import__("datetime").datetime.fromtimestamp(now + 30 * 86400, __import__("datetime").timezone.utc)
        try:
            ap.lane_tick(st, dict(lanes[0], envelope=env) if env else dict(lanes[0]), False)
        finally:
            ap.WALL = keep_wall
        return st
    W = watch_run()
    check("V-AP-HELD-RUNNING-NOTICE", q_text().count("RUNNING with no worker") == 1 and not auth_calls()
          and W["lanes"]["L"]["status"] == "RUNNING")
    watch_run(st=W)
    check("V-AP-HELD-NOTICE-ONCE", q_text().count("RUNNING with no worker") == 1)
    watch_run(held_s=600)
    check("V-AP-HELD-NOTICE-WAITS", "RUNNING with no worker" not in q_text())
    # 2026-11-17 (S108W, Owner "b"): BLOCKED on a host permission prompt is told once, the lane stays RUNNING
    BLK = {"class": "HOST_GATE", "unblock_condition": {"gate": "permission prompt", "needs": "approve Bash: rm cfg"}}
    W = watch_run(reason="progress moved", state="BLOCKED", blocker=BLK)
    check("V-AP-BLOCKED-NOTICE", q_text().count("is BLOCKED for") == 1 and "approve Bash: rm cfg" in q_text()
          and W["lanes"]["L"]["status"] == "RUNNING")
    watch_run(st=W, reason="progress moved", state="BLOCKED", blocker=dict(BLK, at=rec["blocker"]["at"]))
    check("V-AP-BLOCKED-NOTICE-ONCE", q_text().count("is BLOCKED for") == 1)
    watch_run(reason="progress moved", state="BLOCKED", blocker=BLK, held_s=600)
    check("V-AP-BLOCKED-NOTICE-WAITS", "is BLOCKED for" not in q_text())
    rec.pop("blocker", None)
    W = watch_run(reason="running", age_h=15.0)
    a = auth_calls()
    check("V-AP-AGE-EXTEND-PROGRESS", len(a) == 1 and "--tokens" not in a[0] and "--extend-hours" in a[0]
          and a[0][a[0].index("--extend-hours") + 1] == "4" and a[0][a[0].index("--owner-turn") + 1] == envt["owner_turn"]
          and [r.get("extend_hours") for r in ledger() if r["kind"] == "age_extend"] == [4.0])
    watch_run(reason="running", age_h=15.0, st=W)
    check("V-AP-AGE-EXTEND-ONCE", not auth_calls())
    watch_run(reason="running", age_h=15.0, commits="0")
    check("V-AP-AGE-EXTEND-NEEDS-WORK", not auth_calls() and "age wall" not in q_text())
    watch_run(reason="running", age_h=10.0)
    check("V-AP-AGE-EXTEND-NOT-EARLY", not auth_calls())
    watch_run(reason="running", age_h=15.0, fail=("authority",))
    check("V-AP-AGE-EXTEND-REFUSED-TOLD", len(auth_calls()) == 1 and "new Owner turn" in q_text()
          and not [r for r in ledger() if r["kind"] == "age_extend"])
    fail_on.clear()
    # review 2026-11-16: MEDIUM near its cap the extension waits for cost_topup's one act; LOW the two unextendable poles
    watch_run(reason="running", age_h=15.0, spent=8_000_000)
    check("V-AP-AGE-EXTEND-DEFERS-NEAR-CAP", not auth_calls() and "age wall" not in q_text())
    watch_run(reason="running", age_h=15.0, env=None)
    check("V-AP-AGE-EXTEND-NO-ENVELOPE-TOLD", not auth_calls() and "no Owner envelope turn" in q_text())
    watch_run(reason="running", age_h=15.0,
              wall=__import__("datetime").datetime.now(__import__("datetime").timezone.utc)
              + __import__("datetime").timedelta(minutes=10))
    check("V-AP-AGE-EXTEND-WALL-CLOSE-TOLD", not auth_calls() and "programme wall is too close" in q_text())
    rec["state"] = "RUNNING"
    for k in ("reason", "binding", "updated_at", "created_at", "max_hours", "cost_mark"):
        rec.pop(k, None)
    rec["owner_hold"] = dict(keep_hold)
    check("V-AP-HOLD-SHA", ap.hold_checkpoint({"evidence": "8afbd99bb2a8f512cdc67cc7433a153ae7ca78bd", "residual": "r.md"})
          == "r.md" and ap.hold_checkpoint({"evidence": "None", "residual": "r.md"}) == "r.md")
    check("V-AP-HOLD-PATH-KEPT", ap.hold_checkpoint({"evidence": "e/ck.md", "residual": "r.md"}) == "e/ck.md")
    check("V-AP-HOLD-SHA-NONE", ap.hold_checkpoint({"evidence": "8afbd99"}) == "")
    # 2026-11-17 (S113R): prose naming the file -> the file; prose naming none -> the residual
    check("V-AP-HOLD-FREEFORM", ap.hold_checkpoint(
        {"evidence": "branch worktree-s113r commit ac2201a: evidence/ascension/s113r/checkpoint.md"})
          == "evidence/ascension/s113r/checkpoint.md"
          and ap.hold_checkpoint({"evidence": "see the run log", "residual": "r.md"}) == "r.md"
          and ap.hold_checkpoint({"evidence": "/abs/dir/ck.md"}) == "/abs/dir/ck.md")
    check("V-AP-HOLD-SHA-PATH", ap.hold_checkpoint({"evidence": "c235442:evidence/s70w/ck.md", "residual": "r.md"})
          == "evidence/s70w/ck.md")
    check("V-AP-HOLD-PATH-AT-SHA", ap.hold_checkpoint({"evidence": "evidence/s177m/ck_r1b.md@74cbfef", "residual": "r.md"})
          == "evidence/s177m/ck_r1b.md" and ap.hold_checkpoint({"evidence": "e/a@b.md"}) == "e/a@b.md")
    check("V-AP-HOLD-PATH-IN-REASON", ap.hold_checkpoint({"evidence": None, "reason": "CHECKPOINT_COMPLETE: S202K final: "
          "0 new; see evidence/ascension/s202k/checkpoint_s202k.md"}) == "evidence/ascension/s202k/checkpoint_s202k.md"
          and ap.hold_checkpoint({"reason": "wrote evidence/x/held_result.json"}) == ""
          and ap.hold_checkpoint({"reason": "see e/ck.md", "residual": "r.md"}) == "r.md")
    # 2026-11-19 (Owner: "extiende tennis y dale capacidad de autoextenderse 30 veces"): an Owner grant lets a lane lift
    # its own research-allowance, designed-lever and planner stops, each once per extension, never beyond `max`
    E = ap.evolve
    xls = {"auto_extend": {"max": 2, "used": 0, "tranche": 50_000_000, "owner_turn": "t:1"}}
    check("V-AP-AUTOEXT-BOUNDED", [E.consume_extension(xls, "a"), E.consume_extension(xls, "b"),
                                   E.consume_extension(xls, "c")] == [1, 2, 0] and xls["auto_extend"]["used"] == 2
          and E.consume_extension({}, "x") == 0)
    n0 = len([r for r in ledger() if r["kind"] == "auto_extend"])
    rls = {"research_spent": 199_500_000, "research_cap": 200_000_000,
           "auto_extend": {"max": 30, "used": 0, "tranche": 50_000_000, "owner_turn": "t:2"}}
    ax_room = {"research_spent": 10_000_000, "research_cap": 200_000_000, "auto_extend": dict(rls["auto_extend"])}
    check("V-AP-AUTOEXT-RESEARCH-ALLOWANCE", ap.extend_research_if_spent("XL", rls) and rls["research_cap"] == 250_000_000
          and rls["auto_extend"]["used"] == 1 and not ap.extend_research_if_spent("XL", ax_room)
          and ax_room["auto_extend"]["used"] == 0
          and len([r for r in ledger() if r["kind"] == "auto_extend"]) == n0 + 1 and "auto-extension 1/30" in q_text()
          and not ap.extend_research_if_spent("XL", {"research_spent": 199_500_000, "research_cap": 200_000_000}))
    sls = {"synth_streak": 3, "auto_extend": {"max": 30, "used": 0}}
    lv, why = E.synthesize({}, "XL", sls, str(tmp), "FAM", lambda fam: {"none": "nothing"}, None)
    lv2, why2 = E.synthesize({}, "XL", {"synth_streak": 3}, str(tmp), "FAM", lambda fam: {"none": "nothing"}, None)
    check("V-AP-AUTOEXT-SYNTH-MAX", lv is None and "designer proposed no lever" in why and sls["synth_streak"] == 0
          and sls["auto_extend"]["used"] == 1 and lv2 is None and "in a row" in why2)
    pls = {"status": "RUNNING", "judged_for": "m-x:1", "auto_extend": {"max": 1, "used": 0}}
    pend = {"for": "m-x:1", "verdict": {"verdict": "AGREE"}, "directive": "old"}
    ok1 = ap.extend_after_stop("XL", pls, pend, "lever exhausted: 0/97")
    ok2 = ap.extend_after_stop("XL", dict(pls, status="RUNNING"), pend, "again")
    check("V-AP-AUTOEXT-PLANNER-STOP-REPLANS", ok1 and not ok2 and pls["status"] == "WAITING" and pls["judged_for"] is None
          and pls["pending_plan"]["for"] == "m-x:1" and "lever exhausted: 0/97" in pls["pending_plan"]["directive"]
          and ap.resumable_plan(pls, "m-x:1") is not None)
    ap.sh, rec["owner_hold"], rec["authority_tokens"] = keep_sh2, keep_hold, keep_auth
    if keep_auth is None:
        rec.pop("authority_tokens")
    recp.write_text(json.dumps(rec))
    # One re-plan after a policy refusal, told why (2026-11-14: S35K/S37K/S38K/S40K/S40T each parked for hours);
    # the checks are unchanged and a second refusal parks.
    BADP = {"title": "t", "facts": [], "phases": ["Phase 1: K1 define a new profile P9 (cap 3M): x", *GOOD[1:]]}
    dirs = []

    def seq_plan(*plans):
        q = list(plans)
        return lambda lane, name, ck, prod, v, d: dirs.append(d) or dict(q.pop(0), _tokens=1)
    st = fresh(80)
    ap.plan = seq_plan(BADP, {"title": "t", "facts": [], "phases": GOOD})
    ap.lane_tick(st, lanes[0], False)
    prow = [r for r in ledger() if r["kind"] == "plan"]
    check("V-AP-REPLAN-ADMITS-SECOND", any(c[0] == "arm" for c in calls) and len(prow) == 2 and prow[1].get("replan")
          and "AUTOPILOT POLICY REFUSED" in dirs[-1] and "define a new profile P9" in dirs[-1])
    dirs.clear()
    st = fresh(81)
    per_tick, retry_ticks = 1 + ap.POLICY_REPLANS, 2  # the bound is pinned here, not read back from the module
    ap.plan = seq_plan(*[BADP] * (per_tick * (1 + retry_ticks) + 1))
    ap.lane_tick(st, lanes[0], False)
    # 2026-11-18 (Owner 'y', MKWLIB S150L): a planner-fixable refusal re-plans at the next tick, not a park
    check("V-AP-POLICY-REFUSAL-RETRIES-NEXT-TICK", st["lanes"]["L"]["status"] != "PARKED"
          and st["lanes"]["L"].get("policy_retry") == 1 and (st["lanes"]["L"].get("pending_plan") or {}).get("bad"))
    for _ in range(retry_ticks):
        ap.lane_tick(st, lanes[0], False)
    check("V-AP-REPLAN-BOUNDED-THEN-PARKS", st["lanes"]["L"]["status"] == "PARKED" and not any(c[0] == "arm" for c in calls)
          and len([r for r in ledger() if r["kind"] == "plan"]) == per_tick * (1 + retry_ticks)
          and "| line:" in q_text() and len([r for r in ledger() if r["kind"] == "judge"]) <= 1)
    # S41K: the 1st re-plan fixed the profile line but left a phase without a cap; that phase is named to the planner
    NOCAP = {"title": "t", "facts": [], "phases": [GOOD[0], "Phase 2: K2 closeout: re-run gates and write the checkpoint"]}
    dirs.clear()
    st = fresh(82)
    ap.plan = seq_plan(BADP, NOCAP, {"title": "t", "facts": [], "phases": GOOD})
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-REPLAN-SECOND-FIXES-CAP", any(c[0] == "arm" for c in calls) and len(dirs) == 3
          and "K2 closeout: re-run gates" in dirs[2])
    # S39K (2026-11-14, Owner "y"): the un-park after a policy refusal re-plans from the kept judgment; the judge is
    # not called again, so one result is credited once. A new hold on the lane is judged as always.
    jn = {"n": 0}
    st = fresh(84)
    keep_judge = ap.judge  # fresh() installs the good judge; count its calls

    def count_judge(*a):
        jn["n"] += 1
        return keep_judge(*a)
    ap.judge = count_judge
    ap.plan = seq_plan(*[BADP] * (1 + ap.POLICY_REPLANS))
    keep_rt, ap.POLICY_RETRY_TICKS = ap.POLICY_RETRY_TICKS, 0  # the park path itself (the retries are pinned above)
    ap.lane_tick(st, lanes[0], False)
    ap.POLICY_RETRY_TICKS = keep_rt
    kept = st["lanes"]["L"].get("pending_plan") or {}
    check("V-AP-REFUSAL-KEEPS-JUDGMENT", st["lanes"]["L"]["status"] == "PARKED" and kept.get("for", "").endswith(":84")
          and kept.get("verdict", {}).get("verdict") == "AGREE" and "_tokens" not in kept.get("verdict", {}))
    st["lanes"]["L"].update(status="WAITING", judged_for=None)  # the Owner's un-park, as done by hand
    calls.clear()
    dirs.clear()
    ap.plan = seq_plan({"title": "t", "facts": [], "phases": GOOD})
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-UNPARK-REPLANS-WITHOUT-REJUDGE", jn["n"] == 1 and any(c[0] == "arm" for c in calls)
          and len([r for r in ledger() if r["kind"] == "replan_resume"]) == 1
          and "AUTOPILOT POLICY REFUSED" in dirs[0] and "pending_plan" not in st["lanes"]["L"])
    st = fresh(85)
    ap.judge = count_judge
    st["lanes"] = {"L": {"status": "WAITING", "blank": 0, "arm_fails": 0, "gen": None,
                         "pending_plan": dict(kept)}}  # kept for hold 84; the lane now holds 85
    ap.plan = seq_plan({"title": "t", "facts": [], "phases": GOOD})
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-NEW-HOLD-IS-JUDGED", jn["n"] == 2 and any(c[0] == "arm" for c in calls))
    ap.judge = keep_judge
    st = fresh(4)
    ap.judge = lambda *a: dict(full, new_canonical_certs=3, _tokens=None)
    ap.plan = lambda *a: {"title": "t", "facts": [], "phases": GOOD, "_tokens": None}
    ap.lane_tick(st, lanes[0], False)
    rows = ledger()
    check("V-AP-UNMEASURED-JUDGE-PLAN-BOOKED", [r["tokens"] for r in rows if r["kind"] in ("judge", "plan")]
          == [2_000_000, 2_000_000])
    st = fresh(5)
    ap.judge = lambda *a: dict(full, new_canonical_certs=0, validated_capability=False, _tokens=5)
    for k in range(3):
        st.setdefault("lanes", {}).setdefault("L", {})["judged_for"] = None
        st["lanes"]["L"]["status"] = "WAITING"
        rec["owner_hold"]["set_at"] = k + 10
        recp.write_text(json.dumps(rec))
        st["lanes"]["L"]["mission"] = "m-aaaaaaaaaaaa"
        ap.lane_tick(st, lanes[0], False)
    check("V-AP-THREE-BLANK-STOPS", st["lanes"]["L"]["status"] == "STOPPED")
    st = fresh(99)
    ap.lane_tick(st, lanes[0], False)
    acts = [c[0] for c in calls]
    check("V-AP-ARM-SEQUENCE", acts == ["close", "arm", "hold", "authority", "release"]
          and st["lanes"]["L"]["status"] == "RUNNING" and st["lanes"]["L"]["mission"] == "m-bbbbbbbbbbbb"
          and "pending_arm" not in st["lanes"]["L"])
    auth = [c for c in calls if c[0] == "authority"][0]
    check("V-AP-AUTHORITY-IS-PHASE-CAPS", auth[auth.index("--tokens") + 1] == str(15_000_000))
    check("V-AP-OWNER-TURN-PASSED", "--owner-turn" in auth)
    check("V-AP-RESERVE-BOOKED", sum(r["tokens"] for r in ledger() if r["kind"] == "arm_reserve") == 15_000_000)
    st = fresh(100)
    sh_out["dirty"] = " M .planning/STATE.md"
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-DIRTY-NO-MISSION-ACT", not calls and st["lanes"]["L"]["status"] != "PARKED"
          and st["lanes"]["L"]["arm_fails"] == 1)
    # 2026-11-14 (Owner 'y', pane c26eafbf): a RETRY keeps the judgment; the next tick re-plans from it and does
    # not call the judge again, so the checkpoint's class and graph credit are counted once
    check("V-AP-RETRY-KEEPS-JUDGMENT", (st["lanes"]["L"].get("pending_plan") or {}).get("for", "").endswith(":100"))
    _jr, _kj = {"n": 0}, ap.judge
    ap.judge = lambda *a: (_jr.__setitem__("n", _jr["n"] + 1), _kj(*a))[1]
    sh_out["dirty"] = ""
    calls.clear()
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-RETRY-REARMS-WITHOUT-REJUDGE", _jr["n"] == 0 and any(c[0] == "arm" for c in calls)
          and len([r for r in ledger() if r["kind"] == "judge"]) == 1
          and len([r for r in ledger() if r["kind"] == "replan_resume"]) == 1)
    ap.judge = _kj
    # 2026-11-14 (Owner 'y', pane 4de9b293): MKW's first arm failed twice on `git add` of an archive dir never created
    # (a new lane has no .planning); then its commit failed unseen for lack of a git identity, and the staged tree it
    # left held the worker's relaunch for 3.5 h
    shc, base_sh = {"rc": {}, "log": []}, ap.sh

    def rec_sh(cmd, **k):
        shc["log"].append([str(c) for c in cmd])
        for key, rc in shc["rc"].items():
            if key in cmd:
                return (rc, f"{key} refused")
        return base_sh(cmd, **k)
    ap.sh = rec_sh
    st = fresh(106)
    shc["log"] = []
    ap.lane_tick(st, lanes[0], False)
    adds = [c for c in shc["log"] if "add" in c and "-A" in c]  # the arm's own add (a later step adds .planning)
    check("V-AP-ARM-NO-PLANNING-ADDS-PACKET-ONLY", not (Path(lanes[0]["cwd"]) / ".planning/STATE.md").exists()
          and len(adds) == 1 and not any("archived" in a for a in adds[0])
          and any(a.endswith(".md") for a in adds[0]) and any(c[0] == "arm" for c in calls))
    st = fresh(107)
    shc["rc"], shc["log"] = {"var": 128}, []
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-ARM-NO-GIT-IDENT-NO-MUTATION", not calls and st["lanes"]["L"]["arm_fails"] == 1
          and not any(x in c for c in shc["log"] for x in ("mv", "add", "commit")))
    st = fresh(108)
    shc["rc"], shc["log"] = {"commit": 1}, []
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-ARM-COMMIT-FAIL-NO-MISSION-ACT", not calls and st["lanes"]["L"]["arm_fails"] == 1
          and "git commit failed" in (tmp / "home" / "autopilot.log").read_text())
    ap.sh = base_sh
    st = fresh(101)
    fail_on.add("authority")
    ap.lane_tick(st, lanes[0], False)
    acts = [c[0] for c in calls]
    check("V-AP-AUTHORITY-FAIL-STAYS-HELD-PARKS", acts == ["close", "arm", "hold", "authority"]
          and st["lanes"]["L"]["status"] == "PARKED" and sum(r["tokens"] for r in ledger()
                                                            if r["kind"] in ("arm_reserve", "arm_refund")) == 0)
    st = fresh(102)
    fail_on.add("hold")
    ap.lane_tick(st, lanes[0], False)
    acts = [c[0] for c in calls]
    check("V-AP-HOLD-FAIL-HALTS-NEW", acts[-1] == "close" and "HALTED" in calls[-1] and "authority" not in acts
          and st["lanes"]["L"]["status"] == "PARKED")
    st = fresh(103)
    st = {"lanes": {"L": {"status": "WAITING", "pending_arm": {"gen": "S30K", "step": "arm"}}}}
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-INTERRUPTED-ARM-PARKS", st["lanes"]["L"]["status"] == "PARKED" and not calls)
    st = fresh(104)
    ap.plan = lambda *a: {"title": "t", "facts": ["then push the branch to origin"], "phases": GOOD, "_tokens": 7}
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-POLICY-BLOCKS-ARM-VIA-FACTS", st["lanes"]["L"]["status"] != "RUNNING" and not calls
          and "push" in json.dumps(st["lanes"]["L"].get("pending_plan") or {}))
    st = fresh(105)
    ap.lane_tick(st, dict(lanes[0], protected=[{"path": str(pf), "sha256_prefix": "00000000"}]), False)
    check("V-AP-PROTECTED-OVERRULES-AGREE", st["lanes"]["L"]["status"] == "PARKED" and not calls)
    # ---- progress rules on the lane (classification stubbed here; the classes themselves are tested above)
    orig_cls = ap.classify_progress

    def seq(classes, base):
        st = fresh(base)
        for k, c in enumerate(classes):
            ls = st.setdefault("lanes", {}).setdefault("L", {})
            if ls.get("status") in ("PARKED", "STOPPED"):
                break
            ap.classify_progress = (lambda c: (lambda v, p, b=None, lane=None: (c, "")))(c)
            ls.update(judged_for=None, status="WAITING", mission="m-aaaaaaaaaaaa")
            (tmp / "home" / "ledger.jsonl").unlink(missing_ok=True)  # the day cap is tested elsewhere
            rec["owner_hold"]["set_at"] = base * 100 + k
            recp.write_text(json.dumps(rec))
            ap.lane_tick(st, lanes[0], False)
        ap.classify_progress = orig_cls
        q = tmp / "home" / "owner_queue.md"
        return st["lanes"]["L"], (q.read_text() if q.exists() else "")
    ls, q = seq(["INFORMATION", "INFORMATION"], 200)
    check("V-AP-INFO-TWICE-PARKS", ls["status"] == "PARKED" and "research without conversion" in q)
    check("V-AP-PARK-STARTS-FRESH-WINDOW", ls.get("info_streak") == 0 and ls.get("no_conversion") == 0
          and ls.get("judged_for") is None)
    # a checkpoint whose arm waits for the next day is judged again: its class must not be counted twice
    st = fresh(205)
    import time as _t
    # 30M of day headroom whatever the cap (was a literal 50M, tuned to the 80M cap; DAY_CAP 90M left it never waiting)
    (tmp / "home" / "ledger.jsonl").write_text(json.dumps({"ts": _t.time(), "tokens": ap.DAY_CAP - 30_000_000}) + "\n")
    ap.judge = lambda *a: dict(full, _tokens=20_000_000)
    ap.classify_progress = lambda v, p, b=None, lane=None: ("INFORMATION", "")
    ap.lane_tick(st, lanes[0], False)
    ap.classify_progress = orig_cls
    lsd = st["lanes"]["L"]
    check("V-AP-DAY-WAIT-DOES-NOT-DOUBLE-COUNT", lsd.get("status") != "PARKED" and lsd.get("judged_for") is None
          and lsd.get("info_streak", 0) == 0 and not any(c[0] == "arm" for c in calls))
    ls, q = seq(["INFORMATION", "NONE", "INFORMATION"], 201)
    check("V-AP-NO-CONVERSION-PARKS", ls["status"] == "PARKED" and "without a certificate or capability" in q)
    ls, q = seq(["NONE", "NONE", "CERT", "NONE", "NONE"], 202)
    check("V-AP-CERT-RESETS-STREAKS", ls["status"] == "RUNNING" and not q)
    ls, q = seq(["INFORMATION", "CAPABILITY", "INFORMATION"], 203)
    check("V-AP-INFO-AFTER-CAPABILITY-CONTINUES", ls["status"] == "RUNNING" and not q)
    st = fresh(204)
    (tmp / "home" / "ledger.jsonl").write_text(json.dumps({"ts": now - 86400, "tokens": 70_000_000}) + "\n")
    judged = []
    ap.judge = lambda *a: judged.append(a) or dict(full, _tokens=1)
    _keep_u = ap.UNLOCKED_CAP; ap.UNLOCKED_CAP = 285_261_779  # Owner released all frozen 2026-11-12; test the mechanism
    ap.lane_tick(st, lanes[0], False)
    ap.UNLOCKED_CAP = _keep_u
    check("V-AP-FROZEN-PARKS-BEFORE-JUDGE", st["lanes"]["L"]["status"] == "PARKED" and not judged and not calls)
    # ---- kill switch: the judge must not even be called
    st = fresh(106)
    (tmp / "home" / "OFF").write_text("")
    (tmp / "home" / "lanes.json").write_text(json.dumps(lanes))
    judged = []
    ap.judge = lambda *a: judged.append(a) or {"verdict": "DISAGREE"}
    ap.main(["x", "tick"])
    check("V-AP-KILL-SWITCH", not judged and not calls and not (tmp / "home" / "state.json").exists())
    (tmp / "home" / "OFF").unlink()
    # ---- dry-tick writes nothing real
    st = fresh(107)
    (tmp / "home" / "state.json").write_text('{"lanes": {}}')
    (tmp / "home" / "ledger.jsonl").write_text('{"kind": "x", "tokens": 1, "ts": 1}\n')
    before = [(tmp / "home" / f).read_bytes() for f in ("state.json", "ledger.jsonl")]
    m2 = load()  # an unstubbed module for the real dry path (gm -> sh(dry=True))
    for attr in ("killed", "tempfile", "protected_check", "agree_supported"):
        setattr(m2, attr, getattr(ap, attr))  # carry this run's mutation, if any
    m2.sh = lambda cmd, **k: (0, "")
    m2.main(["x", "dry-tick"])
    after = [(tmp / "home" / f).read_bytes() for f in ("state.json", "ledger.jsonl")]
    scratch = json.loads((m2.OUT / "state.json").read_text()) if (m2.OUT / "state.json").exists() else {}
    check("V-AP-DRY-TICK-WRITES-NOTHING-REAL", before == after and m2.OUT != m2.HOME
          and scratch.get("lanes", {}).get("L", {}).get("status") == "RUNNING")

    # ---- EVO (Owner "y" 2026-11-12): instrument failure, stagnation -> research, continuity
    E = ap.evolve
    orig_vif = E.verify_instrument_failures
    import subprocess as _sp
    os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

    def git(d, *a):
        return _sp.run(["git", "-C", str(d), *a], capture_output=True, text=True).stdout.strip()

    # 2026-11-16 (stall fixes): every run_all after the first used to die here on FileExistsError, so EVERY mutant was
    # "killed" by a crash, never by its own test. Each run now starts from clean scratch repos and work trees.
    for old in tmp.glob("evo_*"):
        __import__("shutil").rmtree(old, ignore_errors=True)

    def mkrepo(name):
        d = tmp / name
        d.mkdir()
        git(d, "init", "-q", "-b", "main")
        (d / "a.txt").write_text("a\n")
        git(d, "add", "-A"); git(d, "commit", "-q", "-m", "c0")
        return d
    # instrument failures are verified in git (window, file changed by the commit, data file, INSTRUMENT_FAIL in its body)
    ir = mkrepo("evo_instr")
    c0 = git(ir, "rev-parse", "HEAD")
    (ir / "neg.jsonl").write_text('{"verdict": "INSTRUMENT_FAIL (positive control failed)"}\n')
    (ir / "ok.jsonl").write_text('{"verdict": "REFUTED"}\n')
    git(ir, "add", "-A"); git(ir, "commit", "-q", "-m", "c1")
    c1 = git(ir, "rev-parse", "HEAD")
    claim = lambda f, c: {"instrument_failures": [{"instrument": "ctl", "file": f, "commit": c}]}  # noqa: E731
    apr = load()  # the git helpers unstubbed (this run's ap.sh is a stub)
    check("V-EVO-INSTRUMENT-VERIFIED", orig_vif(claim("neg.jsonl", c1), str(ir), c0, apr) == ["ctl"])
    check("V-EVO-INSTRUMENT-OUTSIDE-WINDOW", orig_vif(claim("neg.jsonl", c1), str(ir), c1, apr) == [])
    check("V-EVO-INSTRUMENT-NOT-A-FAILURE", orig_vif(claim("ok.jsonl", c1), str(ir), c0, apr) == [])
    check("V-EVO-CLASSIFY", E.classify("NONE", ["ctl"]) == "INSTRUMENT_FAIL" and E.classify("INFORMATION", ["ctl"]) == "INFORMATION"
          and E.classify("NONE", []) == "NONE")

    LA = {"id": "lev_a", "family": "F1", "blockers": ["B1"], "requires": [], "cost": 1, "status": "open", "what": "a"}
    LB = {"id": "lev_b", "family": "F2", "blockers": ["B1"], "requires": [], "cost": 5, "status": "open", "what": "b"}
    LC = {"id": "lev_c", "family": "F1", "blockers": ["B1"], "requires": [], "cost": 0, "status": "open", "what": "c"}
    LX = {"id": "lev_x", "family": "F3", "blockers": ["B1"], "requires": ["missing/x.json"], "cost": 0, "status": "open"}
    LR = {"id": "lev_r", "family": "REPAIR", "kind": "repair", "blockers": ["CTL"], "repairs": ["lev_a"], "requires": [],
          "cost": 1, "status": "open"}
    RES = {"title": "r", "facts": [], "phases": [
        "Phase 1: X1 lev_b discriminating test (cap 3M): rival hypotheses A and B, positive control, decision rule frozen "
        "in a commit before any run; gate tools/test_x1.py with planted mutants",
        "Phase 2: X2 checkpoint (cap 2M): re-run gates, write the checkpoint file stating new canonical certificates per "
        "profile by function identity, CHECKPOINT_COMPLETE"]}
    REP = {"title": "p", "facts": [], "phases": [
        "Phase 1: F1 lev_r repaired instrument (cap 3M): positive control demonstrated at freeze, thresholds unchanged; "
        "gate tools/test_f1.py with planted mutants",
        "Phase 2: F2 checkpoint (cap 2M): re-run gates, write the checkpoint file stating new canonical certificates per "
        "profile by function identity, CHECKPOINT_COMPLETE"]}
    GOODP = {"title": "g", "facts": [], "phases": GOOD}
    ctr = [0]

    def evo_fresh(levers, lane_state=None, plans=(GOODP,)):
        fresh(7000 + ctr[0])
        for f in ("EVO_OFF", "method_graph.json"):
            (tmp / "home" / f).unlink(missing_ok=True)
        (tmp / "home" / "levers.json").write_text(json.dumps({"L": levers}))
        seqp = list(plans)
        ap.plan = lambda *a: dict(seqp.pop(0) if len(seqp) > 1 else seqp[0], _tokens=1)
        return {"lanes": {"L": dict({"status": "WAITING", "mission": "m-aaaaaaaaaaaa", "blank": 0, "arm_fails": 0},
                                    **(lane_state or {}))}}

    def evo_run(st, classes, instr=()):
        E.verify_instrument_failures = lambda *a: list(instr)
        for c in classes:
            ls = st["lanes"]["L"]
            if ls.get("status") in ("PARKED", "STOPPED"):
                break
            ctr[0] += 1
            ap.classify_progress = (lambda c: (lambda v, p, b=None, lane=None: (c, "")))(c)
            ls.update(judged_for=None, status="WAITING", mission="m-aaaaaaaaaaaa")
            (tmp / "home" / "ledger.jsonl").unlink(missing_ok=True)
            rec["owner_hold"]["set_at"] = 7000 + ctr[0]
            recp.write_text(json.dumps(rec))
            ap.lane_tick(st, lanes[0], False)
        ap.classify_progress = orig_cls
        E.verify_instrument_failures = orig_vif
        q = tmp / "home" / "owner_queue.md"
        return st["lanes"]["L"], (q.read_text() if q.exists() else "")

    ls, q = evo_run(evo_fresh([LA, LB, LC, LX, LR], {"lever": "lev_a"}, (GOODP, RES)), ["INFORMATION", "INFORMATION"])
    check("V-EVO-PLATEAU-ENTERS-RESEARCH", ls["status"] == "RUNNING" and ls.get("mode") == "RESEARCH" and ls.get("lever") == "lev_b"
          and int(ls.get("research_spent") or 0) == 5_000_000)
    # E5 (2026-11-12): a selection decided by a learned edge must say so in its ledger row, and one decided by cost/id
    # alone must not claim an edge. lev_b2 costs more than lev_b, so only the learned edge B1 -> lev_b2 can pick it.
    LB2 = {"id": "lev_b2", "family": "F4", "blockers": ["B1"], "requires": [], "cost": 9, "status": "open", "what": "b2"}

    def sel_row():
        rows = [json.loads(x) for x in (tmp / "home" / "ledger.jsonl").read_text().splitlines() if x.strip()]
        return next((r for r in reversed(rows) if r.get("kind") == "evo_decision" and r.get("lever")), {})
    st_g = evo_fresh([LA, LB, LB2], {"lever": "lev_a"}, (RES,))
    (tmp / "home" / "method_graph.json").write_text(json.dumps({"paths": [["B1", ["lev_b2"]]]}))
    evo_run(st_g, ["INFORMATION", "INFORMATION"])
    r = sel_row()
    sel = r.get("selection") or {}
    check("V-EVO-SELECTION-CITES-LEARNED-EDGE", r.get("lever") == "lev_b2" and sel.get("prior", 0) > 0
          and [e[:2] for e in sel.get("edges", [])] == [["B1", "lev_b2"]])
    evo_run(evo_fresh([LA, LB, LB2], {"lever": "lev_a"}, (RES,)), ["INFORMATION", "INFORMATION"])
    r = sel_row()
    check("V-EVO-SELECTION-NO-EDGE-WITHOUT-GRAPH", r.get("lever") == "lev_b"
          and r.get("selection") == {"prior": 0.0, "edges": []})
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a"}), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SAME-FAMILY-NEVER-CHOSEN", ls["status"] == "PARKED" and "another family" in q)
    ls, q = evo_run(evo_fresh([LA, LX], {"lever": "lev_a"}), ["INFORMATION", "INFORMATION"])
    check("V-EVO-PRECONDITION-REQUIRED", ls["status"] == "PARKED" and "another family" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a"}), ["INFORMATION", "INFORMATION"])
    check("V-EVO-RESEARCH-PACKET-NEEDS-DISCRIMINATING-TEST", ls["status"] != "RUNNING"
          and "no 'rival'" in json.dumps(ls.get("pending_plan") or {}))
    # 2026-11-17 (Owner 'y', pane 08cba76c): an Owner-set per-lane research_cap replaces the 100M default, both ways
    ph = ["P1 lev_a " + " ".join(E.RESEARCH_WORDS)]
    spent = {"research_spent": E.RESEARCH_LANE_CAP - 1_000_000}
    over = E.packet_problems("RESEARCH", "lev_a", ph, 2_000_000, dict(spent))
    raised = E.packet_problems("RESEARCH", "lev_a", ph, 2_000_000, dict(spent, research_cap=E.RESEARCH_LANE_CAP + 50_000_000))
    check("V-EVO-LANE-RESEARCH-CAP-RAISED", any("research budget" in b for b in over) and raised == []
          and E.lane_research_cap({"research_cap": "junk"}) == E.RESEARCH_LANE_CAP)
    # 2026-11-17 (S112T, S114M, Owner "b"): an EVO packet refusal is re-planned with its reasons, not parked at once
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a"}, (GOODP, GOODP, RES)), ["INFORMATION", "INFORMATION"])
    rp = [r for r in ledger() if r["kind"] == "plan" and r.get("replan")]
    check("V-EVO-REFUSAL-REPLANNED", ls["status"] == "RUNNING" and ls.get("mode") == "RESEARCH"
          and ls.get("lever") == "lev_b" and len(rp) == 1)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, (RES,)), ["NONE", "NONE"])
    check("V-EVO-RESEARCH-STOP-RULE", ls["status"] == "PARKED" and "research stop rule" in q)
    # Owner 2026-11-16 (pane 08cba76c, "deberia haberse hecho de forma autonoma"): where a lane would park for want of a
    # lever, the autopilot designs one from the residual, admits it deterministically, persists it and researches.
    SYN = {"id": "lev_syn", "family": "F9", "blockers": ["B1"], "requires": [], "cost": 1,
           "what": "Designed from ck.md: " + "build the instrument, rival A vs B, positive control on known ids, frozen "
                   "decision rule, fresh held-out draw. " * 3}
    RES_S = dict(RES, phases=[x.replace("lev_b", "lev_syn") for x in RES["phases"]])
    designed = []

    def with_designer(lever):
        ap.design_lever = lambda lane, ck, prod, fam, refused=None: designed.append((ck, fam)) or (
            dict(lever) if lever else None)

    def lever_file():
        return json.loads((tmp / "home" / "levers.json").read_text()).get("L", [])
    with_designer(SYN)
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a"}, (RES_S,)), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SYNTH-PLATEAU", ls["status"] == "RUNNING" and ls.get("mode") == "RESEARCH" and ls.get("lever") == "lev_syn"
          and designed and designed[-1][1] == "F1" and ls.get("synth_streak") == 1)
    check("V-EVO-SYNTH-PERSISTED", any(x.get("id") == "lev_syn" and x.get("origin") == "autopilot" for x in lever_file())
          and "NOTICE" in q)
    with_designer(dict(SYN, family="F1"))
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a"}, (RES_S,)), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SYNTH-SAME-FAMILY-REFUSED", ls["status"] == "PARKED" and "designed lever refused" in q
          and not any(x.get("id") == "lev_syn" for x in lever_file()))
    with_designer(dict(SYN, what="no residual named here; " * 20))
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a"}, (RES_S,)), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SYNTH-MUST-CITE-RESIDUAL", ls["status"] == "PARKED" and "does not cite" in q)
    # 2026-11-18 (Owner 'y', KSR parked on "id ksr_handsource_regalloc already exists"): one second design, told why
    retold = []
    ap.design_lever = lambda lane, ck, prod, fam, refused=None: retold.append(refused) or (
        dict(SYN, id="lev_syn2") if refused else dict(SYN, id="lev_a"))
    RES_S2 = dict(RES, phases=[x.replace("lev_b", "lev_syn2") for x in RES["phases"]])
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a"}, (RES_S2,)), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SYNTH-REDESIGN-ON-REFUSAL", ls["status"] == "RUNNING" and ls.get("lever") == "lev_syn2"
          and len(retold) == 2 and "already exists" in "; ".join(retold[1] or []))
    with_designer(SYN)
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a", "synth_streak": 3}, (RES_S,)), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SYNTH-BOUNDED", ls["status"] == "PARKED" and "in a row" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, (RES, RES_S)), ["NONE", "NONE"])
    check("V-EVO-SYNTH-RESEARCH-STOP", ls["status"] == "RUNNING" and ls.get("lever") == "lev_syn")
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, ({"stop": "no route"}, RES_S)),
                    ["INFORMATION"])
    check("V-EVO-SYNTH-PLANNER-STOP", ls["status"] == "RUNNING" and ls.get("lever") == "lev_syn")
    # 2026-11-17 (Owner "arreglalo", KSR S143K): a planner stop on a POLICY RE-PLAN designs a lever too, then plans it
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, (GOODP, {"stop": "no route"}, RES_S)),
                    ["INFORMATION"])
    check("V-EVO-SYNTH-REPLAN-STOP", ls["status"] == "RUNNING" and ls.get("lever") == "lev_syn")
    with_designer(None)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, (GOODP, {"stop": "no route"}, RES_S)),
                    ["INFORMATION"])
    check("V-EVO-REPLAN-STOP-NO-DESIGN-PARKS", ls["status"] == "PARKED" and "re-plan stopped" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, ({"stop": "no route"},)), ["INFORMATION"])
    check("V-EVO-SYNTH-NONE-STOPS-AS-BEFORE", ls["status"] == "STOPPED" and "designer proposed no lever" in
          (tmp / "home" / "ledger.jsonl").read_text())
    ap.design_lever = lambda *a, **k: None
    ls, q = evo_run(evo_fresh([LA, LR], {"lever": "lev_a"}, (REP,)), ["NONE", "NONE"], ["ctl_pool"])
    check("V-EVO-INSTRUMENT-FAIL-NOT-NEGATIVE", ls["status"] == "RUNNING" and ls.get("mode") == "REPAIR"
          and ls.get("blank") == 0 and ls.get("no_conversion", 0) == 0 and ls.get("repair") == {"ctl_pool": 2})
    st_rep = {"lanes": {"L": ls}}
    ls, q = evo_run(st_rep, ["NONE"], ["ctl_pool"])
    check("V-EVO-REPAIR-CAP-PARKS", ls["status"] == "PARKED" and "repair cap" in q)
    # S31T -> S33T (2026-11-12): the judge's instrument names embed the measurement; a repeat failure with another n
    # must count against the SAME instrument, and two names of one instrument in one judgment are one failure
    st_k = evo_fresh([LA, LR], {"lever": "lev_a"}, (REP,))
    for n in ("2", "12", "5"):
        ls, q = evo_run(st_k, ["NONE"], [f"H-X1 control pool (frozen rule, n={n}<22)"])
    check("V-EVO-REPAIR-KEY-IGNORES-MEASUREMENT", ls["status"] == "PARKED" and "repair cap" in q and "H-X1" in q)
    ls, q = evo_run(evo_fresh([LA, LR], {"lever": "lev_a"}, (REP,)), ["NONE"],
                    ["H-X1 control pool (n=2<22)", "H-X1 negative row (INSTRUMENT_FAIL)"])
    check("V-EVO-REPAIR-ONE-COUNT-PER-JUDGMENT", ls.get("repair") == {"H-X1": 1} and ls.get("mode") == "REPAIR")
    ls, q = evo_run(evo_fresh([LA, LR], {"lever": "lev_a", "repair": {"H-X1 control pool (n=2<22)": 1,
                                                                     "H-X1 negative row (INSTRUMENT_FAIL)": 1}}, (REP,)),
                    ["NONE"], ["H-X1 control pool (n=12<22)"])
    check("V-EVO-REPAIR-LEGACY-KEYS-FOLD", ls.get("repair") == {"H-X1": 2})
    # 2026-11-15 (KSR S50K, S62K): a repair lever repairs only the instrument it declares (by id or shared blocker); with
    # none for the failed lever, the repair stays on that lever in REPAIR mode, not on a repair lever with no work
    LRZ = dict(LR, id="lev_rz", repairs=["lev_z"])
    LRB = dict(LR, id="lev_rb", repairs=[], blockers=["B1"])
    REPA = dict(REP, phases=[p.replace("lev_r", "lev_a") for p in REP["phases"]])
    REPB = dict(REP, phases=[p.replace("lev_r", "lev_rb") for p in REP["phases"]])
    ls, q = evo_run(evo_fresh([LA, LRZ], {"lever": "lev_a"}, (REPA,)), ["NONE"], ["ctl"])
    check("V-EVO-REPAIR-LEVER-MATCHES-INSTRUMENT", ls["status"] == "RUNNING" and ls.get("mode") == "REPAIR"
          and ls.get("lever") == "lev_a")
    ls, q = evo_run(evo_fresh([LA, LRZ, LRB], {"lever": "lev_a"}, (REPB,)), ["NONE"], ["ctl"])
    check("V-EVO-REPAIR-LEVER-BY-SHARED-BLOCKER", ls["status"] == "RUNNING" and ls.get("mode") == "REPAIR"
          and ls.get("lever") == "lev_rb")
    ls, q = evo_run(evo_fresh([dict(LA, status="retired"), LRZ], {"lever": "lev_a"}, (REPA,)), ["NONE"], ["ctl"])
    check("V-EVO-REPAIR-NO-LEVER-PARKS", ls["status"] == "PARKED" and "no repair lever" in q)
    # Owner-directed method transition (2026-11-13, TENNIS parked on H-T1a x2): with owner_resume=research the lane
    # leaves the closed instrument for a lever of another family instead of parking on the repair cap; one-shot.
    ls, q = evo_run(evo_fresh([LA, LB, LR], {"lever": "lev_a", "repair": {"ctl": 2}, "owner_resume": "research"},
                              (RES,)), ["NONE"], ["ctl"])
    check("V-EVO-OWNER-RESUME-RESEARCH", ls["status"] == "RUNNING" and ls.get("mode") == "RESEARCH"
          and ls.get("lever") == "lev_b" and ls.get("repair") == {} and "owner_resume" not in ls)
    ls, q = evo_run(evo_fresh([LA, LB, LR], {"lever": "lev_a", "repair": {"ctl": 2}}, (RES,)), ["NONE"], ["ctl"])
    check("V-EVO-OWNER-RESUME-CONTROL-PARKS", ls["status"] == "PARKED" and "repair cap" in q)
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a", "owner_resume": "research"}, (RES,)), ["NONE"], ["ctl"])
    check("V-EVO-OWNER-RESUME-SAME-FAMILY-PARKS", ls["status"] == "PARKED" and "Owner resume" in q)
    # owner_resume="research:<id>" (2026-11-14): the named lever wins over a higher-ranked one; a bad name parks
    LD = dict(LB, id="lev_d", cost=99)
    RESD = dict(RES, phases=[p.replace("lev_b", "lev_d") for p in RES["phases"]])
    ls, q = evo_run(evo_fresh([LA, LB, LD], {"lever": "lev_a", "owner_resume": "research:lev_d"}, (RESD,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-NAMED-LEVER", ls["status"] == "RUNNING" and ls.get("lever") == "lev_d"
          and ls.get("mode") == "RESEARCH" and "owner_resume" not in ls)
    ls, q = evo_run(evo_fresh([LA, LB, LC], {"lever": "lev_a", "owner_resume": "research:lev_c"}, (RES,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-NAMED-SAME-FAMILY-PARKS", ls["status"] == "PARKED" and "lev_c" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a", "owner_resume": "research:nope"}, (RES,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-NAMED-UNKNOWN-PARKS", ls["status"] == "PARKED" and "nope" in q)
    # owner_resume="design" (Owner 2026-11-17 "que diseñe otra palanca", WSR parked on the pivot rule): the designer is
    # called even with an open lever of another family (lev_b), and the Owner's look clears the SYNTH_MAX streak
    with_designer(SYN)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a", "owner_resume": "design", "synth_streak": 3}, (RES_S,)),
                    ["NONE"])
    check("V-EVO-OWNER-RESUME-DESIGN", ls["status"] == "RUNNING" and ls.get("lever") == "lev_syn"
          and ls.get("mode") == "RESEARCH" and ls.get("synth_streak") == 1 and "owner_resume" not in ls)
    with_designer(dict(SYN, family="F1"))
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a", "owner_resume": "design"}, (RES_S,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-DESIGN-REFUSED-PARKS", ls["status"] == "PARKED" and "designed lever refused" in q)
    # 2026-11-17 (Owner "deberia haber sido autonomo", MKW STOPPED at 17:30Z): the no-progress rule designs a lever;
    # with none admitted it parks for a look and never STOPS the lane
    with_designer(SYN)
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a", "blank": 2}, (RES_S,)), ["NONE"])
    check("V-EVO-BLANK-RULE-DESIGNS", ls["status"] == "RUNNING" and ls.get("lever") == "lev_syn"
          and ls.get("mode") == "RESEARCH" and ls.get("blank") == 0)
    ap.design_lever = lambda *a, **k: None
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a", "blank": 2}, (RES_S,)), ["NONE"])
    check("V-EVO-BLANK-RULE-PARKS-NOT-STOPS", ls["status"] == "PARKED" and "no verified progress" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH", "info_streak": 1}), ["CERT"])
    check("V-EVO-CERT-RETURNS-TO-EXPLOIT", ls["status"] == "RUNNING" and ls.get("mode") == "EXPLOIT")
    # SPEC-match-exploit B: an objdiff MATCH is a conversion, exploited on the same lever with an exploit directive
    seen_dir = []
    keep_plan = ap.plan
    st_m = evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH", "no_conversion": 2, "synth_streak": 2,
                                "pivot_streak": 2})
    inner = ap.plan
    ap.plan = lambda lane, name, ck, prod, v, d="": seen_dir.append(d) or inner(lane, name, ck, prod, v, d)
    ls, q = evo_run(st_m, ["MATCH"])
    ap.plan = keep_plan
    check("V-EVO-MATCH-EXPLOITS", ls["status"] == "RUNNING" and ls.get("mode") == "EXPLOIT" and ls.get("lever") == "lev_b"
          and ls.get("no_conversion") == 0 and ls.get("synth_streak") == 0 and ls.get("pivot_streak") == 0
          and any("EVO MODE EXPLOIT" in d and "lev_b" in d for d in seen_dir))
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a", "no_conversion": 2, "pivot_streak": 1,
                                         "pivot_history": [{"method_class": "F1", "evidence_delta": False}]}), ["NONE"])
    check("V-EVO-PIVOT-RULE-REUSED", ls["status"] == "PARKED" and "zero evidence delta twice" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a"}, ({"stop": "nothing admissible"}, RES)), ["INFORMATION"])
    check("V-EVO-PLANNER-STOP-BECOMES-RESEARCH", ls["status"] == "RUNNING" and ls.get("lever") == "lev_b"
          and ls.get("mode") == "RESEARCH")
    # budget park: resumes when the ledger admits (an Owner release), holds otherwise; other parks never self-resume
    st = evo_fresh([LA], {"status": "PARKED", "park_kind": "budget", "lever": "lev_a"})
    ap.classify_progress = lambda v, p, b=None, lane=None: ("INFORMATION", "")
    rec["owner_hold"]["set_at"] = 7900; recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    check("V-EVO-BUDGET-PARK-RESUMES", st["lanes"]["L"]["status"] == "RUNNING")
    st = evo_fresh([LA], {"status": "PARKED", "park_kind": "budget", "lever": "lev_a"})
    (tmp / "home" / "ledger.jsonl").write_text(json.dumps({"ts": now - 86400, "tokens": 70_000_000}) + "\n")
    judged = []
    ap.judge = lambda *a: judged.append(a) or dict(full, _tokens=1)
    _keep_u = ap.UNLOCKED_CAP; ap.UNLOCKED_CAP = 285_261_779
    rec["owner_hold"]["set_at"] = 7901; recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    ap.UNLOCKED_CAP = _keep_u
    # the resume itself must not happen (a resumed lane re-parks at the next gate, so status alone cannot see it;
    # evo_budget_resume_always survived on that until 2026-11-16, hidden while every mutant crashed in mkrepo)
    aplog = (tmp / "home" / "autopilot.log").read_text() if (tmp / "home" / "autopilot.log").exists() else ""
    check("V-EVO-BUDGET-PARK-HOLDS-WITHOUT-RELEASE", st["lanes"]["L"]["status"] == "PARKED" and not judged
          and "budget admits again" not in aplog)
    st = evo_fresh([LA], {"status": "PARKED", "park_kind": "evo", "lever": "lev_a"})
    rec["owner_hold"]["set_at"] = 7902; recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    check("V-EVO-OTHER-PARK-HOLDS", st["lanes"]["L"]["status"] == "PARKED")
    # Owner 2026-11-13 (pane c26eafbf): a pivot hold names its path in `residual` (evidence null): judge that path,
    # and never call the judge with an empty one
    check("V-AP-HOLD-PATH-ORDER", ap.hold_checkpoint({"evidence": "/e", "residual": "/r"}) == "/e"
          and ap.hold_checkpoint({"evidence": None, "residual": "/r"}) == "/r" and ap.hold_checkpoint({}) == "")
    judged = []
    st = evo_fresh([LA], {"lever": "lev_a"})  # evo_fresh resets ap.judge: install the recorder after it
    ap.judge = lambda lane, ck, prod: judged.append(ck) or dict(full, _tokens=1)
    rec["owner_hold"].update(set_at=7903, evidence=None, residual=str(tmp / "ck.md")); recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-PIVOT-HOLD-JUDGES-RESIDUAL", judged == [str(tmp / "ck.md")])
    st = evo_fresh([LA], {"lever": "lev_a"})
    ap.judge = lambda lane, ck, prod: judged.append(ck) or dict(full, _tokens=1)
    judged.clear()
    rec["owner_hold"].update(set_at=7904, evidence=None, residual=None); recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-EMPTY-HOLD-PARKS-UNJUDGED", not judged and st["lanes"]["L"]["status"] == "PARKED")
    # 2026-11-17 (S111C, Owner "b"): an empty hold whose generation branch committed a checkpoint is judged on it
    st = evo_fresh([LA], {"lever": "lev_a"})
    ap.judge = lambda lane, ck, prod: judged.append(ck) or dict(full, _tokens=1)
    judged.clear()
    keep_cfb = ap.checkpoint_from_branch
    ap.checkpoint_from_branch = lambda p, b, h: str(tmp / "ck.md")
    rec["owner_hold"].update(set_at=7905, evidence=None, residual=None); recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    ap.checkpoint_from_branch = keep_cfb
    check("V-AP-EMPTY-HOLD-FINDS-BRANCH-CHECKPOINT", judged == [str(tmp / "ck.md")])
    rec["owner_hold"].update(evidence=str(tmp / "ck.md")); rec["owner_hold"].pop("residual", None)
    recp.write_text(json.dumps(rec))
    ap.classify_progress = orig_cls
    # checkpoint discovery across worktree branches: fast-forward only, from a clean tree, exactly one holder
    pr = mkrepo("evo_prod")
    wt = tmp / "evo_wt"
    git(pr, "worktree", "add", "-q", "-b", "gen", str(wt))
    (wt / "ck.md").write_text("checkpoint\n")
    git(wt, "add", "-A"); git(wt, "commit", "-q", "-m", "ck")
    how, note = E.discover_checkpoint(str(pr), "ck.md")
    check("V-EVO-CHECKPOINT-FF", how == "FF" and (pr / "ck.md").exists() and git(pr, "rev-parse", "HEAD") == git(wt, "rev-parse", "HEAD"))
    check("V-EVO-CHECKPOINT-OK-IN-PRODUCT", E.discover_checkpoint(str(pr), "ck.md")[0] == "OK")
    pr2 = mkrepo("evo_prod2")
    wt2 = tmp / "evo_wt2"
    git(pr2, "worktree", "add", "-q", "-b", "gen", str(wt2))
    (wt2 / "ck.md").write_text("checkpoint\n"); git(wt2, "add", "-A"); git(wt2, "commit", "-q", "-m", "ck")
    (pr2 / "b.txt").write_text("b\n"); git(pr2, "add", "-A"); git(pr2, "commit", "-q", "-m", "diverge")
    head2 = git(pr2, "rev-parse", "HEAD")
    how, note = E.discover_checkpoint(str(pr2), "ck.md")
    check("V-EVO-CHECKPOINT-NON-FF-PARKS", how == "PARK" and git(pr2, "rev-parse", "HEAD") == head2 and not (pr2 / "ck.md").exists())
    pr3 = mkrepo("evo_prod3")
    wt3 = tmp / "evo_wt3"
    git(pr3, "worktree", "add", "-q", "-b", "gen", str(wt3))
    (wt3 / "ck.md").write_text("checkpoint\n"); git(wt3, "add", "-A"); git(wt3, "commit", "-q", "-m", "ck")
    (pr3 / "a.txt").write_text("dirty\n")
    head3 = git(pr3, "rev-parse", "HEAD")
    how, note = E.discover_checkpoint(str(pr3), "ck.md")
    check("V-EVO-CHECKPOINT-DIRTY-PARKS", how == "PARK" and git(pr3, "rev-parse", "HEAD") == head3)
    check("V-EVO-CHECKPOINT-ABSENT-PARKS", E.discover_checkpoint(str(pr3), "none.md")[0] == "PARK")
    check("V-EVO-CHECKPOINT-OUTSIDE-PRODUCT-UNTOUCHED", E.discover_checkpoint(str(pr3), str(tmp / "elsewhere.md"))[0] == "OK")
    # F3 (stall fixes, S63F 2026-11-15): an absolute path inside <product>/.claude/worktrees/<w>/ is not "in the product";
    # committed there it follows the branch rule (ff), uncommitted it parks without a judge call
    pr4 = mkrepo("evo_prod4")
    wt4 = pr4 / ".claude" / "worktrees" / "g4"
    git(pr4, "worktree", "add", "-q", "-b", "g4", str(wt4))
    (wt4 / "ev").mkdir()
    (wt4 / "ev" / "ck.md").write_text("checkpoint\n"); git(wt4, "add", "ev/ck.md"); git(wt4, "commit", "-q", "-m", "ck")
    (wt4 / "ev" / "loose.md").write_text("x\n")
    how, note = E.discover_checkpoint(str(pr4), str(wt4 / "ev" / "loose.md"))
    check("V-AP-CKPT-UNCOMMITTED", how == "PARK" and "CHECKPOINT_UNCOMMITTED" in note and not (pr4 / "ev").exists())
    how, note = E.discover_checkpoint(str(pr4), str(wt4 / "ev" / "ck.md"))
    check("V-AP-CKPT-WORKTREE", how == "FF" and (pr4 / "ev" / "ck.md").exists())
    check("V-AP-CKPT-WORKTREE-REL", (E.worktree_rel(str(pr4), str(wt4 / "ev" / "ck.md")) or ("", ""))[1]
          == os.path.join("ev", "ck.md") and E.worktree_rel(str(pr4), str(pr4 / "ev" / "ck.md")) is None
          and E.worktree_rel(str(pr4), "ev/ck.md") is None)
    # 2026-11-17 (Owner "b"): the worktree Claude removed on exit keeps its branch; the branch tip still counts
    prv = mkrepo("evo_prod_vanish")
    wtv = tmp / "evo_wt_vanish"
    git(prv, "worktree", "add", "-q", "-b", "gone", str(wtv))
    (wtv / "ck.md").write_text("checkpoint\n"); git(wtv, "add", "-A"); git(wtv, "commit", "-q", "-m", "ck")
    hv = git(wtv, "rev-parse", "HEAD")
    git(prv, "worktree", "remove", "--force", str(wtv))
    how, note = E.discover_checkpoint(str(prv), "ck.md")
    check("V-EVO-CHECKPOINT-VANISHED-WORKTREE", how == "FF" and git(prv, "rev-parse", "HEAD") == hv)
    # two unrelated tips holding the same path stay ambiguous: parked, product untouched
    pr7 = mkrepo("evo_prod_tips")
    base7 = git(pr7, "rev-parse", "HEAD")
    for br in ("x1", "x2"):
        git(pr7, "checkout", "-q", "-b", br, base7)
        (pr7 / "ck.md").write_text(f"{br}\n"); git(pr7, "add", "-A"); git(pr7, "commit", "-q", "-m", br)
    git(pr7, "checkout", "-q", "--detach", base7)
    check("V-EVO-CHECKPOINT-TWO-TIPS-PARKS", E.discover_checkpoint(str(pr7), "ck.md")[0] == "PARK"
          and git(pr7, "rev-parse", "HEAD") == base7)
    # 2026-11-17 (S111C): the checkpoint a hold forgot to name, found inside the generation's window only
    pr8 = mkrepo("evo_prod_nopath")
    b8 = git(pr8, "rev-parse", "HEAD")
    (pr8 / "ev").mkdir()
    (pr8 / "ev" / "checkpoint_s1.md").write_text("ck\n"); git(pr8, "add", "-A"); git(pr8, "commit", "-q", "-m", "ck")
    (pr8 / "ev" / "budget.md").write_text("b\n"); git(pr8, "add", "-A"); git(pr8, "commit", "-q", "-m", "budget")
    h8 = git(pr8, "rev-parse", "HEAD")
    keep_sh8, ap.sh = ap.sh, load().sh  # real git here: ap.sh is a recorder in this part of the gate
    try:
        check("V-AP-NOPATH-FOUND-ON-BRANCH", ap.checkpoint_from_branch(str(pr8), b8, h8) == "ev/checkpoint_s1.md")
        check("V-AP-NOPATH-WINDOW-ONLY", ap.checkpoint_from_branch(str(pr8), h8, h8) == ""
              and ap.checkpoint_from_branch(str(pr8), None, h8) == "")
        (pr8 / "ev" / "notes.md").write_text("n\n"); git(pr8, "add", "-A"); git(pr8, "commit", "-q", "-m", "n")
        check("V-AP-NOPATH-NONE-NAMED", ap.checkpoint_from_branch(str(pr8), h8, git(pr8, "rev-parse", "HEAD")) == "")
    finally:
        ap.sh = keep_sh8
    # F4b (2026-11-16, S71F/S69T): a continuation fast-forwards the product to the halted branch head before arming;
    # diverged or dirty -> refused and the product untouched (real git, both poles)
    pr5 = mkrepo("evo_prod5")
    wt5 = tmp / "evo_wt5"
    git(pr5, "worktree", "add", "-q", "-b", "s9/work", str(wt5))
    (wt5 / "w.txt").write_text("w\n"); git(wt5, "add", "-A"); git(wt5, "commit", "-q", "-m", "work")
    h5 = git(wt5, "rev-parse", "HEAD")
    ok5, n5 = E.ff_to(str(pr5), h5)
    check("V-EVO-FF-TO-BRANCH", ok5 and git(pr5, "rev-parse", "HEAD") == h5 and (pr5 / "w.txt").exists())
    check("V-EVO-FF-TO-SAME-OK", E.ff_to(str(pr5), h5)[0] and not E.ff_to(str(pr5), None)[0])
    (wt5 / "x.txt").write_text("x\n"); git(wt5, "add", "-A"); git(wt5, "commit", "-q", "-m", "more")
    (pr5 / "p.txt").write_text("p\n"); git(pr5, "add", "-A"); git(pr5, "commit", "-q", "-m", "packet")
    hp5 = git(pr5, "rev-parse", "HEAD")
    ok6, n6 = E.ff_to(str(pr5), git(wt5, "rev-parse", "HEAD"))
    check("V-EVO-FF-TO-DIVERGED-REFUSED", not ok6 and "not a fast-forward" in n6 and git(pr5, "rev-parse", "HEAD") == hp5)
    pr6 = mkrepo("evo_prod6")
    wt6 = tmp / "evo_wt6"
    git(pr6, "worktree", "add", "-q", "-b", "s8/work", str(wt6))
    (wt6 / "w.txt").write_text("w\n"); git(wt6, "add", "-A"); git(wt6, "commit", "-q", "-m", "work")
    (pr6 / "a.txt").write_text("dirty\n")
    hp6 = git(pr6, "rev-parse", "HEAD")
    ok7, n7 = E.ff_to(str(pr6), git(wt6, "rev-parse", "HEAD"))
    check("V-EVO-FF-TO-DIRTY-REFUSED", not ok7 and "tracked changes" in n7 and git(pr6, "rev-parse", "HEAD") == hp6)
    return [n for n, ok in results if not ok]


def guarded(ap):
    try:
        return run_all(ap)
    except Exception as exc:  # noqa: BLE001 -- a crash under a mutant counts as red
        return [f"EXC {type(exc).__name__}: {exc}"]


fails = guarded(load())
for n, ok in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"{len(results) - len(fails)}/{len(results)}", fails if fails and fails[0].startswith("EXC") else "")


class _SameDir:
    @staticmethod
    def mkdtemp(prefix=""):
        return os.environ["AP_HOME"]


def _evo_copy(m, **attrs):
    """A private copy of evolve.py for one mutant (the shared module must never carry a mutation into the next run)."""
    spec = importlib.util.spec_from_file_location("evolve_mut", HERE / "evolve.py")
    e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e)
    for k, v in attrs.items():
        setattr(e, k, v(e) if callable(v) and k.startswith("_wrap_") is False and getattr(v, "_wrap", False) else v)
    m.evolve = e
    return e


def _evo_mut(**attrs):
    def f(m):
        e = _evo_copy(m)
        for k, v in attrs.items():
            setattr(e, k, v(e) if getattr(v, "_wrap", False) else v)
    return f


def _wrap(fn):
    fn._wrap = True
    return fn


def _git_unsafe(e):
    real = e._git

    def g(cwd, *args):
        if args[:1] == ("merge-base",) or args[:1] == ("status",):
            return 0, ""
        return real(cwd, *[a for a in args if a != "--ff-only"])
    return g


def _evo_copy_select(e, levers, lane, ls, product, graph, family_not=None, kind=None, repairs_for=None):
    return _SEL_ORIG(e)(levers, lane, ls, product, graph, None, kind, repairs_for)


def _SEL_ORIG(e):
    spec = importlib.util.spec_from_file_location("evolve_sel", HERE / "evolve.py")
    x = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(x)
    return x.select


def _ignore_extra(m):
    orig = m.policy_check
    m.policy_check = lambda ph, c, extra=(): orig(ph, c)


# mutation drill: disabling each guard must make the suite fail
def _worktree_unchecked(m):
    """The working-tree gate is reported as the HEAD blob, i.e. what runs is never compared with what was cited."""
    orig = m._git
    m._git = lambda p, *a: ((0, m._blob(p, "HEAD", a[-1]) or "") if a and a[0] == "hash-object" else orig(p, *a))


drill = {"policy_off": lambda m: setattr(m, "policy_check", lambda *a, **k: []),
         "policy_ignores_facts": _ignore_extra,
         "budget_off": lambda m: setattr(m, "budget_admits", lambda *a, **k: None),
         "fresh_any_word_is_count": lambda m: setattr(m, "FRESH_BUDGET_WORDS", frozenset()),
         "fresh_old_regex": lambda m: setattr(m, "FRESH_RE", __import__("re").compile(
             r"\bfresh\b[^.;]{0,30}?(\d[\d,]*(?:\.\d+)?)\s*([MmKk]\b)?()")),
         "blank_off": lambda m: setattr(m, "BLANK_STOP", 99),
         "profile_off": lambda m: setattr(m, "PROFILE_CONDITIONS", {}),
         "negation_off": lambda m: setattr(m, "NEGATION", __import__("re").compile(r"(?!x)x")),
         "trigger_negation_off": lambda m: setattr(m, "TRIGGER_NEGATED", __import__("re").compile(r"(?!x)x")),
         "hold_residual_ignored": lambda m: setattr(m, "hold_checkpoint", lambda h: h.get("evidence") or ""),
         "trigger_negation_all": lambda m: setattr(m, "TRIGGER_NEGATED", __import__("re").compile(r"")),
         "drift_off": lambda m: setattr(m, "packet_phase_drift", lambda *a: None),
         "agree_unchecked": lambda m: setattr(m, "agree_supported", lambda v, prior=None: True),
         "protected_off": lambda m: setattr(m, "protected_check", lambda lane: None),
         "topup_ignores_certificates": lambda m: setattr(m, "certified_since", lambda p, b: True),
         "topup_unbounded": lambda m: setattr(m, "MAX_TOPUPS", 99),
         "topup_never": lambda m: setattr(m, "cost_topup", lambda *a, **k: None),
         "topup_progress_ignored": lambda m: setattr(m, "progressed_since", lambda *a: None),
         "topup_progress_any": lambda m: setattr(m, "progressed_since", lambda *a: "x"),
         "topup_fingerprint_unchecked": lambda m: setattr(m, "progressed_since", lambda p, ls, rec: (
             "x" if m.branch_commits(p, ls.get("topup_head") or ls.get("base"), m.gen_head(rec)) else None)),
         "topup_progress_not_reset": lambda m: setattr(m, "progressed_since", lambda p, ls, rec: (
             "x" if m.branch_commits(p, ls.get("base"), m.gen_head(rec))
             and float((rec.get("cost_mark") or {}).get("at") or 0) > 0 else None)),
         "branch_commits_always": lambda m: setattr(m, "branch_commits", lambda *a: 1),
         "age_ignored": lambda m: setattr(m, "AGE_MIN_H", -1.0),
         "age_always": lambda m: setattr(m, "AGE_MIN_H", 99.0),
         "hold_sha_as_path": lambda m: setattr(m, "hold_checkpoint", lambda h: h.get("evidence") or h.get("residual") or ""),
         "autoext_unbounded": lambda m: setattr(m.evolve, "consume_extension", (lambda f: lambda ls, why, now=None: (
             ls.get("auto_extend", {}).update(max=10 ** 6) or f(ls, why, now)) if isinstance(ls.get("auto_extend"), dict)
             else 0)(m.evolve.consume_extension)),
         "autoext_research_no_raise": lambda m: setattr(m, "AUTO_EXT_TRANCHE", 0) or setattr(
             m, "extend_research_if_spent", (lambda f: lambda n, ls: f(n, dict(ls)) and False)(m.extend_research_if_spent)),
         "autoext_stop_still_stops": lambda m: setattr(m, "extend_after_stop", lambda *a: False),
         "hold_reason_ignored":lambda m: setattr(m, "CKPT_NAME_RE", m.re.compile(r"(?!x)x")),
         "kept_checkpoint_ignored":lambda m: setattr(m, "resumable_plan", (lambda f: lambda ls, key: (
             lambda p: dict(p, checkpoint=None) if p else p)(f(ls, key)))(m.resumable_plan)),
         "hold_at_sha_as_path":lambda m: setattr(m, "PATH_AT_SHA_RE", m.re.compile(r"(?!x)x")),
         "halt_never_continues": lambda m: setattr(m, "continue_halted", lambda *a: False),
         "halt_continues_forever": lambda m: setattr(m, "continue_halted", (lambda real: lambda st, lane, ls, *a: (
             ls.pop("continued_from", None), real(st, lane, ls, *a))[1])(m.continue_halted)),
         "evo_worktree_path_trusted": _evo_mut(worktree_rel=lambda p, c: None),
         "replan_off": lambda m: setattr(m, "POLICY_REPLANS", 0),
         "replan_blind": lambda m: setattr(m, "replan_feedback", lambda bad, off=None: ""),
         "unpark_rejudges": lambda m: setattr(m, "resumable_plan", lambda ls, key: None),
         "resume_any_hold": lambda m: setattr(m, "resumable_plan", lambda ls, key: ls.get("pending_plan")),
         "reserve_zero": lambda m: setattr(m, "CALL_RESERVE", 0),
         "prior_ignored": lambda m: setattr(m, "PRIOR_AUTHORITY", ()),
         "off_guard_removed": lambda m: setattr(m, "killed", lambda: False),
         "dry_writes_real": lambda m: setattr(m, "tempfile", _SameDir),
         "tranche_not_released": lambda m: setattr(m, "UNLOCKED_CAP", 285_261_779),
         "total_not_raised": lambda m: setattr(m, "TOTAL_CAP", 400_000_000),
         "envelope_ignored": lambda m: setattr(m, "envelope_admits", lambda *a: None),
         "info_park_off": lambda m: setattr(m, "INFO_PARK", 99),
         "no_conversion_park_off": lambda m: setattr(m, "NO_CONVERSION_PARK", 99),
         "data_allowlist_off": lambda m: setattr(m, "DATA", __import__("re").compile(r".")),
         "window_off": lambda m: setattr(m, "in_window", lambda p, b, c: bool(m._sha(p, c))),
         "cert_whole_file": lambda m: setattr(m, "verify_cert", lambda v, p, b=None, lane=None: (
             True if (v.get("new_canonical_certs") or 0) > 0 and v.get("cert_receipts") and sum(
                 m._git(p, "show", f"{r['commit']}:{r['path']}")[1].count("CERTIFIED") for r in v["cert_receipts"])
             >= v["new_canonical_certs"] else None)),
         "worktree_gate_unchecked": _worktree_unchecked,
         "ancestry_trusted": lambda m: setattr(m, "verify_information", lambda v, p, b=None, lane=None: (
             True if isinstance(v.get("information"), dict) else None)),
         "cert_count_trusted": lambda m: setattr(m, "verify_cert", lambda v, p, b=None, lane=None: (
             True if (v.get("new_canonical_certs") or 0) > 0 else None)),
         "capability_trusted": lambda m: setattr(m, "verify_capability", lambda v, p, b=None, lane=None: (
             True if v.get("validated_capability") is True else None)),
         "evo_instrument_fail_as_none": _evo_mut(classify=lambda cls, instr: cls),
         "evo_same_family_allowed": _evo_mut(select=_wrap(lambda e: (lambda *a, **k: _evo_copy_select(e, *a, **k)))),
         "evo_no_packet_check": _evo_mut(packet_problems=lambda *a, **k: []),
         "evo_lane_cap_ignored": _evo_mut(lane_research_cap=lambda ls: 100_000_000),
         "evo_research_never_stops": _evo_mut(RESEARCH_FAIL_STOP=99),
         "evo_repair_unbounded": _evo_mut(MAX_REPAIR=99),
         "evo_owner_resume_ignored": _evo_mut(OWNER_RESUME="zzz_never_set"),
         "evo_owner_design_ignored": _evo_mut(OWNER_DESIGN="zzz_never_set"),
         "evo_match_not_conversion": _evo_mut(CONVERSIONS=("CERT", "CAPABILITY")),
         "match_off": lambda m: setattr(m, "verify_match", lambda lane, product, notes: None),
         "match_ignores_regressions": lambda m: setattr(m, "match_lost", lambda old, cur: []),
         "owner_questions_dropped": lambda m: setattr(m, "OWNER_Q", __import__("re").compile("zzz_never_matches")),
         "owner_question_negations_kept": lambda m: setattr(m, "OWNER_Q_NOT", __import__("re").compile("zzz_never")),
         "match_build_dirt_kept": lambda m: setattr(m, "_tracked_dirty", lambda product: None),
         "superseded_never_admitted": lambda m: setattr(m, "_superseded", lambda g, n, prior=None: False),
         "superseded_any_count": lambda m: setattr(m, "_superseded", lambda g, n, prior=None: (
             type(g.get("rc")) is int and g["rc"] != 0 and g.get("superseded_by_certs") is not None)),
         "superseded_unchecked": lambda m: setattr(m, "superseded_ok", lambda v, p, b, prior=None, lane=None: None),
         "halt_waiting_not_resumed": lambda m: setattr(m, "halt_resumable", lambda ls, mid: ls.get("status") == "RUNNING"),
         "halt_any_waiting_resumed": lambda m: setattr(m, "halt_resumable", lambda ls, mid: (
             ls.get("status") in ("RUNNING", "WAITING"))),
         "terminal_checkpoint_ignored": lambda m: setattr(m, "terminal_checkpoint", lambda ls, p, rec: ""),
         "terminal_gen_head_only": lambda m: setattr(m, "terminal_checkpoint", lambda ls, p, rec: m.checkpoint_from_branch(
             p, ls.get("base"), m.gen_head(rec))),
         "own_gate_never_admitted": lambda m: setattr(m, "_gate_age_ok", (lambda real: lambda g, p, b, receipts=None: real(
             g, p, b, None))(m._gate_age_ok)),
         "own_gate_any_age": lambda m: setattr(m, "_gate_age_ok", lambda g, p, b, receipts=None: bool(m._gate_path(g))),
         "match_supersede_off": lambda m: setattr(m, "_superseded_m", lambda g, prior=None: False),
         "match_supersede_prior_ignored": lambda m: setattr(m, "_superseded_m", (lambda real: lambda g, prior=None: real(
             g, None))(m._superseded_m)),
         "match_new_moves_nothing": lambda m: setattr(m, "match_new", lambda lane, p: (0, None)),
         "superseded_must_be_all_certs": lambda m: setattr(m, "_superseded", lambda g, n, prior=None: (
             type(g.get("rc")) is int and g["rc"] != 0 and type(g.get("superseded_by_certs")) is int and type(n) is int
             and n > 0 and g["superseded_by_certs"] == n + int((prior or {}).get(m._gate_path(g)) or 0))),
         "superseded_any_gate_age": lambda m: setattr(m, "GATE_PATH", __import__("re").compile(r"(?!x)x|^")),
         "excluded_unchecked": lambda m: setattr(m, "excluded_ok", lambda v, p, b: None),
         "unfinished_never_continued": lambda m: setattr(m, "UNFINISHED_MAX", 0),
         "unfinished_unbounded": lambda m: setattr(m, "UNFINISHED_MAX", 99),
         "unfinished_any_inconclusive": lambda m: setattr(m, "continue_unfinished", (lambda real: (
             lambda st, lane, ls, key, ck, prod, v, dry: real(st, lane, ls, key, ck, prod, dict(v, checkpoint_final=False),
                                                              dry)))(m.continue_unfinished)),
         "superseded_prior_ignored": lambda m: setattr(m, "_superseded", (lambda real: lambda g, n, prior=None: real(
             g, n, None))(m._superseded)),
         "superseded_not_recorded": lambda m: setattr(m, "superseded_record", lambda v, prior=None: dict(prior or {})),
         "policy_refusal_parks_at_once": lambda m: setattr(m, "POLICY_RETRY_TICKS", 0),
         "policy_retry_forever": lambda m: setattr(m, "POLICY_RETRY_TICKS", 99),
         "evo_owner_lever_ignored": _evo_mut(owner_lever=lambda *a, **k: None),
         "evo_synth_off": _evo_mut(synthesize=lambda *a, **k: (None, "off")),
         "evo_synth_admits_anything": _evo_mut(synth_problems=lambda *a, **k: []),
         "evo_synth_unbounded": _evo_mut(SYNTH_MAX=99),
         "evo_synth_residual_unchecked": _evo_mut(synthesize=_wrap(lambda e: (lambda real: (
             lambda levers, lane, ls, product, family, designer, residual: real(
                 levers, lane, ls, product, family, designer, None)))(e.synthesize))),
         "synth_not_persisted": lambda m: setattr(m, "persist_designed", lambda *a, **k: None),
         "halt_continues_owner_close": lambda m: setattr(m, "owner_closed", lambda rec: False),
         "hold_sha_path_ignored": lambda m: setattr(m, "SHA_PATH_RE", __import__("re").compile(r"(?!x)x")),
         "halt_once_spent_before_arm": lambda m: setattr(m, "continue_halted", (lambda real: lambda st, lane, ls, mid, *a: (
             real(st, lane, ls, mid, *a), ls.__setitem__("continued_from", mid))[0])(m.continue_halted)),
         "evo_ff_to_always_ok": _evo_mut(ff_to=lambda p, h, d=False: (True, "x")),
         "designer_no_redesign": lambda m: setattr(m, "lever_designer", lambda lane, ck, prod: (
             lambda fam: m.design_lever(lane, ck, prod, fam))),
         "hold_freeform_ignored": lambda m: setattr(m, "PATH_IN_TEXT_RE", __import__("re").compile(r"(?!x)x")),
         "nopath_never_found": lambda m: setattr(m, "checkpoint_from_branch", lambda p, b, h: ""),
         "nopath_any_window": lambda m: setattr(m, "checkpoint_from_branch", (lambda real: lambda p, b, h: (
             real(p, b, h) or (real(p, m._git(p, "rev-list", "--max-parents=0", str(h))[1].strip()[:40], h)
                               if h else "")))(m.checkpoint_from_branch)),
         "evo_branches_ignored": _evo_mut(_branch_heads=lambda p: []),
         "held_notice_never": lambda m: setattr(m, "HELD_NOTICE_S", 10 ** 9),
         "held_notice_immediate": lambda m: setattr(m, "HELD_NOTICE_S", 0),
         "running_watch_off": lambda m: setattr(m, "running_watch", lambda *a: None),
         "running_watch_repeats": lambda m: setattr(m, "running_watch", (lambda real: lambda st, lane, ls, *a: (
             ls.pop("age_ext_for", None), ls.pop("held_notice", None), real(st, lane, ls, *a))[2])(m.running_watch)),
         "age_defer_off": lambda m: setattr(m, "AGE_DEFER_SPENT", 99.0),
         "age_defer_always": lambda m: setattr(m, "AGE_DEFER_SPENT", 0.0),
         "evo_repair_key_free_text": _evo_mut(instrument_key=lambda n: n),
         "evo_repair_any_instrument": _evo_mut(repair_admits=lambda x, f: True),
         "evo_repair_no_in_place": _evo_mut(repair_in_place=lambda *a, **k: None),
         "evo_selection_evidence_blank": _evo_mut(selection_evidence=lambda lv, g: {"prior": 0.0, "edges": []} if lv else None),
         "evo_selection_evidence_claims_edge": _evo_mut(selection_evidence=lambda lv, g: (
             {"prior": 1.0, "edges": [[b, lv["id"], 1.0] for b in lv.get("blockers", [])]} if lv else None)),
         "evo_pivot_rule_bypassed": _evo_mut(_pivot=lambda *a, **k: {"action": "pivot", "streak": 1, "why": "bypass"}),
         "evo_budget_resume_always": _evo_mut(budget_resume=lambda ls, why: ls.get("status") == "PARKED"),
         "evo_budget_never_resumes": _evo_mut(budget_resume=lambda ls, why: False),
         "gen_head_unbound_none": lambda m: setattr(m, "gen_head", (lambda real: lambda rec: (
             real(rec) if rec.get("binding") else None))(m.gen_head)),
         "evo_unsafe_merge": _evo_mut(_git=_wrap(_git_unsafe)),
         "arm_no_git_ident_check": lambda m: setattr(m, "git_ident_ok", lambda cwd: True),
         "arm_commit_rc_ignored": lambda m: setattr(m, "arm_commit", (lambda real: lambda *a, **k: (
             real(*a, **k), "")[1])(m.arm_commit)),
         "arm_adds_missing_archive": lambda m: setattr(m, "arm_commit", (lambda real: lambda cwd, paths, msg, dry: real(
             cwd, [".planning/milestones/x-archived-0"] + [p for p in paths if "archived" not in p], msg, dry))(
             m.arm_commit))}
survivors, crashed = [], []
for name, mut in drill.items():
    m = load()
    mut(m)
    red = guarded(m)
    if not red:
        survivors.append(name)
    elif red[0].startswith("EXC"):
        crashed.append(f"{name}: {red[0][:120]}")  # killed by a crash, not by an assertion: reported, never hidden
print("MUTANTS SURVIVED:", survivors or "none", f"({len(drill) - len(survivors)}/{len(drill)} killed)")
print("KILLED BY CRASH (not by a check):", crashed or "none")
ok = not fails and not survivors
print("AUTOPILOT_GATE_PASS" if ok else "AUTOPILOT_GATE_FAIL")
sys.exit(0 if ok else 1)
