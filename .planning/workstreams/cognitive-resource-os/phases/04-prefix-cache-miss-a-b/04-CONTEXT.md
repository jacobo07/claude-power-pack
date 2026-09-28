# Phase 4: Prefix cache-miss A/B - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Test the unmeasured hypothesis that a new session misses the previous session's cached prefix because the tool
list varies with MCP. Requirement: CRO-04. Success criteria: see ROADMAP.md Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, operating constraints and codebase conventions to guide decisions.

### Fixed by the roadmap
- This is the only phase allowed to make model calls, and only on this host's subscription quota
  (claudeAiOauth, no API key). `ANTHROPIC_API_KEY` set in the run environment => BLOCKED, no runs.
- Exactly 4 `claude -p` runs: Arm A = 2 back-to-back runs, identical short prompt, one scratch dir;
  Arm B = same with `--strict-mcp-config` and an empty MCP config. Cheapest model the protocol allows. Output discarded.
- First-call `cache_read_input_tokens` / `cache_creation_input_tokens` are read from each run's TRANSCRIPT via
  tis_observed (not from CLI stdout). n=2 per arm is stated as a limit.
- Verdict: SUPPORTED / REFUTED / UNJUDGED (with why).

### Inputs from earlier phases
- Phase 2 (CRO-02 MEASURED): `phases/02-gex44-observed-baseline/by_entrypoint.py` composes tis_observed per
  entrypoint; import-safe after review fix WR-04. GEX44 first-call shared share 30.0 % sdk-cli (n=3) / 46.6 % cli.
- Phase 3 (P3 pre-flight): claude 2.1.283 installed at ~/.local/bin/claude (auto-updates; record version at start
  and end). ~/.claude/rules does not exist on GEX44.
- Phase 1: pytest not installed on this host (do not install); tools/test_*.py gates run on plain python3.

### Run-environment note
Work happens in the isolated worktree `.claude/worktrees/cro-gex44` on branch
`mission/cognitive-resource-os-gex44`. Scratch dirs for the runs must live OUTSIDE ~/.claude config paths and
outside any other mission's directory; never write ~/.claude settings or copy credentials.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — discuss phase skipped. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
