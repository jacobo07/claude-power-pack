# Phase 6: Compile-out lineage - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Pillar G of `vault/programs/skill-capability/ledger.json`: compile-out + lineage. Frozen rule: "a compiled-out card
names the skill and commit it was compiled from, and a gate fails when the source skill changes without the card
being re-derived". Owner: `hooks/doctrine_cards.js`. Predicted IMPLEMENTED_AND_VERIFIED.

</domain>

<decisions>
## Implementation Decisions

### D-01 Population: discovered, two cards today
- Compiled-out cards present in `hooks/`: `doctrine_cards.js` (commit card <- skill `concurrent-writers-shared-tree`,
  text at doctrine_cards.js ~417-428) and `destructive_doctrine_card.js` (<- skill `destructive-state-authorization`,
  card text ~line 61). Discover cards by a marker, not by this list: e.g. a `// COMPILED-FROM:` header, and a sweep
  that finds every hooks/*.js whose card text names a skill (`the \`<skill>\` skill`) and fails if any such file lacks
  the lineage header. Floor: population >= 2; positive control: both known cards found.

### D-02 Lineage field
- Each card carries `skill`, `source path` (repo `skills/<name>/SKILL.md`), `source digest` (sha256 of the LF-normalized
  SKILL.md at derivation time) and `commit` (the commit that last changed that SKILL.md when the card was derived).
  Digest is the identity; the commit is provenance (a commit can stay constant while bytes change in a working tree,
  so the gate compares the digest of the COMMITTED blob, read with git from HEAD or from the working file — decide and
  justify; the CE verifier re-runs the gate on the laptop, where repo `skills/` exists, so reading repo files is fine).
- Re-derivation = a human/agent re-reading the skill and updating the card text + lineage fields together. The gate
  does not generate card text.

### D-03 Gate driven from both poles
- Clean: every card's digest matches its source -> pass. Mutant: a temp copy of a source SKILL.md with one byte changed
  (or the card's recorded digest altered) -> the gate fails naming the card. A card naming a skill that does not exist
  in repo `skills/` -> fail. Drills must not edit the real skill files (copy to a temp root and point the gate at it).
- Editing `hooks/doctrine_cards.js` or `hooks/destructive_doctrine_card.js` must keep their suites green:
  `node hooks/tests/test-doctrine-cards.js`, `node hooks/tests/test-destructive-doctrine-card.js`,
  `python3 tools/test_card_precision.py` (pillar A gate, re-run by the CE verifier), and `--pillar A` stays PASS.
  A header-only comment edit is the least invasive shape.

### D-04 Closure
- `state.G` IMPLEMENTED_AND_VERIFIED: gate argv + prg `vault/programs/skill-capability/evidence/G-lineage.md` (sha256 LF,
  `command:` lines). Ledger edit replaces only the state.G line; frozen asserted equal to the FROZEN_AT copy.
- The live laptop hooks (`~/.claude/hooks/`) are a different plane: one `[G]` owner-bundle line if the live copies
  must be re-synced to carry the header (gex44 never edits ~/.claude).
- `--pillar G` PASS; earlier pillars stay PASS.

### Claude's Discretion
Header syntax, gate file name, whether the gate also checks H's card-vs-source drift output (phase 4) — reuse, do not
duplicate, if phase 4 shipped a card-vs-source check.

</decisions>

<code_context>
## Existing Code Insights
- `hooks/doctrine_cards.js` (window rule, `module.exports` incl. MAX_WINDOW_MS), `hooks/destructive_doctrine_card.js` (SHAPES table).
- Repo skills: `skills/concurrent-writers-shared-tree/SKILL.md`, `skills/destructive-state-authorization/SKILL.md`.
- Phase 4 plans (pillar H) may already add card-vs-source drift detection: read `phases/04-*/04-*-PLAN.md` and SUMMARYs first.
</code_context>

<specifics>
## Specific Ideas
- One shared `tools/` gate for lineage; H's card-vs-source check (if any) and G's gate should be one implementation.
</specifics>

<deferred>
## Deferred Ideas
- Laptop live hook re-sync -> owner bundle `[G]`.
</deferred>
