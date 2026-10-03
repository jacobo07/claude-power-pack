# Phase 5: Representation operations - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44 (D-LISTING is a laptop fresh-session denominator; no gex44 session produces a D-LISTING reading)
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Pillar F of `vault/programs/skill-capability/ledger.json`: disclosure / fission / fusion / inline / dedup.
Frozen rule: "each representation operation applied to a skill carries a before/after listing measurement against
D-LISTING and a recall check; dedup decisions come from a content-hash sweep".
Owners: `vault/plans/skill-virtualization-k-slice-2026-10-03.md`, `modules/skill_router/skill_index.py`.
Predicted IMPLEMENTED_AND_VERIFIED. CE L6 (tools/test_cognitive_economy_program.py:237-242): a pre-registered
IMPLEMENT that ends with any other terminal needs a `falsification` evidence file naming `[F]`.

</domain>

<decisions>
## Implementation Decisions

### D-01 What can be honestly implemented on gex44
- Applying an operation needs a before/after D-LISTING, i.e. fresh LAPTOP sessions (D-SESSIONS: listing family
  8 of 12 left), and B just FALSIFIED listing hiding twice (C6, K4: the 30,000-char cap binds and refills). So this
  run applies ZERO operations. Each operation that is evidence-backed goes to the owner bundle as one `[F]` line
  with its predicted effect as an UPPER BOUND, never a realized saving.
- What IS implementable and checkable here:
  1. **Dedup content-hash sweep**: discovered (never listed) over repo `skills/*/` and the host's live
     `~/.claude/skills/*` (gex44: 186 entries), whole-directory content hash plus SKILL.md body hash with
     frontmatter stripped; output candidate groups (identical body under different names; repo vs live
     duplicates are drift, pillar H, not dedup — keep them apart). Record the gex44 reading in a committed JSON
     (plane `gex44`), as phase 3 did for window G; the gate argv reads only committed files (the CE verifier
     re-runs it on the Windows laptop at `--final`).
  2. **Operation ledger + gate**: a committed operations file (e.g. `vault/programs/skill-capability/f-operations.json`)
     where each applied operation must carry `{op, skill, before:{D-LISTING ref, command}, after:{...}, recall:{n,...}}`.
     The gate refuses an entry missing either measurement or the recall check, refuses an `op` outside
     {disclosure, fission, fusion, inline, dedup}, and refuses a dedup entry whose group is not in the sweep output.
     With zero applied entries the gate must still prove it can fail: drills with fabricated entries (missing
     after, missing recall, dedup not in sweep) must each go red by their own clause; positive control: a fully
     formed fabricated entry passes.
- Recommended terminal: IMPLEMENTED_AND_VERIFIED on (sweep + operation gate), with the reason stating 0
  operations applied on gex44 and why. If the planner judges that implementing a refusal gate without any applied
  operation does not satisfy the frozen rule, the alternative is AUTHORIZATION_BOUND with an `owner_decision`
  file plus the L6 `falsification` file naming `[F]` — the planner decides and justifies; no third option.

### D-02 Reuse owners
- `modules/skill_router/skill_index.py` already walks `~/.claude/skills/<name>/SKILL.md` frontmatter: reuse its
  walk if it fits (read only head bytes is its contract — the sweep needs whole files, so a separate pass is
  likely; justify). New code goes under `tools/`, not `modules/` (Liveness Standard; phase 1 precedent).

### D-03 Closure
- `state.F` with gate argv + prg `vault/programs/skill-capability/evidence/F-representation.md` (sha256 LF,
  `command:` lines, plane-labelled figures); `[F]` owner-bundle line(s); `--pillar F` PASS; earlier pillars stay PASS.
- Ledger edit replaces only the state.F line; assert `frozen` equals the FROZEN_AT copy.

### Claude's Discretion
File names, hash scheme details, how candidate groups are ranked.

</decisions>

<code_context>
## Existing Code Insights
- `modules/skill_router/skill_index.py` (frontmatter head-byte walk, 1 h cached index at ~/.claude/state/skill-index.json).
- `vault/plans/skill-virtualization-k-slice-2026-10-03.md` (K-slice: K4 gateway falsified; next hypothesis line ~109).
- Gate style to copy: `tools/test_listing_floor_verdict.py` (phase 2, incl. review fixes in 4ddd8846: verdict depends on
  every provenance clause, zero/absent is UNMEASURED, integer arithmetic) and the phase 3 gate.
</code_context>

<specifics>
## Specific Ideas
- Report per candidate group: names, plane, body hash, size, and whether the members are listed (described /
  name-only) in the last committed listing probe row — that is the predicted listing effect, an upper bound.
</specifics>

<deferred>
## Deferred Ideas
- Applying any operation (needs laptop fresh sessions + Owner) -> owner bundle `[F]`.
</deferred>
