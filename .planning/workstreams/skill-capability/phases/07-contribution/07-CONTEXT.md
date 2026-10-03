# Phase 7: Contribution - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44 (existing paired runs below are laptop readings, committed; no gex44 run is a laptop reading)
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Pillar E of `vault/programs/skill-capability/ledger.json`: contribution + result consumption. Frozen rule:
"contribution is claimed only from a paired benchmark inside the <= 10 new-session budget (D-SESSIONS); otherwise the
measurement records why the budget cannot separate the arms". Owners: `vault/specs/agent-capability-virtualization.md`,
`modules/capability_runtime/agent_spec.py`. Predicted RESEARCH_INSUFFICIENT_EVIDENCE (needs a `measurement` evidence:
file names a frozen denominator — here D-SESSIONS — and carries `command:` lines).

</domain>

<decisions>
## Implementation Decisions

### D-01 Use the committed paired data; spend no sessions unless the bound says it could separate
- Committed paired benchmark (laptop, PLAN-SKILL-RESIDENCY C2):
  `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/results-delivery.jsonl`, 8 rows, arms N0/R/C/P,
  n=2 each; orchestrator read at plan time: P PASS 1/2, N0 0/2, R 0/2, C 0/2 (verdict field `grade`; re-derive by
  script, also read `results-delivery-regrade.jsonl` and REPORT.md / ADDENDUM*.md for which grade is authoritative).
- Separation bound (computed by script, exact, no approximation): for the budget left (D-SESSIONS `new_benchmark_cap` =
  10, minus any sessions already consumed this program — 0 so far per phases 1-3 EVIDENCE/SUMMARY), enumerate the
  allocations (k per arm, two arms, 2k <= remaining) and, for each, the smallest pass-count difference that a two-sided
  Fisher exact test separates at alpha 0.05; then compare with the effect the committed data suggests. Expected
  conclusion (verify, do not trust): at 5 vs 5 only 5/5 vs 0/5 (p~0.008) or 4/5 vs 0/5 (p~0.048) separate, i.e. an
  effect >= 80 points; the committed data suggest ~50 points (n=2), so the budget cannot separate the arms ->
  RESEARCH_INSUFFICIENT_EVIDENCE with the bound as the measurement. If the computed bound says it CAN separate, stop
  and record an `[E]` owner-bundle line instead of running sessions (fresh sessions are laptop-plane and Owner-gated
  by boundary 2; gex44 runs of p3_delivery are impossible anyway: p3_runner sets Windows paths at import).
- Result consumption: report from the committed rows whether the delivered capability's output was consumed (e.g.
  `delivery` field vs `grade`), with n, never extrapolated (n < 5 -> not estimated, as pillar C's rule).

### D-02 Gate
- A small verdict script under `tools/` that recomputes the bound and the per-arm figures from the committed jsonl,
  renders the measurement file, and is drilled red: a fabricated jsonl with 5/5 vs 0/5 must flip the verdict to
  "separable"; zero/absent rows are UNMEASURED, never 0 (phase 2 review WR-03 lesson). Integer/exact arithmetic
  (fractions / math.comb), no scipy dependency.

### D-03 Closure
- `state.E` = RESEARCH_INSUFFICIENT_EVIDENCE with `measurement` evidence `vault/programs/skill-capability/evidence/E-contribution.md`
  (sha256 LF, names D-SESSIONS, `command:` lines), owner + commit refs; no gate entry needed (L5 runs gates only for
  IMPLEMENTED; cite the script via `command:` lines, as phase 2 did); L6 does not apply (predicted is not IMPLEMENT).
- Sessions consumed this phase: 0 (state it, with the evidence it is 0).
- `--pillar E` PASS; earlier pillars stay PASS. Ledger edit replaces only state.E; frozen asserted equal to FROZEN_AT copy.

### Claude's Discretion
Script name, whether to include a one-sided variant (report both if included; the verdict uses two-sided).

</decisions>

<code_context>
## Existing Code Insights
- p3 ablation dir: `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/` (REPORT.md, ADDENDUM*.md,
  results-*.jsonl, p3_delivery.py — read-only; another workstream owns it).
- Gate style: `tools/test_listing_floor_verdict.py` after review fixes 4ddd8846.
</code_context>

<specifics>
## Specific Ideas
- Print the full allocation table (k, min separable difference, p at that difference) in the measurement file.
</specifics>

<deferred>
## Deferred Ideas
- A larger-budget paired benchmark (laptop, Owner) -> owner bundle `[E]` with the n per arm the bound says is needed.
</deferred>
