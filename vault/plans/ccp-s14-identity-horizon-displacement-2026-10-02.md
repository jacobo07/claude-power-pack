# CCP §14 — identity sweep, rollback horizon, displacement (pane claude-power-pack-da)

Status: PROPOSED 2026-10-02 23:3xZ, awaiting one Owner approval. Extends plan of record
`cognitive-control-plane-2026-10-02.md` §12/§12.1/§13; overrides nothing in them.

## Reality (measured this turn)
- HEAD `4685689` on `feature/knowledge-acquisition`, 2 ahead of origin, 723 dirty paths (other panes).
- Prompt premise "HEAD 9fe8ea1, Commit 4 next" is FALSE (CLASE 2, stale repo state): c4 sealed
  `2856f8e` by pane 2a; §13 recorded `52ef7db`. Pane `claude-power-pack-2a` is LIVE/busy and owns
  c5-c10. This pane stays off usage_index / fanout_ledger / estate_shadow / decide_spawn.
- `tools/fanout_ledger.py` shows `M` with an empty content diff (stat/EOL touch 23:16).
- token_ground_truth junction debt CLOSED `4685689` (152/258 duplicate transcripts -> 0).
- Store consumers: 88 files / 190 hits reference the projects store; unclassified.
- Backup `index.identity-1790970811.bak` 111,706,112 B (21:53) predates identity AND v3.
- `usage_index.py --db` exists: a scratch rebuild cannot touch the live index.

## Lanes
- 2a (§13): c5 shape, c6 golden, c7 progress v1, c8 decide_spawn v2 + input hash, c9 mutants, c10 UKDL.
- da (§14): S1 identity-consumer sweep, S2 rollback horizon, S3 displacement (after c8), S4 UKDL seeds
  handed to c10.

## S1 identity-consumer sweep (EXECUTION)
Classify every store consumer ACCOUNTING (sums across files: alias double-counts) vs LOOKUP (one
transcript by id: alias harmless) vs OTHER. One shared primitive `store_dirs()` in
`tools/tis_observed.py` (the reference reader both accounting readers already import); token_ground_truth
switches to it; usage_index's copy is handed to 2a as a one-line follow-up (its lane). Fix only
ACCOUNTING consumers with a measured duplicate; each fix red-first on the mklink /J fixture.
Done: table of all 88 classified; duplicates measured per ACCOUNTING consumer on the live store.

## S2 rollback horizon (EXECUTION, zero model calls)
Close by evidence, not by commit: (a) open the backup read-only, assert every backup call key exists
in the live index after alias canonicalisation (124 rewritten rows mapped) -> backup holds nothing
live lacks; (b) scratch rebuild `--db <scratchpad>` from transcripts, compare anchor 23,925 /
6,230,548,450 / 9,893 and spawn outcomes 201/39 for the PRG window. Gate on host RAM (was 4 % free).
Outcome: recommend delete or keep with reason; deletion only on Owner's typed consent, re-hashing
the file immediately before. Risk: transcripts pruned by cleanupPeriodDays make the live index, not
the store, the record for old rows; (a) covers that.

## S3 displacement accounting C3.5 (PLAN locally; depends on c8 input hash)
Per WOULD_DEFER spawn, evidence-only classes: RAN_LATER_EQUIVALENT (later spawn, same input hash,
same root), PARENT_OVERLAP (PROBABLE: parent's later tool inputs overlap the child's), UNKNOWN
(default). ELIMINATED / CONSUMED never asserted historically. Savings = interval [0, upper bound],
never a point. Home: function in `estate_shadow` via handoff after c8. Done: the 15 PRG-2 defers
classified; "savings" wording removed from replay output.

## Not this pane / not now
Horizontal = decide_spawn + estate_shadow (2a). Longitudinal actuator = rollover + context-watchdog
(peer, do not edit); CCP feeds metrology via c5 shape. Fresh-epoch counterfactual needs c5. Progress
producers = c7 (construction) + goal/judge (proof) + goal spine (decision); evidence advancement
RESEARCH. Institutional layer: LATER/RESEARCH/REJECT per §12 lists.
