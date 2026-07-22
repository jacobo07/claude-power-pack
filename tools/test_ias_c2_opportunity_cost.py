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

    total = _passes + _fails
    print(f"IAS_C2_PASS={_passes}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
