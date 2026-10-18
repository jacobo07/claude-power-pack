# Mission economics repair + ORCA DWS rows 70/65 self-host canary (2026-10-17)

Status: AWAITING ONE OWNER APPROVAL. Inline copy in chat is the approval surface; this file is the backup.

## 0. Reality check (iteration protocol, phase 1)

| Brief premise | Measured | Verdict |
|---|---|---|
| Worker forecast ~8.3M | `token_estimate_basis`: `(spent 1,664,910 + headroom 15,000,000 [mission-budget-defaults.json clamp]) / trip ratio 2 = 8,332,455` | FALSE. No forecast existed; 8.3M is a default ceiling divided by 2 |
| Breaker stops at ~2x forecast | trip at 2 x 8,332,455 = 16,664,910 = the same default ceiling; hold wait type `CAPITAL_EXHAUSTED`, spent 17,032,240 | A ceiling hit wearing forecast words |
| Hard authority remains | No Owner-declared authority on the record; `price_lease` (mission_recovery.py:395) treats "ratio x estimate" as hard authority when none is declared | Default policy ceiling exhausted (-367,330). No Owner authority ever existed |
| Runtime asked Owner inline/release/stop | Runtime packet asked only `authority --tokens <NEW_TOTAL>`; the topology menu was written by this session | Owner topology decision count = 1, caused by me |
| R: may be unavailable | R: NTFS 535,752,704 B, `R:\hwf` present | AVAILABLE |
| Rows independent of each other's resources | Both rows are laptop Electron legs; laptop free RAM 3.0 GB vs 6 GB admission rule | Both WAIT_RESOURCE(ram) now |

## 1-3. Current ORCA reality, mission/worker, Phase 2 proof

- Worktree `C:\Users\User\Apps\orca-rb-live-wt`, branch `rb-live`, HEAD = origin `orca-x/dws-rebaseline-live` = `0595f9e758`. Dirty: untracked row-70 spec (mine, fixed this session) + session artifacts (never committed). No other writer in this worktree.
- Mission `m-3f1feb210a74`: state RUNNING with owner_hold kind=cost, recovery OWNER_BOUNDARY, epoch 1, model sonnet. Worker `4116d0e6` DEAD (pid gone). Mission identity intact.
- Phase 2 proof: commit `0595f9e758` = spec `hwf-two-host-mission-locality.spec.ts` + matrix + `docs/dws/live-2026-10-17-rows-24-34-evidence.md`; live run `rbl\d4-ev-r24h-20261017-213756` PLAYWRIGHT_EXIT=0, WITNESS_UNCHANGED=True. Row 34 PASS. Reused, never rerun.

## 4. Row 24 PARTIAL contract
Done = "hydrated node preferred, measured". Residual obligations: R24-a freshness window not measured; R24-b the only prepared environment was the laptop (no GEX44-prepared case). Independent of rows 70/65; stays PARTIAL.

## 5-7. Row 70, row 65, resource R
- Row 70 done: "a working set translates through projectId to another host; each pane reattach/resume/restart/unavailable". Live run r70a FAILED (store-written projectId re-derived by `normalizeHydratedProjectHostSetupProjection`); spec now uses laptop + GEX44 replicas sharing root `a168f40`, no store write; tsc/oxlint/oxfmt clean. Spec observes restart + unavailable; reattach/resume are NOT covered (spec header says so). PASS requires an observed reattach or resume; otherwise row 70 is restated truthfully (real-SSH restore + remote Open) and stays PARTIAL with that residual named.
- Row 65 done: fast-forward + disk-full + disconnect + stale stay failures. Spec exists (`hwf-two-host-replica-pair.spec.ts -g disk-full-and-disconnect`), never run live. Needs R: (AVAILABLE) + RAM.
- Resources: `R:` AVAILABLE (VHD mounts idempotently via `rbl\mount-smallfs.ps1`, elevated; after reboot it is a human-only action). `ram.free_gb>=6` WAIT. GEX44 reachable (r70a provisioned and tore down cleanly).

## 8-10. Authority, forecast, breaker (as they are)
- Authority: none declared by the Owner. Default ceiling 16,664,910, exhausted. Settled 17,032,240. Reserved 0. Recovery reserve fraction 0.15 (`price_lease`).
- Forecast: none for the work; envelope fallback only. `phase_lease.py` (WARN 1.2 / HARD 1.5), `cost_to_completion.py` (claim-graph residual compiler) and `ccr_pgo.py` (work-class profile with quantiles, heldout, anomaly) exist and were NOT wired to this mission.
- Breaker: `_cost_breaker` (gsd_mission.py:1706) -> `mission_spend.judge` with DEFAULT_TRIP_RATIO 2.0 -> `set_owner_hold(kind=cost)`; `owner_wait_type` regex maps any "cost breaker" text to CAPITAL_EXHAUSTED.

## 11. Root-cause matrix (Phase 2 = 17,032,240 processed)
Measured from the worker transcript (100 model calls, single file, no subagents):
| Cause | Tokens | Share |
|---|---|---|
| Estate context floor: first call already 106,776 tokens (route-floors.json top-level-worker floor 110,835) x 100 calls | ~10.7M | ~63% |
| Context growth inside the turn (106k -> 216k, one compaction at 19:40:38) | ~6.3M | ~37% |
| Of which cache_read | 16,617,833 | 97.6% |
| Output | 53,782 | 0.3% |
By activity window: r24d-g failing runs 5.70M (31 calls); r24h pass + commit 8.21M (50 calls); r70a 1.46M (7 calls); start 1.66M (12 calls). Live attempts: 8 for row 24/34 (7 failed), 1 for row 70 (failed). Tools: Grep 45, Read 40, Edit 25, PowerShell 23.
Causal statement: cost = calls x carried context. Unattended mode is not the cause; the cause is ~107k fixed context per call plus unbounded growth to 216k, multiplied by a retry loop of 8 live attempts with no attempt cap. The ceiling was never a forecast, so "2x surprise" is not a measurement of forecast error.
Note: runs r24a-c (18:29-18:41) predate this transcript and belong to the held mission m-0a2b4dad289b; Phase 2's true total is 17.0M plus an unmeasured share of that mission's 10.7M.

## 12-13. Type separation (the fix)
Three types on the record, never derived from each other:
- `authority`: {kind: OWNER | DEFAULT_POLICY, tokens, source}. Only OWNER is hard authority. DEFAULT_POLICY exhaustion = PREEMPTED_REFORECAST, not CAPITAL_EXHAUSTED.
- `forecast`: per phase, from the work-class profile (`ccr_pgo.forecast`) or the claim graph (`cost_to_completion`); labelled UNKNOWN when neither exists, never synthesized from a ceiling.
- `breaker`: phase lease ratios. Trip = RECOMPILE (seal, reforecast residual, re-admit), not Owner.
Mission state vs worker state: worker DEAD is a liveness fact; mission state comes from obligations + authority + resources.

## 14-16. Obligation graph, resource graph, actionable frontier
| Obligation | Depends on | State now |
|---|---|---|
| O-34 row 34 | - | CLOSED PASS (0595f9e758) |
| O-24 row 24 residual R24-a, R24-b | GEX44-prepared setup, freshness clock | OPEN, PARTIAL, not in this tranche |
| O-70 row 70 live leg | ram.free_gb>=6, gex44.ssh, spec fixed | WAIT_RESOURCE(ram) |
| O-70r row 70 reattach/resume evidence | live provider session on target (may need OD-1 credential) | CLASSIFY first (deterministic grep), then ACTIONABLE or WAIT_OWNER(OD-1) |
| O-65 row 65 live leg | ram.free_gb>=6, volume R:, gex44.ssh | WAIT_RESOURCE(ram) |
| O-close matrix restate + push | O-70, O-65 settled | BLOCKED on siblings |
Frontier today: empty of executable legs (RAM); PP repair stages are executable. The RAM watcher wakes O-70 then O-65.

## 17-21. Work-class profile, envelopes, reconciliation, calibration, surprise
- Work class `DWS_LIVE_LEG` (new profile file under the existing ccr_pgo store). Fields: calls, avg/max context, processed, live attempts, attempt outcomes, floor, host topology. Seed sample n=1 (Phase 2: 100 calls, 170k avg, 8 attempts, 17.0M). Quantiles are NOT claimed from n=1; forecasts carry `confidence: LOW (n=1)` until n>=3.
- Envelopes: mission authority -> phase lease (phase_lease.make_lease) -> attempt cap (3 live attempts per row, then the row is settled as FAIL/NOT_RUN with evidence instead of iterating).
- Post-unit reconciliation: on a sealed phase, append the actual to the profile BEFORE the next lease is made; record forecast/actual/variance/cause as a ledger row.
- Calibration error = |actual-forecast|/actual per phase; surprise = actual > forecast P80. Both computed from ledger rows; first value after row 70.

## 22-24. Breaker policy
Multi-stage on the phase lease: NORMAL < WARN(1.2) -> profile update; RECOMPILE at HARD -> seal, reforecast residual, re-lease inside OWNER authority with no Owner prompt; WAIT_CAPITAL only when the compiled residual does not fit OWNER authority; TOMBSTONE only on OWNER authority exhaustion. Variance-aware ratios are deferred honestly: with n=1 any variance is fiction. The hook is a profile field (`hard_ratio` from the profile's P95/P50 once n>=3); until then the fixed 1.5 lease ratio is the explicit fallback.

## 25-27. Capital deflation, residual compiler, topology compiler
Deflation applied before the ask:
1. Deterministic runner for live attempts: `d4-live.ps1` plus a marker parser writing `verdict.json` (PASS/FAIL/HARNESS_FAILED + markers). No model call while a leg runs.
2. Attempt cap 3 per row bounds P95.
3. Fresh boundary per row with a compact packet (no 17M history) and autocompact 150k instead of 250k: cuts average carried context from ~170k toward ~130k.
4. Proof reuse: row 34, row 16 grouping, R: provisioning are reused, never rerun.
Residual (ORCA OPEX), per row: PASS path ~12 calls x ~130k = 1.6M; each failed attempt triage ~8 calls x ~135k = 1.1M.
| Row | P50 (1 fail) | P80 (2 fails) | P95 (3 fails, cap) |
|---|---|---|---|
| 70 | 2.7M | 3.8M | 4.9M |
| 65 | 2.7M | 3.8M | 4.9M |
| Closeout (matrix restate, push, resumption) | 0.8M | 1.0M | 1.2M |
| Total | 6.2M | 8.6M | 11.0M |
Confidence LOW (n=1 work-class sample; attempt failure base rate taken from Phase 2's 7/8). Topology per unit: live attempt = DETERMINISTIC_RUNNER; triage/evidence/commit = one fresh sonnet worker per row (CLEAN_MODEL_WORKER), not this session (this session's context is far above the 107k floor, so each inline call costs more).

## 28. Host locality
Phase 2 measured: the hydrated low-memory host was preferred over the roomier unprepared one, with a no-setup control. Profile field `prepared_state` outranks `free_memory` in host scoring for setup-bound work. For these legs the laptop is fixed (two-host client) so locality chooses GEX44 roots `/tmp/orca-hwf-p<NN>-*` that are already seeded.

## 29-30. AMR executor replacement, resource wakeup
- AMR: on worker death with an actionable obligation and OWNER authority remaining, compile a successor packet (residual obligations only) and relaunch; the invalid state (open mission + dead worker + actionable obligation + authority + no executor) becomes a sweep incident.
- Resource wakeup: obligations carry typed `requires` (`ram.free_gb>=N`, `volume:R:`, `ssh:gex44`). The existing 5-minute sweep evaluates them deterministically (no model). Unmet -> WAIT_RESOURCE with the measured value; met -> RESOURCE_AVAILABLE ledger row -> the obligation joins the frontier and the mission relaunches. An unmeasurable resource is UNKNOWN, never AVAILABLE. A blocked obligation never holds an independent sibling.

## 31-32. Canaries
Row 70: wake on RAM -> deterministic run `d4-live -Tag r70b -Specs tests/e2e/hwf-two-host-continue-here-ssh.spec.ts -SeedVerb none -PathEnv none` (run-file carries `--seed --local-seed` paths) -> verdict.json -> worker writes evidence, restates row 70 (PASS only with an observed reattach/resume, else PARTIAL with the residual), micro-commit, ff push.
Row 65: wake on RAM + R: -> `ORCA_HWF_SMALL_FS_ROOT=R:\hwf`, `-g disk-full-and-disconnect` -> same pipeline. Teardown REMAINING=0, PROC_COUNT=0, witness unchanged on every run.

## 33-34. Reprofile and drift RCA
After each row: profile n+1, calibration error, surprise flag, ledger receipt. The Phase 2 RCA in section 11 is recorded as an economic incident correction (the ESTIMATE_RATIO incident is relabelled DEFAULT_CEILING_EXHAUSTED with this attribution).

## 35. Mode by workstream
Reality delta EXECUTION (done). Breaker audit EXECUTION (done above). Type separation EXECUTION. Mission state machine EXECUTION (extend existing states; add PREEMPTED_REFORECAST, WAIT_RESOURCE). Obligation graph EXECUTION (record field, no new store). Resource graph/wakeup EXECUTION. Work-class profile EXECUTION (extend ccr_pgo). Calibration EXECUTION. Variance-aware breaker PLAN only (deferred until n>=3). Topology compiler EXECUTION as a per-unit route rule in mission_recovery candidates, not a new module. AMR continuation EXECUTION. ORCA self-host EXECUTION. CBR EXECUTION after proof. No ULTRA: no foundational owner conflict; every owner exists.

## 36. Micro-commits (PP, private-index commits; another session is committing on the same branch)
1. authority kind separation + owner_wait_type DEFAULT ceiling -> PREEMPTED_REFORECAST (tests red first)
2. auto envelope labelled default ceiling, never "estimate"; incident text corrected
3. typed resource requires + WAIT_RESOURCE + wake (tests: sibling independence, wake, UNKNOWN != AVAILABLE)
4. post-unit reconciliation into a DWS_LIVE_LEG profile before next lease (test: forecast changes before admission)
5. attempt cap + deterministic verdict parser (rbl, outside both repos)
6. AMR invalid-state incident + successor relaunch (test: dead worker + actionable + authority -> prepared successor)
7. knowledge: vault/UKDL/FIOS entries; CBR promotion after canary proof
ORCA: one commit per row (spec + matrix + evidence doc), ff push to orca-x/dws-rebaseline-live.

## 37. Infrastructure CAPEX (PP repair), fresh sonnet boundaries
| Stage | Lower bound | P50 | P80 | P95 | Calls | Avg ctx | Conf |
|---|---|---|---|---|---|---|---|
| M1 authority/forecast type separation (commits 1-2) | 1.2M | 2.4M | 3.6M | 5.0M | 18-30 | 130k | LOW |
| M2 resource requires + wake + sibling (3) | 1.2M | 2.4M | 3.6M | 5.0M | 18-30 | 130k | LOW |
| M3 profile + post-unit reconcile + attempt cap (4-5) | 0.8M | 1.6M | 2.4M | 3.4M | 12-20 | 125k | LOW |
| M4 AMR invalid-state + relaunch (6) | 0.8M | 1.6M | 2.4M | 3.4M | 12-20 | 125k | LOW |
| M5 knowledge/UKDL/CBR (7) | 0.4M | 0.8M | 1.2M | 1.6M | 6-10 | 120k | MED |
| Total | 4.4M | 8.8M | 13.2M | 18.4M | | | |
Hard authority requested = P80 / (1 - 0.15 reserve) = 15,500,000.

## 38-39. ORCA OPEX and capital packet
Current ORCA authority: OWNER none; DEFAULT ceiling exhausted (-367,330). Residual P80 8.6M (section 27). Requested = 8,600,000 / 0.85 = 10,100,000, set on mission m-3f1feb210a74 as OWNER authority (`gsd_mission.py authority --mission m-3f1feb210a74 --tokens <spent+10,100,000>`), released by the runtime only when RAM admits a row.
Combined new authority: CAPEX 15,500,000 + ORCA OPEX 10,100,000 = 25,600,000 processed tokens.

## 41. Return-to-Owner conditions
OWNER authority exhausted after recompilation; R: missing after a reboot (elevated mount is human-only); OD-1 credential needed for a reattach/resume leg; RAM never reaching 6 GB within 24 h (the watcher reports it once, not repeatedly); a product bug whose fix changes scope; any GEX44 production unit (`orca-dws-serve.service`, mission m-07a78fbae3c7) would be touched.

## Separate (not part of this approval)
PP branch `feature/knowledge-acquisition` is 46 commits ahead of origin, including other sessions' commits (latest 0fdb36bc decision-plane by another writer). Pushing it is that branch's own decision, recorded here only so it is not lost; ORCA recovery does not depend on it.

## Approval (Owner, 2026-10-17 ~22:45 local): "aprobado 40M"
- Granted 40,000,000 processed tokens against plan sha256 dcfbd3784a7182e871def7a8197b95b9d689e9403019b693a7199de2894ef24f (requested 25,600,000).
- Allocation: CAPEX (PP repair M1-M5) 15,500,000. ORCA OPEX (rows 70/65 + closeout) 10,100,000. Unallocated programme reserve 14,400,000: drawn only after a logged recompilation shows a stage's P80 exceeds its allocation.
- ORCA authority is written to m-3f1feb210a74 (authority_tokens = 17,032,240 + 10,100,000 = 27,132,240) only after M2 lands, so the sweep cannot relaunch the dominated /gsd-autonomous topology before resource admission exists.
- Topology chosen by the runtime: one fresh sonnet subagent per PP stage with a compact packet; live legs by deterministic runner.
## O-70r classified (2026-10-17 ~22:45, deterministic source read)
- Dispositions come from planContinueOnHost (src/shared/project-working-set-host-translation.ts:207-235): reattach needs pane.presence 'live-here', resume needs capability 'exact-resume' + resumeOnOpen. Presence is the LIVE AGENT SESSION reading (src/main/agent-hooks/live-agent-session-presence.ts), not a plain PTY.
- reattach: ACTIONABLE with a new leg (an agent process live on GEX44 in the target pane; row 59 launched claude there without a model turn). Not in the current spec.
- resume: WAIT_OWNER(OD-1): needs a provider session created by a real model turn on GEX44.
- Consequence: the current row-70 spec can at most move row 70 to real-SSH restart+unavailable evidence; PASS needs the reattach leg; resume stays named residual under OD-1.
- Deterministic runner ready: rbl\run-leg.ps1 (admission ram/electron/volume -> d4-live -> leg-verdict.py). Verdict reader verified on r24h/r61c PASS, r70a/r24g FAIL, wrong-marker HARNESS_FAILED; admission probe returned WAIT_RESOURCE (ram 3.05<6) and launched nothing.
## Self-host step (2026-10-17 ~23:15)
- PP M1 203e8e26 (default envelope != Owner authority; recompile under authority) verified OWNER_HOLD 45/45. PP M2 142cf8ea (typed requires, WAIT_RESOURCE, sweep wake, sibling independence) verified RES 17/17; real probes on this laptop: ram 5.57 GB, R:\hwf True, Q:\nope False, electron 0.
- m-3f1feb210a74: authority_tokens 27,132,240 (OWNER, Owner "aprobado 40M"); requires O-70 {ram>=6, no electron}, O-65 {ram>=6, R:\hwf, no electron}. Cost hold kept ON on purpose: the row-70 live attempt is executed by the deterministic watcher (rbl\leg-watch.ps1 -> run-leg.ps1, background), and lifting the hold now would put a second executor on O-70. Release after the watcher's verdict, for settle/triage only.