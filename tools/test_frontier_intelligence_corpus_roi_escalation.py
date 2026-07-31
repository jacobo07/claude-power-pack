#!/usr/bin/env python3
"""B1 escalation done-gate -- corpus_roi.escalate_negative_roi().

Verifies the wiring gap closed 2026-07-31: corpus_roi's own docstring named
CO-12's readiness_report() as its destination, but readiness_report() has no
live caller anywhere (vault/OWNER_QUEUE.md 2026-07-30 DEFERRED entry). The
actually-live consumer is modules/owner_queue/owner_queue.py::append() --
this gate proves escalate_negative_roi() reaches it and produces an
observable, idempotent OWNER_QUEUE row.

Hermetic: every gate uses tempfile.TemporaryDirectory() as state_dir; no
global ~/.claude/state writes. Run x3 -> identical results each time.

    python tools/test_frontier_intelligence_corpus_roi_escalation.py

Exit 0 when every gate passes, 1 otherwise.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from modules.frontier_intelligence import corpus_roi as C  # noqa: E402
from modules.owner_queue.owner_queue import load as oq_load  # noqa: E402

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(f"  FAIL {gate}: {diagnostic}")


def _report(corpus_id: str, *, citations: int, words: int) -> C.CorpusROIReport:
    return C.CorpusROIReport(
        corpus_id=corpus_id, word_count=words, citation_count=citations,
        measured=True, note="synthetic",
    )


def test_zero_citation_escalates() -> None:
    with tempfile.TemporaryDirectory() as td:
        reports = [_report("orphaned", citations=0, words=2000)]
        ids = C.escalate_negative_roi(reports, state_dir=td)
        rows = oq_load(td)
        if (len(ids) == 1 and len(rows) == 1
                and rows[0]["component"] == "corpus:orphaned"
                and rows[0]["source"] == "corpus_roi"
                and rows[0]["status"] == "pending"):
            _ok("V-ROI-ESCALATE-ZERO-CITATION",
                f"zero-citation corpus escalated: {rows[0]['action']!r}")
        else:
            _fail("V-ROI-ESCALATE-ZERO-CITATION", f"ids={ids} rows={rows}")


def test_cited_corpus_never_escalates() -> None:
    with tempfile.TemporaryDirectory() as td:
        reports = [_report("healthy", citations=3, words=2000)]
        ids = C.escalate_negative_roi(reports, state_dir=td)
        rows = oq_load(td)
        if not ids and not rows:
            _ok("V-ROI-ESCALATE-CITED-SKIPPED", "corpus with real citations never queued")
        else:
            _fail("V-ROI-ESCALATE-CITED-SKIPPED", f"ids={ids} rows={rows}")


def test_below_min_words_never_escalates() -> None:
    """A tiny stub corpus with zero citations is noise, not a real ROI signal --
    min_words filters it out."""
    with tempfile.TemporaryDirectory() as td:
        reports = [_report("stub", citations=0, words=20)]
        ids = C.escalate_negative_roi(reports, min_words=500, state_dir=td)
        rows = oq_load(td)
        if not ids and not rows:
            _ok("V-ROI-ESCALATE-MINWORDS", "sub-threshold stub corpus never queued")
        else:
            _fail("V-ROI-ESCALATE-MINWORDS", f"ids={ids} rows={rows}")


def test_mixed_batch_only_qualifying_escalate() -> None:
    with tempfile.TemporaryDirectory() as td:
        reports = [
            _report("orphaned-a", citations=0, words=1000),
            _report("healthy-b", citations=2, words=1000),
            _report("orphaned-c", citations=0, words=800),
            _report("stub-d", citations=0, words=10),
        ]
        ids = C.escalate_negative_roi(reports, state_dir=td)
        rows = oq_load(td)
        components = {r["component"] for r in rows}
        if (len(ids) == 2
                and components == {"corpus:orphaned-a", "corpus:orphaned-c"}):
            _ok("V-ROI-ESCALATE-MIXED-BATCH",
                f"2/4 qualifying corpora escalated: {sorted(components)}")
        else:
            _fail("V-ROI-ESCALATE-MIXED-BATCH", f"ids={ids} components={components}")


def test_idempotent_rerun() -> None:
    """append() is idempotent by (action, command) hash -- re-running the same
    escalation over the same state_dir must not duplicate the row."""
    with tempfile.TemporaryDirectory() as td:
        reports = [_report("orphaned", citations=0, words=2000)]
        first = C.escalate_negative_roi(reports, state_dir=td)
        second = C.escalate_negative_roi(reports, state_dir=td)
        rows = oq_load(td)
        if first == second and len(rows) == 1:
            _ok("V-ROI-ESCALATE-IDEMPOTENT",
                f"two runs, same row id {first!r}, exactly 1 OWNER_QUEUE row")
        else:
            _fail("V-ROI-ESCALATE-IDEMPOTENT", f"first={first} second={second} rows={len(rows)}")


def test_failopen_bad_report_never_blocks_batch() -> None:
    """A malformed report (wrong type in a field) must not stop the rest of
    the batch from escalating -- fail-open per report, per corpus_roi's own
    ABSOLUTE fail-open contract."""
    with tempfile.TemporaryDirectory() as td:
        bad = _report("bad", citations=0, words=2000)
        bad.corpus_id = None  # type: ignore[assignment] -- forces an f-string TypeError path...
        # ...none: corpus_id=None still f-string-formats cleanly in Python, so use a
        # genuinely broken attribute instead to force the except branch.
        del bad.__dict__["word_count"]
        good = _report("good", citations=0, words=2000)
        ids = C.escalate_negative_roi([bad, good], state_dir=td)
        rows = oq_load(td)
        if len(ids) == 1 and len(rows) == 1 and rows[0]["component"] == "corpus:good":
            _ok("V-ROI-ESCALATE-FAILOPEN",
                "malformed report skipped, sibling report still escalated")
        else:
            _fail("V-ROI-ESCALATE-FAILOPEN", f"ids={ids} rows={rows}")


def main() -> int:
    for fn in (
        test_zero_citation_escalates,
        test_cited_corpus_never_escalates,
        test_below_min_words_never_escalates,
        test_mixed_batch_only_qualifying_escalate,
        test_idempotent_rerun,
        test_failopen_bad_report_never_blocks_batch,
    ):
        fn()

    for line in _passes:
        print(line)
    for line in _fails:
        print(line)

    total = len(_passes) + len(_fails)
    print(f"\nCORPUS_ROI_ESCALATION_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
