---
status: LF1 APPROVED 2026-10-30 (Owner "go ahead, preparalo y hazlo"). Pilot first; the pilot's measured yield decides whether it widens.
covers: [recon-fabric-llm-fix, llm-fix, lf1, tennis-llm-agent]
extends: [recon-fabric-ogws-donor.md, recon-fabric-tc-search.md]
tier: T2 (a model in the loop of a certification authority, persisted evidence, projection change)
---

# LF1: a coding agent in the loop for Tennis near-misses (SportsPackEP.dol)

## Premises (measured 2026-10-29/30, GEX44 t1/campaign ae9ffbc2)
- Frontier 632/1797. The v5d-sd8 lane has 152 uncertified near-misses (compile, >= 95 %, no match).
- The TC3 operator search just went **0/152** on that cohort (128 EXHAUSTED, 24 BUDGET_EVALS). The OG3 probe showed
  the NO_COMPILE remainder fails on chains of distinct errors, not one shape. A fixed operator set and one regex at a
  time are spent; a reader of the actual diff is the untried lever (N64 agent write-up, DAITK, Mizuchi).
- GEX44 has Claude Code authenticated. The shared `/usr/local/bin/claude` is 2.1.113 and refuses current models;
  a private CLI lives at `~/.local/claude-lf1` (2.1.314), so the shared binary is untouched. Smoke: 2 turns, $0.48.
- `claude -p` reads stdin: it must run with `< /dev/null` (it swallowed a `bash -s` script otherwise).

## Design
`modules/recon_fabric/llm_fix.py` (GEX44 clone only, lane flags via `toolchain_sd.use_sd8()`).

1. **`run [--n N] [--min-pct P] [--max-turns T] [--model M] [--jobs J] [--budget-usd B]`**
   - Cohort: `toolchain_sd.search_cohort` (the same near-misses as TC3), first N by (-pct, fn).
   - Per function, a work dir under `.local/llm-fix/<run>/<fn>/` holding:
     - `fn.c`, the lane source;
     - `target.s`, the target function's disassembly with its relocations;
     - `check.py`, which runs `llm_fix check` for that dir.
   - `check` applies the source policy, compiles `cv1.compose(fn.c)` under the lane flags and judges it with
     `cv1.judge`. It prints the pct and a diff of the two disassemblies, and keeps `best.c` itself whenever the pct
     rises. The agent never writes `best.c` and never reports a score.
   - The agent: `claude -p` from the work dir, model M, `--max-turns T`, tools limited to
     `Read, Edit, Bash(python3 check.py)`, stdin `/dev/null`.
   - After the agent ends, the harness judges `best.c` again by itself.
     - States: SOLVED (100), IMPROVED, NO_GAIN, POLICY_REFUSED, AGENT_ERROR.
     - Every row records the cost (`total_cost_usd`) and the turns. The run stops dispatching once the summed cost
       reaches B.
   - Evidence: `evidence/llm-fix/<run>/{run.json, results.jsonl, solved.jsonl, src/<fn>.c}` (SOLVED sources only).
2. **Source policy** (`policy(src, fn)` -> reason or None):
   - refused: `asm` / `__asm` / `__asm__`, `#pragma`, `#include`, `#define`;
   - refused: a function body defined for any symbol other than `fn` and its own static helpers;
   - required: `fn` is defined.
   Inline asm would match by copying the target. A pragma or define could change the flags the lane records.
3. **`certify-solved <run>`**: the TC3 rule, with the source read from `src/<fn>.c`:
   - controls `m1.run_controls` before and after;
   - a fresh-cache replay through `fastmatch.measure_fn` must compile and score 100;
   - the source policy again;
   - `certify.disputed_extents`;
   - A2 negative on the renamed source, `certify.batch_ok`.
   `decide` order: INSTRUMENT, POLICY, SOURCE_CHANGED (the sha no longer equals solved.jsonl), REPLAY_NOT_100,
   EXTENT_DISPUTED. Receipts go to `evidence/cert1-llm/receipts.jsonl` with `kind: "llm"`, the model, the run,
   `src_path`, `src_sha256`, the flags, pct_replay, obj_sha256_replay, the negative and the batch.
4. **`projection.py`**: an optional `llm_cert` input after ogws. A receipt certifies (`certified_by: "llm"`) only when:
   - it is CERTIFIED;
   - its `src_path` exists and hashes to `src_sha256`;
   - its flags equal the lane flags;
   - no earlier authority holds the function.
   Otherwise it lapses into `cert_invalidated`. An unknown verdict is a hard red. With the input absent, the
   projection is byte for byte the one before LF1. `fingerprint.built_frontier` leaves `llm_cert` out.

## Acceptance (each driven red -> green)
- V-RF-LF1-POLICY: asm, pragma, include, define and a foreign function body are each refused; a plain source passes.
- V-RF-LF1-DECIDE: the order above, each refusal reachable.
- V-RF-LF1-BEST: `check` keeps `best.c` only on a strict rise; a policy-refused source never becomes best.
- V-RF-LF1-PROJECTION: certifies; a refusal, a changed source file, other flags and an earlier authority do not; an
  unknown verdict is red.
- V-RF-LF1-ABSENT: no input = no `llm` counter or input.
- Real: a pilot run (N=12, Opus, 30 turns, budget $60) and `certify-solved` on what it solves with healthy controls.
  Whatever is measured is the result, 0 included.
- Every existing suite stays green: TC1, OG1, FR1, FP1, CERT1, RR1, CP1, NEXT, SR1. `projection check` OK.

## Out of scope
NO_COMPILE functions (pilot first), names, pushing, changing the shared Claude CLI.

## Rollback
Revert the commits; with `evidence/cert1-llm/` removed the projection is the pre-LF1 one.
