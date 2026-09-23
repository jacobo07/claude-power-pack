"""Gates for the W12 runner's preflight.

The preflight's whole value is that it refuses in under a second instead of after
thirty minutes, so every refusal it can make must be driven — a preflight nobody has
falsified could have every clause removed and still print PASS five times.

The projection case is the one that earned this file. The first version of that check
read `getattr(proj, "source_fresh", None)`, and `Projection` has no such field: `load()`
records the fingerprint the projection was BUILT with and never compares it, while
`--verify` does the comparison itself. So the check returned None on every call and the
stale branch could not fire — a vacuous guard in front of the one precondition that
silently voids the treatment, since a stale projection still loads, still reports LOADED,
and still answers every query with the wrong generation of evidence. It was visible only
because the live run printed `source_fresh None` where it should have printed a boolean.

Every refusal here is therefore paired with a control in which the same check PASSES.
A guard that refuses everything satisfies every refusal assertion on its own.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ucr_cif_w12_run as R  # noqa: E402
from modules.ucr_cif import disposition_consumer as dc  # noqa: E402
from modules.ucr_cif import structural_projection as sp  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}  {diag}")


def expect_refusal(gate: str, fn, must_mention: str = "") -> None:
    try:
        got = fn()
    except R.Refusal as exc:
        if must_mention and must_mention.lower() not in str(exc).lower():
            _fail(gate, f"refused, but the reason never mentions {must_mention!r}")
            return
        _ok(gate, f"refused: {str(exc).splitlines()[0][:88]}")
        return
    except Exception as exc:                                   # noqa: BLE001
        _fail(gate, f"raised {exc!r} instead of Refusal — a check that crashed is "
                    f"not a check that refused")
        return
    _fail(gate, f"did NOT refuse; returned {got!r}")


def expect_pass(gate: str, fn) -> None:
    try:
        got = fn()
    except R.Refusal as exc:
        _fail(gate, f"refused when it should have passed: {str(exc).splitlines()[0]}")
        return
    except Exception as exc:                                   # noqa: BLE001
        _fail(gate, f"raised {exc!r}")
        return
    _ok(gate, str(got)[:88])


def main() -> int:
    # ---- reaper -------------------------------------------------------
    prior = os.environ.pop(R.REAPER_ENV, None)
    try:
        expect_refusal("V-W12RUN-REAPER-REFUSES",
                       lambda: R._check_reaper(False), "relaunch")
        expect_pass("V-W12RUN-REAPER-OVERRIDE-IS-EXPLICIT",
                    lambda: R._check_reaper(True))
        os.environ[R.REAPER_ENV] = "1"
        expect_pass("V-W12RUN-REAPER-SET-PASSES", lambda: R._check_reaper(False))
        os.environ[R.REAPER_ENV] = "0"
        expect_refusal("V-W12RUN-REAPER-ZERO-IS-NOT-SET",
                       lambda: R._check_reaper(False), "relaunch")
    finally:
        os.environ.pop(R.REAPER_ENV, None)
        if prior is not None:
            os.environ[R.REAPER_ENV] = prior

    # ---- projection freshness: the branch that could not fire ---------
    real_fp = sp.repo_fingerprint
    try:
        # SYNTHETIC on purpose. The first version asserted that the REAL tree is
        # fresh, which is a statement about today's working copy rather than about
        # this clause -- and it failed immediately, because adding the two files
        # under tools/ that this wave is testing moved the fingerprint. A control
        # pinned to a state that drifts on every commit flakes forever and teaches
        # nothing. Pinning the live projection's own fingerprint drives the PASS
        # pole of the same comparison, independently of what the tree is doing.
        sp.repo_fingerprint = lambda root: sp.load().repo_fingerprint
        expect_pass("V-W12RUN-FRESH-PROJECTION-PASSES", R._check_projection)

        sp.repo_fingerprint = lambda root: "0" * 64
        expect_refusal("V-W12RUN-STALE-PROJECTION-REFUSES",
                       R._check_projection, "stale")
    finally:
        sp.repo_fingerprint = real_fp

    real_load = sp.load
    try:
        class _NoFp:
            status = sp.LOADED
            usable = True
            repo_fingerprint = None
        sp.load = lambda *a, **k: _NoFp()
        expect_refusal("V-W12RUN-NO-FINGERPRINT-IS-NOT-FRESH",
                       R._check_projection, "could not look")

        class _Unusable:
            status = sp.STALE_LEDGER
            usable = False
            repo_fingerprint = "x"
        sp.load = lambda *a, **k: _Unusable()
        expect_refusal("V-W12RUN-UNUSABLE-PROJECTION-REFUSES",
                       R._check_projection, "contribute no structural evidence")
    finally:
        sp.load = real_load

    # ---- frozen constants ---------------------------------------------
    expect_pass("V-W12RUN-FROZEN-UNCHANGED-PASSES", R._check_frozen)
    real_cap = dc.MAX_OWNERS
    try:
        dc.MAX_OWNERS = 7
        expect_refusal("V-W12RUN-FROZEN-DRIFT-REFUSES", R._check_frozen, "moved")
    finally:
        dc.MAX_OWNERS = real_cap

    # ---- stores --------------------------------------------------------
    expect_refusal("V-W12RUN-CANONICAL-STORE-REFUSES",
                   lambda: R._check_stores([R.CANONICAL_STORE], False), "canonical")
    expect_pass("V-W12RUN-ARM-STORES-PASS",
                lambda: R._check_stores([R.DEFAULT_W9_STORE, R.DEFAULT_W11_STORE],
                                        False))

    with tempfile.TemporaryDirectory(dir=str(ROOT)) as td:
        rel = Path(td).name + "/existing.json"
        (ROOT / rel).write_text("{}", encoding="utf-8")
        expect_refusal("V-W12RUN-EXISTING-STORE-REFUSES",
                       lambda: R._check_stores([rel], False), "already exists")
        expect_pass("V-W12RUN-FORCE-OVERRIDES-EXISTING",
                    lambda: R._check_stores([rel], True))

    total = _passes + _fails
    print(f"\nW12RUN_PREFLIGHT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
