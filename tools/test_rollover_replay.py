#!/usr/bin/env python
"""V-RR-* gates for tools/rollover_replay.py (plan ccp-s16). Hermetic: a fixture rollover ledger
and fixture transcripts, resolved through an injected lookup. No model call, no real ledger.

Each gate pins a fault met while measuring the real ledger on 2026-10-03: the certified-resume row
names the PREDECESSOR (a reader that trusts it measures the wrong session), torn concurrent
appends, commits written late in long PowerShell lines, and too few samples read as a number."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover_replay as rr  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def call(mid, ctx, tools=(), ts="2026-10-01T12:00:00Z"):
    """One assistant line: `ctx` resident tokens, optional tool uses (name, input)."""
    content = [{"type": "tool_use", "name": n, "input": i} for n, i in tools]
    return json.dumps({"type": "assistant", "timestamp": ts, "requestId": f"r-{mid}",
                       "message": {"id": f"m-{mid}", "model": "claude-opus-5-5", "content": content,
                                   "usage": {"input_tokens": 10, "cache_creation_input_tokens": 0,
                                             "cache_read_input_tokens": ctx - 10, "output_tokens": 5}}})


def transcript(d: Path, name: str, lines: list[str]) -> Path:
    p = d / f"{name}.jsonl"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="rr-"))
    commit = ("PowerShell", {"command": "$g='C:\\Program Files\\Git\\cmd\\git.exe'; & $g -C $r commit -q -F m.txt -- a.py"})
    paths = {
        # predecessor P1 (floor 300k) -> successor S1 (floor 120k, first mutation at call 3)
        "P1": transcript(d, "P1", [call("p1a", 300_000), call("p1b", 310_000)]),
        "S1": transcript(d, "S1", [call("s1a", 120_000, [("Read", {"file_path": "x"})]),
                                   call("s1a", 120_000),                       # duplicate line, same call
                                   call("s1b", 125_000, [("Grep", {"pattern": "y"})]),
                                   call("s1c", 130_000, [("Edit", {"file_path": "x"})])]),
        "S2": transcript(d, "S2", [call("s2a", 140_000), call("s2b", 150_000, [commit])]),
        "S3": transcript(d, "S3", [call("s3a", 110_000, [("Read", {"file_path": "x"})])]),   # never mutates
        "S4": transcript(d, "S4", [call("s4a", 900_000, [("Edit", {"file_path": "x"})])]),   # FAILED resume
    }
    led = d / "rollover-ledger.jsonl"
    rows = [
        {"event": "successor_claimed", "session_id": "P1", "claimant": "S1"},
        {"event": "resume_certified", "session_id": "P1", "wrong": []},
        {"event": "successor_claimed", "session_id": "P2", "claimant": "S2"},
        {"event": "resume_certified", "session_id": "P2", "wrong": []},
        {"event": "successor_claimed", "session_id": "P3", "claimant": "S3"},
        {"event": "resume_certified", "session_id": "P3", "wrong": []},
        {"event": "successor_claimed", "session_id": "P4", "claimant": "S4"},
        {"event": "resume_failed", "session_id": "P4", "wrong": [{"key": "head"}]},
        {"event": "resume_certified", "session_id": "P9", "wrong": []},       # certified, no claim row
    ]
    led.write_text("\n".join(json.dumps(r) for r in rows[:3]) + "\n" + 'hars": 805}\n' +
                   "\n".join(json.dumps(r) for r in rows[3:]) + "\n", encoding="utf-8")

    parsed, torn = rr.read_ledger(led)
    ok("V-RR-TORN-COUNTED", torn == 1 and len(parsed) == len(rows), f"torn={torn} rows={len(parsed)}")

    res = rr.fresh_cost(led, find=paths.get, min_samples=1)
    by = {s["successor"]: s for s in res["samples"]}
    ok("V-RR-SUCCESSOR-NOT-PREDECESSOR", by.get("S1", {}).get("first_ctx") == 120_000,
       f"S1 first_ctx={by.get('S1', {}).get('first_ctx')} (predecessor floor is 300000)")
    ok("V-RR-ONE-CALL-ONCE", by.get("S1", {}).get("calls_to_first_mutation") == 3,
       f"S1 calls_to_first_mutation={by.get('S1', {}).get('calls_to_first_mutation')}")
    ok("V-RR-COMMIT-IS-MUTATION", by.get("S2", {}).get("calls_to_first_mutation") == 2,
       f"S2={by.get('S2', {}).get('calls_to_first_mutation')}")
    ok("V-RR-NO-MUTATION-IS-NOT-ZERO", by.get("S3", {}).get("calls_to_first_mutation") is None
       and res["no_mutation"] == 1, f"S3={by.get('S3')} no_mutation={res['no_mutation']}")
    ok("V-RR-FAILED-RESUME-EXCLUDED", "S4" not in by, str(sorted(by)))
    ok("V-RR-CERTIFIED-WITHOUT-CLAIM-REPORTED", res["missing_claim"] == ["P9"], str(res["missing_claim"]))
    ok("V-RR-DISTRIBUTION", res["first_ctx"]["n"] == 3 and res["first_ctx"]["p50"] == 120_000,
       str(res["first_ctx"]))

    few = rr.fresh_cost(led, find=paths.get, min_samples=5)
    ok("V-RR-FEW-SAMPLES-INSUFFICIENT", few["verdict"] == "INSUFFICIENT_EVIDENCE"
       and few["first_ctx"].get("p50") is None, f"{few['verdict']} {few['first_ctx']}")
    ok("V-RR-ENOUGH-SAMPLES-MEASURED", res["verdict"] == "MEASURED", res["verdict"])   # positive control

    for cmd, want in (("git commit -m x", True), ("& $g -C $r commit -F m -- a", True),
                      ("git status --short", False), ("echo commitment; git log", False),
                      ("git -C r log --format=%s commit", False)):
        got = rr.is_commit_command(cmd)
        ok(f"V-RR-COMMIT-DETECT[{cmd[:24]}]", got is want, f"got {got}")

    ok("V-RR-DRY-RUN-NOT-COMMIT", not rr.is_commit_command("git commit --dry-run -m x"))

    # ---- C2 boundaries: a successful commit only, and only what was known at that call.
    def use(mid, tid, ctx, cmd):
        return json.dumps({"type": "assistant", "requestId": f"r-{mid}", "timestamp": "2026-10-01T12:00:00Z",
                           "message": {"id": f"m-{mid}", "model": "claude-opus-5-5",
                                       "content": [{"type": "tool_use", "id": tid, "name": "PowerShell",
                                                    "input": {"command": cmd}}],
                                       "usage": {"input_tokens": 10, "cache_read_input_tokens": ctx - 10}}})

    def result(tid, err=False):
        return json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "is_error": err, "content": "x"}]}})

    b_lines = [call("b1", 100_000), use("b2", "t-ok", 200_000, "git commit -m a"), result("t-ok"),
               use("b3", "t-hook", 300_000, "git commit -m b"), result("t-hook", err=True),
               use("b4", "t-open", 350_000, "git commit -m c"),                 # no result: unknown
               call("b5", 900_000)]
    bt = rr.session_trace(transcript(d, "B", b_lines))
    ok("V-RR-ONLY-SUCCESSFUL-COMMITS", bt["commit_calls"] == [2], str(bt["commit_calls"]))
    bnd = rr.boundaries(bt)
    trunc = rr.boundaries(rr.session_trace(transcript(d, "B2", b_lines[:3])))
    ok("V-RR-BOUNDARY-NO-FUTURE", bnd == trunc and bnd[0]["resident"] == 200_000,
       f"full={bnd} truncated={trunc}")

    # ---- prior: ended-before-T only, own capsule chain and rolled sessions out (censored, counted).
    T = 1_790_000_000.0
    for name, n in (("E1", 50), ("E2", 50), ("LATE", 50), ("ROLLED", 50), ("CHAIN", 50)):
        transcript(d, name, [use(f"{name}{k}", f"{name}t{k}", 100_000, "git commit -m x") if k == 10
                             else call(f"{name}{k}", 100_000) for k in range(n)] +
                   [result(f"{name}t10")])
    sessions = [("E1", d / "E1.jsonl", T - 100), ("E2", d / "E2.jsonl", T - 200),
                ("LATE", d / "LATE.jsonl", T + 100), ("ROLLED", d / "ROLLED.jsonl", T - 100),
                ("CHAIN", d / "CHAIN.jsonl", T - 100)]
    chain = rr.capsule_chain([{"event": "successor_claimed", "session_id": "ROOT", "claimant": "CHAIN"}], "ROOT")
    pri = rr.Prior(sessions, chain, rolled={"ROLLED"}).at(T)
    ok("V-RR-PRIOR-ENDED-BEFORE-T", pri["values"] == [39, 39] and pri["sessions"] == 2,
       f"values={pri['values']} sessions={pri['sessions']}")
    ok("V-RR-PRIOR-CENSORED-COUNTED", pri["censored_excluded"] == 1, str(pri))

    # ---- judge: every verdict is rollover.decide; both poles reachable (audit G11).
    price = rr.price_at("claude-opus-5-5", T)
    ok("V-RR-PRICED", price.get("state") == "OK", str(price))
    big = {"call": 50, "ts": T, "model": "claude-opus-5-5", "floor": 130_000, "resident": 600_000}
    many = {"values": [200] * 10, "sessions": 5, "censored_excluded": 0}
    few_left = {"values": [1] * 10, "sessions": 5, "censored_excluded": 0}
    j = rr.judge(big, 4000, many, [0.0])
    ok("V-RR-POSITIVE-CONTROL-WOULD", j["prior"]["verdict"] == "WOULD_ROLLOVER", str(j["prior"]))
    j = rr.judge(big, 4000, few_left, [0.0])
    ok("V-RR-SHORT-HORIZON-CONTINUE", j["prior"]["verdict"] == "CONTINUE", str(j["prior"]))
    small = {**big, "resident": 200_000}
    j = rr.judge(small, 4000, many, [0.0])
    ok("V-RR-GROWTH-GATE-IS-DECIDES", j["prior"]["verdict"] == "CONTINUE" and "growth" in j["reason"], j["reason"])
    j = rr.judge(big, 4000, {"values": [200] * 3, "sessions": 1, "censored_excluded": 0}, [0.0])
    ok("V-RR-FEW-PRIOR-INSUFFICIENT", j["prior"]["verdict"] == "INSUFFICIENT_EVIDENCE", str(j["prior"]))
    # rehydration flips a borderline horizon: C=0 says WOULD, a large C says no -> not a clean verdict
    edge = {"values": [int(rr.judge(big, 4000, many, [0.0])["breakeven_calls"]) + 2] * 10,
            "sessions": 5, "censored_excluded": 0}
    j = rr.judge(big, 4000, edge, [0.0, 20_000_000.0])
    ok("V-RR-REHYDRATION-COUNTS", j["prior"]["verdict"] == "WOULD_ROLLOVER"
       and j["rehydrated"] == "INSUFFICIENT_EVIDENCE", f"{j['prior']} rehydrated={j['rehydrated']}")
    ev = rr.exposure(big, 200, rr.judge(big, 4000, many, [0.0]), [0.0, 1_000_000.0])
    ok("V-RR-EXPOSURE-NOT-A-SAVING", ev and "NOT a saving" in ev["label"]
       and ev["mechanical_exposure_read_eq"][0] < ev["mechanical_exposure_read_eq"][1], str(ev))
    # the write premium a fresh epoch pays (audit fold) must be in the number, not only in the prose:
    # a mutant dropping it kept the label and the interval and passed (C5 drill m5, 2026-10-03)
    g = rr.judge(big, 4000, many, [0.0])["growth_above_fresh"]
    prem = (big["resident"] - g) * (price["write"] - price["read"]) / price["read"]
    want = [round(g * 150 - prem - 1_000_000), round(g * 150 - prem)]
    ok("V-RR-EXPOSURE-CARRIES-WRITE-PREMIUM", prem > 0 and ev and ev["mechanical_exposure_read_eq"] == want,
       f"premium={prem:.0f} want={want} got={ev and ev['mechanical_exposure_read_eq']}")

    print(f"ROLLOVER_REPLAY_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
