# Gen3 T1 README (2026-10-05, pane subagent of 87601e81)
Unit: processed tokens (input+cache_write+cache_read+output, dedup by message id). All scripts zero-model. Raw outputs: k1_out.txt, regress_out.txt, k2_out.txt, k4_out.txt, OBLIGATIONS-io-phase4.md. Cache: g3_extract.py over 237 distinct main sessions (since 2026-10-02) -> scratchpad cache.json (not committed).

## Decisive finding (changes Stage 0 / Gen2.1)
hook_success records are NOT model context. Regression of 29,028 call-intervals (g3_regress.py): tool_result 0.447, rendered attachments 0.38-0.43, assistant output 0.998 tok/char (positive controls); hook_success stdout 0.03-0.05 (shuffled-column negative control 0.02); big-vs-small hook_success intervals differ by 0.9 tok where 200 would be expected. Records that reach the model carry a top-level endered field; hook_success has none. So the Gen2.1 "hook success text 11-13% of main context" is a record-vs-context misattribution. Counterfactual if it WERE context: 2.83% of estate main context (182M of 6.43B), 1.3-2.4% per workload (k4 b').

## K1 floor after E1 (commit 288c5a28)
Only n=1 main session estate-wide started after 12:34Z (a5fafaa2); per-project n>=3 sets: none -> first-call median effect UNKNOWN (point: 124,464 vs same-day PP n=7 median 128,760 = -4.3k; estate same-day n=17 median 128,169). Positive control PASS: instructions attachment 159,755 -> 131,735 chars in the same project (-28,020 chars ~ -9.0k tok at 0.32; 32,121 B rule-text figure is bytes). Used in K4: d=3,705 (measured, n=1) and d=8,966 (instructions-implied).
STATE.md of cognitive-economy-e1 was clean -> status executed; REPORT hash 9787a946 is NOT in this checkout (UNVERIFIED).

## K2 hook inventory (k2_out.txt)
Model-visible hook text = hook_additional_context only: 5,199 events, 188.9M tok rent = 2.94% of main context (6.43B). By event: UserPromptSubmit 84.7M, SessionStart 69.4M, PreToolUse:PowerShell 21.1M, others <5M each. Top emitters: superpowers plugin 58.5M (0.91%, THIRD_PARTY_PLUGIN, not CPP), tower-baseline 23.9M (0.37%), ExecutionOS Lite tier FORENSIC/DEEP 16.4M+12.8M, woz 10.5M (1,575 events, median 235 chars), Graph-First 10.0M, cross-project-baseline 6.3M, persisted-output 5.9M, skill-advisor 5.9M. CPP_CONTROLLED (text produced by the CPP dispatcher chain / hooks under ~/.claude/hooks: dispatcher joins hook additionalContext with a blank line; anchors found in hook-dispatcher.js, correction-guard.js, learning-sentinel.js, research-intent-detector.js); no single CPP cluster reaches 1% of main context (max 0.37%). Origin file UNKNOWN for tower-baseline, skill-advisor, ExecutionOS Lite, Graph-First (anchor not in ~/.claude/hooks .js/.py). HOST_IMPOSED: the framing wrapper (<system-reminder> + "<event> hook additional context:") = 420,785 chars = 6.2% of rendered hook chars; hook_success recording itself (host). hook_system_message: 1,526 events, 0 rendered (not context). Repo dispatcher mirror hooks/hook-dispatcher.js has the same 1,613 lines as the live one (line-count only; not diffed).

## K4 factorial (CEILINGS / counterfactuals, k4_out.txt). KSR control: ctx 273,912,110 EXACT MATCH.
| workload | base | (a) floor | (b) hook ctx | (c) meta c=0/2/5M | (d) grid N10S10k..N40S30k | (e) combined N20/S10k c=0/2/5M (a=impl) |
|---|---|---|---|---|---|---|
| KSR 274.58M | | -1.5/-3.7% | -1.6% | -18.1/-9.4/+3.7% | -43.2..-22.9% | -55.8/-47.0/-33.9% |
| InfinityOps 374.55M | | -1.5/-3.7% | -1.6% | -22.6/-17.2/-9.2% | -43.7..-22.1% | -56.0/-50.6/-42.6% |
| KME 107.76M | | -1.4/-3.3% | -2.2% | 0 (no planner/researcher/checker runs) | -43.7..-29.2% | -45.2% |
Meta runs removed: KSR 12 (49.7M), InfinityOps 10 (84.6M). Hook arm (b) is hook_additional_context only, main calls; hook_success arm is 0 as measured. (d) is the ksr_floor.py capsule ceiling; (e) is sequential a>b>c>d, not additive. Not savings: break-even c for meta removal is ~4.1M/run (KSR) -> compilation cost decides.

## K5 (OBLIGATIONS-io-phase4.md)
obligation rows 6 decisions 5 flags 0. Extractor is a FLOOR (list/table lines only; prose obligations not extracted); types are keyword heuristics, unreviewed.

## K3 hook success-text policy: NOT IMPLEMENTED (by design)
hook_success is a host record of hook stdout with measured model rent ~0 (K2), so there is no success text in context to silence; implementing would change nothing measurable. HOST_IMPOSED for the record, CPP-controlled for the stdout content. Files changed: NONE; no live paths to deploy. Possible follow-up needing Owner decision: compact the model-visible advisory hac (woz/tower-baseline/ExecutionOS tier) -- ceiling (b) is only 1.6-2.2% of context, so low priority.

## Spend and scripts
Own metered spend at README time: agent-ac0efaaaee9221fbd.jsonl calls 32 processed 4,931,354 (cap 6M). 
- g3_extract.py sha256:77E705905729
- g3_k1_floor.py sha256:CBDE27AC9371
- g3_k2_hooks.py sha256:CAB087928E9A
- g3_k4_factorial.py sha256:91FF12F55023
- g3_k5_obligations.py sha256:9BFF0536D61B
- g3_meter.py sha256:BDA535F7199A
- g3_regress.py sha256:C17FBBF0A758