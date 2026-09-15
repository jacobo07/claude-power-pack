"""V-CONTENTION-* -- can the umbrella tell a broken row from a busy machine?

A parallel run measures the row and the harness together and reports one
number for both. Measured 2026-09-02 over 75 rows: fourteen strict fails
and three unmeasured, of which FIVE passed cleanly when re-run alone --
36% of the reds were the validator measuring itself. The estate already
said so in a comment beside its MARGINAL BUDGET warning ("a gate that
changes verdict with ambient load is not measuring the code") and had no
way to settle it, so every session re-derived the answer by hand.

The obvious alternative was a hand-maintained list of expected reds. This
repo has already sealed why that fails: an audit whose subjects are
enrolled by hand measures memory, and a suppression list is the same
object with a friendlier name. Re-running the row is evidence.

These gates drive the decision, not the subprocess: which rows are
eligible, what a solo pass does to a row, and -- the one that matters --
that the mechanism cannot manufacture a green it was not given.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

import tools.verify_spp as vs  # noqa: E402

EXPECTED_GATES = 6
_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _row(name, rc=0, timed_out=False):
    return {"name": name, "rc": rc, "timed_out": timed_out, "elapsed": 1.0}


def main() -> int:
    adv = {"advisory-row"}
    rows = [_row("green"), _row("red", rc=1),
            _row("late", rc=124, timed_out=True),
            _row("advisory-row", rc=1)]
    picked = [r["name"] for r in vs.suspect_rows(rows, adv)]

    if picked == ["red", "late"]:
        _ok("V-CONTENTION-SELECTS-REDS",
            "an exited-nonzero row and a timeout are both eligible; "
            "selecting on timeout alone would have missed two of the five "
            "real cases measured on this host")
    else:
        _fail("V-CONTENTION-SELECTS-REDS", f"picked {picked}")

    if "green" not in picked:
        _ok("V-CONTENTION-NEVER-RERUNS-A-PASS",
            "a passing row is never re-run, so no green can be flipped red "
            "by a second sample -- the mechanism is one-directional and "
            "that limit is stated, not hidden")
    else:
        _fail("V-CONTENTION-NEVER-RERUNS-A-PASS", f"picked {picked}")

    if "advisory-row" not in picked:
        _ok("V-CONTENTION-SKIPS-ADVISORY",
            "an advisory red costs nothing already; re-running it would buy "
            "a label nobody reads")
    else:
        _fail("V-CONTENTION-SKIPS-ADVISORY", f"picked {picked}")

    r = _row("late", rc=124, timed_out=True)
    freed = vs.apply_solo(r, {"rc": 0, "elapsed": 3.0})
    if freed and r["rc"] == 0 and r["contended"] and not r["timed_out"]:
        _ok("V-CONTENTION-SOLO-PASS-EXONERATES",
            "a row that passes alone is marked contended and stops being "
            "counted as unmeasured")
    else:
        _fail("V-CONTENTION-SOLO-PASS-EXONERATES", str(r))

    r2 = _row("red", rc=1)
    kept = vs.apply_solo(r2, {"rc": 1, "elapsed": 3.0})
    if not kept and r2["rc"] == 1 and "contended" not in r2:
        _ok("V-CONTENTION-SOLO-FAIL-KEEPS-RED",
            "a row still red alone is untouched -- the pass exonerates, it "
            "does not suppress")
    else:
        _fail("V-CONTENTION-SOLO-FAIL-KEEPS-RED", str(r2))

    # The whole point is the exit code, not the label. A row exonerated by
    # a solo pass must leave the strict-fail set; one still red must not.
    after = [_row("late", rc=0, timed_out=False), _row("red", rc=1)]
    after[0]["contended"] = True
    strict = [x["name"] for x in after if x["rc"] != 0 and x["name"] not in adv]
    if strict == ["red"]:
        _ok("V-CONTENTION-VERDICT-FOLLOWS-EVIDENCE",
            "the exonerated row leaves STRICT FAIL and the confirmed one "
            "stays; the report changes because the evidence did")
    else:
        _fail("V-CONTENTION-VERDICT-FOLLOWS-EVIDENCE", f"strict={strict}")

    ran = len(_passes) + len(_fails)
    print(f"\nCONTENTION_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
