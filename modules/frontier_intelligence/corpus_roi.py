#!/usr/bin/env python3
"""corpus_roi.py -- B1: Dataset ROI Ledger (D2A+ Replacement Systems Discovery, macrofamily B).

FIOS `token_irr.py` prices a SESSION's frontier spend against its deposits. Nothing
in the estate prices a SEALED KB CORPUS's build-and-maintain cost against its
realized value -- confirmed absent by direct read of FIOS (`evolution_engine.py` is
a health/mutation heuristic, not a cost-vs-benefit number) and DFP (`dfp_00...:X.3`
names a citation-rate proxy but ships no formula). See
`vault/plans/d2a-replacement-2026-07-17.md` macrofamily B for the reality scan.

This does NOT invent a token-cost figure: no historical per-corpus token-spend
ledger exists anywhere on disk (`PP_SESSION_TOKENS` is live-session-only, never
persisted per corpus over time), and fabricating one would violate CO-12's
Telemetry-Before-Claims contract ("(metric, source, value), or it is a
hypothesis"). Instead this computes an honest, disk-sourced PROXY:

  word_count          -- the corpus's own build size (SQI's own WORD_FLOOR logic,
                          generalized to any corpus; a stand-in for spend, since
                          size is the one cost signal actually on disk).
  citation_count       -- real cross-corpus references to this corpus's own IDs,
                          found by grepping every OTHER corpus + modules/ + tools/.
                          Evidence of reuse, not a claimed one.
  liveness_state        -- the corpus's runtime module's D1 Liveness Ledger verdict,
                          if one is registered (most KB-only corpora have none --
                          reported honestly as NOT_REGISTERED, never fabricated).
  citations_per_1k_words -- the one composite ratio, shaped like token_irr's
                          "assets per 1k tokens" but at corpus granularity.

Fail-open ABSOLUTE: any error -> a benign zeroed report, never an exception.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Registry of sealed corpora this ledger knows how to price. Each entry names its
# own directory (for word_count + exclusion during citation search), the
# word-boundary citation pattern(s) that mark a genuine reference to it elsewhere
# (never a bare substring -- SQI's own GMV/ROAS/CAC lesson: an imprecise pattern
# manufactures findings), and its D1 Liveness Ledger id if one is registered.
# `liveness_id: None` is itself an honest, reportable fact -- not every sealed
# corpus has a runtime module wired into D1 yet.
CORPUS_REGISTRY: dict[str, dict] = {
    "daif":     {"dir": "d2a_fabric",          "patterns": [r"\bDAIF\b"],                    "liveness_id": None},
    "sqi":      {"dir": "sqi",                 "patterns": [r"\bSQI\b"],                     "liveness_id": "sqi-runner"},
    "fd":       {"dir": "fable_distillation",  "patterns": [r"\bFD-\d\d\b", r"\bFD-07\b"],   "liveness_id": "fd-07-flywheel"},
    "drk":      {"dir": "decision_review",     "patterns": [r"\bDRK\b"],                     "liveness_id": "drk-kernel"},
    "co":       {"dir": "cognitive_os",        "patterns": [r"\bCO-\d\d\b"],                 "liveness_id": None},
    "graphify": {"dir": "graphify",            "patterns": [r"\bGK-\d\d\b", r"\bgraphify\b"], "liveness_id": None},
    "dfp":      {"dir": "dataset_first",       "patterns": [r"\bDFP\b"],                     "liveness_id": "dfp-necessity-ledger"},
    "acis":     {"dir": "acis",                "patterns": [r"\bACIS\b"],                    "liveness_id": None},
}

_TEXT_SUFFIXES = (".txt", ".md")


@dataclass
class CorpusROIReport:
    corpus_id: str
    word_count: int
    citation_count: int
    citing_files: list[str] = field(default_factory=list)
    liveness_state: str = "NOT_REGISTERED"
    citations_per_1k_words: float = 0.0
    measured: bool = False
    note: str = ""


def _word_count(corpus_dir: Path) -> int:
    """Sum word counts across every dataset file in a corpus's own directory.
    Generalizes SQI's own Part-size logic (test_sqi.py WORD_FLOOR check) to any
    corpus's whole directory rather than just its Parts."""
    total = 0
    if not corpus_dir.is_dir():
        return 0
    for path in corpus_dir.rglob("*"):
        if path.suffix.lower() not in _TEXT_SUFFIXES or not path.is_file():
            continue
        try:
            total += len(path.read_text(encoding="utf-8-sig", errors="replace").split())
        except OSError:
            continue
    return total


def _citations(corpus_id: str, patterns: list[str], own_dir: Path, *,
               repo_root: Path, kb_root: Path) -> tuple[int, list[str]]:
    """Grep every OTHER corpus's files + modules/ + tools/ for a word-boundary
    match on this corpus's own citation patterns. Real cross-corpus reference
    count, not a claimed one. Fail-open per-file: an unreadable file is skipped,
    never a fatal error."""
    compiled = [re.compile(p) for p in patterns]
    hits = 0
    files: list[str] = []
    search_roots = [
        d for d in (kb_root.iterdir() if kb_root.is_dir() else [])
        if d.is_dir() and d.resolve() != own_dir.resolve()
    ]
    search_roots += [repo_root / "modules", repo_root / "tools"]
    for root in search_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() not in (*_TEXT_SUFFIXES, ".py"):
                continue
            try:
                text = path.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            n = sum(len(rx.findall(text)) for rx in compiled)
            if n:
                hits += n
                files.append(str(path.relative_to(repo_root).as_posix()))
    return hits, sorted(files)


def _liveness_state(liveness_id: str | None) -> str:
    """Pull the D1 Liveness Ledger's own verdict for this corpus's runtime module,
    if one is registered. Absence of a registration is reported honestly as
    NOT_REGISTERED -- it is not the same claim as WIRED-BUT-SILENT or ORPHANED,
    and collapsing the distinction would fabricate a verdict D1 never rendered."""
    if not liveness_id:
        return "NOT_REGISTERED"
    try:
        from modules.liveness.liveness_ledger import audit
        rows = audit()
        for row in rows:
            if row.get("id") == liveness_id:
                return str(row.get("verdict", "UNKNOWN"))
        return "NOT_REGISTERED"
    except Exception:  # noqa: BLE001 -- fail-open
        return "UNKNOWN"


def compute_corpus_roi(corpus_id: str, *, repo_root: Path | None = None,
                        registry: dict | None = None,
                        probe_liveness: bool = True) -> CorpusROIReport:
    """Compute the disk-sourced ROI proxy for one sealed corpus. `corpus_id` must
    be a key of `registry` (defaults to CORPUS_REGISTRY). `repo_root` retargets
    BOTH the corpus lookup (repo_root/vault/knowledge_base) and the modules/tools
    search roots -- a test pointing repo_root at a temp tree touches nothing real.
    `probe_liveness=False` skips the D1 Liveness Ledger call for a fully hermetic
    run (liveness reflects the REAL live system, not a temp repo, so a hermetic
    test that cares only about word/citation counting should disable it).
    Fail-open -> a zeroed, honest report."""
    try:
        repo_root = Path(repo_root) if repo_root else _PP_ROOT
        kb_root = repo_root / "vault" / "knowledge_base"
        reg = registry if registry is not None else CORPUS_REGISTRY
        spec = reg.get(corpus_id)
        if spec is None:
            return CorpusROIReport(
                corpus_id=corpus_id, word_count=0, citation_count=0,
                measured=False,
                note=f"unknown corpus_id (not in registry): {corpus_id}",
            )
        own_dir = kb_root / spec["dir"]
        words = _word_count(own_dir)
        cites, files = _citations(corpus_id, spec["patterns"], own_dir,
                                   repo_root=repo_root, kb_root=kb_root)
        live = _liveness_state(spec["liveness_id"]) if probe_liveness else "SKIPPED"
        ratio = round(cites / (words / 1000.0), 3) if words else 0.0
        return CorpusROIReport(
            corpus_id=corpus_id, word_count=words, citation_count=cites,
            citing_files=files, liveness_state=live,
            citations_per_1k_words=ratio, measured=bool(words),
            note=(f"{cites} citation(s) across {len(files)} file(s), "
                  f"{words:,} words, liveness={live}"),
        )
    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE
        return CorpusROIReport(
            corpus_id=corpus_id, word_count=0, citation_count=0,
            measured=False, note=f"corpus_roi error (fail-open): {e}",
        )


def record_corpus_roi(report: CorpusROIReport, *, state_dir=None) -> bool:
    """Feed the corpus ROI to CO-12 (the single instrument) as one producer
    signal. NEVER a parallel accountant -- mirrors token_irr.record_irr exactly.
    Fail-open."""
    try:
        from modules.cognitive_os.co_12_telemetry import record_signal
        return record_signal("corpus_roi", {
            "corpus_id": report.corpus_id,
            "word_count": report.word_count,
            "citation_count": report.citation_count,
            "citations_per_1k_words": report.citations_per_1k_words,
            "liveness_state": report.liveness_state,
        }, state_dir=state_dir)
    except Exception:  # noqa: BLE001 -- a telemetry write never breaks the caller
        return False


def escalate_negative_roi(reports: list[CorpusROIReport], *, min_words: int = 500,
                           state_dir=None) -> list[str]:
    """Escalate corpora with zero cross-corpus citations despite a substantial
    word count -- the one live decision surface confirmed for this producer
    (see vault/OWNER_QUEUE.md's 2026-07-30 DEFERRED entry: CO-12's
    readiness_report() has no live caller, so that path stays closed).
    Fail-open per report; returns the row ids actually appended."""
    ids: list[str] = []
    for r in reports:
        try:
            if r.citation_count != 0 or r.word_count < min_words:
                continue
            from modules.owner_queue.owner_queue import append
            rid = append(
                action=(f"Corpus '{r.corpus_id}' has {r.word_count:,} words and "
                        f"zero cross-corpus citations -- review for "
                        f"consolidation/retirement"),
                command=(f"python modules/frontier_intelligence/corpus_roi.py "
                         f"--corpus {r.corpus_id} --json"),
                component=f"corpus:{r.corpus_id}",
                source="corpus_roi",
                state_dir=state_dir,
            )
            ids.append(rid)
        except Exception:  # noqa: BLE001 -- fail-open, one bad report never blocks the rest
            continue
    return ids


def rank_all(*, repo_root: Path | None = None, registry: dict | None = None,
             probe_liveness: bool = True) -> list[CorpusROIReport]:
    """Compute the ROI proxy for every registered corpus, ranked descending by
    citations_per_1k_words. The ranking IS the deliverable -- a bare number per
    corpus is not comparable without its siblings."""
    reg = registry if registry is not None else CORPUS_REGISTRY
    reports = [compute_corpus_roi(cid, repo_root=repo_root, registry=reg,
                                   probe_liveness=probe_liveness) for cid in reg]
    return sorted(reports, key=lambda r: r.citations_per_1k_words, reverse=True)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="B1 Dataset ROI Ledger -- corpus citation density proxy")
    ap.add_argument("--corpus", default=None, help="one corpus_id (see CORPUS_REGISTRY); omit for all, ranked")
    ap.add_argument("--record", action="store_true", help="feed each report to CO-12")
    ap.add_argument("--escalate", action="store_true",
                     help="escalate zero-citation corpora to OWNER_QUEUE")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    reports = [compute_corpus_roi(args.corpus)] if args.corpus else rank_all()
    if args.record:
        for r in reports:
            record_corpus_roi(r)
    if args.escalate:
        ids = escalate_negative_roi(reports)
        print(f"escalated {len(ids)} corpus/corpora to OWNER_QUEUE: {ids}"
              if ids else "escalate: no corpus qualified this run")
    if args.json:
        print(json.dumps([asdict(r) for r in reports], ensure_ascii=False, indent=2))
    else:
        for r in reports:
            print(f"{r.corpus_id:10s}  words={r.word_count:>7,}  citations={r.citation_count:>3}  "
                  f"ratio={r.citations_per_1k_words:>6.3f}/1k  liveness={r.liveness_state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
