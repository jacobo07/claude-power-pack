---
covers: [ccr, long-horizon-text, one-read, reread-admission, non-convergence, lobby-benchmark, epoch-economics]
goal: ccr
status: PROPOSED
authority: existing goal ccr (cap 36,880,000; used 5,171,864; remaining 31,708,136 at 2026-10-12 16:24). P80 fits.
---
# CCR v3: long-horizon textual rent, one-read admission, non-convergence (2026-10-12)

Continuation of goal `ccr`, not a new programme. Extends v2 + addendum + addendum-umvm. RESUMPTION_FILE stays
owned by the live ccr owner pane; this file is the plan of record for the v3 scope.

## A. Frontier (measured this scan)
- HEAD c99dbf68 on feature/knowledge-acquisition (shared tree, ~1000 foreign dirty files: pathspec commits only).
- Sealed: S1-S4, M1 (carry receipts + rotate advice, observe only), M2 (pixel GC opt-in), M3 (text carry by kind),
  M4 evidence (Madzia a4/a5). Release still 0.1.0-feaae8b0; M1-M3 unreleased pending the arm-B canary.
- Owner pane per RESUMPTION_FILE: c13cda65 (transcript last written 16:08, idle at 16:24). One owner at a time.
- Open RESUMPTION actions: (1) Madzia ContextImage drops the runs-tree listing; (2) arm B on GEX44; (3) release.

## Facts already in hand that bound this plan (do not re-derive)
- CE CLOSE (2026-10-03): F reread/materialized cognition FALSIFIED at 1.88 % < 3 %; G CSE FALSIFIED (F gate not met);
  K tool-output admission 2.67 %; J non-convergence measured 3.51 % >= 3 %, handed to a stronger owner, not built.
  Realized savings: none. EFFECTIVENESS_NOT_CERTIFIED. Those were estate-wide windows, NOT Lobby-specific.
- M3 NO_WORK scope: Madzia workers a2/a3 only; liveness signal tested = "same file and range read again later in the
  same epoch" (0 tokens). It did not test cross-epoch / cross-session rereads, Lobby, or semantic (not byte) identity.
- Host 2.1.296: session.append may drop media only; headless $.session.compact() refused; a /compact turn with a full
  rebuilt kept-set works with zero model calls; a mixed handle/rebuilt kept-set is a silent no-op. Text CAN be dropped
  by the full-rebuild path; the missing piece was a liveness signal, not a host capability.
- Price: a rebuild/rotation rewrites the prefix (cw 80,256 measured). Weighted ledger: input 1, cache_read 0.1,
  cache_write 2, output 5 (CLOSE table). Gross wins can be weighted losses.
- Existing owners: mod `page` tool (skills/agents/instruction files only); mod carry advice file per sid;
  `tools/gsd_mission.py` NO_PROGRESS_EPOCHS=3 (work tree unchanged across relays -> HALTED);
  `tools/usage_index.py` (refresh/window/burn/replay/holdout) over per-call rows with session id.
- Lobby corpus: `~/.claude/projects/C--...-KobiiCraft-Core-Files` 575 jsonl, 2,265 MB; 2-3 sessions writing NOW
  (foreign live writers). No `lobby` goal exists. The 2,044 / 755M / 194M figures are NOT in the vault: unverified.

## Root-cause matrix
| class | verdict | basis |
|---|---|---|
| PROMPT_CACHE_WORKING | CONFIRMED | ccr ctx == provider usage; 98 % cr reported |
| LONG_SESSION_TEXT_CARRY | CONFIRMED (Madzia) / UNKNOWN (Lobby) | text 44.9 % of a3 |
| CURRENT_BOUNDARY_OVERMATERIALIZATION | PARTIAL | runs-tree listing 14-18 %/attempt |
| REPEATED_CERTIFIED_FACT_READ | UNKNOWN | estate 1.88 %; Lobby cross-epoch unmeasured |
| RESUME_RENT | UNKNOWN | not measured |
| CACHE_WRITE_ROTATION_PENALTY | CONFIRMED | cw 80,256 per rewrite |
| M3_IN_PLACE_PROJECTION_LIMIT | CONFIRMED, scoped | see above |
| UTVM_NOT_EFFECTIVE | CONFIRMED (not built) | no history store behind `page` |
| CERTIFIED_STATE_NOT_EFFECTIVE | UNKNOWN | no owner found |
| PROOF_OF_REREAD_MISSING | CONFIRMED | no admission code |
| SEMANTIC_PAGE_FAULT_MISSING | PARTIAL | page tool lacks history kind |
| ONE_READ_CAPITALIZATION_MISSING | CONFIRMED | |
| NON_CONVERGENCE_MISSING | PARTIAL | tree-unchanged predicate; a docs commit resets it (hypothesis for 25-09) |
| ZERO_PROGRESS_BURN | UNKNOWN | 194M unverified until U1 |

## Owner map
| capability | class | owner |
|---|---|---|
| per-call carry receipts | ALREADY_DONE | mod session.append / turn.complete |
| rotate advice | IMPLEMENTED_NOT_HOT_PATH | mod advice file; no driver reads it |
| page faults | EXTEND | mod `page`: add kind `history` + `fact` |
| UTVM L0/L1 | EXTEND | jsonl (L0) + usage_index (L1) |
| L2/L3 semantic + certified state | IMPLEMENT (small) | new receipt store under the mod state dir |
| Proof of Re-read / One-Read admission | IMPLEMENT | mod tool.call hook on Read |
| ContextImage / tiny continuation | EXTEND | KSR boundary.py compiler (driver-owned) + gsd_mission capsule |
| epoch compiler | EXTEND | carryAdvice -> weighted break-even |
| ASER | CONNECT | executes rotation |
| non-convergence | EXTEND | gsd_mission NO_PROGRESS breaker -> progress receipt |
| Semantic CSE | NO_WORK unless D1 shows >= 3 % | CE G falsified |
| Prompt Recall / UKAI | CONNECT (L2 query path) | modules.gsd_x.recall |
| UKDL / CBR / FIOS | EXTEND | existing writers |

## Workstreams, mode, gate (execution order)
| # | unit | mode | done-gate |
|---|---|---|---|
| U1 | Lobby corpus: usage_index rows for the KobiiCraft project + git log of the Lobby repo -> per-day calls, gross, weighted; verify or correct 2,044 / 755M / 194M | EXECUTION | figures reproduced by one command, or corrected |
| U2 | 25-09 autopsy: per Ralph epoch, tree delta, commit kind, failure signature, strategy hash; first epoch the evidence shows zero progress | EXECUTION | earliest detectable epoch + counterfactual saved spend |
| U3 | Non-convergence: progress receipt (gate movement, accepted non-doc delta, new certified fact, failure signature, strategy id, cost slope); docs-only commits do not reset stalls; same strategy + flat progress refuses renewal | EXECUTION | replays U2 and halts earlier; a real-progress control is NOT halted |
| D1 | Read attribution on Lobby: per Read/Bash result, semantic id = (path, content hash, range); count model-facing re-reads across epochs/sessions, ride length, weighted rent | EXECUTION | share of weighted spend that is repeated unchanged reads; GO only if >= 3 % (CE F rule) |
| D2 | Lobby rent composition (floor / tool text / thinking / user / assistant) per boundary, sampled | EXECUTION | dominant-rent rank for Lobby |
| E1 | Epoch economics: offline simulator over usage rows, arms A-F, weighted with cw; break-even epoch length per work class | EXECUTION | per-class rotation rule beats A in weighted cost on held-out sessions |
| G1 | Semantic read receipt + certified fact store (path, hash, fields, provenance, invalidators); capitalization on first material read | EXECUTION, only if D1 GO | receipts on a real run |
| H1 | One-Read admission in the mod: Read of an unchanged (path, hash, range) already receipted this goal -> answer from receipt or allow with logged necessity reason; changed hash invalidates only that id | EXECUTION, only if D1 GO | falsifier: changed file is re-read; unchanged is not; quality parity |
| K1 | page kind `history`/`fact`: smallest projection from L0 by id; fault receipts; prefetch on repeated faults | EXECUTION | raw recall exact on 20 sampled quotes |
| M1 | Tiny continuation: capsule built from certified state + next obligation; resume-rent gate (bytes) in CI | EXECUTION | capsule size flat under history doubling |
| R1 | Context elasticity: fixed WU, history H vs 2H vs 4H (synthetic padding in L0/L1) -> model-facing tokens | EXECUTION | elasticity < 0.05 after floor |
| V1 | Real canary: one bounded textual WU under the winning policy vs historical analogue | PLAN (ownership) | provider usage + reviewer parity |
| X1 | Certification or exact abstention; Lobby reforecast; KV/UKDL/CBR | EXECUTION | contract below |

## Effectiveness contract (EFFECTIVENESS_NOT_CERTIFIED -> EFFECTIVENESS_CERTIFIED_LONG_HORIZON_TEXT)
All of: E1 offline weighted saving >= 15 % on held-out Lobby sessions with cw included; V1 real canary weighted
saving >= 15 % vs matched analogue at reviewer/test parity; raw recall exact (K1); freshness falsifier passes (H1);
elasticity < 0.05 (R1); resume rent bounded (M1); control overhead counted inside the saving; U3 halts the 25-09
replay at <= 25 % of its burn while not halting the real-progress control. Any miss -> ABSTAIN with the named limit.

## Token budget (this continuation, tokens)
| item | P50 |
|---|---|
| reality delta (done) | 0.3M |
| U1 corpus + U2 autopsy | 2.5M |
| U3 non-convergence | 2.5M |
| D1 + D2 attribution, M3 scope | 2.5M |
| E1 epoch economics + cache-write | 2.0M |
| G1 + H1 + K1 (if D1 GO) | 4.5M |
| M1 continuation + resume rent | 1.5M |
| R1 elasticity + offline benchmark | 2.0M |
| V1 real canary | 3.0M |
| self-host, KV/UKDL/CBR | 1.5M |
| meta-optimization tax | 1.2M |
| recovery reserve | 3.0M |
Semantic lower bound 6M (U1-U3, D1, E1 only, D1 NO-GO) · LOWER 10M · P50 26.5M · P80 30M · P95 38M ·
HARD AUTHORITY 31,708,136 remaining. P80 is covered; P95 is not: at 28M settled, stop and re-forecast before V1.

## Stop-losses
D1 < 3 % -> G1/H1 become NO_WORK (record negative knowledge) and the programme proceeds on E1 + U3 + M1 only.
Any reviewer/test regression kills an arm. Benchmarks are offline first; provider spend only in V1.
