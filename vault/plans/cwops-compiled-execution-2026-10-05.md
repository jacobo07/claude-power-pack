# CW Ops compiled execution (Owner "y" 2026-10-05, pane tua-x-96 / session 8d714d99)

Supersedes the A/B/C token menu given earlier the same day (priced CW Ops with InfinityOps phase-role costs: invalid).
Goals stay distinct: Clock A Phase 1 · Clock A Phases 2-9 (+10 subordinate) · Peak Commerce plan · Peak Commerce execution.

## Ceilings (processed tokens; ceilings, not targets)
| Goal | Ceiling | Central |
|---|---|---|
| Clock A P1 | 1.2M | 0.8M |
| Clock A P2-9 | 16M (recompile mandatory before 18M) | 9M |
| Peak plan | 2.5M | 1.8M |
| Peak execution | 13M | 8M |
| CPP institutional | 4M | 2.5M |
Old-grammar champions (non-authoritative): P1 3-8M, P2-9 200-280M, Peak 4-10M + 60-150M, total 270-440M.
Sunk: pane 8d714d99 ~9.7M before approval.

## Verified facts at approval
- Mission m-3a1a8b1f7fed canonical (lineage m-cb3fb77097d6 -> it; m-c952a800dddc halted). Hold released, directive #1
  recorded (CJ +2, one attempt, no retry; PRG 11/11 first). ed21e129 on kobicraft deploy/live (merge-base verified).
- Worker cec68800: blocked on a stale question; launch flags opus[1m] + --autocompact 600k. Its "check and stop" run
  cost 3.2M = /gsd-autonomous orchestration overhead. Phase 1 is NOT run through /gsd-autonomous.
- Fresh floor this pane 111.8k (first call); 158k average was context growth. InfinityOps split: tools 35k, instr 45k,
  agents 13k, skills 12k, hooks 9k.
- TOK-18 Gen2.1 (15M cap, no live runs before 10-11) governs Cognitive Economy experiments only, not CW Ops.
- BF T0 2026-11-27 (53 days from 2026-10-05). Price-history recording first if the 30-day prior-price claim holds
  (source claim: verify against legal evidence before any discount copy) -> start by ~2026-10-28.
- Peak owners: Commercial Moment (`commercial_moment_events`, Carla line 107a81e9); Clock A Phase 10 already holds the
  BF decision contract + truthfulness check. PDF: Downloads\Playbook_Black_Friday_2026_JRG_Media.pdf (unread; read once
  by an extractor into a claim registry).

## Compiled graphs
- P1: zero-model transaction (stop cec68800, PRG 11/11, ledger +2, one cj.inventory, audit read-back, evidence sha)
  + 1 semantic interrupt (verdict, 01-05 record, STATE/ROADMAP). Fresh lean worker, <=8 calls expected, hard stop 20.
- P2-9 WUs: WU-A P2+P3 fused · WU-B P4 folded (default gap "FX" unless a canonical owner exists) · WU-C P5 (root R2
  hero frontier; NO_CANDIDATE_SURVIVES collapses P6-8 to read-outs) · WU-D P6+P7 read-outs · WU-E P8 · WU-F P9.
  No default planner/researcher/verifier; drills + read-back scripts verify.
- Peak: 2 workers (PDF extractor -> claim registry; builder). Order: price history -> event model (extend
  commercial_moment_events unless proven wrong) -> T0 compiler -> applicability/clock table -> BF2026 fixture over the
  43 actions -> no-regression drill (TEST READY never needs BF READY). Control room + post-event writeback DEFERRED,
  reopen: BF verdict != BF_DO_NOT_SCALE or 2026-11-06.

## Breakers
Per WU: warn 2x expected calls, hard stop + recompile 3x; rotate at 300k context; 5 calls without obligation/test/
evidence change -> stop. Mission token_estimate = compiled HIGH so the existing cost breaker parks overrun.

## Owner-only boundaries
CJ budget for P2 (<=30 calls) · P9 frontier (test price, capital envelope, Meta login/2FA/payment) · publishing any
discount/price claim · capital exception above a ceiling.

## Micro-commits
CPP: c0 this file · c1 KV incident (cross-project role-cost budgeting) · c2 mission envelope (token_estimate) + test ·
c3 compiled-WU launch path (packet instead of /gsd-autonomous) red/green · c4 lean worker profile + floor measurement ·
c5 CBR candidate (expensive-mission compilation gate; candidate until P1 + WU-A actuals exist).
TUA-X clock-a worktree: t1 P1 closure · t2 obligation graph + packets. Product: GEX44 gated_commit.sh / cw_rollout.

## Execution log
- 2026-10-05: plan approved ("y"). c0+c1 committed a0f90a6c (CPP).
- Mission m-3a1a8b1f7fed re-held with reason "compiled execution" (NOT an Owner park): stops the supervisor relaunching
  /gsd-autonomous while the compiled WU runs. cec68800 process gone (`claude stop` failed 3x, daemon pipe; pid 28472 exited).
- WU CWOPS-A1 (Phase 1) = bg worker b380e956 "cwops-a1-p1b", Sonnet, no MCP, no skills, autocompact 300k, cwd
  clock-a worktree. Output: phases/01-probe-truth-cj-inventory-op/01-05-VERIFY.md + STATE/ROADMAP commit.
  (First attempt 1731c3a4 idle: prompt swallowed by variadic --add-dir; stopped, 0 tokens.)
- WU CWOPS-P1 (Peak source) = bg worker bd4af0d5 "cwops-peak-src", Sonnet, cwd TUA-X-brand001.
  Output: vault/sources/jrg-bf-2026/CLAIMS.md (claims + checklist with T0-relative status and provisional verdicts).

## Results (measured from transcripts, dedupe by message id)
- **A1 Phase 1: DONE, SC3 + SC4 PRODUCTION VERIFIED** (commits 75c492b6, 39e6c8df on gsd/brand001-clock-a-ws).
  Cost 2,846,825 processed / 20 calls -> **CEILING 1.2M MISSED (2.4x)**; old grammar 3-8M. No CJ spend (the real call
  had already been made by pane tua-x-08 at 09:56:15Z; ledger stays 8; Owner +2 unused). Misses:
  STATE MISS (packet built from STATE.md, stale vs HEAD 3f0997b2 / 01-04-REAL-CALL.md -> ~4 calls),
  CONTROL-LOOP MISS (worker ended its turn on an in-authority question despite AskUserQuestion disallowed -> resume
  cost ~8 calls re-carrying ~140k context), PROOF MISS (async probe not awaited, re-run, 1 call).
  Lessons for every packet: (1) derive state from `git log` + phase dir listing, not STATE.md alone; (2) packet says
  "decide anything within authority yourself; ending the turn on a question is a failure"; (3) evidence-run scripts
  are checked for awaited effects before the run.
- **Peak source WU: DONE** -> TUA-X-brand001 vault/sources/jrg-bf-2026/CLAIMS.md (60d11e8d), 29 KB: claims ledger
  (legal items C09-C11, C13, C31, C48, C63 = CANDIDATE only) + 43-action checklist triage with T0-relative status.
  Cost 1,392,236 / 10 calls (plan ceiling 2.5M, remaining 1.1M).
- **Floor:** lean launch (no MCP, no skills, Sonnet) first call 107,040 vs 111,840 full pane -> MCP+skill listing
  only ~5k. Remaining floor = host tools + user instructions/hooks: c4 must measure `--setting-sources`/`--tools`
  variants (they drop user hooks = safety guards: decide per worker class, do not blanket-strip).
- Owner approved CJ Phase 2 budget <=30 calls ("yes", directive #2, backlog 085fece7af5c).
- Pane 8d714d99 orchestration: ~11M cumulative (calls now ~250k each) -> rotate; do not execute from it.

## Next (successor: read this section only)
1. c2+c3 in CPP (bounded worker, spec first): mission envelope setter (token_estimate, model, autocompact) + compiled-WU
   launch path (packet file instead of /gsd-autonomous, carrying the 3 packet lessons above), red/green tests,
   path-scoped commits. Then set m-3a1a8b1f7fed envelope (token_estimate 16M, model sonnet, autocompact 300k) and
   release the compiled-execution hold.
2. t2: Clock A obligation graph P2-9 from ROADMAP SCs (reuse g3_k5_obligations.py) -> WU-A packet (P2+P3, CJ <=30).
3. Peak: price-history WU first (verify the 30-day prior-price claim against primary legal text before any copy;
   window ~2026-10-28), then event model on commercial_moment_events, T0 compiler, applicability table, BF fixture.
