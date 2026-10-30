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
| P1b | **Incident**: the agent's Bash is unrestricted on GEX44 (user settings allow Bash, mode auto; `--allowedTools` only adds). The agent ran `cp fn.c best.c` and `rm -f best.c`, which understated 12 rows (4 at 100 %). Fix: the harness keeps its own sha copy outside the agent's cwd; `judge_work` measures every candidate; `llm_fix rejudge RUN`. Backfill gave +4 certified at $0 (868 -> 872) and motion 18 -> 20 | **DONE** `06c3862b`. **Open, P1b-2**: a real agent sandbox (own CLAUDE_CONFIG_DIR, deny by default, allow only Read/Edit/`Bash(python3 check.py)`), proven with one real agent call. **Pending**: the running campaign loaded the pre-fix code, so restart it after its generation 1 and run `rejudge` on its `-g00N-` runs |
| P1b-2 | Real agent sandbox in `agent_cmd()`: `--restricted --tools Read,Edit,Bash --permission-mode dontAsk --settings {allow Read, Edit, Bash(python3 check.py)}`. Proven with a real call: `rm` and `cat` denied, check.py and Edit allowed | **DONE** `42b68680` (LF1 21/21) |
| P1c | **Incident 2026-10-30, gen 2**: `provider_state` read every paid error as HEALTHY, so 6 sessions the 5-hour limit cut after 8-15 turns (~$0.6 each, `terminal_reason` api_error, 429) became IMPROVED/NO_GAIN verdicts that no resume retried. Fix: a paid error with an API-error marker is classified from its text. The 6 g002 rows were backfilled to AGENT_ERROR (pre-backfill copy in `~/g2_aborted/`) | **DONE** `edef2b18` (LF1 22/22; the new gate goes red against the old classifier) |
| P9a | Motion factorisation census `evidence/d21-motion/factor-v1.json`. Of the 32 uncertified, 22 already have a compiling candidate >= 95 %: a compiler-form tail, whose resolver is exact search (P8), not more LLM turns. 8 sit at 80-95 %, 2 have no useful candidate | DONE (in `06c3862b`) |
| P2 | Semantic run identity + immutable manifest; `--resume RUN` reads the cohort from the manifest; options not given on resume come from the manifest | **DONE** `164f221f` |
| P13 | `llm_fix campaign --cap-usd 340`: regime cohorts, per-regime demotion, health wait, certify + projection per generation, receipts in `evidence/llm-fix/campaign/campaign.jsonl` | **DONE** `c4b55e88`. Gen 1 (pre-fix code): 16/16 certified, 888, $99.93, evidence `12c48427`; rejudge +2 IMPROVED, 0 solves. Relaunched on `edef2b18` at 17:12 CET 2026-10-30 (pid 480425, log `~/g2_campaign_r3.log`). It resumes gen-2 run `-g002-5d238973a7` and sits in its health wait until the 18:40 Berlin quota reset. The remaining $60 of the $400 is reserved for the Motion lane |
| P3 | Durable candidate store `evidence/llm-fix/candidates/` (CAS, lineage, Pareto <= 4); seeds read from it | |
| P4 | pct trajectory per function, adaptive lease (20 turns, extend on gradient), plateau = reroute | |
| P5 | Incremental idempotent certify-solved + projection every K solves | |
| P6 | FR1 checks invariants and a monotone floor written by the projection | **DONE** `ad795cf9` (FR1 17/17; mutations red). `llm_fix report` is still open: the campaign receipts in `campaign.jsonl` already give machine-derived metrics |
| P7 | objdiff diff-row morphology | |
| P8 | decomp-permuter audit + thin adapter; 2 motion CNM + a sample of CNM | Audit 2026-10-30: MIT (c) 2019 Simon Lindholm; pin `8556c81d` (main HEAD); README lists PowerPC; scores from objdump diffs (ours: powerpc-linux-gnu-objdump). Clone `~/tools/decomp-permuter` @8556c81d, venv `~/tools/permuter-venv`. **Adapter DONE** `a6348139` + `e07e86ea`: `modules/recon_fabric/permute.py` (+ `permute_cut.py`, run under the venv). Setup: base.c = compose(candidate); compile.sh is the oracle's own; objdump `--disassemble=<fn>` (the scorer objdumps whole objects, and our targets are split). Each output is cut back by AST, `inline static` is normalised to `static inline`, then llm_fix.policy, then cv1.judge. The proxy is never a verdict. A proxy-0 base under an oracle < 100 is PROXY_BLIND; an unscored base is PERMUTER_FAILED. PM1 5/5, 4 mutations red. Spike fn_80204070: proxy 60 -> 50 = oracle 99.549 -> 99.577. **RUNNING** `pm-20261030-173608-8556c81` (20 fns, 300 s, -j4, log `~/g2_permute.log`). Open: certify-solved reads only `evidence/llm-fix/<run>`, so a permuter SOLVED row needs a path into it |
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

## Gen3: Resolution Atoms + Compilation Fabric (APPROVED by the Owner "y", 2026-10-30)
Addenda: Owner Gen3 atomic addendum + G3-COMP compilation-fabric addendum (2026-10-30, pasted in session 57e9a24a).
The bulk campaign keeps running throughout (pid 480425, cap $340). Gen3 model work lives in the $60 Motion reserve; there is
no new capital, and anything past $400 goes to the Owner. Owner gates are only capital, push, or a red Production Reality Gate.

State at approval (GEX44 `f7cf0967`):
- Tennis 906/1797 (gen 2: 18 SOLVED, $78.88, $4.38/SOLVED). Motion 20/50.
- Permuter cohort 20: 10 IMPROVED / 9 NO_GAIN / 1 PROXY_BLIND / 0 SOLVED.
- Roofline sample: compile 0.01-0.02 s, objdiff 0.02-0.48 s. The path is DIFF- and orchestration-bound, not compile-bound.
- The fm1 cache (`STAGE/fm1-cache`) already keys source + ctx + flags + mw sha + target bytes. Missing from the key: wibo sha,
  objdiff version, normalization version.
- Second dangling artifact: g001 `fn_80240A1C` has no best.c.

Owners to EXTEND, never duplicate:
- atoms.py + science.py (WROS claims, edges, stale/invalidate)
- fingerprint.py, roots.py, d12d/d12_struct/ksr_atlas, search/search_c/search_ops, permute.py, fastmatch (cache, measure)
- toolchain_sd (twin variants), certify, projection, disposition, homology/ogws_donor

Steps (micro-commits on GEX44 t1/campaign), status column to update:
| # | Step | Status |
|---|---|---|
| 1 | G3-1 NO_COMPILE diagnostics as structured evidence + root-cause graph | |
| 2 | G3-2 shared blockers + fan-out (extend roots.py) | |
| 3 | G3-3 fingerprint rebuild + causal diff + distance vector (C6) | |
| 4 | G3-C0 roofline spans P50/90/99 + upstream registry `vault/registries/upstream-baselines.json` | |
| 5 | G3-C1 Build Twin: replay 906 certified, falsify alternatives (sd0, -O/-inline/-fp_contract), ogws per-TU flags, toolchain evidence profile + twin atoms | |
| 6 | G3-C2/C3/C12 action id (+wibo, objdiff, norm versions), CAS for diff results, receipts + snapshot, no-dangling-artifact gate (PR2, PR3, PR8) | |
| 7 | G3-C5 oracle capability matrix (PROXY_BLIND regression) | |
| 8 | G3-C7/C9 differential microscope + operator mining from 272 SOLVED lineages -> transformation registry | |
| 9 | G3-C4 farm slice: durable queue, backpressure, stale cancel, no model (PR4) | |
| 10 | G3-C8 tomography on top-fan-out compiler atom (PR5, PR6) | |
| 11 | G3-C10/C11 search plans, Pareto set, dead-compile/plateau, first Genome rule, one supercompiled trajectory | |
| 12 | G3-4 atoms ingestion (incl compiler/twin atoms) | |
| 13 | G3-5 compile-to-fixed-point before any model call | |
| 14 | G3-6 Motion targeted canary (PR7); never a bigger blind permuter run | |
| 15 | G3-7 Semantic Interrupt + bulk A/B Gen2 vs Gen3 | |
| 16 | G3-8 atomic progress receipts + proof CSE (PR9) | |
| 17 | G3-9 cross-title canary on ogws (PR10) | |
| 18 | G3-10 KV/UKDL/CBR (seeds: quota-cut verdict, PROXY_BLIND as NO_GAIN, best.json dangling x2, run-id collision, blind permuter 0 solved) | |

Dormant: compiler genealogy, experiment set cover, unasked synthetic labs, MVCC (until step 13), full Genome ABI (until step 17),
Ray/Temporal/OTel deps, Z3/cvc5/egglog/angr/Tree-sitter.
Budget: model $0/$45/$60 (low/central/high); deterministic about 70k compiles; CAPEX about 10M session tokens; mission authority
160M + 3x40M.
Every step: a gate with mutation drills (red first), the suites, a commit, then update this table. The iteration file runs at the
checkpoints named in the addendum.

Ops:
- Progress: `ssh gex44 "tail -n 3 ~/missions/t1-campaign/evidence/llm-fix/campaign/campaign.jsonl"`.
- Commit campaign evidence at checkpoints: `git add evidence/llm-fix evidence/cert1-llm evidence/frontier` after the suites;
  KSR-REAL is red while `evidence/frontier` is uncommitted.
- Known red at clean HEAD (not G2/G3): D12D 20/22, IR0A 1/18, f1-f7 ImportError.
