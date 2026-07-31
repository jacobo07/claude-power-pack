---
title: corpus_roi wiring + Emergence Runtime audit — ULTRA-PLAN
date: 2026-07-31
status: EXECUTED (all 3 sprints)
originating_prompt: PLAN MODE, "Dos gaps con evidencia directa: corpus_roi wiring + audit de Emergence Runtime"
---

# corpus_roi wiring + Emergence Runtime audit

Institutional backup of the plan approved via ExitPlanMode this session
(plan file: `~/.claude/plans/snoopy-leaping-fog.md`). Same content, this file
is the durable, git-tracked record per PP session-continuity doctrine.

## Summary of findings

1. `corpus_roi.py`'s originally-intended consumer (CO-12's
   `readiness_report()`) has zero live callers anywhere — confirmed via
   `vault/OWNER_QUEUE.md`'s own 2026-07-30 DEFERRED investigation. Wired to
   `modules/owner_queue/owner_queue.py::append()` instead — the one
   independently-verified-live escalation surface in the repo.

2. "Emergence Runtime" is **not novel**. `tools/dataset_enricher.py
   ::write_cross_project_patterns()` already scans every `Desktop/Cursor
   Projects` repo, detects error/lesson categories recurring in 2+ projects,
   and writes `CROSS-PROJECT-PATTERNS.md` — but that report has zero
   consumers, the same orphan-producer shape as (1). Verdict:
   `EXTEND_EXISTING_OWNER`. Full audit: `vault/audits/EMERGENCE_NOVELTY_AUDIT.md`.

Both gaps resolved the same way: wire the existing real producer to
`owner_queue.append()`, the confirmed-live surface, rather than building new
consumer infrastructure or a parallel detection system.

## Sprints executed

- **Sprint A** — `escalate_negative_roi()` added to `corpus_roi.py`,
  `--escalate` CLI flag, hermetic test x3 (6/6 gates:
  `tools/test_frontier_intelligence_corpus_roi_escalation.py`). Commit
  `3a6c1cd`. `vault/OWNER_QUEUE.md`'s corpus_roi entry flipped
  DEFERRED -> RESOLVED (commit `7d5e810`).
- **Sprint B** — novelty audit performed inline during planning (not a
  separate round-trip). Verdict `EXTEND_EXISTING_OWNER`, evidence table in
  `vault/audits/EMERGENCE_NOVELTY_AUDIT.md`.
- **Sprint C** — `escalate_transversal_patterns()` added to
  `tools/dataset_enricher.py` (`write_cross_project_patterns()` now returns
  its computed `transversal`/`cat_to_projects` instead of discarding them),
  wired into `main()`'s `--build` path, hermetic test x3 (6/6 gates including
  a real Entry->categorize()->transversal->OWNER_QUEUE end-to-end proof:
  `tools/test_dataset_enricher_escalation.py`). Commit `cf4f163`.

Full plan text (context, per-sprint rationale, verification plan, files
touched): see `~/.claude/plans/snoopy-leaping-fog.md` or the approved-plan
block in this session's transcript.
