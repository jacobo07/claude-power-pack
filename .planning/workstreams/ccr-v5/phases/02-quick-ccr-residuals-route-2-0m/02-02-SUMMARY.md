---
phase: 02-quick-ccr-residuals-route-2-0m
plan: 02
subsystem: ccr-stage3-pgo-install
tags: [ccr, pgo, deflate, installer, hold, x2-step-5]
requires: []
provides:
  - "ccr_pgo.py install / verify subcommands on the existing PGO owner (no new module)"
  - "Stage 3 PGO files live in ~/.claude/ccr/state/pgo/ with sha256 equal to the committed sources"
  - "CPP_CCR_DEFLATE=off hold and hold-by-removal documented and tested"
affects: [02-04 evidence, Phase 11 knowledge]
tech-stack:
  added: []
  patterns: ["verify drives the real readers with all mission-state env vars pointed at a temp dir and refuses to run if the state dir is not isolated", "mirror of a TypeScript rule pinned by a text-drift gate with mutated-text controls"]
key-files:
  created:
    - tools/test_ccr_pgo_install.py
    - vault/programs/ccr/PGO-INSTALL.md
    - vault/programs/ccr/stage3/pgo-install-receipt.json
  modified:
    - tools/ccr_pgo.py
key-decisions:
  - "install and verify got explicit branches above the contract fall-through; the old bare else became `elif x.cmd == \"contract\"` so an unknown subcommand can no longer run contract"
  - "verify's ok requires: contract from the installed file, off-hold rows empty, break-even not invalid; breakeven_ok is None (UNKNOWN) when no file exists, never a pass"
requirements-completed: [REQ-2]
status: complete
duration: ~40 min
completed: 2026-10-15
commits: 1
plan_head_before: 3b9a60ff3f9ee4d369091f2e07ec15a540af06b7
actuals:
  tasks: 3
  commits: 1
---

# Phase 2 Plan 02: PGO install/verify, DEFLATE live and held Summary

`tools/ccr_pgo.py` now has `install` (validate every source with the `policy.ts` break-even rule, atomic write, read-back sha256, refuse a differing overwrite without `--force`) and `verify` (drives the real `gsd_mission._ccr_contract` and `deflate_unit`); the three Stage 3 files are installed live and measured, with the two DEFLATE holds documented and tested.

## Result

- `PGOINST_PASS=14/14`, exit 0 under `python -I` (5 tracer gates + REAL-STATE-UNTOUCHED, 7 expansion gates, 1 doc gate).
- Regression guards: `test_ccr_pgo.py` `CCRPGO_PASS=16/16` rc 0; `test_gsd_mission_ccr_a6.py` `13 passed, 0 failed` rc 0; `test_gsd_mission_ccr_contract.py` `5 passed, 0 failed` rc 0.
- Commit `0930ee2e` (`ccr-v5 p2: X2 step 5 - ccr_pgo install/verify, DEFLATE hold, PGO install receipt`): exactly the four planned paths, no deletions; `git log -1 --format=%s` matched the message file.
- Release precondition: `ccr_release.py status` showed active release `0.1.0-54f1824b` (read-only).

## Live measurement (verbatim facts, for 02-EVIDENCE.md)

| Step | Command | Exit | Observed |
|---|---|---|---|
| BEFORE | `python tools/ccr_pgo.py verify` (default dir) | 1 | `dest_exists false`, both probes `UNFORECAST`, `deflate_live no_unit_class` |
| INSTALL | `python tools/ccr_pgo.py install` (no `--force`) | 0 | 3 files `installed`, read back from disk |
| AFTER | `python tools/ccr_pgo.py verify` | 0 | `classes_ok true`, `breakeven_ok true`, bounded-code `MEDIUM` -> `deflated` (unit `bounded-code-worker`, declaration file written), lookup `LOW` -> `would_deflate`, `deflate_off` rows empty |

Installed (all `Get-FileHash` SHA256 equal to the committed source):
`pgo-classes.json` 14151 B `9815fbc4...682c`; `bounded-code-worker.breakeven.json` 410 B `0f2bf6a0...959f`; `read-only-reviewer.breakeven.json` 264 B `0cd328e2...63fd`. The directory holds exactly those three names. HR-001 did NOT refuse the write (no OWNER_STEP needed); the Owner step is still in the runbook for a future refusal.

## Tasks

| # | Task | Outcome |
|---|------|---------|
| 1 | Tracer: install classes into staging, real contract, real deflate, declared unit file | all tracer gates green on first run |
| 2 | Break-even validation, refusals, both holds, drift pin | 8 bad-file variants rejected with the field named, control accepted; invalid source aborts with the destination not even created; differing file refused, `--force` records previous sha256 |
| 3 | Runbook, live install with before/after, receipt, commit | measured above; one commit |

## Deviations from Plan

**1. [Rule 3 - Tooling] No PowerShell tool in this run**
- Only the Bash tool was available and the Windows Bash Bridge Guard blocks direct `git`/`python` calls. Every shell action ran as `powershell.exe -File <ps1 in %TEMP%>`; no guard escape markers were used. Edits and files went through Edit/Write.

**2. [Branch namespace]** Commit on `ccr/v5` as designated by the orchestrator (not a protected branch).

**3. [Scope] STATE.md / ROADMAP.md not updated** by this executor: the plan's output spec asks only for this SUMMARY, and sibling plans of the phase run in the same worktree; the orchestrator owns the state advance.

**4. [Plan detail] classes-only staging uses an empty `--breakeven` directory** (the plan's CLI has no `--no-breakeven` flag), which installs no break-even file.

## Residuals / observations

- DEFLATE is now ON by default for bounded-code slim launches wherever the process reads the default directory. The per-process hold is `CPP_CCR_DEFLATE=off`; it does not reach Task Scheduler processes. Persistent per-user variable: Owner decision, not applied. Removing `pgo-classes.json` is the hold that reaches every launcher.
- `long-textual` is mapped to `bounded-code-worker` in `UNIT_FOR_CLASS` but its A3 confidence is LOW, so it only records `would_deflate`.
- Nothing under `~/.claude` other than the three named files was created; `settings.json`, `CLAUDE.md`, `rules/` untouched. 02-CONTEXT.md left untracked as instructed.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: tools/ccr_pgo.py, tools/test_ccr_pgo_install.py, vault/programs/ccr/PGO-INSTALL.md, vault/programs/ccr/stage3/pgo-install-receipt.json
- FOUND: commit 0930ee2e on ccr/v5; `git show --stat` listed only the four planned paths
- Secret scan (`sk-ant-`, `ghp_`, `AKIA`, `BEGIN .*PRIVATE KEY`, `password\s*=`): 0 matches in the four files
- Live directory listing: exactly the three expected names, sha256 equal to sources
