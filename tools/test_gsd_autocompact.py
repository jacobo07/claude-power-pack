#!/usr/bin/env python
"""V-GSDAC-* — done-gate for the /gsd-autonomous auto-compact work.

Spec: vault/specs/gsd-autonomous-autocompact.md

Covers what is actually shipped today:
  * gap B — tier-2 rearm in context-watchdog.py (both poles + the band edge)
  * the autorun marker's write/read/clear contract and its refusals

Gap C (typing the resume command) is NOT covered because it is not shipped:
the auto-mode classifier refused the keystroke daemon. A gate asserting
something green about an unbuilt capability would be the exact "presence read
as health" failure the Liveness Standard exists to stop.

Hermetic: every flag and marker it touches is namespaced to a synthetic
session id it creates and deletes. It never reads the real session's metrics
(``_TEST_CONTEXT_PCT`` bypasses the metrics file) and never lets the
orchestrator overlay spawn its PowerShell RAM probe (the module's own throttle
flag is pre-stamped).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
MARKER_TOOL = ROOT / "tools" / "gsd_autorun_marker.py"
CONFIG_TOOL = ROOT / "tools" / "gsd_long_run_config.py"

# Ledger rows and config backups (spec gsd-long-run-v2.md) go to a throwaway
# dir: this suite must not write test sessions into the Owner's real ledger.
os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="gsdac-state-")

# PROBE POINTS ARE ABSOLUTE, DELIBERATELY. The first version of this gate
# computed them as THRESHOLD_REARM_PCT +/- n, so moving the constant moved the
# probes with it: a mutation of the floor to 0 still scored 10/10. A gate that
# derives its subject from the thing it judges cannot fail. These numbers are
# what the readings MEAN -- 25% is a post-compaction context, 50% is a mid-run
# context that has not compacted -- and must never be re-derived from the
# module under test.
POST_COMPACTION_PCT = 25.0
MID_RUN_PCT = 50.0

# The floor must sit inside this band for the two probes to mean what they
# claim. Pinned independently so a constant moved out of range is named here
# instead of silently relabelling the probes.
REARM_FLOOR_MIN = 30.0

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _stamp_orch_throttle(wd, session_id: str) -> None:
    """Pre-stamp the overlay throttle so run() never spawns the RAM probe."""
    flag = Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(
        session_id=session_id)
    flag.write_text(str(time.time()), encoding="utf-8")


def _boundary_transcript(session_id: str) -> Path:
    """A transcript whose compact_boundary postdates the marker.

    Since C1 (spec exact-target-continuation.md) a resume is requested only
    when a real boundary row is newer than the cycle reference; an empty
    transcript path is exactly the false-"landed" shape the incident had.
    """
    t = Path(tempfile.mkdtemp(prefix="gsdac-tx-")) / f"{session_id}.jsonl"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + 2)) + ".000Z"
    rows = [{"type": "system", "cwd": str(ROOT)},
            {"type": "system", "subtype": "compact_boundary", "uuid": uuid.uuid4().hex,
             "timestamp": stamp, "compactMetadata": {"trigger": "auto"}}]
    t.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return t


def _run_at(wd, session_id: str, pct: float, tp="") -> dict:
    os.environ["_TEST_CONTEXT_PCT"] = str(pct)
    try:
        return wd.run({"session_id": session_id, "cwd": str(ROOT),
                       "transcript_path": str(tp or "")}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)


def gate_thresholds(wd) -> None:
    """Positive control + the band invariant the rearm depends on."""
    if not hasattr(wd, "THRESHOLD_REARM_PCT"):
        _fail("V-GSDAC-CONTROL-LOADED",
              "watchdog module exposes no THRESHOLD_REARM_PCT — nothing under test")
        return
    _ok("V-GSDAC-CONTROL-LOADED",
        f"rearm={wd.THRESHOLD_REARM_PCT} snapshot={wd.THRESHOLD_SNAPSHOT_PCT} "
        f"advisory={wd.THRESHOLD_ADVISORY_PCT}")

    if not (wd.THRESHOLD_SNAPSHOT_PCT < wd.THRESHOLD_ADVISORY_PCT):
        _fail("V-GSDAC-BAND-ORDERED",
              "snapshot floor must sit below the advisory floor")
    elif not (REARM_FLOOR_MIN <= wd.THRESHOLD_REARM_PCT < wd.THRESHOLD_SNAPSHOT_PCT):
        _fail("V-GSDAC-BAND-ORDERED",
              f"rearm floor {wd.THRESHOLD_REARM_PCT} is outside "
              f"[{REARM_FLOOR_MIN}, {wd.THRESHOLD_SNAPSHOT_PCT}) — a floor this "
              "low never rearms (single-cycle runs), one this high rearms "
              "mid-run and re-checkpoints every Stop")
    else:
        _ok("V-GSDAC-BAND-ORDERED",
            f"{REARM_FLOOR_MIN} <= {wd.THRESHOLD_REARM_PCT} "
            f"< {wd.THRESHOLD_SNAPSHOT_PCT} < {wd.THRESHOLD_ADVISORY_PCT}")


def gate_rearm(wd) -> None:
    sid = f"gsdac-{uuid.uuid4().hex[:12]}"
    _stamp_orch_throttle(wd, sid)

    # --- RED POLE: a post-compaction reading must clear the debounce.
    wd._set_flag(sid, wd.ADVISORY_FLAG)
    if not wd._flag_exists(sid, wd.ADVISORY_FLAG):
        _fail("V-GSDAC-REARM-FIRES",
              "could not establish the precondition (flag did not get set) — "
              "inconclusive, not a pass")
    else:
        _run_at(wd, sid, POST_COMPACTION_PCT)
        if wd._flag_exists(sid, wd.ADVISORY_FLAG):
            _fail("V-GSDAC-REARM-FIRES",
                  f"advisory flag survived a {POST_COMPACTION_PCT}% reading — "
                  "tier 2 stays debounced, so the second crossing of a long "
                  "run is silent")
        else:
            _ok("V-GSDAC-REARM-FIRES",
                f"flag cleared at {POST_COMPACTION_PCT}% used")

    # --- GREEN POLE: a mid-run reading must NOT clear it. Raise the floor past
    # this point and tier 2 re-fires (and re-checkpoints) on every Stop.
    wd._set_flag(sid, wd.ADVISORY_FLAG)
    _run_at(wd, sid, MID_RUN_PCT)
    if wd._flag_exists(sid, wd.ADVISORY_FLAG):
        _ok("V-GSDAC-NO-REARM-IN-BAND",
            f"flag preserved at {MID_RUN_PCT}% used")
    else:
        _fail("V-GSDAC-NO-REARM-IN-BAND",
              f"flag was cleared at {MID_RUN_PCT}% used — the rearm floor is "
              "too high and tier 2 would re-fire every Stop")

    # --- Absence is not an error, and it is distinguishable from a clear.
    wd._clear_flag(sid, wd.ADVISORY_FLAG)
    if wd._clear_flag(sid, wd.ADVISORY_FLAG) is False:
        _ok("V-GSDAC-CLEAR-REPORTS-ABSENCE",
            "second clear returned False (nothing to rearm), no exception")
    else:
        _fail("V-GSDAC-CLEAR-REPORTS-ABSENCE",
              "clearing an absent flag reported True — 'rearmed' and 'there "
              "was nothing to rearm' are indistinguishable")


def gate_marker(mk) -> None:
    sid = f"gsdac-{uuid.uuid4().hex[:12]}"
    try:
        path = mk.write_marker(sid, "/gsd-autonomous", cwd=str(ROOT), phase=3)
        data = mk.read_marker(sid)
        if data and data.get("resume_command") == "/gsd-autonomous" \
                and Path(path).is_file():
            _ok("V-GSDAC-MARKER-ROUNDTRIP",
                f"wrote and read back {Path(path).name}")
        else:
            _fail("V-GSDAC-MARKER-ROUNDTRIP", f"round-trip returned {data!r}")

        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if raw.get("phase") == 3 and raw.get("schema_version") == 2 \
                and raw.get("cycles") == 0 and raw.get("armed_at"):
            _ok("V-GSDAC-MARKER-SHAPE", "phase, schema_version 2, cycles=0, armed_at persisted")
        else:
            _fail("V-GSDAC-MARKER-SHAPE", f"unexpected payload {raw!r}")

        # Refusals — each is a command that must never reach a keyboard.
        refusals = {
            "no leading slash": "gsd-autonomous",
            "sendkeys metachar": "/gsd-autonomous --from (3)",
            "multiline": "/gsd-autonomous\n/help",
            "empty": "   ",
            "too long": "/" + ("a" * 250),
        }
        missed = []
        for label, cmd in refusals.items():
            try:
                mk.validate_command(cmd)
                missed.append(label)
            except mk.MarkerError:
                pass
        if missed:
            _fail("V-GSDAC-MARKER-REFUSES",
                  "accepted command shapes that must be refused: "
                  + ", ".join(missed))
        else:
            _ok("V-GSDAC-MARKER-REFUSES",
                f"all {len(refusals)} unsafe shapes refused")

        # Fail-closed on a hand-edited marker: the file exists and parses, but
        # its command is not typeable, so the reader must report absence.
        raw["resume_command"] = "not-a-slash-command"
        Path(path).write_text(json.dumps(raw), encoding="utf-8")
        if mk.read_marker(sid) is None:
            _ok("V-GSDAC-MARKER-FAILS-CLOSED",
                "hand-edited non-slash command read as ABSENT, not as authorization")
        else:
            _fail("V-GSDAC-MARKER-FAILS-CLOSED",
                  "a hand-edited marker was returned as valid authorization")
    finally:
        mk.clear_marker(sid)

    if mk.read_marker(sid) is None:
        _ok("V-GSDAC-MARKER-CLEARED", "marker removed after clear")
    else:
        _fail("V-GSDAC-MARKER-CLEARED", "marker survived clear_marker()")


def gate_resume_clause(wd, mk) -> None:
    """The marker's READER. A writer with no reader is documentation.

    The full tier-2 path is deliberately NOT driven here: it writes vault
    checkpoints, drops the SendKeys trigger flag and spawns the daemon, so
    driving it would dispatch a real compaction into the running session. The
    clause is a pure function for exactly that reason, and the live end-to-end
    crossing stays an Owner-run gate.
    """
    sid = f"gsdac-{uuid.uuid4().hex[:12]}"

    # Negative control first: an ordinary session must be untouched by this.
    if wd._resume_clause(None) == "" and wd._resume_clause({}) == "":
        _ok("V-GSDAC-CLAUSE-EMPTY-WITHOUT-MARKER",
            "no marker yields the empty string — tier-2 message byte-identical")
    else:
        _fail("V-GSDAC-CLAUSE-EMPTY-WITHOUT-MARKER",
              "a session with no autonomous run would have its tier-2 message "
              "altered by this clause")

    if wd._read_autorun_marker(sid) is not None:
        _fail("V-GSDAC-READER-MISSES-WHEN-ABSENT",
              "reader returned a marker for a session that has none")
    else:
        _ok("V-GSDAC-READER-MISSES-WHEN-ABSENT", "absent marker reads as None")

    try:
        mk.write_marker(sid, "/gsd-autonomous", cwd=str(ROOT), phase=4)
        found = wd._read_autorun_marker(sid)
        if found and found.get("resume_command") == "/gsd-autonomous":
            _ok("V-GSDAC-READER-FINDS-MARKER",
                "watchdog resolved and imported the marker contract")
        else:
            _fail("V-GSDAC-READER-FINDS-MARKER",
                  f"watchdog could not read the marker it should see: {found!r} "
                  "— the resume clause would never fire in a real run")

        clause = wd._resume_clause(found)
        if "/gsd-autonomous" in clause and "do NOT stop" in clause \
                and "phase=4" in clause:
            _ok("V-GSDAC-CLAUSE-CARRIES-COMMAND",
                "clause names the command, the phase, and contradicts 'wrap up'")
        else:
            _fail("V-GSDAC-CLAUSE-CARRIES-COMMAND",
                  f"clause missing command/phase/continue instruction: {clause!r}")
    finally:
        mk.clear_marker(sid)


def gate_long_run_config(cfg) -> None:
    """Gap A: GSD's fire-points must end up BELOW the compaction point.

    Driven against a throwaway project directory, never the real one — this
    tool rewrites a config the Owner owns.
    """
    import shutil
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="gsdac-cfg-"))
    try:
        # The ordering that makes gap A a defect at all: GSD must not fire
        # before the watchdog's 30%-remaining compaction.
        if cfg.LONG_RUN_WARNING < 30 and cfg.LONG_RUN_CRITICAL < cfg.LONG_RUN_WARNING:
            _ok("V-GSDAC-CFG-BELOW-COMPACTION",
                f"warning={cfg.LONG_RUN_WARNING} critical={cfg.LONG_RUN_CRITICAL} "
                "both below the 30%-remaining compaction point")
        else:
            _fail("V-GSDAC-CFG-BELOW-COMPACTION",
                  f"warning={cfg.LONG_RUN_WARNING} fires at or before the "
                  "compaction — GSD would still say 'stop' first")

        # Case 1: a project with NO config at all.
        cfg.apply_long_run(root)
        state = cfg.show(root)
        if state["context_warning_threshold"] == cfg.LONG_RUN_WARNING:
            _ok("V-GSDAC-CFG-APPLIES-FROM-ABSENT", "config created and lowered")
        else:
            _fail("V-GSDAC-CFG-APPLIES-FROM-ABSENT", f"got {state!r}")

        cfg.restore(root)
        state = cfg.show(root)
        if state["context_warning_threshold"] is None \
                and state["context_critical_threshold"] is None:
            _ok("V-GSDAC-CFG-RESTORES-ABSENCE",
                "keys absent before are absent after — not reset to a default")
        else:
            _fail("V-GSDAC-CFG-RESTORES-ABSENCE",
                  f"restore invented values the project never had: {state!r}")

        # Case 2: a project that already had its own tuning, plus a sibling
        # key that must survive untouched.
        (root / ".planning").mkdir(parents=True, exist_ok=True)
        (root / ".planning" / "config.json").write_text(
            json.dumps({"hooks": {"context_warning_threshold": 40,
                                  "context_warnings": True},
                        "unrelated": {"keep": "me"}}), encoding="utf-8")
        cfg.apply_long_run(root)
        cfg.apply_long_run(root)          # double-apply must not eat the backup
        cfg.restore(root)
        after = json.loads((root / ".planning" / "config.json").read_text(
            encoding="utf-8"))
        if after["hooks"]["context_warning_threshold"] == 40 \
                and after["hooks"].get("context_warnings") is True \
                and after.get("unrelated", {}).get("keep") == "me":
            _ok("V-GSDAC-CFG-ROUNDTRIP-EXACT",
                "40 restored after a double-apply; siblings untouched")
        else:
            _fail("V-GSDAC-CFG-ROUNDTRIP-EXACT",
                  f"config did not round-trip: {after!r}")

        # A config that does not parse must be refused, never overwritten.
        (root / ".planning" / "config.json").write_text("{not json",
                                                        encoding="utf-8")
        try:
            cfg.apply_long_run(root)
            _fail("V-GSDAC-CFG-REFUSES-UNPARSEABLE",
                  "overwrote a config it could not read — settings destroyed")
        except cfg.ConfigError:
            if (root / ".planning" / "config.json").read_text(
                    encoding="utf-8") == "{not json":
                _ok("V-GSDAC-CFG-REFUSES-UNPARSEABLE",
                    "refused and left the unreadable file byte-identical")
            else:
                _fail("V-GSDAC-CFG-REFUSES-UNPARSEABLE",
                      "raised but still modified the file")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def gate_two_phase(wd, mk) -> None:
    """Gap C: the post-compaction resume state machine.

    `_write_trigger_flag` and `_spawn_daemon` are replaced with recorders for
    the duration. That is not to weaken the check but to keep the test from
    BEING the thing it measures: driving them for real would drop a live
    trigger flag and launch the Enter daemon into the running session. The
    assertions are on whether they were called, which is the actual claim.
    """
    sid = f"gsdac-{uuid.uuid4().hex[:12]}"
    _stamp_orch_throttle(wd, sid)
    real_flag, real_spawn = wd._write_trigger_flag, wd._spawn_daemon
    real_door = wd._dispatch_continuation
    calls = {"flag": 0, "spawn": 0, "legacy": 0}
    # C4: dispatch goes through ONE door (`_dispatch_continuation`), which both
    # chooses the route and starts the delivery, so one door call counts as
    # the old flag+spawn pair. The legacy SendKeys pair is still recorded: any
    # call to it from a session with no opt-in is a foreground leak.
    wd._write_trigger_flag = lambda *a, **k: calls.__setitem__("legacy", calls["legacy"] + 1)
    wd._spawn_daemon = lambda *a, **k: calls.__setitem__("legacy", calls["legacy"] + 1)

    def _door(*a, **k):
        calls["flag"] += 1
        calls["spawn"] += 1
        return {"route": "orca-exact", "pane_key": "stub"}
    wd._dispatch_continuation = _door

    try:
        mk.write_marker(sid, "/gsd-autonomous", cwd=str(ROOT), phase=5)
        tp = _boundary_transcript(sid)

        # Stop A must ASK and must NOT dispatch: the daemon polls every 500 ms,
        # so an Enter here lands in an empty box while the model is generating.
        out_a = _run_at(wd, sid, POST_COMPACTION_PCT, tp)
        armed = wd._flag_exists(sid, wd.RESUME_ARMED_FLAG)
        if out_a.get("decision") == "block" and armed and calls["flag"] == 0:
            _ok("V-GSDAC-TWOPHASE-ARMS-FIRST",
                "Stop A blocked for the resume line and dispatched nothing")
        else:
            _fail("V-GSDAC-TWOPHASE-ARMS-FIRST",
                  f"decision={out_a.get('decision')!r} armed={armed} "
                  f"dispatches={calls['flag']} — an Enter at Stop A is consumed "
                  "on an empty input box and the resume never happens")

        if "/gsd-autonomous" in str(out_a.get("reason", "")):
            _ok("V-GSDAC-TWOPHASE-NAMES-COMMAND", "Stop A names the exact command")
        else:
            _fail("V-GSDAC-TWOPHASE-NAMES-COMMAND",
                  f"reason omits the command: {out_a.get('reason')!r}")

        # Stop B: the turn carrying the line has ended, so dispatch now.
        out_b = _run_at(wd, sid, POST_COMPACTION_PCT, tp)
        if calls["flag"] == 1 and calls["spawn"] == 1 \
                and out_b.get("decision") != "block":
            _ok("V-GSDAC-TWOPHASE-DISPATCHES-SECOND",
                "Stop B dropped the trigger, spawned the daemon, did not block")
        else:
            _fail("V-GSDAC-TWOPHASE-DISPATCHES-SECOND",
                  f"flag={calls['flag']} spawn={calls['spawn']} "
                  f"decision={out_b.get('decision')!r}")

        # One resume per compaction cycle — not one per Stop.
        _run_at(wd, sid, POST_COMPACTION_PCT, tp)
        _run_at(wd, sid, POST_COMPACTION_PCT, tp)
        if calls["flag"] == 1:
            _ok("V-GSDAC-TWOPHASE-ONCE-PER-CYCLE",
                "two further Stops dispatched nothing")
        else:
            _fail("V-GSDAC-TWOPHASE-ONCE-PER-CYCLE",
                  f"dispatched {calls['flag']} times — later Stops would press "
                  "Enter again on whatever the input box holds")

        # No marker: an ordinary session must not enter the branch at all.
        sid2 = f"gsdac-{uuid.uuid4().hex[:12]}"
        _stamp_orch_throttle(wd, sid2)
        before = calls["flag"]
        out_n = _run_at(wd, sid2, POST_COMPACTION_PCT, _boundary_transcript(sid2))
        if calls["flag"] == before and not out_n:
            _ok("V-GSDAC-TWOPHASE-INERT-WITHOUT-MARKER",
                "no marker: no block, no dispatch")
        else:
            _fail("V-GSDAC-TWOPHASE-INERT-WITHOUT-MARKER",
                  "a session with no autonomous run was dispatched into")
    finally:
        if calls["legacy"]:
            _fail("V-GSDAC-NO-FOREGROUND-LEAK",
                  f"legacy SendKeys path called {calls['legacy']} times without opt-in")
        else:
            _ok("V-GSDAC-NO-FOREGROUND-LEAK", "no legacy SendKeys call across the whole cycle")
        wd._write_trigger_flag, wd._spawn_daemon = real_flag, real_spawn
        wd._dispatch_continuation = real_door
        mk.clear_marker(sid)
        for f in (wd.RESUME_ARMED_FLAG, wd.RESUME_DONE_FLAG):
            wd._clear_flag(sid, f)


class _NullWriter:
    """Stand-in for atomic_write: accepts every call, writes nothing."""

    def atomic_append_jsonl(self, *a, **k):
        return None

    def atomic_write_bytes(self, *a, **k):
        return None


def gate_tier2_rearms(wd, mk) -> None:
    """Tier 2 must clear BOTH resume flags, or the run resumes exactly once.

    This gate exists because the suite could not see that defect: removing
    tier-2's re-arm scored a clean 24/24. The reason was structural — nothing
    here drove tier 2, because driving it writes vault checkpoints, dumps
    telemetry, drops the live trigger flag and launches the Enter daemon. So
    all five side-effecting calls are replaced for the duration and the branch
    is driven for real. A mutant nobody can catch is a clause nobody is
    holding.
    """
    sid = f"gsdac-{uuid.uuid4().hex[:12]}"
    _stamp_orch_throttle(wd, sid)
    saved = {n: getattr(wd, n) for n in
             ("_import_atomic_write", "_kclear_equivalent", "_dump_telemetry",
              "_write_trigger_flag", "_spawn_daemon", "_append_progress_md",
              "_dispatch_continuation")}
    wd._dispatch_continuation = lambda *a, **k: {"route": "manual", "why": "stubbed by test"}
    wd._import_atomic_write = lambda *a, **k: _NullWriter()
    wd._kclear_equivalent = lambda *a, **k: {}
    wd._dump_telemetry = lambda *a, **k: None
    wd._write_trigger_flag = lambda *a, **k: None
    wd._spawn_daemon = lambda *a, **k: False
    wd._append_progress_md = lambda *a, **k: None

    try:
        # Both resume flags set, as they are after a completed resume.
        wd._set_flag(sid, wd.RESUME_ARMED_FLAG)
        wd._set_flag(sid, wd.RESUME_DONE_FLAG)
        if not (wd._flag_exists(sid, wd.RESUME_ARMED_FLAG)
                and wd._flag_exists(sid, wd.RESUME_DONE_FLAG)):
            _fail("V-GSDAC-TIER2-REARMS-RESUME",
                  "could not establish the precondition — inconclusive, not a pass")
            return

        out = _run_at(wd, sid, 75.0)          # a genuine tier-2 crossing
        if out.get("decision") != "block":
            _fail("V-GSDAC-TIER2-REARMS-RESUME",
                  f"tier 2 did not fire at 75% (decision={out.get('decision')!r}) "
                  "— the gate measured nothing")
            return

        still = [n for n, f in (("armed", wd.RESUME_ARMED_FLAG),
                                ("done", wd.RESUME_DONE_FLAG))
                 if wd._flag_exists(sid, f)]
        if not still:
            _ok("V-GSDAC-TIER2-REARMS-RESUME",
                "tier 2 cleared both resume flags — the next cycle can resume")
        else:
            _fail("V-GSDAC-TIER2-REARMS-RESUME",
                  f"tier 2 left {', '.join(still)} set — the run would resume "
                  "once and then be stranded at every later crossing")
    finally:
        for name, fn in saved.items():
            setattr(wd, name, fn)
        for f in (wd.RESUME_ARMED_FLAG, wd.RESUME_DONE_FLAG,
                  wd.ADVISORY_FLAG, wd.SNAPSHOT_FLAG):
            wd._clear_flag(sid, f)


def main() -> int:
    print("V-GSDAC — /gsd-autonomous auto-compact done-gate")
    for path in (WATCHDOG, MARKER_TOOL, CONFIG_TOOL):
        if not path.is_file():
            print(f"  FAIL V-GSDAC-SUBJECTS-EXIST: missing {path}")
            print("GSDAC_PASS=0/1  threshold=all")
            return 1

    wd = _load(WATCHDOG, "_gsdac_watchdog")
    mk = _load(MARKER_TOOL, "_gsdac_marker")
    cfg = _load(CONFIG_TOOL, "_gsdac_config")

    gate_thresholds(wd)
    gate_rearm(wd)
    gate_marker(mk)
    gate_resume_clause(wd, mk)
    gate_two_phase(wd, mk)
    gate_tier2_rearms(wd, mk)
    gate_long_run_config(cfg)

    total = _passes + _fails
    print(f"GSDAC_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
