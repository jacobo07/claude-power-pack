# DWS-BUDGET-FINAL (ce-a5 U10)

READ-ONLY recompilation: no DWS product work executed. Every figure carries a `[src: ...]` tag; UNKNOWN is never 0.

## Compilation time

- Compiled at 2026-10-09T22:05:44+00:00 [src: system clock at tools/a5_u10_budget.py run]
- Work tree branch ce/a5, goal ce-a5 cap 20,000,000 tokens [src: mission_spend goal-status]

## DWS HEAD and worktree

- HEAD 466b62d82 (expected 466b62d82): MATCH [src: git -C D/orca-dws log -1]
- Worktree status: `?? .planning/` (untracked .planning/ is git-excluded by design) [src: git -C D/orca-dws status --short]

## Scope

- Priced: 44 open claims with obligations; parked and not priced: 46 sleeping claims (UNKNOWN cost) [src: inputs/dws-budget-compiled.json]
- Owner-only (zero model tokens): 2 claims; deterministic: 1 [src: inputs/dws-budget-compiled.json]
- Not in scope: executing any DWS claim, the sleeping claims' own pricing, quota measurement [src: packet U10]

## Counts

- Matrix rows 76: PASS 11, PARTIAL 33, ABSENT 31, UNKNOWN 1 [src: D/orca-dws/config/dws-completion-matrix.jsonc]
- DONE 11 (matrix PASS rows, not in claim list) [src: matrix state field]
- NO_WORK 0 obligations (no valid reusable proof with a measured invalidator) [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- NO_COMPUTE 42 obligations (script-only evidence stamp) [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- DETERMINISTIC 1 claim (vis-pixel-gate) [src: inputs/dws-budget-compiled.json]
- KNOWN_TRANSFORM 11 claims [src: inputs/dws-budget-compiled.json]
- BOUNDED_FAMILY 19 claims -> 19 family obligations [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- NOVEL 12 claims (of which visual 2) [src: inputs/dws-budget-compiled.json]
- REALITY 14 distinct observations over 11 claims [src: inputs/dws-reality-obs.json]
- OWNER_ONLY 2 claims (row-46, p25-sc4-physical-pcs) [src: inputs/dws-budget-compiled.json]
- SLEEPING/BLOCKED 46 claims [src: inputs/dws-budget-compiled.json]

## Old-architecture baseline

- Runnable candidate 6,501,959,646 tokens over 25,683 calls; with margin 7,802,351,576; ceiling 11,016,344,430 [src: inputs/dws-budget-compiled.json]
- Reproduced by the extended cost_to_completion: 6,501,959,646 tokens, flag HISTORICAL_PROFILE [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json; historical doc in tools/a5_u10_budget.py]
- Unblocked (all 46 sleeping included) 14,456,816,010 tokens [src: inputs/dws-budget-compiled.json]
- Measured history: 8,066 calls, 2,042,008,282 processed tokens for 19 steps = 424.5 calls/step, ctx 253,162/call [src: inputs/dws-budget-compiled.json]

## New irreducible lower bound

- 76 irreducible items = 32 decisions + 11 distinct observations + 33 assurance judgments + 0 owner decisions (kind: estimate) [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- Token floor if each item cost one call at the slim floor: 1,026,532 tokens ESTIMATE (76 x 13,507) [src: lb above x tools/a5_counterfactual.SLIM]
- Overhead multiplier input: 337.9 (historical 25,683 calls / 76 items) [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- This closes the U0 ledger UNKNOWN rows P1-63 / P1-64 (DWS lower-bound number), as an estimate [src: A/U0-receipt.md]

## New execution profile

- Floor per call 13,507 (slim), rotation every 20 calls with a 2,500-token capsule, STATE card, read-once, poll->event, stall K=14 [src: A/COUNTERFACTUAL.md, A/STALL.md, A/PROJECTION.md]
- Replay of policy f: 322,165,170 processed tokens, 9,780 calls vs actual 3,100,841,244, 10,985 [src: A/COUNTERFACTUAL.md]
- ctx per call under f, capsule 2500: n 9,780, mean 32,941, p50 30,508, p90 59,415 [src: replay of A/data/calls.jsonl.gz by tools/a5_u10_budget.ctx_stats]
- ctx per call under f, capsule 10000: n 9,780, mean 38,353, p50 36,720, p90 62,863 [src: replay of A/data/calls.jsonl.gz by tools/a5_u10_budget.ctx_stats]
- Calls per obligation (lower / expected / p90-ceiling): known_transform 2/19/189, bounded_coding 6/64/676, novel 15/100/661 [src: lower = cost_to_completion PRIORS (chosen, not measured); p90 = mean budget est_calls per class x f call ratio 9780/10985; expected = geometric mean]
- New-grammar flag HISTORICAL_PROFILE = False (all three model classes priced from `profiles`) [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]

## Token budget

Processed tokens (ctx-sum currency of the trace corpus; output tokens excluded), by component.

| component | lower | expected | P90 | hard ceiling | source [src: Token budget] |
|---|---|---|---|---|---|
| known-transform | 671,176 | 6,884,669 | 148,228,542 | 156,830,613 | [src: compile_cost subset by obligation category] |
| family | 2,257,592 | 25,232,806 | 568,530,252 | 601,523,475 | [src: compile_cost subset by obligation category] |
| novel | 4,576,200 | 32,941,000 | 471,279,780 | 1,495,887,948 | [src: compile_cost subset by obligation category] |
| visual | 915,240 | 6,588,200 | 94,255,956 | 299,177,590 | [src: compile_cost subset by obligation category] |
| proof | 2,013,528 | 20,654,007 | 444,685,626 | 470,491,838 | [src: compile_cost subset by obligation category] |
| reality | 854,224 | 8,762,306 | 188,654,508 | 199,602,598 | [src: compile_cost subset by obligation category] |
| closeout | 1,037,272 | 10,639,943 | 229,080,474 | 242,374,583 | [src: compile_cost subset by obligation category] |
| recovery | 0 | 10,946,888 | 420,364,168 | 1,018,971,262 | [src: compile_cost subset by obligation category] |
| **TOTAL** | 12,325,232 | 122,649,819 | 2,565,079,306 | 4,484,859,907 | [src: sum of components] |

- Scenarios: lower = prior calls x p50 ctx; expected = geometric-mean calls x mean ctx; P90 = historical-per-class calls x p90 ctx x 1.2 margin; ceiling = P90 calls x p90 ctx at capsule 10,000 x same margin with novel deopt x3 [src: tools/a5_u10_budget.compile_all]
- Closeout = 17 phases touched x one known_transform pass; recovery = 0.098 / 0.196 / 0.294 of the subtotal (expected/P90/ceiling), 0 in lower; 0.098 = historical RECOVERY label share [src: A/TRACE-REPORT.md section 1; multiples are chosen]
- Uncovered observations priced as one known_transform pass each: gex44-heavy-exec, login-portatil, login-sobremesa (3) [src: tools/a5_u10_budget; reachable only via owner_reality claims]

## Model routing shares

- claude-opus-5: 39,529,200 expected tokens = 32.2% [src: routing assumption by category (judgment) x A/dws-claims-semantic.json]
- claude-sonnet-5: 83,120,619 expected tokens = 67.8% [src: routing assumption by category (judgment) x A/dws-claims-semantic.json]
- Routing is an assumption: sonnet for transforms/proof/reality/closeout/recovery, opus for novel and visual decisions [src: judgment, no measured routing outcome]

## USD

| scenario | cache-read floor USD | measured blended USD | source |
|---|---|---|---|
| lower | 4 | 4 | [src: anthropic_2026-09.json cache_read by routed model; blended = tokens x 0.3641 USD/Mtok from inputs/dws-budget-compiled.json] |
| expected | 36 | 45 | [src: anthropic_2026-09.json cache_read by routed model; blended = tokens x 0.3641 USD/Mtok from inputs/dws-budget-compiled.json] |
| p90 | 683 | 934 | [src: anthropic_2026-09.json cache_read by routed model; blended = tokens x 0.3641 USD/Mtok from inputs/dws-budget-compiled.json] |
| ceiling | 1,435 | 1,633 | [src: anthropic_2026-09.json cache_read by routed model; blended = tokens x 0.3641 USD/Mtok from inputs/dws-budget-compiled.json] |
- Old runnable candidate USD 2,368, with margin 2,841, ceiling 4,011 [src: inputs/dws-budget-compiled.json]
- Cache-read floor excludes cache writes (rotation re-writes the capsule each segment) and output tokens, so it understates; blended rate comes from the historical mix and may not transfer [src: pricing file notes; judgment]

## Quota reality

- Subscription quota consumed by this budget: UNKNOWN (never measured in this mission) [src: no measurement exists]
- Goal ledger so far: used 5,351,527, settled 4,601,527, open hold 750,000, remaining 14,648,473 of cap 20,000,000 [src: mission_spend goal-status --goal ce-a5]

## Confidence

- LOW overall. Token ctx per call is a replay of measured traces (LOW-MED); calls per obligation are NOT measured (priors vs historical bracket); the 46 sleeping claims are unpriced [src: A/COUNTERFACTUAL.md confidence column; this document]
- Spread expected->P90 20.9x and P90->ceiling 1.7x [src: Token budget table]

## Assumptions

- A1-A11 of the counterfactual replay hold (ctx-only currency, growth independent of policy, capsule 2,500, no event wake cost) [src: A/COUNTERFACTUAL.md]
- Calls per obligation lie between cost_to_completion PRIORS and the historical per-class calls scaled by the f call ratio [src: tools/a5_u10_budget.compile_all]
- Claim classes (known/bounded/novel) are inherited from the old compile and not re-judged [src: inputs/dws-budget-compiled.json]
- Observation set and Owner minutes from U4 are hand-derived estimates [src: A/REALITY-PLAN.md]
- Stall trip K=14 and resource admission are guards, not savings: K=15 cuts 1.79% of corpus tokens and is not counted [src: A/STALL.md]
- Judgment calls on obligations are listed in A/dws-claims-semantic.json under `judgments` [src: A/dws-claims-semantic.json]

## Top uncertainties

- Rotation capsule fidelity and re-derivation after rotation are not modelled; this alone moves the replay from -46% to -39% on rotate N=40 vs 12 [src: A/COUNTERFACTUAL.md rows b1-b3]
- Calls per obligation: expected vs P90 differ by the call bracket above; no worker has run the new grammar [src: Token budget table]
- 46 sleeping claims unpriced; the old unblocked scope was 14,456,816,010 tokens [src: inputs/dws-budget-compiled.json]
- Real worker replay on the STATE card never run (static fault check only: 0 FAULT of 119 reads) [src: A/PROJECTION.md]
- Owner session minutes (55 single-sitting) assume all PCs and phone available together [src: A/REALITY-PLAN.md]
- Two live-dispatcher guard tests fail outside scope (V-SBG-WIRED, V-SBG-E2E) [src: A/U7-receipt.md]
- Consistency note: the lower bound counts 0 owner decisions while 2 claims are OWNER_ONLY; owner ACTIONS (login, physical PCs) are reality observations, not decisions [src: A/REALITY-PLAN.md]
- Consistency note: NO_COMPUTE 42 means evidence stamps produced by script, i.e. no model call for the stamp; it does not mean the underlying work is done [src: Counts section]

## Savings vs old

- Old runnable candidate 6,501,959,646 vs new expected 122,649,819, new P90 2,565,079,306, new ceiling 4,484,859,907 tokens: two independent compiles, not a percentage of the old [src: Old-architecture baseline; Token budget table]
- Even the new hard ceiling is below the old runnable candidate [src: comparison of the two figures above]
- Difference old - new expected = 6,379,309,827 tokens [src: arithmetic on the two compiled figures]

## Extinguished

- Work: 42 evidence stamps become scripts; 1 pixel gate is a script; read-once and poll->event remove calls (10,985 -> 9,780 replay calls) [src: A/COUNTERFACTUAL.md; src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- Boundaries: reality acquisitions 35 -> 14 distinct observations; sessions 11 -> 1 [src: A/REALITY-PLAN.md totals]
- Context: floor 110,835 -> 13,507 per call; mean ctx per call 253,162 -> 32,941 [src: src: inputs/dws-budget-compiled.json; replay ctx_stats]
- Proof: 42 proof obligations share 33 distinct proofs [src: tools/cost_to_completion.compile_cost on A/dws-claims-semantic.json]
- Owner work: 220 min per-claim -> 55 min one session (165 saved, ESTIMATE) [src: A/REALITY-PLAN.md]

## OLD vs NEW

| dimension | OLD | NEW | source |
|---|---|---|---|
| runnable tokens | 6,501,959,646 | expected 122,649,819 (ceiling 4,484,859,907) | [src: budget JSON; this file] |
| calls | 25,683 | expected 3,011 priced obligation calls | [src: budget JSON; compile_cost] |
| ctx per call | 253,162 | 32,941 | [src: budget JSON; replay] |
| first-call floor | 110,835 | 13,507 | [src: budget JSON; counterfactual SLIM] |
| unit of cost | claim x phase-sized est_calls | obligation x class calls | [src: tools/cost_to_completion.py] |
| runnable USD (blended) | 2,368 | 45 | [src: budget JSON; USD table] |
| Owner minutes | 220 | 55 | [src: A/REALITY-PLAN.md] |
| stall trip K | 25 | 14 | [src: A/STALL.md] |

## Meta-analysis

**What caused 424 calls/step?** [src: A/U1-receipt.md]
- The figure is 8,066 calls / 19 steps = 424.5 [src: inputs/dws-budget-compiled.json]; the mission's own step definition (rows whose state changed) gives 269.7 calls/change [src: A/U1-receipt.md]. Context share by label: NOVELTY 38.4%, MUTATION 22.3%, PROOF 10.5%, RECOVERY 9.8%, CONTROL_LOOP 7.1%, REDISCOVERY 5.4%, STATE_READ 5.2% (proxy labels) [src: A/U1-receipt.md]. The first-call floor alone is 36.2% of processed tokens and subagents carry 87.1% [src: A/U1-receipt.md]. Call count per step is not reduced much by any policy (10,985 -> 9,780 calls); the saving is per-call context [src: A/COUNTERFACTUAL.md].
**Global vs DWS-local?**
- Global (PROMOTABLE): slim floor, rotation, combined f (gains 42.4/36.6/75.7% on the CE holdout and 30.5/57.1/85.8% on ql-quickie). DWS-local: read-once, STATE projection, poll->event [src: A/HOLDOUT.md].
**Rejected as negative ROI?**
- 36 ledger rows dispositioned NEGATIVE_ROI (e.g. P1-19 tool schemas as memory, P2-11 cross-project computation market, P2-13 shadow price of uncertainty) [src: A/LEDGER.json]; no replay policy fell below 3% so none was dropped by the counterfactual [src: A/U2-receipt.md]. Tool-schema share of the floor is UNKNOWN [src: A/COUNTERFACTUAL.md].
**Largest remaining debt?**
- Unmeasured calls per obligation (the P90/expected spread is 20.9x), then rotation capsule fidelity, then the 46 unpriced sleeping claims, then the Owner reality session (55 min) [src: Token budget table; A/COUNTERFACTUAL.md; A/REALITY-PLAN.md].
**Could another bounded pass have positive NPV?**
- A pass costs at most the unit cap of 1,000,000 tokens [src: packet U10]; the expected-to-P90 gap is 2,442,429,487 tokens [src: Token budget table]. A single instrumented DWS obligation run (real calls per obligation, capsule fidelity) would shrink that gap, so a bounded measurement pass is plausibly positive NPV; a further paper compile is not (no new information) [src: judgment]. This is the OPTIMIZE FURTHER case; approving execution without it spends against LOW confidence.

## Universal iteration pass

Applied once (inputs/iteracion-avanzada-universal.txt).
- REALITY CHECK. Source read: packet U10 lines 1-31, A/U*-receipt.md, inputs/dws-budget-compiled.json, D/orca-dws matrix. Exact error: the Owner's mission text 'FINAL DWS TOKEN BUDGET OUTPUT' is not in the work tree (grep over vault/ and tools/ finds only the packet). Premise false: yes - the section order is taken from the packet's list [src: grep of W].
- CLASE 2: the plan assumed a mission text on disk; it was not. Fix: use the packet's enumerated order, record the deviation in the receipt [src: grep of W].
- CLASE 5 guard: DONE is claimed only with the test output pasted in the receipt (A5_U10_PASS). No placeholder remains; UNKNOWN is stated where unmeasured [src: tools/test_a5_u10.py].
- UKDL seed: PR-CE-A5-001 'budget text is only as good as its unmeasured call count: price calls per obligation before approving' [src: this pass].

DECISION REQUIRED
APPROVE DWS EXECUTION
or
OPTIMIZE FURTHER
