# C2 cohort {{COHORT}} -- arm {{ARM}}, draw positions {{POSITIONS}} (ONE cohort, ONE fresh process)

Template, instantiated by the main pane per cohort (CP50 plan C2/C4; amendment (a) Context Rent). Slots: {{COHORT}}
{{ARM}} {{POSITIONS}} {{LEASE}} {{STOP}} {{CALLS}} {{MISSION}} {{EXECUTOR}}. Never run two cohorts in one process.
Mission {{MISSION}} (write it in the receipt). Lease {{LEASE}}, stop {{STOP}}, hard limit {{CALLS}} tool calls, 0
subagents, NO search tools. At the SESSION BUDGET warn advisory: checkpoint, receipt, commit, exit -- PARTIAL is a result.

## Preconditions (refuse the cohort, writing nothing, if any fails)
- `bench.py plan --draw <G0_FREEZE.json> --arm {{ARM}} --first <a> --last <b>` prints exactly one COHORT line for
  {{POSITIONS}}; the draw anchor 0f2ecb37... is recomputed by bench.load_draw, never trusted from this text.
- Arm B only: THRESHOLD_A.json exists (bench.read_b refuses B_LOCKED otherwise). Arm A: no THRESHOLD_A.json yet.
- The executor {{EXECUTOR}} exists and has its own drill PASS. C1 measured that NO arm-A executor existed
  (no candidates, no cohort capsule path; capsule_build.build selects from the factory ledger). The FIRST C2 lease builds
  it: candidates for the cohort ids (05-04 Task 1 design) -> a cohort capsule through capsule_build/custody only (GAP-3)
  -> GEX44 job on the RF root (cap 4, GAP-10; GAP-7/9 checks before the enqueue) -> repatriate -> records.
- Never read G0_HOLDOUT.json.

## Work
1. Run the cohort through `bench.run_cohort({{ARM}}, cohort, executor={{EXECUTOR}}, out=<arm>.jsonl)`.
2. One record per function, schema ksr.recon.bench_record/1: cost {wall_s, compiles, local_tokens, paid_tokens,
   new_cognition_tokens} and amendment (d) {fresh_floor, live_frontier, ctx_mean, ctx_p95, marginal_context_rent,
   physical_calls, deterministic_vs_cognitive, novelty, cost_to_verified, proof_cost, rehydrations, family_reuse,
   capital_class}. Unmeasured = {"absent": "<reason>"}, never 0. host_plane = the plane the compile ran on (GEX44).
3. Token fields come from the control plane's metered receipt for THIS process, not from the worker's own estimate.

## Close (in this order, then the process exits)
1. Checkpoint: append the records; print their count and the jsonl sha256.
2. SAFE_TO_FORGET: one line naming what the next cohort needs (the jsonl path + sha256, the next positions) and nothing
   else from this context.
3. Receipt `gen3/C2-cohort-{{COHORT}}-receipt.md` (<= 15 lines): mission, calls, records n, jsonl sha256, per-function
   cost table, PAID count, open points. Commit by pathspec in each repo. End with `HANDOFF NOTE: cohort {{COHORT}} done`
   or the blocker. Ending on a question counts as a failure.
