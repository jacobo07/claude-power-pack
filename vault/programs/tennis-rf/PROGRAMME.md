# Tennis Reconstruction Optimization + Reforecast (TRF) -- common brief for every unit worker

Binding plan: `C:\Users\User\.claude\skills\claude-power-pack\vault\plans\tennis-rf-optimization-MASTER-PLAN-2026-10-11.md`
(d69b4556; Owner "y" and "si, hard stop 55M", 2026-10-11). Read sections 1-3 and 7 once; your packet names what is
yours. No orchestrator exists above you. `chain.json` here is ticked every 10 min by the zero-model task
PP-TrfChain-Tick, which arms the next unit when your receipt says DONE. Goal `tennis-rf`, hard stop 55M processed
tokens for the whole programme (W0 spent ~2M of it in the planning pane).

The question this programme answers: what will Tennis Scope A and Scope B really cost, measured on Tennis evidence,
after the factory stops wasting work on shared failures and uses cheap paths before the model. It does NOT execute
Scope A or B. It does NOT change their definition (D21 in `vault/plans/deferred-backlog.md`).

## Paths
- Work tree (your cwd): `C:\Users\User\Apps\recon_work\wt_tennis_rf` (branch tennis-rf, from keosdtk-home 3c86ae2).
  Decomp core: `tools\wros\binary\decomp\` (+ `gex44\`). Never write into wt_keosdtk_home, wt_cp50_c1, wt_cp50_c2.
- Factory state (shared, read; append only through its own tools): `C:\Users\User\Apps\recon_work\recon_factory\`.
- Tennis evidence so far: `C:\Users\User\Apps\recon_work\wst_tennis\step0..step3\` and PP `vault/plans/d11-tennis-step{0..3}.md`.
  Binary: `files/EU/sys/sports/SportsPackEP.dol` extracted under step0 (do not re-extract the disc).
- The failed C2b evidence: job `recon_factory\gex44\jobs\candidate-20261010T151142Z`, return
  `recon_factory\gex44\returns\ksrmb-20261010-203003`, ledger `recon_factory\gex44\candidate_ledger.jsonl`.
- Programme files and receipts: this folder (PP live checkout, `vault/programs/tennis-rf/`).

## Session loop
1. Tests first (RED), then code. Pathspec micro-commits with the Co-Authored-By line from the commit attribution.
   Never `git add -A`. Git via `git -C <path>`; never Set-Location into another goal's root.
2. If the recon commit hook (`.ksr_vault` snapshot gate) refuses a commit in wt_tennis_rf: do NOT use --no-verify.
   Save `git -C <wt> diff --cached --binary` to `vault/programs/tennis-rf/patches/<unit>-<n>.patch` here, commit that
   patch in the PP checkout (pathspec), and continue. W1 owns fixing the gate or certifying a copy route.
3. Close: overwrite your receipt `WU-<id>-receipt.md` beside your packet. Line 1 `# <id> receipt`, line 2
   `Status: DONE`, then commits, PROVEN / NOT_PROVEN / BLOCKED_* / INCONCLUSIVE per claim, measured numbers with the
   command that produced them, calls used, what the next unit must know (<= 8 lines). Commit it (PP, pathspec).
4. Unit too big (stop starting new work at 85 % of your calls): commit what is done, INSERT a continuation unit into
   `chain.json` right after yours (id `<id>b`, `after` = your id, packet `WU-<id>b.md` with the exact remaining steps,
   same route), then receipt `Status: DONE` (slice done); commit all three together. Never write PARTIAL: the chain
   does not re-arm a unit that ended without DONE.
5. Blocked on something only the Owner can do: receipt `Status: BLOCKED_HUMAN` with the exact action (stops the chain).
   Capital, legal/security, credentials and Tennis scope are the only such things.

## Economic rules (the point of the programme)
- Cascade before cognition: NO_WORK -> cached/prior result -> Resort-shape donor -> deterministic transform ->
  compile/objdiff oracle -> model. A model step on a function needs a one-line Proof of Model Necessity in its record:
  which cheaper layer was tried and what it returned.
- Measure, never assume: every per-function record carries processed tokens deduplicated by message.id
  (`tools/mission_spend.py` session_tokens / `tools/session_autopsy.py` in PP), calls, compiles, verdict, and which
  layer closed it. Missing measurement is UNKNOWN, not zero.
- No fan-out before shared readiness: nothing goes to GEX44 without the W2 certificate once W2 exists.
- No Agent / Task spawns, no `/gsd-autonomous`, no EnterWorktree. One worker, one unit.

## Hard constraints
- Owner rule (2026-10-03): zero local compiles. Compiles run on GEX44 compute jobs through stage.py. Tennis may use up
  to 4 compute jobs in total (plan section 8); record each job id in `vault/programs/tennis-rf/JOBS.md` before sending.
  Phase-7 jobs (RF_PHASE_JOB_CAPS phase 7) and goal cp50-c2 are NOT this programme's.
- No Dolphin, no real Wii, no GEX44 live-install change, no push, no cap change.
- Windows: git/python via the PowerShell tool with absolute paths (`C:\Program Files\Git\cmd\git.exe`,
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`). No Bash for git/python.
- Analyse only the Owner's own disc image (SP2P01) and the factory's existing binaries.
- Iterate with `C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` at the
  checkpoints your packet names (read once per session; apply; never paste it into commits).
- Every bug found: an entry in `vault/programs/tennis-rf/KNOWLEDGE.md` (symptom, trigger, root cause, economic
  impact, fix, prevention, proof). W9 promotes them.
