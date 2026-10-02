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

## Results
- S1 SEALED `2fc1a3c5`: 4 ACCOUNTING consumers fixed (tis --all-projects 152 dup files; co_12
  2,275 -> 2,124 sessions, keyed by session id; sovereign_miner 273 dup files; budget_monitor
  programmatic 7 d 1,295 -> 1,245 calls, same moment). Shared `tis_observed.store_dirs`;
  token_ground_truth delegates. SAFE, untouched: cognitive_os.scheduler, token_autopsy, nightly,
  resume_reindex (report-only inflation, rename re-checked). Gate `test_store_identity_consumers` 7/7.
- S2 (a) DONE 2026-10-02, read-only: backup sha256 `167f16fe5dc73f39f9e8a1c931d4e8abd861e99074abe53ff1ab4a4ce904bfb2`,
  111,706,112 B. Backup-only keys after alias mapping: 0 in calls / files / prompts / spawns /
  subagents. Controls: mapping fired on 452 path values (files.path 230, spawns.file 118,
  subagents.file 80, quota.file 18, calls.file 6); mapping OFF -> all 452 red, ON -> 0. Calls with
  changed values: 0. Anchor window identical (23,925 / 6,230,548,450 / 9,893). Source transcript
  missing for 0 of 2,719 files (228,249 calls). Verdict: the backup is strictly dominated by the
  live index plus the transcript store; restoring it could only lose v3/v4 columns and 1,601 calls.
  S2 (b) scratch rebuild NOT RUN: it tests live-index regenerability, not this decision.
  Recommendation: DELETE, on the Owner's typed consent only, re-hashing to the sha256 above
  immediately before the delete and refusing on any mismatch.
- S3 MEASURED 2026-10-03 (scratch, read-only, 0 model calls; code waits for its audit). Handoff
  from 2a: `spawns.input_hash` (schema v4), `replay_v2` receipts, estate_shadow free to edit.
  replay-v2 over the PRG window judged 240 spawns: 20 WOULD_DEFER (v1: 15), 0 WOULD_REJECT.
  Displacement: REUSABLE_RESULT_EXISTED 0, EQUIVALENT_ACTIVE 0, RAN_LATER_EQUIVALENT 1 (child 0
  calls, equivalent ran later), UNKNOWN 19. Parent overlap (child tool inputs re-issued by the
  parent after the spawn) measured 18/20: max 0.111, 11 at 0.0 -> evidence AGAINST absorption.
  Saving claim = interval [0, 1,399 calls / 349,600,836 cache read]; history cannot place the
  work, and it was not duplicate work. Implication for live admission: these defers would delay
  or drop distinct work, not remove waste.

## Not this pane / not now
Horizontal = decide_spawn + estate_shadow (2a). Longitudinal actuator = rollover + context-watchdog
(peer, do not edit); CCP feeds metrology via c5 shape. Fresh-epoch counterfactual needs c5. Progress
producers = c7 (construction) + goal/judge (proof) + goal spine (decision); evidence advancement
RESEARCH. Institutional layer: LATER/RESEARCH/REJECT per §12 lists.
