---
phase: 02-persistent-failures-and-remote-integrity
plan: 04
subsystem: remote-env-integrity
tags: [pillar-B, pillar-C, IC-B, IC-C, deploy, env-preflight, owner-bundle, evidence, mutation-drill]
requires: ["02-01", "02-02", "02-03"]
provides:
  - "tools/gex44_env_deploy.py: plan_deploy, apply_deploy, main (--env-root, --source-repo, --commit, --apply, --json); exit codes 0/3/4/5/6/7/8; backup namespace refs/pp-deploy/backup-<ts>, env.sh.bak-<ts>, pp.head.bak-<ts>, pp-deploy.log; env line export CPP_MISSION_PLANE=gex44"
  - "tools/test_gex44_env_deploy.py: 16 V-DEPLOY-* gates against real-history scratch envs plus --drill (6 mutants)"
  - "gex44_env_preflight.PP_COMMIT_FLOOR raised to the 02-03 commit; PP_REQUIRED_FILES gains tools/mission_launch_gate.py"
  - "evidence/C.md, evidence/B.md, evidence/B-deploy-dryrun-gex44.json; owner-bundle [C] x1 and [B] x6 lines"
affects: []
tech-stack:
  added: []
  patterns: ["plan -> refuse -> back up -> act -> read back, re-planned under the lock", "dry-run default, the CLI cannot mutate without --apply", "refusal is a field of the plan, never an exception"]
key-files:
  created: [tools/gex44_env_deploy.py, tools/test_gex44_env_deploy.py, vault/programs/incremental-cognition/evidence/C.md, vault/programs/incremental-cognition/evidence/B.md, vault/programs/incremental-cognition/evidence/B-deploy-dryrun-gex44.json]
  modified: [tools/gex44_env_preflight.py, vault/programs/incremental-cognition/owner-bundle.md]
decisions:
  - "Hook scripts are restored by the deploy itself, only registered-but-missing ones, only into the env's own hooks dir, never overwriting: tools/install_global_core.py does not copy hooks (it prints cp lines), so the plan's premise was false"
  - "A dirty install (exit 4) and a non-ancestor env head (exit 5) are refusals reported as results; the real a5 (1024 modified files) and a7 (1 modified file) both refuse and nothing is resolved by the executor"
  - "ledger state.B / state.C are not written and IC-B / IC-C are not ticked: both terminals are Owner-run PRGs"
status: complete
commits: 3
plan_head_before: 60a1edb7b15b0bbed92d8f0252185aaec1fca340
actuals:
  tokens: 23400
  tasks: 3
  commits: 3
metrics:
  duration: "about 1h (start time not recorded; estimated from file mtimes)"
  completed: 2026-10-03
requirements: [IC-B, IC-C]
---

# Phase 2 Plan 04: One repeatable git deploy for stale GEX44 envs; C/B evidence and the Owner bundle Summary

A stale env's PP install is now moved to a target commit by one locked, backed-up, re-planned git deploy that refuses every destructive surprise (dirty install, env HEAD not an ancestor, held sweep lock, non-env directory, the user's own HOME), proven on scratch envs cloned from real history at a7's measured head `01199995`; the read-only dry-run on the real a5 and a7 both refuse (exit 4, modified installs) and that is recorded as the result, with every Owner action as an exact command in the bundle.

**Commits:** `562ff3d29d07739f5101488ab01bc755f0dc6450` (tracer), `37a8b5187985500fd82e73be8baeab6dd6bde673` (apply path), `f6a40285c02b0282536f06d78b556df5c74e0bc3` (evidence + owner bundle). `PP_COMMIT_FLOOR` is `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`.

## What was done

- **Task 1 (tracer):** raised the preflight floor to the 02-03 commit and added `tools/mission_launch_gate.py` to the required files (`ENVPF_PASS=55/55`, `V-ENVPF-PP-REAL-READY` and `V-ENVPF-PP-STALE-REAL` still PASS), then built `plan_deploy` and a dry-run-only CLI. The dry-run reproduces the measured a7 staleness (`pp_install_stale` + `hooks_broken`) on real history and a fingerprint (file hashes, ref list, every non-.git path with size) proves it wrote nothing, with a positive control showing the fingerprint can see a created file and a new ref.
- **Task 2:** `apply_deploy`: non-blocking `flock` on the env's own `sweep.lock`, re-plan under the lock, `git fetch` from the source repo, backup ref, detached checkout, `pp.head` and `env.sh` backed up then rewritten atomically, hooks repair only when measured `hooks_broken`, final preflight, one `pp-deploy.log` JSON line, exit 0 only when neither `pp_install_stale` nor `hooks_broken` remains. `--drill` 6/6.
- **Task 3:** read-only dry-run on the real a5 and a7, `C.md`, `B.md`, `B-deploy-dryrun-gex44.json`, owner-bundle lines, runs-as-written proof, final regression, one pathspec commit.

## RED output, verbatim

Task 1, before `tools/gex44_env_deploy.py` existed:

```
Traceback (most recent call last):
  File ".../tools/test_gex44_env_deploy.py", line 31, in <module>
    import gex44_env_deploy as dep  # noqa: E402
ModuleNotFoundError: No module named 'gex44_env_deploy'
```

Task 2, with the Task 1 gates green and the apply gates added but no apply path (the harness also showed `usage: ... error: unrecognized arguments: --apply`; the first run crashed on the argparse `SystemExit`, so `guarded` was changed to catch it before this run):

```
PASS V-DEPLOY-DRYRUN-PLAN / -DRYRUN-NO-MUTATION / -NOT-ENV-ROOT / -REFUSES-HOME
FAIL V-DEPLOY-APPLY: AttributeError: module 'gex44_env_deploy' has no attribute 'apply_deploy'
FAIL V-DEPLOY-IDEMPOTENT / -DIRTY-REFUSED / -NOT-ANCESTOR-REFUSED / -LOCK-HELD / -REPLAN-UNDER-LOCK: same AttributeError
FAIL V-DEPLOY-CREDENTIALS-UNTOUCHED: SystemExit: 2
FAIL V-DEPLOY-CLI-EXIT: {'dirty': 2, 'ancestry': 2, 'lock': 2}
FAIL V-DEPLOY-CLI-APPLY: rc=2 head_ok=False last='' rollback_lines=0
PASS V-DEPLOY-NO-SHELL-NO-CREDENTIALS-NAME / -SOURCE-UNTOUCHED / -REAL-UNTOUCHED
DEPLOY_PASS=7/16  threshold=16/16
```

## GREEN, drills and regression (observed in this run)

```
python3 tools/test_gex44_env_deploy.py           DEPLOY_PASS=16/16  threshold=16/16
python3 tools/test_gex44_env_deploy.py --drill   DRILL killed=6/6  (control 16/16 before and after)
python3 tools/test_gex44_env_preflight.py        ENVPF_PASS=55/55      --drill DRILL killed=6/6
python3 tools/test_mission_launch_gate.py        LG_PASS=19/19         --drill DRILL killed=6/6
python3 tools/test_persistent_failure_park.py    PFP_PASS=24/24        --drill DRILL killed=5/5
python3 tools/test_provider_breaker.py           BREAKER_PASS=18/18
python3 tools/test_gsd_mission.py                MC_PASS=212/213  (only V-MC-PLAN-FACTS-REFUSES-OVERLAP, node v18.19.1; same as the 02-03 baseline)
python3 tools/test_gsd_epoch.py                  EPOCH_PASS=82/82
python3 tools/test_gsd_mission_cwd_align.py      MCA_PASS=16/16
```

Drill lines show each mutant killed for its own reason (M1 dirty skipped `code=0`; M2 ancestry skipped moved the install BACKWARDS, `code=7 head=01199995`; M3 dry-run also applies `changed=['git_head','tree']`; M4 no backup `FileNotFoundError ...pp.head.bak-`; M5 lock ignored `code=0`; M6 pre-lock plan `apply_old_head=01199995 moved_to=e5280349`). `grep -c "shell=True"` -> 0; `grep -c '\.credentials\.json' tools/gex44_env_deploy.py` -> 0; `git diff --stat 34d08aa9 -- vault/programs/incremental-cognition/ledger.json` prints nothing; `--pillar B` and `--pillar C` print `CEP_PILLAR_B=FAIL` / `CEP_PILLAR_C=FAIL` "no terminal disposition" (expected).

## Real-env dry-run (read-only, never --apply)

| env | exit | result |
|-----|------|--------|
| a7 | 4 | REFUSED: 1 modified tracked file `vault/terminal_slots.json` (+21 lines); env head 01199995 is an ancestor of the target |
| a5 | 4 | REFUSED: 1024 modified tracked files (about 981 line-ending-only, 43 real, +20463/-444: `a5_linux.patch` is the candidate); env head 192390b9 is an ancestor |

A refusal is a result: the decision about what to discard belongs to the Owner and is routed through the bundle. `stat` of the 9 env files before/after the dry-runs and the verbatim bundle commands: `diff` printed nothing (details and a disclosure below).

## Runs-as-written proof (from cwd /tmp, extracted verbatim from the bundle)

```
[1] rc=1 missing_file_msgs=0 :: python3 IC/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env
[2] rc=4 missing_file_msgs=0 :: python3 IC/tools/gex44_env_deploy.py --env-root /home/kobii/a7-env --source-repo IC --commit mission/incremental-cognition-run
[3] rc=4 missing_file_msgs=0 :: python3 IC/tools/gex44_env_deploy.py --env-root /home/kobii/a5-env --source-repo IC --commit mission/incremental-cognition-run
[4] rc=1 missing_file_msgs=0 :: python3 IC/tools/gex44_env_preflight.py --env-root /home/kobii/a5-env
[5] rc=1 missing_file_msgs=0 :: python3 IC/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env --json
```

(`IC` abbreviates `/home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run`.) Preflight exit 1 is NOT_READY, deploy exit 4 is the dirty-install refusal; none reported a missing file. Bundle counts: `[B]` lines 6, `[C]` lines 1, `DEBT, shrink-only` 1, ic-run tool-path lines 8, angle-bracket slots 0, removed lines vs `34d08aa9` 0.

## Deviations from Plan

**1. [Rule 1 - plan premise false] `tools/install_global_core.py` does not copy hook scripts.** The plan's interface note says apply mode copies `pp_original` hooks into `<home>/.claude/hooks`. The code at this HEAD says "HOOKS are intentionally NOT installer-shipped" and prints `cp` lines for the Owner (confirmed by running it against a scratch HOME: it installed commands, agents and the session-safety contract, hooks directory absent). With the installer alone the plan's APPLY behavior (`learning-sentinel.js` exists afterward) is unreachable. Fix kept inside the plan's intent: the deploy still calls the existing installer (not a fork) when hooks are measured broken, and then restores only the registered-but-missing hook scripts from the install's own tracked `hooks/` directory, only into this env's own `<home>/.claude/hooks`, never overwriting, never into another env's tree (a7's hooks resolve into a5's). Recorded in the bundle's decisions line so the Owner can choose to change the installer instead. Files: `tools/gex44_env_deploy.py` (`_restore_hook_scripts`). Commit `37a8b518`.

**2. [Rule 1 - test shape] `V-DEPLOY-DRYRUN-NO-MUTATION` calls `main` in-process,** because mutant M3 can only be applied in-process; the CLI-as-subprocess path is still covered by `V-DEPLOY-DRYRUN-PLAN`, `V-DEPLOY-REFUSES-HOME` and `V-DEPLOY-CLI-*`. Extra gates beyond the plan: `V-DEPLOY-CLI-APPLY`, `V-DEPLOY-NO-SHELL-NO-CREDENTIALS-NAME`, a positive control inside the no-mutation gate, a shim-`git` control inside `V-DEPLOY-REFUSES-HOME`, and a standalone-history scratch env so the apply gate really exercises `git fetch`.

**3. [Orchestrator note vs measurement] The a5/a7 ENV nodes are v24.15.0 (inside `^22.23.2 || ^24.14.0`),** not v18.19.1; only the GEX44 main node is v18.19.1. So the real env preflight does NOT yield `interpreter_unsupported` for a5/a7 (their `interpreters` check is UNMEASURABLE today because the old installs have no `vendor/genesis-suite/package.json`, and is expected to read READY after a deploy). The node-upgrade `[B]` line is kept (Owner action, never bypassed) with this scope stated, and I did not repeat the plan's claim that the upgrade also clears `V-G23-*` (those are card-byte reds, not node ones).

**4. [Commit granularity / attribution] Three commits, one per task** (the orchestrator asked for per-task commits; the plan's Task 3 pathspec also lists the earlier files, harmless). The trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` per the session attribution instruction, not the plan's literal Opus text. Commits are on `mission/incremental-cognition-run`, not an `agent-*` branch (as in 02-03); the protected-branch check passed.

**5. [Disclosure - my own slip, no harm found] I touched a5's `.git/index` stat cache.** The first no-write proof failed: a5's install `.git/index` mtime moved (1790281507 -> 1791053631). The cause was an ad-hoc `git --no-optional-locks diff --stat` / `diff -w` I ran in a5's install to describe the 1024 modified files, not the deploy (the move is after the a5 dry-run ended, no cron sweep fired between, and a fresh bracket around only the dry-runs shows no change). It refreshed git's stat cache only; no tracked content, ref or HEAD changed. I redid the proof with a fresh `.before` and no ad-hoc git inside either env between the stats; that second proof is the one recorded (`diff` empty). Also recorded in `B.md` and `B-deploy-dryrun-gex44.json`.

Otherwise the plan executed as written. No auth gates. No architectural changes. HARD BOUNDARY respected: `--apply` ran only against scratch envs under a tempfile root; the real `~/.claude`, `~/a5-env`, `~/a7-env` were only dry-run and read (`V-DEPLOY-REAL-UNTOUCHED` PASS), no re-login, no node upgrade.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-02-04-01..08 are pinned by `V-DEPLOY-DIRTY-REFUSED`/M1, `V-DEPLOY-NOT-ANCESTOR-REFUSED`/M2, `V-DEPLOY-LOCK-HELD`/M5 and `V-DEPLOY-REPLAN-UNDER-LOCK`/M6, the backup artifacts checked by `V-DEPLOY-APPLY`/M4, `V-DEPLOY-REFUSES-HOME` + `V-DEPLOY-REAL-UNTOUCHED` + the stat bracket, `V-DEPLOY-CREDENTIALS-UNTOUCHED` + the zero-occurrence grep, the hooks repair running only on measured `hooks_broken` through the existing installer, and the ancestry plus floor checks.

## Named debts (shrink-only)

- `gsd_mission.py arm` first launch is ungated: in `owner-bundle.md` as the `[B]` DEBT line and in `B.md`; closing condition stated there; NOT closed by either PRG.
- The apply path has only ever run on scratch envs; the first real `--apply` is an Owner action.
- Both real installs are dirty (a7: 1 file, a5: 1024), so neither can be deployed until the Owner decides what to discard.
- `modules/liveness/reachability.py` does not enumerate `tools/`; `tools/test_gsd_x_runtime_preflight.js` is laptop-plane (3/7 on GEX44); the Linux-firing Windows git trap in `modules/cascade_prevention/dangerous_cmds.py` (it also annotated nearly every plain `git` command in this run).

## State bookkeeping

Ledger `state.B` / `state.C` NOT written; IC-B / IC-C NOT ticked (the terminals are the Owner-run PRGs). `vault/progress.md`, the workstream `config.json` and `milestone.lock` left alone.

## Self-Check: PASSED

- Files exist: `tools/gex44_env_deploy.py`, `tools/test_gex44_env_deploy.py`, `evidence/C.md`, `evidence/B.md`, `evidence/B-deploy-dryrun-gex44.json`, `owner-bundle.md` (checked with `[ -f ]`).
- Commits exist: `562ff3d2`, `37a8b518`, `f6a40285` (checked with `git log`); no deletions in any of them.
- `DEPLOY_PASS=16/16`, `DRILL killed=6/6`, suites equal their baselines, ledger diff empty.
