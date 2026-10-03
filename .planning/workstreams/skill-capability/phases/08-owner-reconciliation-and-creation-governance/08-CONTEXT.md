# Phase 8: Owner reconciliation and creation governance - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Five pillars of `vault/programs/skill-capability/ledger.json` (frozen rules verbatim in the ledger):
- **I** lifecycle / retirement / GC -> predicted MERGED_INTO_EXISTING_OWNER: "merged into cognitive-economy pillar T; this
  program hands over its retirement candidates with evidence and deletes nothing". Owners `modules/liveness/reachability.py`,
  `vault/programs/cognitive-economy/ledger.json` (CE pillar T: "institutional GC / simplification", predicted AUTHORIZATION_BOUND).
- **J** creation governance -> IMPLEMENTED_AND_VERIFIED: "a new skill must declare its opportunity detector or why it has
  none; a gate refuses a skill directory without the declaration". Owner `~/.claude/skills/skill-creator/SKILL.md`.
- **K** capability routing + ACV -> MERGED_INTO_EXISTING_OWNER: "routing lives with ACV; this program contributes opportunity
  rows through CO-12 and builds no second router". Owners `vault/specs/agent-capability-virtualization.md`, `modules/capability_runtime/agent_spec.py`.
- **L** CO-12 + Context Compiler -> DEFERRED_STRONGER_OWNER: "the Context Compiler is ABSENT; it is deferred to the
  cognitive-economy program with a handoff; CO-12 is written only through record_signal". Owners `modules/cognitive_os/co_12_telemetry.py`, CE ledger.
- **M** economics / model / goal relativity -> MERGED_INTO_EXISTING_OWNER: "cost figures come from tools/usage_index.py windows;
  this program reports token and turn deltas relative to a named denominator and owns no cost model". Owner `tools/usage_index.py`.

</domain>

<decisions>
## Implementation Decisions

### D-01 Handoffs (I, K, L, M): CE verifier contract, measured
- MERGED / DEFERRED need evidence kinds `owner` (a frozen owner path) AND `handoff`: a file under
  `vault/programs/skill-capability/handoffs/<P>.md` (the wrapper rebinds HANDOFF_DIR, tools/test_skill_capability_program.py:42),
  sha256 LF, text naming `[<P>]` and at least one of the pillar's frozen owner paths, with a commit after the freeze
  (`handoff_landed`). The handoff lives in THIS program's dir; never edit `vault/programs/cognitive-economy/**`
  (another live mission owns it). The owner receives the handoff by reading it; an `[I]`/`[L]` owner-bundle line tells
  the Owner to point the CE mission at it.
- Each handoff carries real content, not a pointer: I = retirement candidates discovered by
  `python3 modules/liveness/reachability.py` (and phase 4's coverage sweep: skills with coverage `none` and no
  invocation in the windows of phase 3), each with its evidence, deleting nothing; K = the CO-12 opportunity rows this
  program produces (tools/skill_opportunity_signals.py) and the statement that no router was built (verify by a sweep:
  no new file under modules/ or tools/ in this program's commits implements routing); L = Context Compiler ABSENT
  (verify absence by a discovered search, report the search command and its zero-hit output as a measured absence with
  its aperture), CO-12 writes only via record_signal (grep this program's commits for any other writer of signals.jsonl);
  M = every token/turn delta this program reported (phases 1-7 evidence files) with its denominator, and the statement
  that no cost model was added.
### D-02 J creation gate (IMPLEMENTED)
- A gate under `tools/` that sweeps skill directories (repo `skills/*`, discovered) and refuses one whose SKILL.md lacks
  an opportunity-detector declaration (frontmatter field, e.g. `opportunity_detector: <path>` or
  `opportunity_detector: none` + `opportunity_detector_reason: <text>`; the planner fixes the exact syntax and checks it
  against how Claude Code parses SKILL.md frontmatter so the field does not break loading). Both poles: an undeclared temp
  skill is refused, a declared one admitted; floor and positive control.
- Existing repo skills: either add the declaration to each (derive it from phase 4's coverage class — CWST -> its card
  ledger detector, others -> none + reason) or have the gate apply only to skills added after a named commit; decide and
  justify (prefer declaring all: a gate that grandfathers everything measures nothing).
- `skill-creator` (the frozen owner) lives at `~/.claude/skills/skill-creator/SKILL.md` on the live tree: never edited
  from gex44. The instruction for skill-creator to emit the field goes to the owner bundle as `[J]`.
### D-03 Closure
- One ledger edit per pillar state line (I, J, K, L, M), frozen asserted equal to the FROZEN_AT copy; each `--pillar <P>`
  PASS; earlier pillars stay PASS. J gets gate argv + prg `evidence/J-creation-gate.md`.

### Claude's Discretion
Plan split (likely 2-3 plans: handoffs I/K/L/M; J gate; ledger closure), handoff layout.

</decisions>

<code_context>
## Existing Code Insights
- `tools/test_cognitive_economy_program.py` handoff rules ~lines 286-296, `handoff_landed` ~148; owners must exist (L1 ~198).
- `tools/skill_opportunity_signals.py` (CO-12 via record_signal), `modules/liveness/reachability.py`, `tools/usage_index.py` (read only).
- Phase 4 coverage sweep (pillar D) output: read phases/04-*/ SUMMARYs and evidence/D-coverage.md.
</code_context>

<specifics>
## Specific Ideas
- Handoff header: `[<P>] -> <owner path>` on the first line, then the evidence table, then "what the owner should do".
</specifics>

<deferred>
## Deferred Ideas
- skill-creator emitting the declaration -> owner bundle `[J]`.
</deferred>
