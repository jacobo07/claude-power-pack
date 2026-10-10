# WU-W9 -- Knowledge promotion and the final Owner handoff

Common brief: `PROGRAMME.md`. Plan sections 5 (W9), 9. Needs W8 DONE. Iterate before UKDL, before CBR, before handoff.

1. KNOWLEDGE.md (every bug/failure of the programme) -> Knowledge Vault + FIOS entries, deduplicated against existing
   ones (search UKDL / `vault/knowledge_base/` and `python -m modules.gsd_x.recall --query "<x>"` first).
   Candidate failure classes (keep only the confirmed ones): FANOUT_BEFORE_READINESS, diagnostic label collapse
   ("environment"), EXPERIMENT_CANNOT_MEASURE_ITS_TARGET, SOURCE_UNCOMPILABLE_BY_CONSTRUCTION, FUNCTION_COST_
   INTRINSICNESS_FALLACY, FLAT_MARGINAL_COGNITION (only if measured), REPEATED_RAW_BINARY_PAGE_FAULT (only if measured).
2. UKDL: hard-rule / process-rule / trap candidates from the brief, promoted ONLY where this programme produced
   evidence; each cites its receipt. The rest stay listed as unproven candidates.
3. CBR: a proven mechanism (W1 lint, W2 certificate, the cascade record schema) becomes baseline only if it is wired
   (the send path or the producer calls it) and tested; list promotions and what is NOT promoted and why.
4. Backlog: update D21 in `vault/plans/deferred-backlog.md` with one paragraph pointing at the new budget file and
   the Scope-B admission line. Update `vault/backlog/2026-10-10_cp50-c2-remaining.md` with the C2b root cause.
5. Handoff: `vault/programs/tennis-rf/HANDOFF.md` with the Owner's final contract fields (plan section 9 and the
   brief's FINAL HANDOFF CONTRACT), every figure sourced, UNKNOWN where not measured. Programme spend from
   `mission_spend.py goal-status --goal tennis-rf`.
Receipt: Status DONE, links to HANDOFF.md and the budget file.
