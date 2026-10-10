# WU-W5a -- Measurement cohort 1: cascade on 12 Tennis functions (<= 1 GEX44 job)

Common brief: `PROGRAMME.md`. Plan sections 5 (W5), 6, 7. Needs W3 DONE. Iterate after the first measured function.

This is the redesigned C2b. It must contain the cognition it measures.
1. From W3's 60-row sample pick 12: 6 m2c-clean (0 unresolved types), 6 with few (1-2). Stratify by size; record the
   draw seed and list in `MEASURE.md` BEFORE any work.
2. Per function, in order, stop at the first layer that produces a candidate the oracle can judge:
   NO_WORK (already solved?) -> Resort exact-shape donor source -> deterministic type-repair transform (build it in
   this unit: resolve `?` from callee/caller signatures and known SDK headers, map `unk` offsets to structs already in
   the factory; abstain when unsure) -> model repair (this worker's own reasoning, bounded to the residual question;
   write a one-line Proof of Model Necessity first).
3. Batch all 12 candidates (all preset variants) into ONE certified job (W2), record it in JOBS.md, send, judge.
   For non-matches, one bounded repair round per function, judged in the same job only if the job is not yet sent;
   otherwise record the residual and stop (no extra job).
4. Per-function record (append to `measure/records.jsonl`): layer that closed it, verdict (MATCH / PARTIAL % / FAIL
   class), compiles, model calls attributed, processed tokens attributed (dedupe by message.id; attribute by the
   span of calls you spent on that function -- note the method), proof cost, unresolved-type count, family hint.
5. Also record this session's fixed costs: first-call floor, mean context per call, calls spent on control/status.
Receipt: table summary (closed per layer, tokens per verified function by layer, floor), job id, commits.
