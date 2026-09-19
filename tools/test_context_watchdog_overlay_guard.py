#!/usr/bin/env python3
"""V-OVERLAY-* -- the orchestrator overlay must not import before its guards.

WHY THIS EXISTS. `_orchestrator_overlay` ran `sys.path.insert(0, ROOT)` and
`from modules.cpc_os.auto_reset_orchestrator import orchestrate` ABOVE its
throttle and once-per-session checks. Both guards therefore saved only the
`orchestrate()` call; the import chain was paid on every Stop for the life of
a session, including after the advisory had already fired. Work standing in
front of its own guard.

WHY IT COUNTS INSTEAD OF TIMING. The host that surfaced this sat at 4% free
memory, where this estate has measured 17x drift on identical payloads. A
clock cannot resolve the question there. "Was the module imported?" is
load-independent and answers either way, so it stays valid on a starved host
and on an idle one. It is also the property that actually matters: the fix is
about WHETHER the import runs, not how long it takes.

HOW IT OBSERVES. `builtins.__import__` is wrapped to count attempts on the
orchestrator module and hand back a stub whose `orchestrate` returns
`{"action": None}`. The real orchestrator never runs, so a case has no side
effect outside an isolated temp dir -- and `tempfile.tempdir` is repointed,
which is where BOTH guard flags live.

The two negative cases are meaningless without V-OVERLAY-POSITIVE-CONTROL: a
misspelled module name would satisfy "was not imported" forever.

Usage:
    python tools/test_context_watchdog_overlay_guard.py
    python tools/test_context_watchdog_overlay_guard.py --subject <copy.py>
"""
from __future__ import annotations

import argparse
import builtins
import importlib.util
import os
import sys
import tempfile
import time
import types
import uuid
from pathlib import Path

DEFAULT_SUBJECT = (Path.home() / ".claude" / "skills" / "claude-power-pack"
                   / "modules" / "zero-crash" / "hooks" / "context-watchdog.py")
TARGET = "modules.cpc_os.auto_reset_orchestrator"

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"FAIL {gate}: {diagnostic}")


def _load_subject(path: Path):
    spec = importlib.util.spec_from_file_location("cw_subject", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"HARNESS-FAILED: cannot load subject {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _ImportCounter:
    """Count (and intercept) imports of the orchestrator module."""

    def __init__(self) -> None:
        self.count = 0
        self._real = builtins.__import__

    def __enter__(self):
        stub = types.ModuleType(TARGET)
        stub.orchestrate = lambda *a, **k: {"action": None}

        def counting(name, globals=None, locals=None, fromlist=(), level=0):
            if name == TARGET:
                self.count += 1
                return stub
            return self._real(name, globals, locals, fromlist, level)

        builtins.__import__ = counting
        return self

    def __exit__(self, *exc):
        builtins.__import__ = self._real
        return False


def _event(session_id: str, cwd: str) -> dict:
    return {"session_id": session_id, "cwd": cwd}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", default=str(DEFAULT_SUBJECT))
    args = ap.parse_args()

    subject_path = Path(args.subject)
    if not subject_path.is_file():
        print(f"HARNESS-FAILED: no subject at {subject_path}", file=sys.stderr)
        return 2

    # Isolate BOTH guard flags: they live in tempfile.gettempdir().
    iso = Path(tempfile.gettempdir()) / f"cw-overlay-drill-{os.getpid()}"
    iso.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(iso)
    if Path(tempfile.gettempdir()) != iso:
        print("HARNESS-FAILED: temp isolation did not take", file=sys.stderr)
        return 2

    cw = _load_subject(subject_path)
    cwd = str(iso)

    # --- V-OVERLAY-POSITIVE-CONTROL ------------------------------------
    # forced bypasses both guards, so the import MUST happen. Without this,
    # the two negatives below could pass against a typo.
    sid = f"drill-forced-{uuid.uuid4().hex[:8]}"
    os.environ["_TEST_ORCH_STATE"] = "green"
    try:
        with _ImportCounter() as c:
            cw._orchestrator_overlay(_event(sid, cwd))
        if c.count == 1:
            _ok("V-OVERLAY-POSITIVE-CONTROL",
                "forced path imported the orchestrator exactly once "
                "(the counter can observe an import)")
        else:
            _fail("V-OVERLAY-POSITIVE-CONTROL",
                  f"expected 1 import on the forced path, saw {c.count}; "
                  "the negative cases below prove nothing")
    finally:
        os.environ.pop("_TEST_ORCH_STATE", None)

    # --- V-OVERLAY-OPEN-PATH-IMPORTS -----------------------------------
    # No flags set: the guards must NOT suppress the legitimate run, and the
    # stamp must still precede orchestrate().
    sid = f"drill-open-{uuid.uuid4().hex[:8]}"
    with _ImportCounter() as c:
        cw._orchestrator_overlay(_event(sid, cwd))
    stamped = (iso / cw.ORCH_THROTTLE_FLAG.format(session_id=sid)).exists()
    if c.count == 1 and stamped:
        _ok("V-OVERLAY-OPEN-PATH-IMPORTS",
            "unguarded Stop imported once and stamped the throttle")
    else:
        _fail("V-OVERLAY-OPEN-PATH-IMPORTS",
              f"imports={c.count} (want 1), throttle stamped={stamped} (want True)")

    # --- V-OVERLAY-THROTTLED-NO-IMPORT ---------------------------------
    sid = f"drill-throttled-{uuid.uuid4().hex[:8]}"
    (iso / cw.ORCH_THROTTLE_FLAG.format(session_id=sid)).write_text(
        str(time.time()), encoding="utf-8")
    with _ImportCounter() as c:
        result = cw._orchestrator_overlay(_event(sid, cwd))
    if c.count == 0 and result is None:
        _ok("V-OVERLAY-THROTTLED-NO-IMPORT",
            "a throttled Stop imported nothing and still returned None")
    else:
        _fail("V-OVERLAY-THROTTLED-NO-IMPORT",
              f"imports={c.count} (want 0), result={result!r} (want None) -- "
              "the import is running in front of the throttle")

    # --- V-OVERLAY-ADVISED-NO-IMPORT -----------------------------------
    sid = f"drill-advised-{uuid.uuid4().hex[:8]}"
    (iso / cw.ORCH_ADVISORY_FLAG.format(session_id=sid)).write_text(
        "1", encoding="utf-8")
    with _ImportCounter() as c:
        result = cw._orchestrator_overlay(_event(sid, cwd))
    if c.count == 0 and result is None:
        _ok("V-OVERLAY-ADVISED-NO-IMPORT",
            "an already-advised Stop imported nothing and returned None")
    else:
        _fail("V-OVERLAY-ADVISED-NO-IMPORT",
              f"imports={c.count} (want 0), result={result!r} (want None) -- "
              "the import is running in front of the no-nag flag")

    total = len(_passes) + len(_fails)
    print(f"\nOVERLAY_GUARD_PASS={len(_passes)}/{total}  threshold=4/4")
    return 0 if not _fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
