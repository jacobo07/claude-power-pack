# Phase 2: Listing floor - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44 (no claim here is a gex44 listing measurement; every figure below is a laptop fresh-session reading already committed)
**Governing spec:** vault/plans/skill-capability-program-2026-10-03.md

<domain>
## Phase Boundary

Pillar B of `vault/programs/skill-capability/ledger.json`: listing floor + plugin gateway + economics. Frozen rule
(immutable): listing hiding was falsified twice (C6, K4) against D-LISTING; a third hypothesis closes this pillar
only with its own measurement against D-LISTING recording the command; a lower floor claimed without a
fresh-session measurement is refused. Predicted terminal: FALSIFIED_OR_REJECTED_BY_EVIDENCE.

</domain>

<decisions>
## Implementation Decisions

### D-01 Terminal: FALSIFIED_OR_REJECTED_BY_EVIDENCE on the two committed measurements
- C6 (`d9072185`, laptop, fresh session a5df8940 vs bfe97833): 134 name-only overrides -> initial listing
  29,991 -> 30,002 chars (cap still binds). Source: `vault/plans/skill-residency-program-2026-10-03.md` C6 line.
- K4 (`4d1cfb83`, laptop, `wiki/tools/listing_floor_probe.results.jsonl` rows `champion-startup` /
  `challenger-startup`): 133 pageable skills behind a gateway -> listing 30,000 -> 29,795 chars, startup tokens
  87,739 -> 89,844 (n=1 per arm), described plugin entries 22 -> 50 (plugin refill). Commands are recorded in the
  probe's docstring (`python listing_floor_probe.py --label ... --settings-file ... --prompt ...`).
- These are the D-LISTING denominator itself; the phase re-derives the verdict from the committed jsonl with a
  script (no hand-copied numbers) and writes a measurement file that names `D-LISTING` and carries `command:` lines.

### D-02 No third hypothesis is measured in this run
- The recorded next hypothesis (k-slice plan line 109: a gateway that also pages PLUGIN skills, sized so full
  latent demand < cap) needs Owner approval and fresh laptop sessions (listing family: 8 of 12 left, D-SESSIONS).
  GEX44 is a different install: a GEX44 fresh-session listing says nothing about the laptop's floor and is not run.
- It goes to `vault/programs/skill-capability/owner-bundle.md` as one `[B]` line with its bound: at most ~9k tokens
  of listing, minus ~4k tokens per gateway read (k-slice plan figures) -> an UPPER BOUND, never a realized saving.

### D-03 Economics
- Savings entry: `upper_bound`, displacement `unknown`, denominator `D-LISTING`; the realized saving from the two
  attempts is negative or nil (K4 startup +2,105 tokens, inside the stated +-1.5k noise only partly) and is reported
  as measured, not as a saving.

### D-04 Gate
- A small python verdict script under `tools/` reads `wiki/tools/listing_floor_probe.results.jsonl`, recomputes the
  champion/challenger deltas, and exits 0 only when the falsification holds (challenger listing chars not
  meaningfully below the cap AND startup tokens not below champion); driven red on a mutated copy of the jsonl
  (a fabricated lower floor must flip it). Not required by the terminal's evidence kinds, but it keeps the
  measurement executable (documented-capability-must-be-executable).
- `python3 tools/test_skill_capability_program.py --pillar B` must print PASS.

### Claude's Discretion
Script and file names, measurement file layout.

</decisions>

<code_context>
## Existing Code Insights
- `wiki/tools/listing_floor_probe.results.jsonl` (4 rows: R2R1, R3, champion-startup, challenger-startup;
  `listing` is a python-repr string `{'chars': N, 'entries': N, 'described': N}`, not JSON).
- FALSIFIED needs evidence kind `measurement` (file under repo, sha256 LF, names a frozen denominator, has `command:`).
  L6 does not apply (predicted is FALSIFIED). Frozen owners: wiki/tools/{listing_floor_probe,capability_directory_experiment,skill_listing_visibility}.py.
</code_context>

<specifics>
## Specific Ideas
- Measurement file: `vault/programs/skill-capability/evidence/B-listing-floor.md`.
</specifics>

<deferred>
## Deferred Ideas
- Plugin-paging gateway hypothesis (laptop, Owner, fresh sessions) -> owner bundle `[B]`.
</deferred>
