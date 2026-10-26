# Backlog — CCR-NEXT A2: laptop close-out, waiting on laptop RAM (2026-10-26)

Source: claude-power-pack coordinator pane b20a82d4. The Owner asked for everything pending to go into the backlog, to be done
as soon as the laptop has RAM (2026-10-26).
Nothing is running. The engineering is finished on GEX44; only laptop-plane steps remain.

## State at entry

- GEX44 mission `m-c51d9474f416` is COMPLETED, 8/8 phases, HEAD `dcd3e930`: 79 files, +3122 lines over base `18c93226`.
  - GEX44 clone: `~/missions/ccr-a2`, branch `worktree-ccr-a2-gsd`.
- Laptop worktree `.claude/worktrees/ccr-next-verify`, branch `ccr/next-gex44`, fast-forwarded to `dcd3e930`. Local only, not pushed.
- Laptop gates already green at `dcd3e930`:
  - `claude plugin test mods\cpp-cognitive-runtime`: 61 pass / 0 fail;
  - `python tools\ccr_estate_gate.py --mod mods\cpp-cognitive-runtime`: PASS, kernel 2970, bound 8000.
- The active CCR release is still `0.1.0-40f2c160`, which carries Phase 1 only.
- Why it stopped: at 2026-10-25 17:40Z the laptop had 742 MB free with 29 claude.exe running.
  - The background-shell memory reaper had already killed a smoke run at 3.3 GB free.
- Source of the step list: `.planning/workstreams/ccr-a2/phases/08-hand-off-knowledge-landing/08-EVIDENCE.md`, "LAPTOP STEPs".

## Start condition

Free RAM must be at least 4 GB on two samples a minute apart. Measure it with `(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory`.

Ways to get there:
- the Owner closes idle panes; or
- the Owner relaunches with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`.

Below the floor, record WAIT_RESOURCE and stop. Do not restart a run the reaper killed.

## To do, in order (all in the ccr-next-verify worktree unless stated)

1. **Type-check `mods/cpp-cognitive-runtime/hooks/register.ts`.** GEX44 had no bun or tsc, so it has never been type-checked. A passing test run is not a compile.
2. **G2: pp-code-reviewer on `18c93226..dcd3e930`.** Scope is `mods/`, `tools/` and `modules/`.
   - The agent is read-only, so the parent writes the report.
   - Do not rebase while it runs (HR-G2-REBASE-RACE).
3. **Release once for Phases 1-7.**
   - Before releasing, read the DEPLOY class: `hardrule_compile.py --class DEPLOY`. HR-2 requires a smoke from the same commit.
   - Run `python tools/ccr_release.py release --impact policy`.
   - Then run a start-receipt smoke. Expect `compatible=true`.
   - Then run a real interactive successor (`/clear` then `/kresume`) whose receipt shows `frontier.basis:"capsule"`.
     - This also closes the Phase 1 smoke, which was INCONCLUSIVE.
     - The driver must wait for the turn to finish before `/exit`. Receipts flush only on turn.complete or session.end.
     - Point `CPP_ROLLOVER_STATE_DIR` at an empty dir so no real capsule is claimed.
   - Rollback: `python tools/ccr_release.py rollback`. Kill switch: `CCR_SUCCESSOR_CANARY=0`.
4. **Run the laptop-data checks.**
   - `python tools/ccr_generation_census.py`. It measures stale CCR per process. Debt at entry: 18/25 stale.
   - `python tools/mission_spend.py goal-status --goal ccr --consumers`. Expect 5cadebe8 to have a share.
   - `python tools/mission_console.py --host gex44=ssh:gex44:/home/kobii/missions/ccr-a2`.
   - Measure whether Windows hot-reloads a swapped `active/` within one prompt, the way 2.1.310/Linux does. This is unmeasured.
5. **Land on the main tree** (`~/.claude/skills/claude-power-pack`).
   - First check `git status` on the target paths: they must be clean. Then cherry-pick with a pathspec:
     - `tools/rollover.py` and `tools/test_rollover_latest.py`;
     - `tools/ccr_generation_census.py` and its test;
     - `tools/mission_console.py` and its test;
     - `modules/provider_routing/ledger.py`;
     - `tools/mission_spend.py`;
     - `tools/gsd_mission.py`;
     - `tools/test_lease_consumers.py`.
   - Run those suites on the main tree. DONE means green there.
   - `tools/gsd_mission.py` has foreign WIP elsewhere: diff it before applying.
   - Check `git log -1` after the commit (COMMIT_EDITMSG race).
6. **Settle goal `ccr-a2` with `--measured`.** The spend covers the GEX44 worker sessions (`0f0e092f`, `ac48369c` and any subagent sids) and this coordinator pane, which is bound to ccr-a2 by its Set-Location.
   - First grep every goal ledger for each sid and subtract the prebind. Never use goal-correct.
   - Take the figure from the transcripts. Do not use an estimate.

## Owner decisions (not laptop work)

- **ctx-rent-obs W3 certification** (OWNER_QUEUE, last entry). Both red drills stayed green (N=2), so the battery's sensitivity is unproven.
  - It needs Owner-funded runs: either raise N or add a capability-dependent task.
  - Hand over `tools/ccr_bench/FREEZE.json` (sha 37133485) and `.planning/workstreams/ccr-a2/phases/05-ab-runs/raw/` only after ctx-rent-obs is approved.

## Never

- Release the held laptop missions `m-ae3b41e68f92`, `m-c60b6defbe97` or `m-b85fa1eacc8c`.
- Touch pane 5cadebe8.
- Install CCR into GEX44's `~/.claude`.
- Push from an ssh body.
