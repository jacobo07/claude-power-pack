"""Knowledge Vault Integration (CCF component S5-B), per CCF_KNOWLEDGE_SYSTEMS.md.

Appends CCF feed events into the EXISTING vault/knowledge_base/ tree -- a new
per-domain subdirectory (vault/knowledge_base/ccf/), matching the convention
every other sealed family already uses (cdio/, crawl_os/, d2a_fabric/, ...).
No parallel vault. JSONL append pattern mirrors modules/osa/never_again.py.

Every event carries provenance, timestamp, and confidence per the CCF-wide
convention (CCF_KNOWLEDGE_SYSTEMS.md's feed table).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
FEED_DIR = PP_ROOT / "vault" / "knowledge_base" / "ccf"

CREATIVE_FAILURES_PATH = FEED_DIR / "creative_failures.jsonl"
PROVIDER_BENCHMARKS_PATH = FEED_DIR / "provider_benchmarks.jsonl"
TRADEMARK_RISK_PATH = FEED_DIR / "trademark_risk.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _append_jsonl(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def log_creative_failure(
    failure_id: str, component: str, concept_id: str, evidence: str,
    project: str = None, confidence: float = 1.0,
) -> None:
    """Per Failure Corpus (INSTITUTIONAL_EXTRACTION.md §B): a failure_id is
    added once at first observation; repeated occurrences of the same
    failure_id are still logged here (one line per event) -- recurrence
    counting is a read-time aggregation over this log, not a write-time
    dedup, so the raw event history is never lost.
    """
    _append_jsonl(CREATIVE_FAILURES_PATH, {
        "failure_id": failure_id,
        "component": component,
        "concept_id": concept_id,
        "evidence": evidence,
        "project": project,
        "provenance": {"project": project} if project else {},
        "timestamp": _utc_now_iso(),
        "confidence": confidence,
    })


def log_provider_benchmark(
    provider: str, model_id: str, resolution: str, quality: str,
    cost, latency_ms, verdict: str, project: str = None,
) -> None:
    _append_jsonl(PROVIDER_BENCHMARKS_PATH, {
        "provider": provider,
        "model_id": model_id,
        "resolution": resolution,
        "quality": quality,
        "cost": cost,
        "latency_ms": latency_ms,
        "verdict": verdict,
        "provenance": {"project": project} if project else {},
        "timestamp": _utc_now_iso(),
        "confidence": 1.0,
    })


def log_trademark_risk(
    concept_id: str, concept_description: str, detected_by: str,
    nearest_known_mark, verdict_at_time: str, corpus_version: str,
    resolution: str = None, project: str = None,
) -> None:
    """Per CCF_KNOWLEDGE_SYSTEMS.md's Trademark Risk Corpus -- justified by
    the founding CCF-F01 failure. Never "finished"; the health signal is the
    trend of scanner-missed-but-human-caught collisions over time, not a
    count reaching zero.
    """
    _append_jsonl(TRADEMARK_RISK_PATH, {
        "concept_id": concept_id,
        "concept_description": concept_description,
        "detected_by": detected_by,  # "scanner" | "human"
        "nearest_known_mark": nearest_known_mark,
        "verdict_at_time": verdict_at_time,
        "corpus_version_at_time": corpus_version,
        "resolution": resolution,
        "provenance": {"project": project} if project else {},
        "timestamp": _utc_now_iso(),
        "confidence": 1.0,
    })
