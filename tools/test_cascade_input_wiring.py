"""V-gates for the proactive-signal input wiring (frontier-28 Phase 5).

Origin, measured 2026-08-25. `pp-cascade-guard` was dispatched on every prompt through
jit_skill_loader and had never emitted anything, for two independent reasons:

  1. `ctx_in` hardcoded `current_error=""`, so `evaluate()` returned None at its first
     line before any matching logic ran.
  2. Even given text, it could not match: `_build_cascade_map()` keys on
     `f"{category}:{subsystem}"`, a composite the CEPS recorder assembles from two
     structured fields, while the dispatcher passed a raw error MESSAGE. The store's own
     newest error text returned None while the synthetic key fired.

Hermetic against a growing store: the learned keys are READ from the live cascade map
rather than hardcoded, so adding CEPS events cannot break these gates. If the map is
empty the suite exits NON-ZERO rather than reporting 0/0 -- a suite that asserts nothing
does not pass (T-TEST-SKIPPED-ITSELF-GREEN-001).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))
sys.path.insert(0, str(PP / "tools"))

from modules.pp_agents.signals import cascade            # noqa: E402
from modules.pp_agents.proactive_dispatcher import (      # noqa: E402
    dispatch_to_additional_context as dispatch,
)
import jit_skill_loader as J                              # noqa: E402

_p = _f = 0


def _ok(gate, ev):
    global _p
    _p += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global _f
    _f += 1
    print(f"  FAIL {gate}: {ev}")


def _ctx(**kw):
    base = {"project": "pp", "prompt": "x", "cwd": ".",
            "last_written_code": "", "last_written_file": "",
            "current_error": "", "error_category": "", "error_subsystem": "",
            "session_had_errors": False, "errors_fixed": 0}
    base.update(kw)
    return base


def main():
    cmap = cascade._build_cascade_map()
    if not cmap:
        print("FAIL: cascade map is empty, so zero gates executed. A suite that "
              "asserts nothing does not pass. The CEPS store has no co-occurring "
              "pairs at threshold -- an environment/data condition to investigate.")
        print("CASCADE_WIRING_PASS=0/0  threshold=6/6")
        return 1

    learned = sorted(cmap)[0]
    cat, _, sub = learned.partition(":")

    # V-CASCADE-STRUCTURED-FIRES -- the structured key matches where text cannot.
    sig = cascade.evaluate("", "pp", cat, sub)
    if sig is not None and cmap[learned][0] in sig.advisory:
        _ok("V-CASCADE-STRUCTURED-FIRES",
            f"{learned!r} -> {cmap[learned][:2]}")
    else:
        _fail("V-CASCADE-STRUCTURED-FIRES", f"{learned!r} produced {sig}")

    # V-CASCADE-UNLEARNED-SILENT -- no signal for a key the data never learned.
    # The point of a predictor is that it stays quiet when it knows nothing.
    if cascade.evaluate("boom", "pp", "nosuchcategory", "nosuchsub") is None:
        _ok("V-CASCADE-UNLEARNED-SILENT", "unknown key -> None")
    else:
        _fail("V-CASCADE-UNLEARNED-SILENT", "fired on a key that was never learned")

    # V-CASCADE-AMBIGUOUS-CATEGORY-SILENT -- a category matching several learned keys
    # must NOT pick one. Co-occurrence was learned at subsystem granularity; choosing
    # among siblings would invent a specificity the data does not have.
    cats = Counter(k.split(":", 1)[0] for k in cmap)
    ambiguous = [c for c, n in cats.items() if n > 1]
    if ambiguous:
        if cascade.evaluate("", "pp", ambiguous[0], "") is None:
            _ok("V-CASCADE-AMBIGUOUS-CATEGORY-SILENT",
                f"{ambiguous[0]!r} maps to {cats[ambiguous[0]]} keys -> None")
        else:
            _fail("V-CASCADE-AMBIGUOUS-CATEGORY-SILENT",
                  f"{ambiguous[0]!r} picked one of {cats[ambiguous[0]]} keys")
    else:
        _ok("V-CASCADE-AMBIGUOUS-CATEGORY-SILENT",
            "no ambiguous category in the current store; branch not exercised")

    # V-CASCADE-LEGACY-TEXT-UNCHANGED -- the pre-existing text path must not regress.
    empty_none = cascade.evaluate("") is None
    key_in_text = cascade.evaluate(f"prefix {learned} suffix") is not None
    if empty_none and key_in_text:
        _ok("V-CASCADE-LEGACY-TEXT-UNCHANGED", "empty -> None; key-in-text -> fires")
    else:
        _fail("V-CASCADE-LEGACY-TEXT-UNCHANGED",
              f"empty_none={empty_none} key_in_text={key_in_text}")

    # V-CASCADE-RECENCY-BOUND -- an error older than the window is not "current".
    # Anchored to the store's own newest timestamp, never to wall-clock.
    newest = None
    for raw in reversed(J.CEPS_EVENTS_PATH.read_text(
            encoding="utf-8", errors="replace").splitlines()):
        if raw.strip():
            newest = json.loads(raw)
            break
    when = datetime.strptime(newest["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)
    fresh = J._recent_error_context(now=when + timedelta(seconds=60))
    stale = J._recent_error_context(
        now=when + timedelta(seconds=J.RECENT_ERROR_MAX_AGE_S + 60))
    if fresh.get("error_category") == newest["category"] and stale == {}:
        _ok("V-CASCADE-RECENCY-BOUND",
            f"fresh -> {newest['category']!r}; beyond "
            f"{J.RECENT_ERROR_MAX_AGE_S}s -> {{}}")
    else:
        _fail("V-CASCADE-RECENCY-BOUND", f"fresh={fresh} stale={stale}")

    # V-CASCADE-FAILOPEN -- a missing store yields {}, never an exception. This runs on
    # every prompt; an advisory must never be the reason a prompt fails.
    saved = J.CEPS_EVENTS_PATH
    try:
        J.CEPS_EVENTS_PATH = PP / "vault" / "ceps" / "__absent__.jsonl"
        if J._recent_error_context() == {}:
            _ok("V-CASCADE-FAILOPEN", "absent store -> {} with no raise")
        else:
            _fail("V-CASCADE-FAILOPEN", "absent store did not yield {}")
    finally:
        J.CEPS_EVENTS_PATH = saved

    # V-CASCADE-DISPATCHER-PASSES-KEY -- the real consumer, end to end. Without this
    # the module works and the live path stays silent, which was the original defect.
    # pp-cascade-guard carries cooldown_minutes=5, enforced by a state FILE. Left alone,
    # this gate would pass or fail according to whether anything fired in the last five
    # minutes -- a wall-clock-dependent result -- and it would write global state as a
    # side effect of being tested. Both the throttle read and the throttle write are
    # neutralised: this gate asserts that a structured key reaches the advisory, which
    # is a different question from how often the advisory may repeat.
    from modules.pp_agents import proactive_core as _core
    _saved = (_core.is_throttled, _core.mark_fired)
    try:
        _core.is_throttled = lambda *a, **k: False
        _core.mark_fired = lambda *a, **k: None
        out = dispatch(_ctx(current_error="boom",
                            error_category=cat, error_subsystem=sub)) or ""
        quiet = dispatch(_ctx(current_error="boom",
                              error_category="nosuchcategory")) or ""
    finally:
        _core.is_throttled, _core.mark_fired = _saved
    if "historically preceded" in out and "historically preceded" not in quiet:
        _ok("V-CASCADE-DISPATCHER-PASSES-KEY",
            "advisory reaches additionalContext for a learned key only")
    else:
        _fail("V-CASCADE-DISPATCHER-PASSES-KEY",
              f"learned={'historically preceded' in out} "
              f"unlearned={'historically preceded' in quiet}")

    print(f"CASCADE_WIRING_PASS={_p}/{_p + _f}  threshold={_p + _f}/{_p + _f}")
    return 0 if _f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
