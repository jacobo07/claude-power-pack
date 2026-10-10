# WU-W5b -- Measurement cohort 2: hard stratum + same-family learning sequence + holdouts (<= 1 GEX44 job)

Common brief: `PROGRAMME.md`. Plan sections 5-7. Needs W5a DONE. Read W5a's receipt and `measure/records.jsonl` first;
reuse its transform (do not rebuild it). Iterate after the sequence's third member.

Stop-loss (plan 7): if W5a + the first 6 here show no model-free closure AND fewer than 2 verified by the model path,
stop, write the residual, receipt DONE with that finding.
1. 6 functions with many unresolved types (>= 3).
2. Same-family sequence of 6: pick a family from W3's sample by shape/call-context (or from W7 if it already ran);
   do member 1 cold (record the floor), then members 2-6 reusing what member 1 produced (transform rules, struct
   layouts, claim ledger rows). The quantity is new-cognition tokens per member: does it fall?
3. Holdouts (only if budget allows after 1-2): tooling holdout = 3 functions with the type-repair transform disabled;
   model-routing holdout = 3 functions where the proposal is produced by a cheaper model call (Haiku via the
   cheapest available route) and judged by the same oracle. Record both or record why skipped.
4. One certified job for all candidates (JOBS.md first). Same record schema as W5a.
5. Claims learned (types, struct layouts, transform rules): write them as rows in `measure/claims.jsonl`
   (claim, evidence, confidence, invalidators, consumers) and make the transform READ that file, so the knowledge is
   machine-reachable, not prose.
Receipt: sequence curve (member -> new-cognition tokens), holdout deltas, job id, commits.
