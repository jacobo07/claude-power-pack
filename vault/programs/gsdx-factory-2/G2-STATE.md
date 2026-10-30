# Recon Factory Gen2: state and approved plan (continuation file)

Addendum: `ADDENDUM-recon-factory-gen2-2026-10-30.md` (this folder). The plan was approved by the Owner on 2026-10-30
("y").
- Model-spend cap for tranche G2-A: **$400**.
- Accounts: the "y" did not answer the question, so the conservative default applies. There is no automatic account
  switching; on QUOTA_EXHAUSTED the campaign waits for the reset while the non-model lanes continue.
- Push to `t1/campaign` stays Owner-gated.

## Where
- GEX44 clone `/home/kobii/missions/t1-campaign`, branch `t1/campaign`; ssh `gex44`.
- Laptop: this repo, branch `feature/knowledge-acquisition`.
- Run remote scripts as files (`cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"`) and keep them LF.

## Baseline at plan time (GEX44 98c8d79a)
- Frontier 868/1797: 360 COMPILES_NO_MATCH, 569 NO_COMPILE, 0 UNKNOWN.
- Motion 18/50: 2 COMPILES_NO_MATCH, 30 NO_COMPILE.
- LF1 spend about $497.
- Upstream tools:
  - present: objdiff-cli 3.8.1 (oracle), m2c, MWCC via wibo, dtk (wsr-decomp/build/tools), Ghidra 12.1.2, wsr-decomp;
  - absent: decomp-permuter, tree-sitter, z3.

## Phases (approved order)
| Phase | Content | Status |
|---|---|---|
| P1 | Provider health plane + circuit breaker; `llm_fix health` | **DONE** `de47cb7b` (LF1 17/17, mutations red, 11 suites green) |
| P2 | Semantic run identity + immutable manifest; `--resume RUN` reads the cohort from the manifest; options not given on resume come from the manifest | **DONE** `164f221f` |
| P13 | `llm_fix campaign --cap-usd 340`: regime cohorts, per-regime demotion, health wait, certify + projection per generation, receipts in `evidence/llm-fix/campaign/campaign.jsonl` | **DONE** `c4b55e88`; **RUNNING** on GEX44 since 2026-10-30 (pid 3746887, log `~/g2_campaign.log`). The remaining $60 of the $400 is reserved for the Motion lane |
| P3 | Durable candidate store `evidence/llm-fix/candidates/` (CAS, lineage, Pareto <= 4); seeds read from it | |
| P4 | pct trajectory per function, adaptive lease (20 turns, extend on gradient), plateau = reroute | |
| P5 | Incremental idempotent certify-solved + projection every K solves | |
| P6 | FR1 checks invariants and a monotone floor written by the projection; `llm_fix report` | |
| P7 | objdiff diff-row morphology | |
| P8 | decomp-permuter audit + thin adapter; 2 motion CNM + a sample of CNM | |
| P9-11 | Motion factorisation: clusters, layout graph of the 0xFC0 controller struct, families. No raw retry | |
| P12 | WSR / ogws donors and holdouts | |
| P15 | Compiler-inversion corpus export | |
| End | Red team, Knowledge Vault, UKDL, CBR | |

Upstream registry to create: `vault/registries/upstream-baselines.json`.

Dormant until a consumer exists: Tree-sitter, Z3/cvc5, egglog, Temporal, Ray, Bazel, OpenTelemetry.

## Stop predicates
- No healthy provider and no other route.
- Route collapse (SOLVED < 15 % or > $8 per SOLVED): switch route.
- $400 reached: one consolidated economic decision to the Owner.

## Next action
1. P6 first. FR1 pins the frontier counts and goes red as soon as the campaign certifies more functions. Replace the pin
   with invariants: counters equal a recomputation from the receipts, plus a monotone floor written by the projection.
   Add `llm_fix report`.
2. Then P5 (incremental certification), P3/P4 (candidate store, plateau), P7/P8 (diff morphology, permuter), and P9-11
   (motion factorisation, $60 lane).
3. Progress check:
   `ssh gex44 "tail -n 3 ~/missions/t1-campaign/evidence/llm-fix/campaign/campaign.jsonl"`.
4. Commit campaign evidence on GEX44 at checkpoints:
   `git add evidence/llm-fix evidence/cert1-llm evidence/frontier`, after the suites.
