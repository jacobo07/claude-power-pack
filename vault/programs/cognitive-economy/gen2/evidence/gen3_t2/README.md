# Gen3 T2-0 readout (2026-10-05, worker marker T2ZERO-WORKER-7Q4)

Unit: processed tokens (input + cache_creation + cache_read + output, dedup by message id). Zero-model: every script reads transcripts, no model call, no subagent.
Workloads and windows are the T1/K4 ones (gen3_t1/g3_k4_factorial.py lines 8-11, 110-114). **No saving is claimed as realized; everything below is a measurement or a CEILING.**
Files: `t2_extract.py` (extractor), `t2_instruments.py` (A+B+F, E, C, D, G, H, I), `t2_c_sensitivity.py` (floor-choice sensitivity), `out_*.json`, `manifest.json` (sha256 of scripts and outputs, controls), `t2_summary.txt`, `t2_unclassified_sample_60.json`, `d3_*.txt`, `PROGRESS.md`. The extractor cache is in a scratchpad (not committed; its sha256 is in the manifest).

## Controls (all machine-checked, in `out_*.json` -> `controls`; `manifest.json` -> `controls_all_pass`)
| instr | positive | negative / shuffled | mutant that changed the verdict | pass |
|---|---|---|---|---|
| extractor | KSR ctx 273,912,110 EXACT; InfinityOps 373,740,097 EXACT; KME 107,407,089 EXACT (all three equal K4) | - | - | yes |
| A+B+F | synthetic 11-call session reproduces all 11 expected labels | all-read session has 0 DELTA/REPAIR; shares sum to 100.000% of calls and of processed; tool/result sets shuffled within sessions (30 reps): ATCR real 2.36/2.44/1.75 vs null 2.22/2.26/1.60 (z 4.5/5.3/4.4) | no Bash-write rule: SDD 24.9->19.2%, 26.4->21.8%, 37.7->26.7%; DELTA>REPAIR precedence: REPAIR goes to 0 | yes |
| E | 1000-char result x 10 later calls = 4,470 tokens exact | result on the last call = 0 | removing the compaction stop changes a synthetic case | yes |
| C | k4 formula reproduced: KSR N=20,S=10k = 171,951,765 vs k4 171.95M; N=inf = base | huge S clamps to base | dropping the rehydration charge moves the argmin (N=10 -> N=1) in all 3 workloads | yes |
| D | output copied from an input = 100% overlap | disjoint output = 0%; mismatched run pairing KSR 2.2% (real 2.0%), InfinityOps 23.3% (real 2.2%) | 1-gram instead of 8-gram flips the copy-heavy class (2% -> 64-76%) | yes |
| G/H/I | synthetic 3-of-4 recurring = 75% | all-distinct = 0%; shuffled order + permuted path classes null (200 reps) | path-class-only fingerprint moves recurrence/floor | yes |

## A + B + F: one label per call (REPAIR > DELTA > CONTROL_LOOP > OTHER), % of calls / % of processed
| workload | calls | DELTA | REPAIR | CONTROL_LOOP (strict) | OTHER (strict) | OTHER if CONTROL_LOOP boundary relaxed |
|---|---|---|---|---|---|---|
| KSR | 1,141 | 24.9 / 28.9 | 4.5 / 5.1 | 43.3 / 45.3 | 27.3 / 20.7 | 7.9 calls |
| InfinityOps | 1,531 | 26.4 / 30.8 | 2.9 / 3.5 | 36.5 / 36.3 | 34.2 / 29.4 | 13.3 calls |
| KME | 393 | 37.7 / 39.9 | 3.8 / 4.4 | 43.3 / 44.5 | 15.3 / 11.2 | 6.1 calls |

| workload | Semantic Decision Density (DELTA/calls) | Action Trace Compression Ratio = calls/(DELTA + CONTROL_LOOP runs) | CONTROL_LOOP runs | repair amplification (REPAIR ctx / DELTA ctx) |
|---|---|---|---|---|
| KSR | 0.249 | 2.36 | 200 | 0.176 |
| InfinityOps | 0.264 | 2.44 | 223 | 0.112 |
| KME | 0.377 | 1.75 | 76 | 0.110 |

Read: roughly a quarter to a third of calls make a durable change; 36-45% of processed tokens are read/status/test calls between changes; REPAIR is 3.5-5% of processed.
Shuffled-order null still labels REPAIR 3.9/2.8/2.0% of processed (same-file re-edit after any failure within 10 calls happens by chance), so REPAIR net of null is only about 1.2/0.6/2.4 pp.
**OTHER is above the 5% bar in all three workloads (strict).** Most of it is read-only calls before the first or after the last DELTA (KSR: 258 of 312 OTHER calls are non-dispatch tool calls, 24 dispatches, 24 no-tool, 6 task-management), which the "between two DELTA calls" definition excludes. A stratified 60-call sample (20 per workload; main/subagent x OTHER subtype) for human judgment is in `t2_unclassified_sample_60.json`; no model judged it.

## E JOIN TAX (overlay, not a share)
| workload | subagent results | result tokens (0.447 tok/char, T1 regression) | later parent calls carrying them (mean) | join tax tokens | % of base |
|---|---|---|---|---|---|
| KSR | 17 | 8,313 | 38.8 | 322,752 | 0.12% (0.08% at 0.32 tok/char) |
| InfinityOps | 23 | 11,134 | 33.0 | 367,917 | 0.10% |
| KME | 3 | 1,539 | 45.3 | 69,789 | 0.06% |
Subagent results are tiny (final messages only). Carry stops at a context drop >30% (compaction); disabling that changes nothing measurable here. The larger "join" cost, the parent re-reading the files a subagent wrote, is not in this overlay.

## C WORKER LIFETIME (restart every N calls with handoff S; ceiling, assumes zero information loss and zero rework)
Floor sample: median first-call ctx of all transcripts, KSR 93,364 (n=24: 7 main, 17 subagent), InfinityOps 92,468 (n=31), KME 103,978 (n=6). Rehydration charge (S + floor) added at every restart. Delta vs measured base, with rehydration:
| workload | argmin | N=10,S=10k | N=20,S=10k | N=40,S=60k | k4(d) best (no rehydration, per-transcript f0) |
|---|---|---|---|---|---|
| KSR | N=10,S=5k -48.5% | -46.6% | -42.3% | -21.9% | N=10,S=10k -43.2% |
| InfinityOps | N=10,S=5k -49.7% | -47.8% | -42.7% | -21.6% | N=10,S=10k -43.7% |
| KME | N=10,S=5k -52.6% | -50.8% | -48.4% | -28.9% | N=10,S=10k -43.7% |
Without the rehydration charge the argmin collapses to N=1 (-59..-60%), so the charge is what makes N finite. N=1 with S=60k is +18..+24% (worse than base).
**The pooled median floor is optimistic**: it mixes ~92k subagent first calls into main sessions whose first call is ~123-137k. `out_C_sensitivity.json`: with each transcript's own first-call ctx as floor plus rehydration, N=20,S=10k = -35.3/-35.0/-37.8% and argmin N=10,S=5k = -40.5/-41.1/-40.5%; with the main-session median floor, N=20,S=10k = -33.8/-32.4/-38.0%. The defensible ceiling is therefore -33..-41%, about 2-5 pp below T1's (d) at the same grid points (rehydration costs ~2 pp). Argmin stays at N=10 (T1: N=10).

## D PACKET COMPILE KILL-TEST (planner / researcher / checker runs, K4 META set)
| workload | runs | 8-gram overlap of output with own paid inputs (pooled) | planner / researcher / checker | c lower bound (mean/run) | break-even (mean processed/run) | verdict |
|---|---|---|---|---|---|---|
| KSR | 12 | 2.0% | 4.8% / 2.5% / ~0% | 67,207 | 4,142,531 | SURVIVE (lower bound only) |
| InfinityOps | 10 | 2.2% | 2.3% / 2.1% / ~0% | 120,842 | 8,458,600 | SURVIVE (lower bound only) |
| KME | 0 | n/a | n/a | n/a | n/a | no meta runs |
c lower bound = unique input tokens read once + novel output tokens. It can kill, it cannot prove survival: it ignores the per-call context rent a compile run itself pays. The informative number is the overlap: ~98% of meta-run output is not copyable from what the run was given, so a compile cannot be a deterministic copy step; it is another generation. The break-even equals about 34 (KSR) / 66 (InfinityOps) floor-sized calls (`out_C_sensitivity.json` meta_runs); the meta runs themselves average 22 / 36 calls at 188k / 236k ctx per call. A compile survives only if it uses fewer calls than that at floor-size context. Caveat: the mismatched-pairing control is 23% on InfinityOps (its runs share inputs), so 8-gram overlap is a weak instrument there; the direction (low overlap) is not in doubt.

## G STRUCTURAL RECURRENCE (episode = calls since the previous DELTA/REPAIR up to a DELTA; family = collapsed last-4 tool names + path class + test command)
| workload | episodes | families | recurring families | episodes in recurring families | null (shuffled order + permuted path class) | above null | DELTA context in recurring families (null) |
|---|---|---|---|---|---|---|---|
| KSR | 284 | 106 | 40 | 76.8% | 56.8 +- 2.0% | +19.9 pp (z 10.1) | 78.1% (58.7%) |
| InfinityOps | 404 | 142 | 48 | 76.7% | 62.4 +- 1.6% | +14.4 pp (z 9.0) | 77.4% (63.7%) |
| KME | 148 | 60 | 23 | 75.0% | 62.3 +- 2.9% | +12.7 pp (z 4.3) | 75.3% (62.3%) |
The null is high because the fingerprint is coarse (e.g. Read,Edit on a .md doc); the real signal is the 13-20 pp above it. A tool-set variant gives 85.2/85.6/79.7% (sensitivity).

## H IRREDUCIBLE LOWER BOUND (DELTA not in a recurring family, REPAIR excluded; share of the workload's processed tokens)
KSR 6.3% (21.9% of DELTA; ~66 calls) | InfinityOps 7.0% (22.6% of DELTA; ~94 calls) | KME 9.8% (24.7% of DELTA; ~37 calls). Approximate floor of genuinely new cognition under this fingerprint; not judged for quality. A path-only fingerprint (mutant) would put it near 0%, so it is fingerprint-dependent.

## I BOUNDARY-MISS PROFILE (% of processed / % of calls)
| class | KSR | InfinityOps | KME |
|---|---|---|---|
| control-loop miss (CONTROL_LOOP) | 45.3 / 43.3 | 36.3 / 36.5 | 44.5 / 43.3 |
| repair / proof miss (REPAIR) | 5.1 / 4.5 | 3.5 / 2.9 | 4.4 / 3.8 |
| transformation miss (recurring DELTA) | 22.6 / 19.1 | 23.9 / 20.2 | 30.0 / 28.2 |
| novelty (non-recurring DELTA) | 6.3 / 5.8 | 7.0 / 6.1 | 9.8 / 9.4 |
| unknown (OTHER, strict) | 20.7 / 27.3 | 29.4 / 34.2 | 11.2 / 15.3 |
With the CONTROL_LOOP boundary relaxed, unknown falls to 7.9 / 13.3 / 6.1% of calls and control-loop rises to 62.8 / 57.4 / 52.4% of calls.

## D3 scope conservation
`tools/cep_gen2.py` gained `check_obligations` (absent/false/null -> UNASSESSED; declared -> each obligation needs id, source, valid terminal and an execution mapping or evidence; EXECUTE needs `execution`, SATISFIED needs `evidence`; empty declared list fails). `tools/test_cep_gen2_obligations.py`: OBL_TEST=PASS (17 cases, 5 mutants killed incl. vacuous pass and missing terminal accepted, 3 integration cases, live ledger UNASSESSED). Before/after (`d3_before.txt`, `d3_after.txt`): selftest and status identical; the two modes that run the final check gain one `CEP2_OBLIGATIONS=UNASSESSED` line. Note: argv `--selftest` is not `selftest` in `main()`, so it runs the final check (pre-existing). Live ledger: `obligations_declared=false`, `obligations=[]`.

## CEILING vs measured
Measured: label shares, SDD/ATCR/amplification, join tax, floor medians and their spread, overlap shares, recurrence and its null, spend. CEILING / counterfactual: C grid, D lower bound and break-even framing, H floor, I class mapping (heuristic). Heuristic-dependent: Bash-write DELTA rule (removing it moves SDD 5-11 pp), REPAIR rule (null 2-4%), commit subjects passed by `-F` file are unknown (REPAIR via subject under-detected), 0.447 tok/char taken from T1.

## What this changes
- Revised ceiling: T1's combined -34..-56% rested on (d) at -23..-43%. Rehydration plus a defensible floor puts (d) at about -33..-41% at the best settings (N=10, S=5-10k), 2-5 pp lower at T1's grid points. (e) was not recomputed end to end, so treat the combined range as T1's minus a few points, not a new number.
- Dominant lever: worker lifetime / bounded handoff (d). Next is meta-work removal (c), which is only positive when compile c stays well under the 4.1M (KSR) / 8.5M (InfinityOps) break-even and D says it cannot be a copy step. Floor (a) <=3.7% and hooks (b) 1.6-2.2% are small. Join tax (E) is 0.06-0.12%: not a lever.
- Where the tokens go: 36-45% of processed tokens are control-loop calls and 23-30% are recurring (transformation) changes; genuinely new cognition is 6-10%, REPAIR 3.5-5%. That supports bounding context growth during read/status loops over reducing any single content source.
- InfinityOps Phase 4 as canary: not contradicted, weakly supported. It carries the largest meta-work exposure (10 meta runs, 84.6M, break-even 8.5M/run) and the same control-loop and recurrence profile as KSR; KME has no meta runs so it cannot canary lever (c). Nothing here discriminates KSR from InfinityOps on canary quality beyond that.
- Do NOT build: subagent-result / join-tax mitigation (0.1%); a deterministic copy-based packet compiler (2% overlap, nothing to copy); more hook-text compaction (b <=2.2%); hook_success silencing (T1: ~0 rent); N=1 restarts or S>=60k handoffs (worse than base); a recurrence-template library from this coarse fingerprint without human review of the sample.
- Needs human judgment before any build: the 60-call OTHER sample.

Spend: see PROGRESS.md (meter.py, own transcript agent-a40e09b85220b467d.jsonl).
