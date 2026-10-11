# WU-B0 -- CPX bootstrap: arm the two chains (goal cpx)

Plan: `vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md` (c68383ba, Owner "y" 2026-10-11). Read sections 5, 7, 8 only.
Do NOT read `vault/plans/deferred-backlog.md`: plan section 2 already routed D14/D21-D26.
Why you exist: planning pane 3b4f4757 tripped its own coordinator cap (session-declare stop 1.5M; 4,943,171 processed at
trip). That is the D22/D23 governor firing on its author. Rotation is this packet, not an Owner kclear.
Cwd = `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\cpx` (goal cpx). Git via
`& 'C:\Program Files\Git\cmd\git.exe' -C <path>`; never Set-Location into wt_cp50_c2 or wt_tennis_rf. No Agent spawns.

1. Settle C2c-fix worker 3cf66819 on goal cp50-c2: `tools/mission_spend.py goal-settle` (goal-autopsy measured 799,548,
   8 calls; lease 750,000 open). Mission m-ae80353974b4 is HALTED: never re-arm it.
2. In `vault/programs/cpx/chain.json` (this chain) INSERT units after B0: R1 rule router, R2 control-plane P&L +
   CONTROL_PLANE_TOKEN_INCIDENT + coordinator cap + `status` single-mission filter + generated C2-RESUMPTION, R5 D24/D26/FIOS
   evidence, R9 KV/UKDL/CBR + final handoff (R9 also waits for `vault/programs/cp50-c2/C3-receipt.md` Status DONE; say so
   in its packet). Packets `WU-<id>.md` from plan section 5, each <= 40 lines, each naming its done-check and route.
3. Create `vault/programs/cp50-c2/chain.json`: goal cp50-c2, root `C:\Users\User\Apps\recon_work\wt_cp50_c2`, envelope
   4,300,000, max_residuals 0, units R3 -> J3 -> C3 -> D21F (packets from plan section 5). J3: send refused without the R3
   readiness certificate (W1 port fa8aaf0 + trim + output budget <= 20,971,520 + job-key exactly-once + CURRENT_CAPSULE);
   before prepare, check `vault/programs/tennis-rf/JOBS.md` and the TRF job dirs for a prepared-unsent job (shared
   CURRENT_CAPSULE) and stop BLOCKED_HUMAN only if it cannot be serialized. Phase-7 job 3 is authorized by
   cp50-run-plan D4 (Owner y 2026-10-09): do not ask again. Job 4 per plan section 5 only.
4. If `~/.claude/state/trf-chain-tick.log` shows W2 not yet armed: append to `vault/programs/tennis-rf/WU-W2.md` a step
   "port trim: runner_lib.py:1472 shutil.copyfile -> trim_objdiff_report (PP patch 147115b0)" and a certificate check
   "output budget: sum(.o + trimmed diff) + log ceiling <= 20,971,520 else NOT_READY:OUT_BUDGET". If W2 is armed, write
   the same as `vault/programs/tennis-rf/W2-amendment-cpx.md` and note it in your receipt.
5. Tick task PP-Cp50ChainTick: clone `vault/programs/cpx/chain_tick.ps1` and the PP-CpxChain-Tick task (log
   `cp50-chain-tick.log`). Never tick a chain by hand (no tick lock until APR-3).
6. cp50-c2 cap 14M -> 16M only through `mission_spend capital-apply` (OCA) citing the Owner "y" in transcript
   3b4f4757; if refused, skip it (R3+J3+C3 fit about 4.34M) and record why.
7. Every unit packet you write carries: K7 estimate-vs-actual row in its receipt; no Monitor; no waiting call.
Receipt `vault/programs/cpx/WU-B0-receipt.md`: line 1 `# B0 receipt`, line 2 `Status: DONE`, then commits, settle output,
task names. Pathspec commits only, message ends with the Co-Authored-By line from the commit attribution.
8. Amendment A1 (plan section 7c, binding): in the cp50-c2 chain insert R6 (deterministic evidence dossier + content-
   addressed cache, zero model calls) BEFORE J3; J3's packet runs two arms on the SAME Phase-7 slot (current vs
   current+dossier) and records the per-function metrics listed in 7c; C3's packet reports both arms and the
   model-needed fraction. R5's packet adds the D11-D19 evidence-gated admission table (D14/D20 guards). REA is
   REJECT for PPC (tennis-rf/REA-DISPOSITION.md): do not reinstall it.
9. Amendment A2 (plan section 9): R5's packet includes D27 (REA Wii/PPC Enablement, `vault/plans/deferred-backlog.md`)
   in its admission table and may arm P0 as a small zero-model unit; R6's packet states its dossier contract as the
   baseline for D27 P7.