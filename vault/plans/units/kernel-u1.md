# Work Unit kernel-u1 — economic kernel, Envelopes 0 (rest), 1, 2

Goal `ccr`, lease L17 (cap 13,000,000, reserve 1,000,000). Plan: `vault/plans/ccr-v5-economic-kernel-2026-10-15.md`
(read section 1 only; it holds the measured facts. Do not re-derive them).
Work tree: `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr-v5` (branch ccr/v5).
Live kernel: PP main `4752ce43` already carries phase_lease.py, hooks/lib/mission_gate.js, the supervisor phase breaker
and stopped-worker booking. Tests: test_phase_lease 23/23, test_gsd_mission_phase_lease 15/15, test_mission_gate 31/31,
test_accounting_authority 10/10, test_gsd_mission 230/230. test_gsd_epoch baseline on main = 86/92 (6 pre-existing fails).

## Rules
- You are alone: no subagents, no Agent tool. Main thread only. Batch independent reads in one turn.
- Large files: never page gsd_mission.py top to bottom. `Grep -n` for the symbol, then Read only that range.
- Code changes are made in the worktree, tested there, committed on ccr/v5 (`git commit -F <msg in $env:TEMP> -- <paths>`).
  Then they land in the PP main tree ONLY via
  `C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files\d124ce03-2566-43ed-957e-73d445141e58\scratchpad\land_kernel.ps1`.
  Copy that script, set `$base` to the main HEAD you verified and `$src` to your commit, set `$files` to exactly your files,
  keep its refuse/rollback logic. Never touch other main-tree paths. No push. No settings.json / CLAUDE.md / rules.
- Git `& 'C:\Program Files\Git\cmd\git.exe' -C <repo>`; Python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`,
  `$env:PYTHONIOENCODING='utf-8'`. PowerShell. Never ask the Owner: write blockers to the EVIDENCE file and continue.

## Tasks (in order; commit after each)
1. **Next-call exposure (Env 0).** In `hooks/lib/mission_gate.js`, deny when used + last-call context (from the
   session transcript's last assistant usage) would exceed the authority/phase hard cap. This bounds overshoot to one
   call. Tests: near-cap denies; under-cap allows (control). Land.
2. **Live proof (Env 0, S0-DONE-5).** Drive the REAL dispatcher (`node C:\Users\User\.claude\hooks\hook-dispatcher.js`)
   with a PreToolUse PowerShell payload for a synthetic session bound to a synthetic held mission in a temp state dir
   (env override if the gate supports one; if not, add one in the same change). It must deny, and the control must allow.
   Record the exact command and output.
3. **Sweep priority (Env 0).** `tools/gsd_long_run_sweep.ps1` / `gsd_mission.py supervise`: evaluate cost/phase
   breakers for RUNNING missions before any slow host query, and cap per-mission time, so a 600 s stage timeout cannot
   skip breakers (measured: timeouts at 11:31/11:47/12:01 UTC 2026-10-15). Test with an injected slow host call. Land.
4. **Floor decomposition (Env 1).** Extend `tools/ccr_rent_ledger.py` (Phase 1 of v5) to attribute the invisible
   ~59K of worker 49c0ae70's first call (system prompt, tool schemas) from its `api-request*` transcript rows. Output
   rows per category with HOST_HARD / CONTROLLABLE / UNKNOWN. Record bg vs slim floors side by side.
5. **Context admission (Env 1).** At `arm`/`arm-chain`: expected floor by launch kind (bg ~116K, slim ~13K, from
   step 4). A bg launch for a work class marked slim-capable -> RECOMPILE (refuse with the remedy). Tests.
6. **Boundary ledger + authority (Env 2).** Commit the call classifier (pattern in
   `.../scratchpad/autopsy.py`) as `tools/ccr_call_ledger.py`. Add `max_calls` to the phase lease
   (`tools/phase_lease.py`) and enforce it in mission_gate. Persist the Work-Class profile
   `vault/config/work-class-profiles.json` from measured sessions 49c0ae70, f06addea, af436132.
7. **Close.** Write `vault/programs/ccr/evidence-kernel-u1.md` (commands, exit codes, outputs, verdicts). Book your
   own session: `python tools/mission_spend.py goal-settle --goal ccr --session <your id> --measured <processed>`.
   Then write `vault/plans/units/kernel-u2.md` (Env 3: physical forecast gate, code-map page for files >2k lines,
   fresh epoch per plan, slim canary, Stage A reforecast) and arm it with `tools/gsd_mission.py arm-chain`
   (profile slim-t2, permission-mode auto, target <= L17 remaining minus 1,000,000).
Stop at your envelope; partial and honest beats complete and over budget.
