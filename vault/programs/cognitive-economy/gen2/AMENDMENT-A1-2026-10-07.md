---
id: PLAN-CE-GEN2-AMENDMENT-A1
date: 2026-10-07
status: APPROVED 2026-10-07 Owner 'y' (pane 423e33b0), defaults 1-6; item 2 superseded same day -- executing now
amends: vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md (PLAN-CE-GEN2-COMPLETION, approved 2026-10-07 pane 71ccfa86)
covers: [optimization-moratorium, amortization-ledger, two-strike-optimizer, boundary-census-settle, idle-rebuild-economics, estate-concurrency, resume-exam-failures, unmetered-coordination-spend]
source: Owner ULTRA prompt 2026-10-07 (pane 423e33b0) + weekly audit memory project_token_audit_week_2026-10-04.md
mode: PLAN amendment to an existing owner. No new system. No ULTRA re-architecture (falsified: >90% owned).
---

# Amendment A1 -- the optimizer pays for itself or stops

## Verified reality (2026-10-07, this pane, zero-model scans)
- Canonical Goal: Cognitive Economy gen2 completion (Macro-Goal A) then G2 grammar return (Macro-Goal B). Card
  COMPLETION-PLAN.md; state gen2/ledger.json. Worktree C:/Users/User/Apps/pp-ce-gen2 (ce/gen2-completion de813045):
  T0 done; T1a/T1b/T1c committed (Forget-Safety in certify, C2 transcript/handoff deletion tests CHECKED, C3 lifecycle
  gates, autocompact demoted at the wall); 14 obligations declared. CE-T1a worker was capped by the weekly limit 12:33.
- Spend vs authority: ledger budget_tokens.spent_measured.value = null; listed measured sources sum ~298M processed
  (~157M excluding E1 141M) against authorization_boundary 150M. Unknowns listed in the ledger itself.
- Unmetered spend: laptop sessions whose writes target token-economy paths, 2026-10-04 18:00Z..2026-10-07 10:33Z:
  tier A 520M processed ($253 API-eq), tier B 368M ($147). GEX44 (different account, jacobo@costaluzlawyers.es)
  ~$250 of $266 in optimization missions (autonomous-optimization, cognitive-economy-e1, incremental-cognition, edd,
  grammar). Unit = input+cache_write+cache_read+output, dedup by message.id (same unit as the ledger).
- Boundary census owner EXISTS: measure/turns.py (75,969 calls DW7; 52% of weighted calls "unsettled").
- Resume failures (rollover-ledger, window): 19 resume_failed = exam field wrong: next 11, goal 3, dirty 3,
  goal+dirty 2; plus 6 certify_stale_refresh, 1 claim_taken_over (holder gone). 83 successor_claimed, 76 certified.
- Floors: S1 measured fresh first call 105,454; transcript first-call median 116k after the E1 move (n=189);
  E1 saving measured 8,477/call upper bound. ~/.claude/CLAUDE.md 39,809 chars (Owner-applied only, HR-001).
- Rotation economics (replay of the window): roll at 200k net -$29, 250k +$123, 300k +$165 before resume overhead.
- Quota: laptop account exhausted until 2026-10-11 18:00Z; model-heavy units go to GEX44 (Owner, item 2).

## What A1 adds (everything else stays in COMPLETION-PLAN tranches)
A1-1 Amortization record per tranche (extend ledger completion_plan.tranches + C13): build cost, run cost, measured
     saving, forecast saving, confidence, break-even horizon, failure + retirement criterion. No record, no tranche.
A1-2 Program meter covers coordination: spend attribution by write-path + session lineage (CE-T0a meter), so
     interactive planning/estimation panes count against the boundary. Until then the envelope is UNVERIFIED.
A1-3 Two-strike rule: two consecutive tranches of one optimizer family failing their own criterion -> family FROZEN;
     reopen only with changed mechanism, stronger evidence or Owner phrase. Families: E1 rule-moves, IC/AO measurement
     tooling, context-runtime tranches, gen3 envelopes.
A1-4 Boundary census settle: T3 extends turns.py, not a new census; target is settling the 52% "unsettled" class
     with sampling, then the extinction map.
A1-5 Idle-rebuild + TTL + estate concurrency enter T3 offline replay as classes (117 rebuilds >=150k, 30 sessions/h
     peak); host-controlled TTL is recorded as host floor, not a CPP saving.
A1-6 Resume exam: the 11 "next" failures are a T1 follow-up on rollover.py (capsule next-action derivation vs the
     successor's exam); classify each against its capsule before any fix.

## Moratorium gate (applies from approval)
Allowed now: units with measured or zero-model evidence and a closed criterion (T1 follow-up A1-6, T3 replay, T7
self-retirement, meter A1-2). Frozen until A1-1 records exist: T2 WU3 Context Compiler, T4, T5 champion/challenger,
T6, T8. Each unfreezes only when its amortization record shows break-even inside 30 days of estate use.

## Owner decisions (single approval) -- APPROVED 2026-10-07 Owner 'y' (pane 423e33b0), all defaults
1. Authority: moratorium; no boundary raise. A1 cap 20M processed, metered with the A1-2 meter.
2. SUPERSEDED same day by Owner: "no esperes a que se reinicie la cuota, vamos a cambiar de cuenta en la GEX44 si
   hace falta". Execution starts now; model-heavy units run on GEX44 (account switch is Owner-side). Spend on any
   account counts against the A1 cap -- moving work to another account is never reported as a saving.
3. T2, T4, T5, T6, T8 FROZEN until each has an A1-1 amortization record showing break-even <= 30 days.
4. GEX44 optimization missions paused. Checked 2026-10-07 (gsd_mission status on GEX44): 24 records, 18 HALTED;
   RUNNING m-604666a514a3 and m-84da090be030 already parked by their cost breakers (4.08M / 1.96M processed with
   no work-tree change); BLOCKED m-23ae5b4a7113, m-9d00610493fc, m-f011d7fdebc9; PREPARED m-eaf2843afb16 under
   Owner hold. No live session (daemon + bg-spares only). No additional hold written: nothing would launch.
5. ~/.claude/CLAUDE.md changes delivered as Owner-applied diffs (HR-001).
6. oneshot-architect-auditor runs on this amendment BEFORE any A1 execution (dispatched 2026-10-07).

## Phase 4 audit (oneshot-architect-auditor, 2026-10-07): NEEDS-FIX, 9 gaps -> phase 5 fixes (binding)
G1 BLOCKER: do NOT write estate optimization spend into spent_measured (cep_gen2.py:95 check_spend would go red
   for ever vs 150M, and the window predates gen2 approval 2026-10-05). Fix: separate ledger block
   `budget_tokens.coordination_spend` {value, sources, unknown}; spent_measured gets only program-attributable spend
   since approval.
G2 A1-1 duplicated cep_gen2.py:195-254 check_receipt (cost, saving, forecast, break_even_calls, PAID_BACK/NOT_YET/
   UNKNOWN). Fix: per tranche `experiment:true` + `receipt`; extend check_receipt with horizon_days, confidence,
   retirement_criterion. No new record type.
G3 tools/self_spend.py does not exist (real: gen2/evidence/stage0/self_spend.py, 26 lines, one session). Fix: A1-2 is a
   `turns.py --attribute` mode reusing scan_file / tool_cat (measure/turns.py:133-196).
G4 false negatives: planning panes rarely Write/Edit; shell writes carry no path. Fix: attribute also by lineage (cwd in
   a program worktree, Reads of program cards, subagents rolled up to parent); text_only share reported UNKNOWN.
G5 false positives / double count: per-call attribution between first and last program write; dedup message.id|
   requestId; exclude session ids already in ledger sources; explicit path list incl. pp-ce-gen2; +/- control sessions.
G6 the A1 cap is unmeterable on GEX44 (meter reads laptop projects only). Fix: GEX44 meter run over ssh writing
   per-unit session ids + totals BEFORE any GEX44 unit; until then the cap is UNVERIFIED.
G7 C15/C16 undefined; gen2 gate logic lives in cep_gen2.py:112-192 and run_check refuses self-invocation. Fix: add C15
   (unfrozen tranche has valid receipt; frozen stay frozen; two-strike family state) and C16 (A1 spend <= 20M,
   UNKNOWN fails) pointing at a standalone tools/test_ce_a1.py, OPEN with check:null until it exists.
G8 ordering: T3 is shadow (no per_call saving) so a payback receipt would be rejected (cep_gen2.py:221-223). Fix:
   receipt kind `measurement` (cost + decision value, no payback). Order: A1-6 -> A1-2 -> T3 -> T7 (T7 moves the floor
   T3's KEEP/DEALLOCATE economics read; or parameterize T3's floor).
G9 resume_failed count: 27 in the whole ledger vs 19 cited. Fix: pin window and row ids (done below).

## Executed
- A1-6 (zero-model, 2026-10-07): window 2026-10-04T18Z..2026-10-07: 19 resume_failed rows, ALL followed by
  resume_certified of the same claimant on retry (next 11, goal 3, dirty 3, goal+dirty 2). Zero terminal continuation
  failures; the audit memory's "19 failed resumes" was a misreading. rollover.py:1264-1271 judges the exam against
  the tree as it is now, so "next"/"dirty" misses after a moved tree may be correct-by-design -- label pending.
- Found while classifying: test_gsd_mission_legacy_characterization.py (V-G23) wrote the LIVE rollover ledger on
  every run (7 rows; 210 of 322 capsule_sealed rows in the window, all "not a git work tree" on gsd-mission-g23-*
  temp dirs). Fixed be76dec1: CPP_ROLLOVER_STATE_DIR redirected + gate V-G23-HERMETIC-ROLLOVER-STATE (RED before,
  33/33 GREEN after, live delta 7 -> 0). Corrected window figures: 112 real seals, 94 SAFE_TO_FORGET. Six torn
  JSONL lines (176, 377, 430, ...) predate the window, after "write failed: PermissionError" seals: historical,
  current status UNVERIFIED.

## Resumption (read only this file + gen2/ledger.json in pp-ce-gen2)
1. G7 + G1 + G2: ledger + cep_gen2.py extensions (coordination_spend block, C15/C16 OPEN, receipt fields) in pp-ce-gen2.
2. A1-2 = turns.py --attribute (G3-G5), canary on the 2026-10-04..07 window into coordination_spend; then G6 GEX44 run.
3. T3 replay with a measurement receipt (G8), then T7.
Status line to keep current: A1 spent UNMEASURED (this pane, laptop) / 20M; executed units: A1-6, G23 hermetic fix.
