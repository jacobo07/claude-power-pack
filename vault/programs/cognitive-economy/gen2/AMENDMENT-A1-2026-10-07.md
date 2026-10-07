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
U1 (2026-10-07): packet + route committed fabf3071 (ADMISSIBLE 7.80M / 58 calls). Staged on GEX44 clone
~/missions/ce-a1 at 61ab9f23 (branch mission/ce-a1, git identity + trust set, ~/.claude.json backed up to
~/.claude.json.bak-ce-a1). GEX44 live PP is daf90d00: no `admit`, no route_admission.py, and the packet-gate law is
not deployed (same NO_PHASES defect that BLOCKED G2) -> U1 runs as a bounded headless worker, not a gsd mission:
`cd ~/missions/ce-a1 && nohup claude -p "<run U1-PACKET.md>" --model sonnet --max-turns 58 --permission-mode auto
--output-format json` (out: ~/missions/ce-a1-U1.out.json). First launch: 429 usage_limit_reached on the GEX44
account too (resets Oct 11 20:00), 0 tokens spent. Relaunch after the Owner logs GEX44 into another account.
Relaunched 2026-10-07 on GEX44 account jacobofifa07@gmail.com (the laptop's account: U1 spend draws on the same weekly
quota) as PID 3630229, transcript ~/.claude/projects/-home-kobii-missions-ce-a1/65727119-*.jsonl; 429 artifacts kept as
ce-a1-U1.out.429-costaluz.json/.err. U1 DONE: 4 commits 6f11a3c5..82a493aa (receipt evidence/a1/U1-RECEIPT.md).
U1 worker spend MEASURED 1,097,211 processed (out.json usage == dedup transcript sum, 11 API calls / 12 turns,
sonnet-5-5, $0.71 list) = 14% of the 8M envelope. Done_gate re-run independently by the coordinator on GEX44: all 5
exit 0 (CE_A1_PASS=12/12, null-as-zero mutant killed); real-ledger C16 exit 1 as expected, C15 exit 0 VACUOUSLY
(tranches are bare ints, nothing "started" -- receipt flags it). a1.spent left null on purpose: coordinator (laptop)
spend is unmeasured until the A1-2 meter, so writing 1.1M would make C16 pass on a partial sum.
Integration: fetched as local branch a1/u1 (82a493aa); `git merge-tree` against ce/gen2-completion (be88dee5) is
clean. NOT merged: another pane is live in pp-ce-gen2 (rollover.py dirty 13:45, untracked T1e test); merge it there
when that pane is idle. Open from receipt: C15/C16 OPEN-with-check keep `--final` red; family tranche lists absent.
A1-2 DONE (Owner 'y' to plan, pane b9bd9469): branch a1/a1-2 5a075c91 in worktree C:/Users/User/Apps/pp-a1 (on top of
a1/u1; NOT merged, same reason). `turns.py --attribute` + tools/test_ce_a1_attribute.py 18/18, 3 mutants killed; full
done gate green; receipt evidence/a1/A1-2-RECEIPT.md. Canary 10-04T18Z..10-07T10:33Z: tier A 258,994,397, B
119,920,566, already-ledgered 124,609,059 (controls ok) -> coordination_spend.value = tier A. The ad-hoc 520M/368M
counted whole sessions (555M of program sessions lies outside any write span).
**A1 OVER CAP**: a1.spent = 42,307,381 at 12:22:33Z (423e33b0 from approval 11:12:10Z 24,715,309 + b9bd9469
16,494,861 + U1 1,097,211; upper bound 44,792,057) vs cap 20,000,000. C16 on the real ledger: exit 1, over cap.
Next (T3 replay) is HELD for the Owner: raise the A1 cap, or stop A1 here.

## INCIDENT 2026-10-07 -- A1 ECONOMIC_CONTAINMENT (Owner 'y', pane b9bd9469)
Owner briefly chose a 60M raise (84289c7d), then withdrew it: raising a cap after crossing it turns the limit into a
retrospective number. a1/a1-2 ab44236e: cap back to 20M, cap_history keeps all three entries, a1.status =
ECONOMIC_CONTAINMENT, breach {spent 42,307,381, overshoot 111.5%}, T3 + T7 FROZEN. C16 stays red as the record.
Root cause: the 20M cap was a ledger number read by C16 AFTER spend; no admission path checked it before a call.
Interactive coordinator panes (423e33b0 24.7M, b9bd9469 16.5M) carried 41.2M of 42.3M; the worker (U1) 1.1M.
Universal pattern: POST-HOC BUDGET ENFORCEMENT IS NOT BUDGET ENFORCEMENT.
Existing admission owners (extend, do not build a new kernel -- HR-NOVELTY-001): tools/route_admission.py:61 admit,
tools/gsd_mission.py:1304 admit_route (missions only; not deployed on GEX44 daf90d00), modules/cognitive_os/governor.py:67
admit (weekly account quota), modules/cognitive_os/loop_budget.py:166 admit_subagent (own allowance, not a
sub-allocation), modules/provider_routing/ledger.py:121 reserve (provider capacity only), mission cost breaker (parks
after spend). Missing: one pre-call reservation from the goal's canonical budget, shared by parent/child/resume/machine;
UNKNOWN material spend (GEX44, G6) fail-closed for new cognition.
Host limit to design around: harness hooks see tool calls and turns, not each API request -> the hard gate can refuse a
pane's next tool call / turn and any new worker or Agent before launch, not a call already in flight (bounded, not 0).
NEXT (fresh pane, not b9bd9469): `/ultra plan` pre-call budget admission, spec first (SDD T3); phase 1 = read-only
reality scan of the owners above; done-gate = tiny-cap canary across several panes + Agents with zero unauthorized
overshoot, mutation suite from the Owner's list (concurrent last-reserve, Agent spawn over parent remaining, resume
reset, cross-account, crash with live lease, UNKNOWN cost). Merges of a1/u1 + a1/a1-2 into ce/gen2-completion still
wait for the pp-ce-gen2 pane to go idle.

## EXCEPTION to decision 4 -- 2026-10-07 (Owner 'y', pane b9bd9469), ONE unit only
Autonomous Optimization (IC gen2) phase-1 close-out: CR-01 (population --until bad value -> MEASURED/EXACT, false
PASS), WR-01 (non-OSError aborts refresh), WR-02 (grown legacy file sets launch cwd) + phase-1 verification. Headless
sonnet worker on GEX44, envelope 4M processed / 30 calls, packet
missions/autonomous-optimization .planning/.../01-usage-index-v5-substrate/01-FIX-PACKET.md committed 41e35562, PID
3934792, transcript 1a348a7e. Phases 2-7 stay paused until pre-call budget admission exists. Spend is metered from
the worker's own transcript and counts against the program, not against A1 (A1 stays in containment).
Also settled today: cognitive-resource-os has no open work -- CRO-01 PASS on GEX44 since 2026-09-30 (bb094d1,
194 passed / 4 skipped); the laptop's STATE.md is stale only because mission/cognitive-resource-os-gex44 is unmerged.
