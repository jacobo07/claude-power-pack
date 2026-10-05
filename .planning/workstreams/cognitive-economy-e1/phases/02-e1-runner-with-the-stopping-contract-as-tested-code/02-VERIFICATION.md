---
phase: 02-e1-runner-with-the-stopping-contract-as-tested-code
status: passed
verified: 2026-10-05
---
# Phase 2 Verification

Observed at HEAD 025d4a20 (worktree `.claude/worktrees/e1`, worker epoch 3), commands run from the worktree root.

| # | Success criterion | Evidence | Status |
|---|---|---|---|
| 1 | Every stopping-contract clause is code | `e1_contract.py` + `e1_runner.py`: order by rule bytes (V-E1-ORDER; `plan` lists 6284 -> 1772 bytes), alternation (V-E1-ALTERNATION, -SM; `plan` arms A,B / B,A), one pair per rule (V-E1-ONE-PAIR), rerun-once validity (V-E1-RERUN-ONCE, V-E1-VALID, V-E1-CLI-ERROR, V-E1-GRADE-TIMEOUT), per-rule decision (V-E1-DECIDE, V-E1-TOKENS-NO-TIEBREAK), harm stop (V-E1-HARM-FN, -SM, V-E1-LOOP-HARM), spend stop 17M (V-E1-SPEND-FN, -SM, V-E1-LOOP-SPEND; `plan` prints CAP 17000000), gate-1 positive control (V-E1-POSCTL-FN, -SM, V-E1-LOOP-POSCTL) | PASS |
| 2 | A fake-session test drives every stop branch red and green, no model calls | `python3 vault/programs/cognitive-economy/e1/test_e1_runner.py` -> `E1_PASS=77/77 threshold=77/77`; the loop gates end in ALL_DECIDED, HARM, SPEND, POSCTL, REFUSED, COMMIT_FAILED with a fake CLI; V-E1-NO-MODEL and V-E1-NO-MODEL-END: `blocked=1 with -p=0` (no `-p` session ever launched, one version probe only) | PASS |
| 3 | Before the first counted run, the 13 LF sha256 pins are re-checked against the packet; mismatch refuses | `e1_runner.py preflight` -> `CHECK packet OK sha256 b6b104bb523d`, `CHECK pins OK 13/13`, `CHECK excludes OK 13 paths`, ... `PREFLIGHT OK` rc=0; refusal side: V-E1-PINS, V-E1-PACKET-PIN (other/rewritten/missing packet -> `preflight_refused=['packet']`), V-E1-PACKET-SET, V-E1-PER-RUN-CHECKS / V-E1-LOOP-CHECK-EVERY-RUN (checks repeat before every run) | PASS |

`e1_runner.py run` was not invoked in Phase 2 (cross-cutting constraint): `plan` shows `SPENT 0 RUNS 0`,
`results OK absent`, next run `J-gceg_product_page A 1`.

Limit carried to Phase 4 (unchanged from Phase 1): bank reachability through the shared object store is audited
from transcripts (V-E1-BANK-ACCESS-RECORDED records markers per run), not prevented.
