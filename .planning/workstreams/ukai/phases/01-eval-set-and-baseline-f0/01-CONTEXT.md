# Phase 1: Eval set and baseline (F0) - Context

**Gathered:** 2026-10-10
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss; Owner approved the plan of record)

<domain>
## Phase Boundary

Recall quality is measured by an instrument independent of the retriever: a labelled query set
(`vault/evals/recall/queries.jsonl`, >= 50 queries), a harness (`tools/recall_eval.py`), a gate that proves the
harness can fail (`tools/test_recall_eval.py`, V-RECALL-EVAL-*), and a committed `report-baseline.json` with a
classified miss list. Delivery ledger, scope filtering, new sources and aliasing are NOT in this phase.

</domain>

<decisions>
## Implementation Decisions

### Locked by the plan of record (`vault/plans/ukai-2026-10-10.md`, ROADMAP operating constraints)
- Owner of recall is `modules/gsd_x/recall.py`; spec `vault/specs/prompt-recall.md`; existing gate `tools/test_prompt_recall.py`. Extend, do not replace.
- Labels are written from the SOURCE files (memories, UKDL, HARD-RULES, CLAE), never from recall's own output.
- Each query has `expect` (paths that must appear in top 5), `forbid`, `scope` (cwd project), `why`.
- Metrics: recall@5, precision@5, cross-scope exposure, stale exposure, abstain rate, p50/p95 latency.
- Two runs: (a) hermetic fixture index in a temp HOME, (b) live index `~/.claude/state/recall/recall.db` READ-ONLY.
- Misses are classified source-not-indexed / vocabulary / ranking / scope (feeds Phases 4 and 5).
- Unmeasured metrics stay UNKNOWN; verdict vocabulary PROVEN / OBSERVED / UNJUDGED / BLOCKED.
- Every negative test has a positive control; the harness must be able to return the other answer.

### Claude's Discretion
Query file schema details beyond the four required fields, report JSON layout, CLI flags, fixture corpus shape,
and how the miss classifier decides between categories. Follow the surrounding conventions of
`tools/test_prompt_recall.py` (V-gate naming, `_ok/_fail`, `*_PASS=n/n` summary line).

</decisions>

<code_context>
## Existing Code Insights

Codebase context is gathered during plan-phase research. Known anchors: `modules/gsd_x/recall.py`,
`vault/specs/prompt-recall.md`, `tools/test_prompt_recall.py`, `vault/liveness/reachability_registry.json`
(new tools must be declared or wired in the same commit).

</code_context>

<specifics>
## Specific Ideas

Python is `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`. Git is
`C:\Program Files\Git\cmd\git.exe -C C:\Users\User\Apps\pp-ukai`. Pathspec-scoped micro-commits, one message file
per commit. Never touch the live recall index except to read it; never write the main checkout.

</specifics>

<deferred>
## Deferred Ideas

Delivery ledger (Phase 2), privacy classes (Phase 3), new sources (Phase 4), ES/EN expansion (Phase 5).

</deferred>
