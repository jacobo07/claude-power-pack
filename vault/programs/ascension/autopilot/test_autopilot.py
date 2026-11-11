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
                  AP_PP=str(HERE.parents[3]))
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


def _ignore_extra(m):
    orig = m.policy_check
    m.policy_check = lambda ph, c, extra=(): orig(ph, c)


# mutation drill: disabling each guard must make the suite fail
drill = {"policy_off": lambda m: setattr(m, "policy_check", lambda *a, **k: []),
         "policy_ignores_facts": _ignore_extra,
         "budget_off": lambda m: setattr(m, "budget_admits", lambda *a, **k: None),
         "blank_off": lambda m: setattr(m, "BLANK_STOP", 99),
         "profile_off": lambda m: setattr(m, "PROFILE_CONDITIONS", {}),
         "negation_off": lambda m: setattr(m, "NEGATION", __import__("re").compile(r"(?!x)x")),
         "drift_off": lambda m: setattr(m, "packet_phase_drift", lambda *a: None),
         "agree_unchecked": lambda m: setattr(m, "agree_supported", lambda v: True),
         "protected_off": lambda m: setattr(m, "protected_check", lambda lane: None),
         "reserve_zero": lambda m: setattr(m, "CALL_RESERVE", 0),
         "off_guard_removed": lambda m: setattr(m, "killed", lambda: False),
         "dry_writes_real": lambda m: setattr(m, "tempfile", _SameDir)}
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
