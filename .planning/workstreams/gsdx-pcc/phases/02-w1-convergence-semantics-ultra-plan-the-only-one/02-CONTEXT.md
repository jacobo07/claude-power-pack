# Phase 2: W1 Convergence semantics (ULTRA-PLAN, the only one) - Context

**Gathered:** 2026-10-07
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss; UNATTENDED mission, worker epoch 3)

<domain>
## Phase Boundary

Proof states, certificate validity, causal fingerprint, freshness classes, frontier semantics, event types, kill
switches and legacy-log replay are resolved in the spec, audited, and land as a zero-behaviour-change compatibility
seam. (ROADMAP Phase 2; requirements D01, D03, D10, D43, D44.)

Two halves, in order:
1. **Spec resolution (ULTRA-PLAN).** Amend `vault/specs/gsdx-proof-conserving-convergence.md` §Semantics until every
   item below is decided. Dispatch `oneshot-architect-auditor` on the amended spec. Inject every gap it numbers.
2. **Compatibility seam (EXECUTION).** New event types and projections, with ZERO behaviour change: every existing
   goal suite is unchanged and green, and a replay test over a recorded legacy goal log passes.

</domain>

<decisions>
## Implementation Decisions

### Locked by the spec / roadmap / Owner (not discretionary)
- **Spec of record:** `vault/specs/gsdx-proof-conserving-convergence.md`. §Semantics says "nothing below is final
  until the W1 audit", and this phase is that audit. Amend the spec in place; do not fork a second spec.
- **ULTRA protocol in an unattended run.** The /ultra Q&A pass (phase 2 of 7) is answered BY THE WORKER from the
  spec, the dataset §s that DENOMINATOR rows cite, and Phase 1 evidence. Each answer is recorded as a decision with
  its reason in the workstream STATE.md. Never stop to ask (mission card DECISION GATE). Anything the gate reserves
  to the Owner is recorded as OWNER DECISION NEEDED, and the work continues.
- **Auditor:** `subagent_type: oneshot-architect-auditor`. It is read-only and emits a numbered gap list. Every gap
  is injected into the spec, or dispositioned with a reason in the phase EVIDENCE.md. Agent dispatch goes alone in
  its batch, with a bound and a durable-output clause (write findings to a file as it goes).
- **Items the spec must resolve** (from §Semantics plus the kill-switch and rollback sections):
  - proof states FRESH / INHERITED / SUPERSEDED / STALE / UNKNOWN, with UNKNOWN -> FULL (D01);
  - certificate validity: claim, revision, gate pin, causal fingerprint, environment, policy;
  - the causal fingerprint premise set, with unknown -> legacy whole-tree binding (`git_state.py:129-133`);
  - freshness classes extending `gate_class`, including the legacy mapping;
  - frontier semantics, with `decide()` keeping its signature (D43);
  - the new event types, all additive;
  - kill switches `GSDX_FRONTIER=off` and `GSDX_PROOF_INHERITANCE=off`;
  - legacy-log replay;
  - the typed proof contract, where a legacy done_gate is a one-element contract (D10);
  - the five laws as executable invariants + V-gates (D03);
  - event log, not a second DB (D44).
- **Zero behaviour change** is the seam's whole contract. Every new event type is additive and every projection is
  pure over the GoalLog. No legacy caller changes behaviour, and with no new events present the outputs are
  byte-identical. Incumbent suite counts to hold (spec Reality 13, gate_provider now 18/18 after R01): reconcile
  22/22, judge 11/11, convergence 29/29, sweep 14/14, epoch 19/19, chaos 15/15, mutation_safety 8/8, gate_provider
  18/18, plus every other `tools/test_gsd_x_goal_*.py` at its Phase 1 count (`01-EVIDENCE.md` incumbent table).
- **Legacy replay corpus:** g-002-router-surface and g-001-smoke-runner, recorded by an older engine under
  `~/.claude/state/gsd-x/goals`. They are read ONLY through a hash-verified copy (the `tools/gsdx_goal_timeline.py
  recorded` pattern) and never written. A committed fixture copy under the test tree is preferred, so that the
  replay test is hermetic and does not depend on the live store.
- **RED-first** applies to any behaviour this phase adds. For a seam whose contract is "no change", the red case is
  that a projection or event changes a legacy output, and that case must be driven and seen to fail the
  invariant test.
- **Liveness:** each new module is wired in the same commit, or declared in
  `vault/liveness/reachability_registry.json`. `python modules/liveness/reachability.py` exits 0 at phase end.
- **Operating constraints** in ROADMAP.md apply verbatim: worktree-only writes, PowerShell for git/python, the
  absolute git path, hermetic tests, one msgfile per commit, never push.

### Claude's Discretion
- Module layout for the new event types and projections, inside the `modules/gsd_x/goal/` owner. No new top-level
  package.
- Whether the five laws land as one invariant suite or as gates inside the existing suites, as long as each law has
  a gate that can go red.

</decisions>

<code_context>
## Existing Code Insights

Spec Reality Scan items 1-17 carry file:line anchors: reconcile.py:148/:205, sweep.py:308-390, judge.py:146-179,
git_state.py:129-133, evidence_bundle.py:140-141. Phase 1 premise signatures are in
`../01-w0-reality-baseline-and-incumbent-measurement/01-PREMISES.md`.
Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

- The judge replay baselines (2.9 s g-002, 32.3 s g-001, 0.4 s fixture) are the honest incumbent for any later
  VALIDATE-vs-REPLAY claim (Phase 5). This phase must not regress them.
- Phase 1 warnings carried forward: `tools/gsdx_reality_baseline.py` and `tools/gsdx_goal_timeline.py` sit outside
  the liveness aperture (reachability scans `modules/` only). They are declared or wired by Phase 9/10.

</specifics>

<deferred>
## Deferred Ideas

- Frontier compilation and scheduling behaviour (Phase 3), candidate snapshots and inheritance behaviour (Phase 4),
  the judge VALIDATE path (Phase 5). Phase 2 only lands their event types and projections, with no behaviour change.

</deferred>
