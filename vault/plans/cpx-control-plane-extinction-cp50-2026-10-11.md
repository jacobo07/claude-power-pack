---
covers: [cpx, control-plane-extinction, rule-router, cp50-c2, c2c-fix, c2b-job3, c3, output-budget-admission, scarce-job-readiness]
status: AWAITING_OWNER_APPROVAL
---

# CPX: control-plane extinction + CP50-C2 continuation, 2026-10-11 (fresh pane)

Approval surface is the chat. This file is the durable backup.

## 1. Reality delta (measured, read-only)

| Fact | Value | Source |
|---|---|---|
| C2c-fix mission m-ae80353974b4 | HALTED, 1 iteration, max-cycles 1. No relaunch is possible | `gsd_mission.py status` |
| C2c-fix receipt | PARTIAL. Trim landed in wt_cp50_c2 runner_lib.py:1472, V-CAND-DIFF-TRIMMED PASS, BATCH 74/74, drill 10/10. Prepare NOT run | gen3/C2c-fix-receipt.md, PP 147115b0 |
| C2c residual 1 (2 FAIL test_candidate gates) | Pre-existing: TRF W1 reproduced the same 2 FAILs on clean 3c86ae2. `wt_cp50_c2\.planning` now exists | tennis-rf/WU-W1-receipt.md:28-30 |
| C2c worker 3cf66819 | 799,548 processed, 8 calls. Lease 750,000 still OPEN (unsettled) | goal-autopsy, session-budget json |
| Goal cp50-c2 | cap 14,000,000; used 9,613,176 (settled 8,863,176 + open 750,000). Remaining 4,386,824, or about 4.34M after settle | `mission_spend goal-status` |
| Coordinator cost in the Goal ledger | `panes_processed: 0`. The 37.5M pane is invisible to the programme | goal-autopsy |
| Phase-7 slots | 4 total (run plan D4); 2 spent, 0 productive, 2 failed on infrastructure, 2 remaining | cp50-run-plan:54, C2b*/receipts |
| Job 3 authority | ALREADY COVERED: run plan APPROVED (Owner "y" 2026-10-09, D4 cap 4 + C2 pilot scope = arm A, draw 1-5). The "ask y" in C2-RESUMPTION:29 was procedural | cp50-run-plan:3,26,39,54 |
| TRF programme (goal tennis-rf 55M, Owner y 2026-10-11) | LIVE zero-model chain (PP-TrfChain-Tick, 10 min). W1 DONE (fa8aaf0: CURRENT_CAPSULE refusal at stage.send, source lint, .ksr_vault EOL fix). W4 residual running (m-eee2183689af). W2 = Fan-Out Readiness Certificate, not yet armed. W8 = Tennis reforecast measured ON TENNIS | tennis-rf/PROGRAMME.md, chain tick log, master plan section 5 |
| CROSS-PROGRAMME DEFECT | wt_tennis_rf runner_lib.py:1472 still runs `shutil.copyfile(fn.diff.json)` (full report). TRF W5 would repeat job 2's OUT > 20 MB failure. W2's certificate scope has no output budget | grep runner_lib.py |
| econ-succession A1 | AWAITING_OWNER_APPROVAL. Owns control-plane economic role, CONTROL_PLANE_CHARGED_TO_PRODUCTIVE_GOAL, and Owner authority (OCA packets) | vault/plans/econ-succession-2026-10-11-A1-same-pane-capital.md |
| Status surface | `gsd_mission.py status` dumps 6,168 lines for every mission and rejects a mission-id filter, which is resume rent | this scan |

## 2. Rule routing (D-rows, read by ToC grep and targeted line ranges, not linearly)

| Item | Why relevant | Operative requirement | Machine owner today | Reachable? | Action |
|---|---|---|---|---|---|
| D21 Tennis | CP50 measurement was its activation criterion | Measured cost per function | TRF W5 and W8 now measure on Tennis | YES (TRF chain) | Feed C3 to TRF W8 as a Resort cross-check. No parallel forecast |
| D22 cost rule (l.1042) | Coordinator panes were 49% of 57.2M | Fresh pane that arms and ends | none (prose) | NO | Promote to governor (R2) |
| D23 D-05 (l.1089-1092) | 25.36M / 109 calls vs a 2.0M forecast | Hard-cap the coordinator per phase (1.0M); measure per-call cost first | none (prose) | NO | Promote to governor (R2) |
| D24 W3 | Holds/supersession reconciliation | TERMINAL_PROVEN vs UNKNOWN_RESERVED | gsdx_chain tick already settles (tick log `settled:`) | PARTIAL | KEEP_PARKED (section 6) |
| D25 item 1 | GEX44 goal admission | Bind and settle GEX44 workers | n/a: CP50 uses GEX44 for compute jobs only, no model | NO_WORK | Account jobs in the slot ledger |
| D26 K6 | Supervisor renews non-DONE workers | No blind second cycle | ce-lifecycle-v3; chain side fixed 5e835a8a | PARTIAL | Scarce unit: max_residuals 0 + job-key idempotency in stage.send |
| D26 K7 | Admission overprices about 2.8x | Calibrate | ce-lifecycle-v3 | PARTIAL | Record est/actual per unit (C2c: 1.0M target vs 0.80M actual) |
| D14 | Scope-preserved cost comparison | Equal proof scope old vs new | none | n/a | Applied as a constraint on C3 |

Why the old pane had to discover these by hand: the coordinator rule is a UNIVERSAL rule filed as prose inside OTHER programmes' rows (cost-collapse, EDD). No code reads deferred-backlog.md (zero hits in modules/gsd_x). Nothing keys a row to a goal, root or work class.

## 3. Root-cause matrix

| Class | Verdict | Evidence |
|---|---|---|
| CONTROL_PLANE_TOKEN_INCIDENT | CONFIRMED, recurring x3 | 37.5M/207 (CP50), 27.97M/57.2M (D22), 25.36M/109 (D23) |
| UNREACHABLE_INSTITUTIONAL_INTELLIGENCE | CONFIRMED | Rule exists only as backlog prose |
| BACKLOG_ROUTING_MISSING | CONFIRMED | No indexer or consumer |
| CONTEXT_CARRY_RENT | CONFIRMED | About 180K per call |
| RESUME_RENT | CONFIRMED (status surface), PARTIAL (C2-RESUMPTION is 3 KB but chains to the backlog) | 6,168-line status dump |
| OWNER_CONTEXT_ROTATION_MECHANICS | PARTIAL | ASER auto /clear is live; why it did not cap 62e915d9 is UNKNOWN (measure in R2) |
| PROSE_HANDOFF_RUNTIME_DEPENDENCE | CONFIRMED for CP50, REJECTED for TRF | "Start: read this file" vs chain.json |
| MODEL_MONITOR_LIFECYCLE | CONFIRMED for CP50; the fix already exists | gsdx_chain tick runs TRF/dgl/gsdx; CP50 was never put on it (the real root cause of the 37.5M) |
| SCARCE_JOB_PREFLIGHT_MISSING | CONFIRMED in wt_cp50_c2, PARTIAL overall | W1 fix lives only in wt_tennis_rf; W2 not built |
| OUTPUT_SIZE_ADMISSION_MISSING | CONFIRMED everywhere, live risk to TRF W5 | runner_lib.py:1472 in wt_tennis_rf |
| OWNER_REAUTHORIZATION_REDUNDANCY | CONFIRMED | run plan D4 vs C2-RESUMPTION:29 |
| MANUAL_RECONCILIATION_TAX | PARTIAL | 750K lease open after HALT because no tick watches cp50-c2 |
| ADMISSION_CALIBRATION_DRIFT | CONFIRMED (K7) | 1 local sample at 0.8x |
| FIOS_DUPLICATE_REPROCESSING | UNKNOWN | Not measured; measure before acting |

## 4. Owner map

Rule routing: IMPLEMENT the small piece (`tools/rule_router.py`, an index built from `## Dnn` headings plus one `Applies-when:` line per row for goals, roots, programmes and work classes), then CONNECT it into gsdx_chain arm so routed rows land in the packet header and the arm record.
D22/D23 coordinator cap: EXTEND `mission_spend session-declare` with role=coordinator and a 1.0M cap.
Control P&L: EXTEND goal-autopsy/programme-status (panes_processed exists, today 0) by attributing arming panes.
Owner authority and per-goal control-plane isolation: econ-succession A1 owns them. CONNECT; do not duplicate.
Event lifecycle: ALREADY_DONE (gsdx_chain + tick). CONNECT CP50.
Epoch rotation: ACTIVE (ASER); a chain removes the need to coordinate.
Structured continuation: chain.json + receipts are the state. C2-RESUMPTION becomes a generated projection (RETIRE from the normal path).
Readiness certificate: PARTIAL (TRF W1 DONE, W2 pending). Port W1 to the cp50 tree, and give W2 the output budget.
Trim: DONE in wt_cp50_c2 (uncommitted, patch 147115b0); missing in wt_tennis_rf.
One-cycle: EXTEND (scarce unit max_residuals 0; stage.send refuses a reused job key).
D21 reforecast: NO_WORK beyond feeding C3 (TRF W8 owns it).

## 5. Execution topology (self-hosting: no long coordinator)

This pane self-declares a coordinator cap of 1.5M (including this scan), arms two chains on the existing gsdx_chain substrate, amends one TRF packet, and ENDS. No Monitor, no waiting.

Chain `cpx` (new goal cpx, root = PP worktree `.claude/worktrees/cpx`):
- R1 Rule router + canary: arming a cp50-c2 unit surfaces D21/D22/D23/D24/D26 rows without materializing the backlog. Test V-RR-*.
- R2 Control-plane P&L + CONTROL_PLANE_TOKEN_INCIDENT detector + coordinator cap (D22/D23 promoted). Regression canary: 37.5M vs 8.6M must fire. Also a per-mission `status --mission` filter and the C2-RESUMPTION generator.
- R5 Decisions + evidence: D24 NPV, D26 calibration rows, FIOS duplicate-cost measurement (optimize only if material).
- R9 KV/FIOS/UKDL/CBR promotion + final handoff (after the cp50 chain's C3).

Chain `cp50-c2` (existing goal, root wt_cp50_c2):
- R3 C2c residual + readiness: settle 3cf66819 (799,548); baseline-compare the 2 FAIL gates; port W1 fa8aaf0; add output-budget admission (sum of per-unit .o + trimmed diff + log ceiling <= 20,971,520, else NOT_READY:OUT_BUDGET); job-key exactly-once; `arm_a prepare --first 1 --last 5`; verify CURRENT_CAPSULE + TRIM_CALLS. Replay the job-2 directory: it must refuse. Write the readiness certificate.
- J3 C2b job 3 (Phase-7 slot 3 of 4): sent only with a valid certificate and with no TRF prepared-but-unsent job holding the shared CURRENT_CAPSULE. Exactly one send, max_residuals 0. Repatriate, judge, records to `cp50\c2b_records_1_5.jsonl`.
- C3 Projection from valid records only: productive cost / repair CAPEX / control tax / GEX44 jobs / proof / uncertainty kept separate (D14 scope-equal).
- D21 feed: write the C3 handoff into TRF's inputs for W8.

TRF amendment (pre-arm, PP file only, no writes into wt_tennis_rf): WU-W2.md gains (a) port the trim fix and (b) output-budget admission as a certificate check.

Job 4 stays in reserve. It is used automatically only if job 3 fails for an infrastructure cause that has since received a local regression gate. Never after an unexplained failure.

Mode: ULTRA-PLAN = this scan only. R1/R2 = a short PLAN inside the packet, then EXECUTION. Everything else = EXECUTION.

## 6. D24 NPV: KEEP_PARKED

CAPEX for W3 is about 4-5M (W1b 4.5M, W2 5.1M routes). The recurring tax it removes is already near zero wherever a chain tick runs (ticks settle on terminal). The tax measured here is one open 750K lease, which costs one CLI call. That tax is caused by CP50 not being on a chain, and R3/the chain fixes it. Reprice trigger: 2 or more UNKNOWN holds per week across chain programmes.

## 7. Token budget (processed tokens)

| Workstream | P50 |
|---|---|
| Scan + plan (spent, this pane) | 0.6M |
| R1 rule router | 1.2M |
| R2 control P&L / governor / status filter / projection | 1.9M |
| Chains + ticks + TRF amendment (this pane) | 0.4M |
| R3 C2c residual + readiness + output budget | 1.8M |
| J3 job-3 worker + measurement | 1.5M |
| C3 + D21 feed | 0.8M |
| R5 D24/D26/FIOS | 0.5M |
| R9 KV/UKDL/CBR + handoff | 0.8M |
| Recovery reserve | 2.0M |

SEMANTIC LOWER BOUND 3.5M · LOWER 7M · P50 9.5M (11.5M with reserve) · P80 13M · P95 16.5M · HARD AUTHORITY 18M. Confidence medium-low: one calibration point (0.8x), K7 says the estimator overprices about 2.8x. Meta-optimization tax (R1+R2+chains) is about 3.5M = 37% of P50; cap 40%, above which R2 stops at the detector and the cap.
Goals: cpx = R1, R2, R5, R9 (hard 9M). cp50-c2 = R3, J3, C3 (remaining about 4.34M, +2M reserve raise -> cap 16M).
Historical baseline (not a forecast input): coordinator 37.5M / 207 calls / about 180K per call vs workers 8.6M; 2 Phase-7 slots spent, 0 records.

## 7b. Execution state after Owner "y" (2026-10-11, pane 3b4f4757)

- DONE: goal cpx declared (cap 9,000,000, root .claude/worktrees/cpx, branch cpx/main @ c68383ba); pane self-cap
  session-declare stop 1.5M.
- The self-cap TRIPPED at 4,943,171 processed (the scan alone, about 60 calls at about 80K context): the scan estimate
  of 0.6M was wrong by about 8x. First live measurement for R2: a fresh coordinator's scan costs about 5M, not 0.6M.
- On disk, NOT committed: vault/programs/cpx/{WU-B0.md, chain.json, chain_tick.ps1} (B0 = bootstrap unit that arms
  everything else; see its packet).
- NOT done: task PP-CpxChain-Tick (first registration failed: TRF task action has an empty WorkingDirectory; the
  retry was blocked by the session budget breaker). Without it B0 never arms.
- NOT done: settle 3cf66819 (799,548), cp50-c2 cap raise, TRF W2 amendment: all are B0 steps.
- Next exact action: register the task without -WorkingDirectory (clone PP-TrfChain-Tick's action with
  Arguments -replace 'tennis-rf','cpx'), commit vault/programs/cpx (pathspec). The next tick then arms B0.

## 7c. Amendment A1 (Owner, 2026-10-11): REA-assisted arm + recon-factory rows through D26

- REA premise checked against facts in hand: TRF W4 already ran the REA-Tennis canary today -> REJECT for native PPC
  (`vault/programs/tennis-rf/REA-DISPOSITION.md`: rea 6.3.0 CLI hangs importing dist/cli.js on Win11/Node 24; no DOL or
  ELF32-PPC lane in dist/). Upstream issue drafted, not filed. Sovereignty gate result: evidence plane = KEEP_CPP/WRAP
  (DTK + m2c + Ghidra 12.1.2 headless PowerPC:BE:32), REA = EXTEND_UPSTREAM. Revisit when upstream ships a PPC lane.
- New unit R6 (chain cp50-c2, before J3): deterministic per-function evidence dossier (instructions, m2c pseudocode,
  callers/callees, xrefs, SDA/data refs, Resort-shape donor) with a content-addressed cache keyed by binary sha256 +
  function address (minimal Binary Semantic Genome / Semantic Build Cache). No model calls. Done = dossier for draw 1-5
  plus a size per dossier and a cache-hit drill.
- J3 becomes two arms on the SAME Phase-7 slot (no extra job): arm A current pipeline vs arm A+dossier, per function:
  tokens, provider context, model calls, discovery calls, evidence retrieved without a model, proof, wall time, verdict,
  reusable knowledge written. C3 reports both arms separately and the model-needed fraction.
- D11-D19: NOT executed wholesale (D14/D20 sequencing guards are binding). Each gets one evidence-gated slice only when
  C3 + TRF W6/W7 show falling marginal verified cost; R5 writes that admission table. D26 resumes only on Owner activation
  after C3. Tennis Scope A/B unchanged; D21 reforecast stays TRF W8, fed by C3 (both arms).

## 8. Approval

"y" authorizes: declare goal cpx hard 9M; raise cp50-c2 cap 14M -> 16M; two chains + tick tasks; the TRF W2 packet amendment; pathspec commits on feature/knowledge-acquisition (no push); Phase-7 job 3 (already authorized by run plan D4); job 4 only under the rule in section 5.
Excluded: full CP50 run (C3 ends at "Owner funds CP50"), Tennis Scope A/B execution, `~/.claude/hooks` edits (HR-001), GEX44 live install, D24 W3, push.
Returns to Owner only for: funding CP50 after C3; any goal cap crossing; a TRF/CP50 shared-capsule conflict that cannot be serialized; HR-001.

## 9. Amendment A2 (Owner, 2026-10-11): REA enablement = deferred row D27

- D27 in `vault/plans/deferred-backlog.md` holds the REA Wii/PPC Enablement Program (P0-P7, EVC gate vs the R6 dossier).
- R5's packet MUST include D27 in its admission table and may arm P0 (revalidate the current upstream release + the W4
  hang probe) as a small zero-model unit. R6's packet states its dossier contract as the D27 P7 baseline.
- TRF REA-DISPOSITION.md reading: REJECT = capability gap with a certification path, not REA discarded.