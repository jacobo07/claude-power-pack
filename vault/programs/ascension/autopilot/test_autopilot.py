#!/usr/bin/env python3
"""Gate for the Ascension Autopilot (V-AP-*). Runs against a scratch HOME/STATE_DIR with fake mission records; never
touches real missions (gm/judge/plan are stubbed). Ends with a mutation drill: each guard disabled must turn tests red.
Every refusal asserts its specific label; every guard has an admitting twin so a refuse-everything mutant also dies."""
import importlib.util
import json
import os
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
    day = [{"ts": now, "tokens": 60_000_000}]
    check("V-AP-BUDGET-DAY-REFUSES", ap.budget_admits(day, now, 25_000_000) is not None)
    check("V-AP-BUDGET-DAY-ADMITS", ap.budget_admits(day, now, 20_000_000) is None)
    check("V-AP-BUDGET-NEXT-DAY-ADMITS", ap.budget_admits(day, now + 86400, 25_000_000) is None)
    many = [{"ts": now - 86400 * k, "tokens": 79_000_000} for k in range(1, 6)]  # 395M on earlier days
    check("V-AP-BUDGET-TOTAL-REFUSES", ap.budget_admits(many, now, 25_000_000) is not None)
    # Owner 2026-11-11: S27's 200M counts inside the totals (not the day cap). With the reorientation ceiling
    # (UNLOCKED_CAP 285,261,779): 60M of earlier grants + 200M prior + 25M fits; 61M + 200M + 25M is FROZEN.
    early = lambda t: [{"ts": now - 86400, "tokens": t}]  # noqa: E731
    # Owner 2026-11-12 released +120M: unlocked = total = 405,261,779. 180M + 200M prior + 25M fits; 181M does not.
    check("V-AP-BUDGET-PRIOR-S27-COUNTS-IN-TOTAL", ap.budget_admits(early(180_000_000), now, 25_000_000) is None
          and ap.budget_admits(early(181_000_000), now, 25_000_000) is not None)
    check("V-AP-BUDGET-OWNER-120M-RELEASED", ap.UNLOCKED_CAP == 405_261_779 and ap.TOTAL_CAP == 405_261_779)
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
    check("V-AP-POLICY-BLOCKS-ARM-VIA-FACTS", st["lanes"]["L"]["status"] == "PARKED" and not calls)
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
            ap.classify_progress = (lambda c: (lambda v, p, b=None: (c, "")))(c)
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
    (tmp / "home" / "ledger.jsonl").write_text(json.dumps({"ts": _t.time(), "tokens": 50_000_000}) + "\n")
    ap.judge = lambda *a: dict(full, _tokens=20_000_000)
    ap.classify_progress = lambda v, p, b=None: ("INFORMATION", "")
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
    LR = {"id": "lev_r", "family": "REPAIR", "kind": "repair", "blockers": ["CTL"], "requires": [], "cost": 1, "status": "open"}
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
            ap.classify_progress = (lambda c: (lambda v, p, b=None: (c, "")))(c)
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
    ls, q = evo_run(evo_fresh([LA, LC], {"lever": "lev_a"}), ["INFORMATION", "INFORMATION"])
    check("V-EVO-SAME-FAMILY-NEVER-CHOSEN", ls["status"] == "PARKED" and "another family" in q)
    ls, q = evo_run(evo_fresh([LA, LX], {"lever": "lev_a"}), ["INFORMATION", "INFORMATION"])
    check("V-EVO-PRECONDITION-REQUIRED", ls["status"] == "PARKED" and "another family" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a"}), ["INFORMATION", "INFORMATION"])
    check("V-EVO-RESEARCH-PACKET-NEEDS-DISCRIMINATING-TEST", ls["status"] == "PARKED" and "no 'rival'" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH"}, (RES,)), ["NONE", "NONE"])
    check("V-EVO-RESEARCH-STOP-RULE", ls["status"] == "PARKED" and "research stop rule" in q)
    ls, q = evo_run(evo_fresh([LA, LR], {"lever": "lev_a"}, (REP,)), ["NONE", "NONE"], ["ctl_pool"])
    check("V-EVO-INSTRUMENT-FAIL-NOT-NEGATIVE", ls["status"] == "RUNNING" and ls.get("mode") == "REPAIR"
          and ls.get("blank") == 0 and ls.get("no_conversion", 0) == 0 and ls.get("repair") == {"ctl_pool": 2})
    st_rep = {"lanes": {"L": ls}}
    ls, q = evo_run(st_rep, ["NONE"], ["ctl_pool"])
    check("V-EVO-REPAIR-CAP-PARKS", ls["status"] == "PARKED" and "repair cap" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_b", "mode": "RESEARCH", "info_streak": 1}), ["CERT"])
    check("V-EVO-CERT-RETURNS-TO-EXPLOIT", ls["status"] == "RUNNING" and ls.get("mode") == "EXPLOIT")
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a", "no_conversion": 2, "pivot_streak": 1,
                                         "pivot_history": [{"method_class": "F1", "evidence_delta": False}]}), ["NONE"])
    check("V-EVO-PIVOT-RULE-REUSED", ls["status"] == "PARKED" and "zero evidence delta twice" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a"}, ({"stop": "nothing admissible"}, RES)), ["INFORMATION"])
    check("V-EVO-PLANNER-STOP-BECOMES-RESEARCH", ls["status"] == "RUNNING" and ls.get("lever") == "lev_b"
          and ls.get("mode") == "RESEARCH")
    # budget park: resumes when the ledger admits (an Owner release), holds otherwise; other parks never self-resume
    st = evo_fresh([LA], {"status": "PARKED", "park_kind": "budget", "lever": "lev_a"})
    ap.classify_progress = lambda v, p, b=None: ("INFORMATION", "")
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
    check("V-EVO-BUDGET-PARK-HOLDS-WITHOUT-RELEASE", st["lanes"]["L"]["status"] == "PARKED" and not judged)
    st = evo_fresh([LA], {"status": "PARKED", "park_kind": "evo", "lever": "lev_a"})
    rec["owner_hold"]["set_at"] = 7902; recp.write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    check("V-EVO-OTHER-PARK-HOLDS", st["lanes"]["L"]["status"] == "PARKED")
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


def _evo_copy_select(e, levers, lane, ls, product, graph, family_not=None, kind=None):
    return _SEL_ORIG(e)(levers, lane, ls, product, graph, None, kind)


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
         "blank_off": lambda m: setattr(m, "BLANK_STOP", 99),
         "profile_off": lambda m: setattr(m, "PROFILE_CONDITIONS", {}),
         "negation_off": lambda m: setattr(m, "NEGATION", __import__("re").compile(r"(?!x)x")),
         "trigger_negation_off": lambda m: setattr(m, "TRIGGER_NEGATED", __import__("re").compile(r"(?!x)x")),
         "trigger_negation_all": lambda m: setattr(m, "TRIGGER_NEGATED", __import__("re").compile(r"")),
         "drift_off": lambda m: setattr(m, "packet_phase_drift", lambda *a: None),
         "agree_unchecked": lambda m: setattr(m, "agree_supported", lambda v: True),
         "protected_off": lambda m: setattr(m, "protected_check", lambda lane: None),
         "reserve_zero": lambda m: setattr(m, "CALL_RESERVE", 0),
         "prior_ignored": lambda m: setattr(m, "PRIOR_AUTHORITY", ()),
         "off_guard_removed": lambda m: setattr(m, "killed", lambda: False),
         "dry_writes_real": lambda m: setattr(m, "tempfile", _SameDir),
         "tranche_not_released": lambda m: setattr(m, "UNLOCKED_CAP", 285_261_779),
         "total_not_raised": lambda m: setattr(m, "TOTAL_CAP", 400_000_000),
         "info_park_off": lambda m: setattr(m, "INFO_PARK", 99),
         "no_conversion_park_off": lambda m: setattr(m, "NO_CONVERSION_PARK", 99),
         "data_allowlist_off": lambda m: setattr(m, "DATA", __import__("re").compile(r".")),
         "window_off": lambda m: setattr(m, "in_window", lambda p, b, c: bool(m._sha(p, c))),
         "cert_whole_file": lambda m: setattr(m, "verify_cert", lambda v, p, b=None: (
             True if (v.get("new_canonical_certs") or 0) > 0 and v.get("cert_receipts") and sum(
                 m._git(p, "show", f"{r['commit']}:{r['path']}")[1].count("CERTIFIED") for r in v["cert_receipts"])
             >= v["new_canonical_certs"] else None)),
         "worktree_gate_unchecked": _worktree_unchecked,
         "ancestry_trusted": lambda m: setattr(m, "verify_information", lambda v, p, b=None: (
             True if isinstance(v.get("information"), dict) else None)),
         "cert_count_trusted": lambda m: setattr(m, "verify_cert", lambda v, p, b=None: (
             True if (v.get("new_canonical_certs") or 0) > 0 else None)),
         "capability_trusted": lambda m: setattr(m, "verify_capability", lambda v, p, b=None: (
             True if v.get("validated_capability") is True else None)),
         "evo_instrument_fail_as_none": _evo_mut(classify=lambda cls, instr: cls),
         "evo_same_family_allowed": _evo_mut(select=_wrap(lambda e: (lambda *a, **k: _evo_copy_select(e, *a, **k)))),
         "evo_no_packet_check": _evo_mut(packet_problems=lambda *a, **k: []),
         "evo_research_never_stops": _evo_mut(RESEARCH_FAIL_STOP=99),
         "evo_repair_unbounded": _evo_mut(MAX_REPAIR=99),
         "evo_pivot_rule_bypassed": _evo_mut(_pivot=lambda *a, **k: {"action": "pivot", "streak": 1, "why": "bypass"}),
         "evo_budget_resume_always": _evo_mut(budget_resume=lambda ls, why: ls.get("status") == "PARKED"),
         "evo_budget_never_resumes": _evo_mut(budget_resume=lambda ls, why: False),
         "evo_unsafe_merge": _evo_mut(_git=_wrap(_git_unsafe))}
survivors = []
for name, mut in drill.items():
    m = load()
    mut(m)
    if not guarded(m):
        survivors.append(name)
print("MUTANTS SURVIVED:", survivors or "none", f"({len(drill) - len(survivors)}/{len(drill)} killed)")
ok = not fails and not survivors
print("AUTOPILOT_GATE_PASS" if ok else "AUTOPILOT_GATE_FAIL")
sys.exit(0 if ok else 1)
