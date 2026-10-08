---
id: SPEC-CTX-RENT
title: Context Rent Extinction -- rotate interactive panes on economics, not at the wall
tier: T2
status: approved
covers: [context-rent-extinction, ctx-rent, rollover-policy, kresume-diet, wide-boundary, rent-meter, test_context_economics]
owner_go: "y+floor" (2026-10-08) -- includes trimming CPP instruction files under ~/.claude and retiring "/compact at 70%"
goal: ctx-rent (mission_spend goal-declare, cap 6,000,000 incl. coordinator pane; root C:\Users\User\Apps\pp-ctx-rent)
parent: vault/specs/interactive-context-rollover.md, vault/specs/economic-rollover-trigger.md
sibling: vault/plans/ce-a4-estate-rearm-2026-10-08.md (owns mission/worker side; NOT duplicated here)
---

# Context Rent Extinction

## 1. Reality (rollover ledger, 7 days to 2026-10-08, 2,215 rows)

The /kclear -> SAFE_TO_FORGET -> /clear -> /kresume lifecycle is live (510 seals, 201 safe resets,
207 certified, 22 failed). Provider /compact is already fallback-only. Rotation is LATE:
max resident before a safe reset p50 450,053 / p90 482,706 (n=277, ESTIMATED attribution).

| # | Cause | Evidence |
|---|---|---|
| RC1 | `MIN_GROWTH_TOKENS = 150_000`: no economic rotation below ~floor 124k + 150k | 207 econ rows "growth < 150k" |
| RC2 | econ evaluation only on a new HEAD at >= 20 % used | ~201/277 rotating sessions rotated only at the wall |
| RC3 | ROBUST_ROLLOVER needs 75 % share at n* + C/G with C = 1.78M upper bound; prior unconditioned, CONTINUE unreachable | 292/666 UNDETERMINED |
| RC5 | successor rehydration C p50 1.78M processed tokens before first mutation | `rehydration_tokens` in decisions |
| RC6 | 114 wall rows "usage no transcript" | ledger |
| Floor | fresh first call ~105k (S1 measured); CPP instruction files ~52k ESTIMATED | gen2 S1-decomposition.md |

## 2. Units (extend only: rollover.py, rollover_wall.js, rollover_econ.py, rollover_replay.py, commands/kresume.md)

- S1 rent meter (deterministic, transcripts): resident/call, floor, MCR = resident - (floor + capsule), labels MEASURED/ESTIMATED/UNKNOWN; freeze BEFORE baseline; close RC6.
- S2 successor diet: obligation-scoped goal section + exact refs; page on miss; target C -30 % on real crossings, else PLAN mode.
- S3 wide boundary: commit | clean tree | task done | question-to-Owner closer | growth step; one evaluation per boundary.
- S4 policy: derived minimum growth (anti micro-epoch), state-conditioned prior (CONTINUE reachable), economic-rent ceiling. 45 % wall + autocompact remain safety nets.
- S5 budget edge / pre-model admission: CONNECT goal-admission; checkpoint reserve.
- S6 compact_fallback ledger event = lifecycle miss.
- S7 tools/test_context_economics.py with positive controls + mutants; reachability registered.
- S8 KV/UKDL/CBR; prompt extinction (manual /kclear guidance, kclear-when, "/compact al 70%" rule, instruction-file trims).

## 3. Canaries

Here: 1,2,3,4,5,6,8,11,13,14. From A4 evidence: 7,9,10,12. Production Reality spends subscription quota.

## 4. Done-Gate

Every clause MEASURED. Minimum: p50 max-resident-before-rotation falls from 450k; C falls >= 30 %;
>= 1 KEEP and >= 1 ROTATE decision observed; one automatic self-hosted crossing. Unreached = UNKNOWN/DEFERRED.

## 5. Rollback

`CPP_ROLLOVER_ECONOMIC=0`, `CPP_ROLLOVER_WIDE_BOUNDARY=0`, `CPP_ROLLOVER_ACTIVE=0`; one revertible commit per unit.
Host limit: /clear typed only into Orca/PP-Sessions-owned panes; elsewhere refused (Owner submits).
