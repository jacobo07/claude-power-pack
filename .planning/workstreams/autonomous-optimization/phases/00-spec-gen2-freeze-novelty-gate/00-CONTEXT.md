# Phase 0: Spec, gen2 freeze, novelty gate - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

The programme is pre-registered before any edit (ROADMAP Phase 0). Success criteria, verbatim from ROADMAP:

1. `vault/specs/autonomous-optimization.md` (T3, `covers:` front matter) with PRD, arch, acceptance, rollback,
   kill switches.
2. `vault/programs/incremental-cognition/gen2/ledger.json` + `FROZEN_AT`: pillars M, O, P, Q, R with predicted
   terminal and rule; gen1 `frozen` untouched. The IC done-gate wrapper judges gen2 too; `--selftest` kills a
   mutant per new rule.
3. `modules/spec_gate` novelty check recorded: classification EXTEND_EXISTING_OWNER with file:line evidence from a
   discovered sweep, or the slice stops.
4. Champion numbers frozen with their commands (zero-rescan plan, Run 5 and Run 6).
5. Instrument fix: `tools/gex44_env_preflight.py` judges `pp_install` by commit-hash ancestry of `PP_COMMIT_FLOOR`;
   accept the floor when HEAD contains it OR a commit carrying `(cherry picked from commit <floor>)` OR an equal
   patch-id. Red test first (pick-only history -> READY; unrelated history -> still NOT_READY; mutant dropping the
   hash path -> red). Recorded as the first opportunity row of the programme. The live GEX44 install is never
   updated by hand.

</domain>

<decisions>
## Implementation Decisions

### Locked by the approved plan (vault/plans/autonomous-optimization-2026-10-05.md)
- New pillars live in an IC gen2 ledger (skill-capability/gen2 precedent); gen1 `frozen` object is immutable.
- EXTEND before NEW: no new OS / runtime / DB / scheduler / ratchet.
- Never edit: CE/SC/IC-gen1 ledgers' `frozen` objects, `tools/test_cognitive_economy_program.py`,
  `tools/test_skill_capability_program.py`, root `.planning/STATE.md`. `tools/gsd_mission.py` out of scope.
- Commits: explicit pathspec, one falsifiable increment each; verify `git log -1 --format=%s`.
- Laptop-only work -> one `[<P>]` line in `vault/programs/incremental-cognition/gen2/owner-bundle.md`.
- Every phase commits EVIDENCE.md (Product Delta + Intelligence Delta) and its ledger rows.
- UNKNOWN / INCONCLUSIVE / UNMEASURED are never PASS.

### Claude's Discretion
All other implementation choices: follow repo conventions (skill-capability gen2 ledger shape, IC gen1 ledger,
existing V-gate test style).

</decisions>

<code_context>
## Existing Code Insights

- IC gen1 programme: `vault/programs/incremental-cognition/`, done-gate `tools/test_incremental_cognition_program.py`.
- Gen2 precedent: skill-capability gen2 ledger.
- Champion measurement: `vault/plans/zero-rescan-reality-scan-2026-10-05.md` (Run 5, Run 6).
- Novelty gate: `modules/spec_gate/gate.py::check_novelty_gate`.
- Preflight: `tools/gex44_env_preflight.py`, `PP_COMMIT_FLOOR`.

</code_context>

<specifics>
## Specific Ideas

See ROADMAP operating constraints; they apply to every phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
