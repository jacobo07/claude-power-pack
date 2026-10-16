# WU-PX -- 9-PARTIAL closure pilot: dossiers, permuter admission + runs, --l0 fix, control fixture, job 4 judge

Plan: `vault/plans/r2-failure-recompile-2026-10-16.md` (Owner "y" 2026-10-16), replacing R2+R1+P1. Hard cap 5.0M tokens.
**Checkpoint: the 9 dossiers must be committed by 1.0M processed or stop and write the receipt.**
No orientation searches: every path you need is below. Do not run git log, ls, or a Glob/Grep over a directory tree;
open the named files directly. If a named path is wrong, record it and use one Grep inside that one directory.

## Handles
- Worktree (cwd): `C:\Users\User\Apps\recon_work\wt_tennis_rf`; D = `tools\wros\binary\decomp`
- Judge: `D\gex44\candidate.py` (`l0_row` :225-235, `oracle2` :269, `judge_tree` :477, `cmd_judge` :588; L0 read at :52 from
  `capsule_profile.active()["l0"]`). Profile: `D\gex44\capsule_profile.py`. Staging: `D\gex44\stage.py`, `D\gex44\repatriate.py`.
- Near-match facts (the 9 fns, signals, first diverging insn): PP `vault\programs\tennis-rf\evidence\d28\d2\near_match.json`
- Ledger: `C:\Users\User\Apps\recon_work\wst_tennis\w10\F\candidate_ledger.jsonl`. Donors = rows with producer `w10c_donor`
  and exact_match true (read the file with python, filter; do not search).
- D9 negative knowledge (802128D4, 8032CF78; 31 variants, 0 MATCH): PP `vault\programs\tennis-rf\evidence\d28\d9\synthesis.json`
- Current best source per fn: the ledger row's `evidence` / job tree of job ksrmb-20261012-171117 (W12) under
  `wst_tennis\w10\F` (follow the row's path field).
- Env for judging: `KSR_CAPSULE_PROFILE=tennis`, `MATCH_ACCEL_GEX44=C:\Users\User\Apps\recon_work\wst_tennis\w10\F`.
- GEX44: `ssh gex44` (BatchMode). Compiler: `/home/kobii/ksr_stage/ksrmb-20261014-164017/work/tools/{mwcceppc.exe,
  wibo-x86_64,objdiff-cli}` (check sha256 = ledger `compiler_sha256`); `/usr/bin/powerpc-linux-gnu-objdump`;
  python venv `/opt/ksr-decomp/venv`. Remote scripts: write a no-BOM LF file and run `ssh gex44 bash -s < file`.
- JOBS: PP `vault\programs\tennis-rf\JOBS.md` row 4 (reassigned to this batch); rewrite the row BEFORE send.

## Steps
1. `D\dossier.py` + `D\dossiers\<fn>.json` for the 9 fns: entity, preset, best source path, L0 locator, near-match
   signals, prior attempts (ledger rows), family_key = primary+subsignal+size delta. Commit. (checkpoint)
2. `D\gex44\candidate.py`: `--l0` option on judge; entity absent from profile L0 and no `--l0` -> refuse `L0_ROW_ABSENT`
   (was a silent ORACLE_REFUSED). Verdict logic unchanged. Test both poles. Commit.
3. Permuter: clone github.com/simonlindholm/decomp-permuter to `/opt/ksr-decomp/permuter` (record sha), venv
   `/opt/ksr-decomp/permuter-venv` + `pip install toml`; compile.sh from its `mwcceppc_compile_example.sh` with our
   compiler + preset flags (D\match.py presets). Admission: a sealed donor scores 0 at iteration 0, and the same donor with
   one constant changed scores > 0. Fail -> TOOL_INCOMPATIBLE, skip step 5's permuter runs.
4. Control fixture: from a donor that loads a struct field, a correct-width source (predicted MATCH) and a u8->u32 source
   (predicted non-MATCH). Both go into the job.
5. Routes: 8021F8BC POINTER_STRIDE -> fix the pointee type/stride by hand. 80253348 + 8032CF78 sda21 -> flag sweep
   (-sdata/-sdata2 thresholds, presets incl O2; this retires D9's O2 arm). 80254440 REGALLOC, 8022621C SIZE_-1,
   80241018 bool_idiom -> permuter 20 min wall, -j8, stop at 5 min without score gain, max 3 at once. Stop-loss: first 3
   permuter runs with 0 gain -> no more permuter runs. 8021F3E4 PTMF_R12 -> not attempted (SEMANTIC). T1: each win applied
   unchanged to its partner (8022621C->80278FEC, 80241018->802128D4, 80253348<->8032CF78). Record cpu_s and wall per run.
   Write `D\factory\priors.jsonl` (wins) and `D\factory\negative.jsonl` (exhausted searches, plus D9's 31 variants and the 7
   unrun D12 bundles, reason T2 flat).
6. One GEX44 job (job 4): best source per improved fn + the 2 fixture sources + 3 donors. Certify, send, wait <=540 s per
   wait, repatriate, judge with `--l0` = batch L0. Valid only if donors 3/3 MATCH and the fixture discriminates.

## Receipt `WU-PX-receipt.md` (DONE / DONE_WITH_LIMITS / PARTIAL)
Per fn: route, backend, result (MATCH / IMPROVED / NO_CHANGE / REGRESSION / SEARCH_SPACE_EXHAUSTED / TOOL_INCOMPATIBLE),
cpu_s, wall; T1 per pair; permuter sha + admission both poles; fixture result; job id + validity; tokens; commits.
Limits: no model calls on functions, no capsule edit, no job beyond 4.
