#!/usr/bin/env python3
"""Cross-project pattern escalation done-gate -- dataset_enricher.py.

Verifies the Emergence Runtime novelty audit's resolution (2026-07-31,
vault/audits/EMERGENCE_NOVELTY_AUDIT.md): write_cross_project_patterns()
already detects real cross-repo patterns but CROSS-PROJECT-PATTERNS.md had
zero consumers. escalate_transversal_patterns() closes that gap by feeding
the already-computed transversal list to modules/owner_queue/owner_queue.py
::append() -- the same fix shape as corpus_roi's own escalation (Sprint A,
same session).

Hermetic: every gate uses tempfile.TemporaryDirectory() as state_dir (and,
for the integration gate, as out_dir too); no global ~/.claude/state or
Downloads/PowerPack_Sovereign_Datasets writes. Run x3 -> identical results.

    python tools/test_dataset_enricher_escalation.py

Exit 0 when every gate passes, 1 otherwise.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import dataset_enricher as DE  # noqa: E402
from modules.owner_queue.owner_queue import load as oq_load  # noqa: E402

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(f"  FAIL {gate}: {diagnostic}")


def test_qualifying_pattern_escalates() -> None:
    with tempfile.TemporaryDirectory() as td:
        transversal = [("Anti-Thrash / Edit Discipline", 3, 7)]
        cat_to_projects = {"Anti-Thrash / Edit Discipline": {"proj-a", "proj-b", "proj-c"}}
        ids = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=td)
        rows = oq_load(td)
        if (len(ids) == 1 and len(rows) == 1
                and rows[0]["component"] == "cross-project-pattern:Anti-Thrash / Edit Discipline"
                and rows[0]["source"] == "dataset_enricher"):
            _ok("V-CPP-ESCALATE-QUALIFYING",
                f"3-project pattern escalated: {rows[0]['action']!r}")
        else:
            _fail("V-CPP-ESCALATE-QUALIFYING", f"ids={ids} rows={rows}")


def test_below_min_projects_never_escalates() -> None:
    with tempfile.TemporaryDirectory() as td:
        transversal = [("Two Project Coincidence", 2, 3)]
        cat_to_projects = {"Two Project Coincidence": {"proj-a", "proj-b"}}
        ids = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=td)
        rows = oq_load(td)
        if not ids and not rows:
            _ok("V-CPP-ESCALATE-BELOW-FLOOR",
                "2-project pattern (below default min_projects=3) never queued")
        else:
            _fail("V-CPP-ESCALATE-BELOW-FLOOR", f"ids={ids} rows={rows}")


def test_mixed_batch_only_qualifying_escalate() -> None:
    with tempfile.TemporaryDirectory() as td:
        transversal = [
            ("Cat-A", 4, 10),
            ("Cat-B", 2, 3),
            ("Cat-C", 3, 5),
        ]
        cat_to_projects = {
            "Cat-A": {"p1", "p2", "p3", "p4"},
            "Cat-B": {"p1", "p2"},
            "Cat-C": {"p1", "p2", "p3"},
        }
        ids = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=td)
        rows = oq_load(td)
        components = {r["component"] for r in rows}
        want = {"cross-project-pattern:Cat-A", "cross-project-pattern:Cat-C"}
        if len(ids) == 2 and components == want:
            _ok("V-CPP-ESCALATE-MIXED-BATCH", f"2/3 qualifying patterns escalated: {sorted(components)}")
        else:
            _fail("V-CPP-ESCALATE-MIXED-BATCH", f"ids={ids} components={components}")


def test_idempotent_rerun() -> None:
    with tempfile.TemporaryDirectory() as td:
        transversal = [("Repeatable Pattern", 3, 6)]
        cat_to_projects = {"Repeatable Pattern": {"p1", "p2", "p3"}}
        first = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=td)
        second = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=td)
        rows = oq_load(td)
        if first == second and len(rows) == 1:
            _ok("V-CPP-ESCALATE-IDEMPOTENT",
                f"two runs, same row id {first!r}, exactly 1 OWNER_QUEUE row")
        else:
            _fail("V-CPP-ESCALATE-IDEMPOTENT", f"first={first} second={second} rows={len(rows)}")


def test_failopen_missing_projects_entry_never_blocks_batch() -> None:
    """A transversal category with no matching cat_to_projects key (data
    inconsistency) must not stop the rest of the batch -- fail-open per
    pattern, matching corpus_roi's own ABSOLUTE fail-open contract."""
    with tempfile.TemporaryDirectory() as td:
        transversal = [
            ("Broken Entry", 5, 9),   # deliberately absent from cat_to_projects below
            ("Good Entry", 3, 4),
        ]
        cat_to_projects = {"Good Entry": {"p1", "p2", "p3"}}
        ids = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=td)
        rows = oq_load(td)
        if len(ids) == 1 and len(rows) == 1 and rows[0]["component"] == "cross-project-pattern:Good Entry":
            _ok("V-CPP-ESCALATE-FAILOPEN", "malformed entry skipped, sibling pattern still escalated")
        else:
            _fail("V-CPP-ESCALATE-FAILOPEN", f"ids={ids} rows={rows}")


def test_end_to_end_write_cross_project_patterns_wiring() -> None:
    """Real Entry objects, real categorize(), real write_cross_project_patterns()
    -- proves the return-value wiring (transversal, cat_to_projects) main()
    relies on is correct, not just the escalation function in isolation."""
    with tempfile.TemporaryDirectory() as out_td, tempfile.TemporaryDirectory() as oq_td:
        entries = [
            DE.Entry("proj-a", "lessons", "fake/a.md",
                     "Anti-thrash triggered on repeated edits",
                     "anti-thrash guard fired after 3 consecutive edits"),
            DE.Entry("proj-b", "lessons", "fake/b.md",
                     "Same anti-thrash pattern here",
                     "hit the anti-thrash gate on this file too"),
            DE.Entry("proj-c", "lessons", "fake/c.md",
                     "And a third project with the identical issue",
                     "anti-thrash blocked a third consecutive edit"),
        ]
        stats = {"by_project": {"proj-a": 1, "proj-b": 1, "proj-c": 1}}
        transversal, cat_to_projects = DE.write_cross_project_patterns(entries, stats, out_td)
        cat = "Anti-Thrash / Edit Discipline"
        matched = [t for t in transversal if t[0] == cat]
        if not matched or cat not in cat_to_projects or len(cat_to_projects[cat]) != 3:
            _fail("V-CPP-ESCALATE-E2E-WIRING",
                  f"transversal={transversal} cat_to_projects={dict(cat_to_projects)}")
            return
        ids = DE.escalate_transversal_patterns(transversal, cat_to_projects, state_dir=oq_td)
        rows = oq_load(oq_td)
        if len(ids) == 1 and len(rows) == 1 and rows[0]["component"] == f"cross-project-pattern:{cat}":
            _ok("V-CPP-ESCALATE-E2E-WIRING",
                f"real Entry objects -> real categorize() -> real transversal "
                f"detection -> OWNER_QUEUE row for {cat!r}")
        else:
            _fail("V-CPP-ESCALATE-E2E-WIRING", f"ids={ids} rows={rows}")


def main() -> int:
    for fn in (
        test_qualifying_pattern_escalates,
        test_below_min_projects_never_escalates,
        test_mixed_batch_only_qualifying_escalate,
        test_idempotent_rerun,
        test_failopen_missing_projects_entry_never_blocks_batch,
        test_end_to_end_write_cross_project_patterns_wiring,
    ):
        fn()

    for line in _passes:
        print(line)
    for line in _fails:
        print(line)

    total = len(_passes) + len(_fails)
    print(f"\nDATASET_ENRICHER_ESCALATION_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
