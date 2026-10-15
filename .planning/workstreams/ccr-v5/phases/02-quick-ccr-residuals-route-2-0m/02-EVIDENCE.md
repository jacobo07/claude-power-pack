# Phase 2 EVIDENCE: Quick CCR residuals

Date: 2026-10-15. Branch `ccr/v5` (worktree `.claude/worktrees/ccr-v5`), HEAD at gate time `44291071c763f88bd100a19cee66297f3d8e6b52`.
Producing commits: 02-01 `6376f589` (driver + breaker test), 02-02 `0930ee2e` (PGO install/verify), 02-03 `097a272e` (RESUMPTION_FILE snapshot).
Goal `ccr`, lease L13 (`ccr:v5`, cap 79,000,000), route 2.0M. Every gate below was re-run by plan 02-04 from the worktree (not quoted from the SUMMARY files).
Shell note: no PowerShell tool was available to the executor, so each shell action ran as `powershell.exe -File <script in %TEMP%>`; exit codes are the python/git exit codes captured inside those scripts.

## Commands

| # | Command (cwd = worktree root) | Exit | Verdict line (verbatim) |
|---|---|---:|---|
| 1 | `python -I tools/test_ccr_driver_breaker.py` | 0 | `DRV_PASS=14/14` |
| 2 | `python -I tools/test_ccr_pgo_install.py` | 0 | `PGOINST_PASS=14/14` |
| 3 | `python tools/test_ccr_pgo.py` | 0 | `CCRPGO_PASS=16/16  threshold=16/16` |
| 4 | `python tools/test_gsd_mission_ccr_a6.py` | 0 | `13 passed, 0 failed` |
| 5 | `python tools/test_gsd_mission_ccr_contract.py` | 0 | `5 passed, 0 failed` |
| 6 | `python tools/ccr_pgo.py verify` (real default dir `C:\Users\User\.claude\ccr\state\pgo`) | 0 | `"ok": true`, `"classes_ok": true`, `"breakeven_ok": true`, `"deflate_live": "deflated"` |
| 7 | `git log --oneline -6` | 0 | `44291071 docs(02-03)...`, `097a272e ccr-v5 p2: commit CCR RESUMPTION_FILE snapshot...`, `fb453fd0 docs(02-02)...`, `0930ee2e ccr-v5 p2: X2 step 5...`, `3b9a60ff docs(02-01)...`, `6376f589 ccr-v5 p2: version GEX44 drive3.sh v3...` |
| 8 | `git diff --name-only 0316acff464e22eb7670aad9739ff3769298bbc8..HEAD -- mods/` (0316acff = `plan_head_before` of 02-01) | 0 | empty output (output file 0 bytes): no file under `mods/` changed |
| 9 | `git status --porcelain` | 0 | only `?? .planning/workstreams/ccr-v5/phases/02-quick-ccr-residuals-route-2-0m/02-CONTEXT.md` (committed by this plan) |
| 10 | `ssh -o BatchMode=yes gex44 "sha256sum /home/kobii/missions/ccr-s3-data/drive3.sh"` (read-only, 2026-10-15T07:39:07Z) | 0 | `9f74c589702a8d600c725fddbaa7825072daf04c071adcb57008c26371571dd7` |

No gate exited 2 (INCONCLUSIVE). Nothing was retried in a different shape. Release: the diff in row 8 is empty, so no CCR mod changed and no `ccr_release.py release` was needed or run.

## Clause 1 - PGO install, DEFLATE read, hold

- Before (from the 02-02 receipt `vault/programs/ccr/stage3/pgo-install-receipt.json`, recorded 07:27Z; it cannot be re-run now because the directory is populated): `verify` exit 1, `dest_exists false`, both probes `UNFORECAST`, `deflate_live no_unit_class`. After install: `verify` exit 0.
- Re-run here (row 6): exit 0; `classes_ok true`; `breakeven_ok true`; bounded-code `MEDIUM` -> `deflated` (unit `bounded-code-worker`, declaration written); lookup `LOW` -> `would_deflate`; `deflate_off` rows both `{}`.
- sha256, recomputed with `Get-FileHash` in this plan, live == committed source for all three files and the directory holds exactly those three names:
  `pgo-classes.json` 14151 B `9815FBC4...682C`; `bounded-code-worker.breakeven.json` 410 B `0F2BF6A0...959F`; `read-only-reviewer.breakeven.json` 264 B `0CD328E2...63FD`.
- DEFLATE hold, both forms (gate `V-PGOINST-HOLD-OFF`, `V-PGOINST-HOLD-BY-REMOVAL`, both PASS in row 2): `CPP_CCR_DEFLATE=off` empties the deflate rows while the same state deflates with it on; removing `pgo-classes.json` gives `rc=1 on=no_unit_class`, off rows empty. Runbook: `vault/programs/ccr/PGO-INSTALL.md` (`V-PGOINST-DOC` PASS).
- The environment of this run has `CPP_CCR_DEFLATE` unset in both the process and the User scope.
- Grade of the clause: **OBSERVED**. Sub-claims:

| Sub-claim | Grade | Basis |
|---|---|---|
| The three files are in the real default directory, byte-equal to the committed sources | PROVEN | `Get-FileHash` here; `V-PGOINST-COPY-VERIFIED` |
| The real `_ccr_contract` and `deflate_unit` read the installed files and return a DEFLATE decision | OBSERVED | `verify` drives the real functions with all mission-state env vars pointed at a temp dir (isolation is enforced by the tool), so it is the real code on the real files but not a real launch |
| DEFLATE is live by default for bounded-code slim launches | OBSERVED | follows from the above plus `V-PGOINST-HOLD-OFF` (on => deflated); no launch was run |
| DEFLATE shrinks a real launch (tokens saved) | UNJUDGED | no live launch measured; Phase 8/10 measure it |
| `CPP_CCR_DEFLATE=off` holds scheduled launches | BLOCKED | an interactive-session variable does not reach Task Scheduler processes. Reason: process-scoped env. Owner step: persist the variable at User scope (`[Environment]::SetEnvironmentVariable('CPP_CCR_DEFLATE','off','User')`) or accept that removing `pgo-classes.json` (verified by `V-PGOINST-HOLD-BY-REMOVAL`) is the only hold that reaches every launcher. Not applied: an Owner decision |

## Clause 2 - GEX44 driver versioned, breaker regression

- Committed file `vault/programs/ccr/stage3/driver/drive3.sh`: 3882 bytes, sha256 `9F74C589702A8D600C725FDDBAA7825072DAF04C071ADCB57008C26371571DD7` (`Get-FileHash` here).
- `MANIFEST.json`: `host_alias gex44`, `remote_path /home/kobii/missions/ccr-s3-data/drive3.sh`, `bytes 3882`, `sha256 == remote_sha256 == 9f74c589...1dd7`, `fetched_at 2026-10-15T07:13:16Z`, `fetched_by ccr-v5 phase 2 plan 01`.
- Fresh remote hash (row 10, 2026-10-15T07:39:07Z, this plan): `9f74c589...1dd7`, equal to the committed file. So the host copy has not changed between the fetch and now.
- Gates in row 1 (all PASS, `DRV_PASS=14/14`): `V-DRV-FILE-VERBATIM`, `EXTRACT`, `OVER-ERR-TRIPS` (over ERR 4500000 -> tripped in real bash), `EXTRACT-IS-PURE`, `HARNESS-POSITIVE-CONTROL`, `STRING-MESSAGE-MEASURED` (string-message line skipped, stream measured 5000000, tripped), `OVER-EMPTY-TRIPS`, `OVER-NUMERIC-CONTROLS` (0 and 4499999 not tripped, 4500000 tripped), `CRASHED-MEASUREMENT-IS-ERR`, `FAILED-INTERPRETER-IS-ERR`, `OUTPUT-DOMAIN` (8 corruption variants, all in `^(\d+|ERR)$`), and three mutants.
- Mutants that went red: `V-DRV-MUTANT-OVER-DROPS-ERR` ("mutant (ERR clause removed) fails the ERR predicate: mutant detected; real text passes it"), `V-DRV-MUTANT-OVER-DROPS-EMPTY` (same for the empty clause), `V-DRV-MUTANT-A4-SHAPE` ("string-message stream -> empty measurement, over() NOT tripped (fail-open); mutant detected").
- Driver bytes were not edited: v3 `over()` is proven as shipped, not re-fixed.
- Grade of the clause: **PROVEN** for the property "the shipped `spent()`/`over()` trip on a string-`message` stream, on an empty measurement and on ERR, and a crashed or failed interpreter yields ERR" (real bash, real extracted functions, 14/14, mutants detected, in this context). Separate claims:

| Sub-claim | Grade | Basis |
|---|---|---|
| Versioned bytes equal the host file | OBSERVED | a hash at two fetch times (07:13:16Z, 07:39:07Z), not a live run of the driver |
| The full driver, on the host, trips its breaker in a run | UNJUDGED | the test sources only `spent()`/`over()`; the loop, call sites, pkill path, RAM hold and phase-cap arithmetic were not driven; the host's bash and python3 versions were not observed |
| A missing or misnamed stream file trips the breaker | BLOCKED (OPEN residual a) | see Open residuals |

## Clause 3 - CCR RESUMPTION_FILE committed on ccr/v5

- Capture record (`%TEMP%\ccr-v5-p2-resumption.sha`, written by 02-03): sha256 `749FF9A92F01746A01CF7DE788CBCABD68ABFB94C39E3B3B2999F14AB78437E1`, 12093 bytes, 113 lines, 2026-10-15T07:31:14Z.
- Re-hashed here with `Get-FileHash`: worktree `vault/programs/ccr/RESUMPTION_FILE.md` = `749FF9A9...37E1`; main-tree copy = `749FF9A9...37E1`. Both equal the capture, so the main-tree file did not move after 07:31:14Z.
- Commit `097a272e`: `git show --stat --format= 097a272e` lists one path, `vault/programs/ccr/RESUMPTION_FILE.md | 54 +++-, 1 file changed, 53 insertions(+), 1 deletion(-)`.
- Main tree untouched by this mission: `git status --porcelain -- vault/programs/ccr/RESUMPTION_FILE.md` there prints ` M vault/programs/ccr/RESUMPTION_FILE.md` (dirty before and after; never staged, committed or reverted from here). This plan only read it.
- `core.autocrlf=true` in the worktree: the hashes above are of working-tree bytes. Compare with `Get-FileHash` on files; do not hash `git show` output.
- Grade of the clause: **PROVEN** for "the current content of the continuation file is committed on ccr/v5" (hash equality in three places, one-path commit). Out of scope and not claimed: the durable-owner seal (Phase 4 defines it), so "continuation is SEALED" is UNJUDGED and belongs to Phase 4.

## Coverage audit (plan table re-checked against what landed)

| Source | Item | Gate or file that landed (line from `Grep` on the test file) | Status |
|---|---|---|---|
| GOAL | X2 step 5 live: files copied, DEFLATE reads them, hold documented | `tools/test_ccr_pgo_install.py`: `V-PGOINST-COPY-VERIFIED` :136, `CONTRACT-READS-INSTALLED` :143, `DEFLATE-ON` :149, `HOLD-OFF` :156, `HOLD-BY-REMOVAL` :242, `DOC` :278; receipt `stage3/pgo-install-receipt.json` | COVERED |
| GOAL | Driver versioned into `vault/programs/ccr/stage3/driver/` | `drive3.sh`, `MANIFEST.json`, `.gitattributes`, `README.md`; `tools/test_ccr_driver_breaker.py` `V-DRV-FILE-VERBATIM` :150 | COVERED |
| GOAL | Regression test: string-`message` line trips the breaker | `V-DRV-STRING-MESSAGE-MEASURED` :241, `V-DRV-MUTANT-A4-SHAPE` :370 | COVERED |
| GOAL | Regression test: empty/ERR measurement trips; prove v3 `over()`, do not re-fix | `V-DRV-OVER-ERR-TRIPS` :189, `V-DRV-OVER-EMPTY-TRIPS` :258, mutants :342 and :356; driver file verbatim | COVERED |
| GOAL | RESUMPTION_FILE current content committed on ccr/v5 | commit `097a272e`; no test file exists for it, verified by hash comparison above | COVERED (by hash, not by a V-gate) |
| REQ | REQ-2 | plans 02-01..02-04 all list it | COVERED |
| RESEARCH | none present | n/a | no items |
| CONTEXT | no locked D-NN decisions; Deferred Ideas: none | `02-CONTEXT.md` read; nothing deferred appears in the plans | no items |
| ROADMAP constraint | EVIDENCE.md with graded verdict, iteration prompt, spend booking, pathspec commits, no push, no main-tree writes | this file; Spend section; commit step | COVERED |
| ROADMAP constraint | Self-hosting via `CCR_WORK_UNIT` | see Self-hosting | UNJUDGED |

No row is MISSING. Every quoted gate name was found in its test file by grep.

## Self-hosting

`CCR_WORK_UNIT` is empty in the environment of this executor, and no unit JSON was supplied by the orchestrator. UNJUDGED: the phase was not run under a compiled CCR work unit; no unit was fabricated.

## Spend

- Session `af436132-9889-4908-972f-0a81204d9776` (the gsd-autonomous coordinator for Phase 2, first record 2026-10-15T06:51:40Z; Phase 1 ran in an earlier session). Processed = input + cache_creation + cache_read + output, summed with `mission_spend.session_tokens` (same rule `goal-settle` uses) over the main transcript plus its six `subagents/agent-*.jsonl` files, measured at 2026-10-15T07:38:07Z: main 7,914,104 + subagents 17,181,888 = **25,095,992**.
- Command: `python tools/mission_spend.py goal-settle --goal ccr --session af436132-9889-4908-972f-0a81204d9776 --measured 25095992`, exit 0.
- Output (verbatim): `{"cap": 79000000, "closed": [], "exhausted": false, "goal": "ccr", "ok": true, "open": 1033575, "reason": "", "recovery": {"lease": "L13", "reserve": 0, "used": 0}, "refused_billed": 0, "remaining": 53904008, "settled": 138414270, "tombstoned": [], "used": 25095992}`. Before the booking `used` was 0 and `remaining` 79,000,000 (`goal-status`, exit 0). No cap was raised.
- Route ratio: 25,095,992 / 2,000,000 = **12.55x**, above the 1.5x stop-loss threshold.
- The ledger had no L13 settle row before this booking, so Phase 1's session was never booked and its ratio is UNJUDGED; "twice in a row" cannot be established from the ledger. This is the first measured breach. The coordinator must apply the ROADMAP rule (a second phase above 1.5x marks BLOCKED); this plan does not decide it and did not mark Phase 2 BLOCKED, since the three clauses are delivered.
- Caveat: the number counts every call's cache_read, so a long coordinator context multiplies it; the 2.0M route is not stated in the same unit in the plan of record. Not resolved here. The booking is a snapshot at 07:38:07Z; calls made by this executor after it (writing this file and the commit) are unbooked and are covered by the next watermark-delta settle.

## Open residuals

(a) **OPEN - `spent()` fails open on absence.** `spent()` prints `0` (the sum of an empty set) when its stream file is missing or misnamed, and for a stream whose every line is a string-`message` line, so `over()` never trips on them. Characterized by uncounted lines in the test: "INFO missing-stream unit -> spent prints '0' (over trips: False)", "INFO all-string-message stream -> spent prints '0' (over trips: False)", "INFO OPEN residual: a unit whose stream file is missing or misnamed measures 0 (not ERR) and is never over the stop". `V-DRV-OUTPUT-DOMAIN` shows the set is wider than those two: five of the eight corruption variants also print `0` (string usage field, null usage, usage as a list, message as a list, empty file); two print `ERR`; a non-JSON line is skipped and the valid line after it is counted (`7`). `over()` itself is proven fail-closed only for ERR, empty and unreadable input. Not patched (the phase brief says prove, do not re-fix). Candidate owner: the next driver revision after Phase 9's CI suite.

(b) **DEFLATE is live by default and the hold does not reach the scheduler.** For bounded-code slim launches DEFLATE is now on wherever a process reads the default PGO directory. `CPP_CCR_DEFLATE=off` set in an interactive session does not reach Task Scheduler processes; only removing `pgo-classes.json` reaches every launcher. Persisting the variable at User scope is an Owner decision, not applied. `long-textual` maps to `bounded-code-worker` but has A3 confidence LOW, so it records `would_deflate` only.

(c) **Main-tree RESUMPTION_FILE is dirty with the bytes ccr/v5 now commits.** Same sha256 `749FF9A9...37E1` in the main tree (` M`) and in the `097a272e` working copy. Phase 3's landing will meet a dirty path whose content equals the incoming content; compare with `Get-FileHash` (autocrlf=true), not with `git show` output. If a foreign pane edits the main-tree file later, the committed snapshot lags it.

(d) **UNJUDGED - DEFLATE saving on a real launch.** No live launch measured here; Phase 8/10 measure it.

## Iteration pass

The universal iteration prompt (read in full at execution; its text is outside the repo and not copied) was applied as an adversarial re-read of the three clauses. Reality check: sources read were the two test files, `drive3.sh` via the test, the 02-0N summaries and the live directory; no premise of the plan was false (the 3 PGO names, `mission_spend.py` and the iteration file existed).

| Question | Measured answer | Result |
|---|---|---|
| Could `V-DRV-OVER-ERR-TRIPS` have returned the other answer? | Yes: `V-DRV-MUTANT-OVER-DROPS-ERR` removes the ERR clause and the same predicate fails on the mutant while the real text passes it | grade kept PROVEN |
| What does a green `DRV_PASS=14/14` not observe? | It sources only `spent()` and `over()` from the file. `V-DRV-EXTRACT-IS-PURE` reports the full driver contains `claude` and `pkill` and the extract does not, so the loop, the kill path and the call sites are outside the proof | recorded as UNJUDGED sub-claim, not upgraded |
| Is residual (a) as narrow as first stated (missing file, all-string-message)? | No: `V-DRV-OUTPUT-DOMAIN` printed `0` for string usage, null usage, list usage, message-as-list and an empty file | residual widened in this file; no new gate added because the phase brief forbids re-fixing and the INFO lines already characterize it |
| Is the PGO "read" a real launch? | No: `verify` runs the real readers with state isolated in a temp dir | clause 1 held at OBSERVED, shrink UNJUDGED |
| Does the installed directory still match after the other plans and gates ran? | `V-PGOINST-REAL-STATE-UNTOUCHED` (3 entries before == after) and a fresh `Get-FileHash` here | PROVEN for identity |
| Is the remote driver hash stale? | A second read-only `sha256sum` at 07:39:07Z equals the 07:13:16Z fetch | OBSERVED, now with two timestamps |
| Did a green result hide a spend problem? | The gates are all green yet the session is at 12.55x the route | recorded in Spend as a measured fact, left to the coordinator's stop-loss rule |

What changed as a result: residual (a) widened; the spend breach recorded; no grade was upgraded and none was downgraded. What stayed open: (a), (b), (c), (d), the unrun full-driver path.
UKDL seed (iteration prompt phase 4) is not written here: the plan scopes this phase's writes to this file and STATE.md, and Phase 11 owns knowledge. Candidate trap for Phase 11: "a shell measurement that sums an empty set reads as zero spend; absence must print ERR" (evidence: this file, residual a).

## Hand-offs

- Phase 3: residual (c); `vault/knowledge_base/ukdl-universal.md` in the main tree carries a foreign writer's bytes (ROADMAP constraint). No `mods/` change in this phase, hence no CCR release is required before Phase 3.
- Phase 4: the seal gate must treat `RESUMPTION_FILE.md` (committed in `097a272e`) as a projection of durable state; this phase only snapshotted it.
- Phase 9 (CI suite): carry `tools/test_ccr_driver_breaker.py` and `tools/test_ccr_pgo_install.py` into the suite; candidate owner of residual (a).
- Phase 8/10: measure whether DEFLATE shrinks a real launch (residual d) and decide residual (b) with the Owner.
- Coordinator: apply the 1.5x stop-loss rule given the 12.55x measurement in Spend; Phase 1 was never booked on L13.
- Phase 11: record the three traps above (empty-set sum reads as zero; interactive env var does not reach the scheduler; dirty-path with identical content on landing).

## Production Reality verdict

| Clause | Grade | Never-upgraded note |
|---|---|---|
| 1 PGO install, DEFLATE read, hold | OBSERVED (file identity PROVEN; reader acceptance OBSERVED; shrink UNJUDGED; scheduler hold BLOCKED with Owner step) | the live claim stays at OBSERVED because no real launch ran |
| 2 Driver versioned, breaker regression | PROVEN for the `spent()`/`over()` fail-closed property; remote identity OBSERVED; full-driver run UNJUDGED; missing-stream case BLOCKED/OPEN (residual a) | the proof covers the extracted functions only |
| 3 RESUMPTION_FILE committed | PROVEN (hash equal in worktree, main tree and capture; one-path commit); seal UNJUDGED (Phase 4) | |
| Self-hosting via CCR_WORK_UNIT | UNJUDGED | no unit supplied |
| Spend booked | PROVEN as booked (goal-settle exit 0, `used` 25,095,992); 12.55x the route, stop-loss decision left to the coordinator | snapshot at 07:38:07Z |
