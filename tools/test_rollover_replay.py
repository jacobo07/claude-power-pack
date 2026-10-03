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

    print(f"ROLLOVER_REPLAY_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
