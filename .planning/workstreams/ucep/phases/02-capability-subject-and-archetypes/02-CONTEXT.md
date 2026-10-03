# Phase 2: Capability subject and archetypes - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

A capability subject (traits + archetypes) resolved from repo reality first, intent second.
Success criteria: `.planning/workstreams/ucep/ROADMAP.md` Phase 2 (items 1-4). Requirement UCEP-02.
Plan of record: `vault/plans/ucep-naked-verb-2026-10-02.md` task S1 (5); audit gaps G4, G16.

</domain>

<decisions>
## Implementation Decisions

### Fixed by the plan of record (not open)
- Owner of "what is this capability, its traits, archetypes" is `modules/capability_runtime` — new
  `archetypes.py`, reusing `_hits` from `applicability.py`; no parallel authority.
- Traits: persistent, multi_actor, bulk, destructive, distributed, external_effect, scheduled, money,
  policy_layers, ui. Archetypes are trait conjunctions. Family and archetype are independent outputs.
- Anti-triggers DEMOTE, they do not veto.
- No archetype from vocabulary alone: an archetype needs a structural repo or intent fact (invariant). Live
  evidence of the defect: a subagent hand-back that builds nothing was injected `persistent_state/B0` because
  it contained the word "schema" (plan of record, line 6).
- Structural traits come from a cache keyed by repo root + cheap fingerprint, computed OFF the prompt path; the
  prompt path only reads it [G4]. Cache miss -> traits UNJUDGED, never absent (absent is not zero).
- Intent-only traits carry fact state EXTRACTED and can yield at most CONDITIONAL, never REQUIRED [G16].
- Test file `tools/test_capability_archetypes.py`: vocabulary-overlap negative control, intent-only control,
  trait transitions (ephemeral->persistent, local->distributed) recompile differently, positive controls per
  archetype.
- Phase 1 delivered `modules/tower/baselines.discover_subjects` (walks nested axes); Phase 4 will add the
  `archetype/<ID>` axis — Phase 2 only defines archetypes in code, it writes no baseline generation.

### Claude's Discretion
Fingerprint inputs, cache location/format (must live outside the repo tree's tracked files or be gitignored,
and tests must use a hermetic HOME), structural detectors per trait, the exact archetype set defined in code
(must include at least the three Phase 4 targets: WORLD_MUTATION/persistent-state, EXTERNAL_EFFECT,
BACKGROUND_JOB), and the fact-state vocabulary — choose from existing `capability_runtime` conventions.

</decisions>

<code_context>
## Existing Code Insights

`modules/capability_runtime/applicability.py` (gates then score, anti-trigger veto, `_hits`),
`modules/capability_runtime/contract.py` (13 contracts; `dependencies`, `risk_class`, `maturity`),
`modules/tower/families.py` (families classified by prompt words only — the D7 defect this phase starts to fix).
Hermetic HOME pattern: `tools/test_family_injection.py:79-84`. Further insight gathered in plan-phase research.

</code_context>

<specifics>
## Operating constraints (from ROADMAP, binding)

- Worktree `.claude/worktrees/ucep`, branch `ucep/mission`. Commit only paths this mission wrote, pathspec-scoped;
  never push to main.
- Windows: git via `& 'C:\Program Files\Git\cmd\git.exe' -C <worktree>`; Python
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` with `PYTHONIOENCODING=utf-8`.
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/`.
- New module declared PLANNED in the liveness registry (`vault/liveness/reachability_registry.json`) with an
  owner-queue line in the SAME commit that creates it; never `reachability.py --baseline`.
- Narrow oracles (the phase's own tests), hermetic HOME, no test row in the production ledger.
- Never ask the Owner mid-run: write blockers to EVIDENCE.md, mark BLOCKED/UNJUDGED, continue.
- Phase ends with `02-EVIDENCE.md`: commands, exit codes, observed output, Production Reality verdict
  (PROVEN / OBSERVED / UNJUDGED / BLOCKED). Nothing in this phase is on a live hook path: expect OBSERVED at most.

</specifics>

<deferred>
## Deferred Ideas

Wiring traits/archetypes into the prompt path is Phase 5-6 (envelope compiler + delivery). Open items carried
from Phase 1 EVIDENCE (14 MOVED citations, `wiki/tools/cbr_probe.py` P4 abort, a suite writing
`gsd-x-heartbeat.json` under the real HOME) are not Phase 2 scope.

</deferred>
