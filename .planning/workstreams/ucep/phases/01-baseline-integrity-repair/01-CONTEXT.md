# Phase 1: Baseline integrity repair - Context

**Gathered:** 2026-10-02
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

The baseline chain is green and the known ratchet/gate escape routes are closed before any new authority is built.
Success criteria: `.planning/workstreams/ucep/ROADMAP.md` Phase 1 (items 1-5). Requirement UCEP-01.

</domain>

<decisions>
## Implementation Decisions

### Fixed by the plan of record (not open)
- Re-anchoring is a NEW ratchet operation `ratchet.reanchor(family, {id: new_origin}, reason, authority)`: ONE
  generation per family, `changes[id].kind="REANCHORED"`, ids kept, refused unless the new origin
  `verify_origin == VERIFIED` [audit G1]. revert+promote cannot do it (`promote` builds `existing` from all entries
  incl. reverted, `ratchet.py:169`; `revert` is one id per call).
- The 9 QUOTE_MISSING origins point at `~/.claude/rules/{destructive-state-authorization,monetary-quantity-integrity,
  develop-here-prove-there}.md`, now stubs; re-anchor to PP `skills/<name>/SKILL.md` (or revert with a reason if the
  rule text is gone). Output: `vault/tower/baselines/persistent_state/B1.json`, `wii_homebrew/B1.json`.
- `ratchet.diff` must cover `why`, `origin`, `class`, `propagation_scope`; an unanchored child is not ok; authority
  comes from an allowlist. Probe attacks H1/H2/H3b (`wiki/syntheses/cbr-gap-analysis.md`) go red, controls green.
- Donegate: N/A needs a reason from a closed vocabulary and an N/A-share cap; `test:` checks are NEVER executed on a
  hook path and report UNJUDGED, counted separately from VIOLATED [G13]. Probes H5/H6 no longer pass.
- `test_tower_ratchet.py` (`:237`) and `test_baseline_generations.py` (`:202`) discover subjects by walking
  `BASELINES_DIR` incl. nested axes, with a population floor — no hardcoded family tuple [G9].
- B0 and web_surface B1 bytes are immutable: record sha256 before/after.

### Claude's Discretion
Exact closed N/A vocabulary, cap value, allowlist location and shape — choose from existing code conventions.

</decisions>

<code_context>
## Existing Code Insights

`modules/tower/{ratchet,baselines,donegate,checks}.py`; tests `tools/test_baseline_generations.py`,
`tools/test_tower_ratchet.py`, `tools/test_tower_donegate.py`, `tools/test_family_baselines.py`.
Hermetic HOME pattern: `tools/test_family_injection.py:79-84`. Further insight gathered in plan-phase research.

</code_context>

<specifics>
## Operating constraints (from ROADMAP, binding)

- Work happens in worktree `.claude/worktrees/ucep`, branch `ucep/mission` (based on `581371d`,
  `feature/knowledge-acquisition`). Commit only paths this mission wrote; never push to main.
- Windows: git via `& 'C:\Program Files\Git\cmd\git.exe' -C <worktree>`; Python
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` with `PYTHONIOENCODING=utf-8`.
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/`.
- New modules declared PLANNED in the liveness registry in the same commit; never `reachability.py --baseline`.
- Narrow oracles (the phase's own tests), hermetic HOME, no test row in the production ledger.
- Never ask the Owner mid-run: write blockers to EVIDENCE.md, mark BLOCKED/UNJUDGED, continue.
- Phase ends with `01-EVIDENCE.md`: commands, exit codes, observed output, Production Reality verdict
  (PROVEN / OBSERVED / UNJUDGED / BLOCKED).

</specifics>

<deferred>
## Deferred Ideas

`cli.py` delivered-sentence fix (plan task 4) is true only after Phase 6.

</deferred>
