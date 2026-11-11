# RESUMPTION — Recon research dataset (GSD X Reconstruction Factory gaps)

**Identity.** Doc (claude.ai): https://claude.ai/artifact/5gRQmN7Dmm9X2S6V8DWm1x (doc id 25e59ace-0ab8-4e92-9382-d7274d1c9b8f) — 27 gaps G01-G27, one deep-research prompt each, dataset schema.

**State 2026-11-11.**
- G01-G06 answered by ChatGPT (Owner pasted), raw in `raw/gap-G0N.jsonl`; `python -I ingest.py` -> `recon-research.jsonl` 105 rows (E1 22 / E2 17 / E3 66 / E4 0), 14 G01 ids reassigned. Their scale was inverted; ingest.py maps it.
- Prompts G07-G27 in `prompts/` (scale fixed). `run_codex.py` = sequential Codex runner (`gpt-6-astra`, effort high, `--search`); Owner config default `gpt-5.5` is rejected for ChatGPT accounts (400 model_not_found) — never edit ~/.codex/config.toml, override per call.
- G07 pilot DONE and judged: 30 rows parse, 58 web-search events, scale respected (24 E3 / 6 E1), 18/20 unique URLs answer HTTP 200 (2 nxp.jp PDFs 404 on HEAD: G07 rows citing PPCEABI.pdf / MPC750UM.pdf = unconfirmed link). It refuted a premise of my prompt (`m2c --struct` does not exist upstream; real flags --context, --stack-structs, --dump-typemap). Landed in raw/gap-G07.jsonl; recon-research.jsonl now 135 rows. Verdict: Codex route works, quality >= ChatGPT answers.

**Owner question open:** is deep research worth it? My answer: narrow it to G07/G08, G03/G05, G15/G17; G18-G27 later. Batch G08-G27 NOT launched — needs Owner go.

**NEXT.** (1) judge G07 pilot; (2) Owner go/no-go on the batch; (3) cheap experiment: do KSR FLAGS_SPLIT fns access symbols with incomplete `extern T x[]` (G03-013/G05-003)?; (4) check whether certify.py compares relocation targets (objdiff#393).

**Done 2026-11-11 (session e31c61e1).** (4) ANSWERED: certify.py does NOT compare relocation targets. CERTIFIED = objdiff `match_percent == 100.0` (t1 7a560498 cv1.py:222-237) + replay obj_sha == sweep obj_sha (self vs self, not vs target) + A2 negative control. Pinned objdiff-cli 3.8.1 (sha c8290281e821) has the #381 address fallback (`symbol_name_addend_matches || address_eq`): a reloc to a DIFFERENT symbol at the same address (e.g. both at 0 in their own object) still scores 100. Issue #393 OPEN, no fix in 3.8.1..3.8.3 (inferred from release notes). G05-011 moves HYPOTHESIS -> source-confirmed, still unreproduced on KSR. Risk lands on S26C's certs (pane ddf4990e). (5) DONE: stray research/vault lesson appended to PP session_lessons.md, untracked dir removed. (1) moot: the Owner already chose S26C ("a" 15:44Z).

**S26E (Owner approved both, 2026-11-11).** Plan `../S26E-PLAN.md`. E0 DONE (t1 2ae98cc5): reloc_oracle, 9,269/9,269 CONSISTENT; G05-011 (#393) is now REPRODUCED and wider (4 blind classes, in-object data by address only). Arming S26E after S26D = coordinator ddf4990e (handoff PP 1d4b0e42). Next for this pane: E2 research bridge needs S26E armed; run_codex narrow set still needs Owner go.

**Codex G08 G09 G10 G13 G15 G17 DONE (Owner "y").** 149 rows -> recon-research.jsonl 284. Write-back live: `verdicts.jsonl` + `urlcheck_*.json` merged by ingest.py (G05-011, G13-002 CONFIRMED E4). G13-002 = objdiff `functionRelocDiffs=data_value` closes the blind spot, 9,269/9,269 still 100 (t1 767709a9). Next: run the E3 `test` of the top rows of G09/G10/G15/G17 as KSR experiments once S26E is armed; G19 not approved yet.

**DRX run of the six high-leverage questions (Owner "hazlas todas con Deep Research X", 2026-11-11 19:00-19:48Z).** `run_drx.py`, outputs `drx-out/Q1..Q6`. Sonnet 5.5, USD 0. Q2-Q6 rc=0 but every report states the research did not reach primary sources (no dtk/m2c/objdiff/mwcc repo files; Q2 leaned on the GCC manual + DMCA news). Q1 failed twice before any search (LLM timeout 120 s; then invalid JSON from query generation, DRX had moved to 0.4.1 mid-run) -- not retried a third time (Regla 12). Useful residue: 1 boundary heuristic (Q6: duplicate float constants mark a TU boundary, DERIVED MEDIUM). Yield signal for E3: for this domain Codex --search (reads raw GitHub source; G13 -> E4 judge fix) >> DRX (DuckDuckGo + fetch). DRX-side defects to hand to its pane: no GitHub/source-code reach; query-generation JSON parse failure on long technical prompts.

**Bigger levers (Owner decisions, from S25):** certify the 582 BINARY_EXACT on stage ksrmb-s25; FLAGS_SPLIT per-fn arm rule; `?` repair fallback policy.
