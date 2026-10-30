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

## Result (2026-10-30, GEX44 t1/campaign f2decd83 code, 301a4e3c evidence; unpushed)
- Pilot `v5d-sd8-opus-5-5-n12-t30`, the top 12 near-misses (99.78-99.92 %): **7 SOLVED, 5 NO_GAIN**, $10.26 total
  ($0.66-1.28 each), 3-4 turns per solve, 13-32 s each.
- What the agent fixed: mostly an argument m2c missed (a value in r3 passed through, e.g. `fn_801CD384(arg0->unk8, ..)`),
  restored by reading the diff. These are real source fixes, and the objects match byte for byte.
- `certify-solved` batch a8d8063493640c77: controls OK/OK, A2 negative 5 pairs 0 match (2 excluded), **7/7 CERTIFIED**.
- Frontier **632 -> 639/1797** (`certified_by.llm: 7`), 0 invalidated, 0 regressed, FRONTIER_CHECK OK.
- Gates: LF1 8/8, REAL included. Mutation drills went red on the NULL-head exception (POLICY-REAL) and on the pragma rule
  (POLICY). FR1 repinned to 639; FP1/CERT1/RR1 name `llm` beside ogws. Every other suite is green.
- The missed-argument fix is a candidate deterministic operator: cheaper than the agent if it generalises.

## Widening (Owner "do all 3, including later", 2026-10-30)
1. **Near-misses:** `llm_fix run --cohort near --exclude-runs <pilot> --n 200 --budget-usd 150`. That is every remaining
   function at >= 95 %, minus those the pilot already judged.
2. **P1, the deterministic operator** (`modules/recon_fabric/m2c_proto.py`, GEX44 7b285c93).
   - Measured first: 200 uncertified functions call a Tennis callee with an arity that disagrees with the callee's own
     m2c definition (288 calls with fewer arguments, 315 with more).
   - Design: m2c is re-run with each function's own signature in the context, so m2c recovers the dropped register
     value itself; a regex cannot know that value.
   - Control: the original context reproduces ctx_run1 byte for byte on 40 functions before the run is trusted.
   - Run: 1,687 signatures; 594 sources change; clean 276 -> 293.
   - Lane generation `v5p-sd8` (`proto_source`) applies only to functions outside `keep` (the v5d matches plus the TC3
     solves, 574), so no lane or search certification can lapse. It adds the callee prototypes that `cv1.compose`'s base
     header lacks.
   - Limit: the pilot's own callees (`fn_801CD384`, `fn_80282D50`, `fn_801CDA9C`) are DOL library functions outside the
     1,797, so P1 does not reach them; the agent does.
   - Gates: V-RF-P1-* 5/5 (the keep rule mutation-drilled red). TC1 RETYPE-NO-OP had skipped silently whenever a later
     generation had no sweep; it now fails UNMEASURED instead.
3. **NO_COMPILE:** `--cohort nocompile` (uncertified, lifting, smallest first). It runs in batches; the first is 60
   functions at 40 turns with a $120 cap, and its measured yield decides the next batches.

### Widening results (GEX44 5c9d056c)
- **Near run** `v5d-sd8-near-opus-5-5-o0-n200-t30` (140 functions):
  - 74 SOLVED, 27 IMPROVED, 39 NO_GAIN, $129.98;
  - certify batch 2c29275acd6b34cf: controls OK/OK, A2 72 pairs 0 match, **74/74 CERTIFIED**.
- **P1 probe** of v5p on the 473 changed uncertified functions:
  - for: 6 match, 4 start to compile, 28 rise in pct;
  - against: 102 stop compiling, 39 fall in pct.
  - So proto is gated by `evidence/m2c-proto/apply.json` (32 functions where it measurably helps), and the lane can
    lose nothing.
- **Nocompile batch 1**:
  - 51 of 60 starts were refused by the policy itself. m2c writes `?` for an unknown type, and a m2c failure leaves no
    definition; both read as NOT_DEFINED. The fix allows those starts in the nocompile cohort only (the final source
    still passes the full policy).
  - The 9 that ran: 9 SOLVED ($6.52), 8 CERTIFIED, 1 EXTENT_DISPUTED (refused, as the rule says).
- **Frontier 639 -> 721/1797** (`llm` 89), 0 invalidated, 0 regressed. All 11 suites green.

### Nocompile batch 1, resumed (GEX44 f0dd5d52)
- Run `v5d-sd8-nocompile-opus-5-5-o0-n60-t40`, after the start fix: 68 judged, **42 SOLVED, 26 IMPROVED**, $55.27 for the
  run ($48.75 for the resume), about $0.64-1.58 per function.
- certify batch 01d7470dac91ce85: controls OK/OK, A2 42 pairs 0 match, **41 CERTIFIED**, 1 EXTENT_DISPUTED (the same
  function as the first pass).
- **Frontier 721 -> 754/1797** (`llm` 122, NO_COMPILE 713 -> 680), 0 invalidated, 0 regressed, FRONTIER_CHECK OK.
  FR1 repinned; all 11 suites green.
- Yield: 62 % SOLVED on the smallest NO_COMPILE functions, so the next batches go ahead at the same size.

### P1 lane switch (GEX44 45b1babc)
- `toolchain_sd.LANE` and `projection.TOOLCHAIN` moved to `v5p-sd8`.
- Sweep (controls OK/OK): compiles 1208 -> 1212, matches 572 -> 578.
- certify 74/74; the 2 TC3 search rows re-judged 2/2.
- **Frontier 754 -> 758/1797** (toolchain 72 -> 76). It is +4, not +6: 2 of the new lane matches were already held by
  another authority. 0 invalidated, 0 regressed. FR1 repinned; all 11 suites green.
- Nocompile batch 2: `--exclude-runs v5d-sd8-nocompile-opus-5-5-o0-n60-t40 --n 60 --max-turns 40 --budget-usd 120`. It
  uses the exclude, not `--offset 60`: certified functions leave the cohort, so an offset would skip functions never
  tried.

### Nocompile batch 2 (GEX44 45852dd8)
- Run `v5p-sd8-nocompile-opus-5-5-o0-n60-t40`: 60 judged, **42 SOLVED, 18 IMPROVED**, $56.24.
- certify batch 1b5d489b85b17c0a: controls OK/OK, A2 42 pairs 0 match, **42/42 CERTIFIED**.
- **Frontier 758 -> 800/1797** (`llm` 164, NO_COMPILE 636), 0 invalidated, 0 regressed. FR1 repinned; all 11 suites
  green.
- Yield 70 % at about $1.34 per certified function. LF1 spend to date: about $252.

### Nocompile batch 3 and two run options (GEX44 26264e89, Owner "run batch 3")
- `--tag T` is appended to the run id only when given. Without it, batch 3 would have reused batch 2's id and
  overwritten that committed run.
- `--cohort list --fns FILE` takes the named functions that lift and are uncertified, smallest first. An unknown name
  or an empty list is refused. Gate: V-RF-LF1-COHORT-LIST; dropping the certified filter turns it red (10/11).
- Run `...-o0-n60-t40-b3` (84-172 bytes): **26 SOLVED, 33 IMPROVED, 1 NO_GAIN**, $60.15.
  - certify batch dc652e224ff3fa37: controls OK/OK, **26/26 CERTIFIED**.
  - Yield fell to 43 % as function size grew, about $2.31 per certified function.
- **Frontier 800 -> 826/1797** (`llm` 190, NO_COMPILE 610), 0 invalidated, 0 regressed. 11 suites green.

### D21 motion batch (Owner "lanza ese batch en paralelo", 2026-10-30)
- Motion set: `evidence/d21-motion/motion50.txt`, from the D21 step-3 probe re-run without its 25-row cut. It has 50
  getter callers; the 20 field readers are among them.
- State at launch: 2 CERTIFIED (one is LF1's `fn_80251168`), 3 COMPILES_NO_MATCH, 45 NO_COMPILE (132-4140 bytes).
- Run `v5p-sd8-list-opus-5-5-o0-n48-t60-motion`: the 48 uncertified functions, 60 turns, 1 h per agent, $80 cap.
- Result (GEX44 f5259ce6): **12 SOLVED, 20 IMPROVED, 16 NO_GAIN**, $59.06.
  - certify batch c642689e3c90d768: controls OK/OK, **12/12 CERTIFIED**. `fn_802099C4` was already held from batch 3.
  - **Motion set 2 -> 14/50 CERTIFIED** (2 COMPILES_NO_MATCH, 34 NO_COMPILE).
- **Frontier 826 -> 837/1797** (`llm` 201), 0 invalidated, 0 regressed. 11 suites green.
- LF1 spend to date: about $371.

### Correction: the account limit read as NO_GAIN (GEX44 34aba349)
- The GEX44 Claude account hit its 5-hour limit. `claude -p` then returned `is_error` at $0, and `final_state` recorded
  those functions as NO_GAIN or POLICY_REFUSED. A resume therefore skipped them as already judged.
- In the motion run, **10 of the 16 NO_GAIN never ran**. Only 6 are real NO_GAIN. The committed f5259ce6 results
  overstate NO_GAIN; nothing that was certified is affected.
- The motion retry (`--seed-run`, the 20 IMPROVED, t80, $80 cap) and nocompile batch 4 (`--tag b4`, 60, $120 cap) were
  launched on Owner "lanza ambas". Both ran entirely against the limit: 80 starts at $0. They are not committed.
- Fix:
  - `final_state(never_ran=...)` returns AGENT_ERROR for a zero-cost agent error, unless the start already matched.
  - `needs_retry()` re-dispatches AGENT_ERROR and also the rows written before this fix.
  - Gates: V-RF-LF1-NEVER-RAN and V-RF-LF1-SEED. Each mutation drill turns LF1 red. LF1 13/13; all 11 suites green.
- Next, after the limit resets (15:10 Europe/Berlin): re-issue the same three commands. That means the motion run for its
  10 never-ran functions, the motion retry, and batch 4. Their run dirs exist, so `needs_retry` resumes exactly the
  unrun rows.

### After the account switch (GEX44 98c8d79a)
- New GEX44 account; a 1-turn smoke returned OK for $0.46. The three runs resumed only their never-ran rows.
- Motion run, its 10 never-ran functions: 0 SOLVED, all 10 IMPROVED. The cap went from $80 to $100 because it counts the
  $59.06 already spent. The run now stands at 30 IMPROVED, 6 NO_GAIN, $79.19.
- Motion retry r2 (seeded from best.c, 80 turns): **4 SOLVED**, 4 IMPROVED, 12 NO_GAIN, $33.45. Certified **4/4**.
- Nocompile batch 4: **27 SOLVED**, 29 IMPROVED, 3 NO_GAIN, 1 POLICY_REFUSED, $68.86. Certified **27/27**.
- **Frontier 837 -> 868/1797** (`llm` 232, NO_COMPILE 569). **Motion set 14 -> 18/50.** 0 invalidated, 0 regressed.
  11 suites green.
- What the yields say:
  - Nocompile holds at about 45 %.
  - On motion, a seed at 99 %+ still mostly ends NO_GAIN: 12 of 20.
- LF1 spend to date: about $497.

## Out of scope
Names, pushing, changing the shared Claude CLI.

## Rollback
Revert the commits; with `evidence/cert1-llm/` removed the projection is the pre-LF1 one.
