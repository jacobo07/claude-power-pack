# Backlog — CCR-NEXT A2: landing the CCR line, everything still open (2026-10-27)

Source: pane b2fe2941. The Owner asked for absolutely everything pending to go into the backlog.
Supersedes the step list of `2026-10-26_ccr-a2-laptop-closeout.md` (steps 1-6 there are done or partly done, below).
Status of every row is as measured on 2026-10-27 ~02:30 local; re-check before acting.

## State at entry

- Main tree `~/.claude/skills/claude-power-pack`, branch `feature/knowledge-acquisition`. Two slices of the CCR line are landed:
  - `d5105caa3`: ledger `lease_contention`/`consumers`, `mission_spend goal-status --consumers`, `gsd_mission` contention hook, rollover `latest` pointer (+2 tests).
  - `ce3c39905`: `ccr_generation_census.py`, `mission_console.py`, `ccr_bench/coordinator.py`, the new `ccr_release.py` (+impact) and their tests.
- The other 112 commits of `ccr/next-gex44` are NOT in HEAD. The merge is resolved and committed on a scratch branch, nothing in the main tree:
  - branch `ccr-land-scratch` = `0409d7ee3` (parents `ce3c39905` + `dcd3e930`); worktree `C:\Users\User\AppData\Local\Temp\ccr-land-scratch`.
  - The worktree is in %TEMP% and may disappear. The commit is in the repo, so recreate it with `git worktree add <path> ccr-land-scratch`.
- GEX44 mission `m-c51d9474f416` COMPLETED, 8/8 phases, HEAD `dcd3e930`. Laptop worktree `.claude/worktrees/ccr-next-verify`, branch `ccr/next-gex44` at `dcd3e930`.
- Active CCR release `0.1.0-c42eb4e7` (re-running `release --impact policy` produced the same id: content-addressed).

## Start condition

Free RAM >= 4 GB on two samples a minute apart: `(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory`.
The mission suites fail below ~3000 MB (`feedback_ccr_v5_landing_and_ram_flaky_suites`), and the harness reaps a background run at low memory
(it killed the regression run on 2026-10-27 and asked that it not be restarted unprompted). Run suites in the foreground, in batches.

## To do, in order

### 1. Finish the regression of the resolved merge (blocks the landing)

Run in the scratch worktree, `python tools/<suite>.py`, foreground. Already green there: the 12 changed suites of block A other than accounting, 17/17 of block B
(which includes accounting once HEAD's version of that test was restored), and 14 of the 17 HEAD suites that ran. `test_gsd_mission_envelope` was red once and is 67/67 in scratch AND main at 3.2 GB free: a RAM flake, closed.

- **Failed, not yet explained (rerun at >= 4 GB, then A/B against the main tree):**
  - `tools/test_gsd_mission_capsule_v2.py`: `MV2_PASS=72/73`, 209 s.
  - `tools/test_gsd_mission_cwd_align.py`: `MCA_PASS=17/18` while its own threshold says 16/16, 120 s.
  - If either also fails in the main tree at HEAD, it is pre-existing: record it in `KNOWN_FALSE_POSITIVES.md`. If it passes in the main tree, the merge broke it: find the hunk (11 in `gsd_mission.py`).
- **Never ran (killed by memory pressure):** `test_gsd_mission_legacy_characterization`, `_owner_hold`, `_owner_pause`, `_protocol`, `_quota_relogin`, `_resources`, `_sleep`, `_surface`,
  and in scratch `test_lease_consumers`, `test_mission_console`, `test_mission_spend`, `test_rollover_latest` (all four green in the main tree).
- Money code: `gsd_mission.py` is the supervisor. DONE for this row means every suite above green in scratch, not "most".

### 2. Land the merge into the main tree

- Compare first: `git diff --name-only HEAD ccr-land-scratch` against `git status --short` in the main tree (1,224 dirty files on 2026-10-27). Any overlap = stop.
- `gsd_mission.py` has foreign WIP risk (memory: HEAD +972 lines vs ccr/v5 +227). Land by merge from the scratch branch, never by `git checkout <ref> -- file`.
- Pathspec commits take a whole file: check the hunk headers; another pane had 161 uncommitted lines in `vault/plans/deferred-backlog.md`.
- After the merge: rerun the 8 main-tree suites (rollover, consumers, goal_lease, mission_spend, autopsy, goal_control, baseline, phase_lease) plus `test_ccr_release`,
  `test_ccr_generation_census`, `test_mission_console`; `git log -1 --format=%s` (COMMIT_EDITMSG race); `python modules/liveness/reachability.py`
  (exit 1 is standing debt on `modules/`; it does not scan `tools/`).
- Afterwards remove the scratch worktree and branch (destructive: needs the Owner's yes, read both first).
- Why it matters: the main tree lacks `mods/cpp-cognitive-runtime`; until this lands, releases can only be built from the `ccr-next-verify` worktree.

Merge resolution (29 hunks, 14 files), kept in commit `0409d7ee3`:
HEAD side kept for `mission_gate.js` (workerRecord/holdDecision refactor), `_judge_pre_plan`, `session_tree_report`, `goal_bound`, `judge_wake`;
branch side kept for `phase_lease` E2 `max_calls`/`calls_base`, `_phase_breaker` calls, `set_envelope` call base + E3 forecast gate + fresh epoch per phase, `--phase-max-calls`;
combined by hand: `gsdx_chain.decide` (HEAD filter + `evidence=`) and its status call; both sides kept for `gsd_epoch` breakeven shadow, `record_attempt`, the independent tests and the UKDL entries.

### 3. Branch defect found by the merge

`tools/test_accounting_authority.py` on `ccr/next-gex44` calls `gsd_mission.derive_estimate_from_roadmap`, which exists in no ref
(on the branch alone the test passes its first gates, then dies with AttributeError). Probable origin: commit `9e48faa03` "repair gsd_mission.py from 15b71b82". The scratch merge kept HEAD's version of the test (10/10).
Decide: restore the function from `15b71b82` or drop the 45 branch test lines. Do not re-add the test without the function.

### 4. Review and type-check gaps

- `mods/cpp-cognitive-runtime/hooks/register.ts` (+66/-5) and `hooks/policy.ts` (+154) in `18c93226..dcd3e930` were NOT G2-reviewed: the reviewer said the range does not touch the mod
  (`mods/cpp-cognitive-runtime/src` does not exist, true; the code is under `hooks/`, which it did not look at). The parent read the `register.ts` diff only. Run `pp-code-reviewer` on those two files.
  The agent has no write tool: the parent persists its report (the agent-solo guard blocks a durable-output clause).
- No faithful `tsc`: the host SDK types (`.claude-plugin/types/tsconfig.json`, module `claude-code`) are absent, and `npx tsc` dies inside npm 11.12.1 on node 24 (`Class extends value undefined`).
  The partial check (bun-installed TypeScript 5.6.3 + a stub of `claude-code`) showed only stub-shaped errors at `register.ts` 258, 290, 500, 501, 504. Run `claude plugin test mods\cpp-cognitive-runtime` (61/0 at `dcd3e930` per the old closeout) after landing.

### 5. Verify the release (HR-2 asks a smoke from the same commit)

Read the DEPLOY class first: `python tools/hardrule_compile.py --class DEPLOY`. Not done for the re-run release.
- Start-receipt smoke: expect `compatible=true`.
- A real interactive successor (`/clear` then `/kresume`) whose receipt shows `frontier.basis:"capsule"`. The driver must wait for `turn.complete` before `/exit`
  (receipts flush only then). Point `CPP_ROLLOVER_STATE_DIR` at an empty dir so no real capsule is claimed. Closes the Phase 1 smoke, still INCONCLUSIVE.
- Measure whether Windows hot-reloads a swapped `active/` within one prompt, as 2.1.310/Linux does. Unmeasured.
- Rollback: `python tools/ccr_release.py rollback`. Kill switch: `CCR_SUCCESSOR_CANARY=0`.
- Census debt: `python tools/ccr_generation_census.py` on 2026-10-27 listed processes on `0.1.0-40f2c160` and `0.1.0-f79e3c46` marked STALE against `c42eb4e7`
  (a pane keeps the mod it launched with). Re-run it after panes restart and record the stale ratio.

### 6. Accounting

- `ccr-a2` (lease L1): settled 60,561,329, open 819,265, remaining 19,619,406 of 81,000,000. Settled this session with `--measured` from the GEX44 transcripts:
  `0f0e092f` 5,235,434 and `ac48369c` 36,157,067. Pane `3a4befdd` detached: 9,261,214 booked, tombstoned.
- **Check the undercount risk:** those two figures came from `session_tokens` (the main transcript). If the GEX44 workers spawned subagents, the tree figure
  (`session_tree_tokens`, `subagents/agent-*.jsonl`) is higher. Measure on GEX44 and book the difference with a `--measured` delta; grep every goal ledger for the sid first
  (`feedback_settle_check_every_goal_and_prebind`).
- The 819,265 `open` on `ccr-a2` is a reservation nobody has identified. Find the sid; if it is stranded, release it (a 0 booking, never a measured one).
- Goal `ccr` (lease L32): remaining 24,824,693, used 45,347,596. `5cadebe8` has 48.9% share (21,327,730), not live: the handoff's expectation holds. Pane `5cadebe8` is not to be touched.
- Close `ccr-a2` only when rows 1-5 are done.

### 7. Housekeeping outside this landing

- `.claude/worktrees/ccr-next-verify` is dirty and none of it is from this work: ` M .pp-capabilities`, `?? mods/cpp-cognitive-runtime/.claude/`,
  `?? vault/programs/ccr/compat/probe-results.unconfirmed-ce7e3c76aaa9.json`. Decide per file; do not sweep into a landing commit.
- `.planning/workstreams/ccr-a2/phases/08-hand-off-knowledge-landing/08-EVIDENCE.md` step 4 lists census/console as landable alone: false. Correct it with the dependency closure
  (`ccr_release.py`, `ccr_bench/coordinator.py`).
- Compound Learnings is STUCK for this project: 21 pending files, `/cpp-compound` auto-prompted 15 times without the cursor advancing (Step 7 partial-fails; see `project_compound_loop_sticks_at_steps_7_and_8`).
  Close with `steps78.py` or delete `LEARNINGS_PENDING.md` after reading it.
- Lessons from this session to record (UKDL or `KNOWN_FALSE_POSITIVES.md`):
  - A reviewer's claim of absence ("the range does not touch X") needs the instrument check; here it was false.
  - A handoff file list is a hypothesis: census and console fail to import without `ccr_release._alive` and `ccr_bench`.
  - `git diff | Set-Content` in PowerShell 5.1 corrupts a patch (BOM, CRLF): use `git diff --output=<file>`.
  - `git` is not on PowerShell's PATH: `& 'C:\Program Files\Git\cmd\git.exe'`; bare `git` falls back to Bash and the bridge guard blocks it.
  - The concurrent-writers hook blocks a pathspec commit even for hunks the session wrote through `git apply`/`git checkout`; the documented answer is to re-issue the same commit.

## Owner decisions (not laptop work)

- **ctx-rent-obs W3 certification** (OWNER_QUEUE, last entry): both red drills stayed green (N=2), so the battery's sensitivity is unproven. It needs Owner-funded runs
  (raise N or add a capability-dependent task). Hand over `tools/ccr_bench/FREEZE.json` (sha 37133485) and `.planning/workstreams/ccr-a2/phases/05-ab-runs/raw/` only after ctx-rent-obs is approved.
- Whether the scratch merge may land at all once row 1 is green (it brings the phase lease, `mission_supersede`, UEK and the live hook `hooks/lib/mission_gate.js` into the main tree).

## Never

- Release the held laptop missions `m-ae3b41e68f92`, `m-c60b6defbe97` or `m-b85fa1eacc8c`.
- Touch pane `5cadebe8`.
- Install CCR into GEX44's `~/.claude`.
- Push from an ssh body.
- Restart a background run the memory reaper killed, without being asked.
