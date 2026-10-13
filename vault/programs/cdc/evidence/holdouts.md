# C10 holdouts + cross-domain canary (2026-10-13)

Tool: `tools/cdc_holdout.py` (offline, zero model calls; reuses `cognitive_pgo.analyse_file` + `session_autopsy` roles; test `tools/test_cdc_holdout.py` 7/7).
Raw per-trace numbers: `holdouts.json`; roles per trace: `C10/roles-*.json`. EVC U8 replay harness not used (offline role replay was enough); rollover_replay not needed.
None of these traces was used to design C1-C8 (C1 used the QuickLease InfinityOps trace 6ddc58ea only).

**Avoidable under CDC rules** = REREAD + RECOVERY + CONTEXT_FAULT tokens + every call beyond the C4 breaker trip (25 consecutive no-progress calls).
This is a replay of what the rules would flag, NOT a measured saving: the deployed dispatcher has no C3/C4 hooks (C9), so none of these runs were governed.
**Admission denials: UNKNOWN** (historical transcripts do not record them; not 0). Proof closure: `proof>other` pairs counted per trace (heuristic, refetch candidates).

## Scope-normalized table (tokens = processed tokens incl. subagent files)

| Holdout | traces | calls | tokens | avoidable | breaker trip (calls / tokens, share) | progress events | tokens per progress event | top avoidable causes |
|---|---|---|---|---|---|---|---|---|
| Live QA packet workers (io-liveqa) | 11 | 251 | 10.88 M | 7.1 % | 3 / 0.15 M, 1.4 % | 49 | 222 k | RECOVERY 2.7, CONTEXT_FAULT 1.7, TRIP 1.4, REREAD 1.2 % |
| Clock A (e0cd1dbb, be97307b) | 2 | 1,934 | 304.2 M | 15.1 % | 10 / 1.56 M, 0.5 % | 552 | 551 k | CONTEXT_FAULT 9.6, REREAD 2.8, RECOVERY 2.2 % |
| Intent/order (ec66dcff) | 1 | 2,292 | 371.0 M | 17.0 % | 21 / 3.52 M, 0.9 % | 624 | 595 k | CONTEXT_FAULT 8.9, REREAD 5.9 % |
| DWS (14 sessions >2 MB in orca-dws-wt) | 14 | 10,719 | 3,069 M | 20.2 % | 589 / 179.8 M, 5.9 % | 2,533 | 1.21 M | REREAD 6.6, TRIP 5.9, CONTEXT_FAULT 5.3, RECOVERY 2.6 % |
| (ref) QuickLease Phase 1 (C1, design trace) | 1 | 807 | 126.3 M | not computed here | -- | -- | 1.30 M per transition | READ 31.8 % |

Excluded: the 4 `dws-p2-baseline` transcripts are 1-call stubs (~159 k tokens each, no work); listed in `holdouts.json`, left out of totals.
Worst single traces (DWS): 65129fef 36.4 % avoidable (190 trip calls, 50.9 M tokens); b14d678c 30.6 %; 9983ff03 28.1 %; 4aa2e2d3 26.1 %.

## Reading
- PROVEN (replay): the same waste classes C1/C8 found in QuickLease (CONTEXT_FAULT, REREAD, no-progress runs) recur on four unrelated holdout families, so the rules are not QuickLease-specific. Avoidable share is 7-20 % by family vs a single-digit share only for short Live QA workers (15-31 calls each; they stay under the trip point in 10/11 traces).
- The breaker (trip 25) matters mostly for long autonomous runs: DWS 5.9 % of tokens; Clock A / intent-order < 1 %. There the avoidable mass is context faults and rereads, i.e. C5/C6 (closure, derivation store), not the breaker.
- NOT_PROVEN: any realised saving (nothing governed these runs); that a deny at trip 25 would have been correct for each flagged call (some runs after 25 may be legitimate reading). "Progress" = edit, successful commit, or red->green proof, so doc/analysis-only sessions look unproductive.
- UNKNOWN: admission denials; tokens/progress is not comparable across task kinds (QA vs build) -- compare within a family only.

## Cross-domain canary (TUA-X, non-PP, read-only; no deploy, no push, no edit)
Task: count ADR headings in `ARCHITECTURE_DECISIONS.md` and list the 3 newest (`claude -p`, sonnet, tools Read/Grep/Glob only, `--max-turns 8`, in `C:\Users\User\Desktop\Cursor Projects\TUA-X`).
CDC guards on via `--settings` (PreToolUse `*` -> `semantic_breaker.js` + `cognitive_admission.js`), because the deployed dispatcher has neither (C9 Owner act pending). So this proves the hooks work when wired in a foreign repo, NOT that they are inherited.

| Run | guards | turns | tokens (in / cache-create / cache-read / out) | USD | denials | outcome |
|---|---|---|---|---|---|---|
| 1 | live-landed hooks | 7 | 14 / 67,528 / 505,085 / 1,488 (~574 k processed) | 0.34 | 4 (all false DUPLICATE) | BLOCKED, task not done |
| 2 | worktree hooks with fix | 4 | 8 / 35,770 / 289,730 / 727 (~326 k processed) | 0.18 | 0 (3 allow rows "not a spawn tool") | correct answer (3 decisions D1-D3, 0 `ADR-` headings) |

Incident (found by the canary, fixed): `cognitive_admission.js` hashed `tool_input.prompt||description` for ANY tool; with an empty prompt every Read/Grep got the same hash `e3b0c442...` and the 2nd call inside 120 s was denied as DUPLICATE ("COGNITIVE ADMISSION -- DUPLICATE"). The dispatcher routes it only on Agent|Task, so the estate never saw it; any other wiring (matcher `*`) bricks the session. Fix: non-Agent/Task tool or empty prompt -> allow (still fails open on error). Regression: `tools/test_cognitive_admission.py` C10-NONSPAWN + mutant NONSPAWN flips RED (24/24). No breaker trip occurred (4-7 calls << 25); semantic_breaker produced no deny and no incident.
Run 1 cost ~0.34 USD of which the deny loop was the whole waste: the model spent 3 extra calls re-trying a denied read and gave up (the guard protocol worked as a stop, the guard was wrong).
Limits: n=1 task, 1 repo; fast-path overhead not measured here; goal binding absent (unit `unbound`: log only), so LEASE/EFFECT/NO_WORK branches were not exercised cross-domain.
