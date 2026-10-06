# EDD reforecast from EDD's own evidence (replaces the Orca phase-average champion)

Instrument: transcript parse deduped by message id (`canary/autopsy/edd_autopsy.py`, `tools/mission_spend.py`).
n = 1 canary, on a SCAN phase. Build phases (2-6) are not yet measured on EDD: wide band, stated as estimate.

## Measured
| item | calls | processed |
|---|---|---|
| champion grammar, m-ee81e1595007 (stopped; Phase 1 research incomplete, 0 obligations) | 132 | 32,062,568 |
| canary attempt 1, m-99b4cc7104f9 (BLOCKED: autocompact 120k < floor 95.7k + dossier) | 5 | 489,159 + compactions UNKNOWN |
| canary attempt 2, m-51b4175db047 (Phase 1 matrix 81 rows + spec + receipt; gate 11/13 before G7/G8) | 23 | 3,310,496 |
|  of which the work session bcacdf0f | 16 | 2,597,177 |
|  of which 2 continuation epochs after the packet was done (supervisor asks GSD, not the packet gate) | 7 | 713,319 |
| orchestrating laptop Opus pane 08cb0d86 since the optimization prompt (21:52Z) | 56 | 17,413,320 |
| dossier compile (gsd_dossier.py) | 0 model | 6 s |

## Quality (not proven by the gate, sampled)
Gate proves structure only. Fixed-seed sample of 8 judged rows: 6 sound, 2 wrong (C-15 owner is a vocabulary match,
not the concept; C-54 ALREADY_IMPLEMENTED contradicts its own note -> PARTIAL). 28/81 rows UNKNOWN (declared, not
guessed). Phase 1 is NOT done: repair packet WU-1R (2 wrong rows + 28 UNKNOWN) is unfunded, next tranche.

## Unit costs observed
Worker floor 95.7k-96.6k per call; mean work call 162k; context 96k -> 206k over 16 calls; 0 compactions at 250k.
Continuation tax 21.5% of the canary (7 of 23 calls). Orchestration by a long-lived Opus pane cost 4.6x the work.

## Remaining EDD (Phase 1 repair + Phases 2-7), compiled-packet grammar
Assumptions: phases 2-6 build code, benchmarks, holdouts and mutation drills; 2-4 packets each, 15-40 calls per
packet at the measured ~160k; deterministic runners execute benchmarks/drills; repair x1.1-1.5; orchestration by
fresh short contexts at 1-4M per tranche; continuation tax removed by a packet-level completion signal or not.
| scenario | estimate |
|---|---|
| low | ~36M |
| central | ~95M |
| high | ~215M |
Champion for comparison: 650M low / 1.2B central / 1.87B high (Orca phase averages, n = 1, borrowed).
Prediction error of this plan so far: canary planned 3-8M, actual 3.31M (attempt 2) + 0.49M (attempt 1 failure).
Tranche cap 25M: ~21.2M measured + UNKNOWN compaction cost; the repair packet is held for Owner authority.
## WU-1R repair (m-84da090be030), measured
- 1,958,619 processed / 16 calls (one session 6fab39dd, ctx peak 140,578); estimate was 3M. The stall breaker set a
  hold after the work was committed (1.96M since the tree last changed > 1.5M stall budget) and the worker stayed
  alive until `claude stop` (UC-14 again).
- Outcome: 30 rows re-judged, 0 UNKNOWN, 0 unresolvable; gate 13/13.
- Independent sample (seed 42, 6 rows): 3 correct, 2 minor (C-01, C-07 process instructions -> NOT_A_SYSTEM), 1 wrong
  (C-17: the C-15 vocabulary-match error moved, not removed). Fixed by the orchestrator directly (3 rows).
- Receipt self-report: 3 boundaries vs 16 measured calls -> worker-reported counts are claims; only metered counts count.
- Phase 1 total, compiled grammar: 3.31M + 0.49M (failed attempt) + 1.96M = 5.76M, plus 2 orchestrator edits.
  Precision over the two independent samples: 9 of 14 rows right as first judged; all 5 errors corrected.
