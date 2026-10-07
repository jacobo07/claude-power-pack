---
phase: 01-w0-reality-baseline-and-incumbent-measurement
plan: 01
subsystem: gsd_x goal gate provider
tags: [windows, subprocess, gate-supervisor, mutation-drill, ukdl]

requires: []
provides:
  - gate supervisor that hands its std handles to the gate (gate output reaches the run log and the verdict's observed field on Windows)
  - RED/GREEN/collateral/drill evidence logs for R01
  - UKDL trap T-SUBPROCESS-WITHOUT-INHERITED-STD-HANDLES-LOSES-GRANDCHILD-OUTPUT-ON-WINDOWS-001
affects: [01-05 incumbent measurement (observed now real), 01-06 EVIDENCE, Phase 4 certificate producer (observed redaction, T-01-02)]

actuals:
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns: ["RED captured to the phase dir before the edit, committed with the fix", "drill anchors carried in JSON specs"]

key-files:
  created:
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-r01-red.log
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-r01-green.log
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-r01-collateral-pre.log
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-r01-collateral-post.log
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/r01-drill.json
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/r01-drill-stderr.json
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-r01-drill.log
    - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-r01-drill-stderr.log
  modified:
    - modules/gsd_x/goal/providers/gate.py
    - vault/knowledge_base/ukdl-universal.md

key-decisions:
  - "Kept 18/18 as the literal done criterion; the stderr-only mutant's SURVIVED verdict is recorded as a known blind spot, not hidden"
  - "Executed inline by the orchestrator: subagent sessions have no PowerShell tool and the Windows Bash guard blocks git/python from Bash"

requirements-completed: [R01]

coverage:
  - id: D1
    description: "Gate output captured on Windows: V-GATE-VERDICT-FIELDS green"
    requirement: "R01"
    verification:
      - kind: unit
        ref: "python tools/test_gsd_x_goal_gate_provider.py"
        status: pass
  - id: D2
    description: "Revert of the fix killed for the right reason, with control"
    requirement: "R01"
    verification:
      - kind: other
        ref: "python tools/mutation_drill.py --spec .../r01-drill.json"
        status: pass
---

# Phase 1 Plan 01: R01 gate supervisor fix — Summary

**The gate supervisor now runs the gate with `stdout=sys.stdout, stderr=sys.stderr`, so on Windows the gate's output reaches the run log and every verdict's `observed` field is real instead of `''`.**

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | `58934936` | fix(gsdx-pcc-01): gate supervisor hands its std handles to the gate (R01) |
| 2 | `6216a3c9` | test(gsdx-pcc-01): mutation drill of the R01 fix -- revert KILLED, stderr-only recorded |
| 3 | `0c93c0e9` | docs(gsdx-pcc-01): UKDL trap -- handle-less supervisor loses gate output on Windows (R01) |

## Accomplishments

- **Precondition:** `rc=subprocess.run(cmd).returncode` had exactly 1 hit, at gate.py:72; gate.py clean.
- **RED (before the edit):** `FAIL V-GATE-VERDICT-FIELDS` with `'observed': ''`, `GSDX_GATE_PROVIDER_PASS=17/18`, `EXIT=1`. Raw run logs in `%TEMP%\gsdx_gate_runs_7qvrkn49`: `gate-tok-ok.log` 0 B, `gate-tok-bad.log` 0 B, `gate-tok-slow.log` 0 B.
- **GREEN:** `GSDX_GATE_PROVIDER_PASS=18/18`, `EXIT=0`. Raw run logs in `gsdx_gate_runs_s7mmokbq`: `gate-tok-ok.log` 11 B `12 passed`, `gate-tok-bad.log` 10 B `1 failed` (the failing gate's output is captured too — research open question 3 answered). V-GATE-CANCEL-KILLS stayed green.
- **Collateral (pre = post, all exit 0):** sweep 14/14, gate_class 11/11, cli 25/25, chaos 15/15.
- **Drill:** revert mutant → `MUTANT KILLED gate=V-GATE-VERDICT-FIELDS`, exit 0 (control passed). Stderr-only mutant → `MUTANT SURVIVED gate=V-GATE-VERDICT-FIELDS`, exit 1 (known blind spot: the suite's gates print only to stdout). Live gate.py SHA-256 unchanged; `git status --porcelain -- modules tools` empty.
- **UKDL:** one new tail section, heading present exactly once, numstat 24 added / 0 deleted.

## Deviations from Plan

### Instrument incident — hermeticity fingerprint confounded by a live scheduled writer

- **Found during:** Task 1 step 8.
- **Observed:** `~/.claude/state/gsd-x` file count 254 before and after; max `LastWriteTimeUtc.Ticks` moved 639269757593441469 → 639269760517912049.
- **Attribution:** the only file newer than the baseline was `sweep_heartbeat.json` (276 B, ts `2026-10-07T13:20:51Z`, `refused: autonomy record is for engine 8673feab1dac ...`). The scheduled task `PP-GoalSweep` (wscript → main checkout `tools/goal_sweep.ps1`, 5-minute cadence) last ran 15:20:48 local = 13:20:48Z. These suites did not write the store.
- **Consequence:** the plan's whole-directory max-mtime fingerprint cannot distinguish a suite write from the live sweeper (an instance of T-AN-MTIME-SENTINEL-OVER-STATE-OTHER-WRITERS-OWN-001). Plan 01-02's `fingerprint` must exclude `sweep_heartbeat.json` (or attribute it by name and timestamp to the scheduler) so a heartbeat tick is not reported as a non-hermetic suite. Production Reality: hermeticity of these suites OBSERVED (count unchanged, only scheduler file moved).

### Execution mode

Executed inline in the orchestrator session (not a gsd-executor subagent): subagents in this session have no PowerShell tool and the Windows Bash guard blocks git/python from Bash. All commands followed the plan's PowerShell recipes.

### UKDL commit

The concurrent-writers hook blocked the first commit attempt (shell-appended lines it could not attribute); the lines were this plan's append (24/0), so the same commit was re-issued.

## Self-Check: PASSED

- gate.py contains the fixed call exactly once; RED/GREEN/collateral/drill logs exist and are committed; three commits verified with `git log -1 --format=%s`; nothing pushed.
