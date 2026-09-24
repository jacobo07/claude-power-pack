#!/usr/bin/env python3
"""V-gates for the KEOS-Qwen shared-endpoint ledger.

Every refusal is paired with an admitted control. A ledger that refused
everything would pass all five refusal assertions and be indistinguishable from
one that works -- and it would also be indistinguishable from an outage, which
is the failure mode that matters here: the endpoint serves one model on a host
running 15 production services, so a ledger stuck at "no" is a silent shutdown.

    python tools/test_keos_qwen_ledger.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from modules.keos_qwen.ledger import ledger as L  # noqa: E402
except Exception as exc:  # noqa: BLE001 -- the precondition, not the subject
    print(f"HARNESS-FAILED: modules.keos_qwen.ledger did not import from {ROOT}: "
          f"{exc.__class__.__name__}: {exc}")
    raise SystemExit(2)


def main() -> int:
    passes: list = []
    fails: list = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    def fresh() -> Path:
        d = Path(tempfile.mkdtemp(prefix="keosq_ledger_"))
        return d

    NOENV: dict = {}

    # --- the admitted control, first ----------------------------------------
    r = fresh()
    d = L.decide(str(r), budget=200, env=NOENV)
    check("V-KEOSQ-LEDGER-ALLOW-CLEAN", d.allowed and d.verdict == L.ALLOW,
          f"a clean ledger allows: {d.reason} (control: without this, every "
          f"refusal below would pass against a decide() stuck at no)",
          f"a clean ledger refused: {d.to_dict()}")

    # --- kill switches, both poles ------------------------------------------
    d = L.decide(str(r), env={L.DISABLED_ENV_VAR: "1"})
    check("V-KEOSQ-LEDGER-ENV-KILL", d.verdict == L.DISABLED_ENV,
          "the environment switch refuses", f"got {d.to_dict()}")
    d = L.decide(str(r), env={L.DISABLED_ENV_VAR: "0"})
    check("V-KEOSQ-LEDGER-ENV-FALSY", d.allowed,
          "'0' does not kill (control: a truthiness test that treated any value "
          "as set would make the variable impossible to turn off)",
          f"'0' was treated as enabled: {d.to_dict()}")

    r2 = fresh()
    (r2 / "DISABLED").write_text("owner stopped the loop at 19:40", encoding="utf-8")
    d = L.decide(str(r2), env=NOENV)
    check("V-KEOSQ-LEDGER-FLAG-KILL",
          d.verdict == L.DISABLED_FLAG and "19:40" in d.reason,
          "the flag file refuses AND carries its own recorded reason -- this is "
          "the switch that stops a loop already running, which an env var cannot",
          f"got {d.to_dict()}")

    r3 = fresh()
    (r3 / "DISABLED").write_text("   ", encoding="utf-8")
    d = L.decide(str(r3), env=NOENV)
    check("V-KEOSQ-LEDGER-FLAG-EMPTY-REASON",
          d.verdict == L.DISABLED_FLAG and "no reason recorded" in d.reason,
          "an empty flag still refuses and says the reason is missing",
          f"got {d.to_dict()}")

    # --- budget, and the boundary ------------------------------------------
    r4 = fresh()
    for i in range(199):
        L.record(str(r4), caller="gate", outcome="OK", detail=f"n{i}")
    d = L.decide(str(r4), budget=200, env=NOENV)
    check("V-KEOSQ-LEDGER-BUDGET-BOUNDARY-ALLOW", d.allowed and d.used_today == 199,
          "199 of 200 still allows (the off-by-one control)", f"got {d.to_dict()}")
    L.record(str(r4), caller="gate", outcome="OK", detail="n199")
    d = L.decide(str(r4), budget=200, env=NOENV)
    check("V-KEOSQ-LEDGER-BUDGET-EXHAUSTED",
          d.verdict == L.BUDGET_EXHAUSTED and "200" in d.reason,
          f"200 of 200 refuses and names the ceiling: {d.reason}", f"got {d.to_dict()}")

    r5 = fresh()
    yesterday = time.time() - 86400 * 2
    for i in range(50):
        L.record(str(r5), caller="gate", now=yesterday, detail=f"old{i}")
    d = L.decide(str(r5), budget=10, env=NOENV)
    check("V-KEOSQ-LEDGER-DAY-SCOPED", d.allowed and d.used_today == 0,
          "calls from another UTC day do not spend today's budget",
          f"old calls counted toward today: {d.to_dict()}")

    # --- cooldown, both poles ----------------------------------------------
    r6 = fresh()
    (r6 / "cooldown").write_text(str(time.time() + 600), encoding="utf-8")
    d = L.decide(str(r6), env=NOENV)
    check("V-KEOSQ-LEDGER-COOLDOWN-FUTURE", d.verdict == L.COOLDOWN,
          f"a future cooldown refuses: {d.reason}", f"got {d.to_dict()}")
    (r6 / "cooldown").write_text(str(time.time() - 600), encoding="utf-8")
    d = L.decide(str(r6), env=NOENV)
    check("V-KEOSQ-LEDGER-COOLDOWN-PAST", d.allowed,
          "an expired cooldown allows (control: a cooldown that never expired "
          "would be a permanent outage wearing a timestamp)", f"got {d.to_dict()}")

    # --- the lock, and the dead holder that must not wedge the endpoint -----
    check("V-KEOSQ-LEDGER-PID-ALIVE-SELF", L._pid_alive(os.getpid()) is True,
          f"our own pid {os.getpid()} reads as alive (control for the check below)",
          "our own pid read as dead; the liveness test is broken")

    dead = 0
    for candidate in range(999999, 900000, -7):
        if not L._pid_alive(candidate):
            dead = candidate
            break
    check("V-KEOSQ-LEDGER-PID-DEAD-FOUND", dead > 0,
          f"found a pid that is not running ({dead}) to drive the steal case",
          "could not find a dead pid; the steal case below cannot be driven")

    r7 = fresh()
    (r7 / "lock.json").write_text(json.dumps({"pid": os.getpid(), "ts": time.time()}),
                                  encoding="utf-8")
    d = L.decide(str(r7), env=NOENV)
    check("V-KEOSQ-LEDGER-LOCK-LIVE", d.verdict == L.LOCK_HELD,
          f"a lock held by a LIVE process refuses: {d.reason}", f"got {d.to_dict()}")

    (r7 / "lock.json").write_text(json.dumps({"pid": dead, "ts": time.time()}), encoding="utf-8")
    d = L.decide(str(r7), env=NOENV)
    check("V-KEOSQ-LEDGER-LOCK-DEAD-STEALS", d.allowed,
          "a lock held by a DEAD process is stolen -- a crash must not wedge the "
          "endpoint forever, which is how a safety mechanism becomes the incident",
          f"a dead holder still blocked us: {d.to_dict()}")

    (r7 / "lock.json").write_text(
        json.dumps({"pid": os.getpid(), "ts": time.time() - L.LOCK_STALE_S - 10}),
        encoding="utf-8")
    d = L.decide(str(r7), env=NOENV)
    check("V-KEOSQ-LEDGER-LOCK-STALE-STEALS", d.allowed,
          f"a lock older than {L.LOCK_STALE_S:.0f}s is stolen even from a live pid",
          f"a stale lock still blocked us: {d.to_dict()}")

    # --- damage vs refusal: the distinction that sends people to the right fix
    r8 = fresh()
    L.record(str(r8), caller="gate", detail="good")
    with (r8 / "calls.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"ts": 1.0, "day": "2026-')  # a killed process, mid-write
    d = L.decide(str(r8), budget=200, env=NOENV)
    check("V-KEOSQ-LEDGER-MALFORMED-SKIPPED", d.allowed and d.used_today == 1,
          "a truncated line is skipped, not fatal: a killed writer must not make "
          "the budget unreadable, because an unreadable budget refuses everything",
          f"got {d.to_dict()}")

    r9 = fresh()
    (r9 / "calls.jsonl").mkdir()  # unreadable as a file, on either platform
    try:
        d = L.decide(str(r9), env=NOENV)
        bad("V-KEOSQ-LEDGER-UNREADABLE-RAISES",
            f"an unreadable ledger returned a verdict instead of raising: {d.to_dict()}")
    except L.LedgerError as exc:
        ok("V-KEOSQ-LEDGER-UNREADABLE-RAISES",
           f"an unreadable ledger raises rather than refusing ({exc.__class__.__name__}): "
           "'we could not read it' and 'it says no' send an operator to different fixes")

    check("V-KEOSQ-LEDGER-REFUSALS-DISTINCT",
          len(set(L.REFUSALS)) == len(L.REFUSALS) and L.ALLOW not in L.REFUSALS,
          f"the {len(L.REFUSALS)} refusal codes are distinct and none of them is ALLOW",
          f"refusal codes collide: {L.REFUSALS}")

    rec = L.record(str(fresh()), caller="elixir", outcome="UNAVAILABLE", detail="tunnel down")
    check("V-KEOSQ-LEDGER-RECORD-COUNTS-UNANSWERED",
          rec["outcome"] == "UNAVAILABLE" and rec["caller"] == "elixir",
          "a call the endpoint never answered is still RECORDED as made -- it "
          "consumed the endpoint's attention -- while staying unclassifiable as "
          "a model failure",
          f"got {rec}")

    total = len(passes) + len(fails)
    print(f"\nKEOSQ_LEDGER_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
