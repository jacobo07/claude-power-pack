---
status: APPROVED (Owner "Approve all", 2026-10-07, pane 9de9bf3b) -- executing as a parentless packet chain
covers: [cost-collapse, compiled-grammar-default, gsd-compile, mission-wait, cognitive-autopsy, obligation-forecast, fresh-floor, gsdx-pcc-reforecast, cognitive-ci]
extends: vault/specs/compiled-grammar-default.md (owner of laws 1-7; this spec funds and finishes it), vault/specs/edd-compiled-execution-canary.md
goal: mission m-53847a002b65 (gsdx-pcc, worktree C:\Users\User\Apps\pp-gsdx-pcc) finishes its UNCHANGED denominator under the compiled grammar
worktree: C:\Users\User\Apps\pp-cost-collapse, branch cost-collapse/main (base 51e46273 + merge origin/grammar/g2-partial + gsd_dossier/edd_canary_gate ported from origin/mission/edd)
---

# Cost collapse -- finish the compiled-execution grammar and move gsdx-pcc onto it

A billion-token forecast is an architecture alarm, not a budget request. Scope, proof, quality, security and
Production Reality of gsdx-pcc are hard constraints; only cognition, context, calls, transport and process lifetime
are optimised.

## Verified reality (deterministic: mission transcripts parsed by usage fields, no model)
- m-53847a002b65 at 2026-10-07T19:30Z: 162,211,437 processed / 637 physical calls / mean ctx 254,649 per call;
  cache_read 158.2M (97.5%); output 573,124 (0.35%). Phase 1 = 118.2M (epoch1 63.3M, epoch2 54.9M).
- Fresh floor (first-call ctx): main workers 125k; subagents 68-99k. Floor rent ~ calls x 100k ~ 40% of spend.
- Context rent: mean ctx ~130k above the floor (dead history in long epochs) ~ 50% of spend.
- One tool per call at 280k ctx: subagent aa7da38b (Opus) 91 calls / 25.6M; a0c42830 (Sonnet) 78 calls / 22.4M.
- Stall 14:25-18:05Z: 0 calls, 0 tokens (waiting already holds zero hot cognition). The wake that followed cost
  13 calls x mean 421,695 = 5.48M: a stale 412k context resumed for small fixes (sunk-context fallacy).
- 1.22B = Phase-1 cost x 9 (extrapolation, retired). 2.44B breaker = catastrophe stop, not a budget.
- ROOT CAUSE: the Owner made the compiled grammar the automatic default (memory project_compiled_grammar_default,
  EDD canary 3.31M vs 32.06M), but G1 never landed on the live branch (only origin/grammar/g2-partial) and G2 is
  unfinished, so `/cpp-gsd-long` still arms the raw planner/researcher/executor grammar with no envelope.
- G1 on this base (Windows laptop): V-GRAMMAR 33/41. Red: NO-ENVELOPE-REFUSED-{SWEEP,CONTINUE,RENEWAL},
  RENEWAL-ENVELOPE-LAUNCHES, UNBOUNDED-ADMITTED-AND-LEDGERED (WinError 193 at launch), PACKET-GATE-COMPLETES-CONTINUE,
  PACKET-GATE-REAL-HANG-NOT-PASS, MUTATION-CONTROL (follows the others). ENVELOPE 55/55.
- Containment: owner hold on m-53847a002b65 (no new epoch); epoch-3 worker stopped after its last commit.

## Law of this program (applies to every tranche)
- NO GIANT COORDINATOR. Each tranche is ONE fresh packet worker (Sonnet unless the row says Opus), armed with an
  envelope, ending on its deterministic gate. No GSD planner/researcher/verifier agents; no Agent unless the packet
  names it with a reason. Raw tool output stays in logs; read summary + failing lines only.
- PARENTLESS CHAIN. A tranche's last act: write the next tranche's packet from the table below (inputs = the spec +
  its own receipt, never its transcript), commit, arm it: `gsd_mission.py arm --cwd <worktree> --command "Execute
  the work unit in the wu_packet" --workstream cost-collapse --no-launch`, then `envelope --wu-packet <packet>
  --token-estimate <row> --model <row> --autocompact 250k`; the 5-minute sweep launches it. No model waits.
- PROGRAM CAP 60M processed across all tranches (metered by mission_spend.processed_tokens per mission + pane
  9de9bf3b's T0). A tranche that misses its own gate twice is frozen; the next row runs.
- Every receipt: `vault/specs/cost-collapse.RECEIPT-<T>.json` (commits, gate lines, processed tokens, calls, mean ctx).

## Tranches
| T | Work | Model | Estimate | Gate (Windows, absolute python) |
|---|---|---|---|---|
| T1 | Land G1 on this base: fix the 8 red V-GRAMMAR gates (launch-boundary admission on every launch path; Windows launch WinError 193; python3 -> sys.executable in fixtures/gates); close F1 (packet sha256 drift -> not judged) and F2 (gate runs in the work tree) per WU-G2b section 1 | sonnet | 8M | test_grammar_default.py 41+/41 incl. F1/F2 gates; test_gsd_mission_envelope.py 55/55; test_gsd_mission.py no new red |
| T2 | `mission_spend.py autopsy --mission M` (per-session/per-subagent calls, processed, cache r/w, first/max/mean ctx, tool mix, stall windows, fork exclusion) + `forecast` (obligation rows: units x calls x (floor + context image) x (1+repair), basis + confidence) | sonnet | 5M | new V-AUTOPSY gates; reproduces m-53847a002b65 to +-1% |
| T3 | G2: `tools/gsd_compile.py` (dossier + packet per roadmap phase, envelope from route floors), `tools/mission_wait.py`, `/cpp-gsd-long` compiles by default (legacy under CPP_MISSION_GRAMMAR=legacy, ledgered); rule: never wake a context above its window -- resume compiles a fresh packet | sonnet | 15M | test_grammar_compile.py (V-GRAMMAR-COMPILE-*, V-WAIT-*) + T1 gates |
| T4 | Fresh-floor breakdown (system/tools/skills/CLAUDE.md/hooks/card) on a real worker; cut the CPP-controllable part for packet workers (e.g. lean hook profile for `bg` packet workers) | sonnet | 6M | measured first-call ctx before/after on a real packet worker; hooks suites green |
| T5 | REAL CANARY: compile gsdx-pcc Phase 2's next work unit (the W1 semantics seam) with gsd_compile; run it; Opus for the one design decision only | opus for design call, else sonnet | 8M | same gsdx-pcc gate as legacy; processed per unit <= 1/5 of Phase-1 per-unit; mean ctx <= 40% of 254k |
| T6 | Reforecast gsdx-pcc bottom-up (T2 forecast over its DENOMINATOR); Amdahl loop on the next dominant tax (max 2 tries per line) | sonnet | 10M | `vault/specs/cost-collapse.FORECAST.json`; estimate <= 200M (target 10x below 1.22B) or a computed lower bound |
| T7 | Ratchet + resume: UKDL HR/PR/T entries (vault/knowledge_base/ukdl-universal.md); Cognitive CI gate (phase inflation, ctx growth after closed uncertainty, calls/boundary, parent tax, floor growth); deploy to live (cherry-pick onto feature/knowledge-acquisition, smoke, rollback point; never push); release gsdx-pcc and re-arm it in the packet grammar with the T6 envelope | sonnet | 4M | `python tools/cost_collapse_done.py` exit 0 |

## Master done-gate (`tools/cost_collapse_done.py`, built in T7)
V-GRAMMAR + V-GRAMMAR-COMPILE + V-WAIT + V-AUTOPSY green; ENVELOPE and V-MC no new red; canary receipt shows >= 5x
per-unit saving at equal proof; FORECAST.json <= 200M or lower-bound proof; floor before/after receipt; Cognitive CI
gate green with a red drill; UKDL entries present; m-53847a002b65 re-armed with --wu-packet and RUNNING; program
spend <= 60M.

## Rollback
`CPP_MISSION_GRAMMAR=legacy` live; every tranche is revertible micro-commits; live install changes only at T7.
</content>
</invoke>
