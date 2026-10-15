---
class: SEARCH
# pre: none. Every deterministic step below needs a script that does not exist yet (draw/compose/stage per W12 evidence/w12/draw.py, records.py);
# a pre that points at absent scripts would only produce pre_failed. The worker writes them first (step 1), then runs them.
---
# WU-W13 -- next production wave, compiled from D28 evidence (PACKET: not run by WU-D10)

Status of this file: compiled 2026-10-13 by WU-D10. Common brief `D28-BRIEF.md` + `PROGRAMME.md`. Frontiers: `vault/plans/tennis-frontiers-2026-10-13.md`.
Tags: M = measured (source named), D = derived by arithmetic from M, H = hypothesis.

## Approval it needs (BLOCKED until given)
Jobs 5-6 are D8's and job 7 is D9's (JOBS.md, Owner 2026-10-13). W13 needs jobs 8 onward: **NOT approved.** Required line in JOBS.md before the worker sends anything:
"Owner approved jobs 8-N for W13" with N = 8 + (jobs below) - 1. Without it the worker writes `Status: BLOCKED_HUMAN` naming this and stops after step 2.
If D8/D9 end NOT_ADMITTED / BLOCKED_HUMAN, their unused slots (5-7) are NOT W13's; the Owner may re-point them by editing JOBS.md (that is an Owner act, not a worker act).

## Population (by D3 distance class, `evidence/d28/d3/residuals.jsonl`)
| class | n (M, D3) | in W13 | why |
|---|---|---|---|
| 0 | 12 | no | already MATCH (W12) |
| 1 | 263 | 254 | lint-clean; 9 were W12 PARTIAL (near-match, D2) -> handled by rule arm below. 254 = 276 lint-clean - 22 sent in W12 (D; matches D3 263 - 9) |
| 2 | 1,307 | probe of 40 only | pure fact-gap; D5/D6: single prototype deltas unlock 0 (11/12 CONTRADICTION; the 1 SUPPORT retracted by D6). Compile rate UNKNOWN -> measure on a seeded stratified 40, do not spend on all |
| 3,4,5 | 92 / 92 / 31 | no | tool-side (m2c) blockers or unexplained; D5 cror rewrite unlocked 0 of 67 |

## Certified facts it relies on
- Header `tennis_context.h` as sealed in wt_tennis_rf (W11/W12: 35 tags, 24 prototypes; TENNIS_CONTEXT_DRILL 9/9 after D6). D6 certified **0** new facts (M): the header is unchanged by D28. 175 -> 276 lint-clean is reproduced (D2: 101/101 with the full header, prelude-only 0/101).
- D1d: INCONCLUSIVE groupings (structural_family, idiom_family) are NOT usable as evidence; VALID: data_family(+anchored), motifs, 7 idioms. Do not select or batch by structural_family.
- Presets O4p only: every W12 O2 match also matched at O4p (M, MEASURE.md), so O2 is dropped (halves units per function).
- NOT relied on: D5 `fn_801D022C void(void)` (retracted D6), cror rewrite (unlock 0), D4 dominator rank (non-causal), UNDECLARED_MACRO/NULL fix (D2 rule written, fix UNMEASURED: include 80252F34-shaped fns only as the explicit NULL probe, below).

## Expected MATCH (measured rates only)
Rate: W12 12/22 lint-clean sent = 0.545, Wilson95 0.347-0.731 (M, MEASURE.md; D3). Applied to 254 unsent class-1: point ~139, **88-186 MATCH** (D). Caveat (H): W12 draw was from the W3 sample60 lint-clean pool; representativeness of the other 254 is unmeasured. The 40-fn class-2 probe: rate UNKNOWN, no expectation stated (W10c with no context was 0/12, M; the context lever is class-1-specific evidence only).
PARTIAL follow-up: W12 9 PARTIAL compress to 5 root classes (ratio 0.556, n=9, M, D2). Expected non-MATCH in W13 = 254 - (88..186) = 68-166 (D); at 0.556 that is ~38-92 rule-classes (H: ratio from n=9). Implement the 5 D2 codegen rules (flag/bool idiom, sda21 vs @ha/@l, size -1, pointer stride, ptmf r12) as a deterministic pre-job transform ONLY on functions whose m2c output matches the rule's stated pattern; a rule that has no red control passing is not applied.

## Job count (D)
Units/job: job 3 = 42 units (22 fns x O4p + O2-for-17, + 3 donor controls); judged 13 min after send (M). With O4p only, 1 unit/fn + 3 controls: ~39 fns per job at job-3 size (H: batch ceiling not measured; larger batches are not excluded).
- 254 class-1 / 39 = 6.5 -> **7 jobs** (jobs 8-14), or 1 job if a ~260-unit batch is accepted (UNKNOWN, ask the custody/capsule limit before sending; if accepted needs 1 approval).
- Class-2 probe 40 fns + 3 controls = 1 job (job 15; or part of the last class-1 job).
- Rule re-submission of PARTIAL (rules arm): 1 job.
Total: **9 jobs (8-16)** at W12 batch size; **2-3 jobs** if batches of ~130+ units are accepted. State the figure the worker actually validated.

## Token estimate and basis
Model calls on functions: 0 (layer is m2c + header + presets, as W12; MEASURE.md). Tokens are coordination: draw/compose scripts, staging, send, custody read-back, judging, records.
Basis (M, goal-lineage lease usage per D unit): D3 0.30M, D6 1.54M, D7 ~1.73M, D2 2.88M, D5v2 ~2.35M, D4 ~1.87M. Range of the deterministic D units 0.3-2.9M, median ~1.7M.
Estimate W13: **P50 ~2.5M, range 1.2-4.5M** (H: scales with job count; each extra job adds send+judge+copy-back turns, W12 whole session was 3.45M/52 calls incl. prep, a ceiling). Remaining programme: 100M - 84.3M used = 15.7M (M, goal-lineage 2026-10-13) -> W13 fits; D8/D9/W8b/D11 also draw on it.

## Steps
1. Write and test (RED first) `draw.py` (seeded; class-1 = all 254 unsent, class-2 stratified 40 by `size_insns` quartile, never in W5a/W12/D2-D7 sets), `compose.py` (m2c + header + rule transforms), `stage` per Recon Factory `stage.py certify`. Record the draw BEFORE candidates (MEASURE.md).
2. If JOBS.md carries no Owner line for these jobs: write `WU-W13-receipt.md` `Status: BLOCKED_HUMAN`, the exact approval above, and stop.
3. Per job: JOBS.md row BEFORE send, certified send, custody read-back, `evidence/w12/records.py`-style records from the ledger (receipt numbers come from the ledger; claim_evidence certificate).
4. Receipt: MATCH/PARTIAL/FAIL per group with Wilson intervals vs the 0.347-0.731 prediction; class-2 probe rate; tokens per MATCH; PARTIAL classes. A prediction outside its interval is reported, not explained away.
Done-check: `WU-W13-receipt.md` exists, status from the ledger certificate, records committed under `evidence/w13/` (pathspec).