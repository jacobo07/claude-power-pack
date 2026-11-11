# DRX — Deep Research X — RESUMPTION FILE

## 1. Mission and approved scope
Owner approved 2026-11-11 ("y"): extend `modules/deep-research` (no new runtime, no DeerFlow/LangGraph);
ratchet = register in existing `baseline_inheritance` + `mutation_ratchet`, no new system. Slice U0-U7:
U0 baseline · U1 ledger · U2 wiring · U3 checkpoint/resume · U4 ratchet registration · U5 12-case eval set
(4 held out) · U6 real-run comparison · U7 UKDL/vault + meta-analysis + handoff.

## 2. State (git-verified on feature/knowledge-acquisition)
- `1c68ddd8` U1 evidence_ledger.py + source_guard.py + tools/test_deep_research_x.py
- `0c88da6f` v0.3.1 fix: claude.exe child loaded all hooks+MCP (61.5 s per call -> 120 s timeout);
  now `--setting-sources local --strict-mcp-config`, cwd outside repo (5.0-5.8 s). Empty run exits 3.
- `e4cf7bfb` U2 ledger wired into deep_research (quotes, untrusted fence, SSRF on every hop,
  `<ts>_<slug>.ledger.json` + deterministic "Evidence ledger" section). DRX_PASS=23/23, mutants 3/3.
- Survey (subagent, WebFetch-paraphrased; re-read before relying): `vault/programs/drx/SOTA_SURVEY.md`.

## 2b. Later commits
- `3f65e070` v0.4.0 bump · `0de91ea6` U3 checkpoint/resume (--resume RUN_ID) · `9ba43e49` U4 mutation_ratchet
  pairs (evidence_ledger 3/6, source_guard 4/6) + U5 `vault/research/drx_eval/EVAL_SET.json` (4 HELD_OUT,
  never run while the engine changes) · `3e10caac` U7 part 1 `vault/knowledge_base/ukdl-deep-research-x.md`.
- DRX_PASS=30/30; hand drill 5/5 mutants (scratchpad `drx_mutants.py`).

## 3. Evidence so far
- Baseline v0.3.0 (`vault/research/drx_eval/baseline_v030/`): 3/3 missions INVALID — 0 queries,
  0 learnings, exit 0 "OK". Measures the launcher defect, not quality.
- v0.3.1 run #1 under `python -I` discarded (`baseline_v031_INVALID_isolated_python`: parsers missing).
- Comparison running (background, sequential, scratchpad `run_drx_missions.ps1`, 12 queries, depth 2,
  breadth 3): `baseline_v031/` then `v040/`, engines snapshotted in scratchpad `drx_v031`, `drx_v040`.
  v031 mission1: 15 learnings, 20 URLs, number-support 10/11 (0.909), 6 queries, 1518 s.

## 4. Next action
When both dirs have `ALL_DONE` in summary.txt: `python tools/drx_compare.py vault/research/drx_eval/baseline_v031
vault/research/drx_eval/v040 --json vault/research/drx_eval/COMPARISON.json`; run `evidence_ledger.py audit` on
each v040 ledger; read one v040 report's Evidence ledger section by eye. Report wins AND losses (the
number-support metric is already ~0.9 on v031, so the ledger's value must show in verified-quote rate).
Then U7 part 2: close-out review + handoff. If the runs died: `--resume RUN_ID` works only for v040+.

## 5. Open debt / traps found
- Mission prompt's UKDL path `knowledge-vault/UKDL/universal-knowledge.md` does not exist (real:
  `vault/knowledge_base/ukdl-universal.md`).
- EPISTEMIC_RANK ranks OBSERVED > VERIFIED: never min() over it (caught by V-DRX-COPIES-ARE-ONE-LINEAGE).
- Lineage mutant is killed only by the unit gate, not by an E2E gate (single coverage).
