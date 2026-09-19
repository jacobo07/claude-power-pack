#!/usr/bin/env python
"""V-COLD-* -- the delivery provider's FIRST call must survive a cold start.

INCIDENT (2026-09-19, session de7f3c91, KobiiCraft Core Files). An autonomous
compaction and, 40 minutes later, its resume, both died the same way:

    11:37:10 delivery_requested  compact   expect_prefix=/compact
    11:37:56 delivery_blocked    BLOCKED_BY_DELIVERY_PROVIDER cli_timeout   (46 s)
    12:16:12 delivery_requested  resume    text=/gsd-autonomous --from 13
    12:17:02 delivery_blocked    BLOCKED_BY_DELIVERY_PROVIDER cli_timeout   (50 s)

Both land on CLI_TIMEOUT_S = 45. The provider was NOT broken: measured on this
host the same instant, `node <orca>/cli/index.js terminal list --json` returns
`ok: true` with a full terminal list in

    cold  101,628 ms      <-- first call of a fresh worker process
    warm    7,272 ms
    warm    7,268 ms

So the 45 s ceiling was sized against the warm path (6.4x headroom) and is
structurally blind to the cold path (0.44x -- a guaranteed loss). Every delivery
worker is spawned fresh (`spawn_delivery`), so the FIRST call it ever makes is
always the cold one, and the first call is `list_terminals()`. The transport was
therefore most likely to fail on the only attempt a crossing gets.

THE FIX IS NOT "RAISE THE TIMEOUT". A cold Electron CLI start is a known fixed
cost, not pathological latency; it is budgeted explicitly and paid once, and the
warm ceiling stays tight so genuine slowness is still caught. A first-call
timeout additionally becomes retryable, because by then the cost is paid.

The instrument is the `timeout` kwarg handed to subprocess.run -- asserting the
BUDGET, not a wall-clock, so the gate cannot drift with host load (this estate's
own rule: on a starved host, count, never time).
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="cold-state-")
os.environ.pop("CPP_CONTINUATION_TRANSPORT", None)

ROOT = Path(__file__).resolve().parents[1]

# The measurement this gate defends, recorded so the constant can never be
# lowered back under it without a test that says why.
MEASURED_COLD_MS = 101_628
MEASURED_WARM_MS = 7_272

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def _load():
    path = ROOT / "tools" / "continuation_transport.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("_cold_ct", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_reset_missing = False


def reset(mod) -> None:
    """Return the module to 'no successful call yet'.

    A missing hook is reported ONCE as its own failure and then tolerated, so a
    subject that lacks the mechanism still gets every remaining gate judged.
    Letting the AttributeError escape would abandon the rest of the run while
    still exiting 1 -- indistinguishable from a subject that failed them, which
    is the verifier-failed-vs-subject-invalid conflation this estate keeps
    paying for.
    """
    global _reset_missing
    fn = getattr(mod, "_reset_warm", None)
    if callable(fn):
        fn()
        return
    if not _reset_missing:
        _reset_missing = True
        _fail("V-COLD-RESET-HOOK-EXISTS",
              "_reset_warm() absent: the warm flag cannot be cleared between cases, so "
              "cold/warm cannot be told apart at all")


class Recorder:
    """Stands in for subprocess.run. Records every budget it was handed.

    Deliberately NOT a Mock: a double that is looser than the real call is how
    this estate has previously turned a TypeError into a plausible value.
    """

    def __init__(self, script):
        self.budgets: list[float] = []
        self.calls = 0
        self._script = list(script)

    def __call__(self, argv, **kw):
        self.budgets.append(kw.get("timeout"))
        self.calls += 1
        behaviour = self._script.pop(0) if self._script else "ok"
        if behaviour == "timeout":
            import subprocess
            raise subprocess.TimeoutExpired(cmd=argv, timeout=kw.get("timeout") or 0)

        class P:
            stdout = '{"ok": true, "result": {"terminals": []}}'
            stderr = ""
        return P()


def main() -> int:
    ct = _load()

    cold = getattr(ct, "COLD_START_BUDGET_S", None)
    warm = getattr(ct, "CLI_TIMEOUT_S", None)

    # --- born cold ----------------------------------------------------------
    # Asserted on the module AS IMPORTED, before any reset(). This is the one
    # property reset() cannot testify about, because reset() is what supplies
    # it: a mutation setting `_WARM = True` at module scope survived the first
    # drill entirely, hidden by my own fixture. In production that mutation is
    # invisible and total -- every fresh worker's first call silently takes the
    # 45 s ceiling again, which is precisely how de7f3c91 was lost.
    born = getattr(ct, "_WARM", "MISSING")
    if born is False:
        _ok("V-COLD-BORN-COLD", "a freshly imported module has paid nothing yet")
    else:
        _fail("V-COLD-BORN-COLD",
              f"_WARM is {born!r} at import time; a fresh delivery worker would treat its "
              "very first call as warm and re-inherit the defect")

    # --- the constant itself -------------------------------------------------
    if cold is None:
        _fail("V-COLD-BUDGET-EXISTS",
              "continuation_transport has no COLD_START_BUDGET_S; the first CLI "
              f"call is capped at CLI_TIMEOUT_S={warm}s against a measured "
              f"{MEASURED_COLD_MS/1000:.1f}s cold start")
    else:
        _ok("V-COLD-BUDGET-EXISTS", f"COLD_START_BUDGET_S={cold}s")
        if cold * 1000 > MEASURED_COLD_MS:
            _ok("V-COLD-BUDGET-EXCEEDS-MEASUREMENT",
                f"{cold}s > measured cold {MEASURED_COLD_MS/1000:.1f}s")
        else:
            _fail("V-COLD-BUDGET-EXCEEDS-MEASUREMENT",
                  f"{cold}s does NOT clear the measured {MEASURED_COLD_MS/1000:.1f}s cold start")
        # The warm ceiling must stay tight, or the fix has merely hidden slowness.
        if warm * 1000 < MEASURED_COLD_MS:
            _ok("V-COLD-WARM-CEILING-STAYS-TIGHT",
                f"CLI_TIMEOUT_S={warm}s still well under the cold cost, so real slowness is caught")
        else:
            _fail("V-COLD-WARM-CEILING-STAYS-TIGHT",
                  f"CLI_TIMEOUT_S={warm}s has been raised to absorb cold start -- that masks latency")

    # --- first call gets the cold budget ------------------------------------
    rec = Recorder(["ok"])
    ct.subprocess.run = rec
    reset(ct)
    ct.orca(["terminal", "list"])
    if rec.calls == 0:
        _fail("V-COLD-HARNESS-LIVE", "recorder never invoked -- the patch did not bind; every "
                                     "assertion below is vacuous")
    else:
        _ok("V-COLD-HARNESS-LIVE", f"recorder observed {rec.calls} call(s)")
        first = rec.budgets[0]
        if cold is not None and first == cold:
            _ok("V-COLD-FIRST-CALL-BUDGET", f"first call budgeted {first}s (cold)")
        else:
            _fail("V-COLD-FIRST-CALL-BUDGET",
                  f"first call budgeted {first}s; a fresh worker's first call must get the "
                  f"cold budget ({cold}s), this is the exact byte that lost de7f3c91")

    # --- after one success the budget tightens ------------------------------
    rec = Recorder(["ok", "ok"])
    ct.subprocess.run = rec
    reset(ct)
    ct.orca(["terminal", "list"])
    ct.orca(["terminal", "list"])
    if len(rec.budgets) == 2 and rec.budgets[1] == warm:
        _ok("V-COLD-WARM-AFTER-SUCCESS", f"second call budgeted {rec.budgets[1]}s (warm)")
    else:
        _fail("V-COLD-WARM-AFTER-SUCCESS",
              f"budgets={rec.budgets}; after a success the ceiling must return to {warm}s")

    # --- an explicit budget is never overridden -----------------------------
    rec = Recorder(["ok"])
    ct.subprocess.run = rec
    reset(ct)
    ct.orca(["terminal", "wait", "--for", "tui-idle"], timeout=135.0)
    if rec.budgets == [135.0]:
        _ok("V-COLD-EXPLICIT-BUDGET-WINS", "caller's 135.0s honoured unchanged")
    else:
        _fail("V-COLD-EXPLICIT-BUDGET-WINS",
              f"budgets={rec.budgets}; the tui-idle wait sets its own budget and must keep it")

    # --- a cold timeout is retried once, warm -------------------------------
    rec = Recorder(["timeout", "ok"])
    ct.subprocess.run = rec
    reset(ct)
    code, terms = ct.list_terminals()
    if code == "OK" and rec.calls == 2:
        _ok("V-COLD-LIST-RETRIES-ONCE",
            "first call timed out, retry succeeded -- the cold cost is paid, so the retry is warm")
    else:
        _fail("V-COLD-LIST-RETRIES-ONCE",
              f"code={code!r} after {rec.calls} call(s); a first-call cli_timeout must be "
              "retried once rather than ending the whole crossing")

    # --- but it does not loop ------------------------------------------------
    rec = Recorder(["timeout", "timeout", "ok"])
    ct.subprocess.run = rec
    reset(ct)
    code, _ = ct.list_terminals()
    if code == "cli_timeout" and rec.calls == 2:
        _ok("V-COLD-RETRY-BOUNDED", "exactly 2 attempts, then cli_timeout reported honestly")
    else:
        _fail("V-COLD-RETRY-BOUNDED",
              f"code={code!r} after {rec.calls} call(s); expected 2 attempts then a refusal")

    # --- a genuine provider failure is NOT laundered into a retry loop ------
    rec = Recorder(["ok"])
    ct.subprocess.run = rec
    reset(ct)

    class Down:
        stdout = '{"ok": false, "error": {"code": "runtime_unavailable"}}'
        stderr = ""

    ct.subprocess.run = lambda argv, **kw: Down()
    code, _ = ct.list_terminals()
    if code == "runtime_unavailable":
        _ok("V-COLD-NON-TIMEOUT-UNCHANGED", "runtime_unavailable still reported as itself")
    else:
        _fail("V-COLD-NON-TIMEOUT-UNCHANGED",
              f"code={code!r}; only cli_timeout is retryable, other failures must pass through")

    total = _passes + _fails
    print(f"\nCOLD_START_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
