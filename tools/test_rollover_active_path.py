#!/usr/bin/env python3
"""V-ROLLACT-* gates for the ACTIVE rollover path in context-watchdog.py.

Spec: vault/specs/interactive-context-rollover.md §7 (Owner decision 2026-09-28).

The chain is: wall asks `/kclear` -> rollover.py judges the capsule it sealed -> only a
SAFE_TO_FORGET verdict licenses `/clear` -> the successor runs `/kresume`. These gates own
the destructive half. Every refusal is paired with a control in which the verdict is good
and `/clear` IS dispatched, so a path that refused everything cannot pass here.

Hermetic: the gate is stubbed per case, the dispatcher is a recorder, and no keystroke is
ever produced. rollover.py's own judgement is proven in tools/test_rollover.py.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"

# Everything the watchdog writes goes to a private dir. Before this, the suite appended to the
# REAL gsd-autorun ledger and heartbeat log (tools/test_state_isolation.py, 2026-09-28).
_TMP = Path(tempfile.mkdtemp(prefix="rollact-"))
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(_TMP / "state"),
                   "GSD_LONG_RUN_SESSIONS_DIR": str(_TMP / "sessions"),
                   "GSD_AUTORUN_MARKER_DIR": str(_TMP / "state"),
                   "CPP_ROLLOVER_STATE_DIR": str(_TMP / "rollover"),
                   "CTXWD_HEARTBEAT_LOG": str(_TMP / "context-watchdog.log"),
                   "CTXWD_SNAPSHOT_LEDGER": str(_TMP / "context_snapshots.jsonl")})
for _d in ("state", "sessions", "rollover"):
    (_TMP / _d).mkdir()

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def load():
    sys.path.insert(0, str(WATCHDOG.parent))
    spec = importlib.util.spec_from_file_location("ctxwd_rollact", WATCHDOG)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ctxwd_rollact"] = mod
    spec.loader.exec_module(mod)
    return mod


def sid() -> str:
    return f"rollact-{uuid.uuid4().hex[:12]}"


def clear(wd, s):
    for f in (wd.ROLLOVER_ASK_FLAG, wd.ROLLOVER_CLEAR_FLAG, wd.ROLLOVER_WAIT_FLAG,
              wd.ROLLOVER_INFLIGHT_FLAG, wd.ADVISORY_FLAG, wd.SNAPSHOT_FLAG):
        wd._clear_flag(s, f)


def main() -> int:
    wd = load()
    calls: list = []
    wd._dispatch_continuation = lambda s_, kind, **k: calls.append(dict(k, kind=kind)) or \
        {"route": "orca-exact", "pane_key": "stub"}

    def with_verdict(v, reasons=()):
        wd._rollover_gate = lambda s_: {"verdict": v, "reasons": list(reasons), "rc": 0}

    print("the destructive step: /clear is dispatched only on SAFE_TO_FORGET")

    # CONTROL. Without a case where /clear IS dispatched, every refusal below is satisfied
    # by a path that never dispatches anything at all.
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("SAFE_TO_FORGET")
    out = wd._rollover_step(s, str(ROOT), "", 75.0)
    check("V-ROLLACT-GREEN-DISPATCHES-CLEAR",
          len(calls) == 1 and calls[0]["kind"] == "clear"
          and calls[0]["expect_prefix"] == "/clear" and calls[0]["expect_line"] == "/clear"
          and (out or {}).get("decision") == "block",
          f"calls={calls} decision={(out or {}).get('decision')}")
    check("V-ROLLACT-GREEN-TEXT-ASKS-FOR-CLEAR",
          "/clear" in (out or {}).get("reason", "") and "/kresume" in (out or {}).get("reason", ""),
          "the block names the line to emit and who picks the thread up")

    # Idempotence: the flag is set BEFORE the dispatch, so a second Stop cannot type twice.
    out2 = wd._rollover_step(s, str(ROOT), "", 75.0)
    check("V-ROLLACT-CLEAR-DISPATCHED-ONCE", len(calls) == 1 and out2 is None,
          f"second call dispatched={len(calls) - 1}")
    clear(wd, s)

    for gate, verdict, reasons in [
        ("V-ROLLACT-REFUSED-TYPES-NOTHING", "REFUSED", ["obligations: none found"]),
        ("V-ROLLACT-NO-CAPSULE-TYPES-NOTHING", "NO_CAPSULE", ["no capsule_sealed receipt"]),
    ]:
        s = sid(); clear(wd, s); calls.clear()
        with_verdict(verdict, reasons)
        out = wd._rollover_step(s, str(ROOT), "", 75.0)
        check(gate, calls == [] and out is None, f"verdict={verdict} calls={calls} out={out}")
        clear(wd, s)

    print("a capsule that never arrives falls back to /compact, never past the wall")
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("NO_CAPSULE")
    wd._set_flag(s, wd.ADVISORY_FLAG)
    outs = [wd._rollover_step(s, str(ROOT), "", 75.0) for _ in range(wd.ROLLOVER_MAX_WAIT)]
    check("V-ROLLACT-FALLBACK-REARMS-COMPACT",
          calls == [] and all(o is None for o in outs)
          and not wd._flag_exists(s, wd.ADVISORY_FLAG),
          f"after {wd.ROLLOVER_MAX_WAIT} waits the advisory flag is cleared so /compact re-fires")
    check("V-ROLLACT-FALLBACK-STOPS-RETRYING", wd._flag_exists(s, wd.ROLLOVER_CLEAR_FLAG),
          "the rollover leg is closed for this cycle; it does not compete with the compact leg")
    clear(wd, s)

    print("the kill switch, and the ask flag as the entry condition")
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("SAFE_TO_FORGET")
    os.environ["CPP_ROLLOVER_ACTIVE"] = "0"
    try:
        check("V-ROLLACT-KILLSWITCH-OFF", not wd._rollover_active(), "CPP_ROLLOVER_ACTIVE=0")
    finally:
        os.environ.pop("CPP_ROLLOVER_ACTIVE", None)
    check("V-ROLLACT-DEFAULT-ON", wd._rollover_active(),
          "unset is ON -- the Owner's default, on this host and on GEX44")

    # run() must not enter the rollover leg for a session the wall never asked.
    s = sid(); clear(wd, s); calls.clear()
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = "20.0"
    try:
        wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""})
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
    check("V-ROLLACT-NO-ASK-NO-STEP", calls == [],
          "a session that never crossed the wall is never asked to clear")
    clear(wd, s)

    # The wall itself. /kclear is the MODEL's work (a skill), not a keystroke: measured
    # 2026-09-29, a trailing `/kclear` line on a terminal no extension owned was refused and
    # never ran across three walls, while invoking the skill directly sealed SAFE_TO_FORGET.
    print("the wall asks the model to seal the capsule itself, and types nothing")
    s = sid(); clear(wd, s); calls.clear()
    proj = _TMP / f"proj-{s}"
    proj.mkdir()
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = "90.0"
    try:
        out = wd.run({"session_id": s, "cwd": str(proj), "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
    reason = out.get("reason", "")
    check("V-ROLLACT-WALL-BLOCKS", out.get("decision") == "block" and "CONTEXT THRESHOLD" in reason,
          f"decision={out.get('decision')} reason={reason[:80]!r}")
    check("V-ROLLACT-WALL-NO-KCLEAR-KEYSTROKE", not [c for c in calls if c["kind"] == "kclear"],
          f"dispatched kinds={[c['kind'] for c in calls]}")
    check("V-ROLLACT-WALL-NAMES-THE-SKILL",
          "`kclear` skill" in reason and "Do NOT end on a trailing `/kclear` line" in reason,
          "the model is told to invoke the skill, and told the trailing line does nothing")
    check("V-ROLLACT-WALL-NO-TRAILING-ASK", "exactly `/kclear`" not in reason,
          "the old ask for a trailing line is gone")
    check("V-ROLLACT-WALL-SETS-ASK-FLAG", wd._flag_exists(s, wd.ROLLOVER_ASK_FLAG),
          "step 2 (the gated /clear) still runs on the next Stop")
    clear(wd, s)

    # A /kclear the wall never asked for (the Owner's, the model's, the breaker's) is the same
    # request to cross. Measured 2026-10-06 (d64f90b2): it sealed SAFE_TO_FORGET and ended as a
    # sentence asking the Owner to type /clear, because step 2 was reachable only via ASK.
    print("a self-sealed capsule crosses on its own, once per seal")
    sys.path.insert(0, str(ROOT / "tools"))
    import rollover  # noqa: E402 -- after CPP_ROLLOVER_STATE_DIR is set above
    couriers: list = []
    wd._spawn_kresume_courier = lambda s_, cwd, tr: couriers.append(s_) or True
    events: list = []
    _real_ledger = wd._ledger
    wd._ledger = lambda s_, ev, **k: events.append(ev) or _real_ledger(s_, ev, **k)

    def self_case(wdm, seal=True, age_s=0.0, certified=False):
        s_ = sid(); clear(wdm, s_); calls.clear(); couriers.clear(); events.clear()
        (Path(tempfile.gettempdir()) / wdm.ROLLOVER_SELF_SEAL_FLAG.format(session_id=s_)).unlink(
            missing_ok=True)
        cap = wdm._own_capsule(s_)
        if seal:
            cap.parent.mkdir(parents=True, exist_ok=True)
            cap.write_text("{}", encoding="utf-8")
            if age_s:
                t = time.time() - age_s
                os.utime(cap, (t, t))
            if certified:
                cap.with_suffix(".certified").write_text("x", encoding="utf-8")
        return s_, cap

    check("V-ROLLACT-SELF-CAPSULE-PATH-PINNED",
          wd._own_capsule("a b/c") == rollover.capsule_path("a b/c"),
          f"{wd._own_capsule('a b/c')} vs {rollover.capsule_path('a b/c')}")
    check("V-ROLLACT-SELF-MAX-AGE-PINNED",
          wd.ROLLOVER_SELF_SEAL_MAX_AGE_S == rollover.RESET_MAX_AGE_S,
          f"{wd.ROLLOVER_SELF_SEAL_MAX_AGE_S} vs {rollover.RESET_MAX_AGE_S}")

    # CONTROL: a fresh own capsule, gate SAFE_TO_FORGET -> /clear typed, courier armed.
    with_verdict("SAFE_TO_FORGET")
    s, cap = self_case(wd)
    out = wd._self_sealed_step(s, str(ROOT), "", 30.0)
    check("V-ROLLACT-SELF-GREEN-DISPATCHES",
          [c["kind"] for c in calls] == ["clear"] and couriers == [s]
          and "rollover_self_sealed" in events and "rollover_clear_dispatched" in events
          and (out or {}).get("decision") == "block",
          f"calls={[c['kind'] for c in calls]} couriers={len(couriers)} events={events}")

    # Same seal again after the rearm wiped ASK/CLEAR at a low reading: one act per seal.
    clear(wd, s); calls.clear(); couriers.clear()
    out2 = wd._self_sealed_step(s, str(ROOT), "", 5.0)
    check("V-ROLLACT-SELF-ONE-ACT-PER-SEAL", calls == [] and couriers == [] and out2 is None,
          f"re-dispatched={len(calls)} after rearm")
    # A new /kclear is a new seal and IS acted on.
    clear(wd, s); calls.clear()
    t = time.time() + 2
    os.utime(cap, (t, t))
    out3 = wd._self_sealed_step(s, str(ROOT), "", 5.0)
    check("V-ROLLACT-SELF-RESEAL-ACTS", [c["kind"] for c in calls] == ["clear"]
          and (out3 or {}).get("decision") == "block", f"calls={[c['kind'] for c in calls]}")
    clear(wd, s)

    # The real Stop path at a LOW reading (the manual /kclear case): no ask flag, still crosses.
    s, cap = self_case(wd)
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = "20.0"
    try:
        out = wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
    check("V-ROLLACT-SELF-STOP-PATH-CROSSES",
          [c["kind"] for c in calls] == ["clear"] and out.get("decision") == "block"
          and "`/clear`" in out.get("reason", ""),
          f"calls={[c['kind'] for c in calls]} decision={out.get('decision')}")
    clear(wd, s)

    # The same Stop with the overlay NOT throttled. Measured 2026-10-06 (e0332e3a): the first
    # Stop after a manual /kclear ran the auto-reset overlay first, the dispatcher killed the
    # hook at 20 s, and /clear was never typed. The crossing must not queue behind the advisory.
    s, cap = self_case(wd)
    overlay_calls: list = []
    real_overlay = wd._orchestrator_overlay
    wd._orchestrator_overlay = lambda ev: overlay_calls.append(ev) or {"systemMessage": "advisory"}
    os.environ["_TEST_CONTEXT_PCT"] = "20.0"
    try:
        out = wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
        wd._orchestrator_overlay = real_overlay
    check("V-ROLLACT-SELF-CROSSES-AHEAD-OF-OVERLAY",
          [c["kind"] for c in calls] == ["clear"] and out.get("decision") == "block"
          and overlay_calls == [],
          f"calls={[c['kind'] for c in calls]} decision={out.get('decision')} "
          f"overlay_ran={len(overlay_calls)}")
    clear(wd, s)
    # Control: with nothing sealed, the overlay still runs and its advisory still surfaces.
    s, cap = self_case(wd, seal=False)
    overlay_calls.clear()
    wd._orchestrator_overlay = lambda ev: overlay_calls.append(ev) or {"systemMessage": "advisory"}
    os.environ["_TEST_CONTEXT_PCT"] = "20.0"
    try:
        out = wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
        wd._orchestrator_overlay = real_overlay
    check("V-ROLLACT-OVERLAY-STILL-SURFACES", len(overlay_calls) == 1 and calls == []
          and out.get("systemMessage") == "advisory",
          f"overlay_ran={len(overlay_calls)} calls={calls} out={out}")
    clear(wd, s)

    for gate, kw, verdict, marker in [
        ("V-ROLLACT-SELF-REFUSED-TYPES-NOTHING", {}, "REFUSED", None),
        ("V-ROLLACT-SELF-STALE-TYPES-NOTHING", {"age_s": wd.ROLLOVER_SELF_SEAL_MAX_AGE_S + 60},
         "SAFE_TO_FORGET", None),
        ("V-ROLLACT-SELF-CERTIFIED-TYPES-NOTHING", {"certified": True}, "SAFE_TO_FORGET", None),
        ("V-ROLLACT-SELF-NO-CAPSULE-TYPES-NOTHING", {"seal": False}, "SAFE_TO_FORGET", None),
        ("V-ROLLACT-SELF-MISSION-TYPES-NOTHING", {}, "SAFE_TO_FORGET", {"mission_id": "m-1"}),
    ]:
        with_verdict(verdict, ["stub"])
        real_marker = wd._read_autorun_marker
        wd._read_autorun_marker = lambda s_, m=marker: m
        try:
            s, cap = self_case(wd, **kw)
            out = wd._self_sealed_step(s, str(ROOT), "", 30.0)
            check(gate, calls == [] and couriers == [] and out is None,
                  f"calls={calls} couriers={couriers} out={out}")
            if verdict == "REFUSED":
                calls.clear()
                with_verdict("SAFE_TO_FORGET")
                clear(wd, s)
                again = wd._self_sealed_step(s, str(ROOT), "", 30.0)
                check("V-ROLLACT-SELF-REFUSED-NOT-RETRIED", calls == [] and again is None,
                      "a refused seal is not re-judged on later Stops; a new /kclear is")
        finally:
            wd._read_autorun_marker = real_marker
            clear(wd, s)

    # Red control: without the per-seal flag, the same seal is dispatched again after the rearm
    # -- the block loop the flag exists to prevent. The mutant MUST fail the one-act property.
    src = WATCHDOG.read_text(encoding="utf-8")
    needle = "return None                              # this seal was already acted on"
    check("V-ROLLACT-SELF-MUTANT-APPLIES", src.count(needle) == 1, "the mutation site is unique")
    mspec = importlib.util.spec_from_loader("ctxwd_rollact_mut", loader=None)
    mut = importlib.util.module_from_spec(mspec)
    mut.__file__ = str(WATCHDOG)
    exec(compile(src.replace(needle, "pass"), str(WATCHDOG), "exec"), mut.__dict__)
    mut._dispatch_continuation = wd._dispatch_continuation
    mut._spawn_kresume_courier = wd._spawn_kresume_courier
    mut._rollover_gate = lambda s_: {"verdict": "SAFE_TO_FORGET", "reasons": [], "rc": 0}
    s, cap = self_case(mut)
    mut._self_sealed_step(s, str(ROOT), "", 30.0)
    clear(mut, s)
    mut._self_sealed_step(s, str(ROOT), "", 5.0)
    check("V-ROLLACT-SELF-MUTANT-GOES-RED", len(calls) == 2,
          f"mutant dispatched {len(calls)}x for one seal (the real hook: 1x)")
    clear(mut, s)

    print("a /clear in flight is not withdrawn by the next Stop (measured 2026-10-06, eab8a573)")
    # The incident: Stop 1 dispatched /clear (inbox deferred it, status-busy); Stop 2 at 48 % fell
    # through to the tier-2 block, the turn re-opened, the daemon WITHDREW the line. Replay it.
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("SAFE_TO_FORGET")
    wd._set_flag(s, wd.ROLLOVER_ASK_FLAG)
    first = wd._rollover_step(s, str(ROOT), "", 48.0)
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = "48.0"
    try:
        second = wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
    check("V-ROLLACT-INFLIGHT-STOP-STAYS-QUIET",
          (first or {}).get("decision") == "block" and len(calls) == 1
          and second.get("decision") != "block",
          f"first={(first or {}).get('decision')} dispatches={len(calls)} second={second}")
    # Control: past the daemon's window the flag no longer mutes the wall.
    flag = Path(tempfile.gettempdir()) / wd.ROLLOVER_INFLIGHT_FLAG.format(session_id=s)
    old = time.time() - wd.ROLLOVER_INFLIGHT_MAX_AGE_S - 60
    os.utime(flag, (old, old))
    check("V-ROLLACT-INFLIGHT-EXPIRES", not wd._clear_in_flight(s),
          "a /clear that never landed cannot silence the wall forever")
    clear(wd, s)
    # Control: the compact fallback sets CLEAR but is NOT in flight (it needs the tier-2 path).
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("NO_CAPSULE")
    for _ in range(wd.ROLLOVER_MAX_WAIT):
        wd._rollover_step(s, str(ROOT), "", 75.0)
    check("V-ROLLACT-FALLBACK-NOT-INFLIGHT",
          wd._flag_exists(s, wd.ROLLOVER_CLEAR_FLAG) and not wd._clear_in_flight(s),
          "fallback closes the rollover leg without muting the compact leg")
    clear(wd, s)

    # Measured 2026-10-06 (1a9ec524): the daemon ledgered `withdrawn` at 20:04:57 (a peer message
    # re-opened the turn), the next Stops stayed quiet "in flight" anyway, and a second /kclear at
    # 20:10 sealed SAFE_TO_FORGET with nothing dispatched -- ASK/CLEAR were still set, so step 2
    # returned None at its first line. The Owner typed /clear. Replay it.
    print("a withdrawn /clear is over, and a fresh seal after it crosses again")
    ledger = _TMP / "state" / "gsd-autorun-ledger.jsonl"

    def daemon_row(s_, event, at=None):
        # Byte-shaped like auto-compact-sendkeys-daemon.ps1 Write-LedgerRow: compact, seconds.
        ts = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(at if at is not None else time.time()))
        with open(ledger, "a", encoding="utf-8") as fh:
            fh.write('{"detail":"terminal inbox %s","session_id":"%s","event":"%s","ts":"%s"}\n'
                     % (event, s_, event, ts))

    def dispatched_case():
        s_, cap_ = self_case(wd)
        calls.clear()
        with_verdict("SAFE_TO_FORGET")
        wd._set_flag(s_, wd.ROLLOVER_ASK_FLAG)
        old_seal = time.time() - 5
        os.utime(cap_, (old_seal, old_seal))      # sealed before the dispatch, as in the incident
        wd._rollover_step(s_, str(ROOT), "", 45.0)
        # The daemon's outcome follows the model's reply, seconds after the dispatch: date the
        # dispatch back so an outcome stamped "now" is unambiguously newer (whole-second stamps).
        back = time.time() - 3
        for f in (wd.ROLLOVER_CLEAR_FLAG, wd.ROLLOVER_INFLIGHT_FLAG):
            os.utime(Path(tempfile.gettempdir()) / f.format(session_id=s_), (back, back))
        return s_, cap_

    s, cap = dispatched_case()
    check("V-ROLLACT-INFLIGHT-UNTIL-OUTCOME", len(calls) == 1 and wd._clear_in_flight(s),
          "no daemon outcome yet: the request is still live (control)")
    daemon_row(s, "withdrawn")
    check("V-ROLLACT-WITHDRAWN-NOT-INFLIGHT", not wd._clear_in_flight(s),
          "the daemon's own `withdrawn` row ends the request; the wall is not muted for 600 s")
    clear(wd, s)

    s, cap = dispatched_case()
    daemon_row(s, "refused")
    check("V-ROLLACT-REFUSED-NOT-INFLIGHT", not wd._clear_in_flight(s), "`refused` ends it too")
    clear(wd, s)

    s, cap = dispatched_case()
    daemon_row(s, "withdrawn", at=time.time() - 120)      # an earlier cycle's outcome
    daemon_row(sid(), "withdrawn")                        # another session's outcome
    check("V-ROLLACT-OLD-OR-FOREIGN-OUTCOME-STILL-INFLIGHT", wd._clear_in_flight(s),
          "only THIS session's outcome, newer than THIS dispatch, ends it")
    clear(wd, s)

    # The loop guard: the SAME seal is never re-dispatched after a withdrawal.
    s, cap = dispatched_case()
    daemon_row(s, "withdrawn")
    again = wd._rollover_step(s, str(ROOT), "", 45.0)
    check("V-ROLLACT-WITHDRAWN-SAME-SEAL-NOT-RETRIED", len(calls) == 1 and again is None,
          f"dispatches={len(calls)} -- a retry needs a new /kclear, or a busy turn would loop")
    # A NEW seal after the withdrawal IS acted on, through the same gate.
    t = time.time() + 2
    os.utime(cap, (t, t))
    out = wd._rollover_step(s, str(ROOT), "", 48.0)
    check("V-ROLLACT-RESEAL-AFTER-WITHDRAW-REDISPATCHES",
          [c["kind"] for c in calls] == ["clear", "clear"] and (out or {}).get("decision") == "block",
          f"calls={[c['kind'] for c in calls]} decision={(out or {}).get('decision')}")
    check("V-ROLLACT-RESEAL-REDISPATCH-IS-INFLIGHT", wd._clear_in_flight(s),
          "the re-dispatch is a live request again, and quiets the Stops after it")
    clear(wd, s)

    # A new seal while the first /clear is STILL live does not dispatch a second one over it.
    s, cap = dispatched_case()
    t = time.time() + 2
    os.utime(cap, (t, t))
    out = wd._rollover_step(s, str(ROOT), "", 48.0)
    check("V-ROLLACT-RESEAL-WHILE-INFLIGHT-WAITS", len(calls) == 1 and out is None,
          f"dispatches={len(calls)}")
    clear(wd, s)

    # A refused gate on the new seal types nothing (the gate stays the only authority).
    s, cap = dispatched_case()
    daemon_row(s, "withdrawn")
    t = time.time() + 2
    os.utime(cap, (t, t))
    with_verdict("REFUSED", ["stub"])
    out = wd._rollover_step(s, str(ROOT), "", 48.0)
    check("V-ROLLACT-RESEAL-REFUSED-TYPES-NOTHING", len(calls) == 1 and out is None,
          f"dispatches={len(calls)}")
    clear(wd, s)

    # The whole incident through run(): withdrawn, re-sealed, next Stop at 48 % crosses.
    s, cap = dispatched_case()
    daemon_row(s, "withdrawn")
    t = time.time() + 2
    os.utime(cap, (t, t))
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = "48.0"
    try:
        out = wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
    check("V-ROLLACT-INCIDENT-REPLAY-CROSSES",
          [c["kind"] for c in calls] == ["clear", "clear"] and out.get("decision") == "block"
          and "`/clear`" in out.get("reason", ""),
          f"calls={[c['kind'] for c in calls]} decision={out.get('decision')}")
    clear(wd, s)

    # Red control: without the in-flight check, a re-seal types a second /clear over a live one.
    src = WATCHDOG.read_text(encoding="utf-8")
    needle = "    if _clear_in_flight(session_id):\n        return False\n    cap = _own_capsule(session_id)"
    check("V-ROLLACT-RESEAL-MUTANT-APPLIES", src.count(needle) == 1, "the mutation site is unique")
    mut2 = importlib.util.module_from_spec(importlib.util.spec_from_loader("ctxwd_reseal_mut", loader=None))
    mut2.__file__ = str(WATCHDOG)
    exec(compile(src.replace(needle, "    cap = _own_capsule(session_id)"), str(WATCHDOG), "exec"),
         mut2.__dict__)
    mut2._dispatch_continuation = wd._dispatch_continuation
    mut2._spawn_kresume_courier = wd._spawn_kresume_courier
    mut2._rollover_gate = lambda s_: {"verdict": "SAFE_TO_FORGET", "reasons": [], "rc": 0}
    s, cap = dispatched_case()
    t = time.time() + 2
    os.utime(cap, (t, t))
    mut2._rollover_step(s, str(ROOT), "", 48.0)
    check("V-ROLLACT-RESEAL-MUTANT-GOES-RED", len(calls) == 2,
          f"mutant dispatched {len(calls)}x over a live /clear (the real hook: 1x)")
    clear(wd, s)

    print(f"ROLLACT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
