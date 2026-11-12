---
spec: mission-autoresolve
tier: T2
status: LIVE (GEX44 first; Windows PP port tracked separately)
covers: [mission-supervisor, route-admission, amr-unit-selection, cwd-alignment, claude-exe-resolution]
origin: Owner 2026-11-12 "no esta funcionando globalmente el autodesbloqueo tras 5 minutos? por cualquier tipo de motivo que fuese el bloqueo?" then "y"
gate: python tools/test_mission_autoresolve.py (V-AUTORES-*)
---

# Mission auto-resolve: stops that durable state can answer

## Problem

On 2026-11-12 mission m-6043c9b8e6c4 (SGE CEF, GEX44) lost about 9 hours to four stops. The 5-minute sweep
judged each of them on every pass. None was an Owner decision, and none cleared on its own:

| # | Stop | Hours | Why the sweep could not clear it |
|---|------|-------|---|
| 1 | `launch held: cwd not aligned with work_dir (diverged)` | 2.25 | The bound worktree held one extra STATE.md commit, and the main tree had moved on with the code. Nothing changes that. |
| 2 | AMR owner boundary `same unit root/phase-01 closed twice` | 2.2 | With no `current_phase:`, recovery took the first incomplete phase, which was human_needed Phase 1. |
| 3 | P7 credential ask (class UNKNOWN) | 0.5 | Needs an Owner act. Kept by design. Also, `decide` over ssh answered woke=False because of the wrong `claude` binary. |
| 4 | `relay re-admission DEFER ... unit lease` -> HALTED | 4.5 | Admission budgeted 2 x a machine-set AMR estimate (0.76M left), not the 320M Owner authority. HALTED renews only on budget halts, and the mission has no steward goal. |

## Non-goals

- No blanket release after N minutes. A stop that durable state cannot answer would recur immediately and spend
  tokens in a loop (stop 2 re-proved Phase 1 three times). It would also bypass the credential and publish gates.
- Credentials, publishing, push and other Owner-class stops stay parked (stop 3).

## Requirements

- **R1** `admit_route`: when the mission has `authority_tokens` and the estimate is machine-set
  (`token_estimate_src` in `auto` or `amr`), `remaining = authority - closeout_reserve - spent`.
  - This is the ceiling `_auto_budget` and AMR lease pricing already use.
  - An operator-set estimate (`src` None) keeps `ratio x estimate - spent`.
  - The unit still stays bounded: the cost breaker trips at `ratio x estimate`, AMR re-prices the next lease (the
    recovery path that worked at r1-r6), and the stall budget catches spend that makes no progress.
- **R1b** The DEFER halt reason no longer promises a steward or chain continuation when the mission has no CE goal.
  It names the remedy instead: raise the authority and arm a successor.
- **R2** `mission_recovery.gsd_unit`, when there is no `current_phase:`: take the first incomplete phase whose
  VERIFICATION.md is not `status: human_needed`. If every open phase is human_needed, keep the first one.
- **R3** `align_cwd`: if the cwd and work_dir have diverged, and the work_dir's own commits since the merge-base touch
  only `.planning/`, return `diverged_planning_only`, which does not block.
  - The supervisor then rebinds the mission to the cwd (`bind_mission`, cause `planning_only_divergence`) and writes a
    ledger row `cwd_planning_only_rebound` naming the stranded head.
  - Nothing is merged or deleted.
  - A divergence that touches code still holds.
- **R4** `claude_exe()`: `CPP_CLAUDE_EXE` wins. Otherwise, off Windows, the per-user `~/.local/bin/claude` (the one
  the sweep unit pins) comes before PATH.

## Acceptance

`tools/test_mission_autoresolve.py` passes. It holds 11 gates: 5 positive, 5 paired controls and 1 env override.
R1b changes a message only and has no gate.
The existing suites stay green: `test_gsd_mission_chain.py`, `test_mission_recovery.py`, `test_gsd_mission.py`
and `test_mission_continuity.py`.

## Rollback

`git revert` the commit. Each requirement is local to one function, and no record format changes. A
`diverged_planning_only` rebind is undone with `gsd_mission.py bind --mission <id> --path <old root>`. The
ledger row names the old head.
