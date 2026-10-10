# C2a -- CP50 arm-A executor: decomp/arm_a.py + test_arm_a.py drill + ONE local staged job (build only, NO send)

Mission: the mission id on your rehydration card (write it in the receipt, mandatory). Goal `cp50-c2`, cap 4.0M, bound
to C:\Users\User\Apps\recon_work\wt_cp50_c2 only. Authority: Owner "y" to D1-D5 2026-10-09 (PP
vault/plans/cp50-run-plan-2026-10-09.md, D5 "Fund C1 and C2 (sized from C1's measurement)"); Owner "fund it"
2026-10-10. C2 = C2a (this lease: the executor) + C2b (the pilot send, a later lease). Funds C2a ONLY: NOTHING is sent to
the VPS or GEX44 (no `stage.py send`, no ssh, no scp), no model or paid call is made by your code, never read
G0_HOLDOUT.json, never arm a mission, never push, never edit stage.py's RF_CURRENT_PHASE (C2b sets 7 at its send).
Envelope (route-C2a.json): target 1.6M | warn 1.7M | stop 1.75M; the session guard then allows up to 4 closeout calls.
When the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt and the commit and write the unfinished part as
PARTIAL. Hard limit 9 tool calls. 0 subagents. NO search tools (Glob/Grep).

## Corpus = ONE file
Read `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\recon-reforecast\C2A-DOSSIER.md`
(~25k tokens; two Read pages at most). It holds the live draw facts (n=300, anchor 0f2ecb37 MATCH, the pilot cohort =
positions 1-5 verbatim), the RF Phase 7 cap and its used count (0 of 4), ROADMAP Phase 7, REFORECAST section 3
(amendment (d)), the C1 receipt, the per-cohort template, the module docstrings (CLI contracts) and verbatim source of
bench.py, baseline.arms_block, m2c_producer.py, gex44 candidate.py, candidate_ledger.py, capsule_build.py, stage.py
(build/send/wait), runner_lib.mode_candidate, repatriate.py and custody.py. Read no other file. Anything not in the
dossier is UNKNOWN: write it in the receipt, never look it up.

## Work tree
Write and commit ONLY in C:\Users\User\Apps\recon_work\wt_cp50_c2 (branch cp50-c2, from keosdtk-home 3c86ae2). Data
inputs stay absolute and read-only (G0_FREEZE.json under wt_keosdtk_home, the factory/split/L0 paths capsule_build already
names). Merging cp50-c2 into keosdtk-home is the coordinator's step. Never Set-Location: absolute paths everywhere.

## The executor (arm A = the decomp Phase 5 free baseline, deterministic, no model)
`tools/wros/binary/decomp/arm_a.py`, stdlib + the existing decomp/gex44 modules only (GAP-3: capsules ONLY through
capsule_build / custody, returns ONLY through repatriate / candidate.py judge). Two CLI verbs and one callable:
1. `prepare --draw <G0_FREEZE.json> --first A --last B --out <dir>` (LOCAL):
   a. bench.load_draw + bench.cohorts -> exactly one cohort; refuse otherwise.
   b. Candidates: run m2c_producer.py under the factory venv python it requires (its venv_ok refusal is a result, not a
      bug: print it and stop PARTIAL) with `--ids` = the cohort ids, once plain and once `--valid-syntax` (baseline
      arms `m2c` and `m2c.valid_syntax`; the valid-syntax arm's composition = header bytes + "\n" + producer text, per
      arms_block). A function whose admit() is not L1 gets NO unit and later a record with verdict = that status.
   c. Units JSONL in candidate.load_units' UNIT_KEYS, one unit per (function, arm, capsule preset); producer
      "m2c" / "m2c.valid_syntax", strategy "free_baseline", family = the census class, variant = the preset name.
   d. Cohort capsule: capsule_build.build has no way to carry a target outside the donors. Add ONE keyword argument,
      `targets_for=None` (a list of census ids), resolved like resolve_targets but from the given ids (asm unit from the
      .fn index, object copied whole once); default None leaves the capsule byte-for-byte what it is today (same rule as
      --targets-from-donors; prove it in the drill). This is the ONLY edit to an existing .py. Build with the trims the
      ceiling needs (P3b-1 used `census`), out_root = the RF root's capsules dir (stage.RF_GEX44_ROOT\capsules).
   e. stage.build(mode="candidate", root=stage.RF_GEX44_ROOT, capsule=<id>, candidate_units=<jsonl>) -> one job dir.
      Print `ARM_A_PREPARED job=<dir> capsule=<id> units=<n> functions=<k> no_unit=<ids with status>`.
2. `records --job <job dir> --draw ... --first A --last B --out <arm A jsonl>` (after C2b's send/wait/repatriate and
   `candidate.py judge <job_id>` CAND_JUDGE=OK): builds an executor from the judged rows and calls
   bench.run_cohort("A", cohort, executor=..., out=...). Per function: verdict = best class over its units (MATCH
   first), verified = both oracles agree on MATCH, host_plane = the receipt host ("kobicraft-gex44" -> "GEX44"), cost
   {wall_s from the receipt's measured timings, compiles = attempted units, local_tokens/paid_tokens/
   new_cognition_tokens = 0 ONLY because arm A makes no model call (say so in deterministic_vs_cognitive =
   "deterministic"); every amendment-(d) field you cannot measure from the job = {"absent": "<reason>"}, never 0.
   Refuse JOB_NOT_JUDGED when the judge has not written its rows; nothing is appended.
3. `executor_from_judged(rows, receipt)` is the callable `records` injects; bench.py is NOT edited.

## Deliverables
1. tools/wros/binary/decomp/arm_a.py. 2. the `targets_for` keyword in gex44/capsule_build.py. 3.
tools/wros/binary/decomp/test_arm_a.py, gates PASS/FAIL, final `ARM_A_DRILL=n/m`, each with its red control, all in temp
dirs (no real ledger, no RF jobs dir):
   V-ARMA-COHORT (1-5 -> one cohort; 1-15 refused, 2 cohorts), V-ARMA-UNITS (units pass candidate.build_units against
   a temp capsule manifest; a unit whose target is not a capsule target -> TARGET_NOT_IN_CAPSULE), V-ARMA-NONL1 (an
   M2C_FAILED function -> no unit, record verdict M2C_FAILED), V-ARMA-CAPSULE-IDENTITY (targets_for=None -> manifest
   bytes identical to a build without the keyword; targets_for=[id] -> that target present), V-ARMA-RECORDS (judged
   fixture rows -> 5 bench records that pass bench.validate_record; MATCH ranks above PARTIAL), V-ARMA-UNJUDGED
   (no judge rows -> JOB_NOT_JUDGED, nothing appended), V-ARMA-NOZERO (an unmeasured (d) field is absent-with-reason,
   never 0), V-ARMA-NOSEND (arm_a.py source contains no call to stage.send / ssh / scp).
4. ONE real `prepare --first 1 --last 5`, local only (m2c + capsule + stage.build on the RF root). It writes a job dir
   and sends nothing. If the venv, the capsule or stage.build refuses, record the refusal code verbatim: that is a
   result (PARTIAL), do not work around it.

## Call plan (9 -- the admission floor fits no more; there is NO spare call)
1-2 Read the dossier (two pages). 3 Write arm_a.py. 4 Edit capsule_build.py (targets_for). 5 Write test_arm_a.py. 6 One
PowerShell call (absolute python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`,
PYTHONIOENCODING=utf-8, absolute script paths, never Set-Location): test_arm_a.py, then test_bench.py (must stay
BENCH_DRILL=8/8), then -- in the SAME call and only if both drills printed all PASS -- `arm_a.py prepare --first 1
--last 5` on the real draw. 7 Write receipt
`C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\C2a-receipt.md`. 8 One PowerShell
call: write each commit message to its own temp file in that call ([System.IO.File]::WriteAllText, UTF-8 no BOM), commit
arm_a.py + test_arm_a.py + gex44/capsule_build.py in wt_cp50_c2, then the receipt in the PP repo, each by pathspec
(`git -C <repo> add -- <paths>; git -C <repo> commit -F <msgfile> -- <paths>`; git = `C:\Program Files\Git\cmd\git.exe`),
then print both `git log -1 --format=%h %s`. 9 reserved for the closeout only. If call 6 is not all PASS, do NOT fix it:
write the receipt PARTIAL with the failing lines verbatim, commit anyway, stop.

Do not edit ROADMAP.md, STATE.md, bench.py, stage.py, runner_lib.py, candidate.py or any other existing .py.
Never write, stage, restore or clean anything under wt_keosdtk_home.

## Receipt (<= 20 lines)
Mission id, calls used, files + commit hashes, drill lines verbatim (ARM_A_DRILL and BENCH_DRILL), the ARM_A_PREPARED
line (or the refusal verbatim), capsule id + manifest sha256, units n, job dir, the functions with no unit and why, open
points. Spend is metered by the control plane. Ending on a question counts as a failure. End with
`HANDOFF NOTE: C2a done` or the blocker.
