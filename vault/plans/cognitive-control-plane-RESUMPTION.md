# Cognitive Control Plane — RESUMPTION

Read this and continue with zero prior context. Update after every sealed unit.

## 1. Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
shared tree (690+ dirty paths from other panes: commit by explicit pathspec only).
Plan of record: `vault/plans/cognitive-control-plane-2026-10-02.md` (Owner APPROVED 2026-10-02,
six defaults; section 10 = audit fixes, overrides sections 4-6). Incident: `weekly-limit-burn-rca-2026-10-02.md`.
Thesis: close the burn control loop inside EXISTING owners; no new mega-system.

## 2. Sealed
- `19a7bc5` plan + C0: CO-08 scheduler docstrings now say verdict LIVE / enforcement ABSENT.
- `286ccbe` C1: `tools/usage_index.py` (incremental SQLite index at
  `~/.claude/state/usage_index/index.sqlite`, typed burn states, MONITOR_FAILURE) wired into
  `cost_gate`; `weekly_burn` unwired. RCA §13 (P0: subagents do not inherit the parent; the floor
  is set by agent type) and §14 (meter reconciliation FAILS: no weighting of transcript usage
  explains 75 % -> 90 %; GEX44 not the cause; anomaly replay NORMAL throughout).
- `30bdaaa` C1b+C2: index schema v2 (prompts, spawns, subagents, quota tables; one-pass
  ancestry via `tis_observed.calls_from(on_line=)`), `tools/fanout_ledger.py` (quota / summary /
  top / prompt), RCA §15 (>= 2 accounts share the transcript store: H4).
- `9a9ea1f` C3: `scheduler.decide_spawn` (SHADOW ONLY) + `tools/estate_shadow.py replay`.
- `4cb3606` C4.0: `tools/floor_probe.py probe` (attachment-text fit, provider remainder explicit).
- Plan §11 = the approved reconciliation (Owner "y" 2026-10-02). Peer state-centric mission owns
  Goal state / packet / delta (`modules/gsd_x/goal`); CCP feeds it metrology only.
- PRG-1 (fanout_ledger on the real index, window 09-30T17Z..10-02T09:40Z): anchor intact;
  roots HUMAN 11,622 / MISSION 10,473 / CONTINUATION 1,637 / SDK 179 / UNKNOWN 14 calls; 9,893/9,893
  subagent calls linked; HUMAN fan-out median 12, p90 67, max 239 (f319ce75 = 214 parent + 25 sub).
  Two report defects found and fixed: `prompt` tree dropped title/entrypoint (mission prompts read
  HUMAN), and subagent project came from the spawn row's file. Cause of the second:
  `projects/C--Users-User-Apps-mcp-video-analyzer` is a JUNCTION to the PP project dir (148
  sessions indexed twice; totals safe via k-dedup, path-keyed rows alias). 39/240 NOT_INDEXED
  spawns = 32 hook-denied + 7 other errors, 0 with a result. Debt: indexer still walks the junction.
Coherence anchor: `test_usage_index` 22/22, `test_fanout_ledger` 17/17, `test_estate_shadow` 9/9,
`test_floor_probe` 4/4; `python tools/usage_index.py window 2026-09-30T17:00:00Z
2026-10-02T09:40:00Z` = 23,925 calls / 6,230,548,450 cache read (must survive the v2 backfill).

## 3. Active decisions
- The 75 % reading is `suspended` in `vault/config/weekly_meter_readings.json`; the alarm shows
  NO percentage until the Owner answers the meter question (RCA §14 hypotheses 1-3).
- Do not edit `tools/rollover.py`, `context-watchdog.py` (SPEC-ECON-ROLLOVER peer-owned and
  implemented), `tools/gsd_mission.py` (Ralph, peer), `hooks/agent-solo-guard.js` (audit G4).
- Model-calling runs wait for the weekly reset (2026-10-07 17:00Z) unless the Owner says "spend now".
- `loop_budget.py` (CO-09) is a declared-budget library with no spawn-path caller; C3 did not
  build on it (spawns declare nothing). A live C3 hook needs Owner OK (shared dispatcher).
- Provider quota: the Wed-17Z seven-day window is REJECTED 2026-10-02T11:54Z -> 2026-10-07T17:00Z.

- PRG-2 PASS (RCA §16): protected_deferred=0, all 15 would-defers reviewed and explainable.
  Plan §12 approved (Owner "y", six defaults): observation -> governed admission, ten micro-commits.
- Phase-4 audit DONE: `vault/audits/ccp-s12-audit.md`, EXECUTE-WITH-FIXES, injected as plan §12.1.
- Golden incident f319ce75 DONE (RCA §17): depth x context rent, legitimate construction;
  store != workspace != repository proven on real data (io-focus = InfinityOps worktree).

- §12 commit 2 SEALED `f234580`: store identity by resolved path (`_store_dirs`), alias rows
  canonicalized in refresh() (8 columns incl. spawns.parent_k, one BEGIN IMMEDIATE, verified
  backup). Pre-fix an id-less `off|<path>` call was DOUBLE-counted when the alias listed first.
  Live: 3 junctions, 1 with rows, 124 rewritten, alias rows 0, anchor unchanged, backup
  `~/.claude/state/usage_index/index.identity-1790970811.bak` (sha256 re-verified; delete only
  with Owner OK). Gate `test_usage_index_identity` 11/11.
- §12 commit 3 SEALED `6b95854`: `fanout_ledger.project_of` shared; nested spawn project fixed;
  bands guard inside `replay()`. PRG-2 replay identical after migration. `test_estate_shadow` 11/11.

- §13 APPROVED (mega-prompt reconciled; additions c8 receipt, c8b journey, c8c ledger
  independence, 3 extra mutants). OWNERSHIP: the §13 pane holds c4-c8; the s12 pane stepped
  off by message and stays off usage_index / fanout_ledger / estate_shadow / decide_spawn
  until a handoff is posted here.
- §12 commit 4 SEALED `2856f8e`: schema v3 spawn outcomes, live index migrated (spawns-only
  backfill, offsets untouched, anchor unchanged). Window: 201 RETURNED / 39 HOOK_BLOCKED / 0
  other (RCA §16 corrected: the 32/7 split was a scratch-matcher error). Gate
  `test_spawn_outcomes` 23/23. Fixed in passing: connect() would have re-run the v2 full re-read
  on ANY schema bump.

- SEALED (§13 pane): c5 `ff7a61d5` execution shape + transitive root (window: depth/area median
  1.0, max width 2 -> cost is sequential depth); c7 `1db28b93` `tools/root_progress.py` progress
  v1 (19/20 costliest roots ADVANCED); c8 `142146f9` decide_spawn v2 + receipts + replay-v2
  (index schema v4 input_hash): window A REJECT (5 changed verdicts, all on ADVANCED roots),
  window B NO_CHANGE -> v1 stays champion; equivalence rule fired 0 times. c8b `65d31a0`:
  `root_progress.py journey` (819 B real record, goal join via bind_mission; live: no mission
  is goal-bound). Lane split: s14 (S1/S2/S3) belongs to pane claude-power-pack-da.
- S3 handoff SENT 2026-10-03 (input_hash, WOULD_DEFER read path, estate_shadow.py free with
  V-SPV2-NO-WRITE-SQL / LEDGER-UNTOUCHED kept green). Peer S1 landed `2fc1a3c5`
  (`tis_observed.store_dirs`); peer S3 displacement `1e2a9725`: 19/20 v2 defers UNKNOWN, no
  absorption, saving stays an interval [0, 1,399 calls / 349.6M cache read].
- c9 SEALED: `vault/audits/ccp-c9/c9_replica_drill.py` (replica = tools + modules +
  vault/pricing + vault/config, clean control per test first, live SHA asserted) -> 11/11
  KILLED, each by its named gate (`c9_results.json`). Two gate defects found and fixed: the
  BANDS gate crashed instead of failing (caught only ValueError), and V-SPV2-NO-WRITE-SQL missed
  CREATE (only the runtime byte gate killed mutant 9; now both do). tools/mutation_drill.py debt
  stands (no repo-layout replica for a modules/* subject drilled by a tools/* test).
- Async-launch bug FIXED (peer S3 audit, verified: 1,184/1,452 results were the launch ack;
  PRG window 200 of 201 "RETURNED"). No schema change: `fanout_ledger.is_launch_ack` derives
  LAUNCHED / ASYNC_RAN from the stored head; `child_last_call` = completion of an async spawn;
  `Equivalents` ends an ack row there. Gate `test_async_spawns` 12/12, 4 fix-mutants KILLED on
  the replica; review APPROVE (`vault/audits/ccp-c9/async-fix-review.md`). Re-run: PRG 200
  ASYNC_RAN / 1 RETURNED / 39 HOOK_BLOCKED; replay-v2 A REJECT, B NO_CHANGE (unchanged);
  WOULD_REJECT 0 is reachable (27 exact repeats all-time, none overlapping a running twin).
  RCA §16 correction 2 + §18 (c5-c8 facts: depth not width, spend != waste) recorded.
- c10 PARTIAL: UKDL `T-PATH-IDENTITY-IS-NOT-RESOURCE-IDENTITY-001` written (uncommitted until
  hunk-staged: the UKDL tail is a live CEPS auto-append). Still open: peer candidates stay
  candidates; tower receipt entry EXPERIMENTAL.

## 4. Next three actions
1. c10: UKDL trap "path identity is not resource identity" (+ validate peer candidates:
   spawn requested != executed, upper bound reported as savings, raw spend != waste [c8
   REJECT], launch ack != completion); tower entry for the receipt contract EXPERIMENTAL only;
   RCA §18 with c5-c8 facts.
2. Switch `_store_dirs` to `tis_observed.store_dirs` (S1 landed; gate
   test_store_identity_consumers 7/7); tell claude-power-pack-da before that commit.
   Still open: `floor_probe.py probe` rent ranking -> C4.1; re-derivation detector (NEXT).

## 5. Start instruction
`git log --oneline -5 -- tools/usage_index.py`, run the coherence anchor (+ `test_spawn_outcomes`
24/24, `test_spawn_policy_v2` 26/26), read plan §12, §12.1, §13 and `vault/audits/ccp-s12-audit.md`,
then action 1.
