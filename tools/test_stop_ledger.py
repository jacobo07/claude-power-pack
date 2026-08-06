#!/usr/bin/env python3
"""V-gate for the STOP #1 disposition ledger.

The load-bearing property is V-STOP-NEVER-EDITS-PLANS: the producer must leave every
sealed plan byte-identical. A plan is a dated statement of belief, and one silently
corrected to match a later verdict is no longer evidence of anything.

    python tools/test_stop_ledger.py
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.owner_queue import stop_ledger as sl   # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _plan(d: Path, name: str, status: str, body: str = "") -> Path:
    p = d / name
    p.write_text(f"---\ntitle: t\nstatus: {status}\n---\n\n{body}\n", encoding="utf-8")
    return p


def _disp(rows: list, plan: str) -> str:
    for r in rows:
        if r.plan == plan:
            return r.disposition
    return "<absent>"


def main() -> int:
    print("STOP LEDGER V-GATE (portfolio-tier transition producer)")

    # --- discovery, classification, witnessing ------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _plan(d, "alpha-2026-01-01.md", "STOP #1 -- BLOCKING, awaiting Owner selection")
        _plan(d, "beta-2026-01-02.md", "STOP #1 -- presented inline, awaiting approval")
        _plan(d, "gamma-2026-01-03.md",
              "STOP #1 RESOLVED -- Owner selected Option B, awaiting nothing")
        _plan(d, "delta-2026-01-04.md", "shipped 2026-01-04")          # no STOP token
        # a witness for beta, authored by a DIFFERENT artifact
        _plan(d, "witness-2026-01-05.md", "STOP #1 note",
              "The beta family was struck on review; nothing was built.")

        rows = sl.build(d, [d])
        names = {r.plan for r in rows}

        if "delta-2026-01-04.md" not in names and len(rows) == 4:
            _ok("V-STOP-DISCOVERED",
                f"{len(rows)} STOP-bearing plans discovered from disk; the non-STOP "
                f"plan is excluded")
        else:
            _fail("V-STOP-DISCOVERED", f"rows={sorted(names)}")

        if _disp(rows, "alpha-2026-01-01.md") == sl.OPEN:
            _ok("V-STOP-NO-WITNESS-IS-OPEN",
                "an open-shaped status with no witness stays OPEN (conservative default)")
        else:
            _fail("V-STOP-NO-WITNESS-IS-OPEN",
                  f"got {_disp(rows, 'alpha-2026-01-01.md')}")

        if _disp(rows, "beta-2026-01-02.md") == sl.CONTRADICTED:
            _ok("V-STOP-WITNESS-CONTRADICTS",
                "a foreign artifact naming the family beside a disposition verb "
                "yields CONTRADICTED")
        else:
            _fail("V-STOP-WITNESS-CONTRADICTS", f"got {_disp(rows, 'beta-2026-01-02.md')}")

        if _disp(rows, "gamma-2026-01-03.md") == sl.RESOLVED:
            _ok("V-STOP-CLOSED-BEATS-OPEN",
                "'RESOLVED ... awaiting nothing' matches both shapes; the stated "
                "resolution wins")
        else:
            _fail("V-STOP-CLOSED-BEATS-OPEN", f"got {_disp(rows, 'gamma-2026-01-03.md')}")

    # --- STOP #1 and STOP #2 are different checkpoints -------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _plan(d, "one-2026-02-01.md", "STOP #1 -- BLOCKING, awaiting Owner selection")
        _plan(d, "two-2026-02-02.md", "STOP #2 -- BLOCKING, presented inline, "
                                      "no dataset written")
        _plan(d, "hyph-2026-02-03.md", "STOP-1 (awaiting Owner approval)")
        rows = sl.build(d, [d])
        got = {r.plan: r.stop_kind for r in rows}
        want = {"one-2026-02-01.md": "STOP #1", "two-2026-02-02.md": "STOP #2",
                "hyph-2026-02-03.md": "STOP #1"}
        if got == want:
            _ok("V-STOP-KIND-DISTINGUISHED",
                "STOP #2 is labelled as itself rather than folded under STOP #1, and "
                "the hyphenated `STOP-1` is still recognised as checkpoint 1")
        else:
            _fail("V-STOP-KIND-DISTINGUISHED", f"got {got} want {want}")

    # --- a plan may not witness itself ----------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _plan(d, "solo-2026-01-01.md", "STOP #1 -- awaiting Owner",
              "The solo family was struck, refused and shelved. Really.")
        rows = sl.build(d, [d])
        if _disp(rows, "solo-2026-01-01.md") == sl.OPEN:
            _ok("V-STOP-NO-SELF-WITNESS",
                "a plan asserting its own disposition in its body is still OPEN")
        else:
            _fail("V-STOP-NO-SELF-WITNESS", f"got {_disp(rows, 'solo-2026-01-01.md')}")

    # --- the producer must never modify a sealed plan ------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        paths = [
            _plan(d, "one-2026-01-01.md", "STOP #1 -- awaiting Owner"),
            _plan(d, "two-2026-01-02.md", "STOP #1 -- awaiting Owner", "two was struck"),
        ]
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        rows = sl.build(d, [d])
        sl.write(rows, d / "STOP_LEDGER.md")
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        if before == after and (d / "STOP_LEDGER.md").is_file():
            _ok("V-STOP-NEVER-EDITS-PLANS",
                "2 plans byte-identical after build+write; the ledger is derived, "
                "the records stay sealed")
        else:
            changed = [k for k in before if before[k] != after[k]]
            _fail("V-STOP-NEVER-EDITS-PLANS", f"mutated: {changed}")

    # --- a short family token must not match everything ------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _plan(d, "ab-2026-01-01.md", "STOP #1 -- awaiting Owner")
        _plan(d, "noise-2026-01-02.md", "STOP #1 note", "ab was struck and shelved")
        rows = sl.build(d, [d])
        if _disp(rows, "ab-2026-01-01.md") == sl.OPEN:
            _ok("V-STOP-SHORT-TOKEN-GUARD",
                "a 2-character family token is refused as evidence, so it cannot "
                "witness itself into a disposition")
        else:
            _fail("V-STOP-SHORT-TOKEN-GUARD", f"got {_disp(rows, 'ab-2026-01-01.md')}")

    # --- fail-open --------------------------------------------------------------------------
    try:
        rows = sl.build(Path(tempfile.gettempdir()) / "definitely-not-here-xyz", [])
        if rows == []:
            _ok("V-STOP-FAILOPEN",
                "a missing plans directory yields an empty ledger, not an exception")
        else:
            _fail("V-STOP-FAILOPEN", f"got {len(rows)} rows from a missing directory")
    except Exception as e:                                   # noqa: BLE001
        _fail("V-STOP-FAILOPEN", f"raised {type(e).__name__}: {e}")

    # --- the live repository ----------------------------------------------------------------
    live = sl.build()
    if live:
        counts = {k: sum(1 for r in live if r.disposition == k)
                  for k in (sl.OPEN, sl.CONTRADICTED, sl.RESOLVED, sl.UNKNOWN)}
        if counts[sl.UNKNOWN] == 0:
            _ok("V-STOP-LIVE-PARSES",
                f"{len(live)} live plans, 0 UNKNOWN -- "
                + " ".join(f"{k}={v}" for k, v in counts.items()))
        else:
            _fail("V-STOP-LIVE-PARSES", f"{counts[sl.UNKNOWN]} plans failed to parse")
    else:
        _fail("V-STOP-LIVE-PARSES", "no STOP-bearing plans found in the live repo")

    total = _passes + _fails
    print(f"\nSTOP_LEDGER_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
