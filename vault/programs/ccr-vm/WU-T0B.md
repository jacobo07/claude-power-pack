# WU-T0B -- CCR boundary CWS: floors, same-session reclamation, one flamegraph

Continues WU-T0A in the same worker after T0A's receipt is committed. Same packet, same forbiddens (no code change, no release, no settings, no capital request, no Tennis state change). Mode EXECUTION. Budget: P50 1.5M, hard 1.7M; the whole T0 stops at 3.0M processed. Headless probes use haiku with a ~1.5M guard (V1 lesson); if a probe would exceed its guard, record UNKNOWN and stop that probe.

## Tasks
1. HARD_HOST_FLOOR vs CPP_ADDED_FLOOR: measure provider-facing input tokens of a bare headless call with maximum safe CPP suppression, versus the default CPP load. Report both numbers and the difference. Extend `tools/context_floor_census.py` output if it already measures this; do not write a new tool.
2. Three same-session reclamation experiments on 2.1.302, each with a before/after provider input-token count and a yes/no verdict:
   a. Can `session.append` rewrite a tool output before it is stored (so later calls never carry it)?
   b. Can an already-resident tool message be altered or evicted by any hook (expected NOT_EXPOSED; prove or record UNKNOWN)?
   c. Does `tool.describe` isDeferred remove a schema from the provider request (measure, do not assume)?
   Classify each context source AVOID / RECLAIM / ROTATE-ONLY with the evidence. If CCR is in shadow on 2.1.302 (COMPAT), say so and mark the result "shadow".
3. Physical context per boundary: state what can be measured per call (input, cache read, cache write, output) and what cannot (per-row attribution is a PROXY). Reuse `tools/token_ground_truth.py`.
4. One flamegraph: take ONE historical large boundary (prefer the Tennis coordinator 85b7c296, 250K-300K per call) and attribute it to causal classes (host floor, history, tool output, schemas, skills, constitution, memory, proofs, dead carry, unknown) with a script that prints totals only. Do not read the transcript in this session. Label proxies.
5. Rotation feasibility: is there a host-supported way to start a fresh epoch with Goal continuity and no Owner pane choice? Cite the existing ASER / `gsd_mission` rotation path and its measured rehydration cost.
6. Session-age elasticity benchmark DESIGN only (no run): equivalent unit at short vs aged history, metric, pass threshold.
7. Write `vault/plans/ccr-vm-tranches.md`: T1..T11 re-checked against T0 facts, budgets re-forecast from T0 measured spend, first tranche that closes the main-session bypass, and conditions from plan section 13.

## Output (path-scoped commit, vault/ and tools/context_floor_census.py only if extended)
`vault/programs/ccr-vm/T0B-measurements.md`, `vault/plans/ccr-vm-tranches.md`, `vault/programs/ccr-vm/WU-T0-receipt.md` (total processed spend, what was MEASURED vs UNVERIFIED, answers to the plan's final meta-questions that T0 can actually answer, remaining Owner decisions). Then stop; do not start T1.
