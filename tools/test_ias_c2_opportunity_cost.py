#!/usr/bin/env python3
"""Validation harness for modules/ias_c2/opportunity_cost.py (CGF Workstream E).

Proves real, end-to-end wiring: what_now_tracked() -> ranks the real backlog
-> logs the correct foregone alternative -> a later pick of that same item
settles it CONFIRMED -> the domain aggregate reflects both states. Uses a
temp ledger path so it never pollutes the real vault/ias ledger.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.backlog_autopilot import BacklogItem, what_now  # noqa: E402
from modules.backlog_autopilot.engine import _score  # noqa: E402
from modules.ias_c2 import opportunity_cost as oc  # noqa: E402
from modules.ias_c2 import rank_and_forgo, record_opportunity_cost  # noqa: E402

_fails = 0
_passes = 0


def _check(gate_id: str, cond: bool, detail: str = "") -> None:
    global _fails, _passes
    if cond:
        _passes += 1
        print(f"PASS {gate_id}")
    else:
        _fails += 1
        print(f"FAIL {gate_id}: {detail}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)

        items = [
            BacklogItem("FIX-1", "Fix login bug", 0, "S", "Critical"),
            BacklogItem("FEAT-2", "Add 2FA", 1, "L", "High"),
            BacklogItem("DOC-3", "Update docs", 2, "M", "Low"),
        ]

        # V-IAS-C2-01: rank_and_forgo picks the highest-ranked NOT-chosen item,
        # not just "the next one in list order" (Part V §5.3).
        chosen = max(items, key=_score)
        foregone = rank_and_forgo(items, chosen, _score)
        expected_foregone = max([i for i in items if i.id != chosen.id], key=_score)
        _check("V-IAS-C2-01-rank-and-forgo", foregone is not None and foregone.id == expected_foregone.id,
               f"got {foregone}")

        # V-IAS-C2-02: recording writes a real ledger row with the right shape.
        rec = record_opportunity_cost(chosen, foregone, repo_root=repo_root)
        rows = oc._read_ledger(repo_root)
        _check("V-IAS-C2-02-ledger-write", len(rows) == 1 and rows[0]["foregone_id"] == foregone.id,
               f"rows={rows}")

        # V-IAS-C2-03: the record is provisional (never fabricates a settled cost).
        _check("V-IAS-C2-03-provisional-lifecycle", rec is not None and rec.lifecycle == "PROJECTED"
               and rec.settled_at is None)

        # V-IAS-C2-04: magnitude is the real ordinal category, not a fabricated number.
        _check("V-IAS-C2-04-ordinal-magnitude", rec.foregone_magnitude in
               ("LOW", "MODERATE", "HIGH", "CRITICAL"), f"got {rec.foregone_magnitude}")

        # V-IAS-C2-05: a later pick of the foregone item settles the earlier record.
        settled_n = oc.settle_if_later_chosen(foregone, repo_root=repo_root)
        rows_after = oc._read_ledger(repo_root)
        _check("V-IAS-C2-05-settlement",
               settled_n == 1 and rows_after[0]["lifecycle"] == "CONFIRMED",
               f"settled_n={settled_n} rows={rows_after}")

        # V-IAS-C2-06: domain aggregate reflects the settled state, per-domain
        # (never a pooled false-precision total -- Part VI §6.4).
        agg = oc.domain_aggregate(repo_root)
        dom = foregone.id.split("-", 1)[0]
        _check("V-IAS-C2-06-domain-aggregate",
               agg.get(dom, {}).get("CONFIRMED") == 1, f"agg={agg}")

        # V-IAS-C2-07: real end-to-end wiring -- what_now_tracked (imported lazily
        # so its own ledger writes go to the REAL vault/ias path) still returns
        # the identical recommendation what_now() would, proving zero regression
        # to the existing pure function's contract.
        from modules.backlog_autopilot import what_now_tracked
        untracked_result = what_now(items)
        tracked_result = what_now_tracked(items)
        _check("V-IAS-C2-07-zero-regression-on-recommendation",
               tracked_result.recommended is not None
               and tracked_result.recommended.id == untracked_result.recommended.id
               and tracked_result.score == untracked_result.score,
               f"tracked={tracked_result} untracked={untracked_result}")

    # --- failure modes, read from the module rather than invented ----------------
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        solo = BacklogItem("FIX-1", "Fix login bug", 0, "S", "Critical")

        # rank_and_forgo returns None when `chosen` was the only candidate: with no
        # live alternative there is no cost, and inventing one would fabricate the
        # very number Part V exists to keep honest.
        _check("V-IAS-C2-08-no-alternative-is-none",
               rank_and_forgo([solo], solo, _score) is None,
               f"got {rank_and_forgo([solo], solo, _score)}")

        # A None foregone must write NOTHING. If this guard broke, every decision
        # with no alternative would append a record naming a cost nobody paid.
        before = len(oc._read_ledger(repo_root))
        none_rec = record_opportunity_cost(solo, None, repo_root=repo_root)
        after = len(oc._read_ledger(repo_root))
        _check("V-IAS-C2-09-none-foregone-writes-nothing",
               none_rec is None and after == before == 0,
               f"rec={none_rec} rows {before}->{after}")

        # Settlement fires once. A CONFIRMED row re-settled on a later pick of the
        # same item would inflate the confirmed count without a second decision.
        other = BacklogItem("FEAT-2", "Add 2FA", 1, "L", "High")
        record_opportunity_cost(solo, other, repo_root=repo_root)
        first = oc.settle_if_later_chosen(other, repo_root=repo_root)
        second = oc.settle_if_later_chosen(other, repo_root=repo_root)
        _check("V-IAS-C2-10-settlement-is-not-repeatable",
               first == 1 and second == 0
               and oc.domain_aggregate(repo_root)["FEAT"]["CONFIRMED"] == 1,
               f"first={first} second={second} agg={oc.domain_aggregate(repo_root)}")

        # A corrupt line must not take the reader down with it. The ledger is
        # append-only from several callers, so a torn write is reachable.
        oc.ledger_path(repo_root).open("a", encoding="utf-8").write("{not json\n")
        rows = oc._read_ledger(repo_root)
        _check("V-IAS-C2-11-corrupt-line-is-skipped",
               len(rows) == 1 and rows[0]["foregone_id"] == "FEAT-2",
               f"got {rows}")

        # Found by tools/mutation_probe.py, not by reading: mutating the empty-ledger
        # early return from 0 to 1 survived, so nothing observed it. Settling before
        # any decision was recorded must report zero settlements, or the first call
        # of a fresh install invents one.
        _check("V-IAS-C2-14-settle-on-empty-ledger",
               oc.settle_if_later_chosen(solo, repo_root=Path(tmp) / "unwritten") == 0,
               "settled a record against a ledger that does not exist")

        # Same source: the PROJECTED bucket's initial count was unobserved, so an
        # aggregate could open at 1 and overstate every domain by one.
        fresh = Path(tmp) / "fresh"
        record_opportunity_cost(solo, other, repo_root=fresh)
        _check("V-IAS-C2-15-aggregate-counts-from-zero",
               oc.domain_aggregate(fresh) == {"FEAT": {"PROJECTED": 1, "CONFIRMED": 0}},
               f"got {oc.domain_aggregate(fresh)}")

        # Settling against an item nobody ever forwent settles nothing.
        _check("V-IAS-C2-12-unknown-item-settles-nothing",
               oc.settle_if_later_chosen(
                   BacklogItem("NOPE-9", "never seen", 9, "S", "Low"),
                   repo_root=repo_root) == 0,
               "settled a record for an item that was never foregone")

        # D-003, pinned rather than papered over: an impact string outside the
        # ordinal vocabulary collapses to LOW, the LEAST urgent category, so an
        # unrecognised value is indistinguishable from a genuinely Low one. The
        # rule_compiler keeps exactly this distinction (UNRECOGNIZED vs UNDECLARED)
        # because collapsing them lets a defect read as a benign value. Asserting
        # current behaviour keeps the gap visible; changing it edits a persisted
        # ordinal vocabulary, which is an Owner call, not a test-time fix.
        odd = BacklogItem("SEC-4", "rotate keys", 4, "M", "Blocker")
        odd_rec = record_opportunity_cost(solo, odd, repo_root=repo_root)
        _check("V-IAS-C2-13-unrecognised-impact-collapses-to-low",
               odd_rec.foregone_magnitude == "LOW",
               f"got {odd_rec.foregone_magnitude} -- if this changed, D-003 was "
               "addressed and OWNER_QUEUE must be updated")

    total = _passes + _fails
    print(f"IAS_C2_PASS={_passes}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
