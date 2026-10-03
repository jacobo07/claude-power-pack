#!/usr/bin/env python
"""V-HW-* gates: the live callers feed decide() measured remaining-work evidence (plan ccp-s16 §16.1
D1b). Hermetic: a throwaway git repo, a fixture transcript, a private state dir. The real 3-minute
prior build never runs here: the refresher is replaced by a recorder and its lock is driven directly."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402
import rollover_econ as ec  # noqa: E402
import rollover_replay as rr  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def call(mid, ctx):
    return json.dumps({"type": "assistant", "timestamp": "2026-10-03T12:00:00Z", "requestId": f"r-{mid}",
                       "message": {"id": f"m-{mid}", "model": "claude-opus-5-5", "content": [],
                                   "usage": {"input_tokens": 10, "cache_creation_input_tokens": 0,
                                             "cache_read_input_tokens": ctx - 10, "output_tokens": 5}}})


def artifact(state: Path, values, expires_in=3600.0, schema=None):
    (state / ro.PRIOR_FILE).write_text(json.dumps({
        "schema": schema or rr.PRIOR_SCHEMA, "basis": "MEASURED_PRIOR", "values": sorted(values),
        "computed_at": time.time(), "expires_at": time.time() + expires_in,
        "rehydration": {"basis": "UPPER_BOUND_P50", "tokens": 10_000}}), encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="hw-"))
    repo, state = tmp / "repo", tmp / "state"
    repo.mkdir()
    state.mkdir()
    for args in (("init", "-q"), ("config", "user.email", "t@t"), ("config", "user.name", "t"),
                 ("commit", "-q", "--allow-empty", "-m", "root")):
        assert ro._git(repo, *args)[0], args
    tr = tmp / "s.jsonl"
    tr.write_text("\n".join(call(i, 130_000 + i * 50_000) for i in range(10)) + "\n", encoding="utf-8")

    ok("V-HW-ONE-SPELLING", rr.PRIOR_FILE == ro.PRIOR_FILE and rr.PRIOR_SCHEMA == ro.PRIOR_SCHEMA)
    ev, _ = ro.horizon_evidence(state)
    ok("V-HW-MISSING-IS-UNKNOWN", ev["basis"] == ro.UNKNOWN and "no prior" in ev["reason"], str(ev))
    artifact(state, [200] * 10, expires_in=-1)
    ev, _ = ro.horizon_evidence(state)
    ok("V-HW-EXPIRED-IS-UNKNOWN", ev["basis"] == ro.UNKNOWN and ev.get("stale"), str(ev))
    artifact(state, [200] * 10, schema="other-v9")
    ok("V-HW-FOREIGN-SCHEMA-IS-UNKNOWN", ro.horizon_evidence(state)[0]["basis"] == ro.UNKNOWN)
    (state / ro.PRIOR_FILE).unlink()

    calls = []
    real_refresh, ec.refresh_prior = ec.refresh_prior, lambda sd=None: calls.append(sd) or "recorded"
    try:
        out = ec.evaluate("hw-none", str(repo), str(tr), 30.0, "0" * 40, state)
        d = out["decision"]
        ok("V-HW-NO-PRIOR-NO-ASK", d.get("would_rollover") is False and d.get("economics") == ro.UNKNOWN
           and d.get("breakeven_calls") is not None, d.get("reason"))
        ok("V-HW-STALE-TRIGGERS-REFRESH", calls == [state] and out.get("prior_refresh") == "recorded", str(calls))
        artifact(state, [200] * 10)
        out = ec.evaluate("hw-long", str(repo), str(tr), 30.0, "0" * 40, state)
        d = out["decision"]
        filed = json.loads(ec.decision_path("hw-long", state).read_text(encoding="utf-8"))["decision"]
        ok("V-HW-EVIDENCE-REACHES-LIVE-DECISION", d.get("would_rollover") is True
           and filed.get("economics") == "ROBUST_ROLLOVER" and filed.get("horizon_basis") == "MEASURED_PRIOR",
           d.get("reason"))
        ok("V-HW-FRESH-PRIOR-NO-REFRESH", len(calls) == 1 and "prior_refresh" not in out, str(calls))
    finally:
        ec.refresh_prior = real_refresh
    rows = [json.loads(x) for x in (state / "rollover-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    ok("V-HW-ROW-CARRIES-OBLIGATIONS", rows and all(isinstance(r.get("obligations"), int) for r in rows),
       str([r.get("obligations") for r in rows]))
    row = ro.observe("hw-shadow", str(repo), str(tr), 30.0, "shadow", None, state)
    ok("V-HW-SHADOW-USES-EVIDENCE", row["decision"].get("horizon_basis") == "MEASURED_PRIOR"
       and "economics" in row["decision"], str({k: row["decision"].get(k) for k in ("horizon_basis", "reason")}))

    holder = os.open(state / "horizon-prior.lock", os.O_RDWR | os.O_CREAT)
    try:
        held = ro._lock_try(holder)
        ok("V-HW-REFRESH-ONE-BUILDER", held and ec.refresh_prior(state) == "busy")
    finally:
        os.close(holder)
    print(f"HORIZON_WIRING_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
