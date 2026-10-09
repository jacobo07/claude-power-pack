---
id: PLAN-CE-LIFECYCLE-V3-WU-ECONOMICS
status: PROPOSED (one Owner answer: A / B / C)
extends: ce-lifecycle-v2 continuation plan (b5f441b6, APPROVED) -- B1..B6 are kept, re-sequenced below
covers: [goal-poison-recovery, live-install-binding-l1, estimator-context-growth, three-miss-invalidation, predictive-lease-edge, closeout-reserve, certified-closeout-transaction, proof-below-model, exe-resolver, residual-fallback-receipt, wu-adv2-immunity-canary, lifecycle-chain]
author: coordinator 3339c6c2 (unbound, cwd claude-power-pack)
---

# ce-lifecycle-v3: Work Unit lifecycle economics, built on the live lineage

## Reality delta (measured 2026-10-09 12:01-12:10 local)
- WU-1H4 m-c60ceb4c354c COMPLETED: 448,589 tokens, 7 calls, under its 460K stop. WU-1H DONE: code d948be61, receipt
  62a62dfb (HALT 10/0, mutants 3/3, ADM 43/43, MC 224/225 pre-existing, LIFE 5/1 V-LIFE-PREMODEL-TRANSPORT open).
- WU-ADV epoch 1 tripped at 833K (stop 800K); stub receipt 014f1edb; ledger.py + _logs/wuadv/{block,patch1}.py unapplied.
- Coordinator 97a3d9cf approved the continuation plan (b5f441b6), fixed 3 install-blocking defects in halt_continue
  (uncommitted: gsd_mission.py +43, test_halt_continues.py 13/0 reported, stub mutant survives), then Set-Location'd into
  the goal root. The live guard bound it by cwd and settled its whole history: journal seq 91 settle 32,579,283,
  seq 93 settle 32,801,829 (real post-bind spend 222,546), seq 94 open final 222,546.
- GOAL ce-lifecycle-v2 IS BRICKED: cap 8,847,012, settled 37,271,203, open 2,359,116, remaining -30,783,307. Every worker
  bound to it is refused. This is R4 (retroactive attribution) for the THIRD time: fc54a743 6.86M, 97a3d9cf 32.58M.
  The fix (prospective binding, WU-1B b62f9019) has been on the branch since 2026-10-08 and is NOT installed live.
- Real authority: 2,241,068 (11:48) - 222,546 real - 222,546 open = ~1,796,000 certain, plus up to 2,136,570 held by the
  last leases of 8 terminal sids (B3), minus their unmeasured tails.
- 97a3d9cf's pane ended its turn at 11:58 and is idle; its transcript is 4.3 MB. Live tree: untouched; it carries a foreign
  uncommitted LAUNCHABLE_VERDICTS change (cost-collapse E4a), so any live install commits by index, never by pathspec.
- Collision still open: gsdx S1 "mission steward" (pp-gsdx-factory-2, m-ffb75e73f813 halted 2.71M, uncommitted) edits
  ledger.py, gsd_mission.py, mission_spend.py.
- Estimator: route_admission.py need = calls x profile floor (vault/config/route-floors.json slim-t2 floor 13,507, n=2)
  plus packet. WU-1H4: forecast 139K, actual 448,589 = 64K per call.

## Answers
1. Four processes for WU-1H: one unit held four phases (archaeology of gsd_mission.py, implementation, proof, closeout),
   each epoch paid a fresh startup plus re-reading, and every epoch ended at the breaker, never at a semantic boundary.
   Epoch 1 spent 926K with zero code. The fission was by accident (breaker), not by design.
2. Three overruns: admission prices every call as call 1. Cost per call = resident context, which grows each call.
3. The 139K: 7 calls x 13.5K floor + packet. Actual 7 calls at 64K average.
4. What is wrong: the CONTEXT-GROWTH term is missing (cost is quadratic in calls, the model is linear), and the floor
   sample is n=2. The call count was right for 1H4 (7/7). Closeout is priced as zero, but the breaker tripped inside
   closeout twice ("2 closeout calls spent"). Proof is not modelled.
5. Predictive edge for WU-1H3: at about call 6 (~350K). From there, the remaining 4 calls at the then-current ~70K
   context plus a 2-call closeout reserve exceeded the 500K stop. The worker should have committed the green test
   (10/10) and written the partial receipt there.
6. Protected reserve: 2 calls at current context (~150K at that size): commit, receipt, settle and the successor arm.
7. Safe to commit before the final receipt: any change whose declared proof is green. For 1H3 that was gsd_mission.py
   plus the test at 10/10. Today it is 97a3d9cf's halt_continue fixes after a deterministic re-run, labelled
   checkpoint (stub mutant open).
8. Zero-model WU-1H4: yes. Everything it did was run suites, commit declared paths, write a receipt from logs and arm
   the next unit. A model is needed only on red or on undeclared dirty paths.
9. The certified closeout transaction owns: proof re-run from packet-declared commands, mutant aggregation, pathspec
   commit of declared paths with message-file verification, receipt compiled from logs, ledger settle and lease close,
   and successor arm. It is idempotent per (mission, epoch) and refuses on anomaly with a compact fault object.
10. Proof below model: the packet declares its proof (commands, the summary line each must print, mutant specs).
    The sweep-side runner executes it and writes a proof receipt. The model reads only a fault object, never logs.
11. Bootstrap lane: the existing sweep plus halt_continue, made live by B2. Until then this coordinator relays only by
    deterministic CLI calls (arm/envelope/admit), never by writing work. No new subsystem.
12. Ambient PATH: one executable resolver for git, python and node in the mission tooling, used by _git_ro and the
    capsule writer. Canary: capsule written with PATH emptied must still carry HEAD, commits and dirty paths.
13. Sizing learns: each finished epoch appends (work class, calls, tokens, per-call series) to a profile file.
    Admission fits floor + growth per class. Three consecutive misses of more than 25% mark the class DEGRADED:
    admission then uses the observed p90 of whole-unit cost and a forced fission at the predicted edge.
14. Cheaper later units: packets carry the design and cited line ranges (no re-survey), checkpoint first,
    zero-model closeout, and the edge fires before the breaker. Measure on WU-ADV2 against WU-1H.
15. Universal baseline: the profile, the edge and the closeout transaction live in gsd_mission / route_admission /
    mission_wall, which every CPP mission already uses. UKDL and CBR promotion happen only after the canaries pass live.
16. Original mission: S6 resumes WU-ADV2 under the new machinery, then 1C, 1D, INST, TRIP, FLOOR, GEX, CLOSE.

## Units (one live writer; coordinator does S0 only, then rotates out)
S0 Freeze and recover, zero model, this pane:
   - re-run test_halt_continues on the dirty tree;
   - checkpoint-commit the verified dirty work by pathspec;
   - lineage goal ce-lifecycle-v3 + worktree pp-ce-lifecycle-v3 off that commit (cap = certified real remainder);
   - settle the 8 terminal sids from transcripts (UNKNOWN stays held);
   - record the poison incident.
S1 Live install, the bootstrap breaker. Covers prospective binding (b62f9019) + L1 halt_continue: 3-way merge in a
   staging worktree of live HEAD, 4 suites, index commit in live, sha receipt, revert if red. Needs HR-001 authority (below).
S2 Executable resolver + PATH-loss canary.
S3 Estimator: per-class floor + growth fitted from ledger epochs, three-miss DEGRADED mode, profile append at epoch end.
S4 Predictive lease edge + reserves in mission_wall / the breaker: warn, edge (checkpoint + partial receipt +
   HANDOFF), hard stop unchanged. Productive budget = lease - closeout reserve - recovery reserve.
S5 Certified closeout + proof runner + fallback receipt / residual. First the bounded S1-steward diff (B1): reuse S1 code
   where it already does fallback receipt or residual, one owner per transition.
S6 WU-ADV2 as the immunity canary: it must finish in ONE worker process with zero-model closeout and the forecast within
   25%. Then the chain WU-1C -> 1D -> INST -> TRIP -> FLOOR -> GEX -> CLOSE, sized by the new estimator, each unit
   WAITING_FOR_AUTHORITY when it does not fit.
S7 Knowledge: incident + traps (coordinator cwd bind, R4 x3, linear estimator), UKDL HR/PR/T, CBR after live canaries.

## Cost (measured 45-65K per worker call)
- S1 0.5M, S2 0.3M, S3 0.7M, S4 0.7M, S5 1.0M, S7 0.3M; +20% proof/recovery reserve: about 4.2M.
- Lifecycle chain S6: about 5.5M (old forecasts x measured 2.4-3x).
- Available: ~1.8M certain + up to ~2.1M after B3.

## Owner decision (one answer)
A  (recommended) v3 lineage + HR-001 install authority for S1 + extension up to 2.5M -> S0-S5 + S7 fully funded.
   S6 runs while the remainder lasts, then WAITING_FOR_AUTHORITY with an EAC from the corrected estimator.
B  A + extension to the full ~8.5M -> the whole chain to terminal.
C  v3 lineage + S1 only, no extension -> S0, S1, S2 and S3 fit; the rest waits.

## Done-gate
Master done-gate of the Owner prompt. In particular:
- S1 installed live with the sha verified;
- the goal cannot be poisoned by a cwd bind (re-run of the fc54/97a3 shape on a temp goal);
- WU-ADV2 is one process with a zero-model closeout;
- the PATH-loss canary is green;
- the three-miss DEGRADED canary is green;
- the edge fires before the breaker in a replay of WU-1H3;
- the chain reaches terminal or WAITING_FOR_AUTHORITY with a measured EAC.
