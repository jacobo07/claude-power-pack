"""V-gates for dispatch-key liveness (frontier-28 Phase 5 item 2).

Origin: `liveness_report.md:209` classed `cascade_prevention/predictive` LIVE, "reached
from modules/cascade_prevention/engine". The import edge is real and the code never ran --
`_detect_session` is registered at `SURFACE_DETECTORS["session"]` and no production caller
supplies that key.

Two disciplines this file is built around.

BOOKEND CONTROLS. Every gate that asserts "not supplied" is paired with one asserting
"supplied". A detector that can only say no is indistinguishable from a detector that is
broken, and the first version of this scanner did exactly that -- it reported ten
NEVER_SUPPLIED rows, every one a false positive, while missing the case it was written for.

THE GATES SURVIVE THE FIX. They assert the MECHANISM against a hermetic fixture, not the
current bug's status. Wiring `detect('session')` tomorrow must not turn this suite red;
a gate that fails when its subject improves teaches people to delete gates.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.liveness import dispatch                      # noqa: E402

_p = _f = 0


def _ok(gate, ev):
    global _p
    _p += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global _f
    _f += 1
    print(f"  FAIL {gate}: {ev}")


FIXTURE_ENGINE = '''\
def _handle_alpha(ctx): return 1
def _handle_beta(ctx): return 2
def _handle_gamma(ctx): return 3

TABLE = {"alpha": _handle_alpha, "beta": _handle_beta, "gamma": _handle_gamma}

TIERS = {"one": WARM, "two": COLD, "three": HOT}

def route(surface, ctx=None):
    fn = TABLE.get(surface)
    return fn(ctx) if fn else None
'''

FIXTURE_CALLER = '''\
from engine import route
route("alpha", {})
# "beta" appears here as a bare literal but is never dispatched -- the loose-substring
# match this scanner originally used would have wrongly called it supplied.
LABEL = "beta"
'''


def _build_fixture(root: Path):
    mods = root / "modules" / "fx"
    mods.mkdir(parents=True)
    (mods / "engine.py").write_text(FIXTURE_ENGINE, encoding="utf-8")
    tools = root / "tools"
    tools.mkdir(parents=True)
    (tools / "caller.py").write_text(FIXTURE_CALLER, encoding="utf-8")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="dispatch_gate_"))
    try:
        _build_fixture(tmp)
        rows = dispatch.scan(tmp)
        by_key = {r["key"]: r for r in rows}

        # V-DISPATCH-TABLE-DETECTED -- a str->callable dict with a dispatcher is found.
        if set(by_key) == {"alpha", "beta", "gamma"}:
            _ok("V-DISPATCH-TABLE-DETECTED", "TABLE detected, 3 keys, via route()")
        else:
            _fail("V-DISPATCH-TABLE-DETECTED", f"keys found: {sorted(by_key)}")

        # V-DISPATCH-VALUE-TABLE-IGNORED -- negative control. TIERS maps names to
        # constants, not callables; reporting it was the original false-positive class.
        if not any(r["table"] == "TIERS" for r in rows):
            _ok("V-DISPATCH-VALUE-TABLE-IGNORED", "TIERS (constants) not a dispatch table")
        else:
            _fail("V-DISPATCH-VALUE-TABLE-IGNORED", "value table reported as dispatch")

        # V-DISPATCH-SUPPLIED -- positive control. A detector that cannot say YES is
        # indistinguishable from one that is broken.
        a = by_key.get("alpha", {})
        if a.get("status") == dispatch.SUPPLIED and a.get("suppliers"):
            _ok("V-DISPATCH-SUPPLIED", f"alpha reached from {a['suppliers'][0]}")
        else:
            _fail("V-DISPATCH-SUPPLIED", f"alpha judged {a.get('status')}")

        # V-DISPATCH-CALL-POSITION-ONLY -- "beta" exists as a quoted literal in the
        # caller but is never dispatched. This is the precision the first version lacked.
        b = by_key.get("beta", {})
        if b.get("status") == dispatch.NEVER_SUPPLIED:
            _ok("V-DISPATCH-CALL-POSITION-ONLY",
                "bare literal 'beta' does not count as a caller")
        else:
            _fail("V-DISPATCH-CALL-POSITION-ONLY", f"beta judged {b.get('status')}")

        # V-DISPATCH-UNREACHED -- a key with no caller at all.
        g = by_key.get("gamma", {})
        if g.get("status") == dispatch.NEVER_SUPPLIED:
            _ok("V-DISPATCH-UNREACHED", "gamma has no caller -> NEVER_SUPPLIED")
        else:
            _fail("V-DISPATCH-UNREACHED", f"gamma judged {g.get('status')}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # V-DISPATCH-LIVE-FOUNDING-CASE -- against the REAL repo, assert the founding table is
    # seen at all. Deliberately asserts STRUCTURE, not the bug: if someone wires
    # detect('session') tomorrow this still passes, because the scanner's job is to keep
    # answering the question, not to keep finding the same answer.
    live = [r for r in dispatch.scan()
            if r["table"] == "SURFACE_DETECTORS"]
    supplied = [r["key"] for r in live if r["status"] == dispatch.SUPPLIED]
    if live and "detect" in (live[0].get("dispatchers") or []) and supplied:
        unsupplied = [r["key"] for r in live if r["status"] == dispatch.NEVER_SUPPLIED]
        _ok("V-DISPATCH-LIVE-FOUNDING-CASE",
            f"{len(live)} keys via detect(); supplied={sorted(supplied)} "
            f"unsupplied={sorted(unsupplied)}")
    else:
        _fail("V-DISPATCH-LIVE-FOUNDING-CASE",
              f"rows={len(live)} supplied={supplied}")

    print(f"DISPATCH_LIVENESS_PASS={_p}/{_p + _f}  threshold={_p + _f}/{_p + _f}")
    return 0 if _f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
