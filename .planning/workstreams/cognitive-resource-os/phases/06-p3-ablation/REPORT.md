# P3 instruction ablation — REPORT (2026-09-29)

Protocol: `vault/plans/cognitive-resource-os-P3-ablation-protocol.md` (committed before any counted run)
+ `ADDENDUM.md`. Raw data: `results.jsonl` (32 rows), `run.log`. Analysis script re-derives every figure
below from `results.jsonl` alone.

## Run
- Host laptop, claude 2.1.284, model `claude-opus-5-5` in both arms, BASE = the commit freezing
  `p3-tasks.json`. 8 tasks x 2 arms x 2 replicates = 32 runs, one `claude -p` session each.
- Validity: **32/32 valid on the first attempt, 0 replacements.** Every transcript MEASURED, every
  entrypoint `sdk-cli`, every grade printed its `_PASS=` line.

## Positive control (arm B really lacked R1)
first-call context, all 16 pairs: A 166,585–166,709; B 137,207–137,605. Per-pair A−B delta 28,996–29,488
tokens, which is the size of the three R1 files. `claudeMdExcludes` applied in every B run.

## Primary metric — task pass (the only one that decides)

| task | A r1 | A r2 | B r1 | B r2 |
|---|---|---|---|---|
| T1-tis-dedupe | pass | pass | pass | pass |
| T2-tis-bom | pass | pass | pass | pass |
| T3-tis-synthetic | pass | pass | pass | pass |
| T4-pricing-newest | pass | pass | pass | pass |
| T5-pricing-missing | pass | pass | pass | pass |
| T6-rollover-sealed-hash (R1 domain) | pass | pass | pass | pass |
| T7-budget-population (R1 domain) | pass | pass | pass | pass |
| T8-budget-unknown-not-zero (R1 domain) | pass | pass | pass | pass |

## Verdict (decision table row 1)
**B passes every task A passes, in 2 of 2 replicates -> R1 is a relocation candidate.**

## What this verdict does NOT show (read before acting on it)
- **Ceiling.** Both arms solved 16/16. The instrument could have returned "A-pass/B-fail" (B was a
  genuinely different prefix, proven above), but no task came near failing in either arm, so the set
  has no measured power to detect a small quality loss. The claim is "no degradation observed on
  8 seeded single-defect tasks graded by an existing test", not "R1 has no effect".
- **Task shape.** Every task hands the agent a failing test that points at the defect. R1's rules are
  about judgement where no test exists yet (choosing an identity, proving an absence, reachability).
  That behaviour is outside what this set can observe, including in the three R1-domain tasks.
- **B-prime (R1 reachable on demand) was not run.** The protocol names it; relocation should give B-prime,
  not B, so the moved rules must still be loadable when relevant.
- One host, one model, one CLI version.

## Secondary metrics (reported, never a tie-breaker)

| arm | runs | wall mean / median s | total context mean | total context sum | output mean | calls mean |
|---|---|---|---|---|---|---|
| A | 16 | 103.5 / 97.2 | 1,152,714 | 18,443,425 | 1,510 | 6.8 |
| B | 16 | 104.1 / 102.2 | 914,439 | 14,631,024 | 1,533 | 6.4 |

Total context read per task fell 20.7 % in arm B (mostly cache reads; ~29k per call x ~6.5 calls).
Wall time and output are unchanged within noise. A/A spread (the two A replicates of one task) reaches
1.73M vs 1.03M total context on T6 and 168 vs 99 s on T7, so per-task secondary differences below that
are not interpretable; only the 16-run aggregate is.

## Next step (Owner consent 2026-09-27: one reversible commit per move)
Per the table: move ONE R1 file at a time from always-loaded `~/.claude/rules/` to on-demand loading
(the B-prime shape), re-run that file's domain tasks after each move. Order by size:
instrument-before-claim, destructive-state-authorization, real-context-reachability. Recommended
before the first move: add at least 2 tasks per file with no pre-existing test (judgement tasks) so the
re-run can actually fail.
