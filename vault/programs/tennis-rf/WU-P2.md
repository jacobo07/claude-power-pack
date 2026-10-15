# WU-P2 -- reprice the Tennis residual by class, choose the next strategy, institutionalize (KV / FIOS / UKDL / CBR)

Plan: `vault/plans/recon-factory-locality-routing-2026-10-15.md` sections 16, 18 (Owner approved 2026-10-15 "y").
Requires WU-P1 receipt (EVC table) and WU-R3 (strategy.json machinery). Budget: <= 2.0M; stop and write the receipt at 1.7M.

Steps:
1. Segment the residual: classify every class 2-5 function (D3 `residuals.jsonl`, D12a `residuals_v1.jsonl`,
   near-match signals where present) with the WU-R2 router classes; counts per class plus "near-match / known family /
   semantic / architecture blocker / unknown". Record the router's version and any fn it cannot classify (UNKNOWN, never
   folded into another class).
2. Reprice: per class, expected cost to close = population x P1's measured EVC for that class. A class with no measured
   close is UNPRICED (not zero, not infinite); give the spend that produced 0 closes. Tranches: cheap deterministic,
   CPU search, family synthesis, model-semantic, deep RE. Closure curve by class, labelled as an estimate with its basis.
3. Next strategy: write candidates into `strategy.json` (WU-R3 format) with expected_evc, info_gain, capital, packet path
   for any candidate that is positive-EVC and fits the remaining envelope (chain envelope 148,150,000; reserve 1.85M is not
   spendable). If none is positive: write the terminal economic verdict `vault/programs/tennis-rf/VERDICT.md` (what is
   closed, what each remaining class would cost, why stopping is correct) and leave the chain returning
   `strategy_exhausted`.
4. Institutionalize (PP, pathspec commits, deduplicate against existing ids first):
   - Knowledge vault records (symptom, trigger, evidence, root cause, economic effect, corrective architecture, proof,
     regression guard, lesson, invalidators) for the confirmed failures only: COORDINATOR_SPEND_OFF_LEASE (19.25M),
     STATIC_CHAIN_EXHAUSTED_WITH_POSITIVE_RESIDUAL, NEGATIVE_CONTROL_NON_DISCRIMINATIVE, T1_TRANSFER_UNMEASURED,
     JUDGE_PROFILE_COUPLING (not leakage), LEDGER_NO_SUPERSEDE (15 vs 27), and any found in R1/R2/P1/R3 receipts.
   - FIOS promotion where `tools/` exposes it; UKDL (`vault/knowledge_base/ukdl-universal.md`): Hard Rule / Process
     Rule / Trap candidates from the plan, promoted only where a receipt proves them.
   - CBR: add the proven pieces (router classes, permuter backend if ADMITTED, judge contract, supersede, control
     standard, coord guard, strategy transition) to the reconstruction baseline doc; retire bulk composition after flat T2.
5. Update `RESUMPTION_FILE.md` of wt_tennis_rf with the new state.

Limits: no GEX44 job, no model calls on functions.
Done-check: segmentation counts sum to the residual population; strategy.json or VERDICT.md written; KV/UKDL entries
committed. Receipt `WU-P2-receipt.md`: class table, tranches, next strategy or verdict, entries written (ids), commits.
