# Evidence: CCR v4 Stage 3, WU-A6 (real admission intervention)

Branch mission/ccr-s3. Code: `tools/gsd_mission.py` (A6 wiring), `tools/test_gsd_mission_ccr_a6.py` (gates).
Scripts and outputs: `vault/programs/ccr/stage3/a6/`.

Number labels:
- Section 3 (DEFLATE) uses **laptop projections** (content-free `pack/sessions/*.jsonl`).
- Sections 4 and 5 are **Linux plane GEX44, host 2.1.296**.

## 1. Where enforcement acts (A3 confidence)
Rule implemented: a CCR contract or a DEFLATE acts only at confidence MEDIUM or HIGH. LOW observes.
- Enforcement: `_ccr_enforceable`.
- DEFLATE: `deflate_unit`.
- A W1 single-class file carries no confidence, and it keeps the W1 behaviour.

The packet expected "observe everywhere", because A3 met the gate for no class. That is only partly right. The A3 gate (HIGH) is met nowhere, but MEDIUM is not LOW:

| class (A3 held-out) | n held-out | P50 APE | P80 coverage | A3 confidence | A6 action |
|---|---:|---:|---:|---|---|
| bounded-code | 24 | 46.4 % | 70.8 % | MEDIUM (fails the gate on APE only) | **acts**: enforce refuses SPLIT/DEFLATE when `CPP_CCR_ADMISSION=enforce`; DEFLATE declares `bounded-code-worker` |
| long-textual | 7 | 21.7 % | 85.7 % | LOW (n 7 < 8) | observe (`would_deflate`) |
| lookup | 3 | 73.1 % | 33.3 % | LOW | observe |
| generic | 3 | 78.5 % | 33.3 % | LOW | observe; it has no unit class (`no_unit_class`) |
| multimodal | 0 | -- | -- | LOW (cold start) | observe; it has no unit class |

So exactly one class, bounded-code, is eligible to act. Every other class observes.

The contract admission stays **observe by default**: `CPP_CCR_ADMISSION` is unset, so a W1 verdict is recorded and never refuses.

DEFLATE is **on by default** for MEDIUM slim launches. Its off switch is `CPP_CCR_DEFLATE=off`.

A `--bg` launch does not inherit the env (W0 E3), so it only records `would_deflate`, with `delivered: false`.

## 2. Admission actions, tested from both poles
`python3 tools/test_gsd_mission_ccr_a6.py` -> **13 passed, 0 failed** (re-run this session):

    PASS V-CCRA6-ENFORCE-MEDIUM-REFUSES RECOMPILE
    PASS V-CCRA6-ENFORCE-LOW-OBSERVES ADMISSIBLE
    PASS V-CCRA6-DEFLATE-DECLARES-UNIT {'class': 'bounded-code-worker', 'id': 'm-defl'}
    PASS V-CCRA6-DEFLATE-LEAVES-DECLARED None
    PASS V-CCRA6-DEFLATE-LOW-OBSERVES [... 'action': 'would_deflate', 'delivered': False}]
    PASS V-CCRA6-DEFLATE-OFF-SWITCH
    PASS V-CCRA6-DEFLATE-BG-NOT-DELIVERED [... 'why': '--bg launch does not inherit env (W0 E3)'}]
    PASS V-CCRA6-DET-RUNS-NO-MODEL {'ok': True, 'rc': 0}
    PASS V-CCRA6-DET-FAIL-NO-FALLBACK
    PASS V-CCRA6-DET-OUTSIDE-TREE-REFUSED deterministic: '../../etc/passwd.py' is not a .py/.sh file inside ...
    PASS V-CCRA6-DET-ABSENT-LAUNCHES-MODEL
    PASS V-CCRA6-A3-MODELS-BOUNDED-CODE-MEDIUM bounded-code MEDIUM SPLIT
    PASS V-CCRA6-A3-MODELS-LOOKUP-LOW lookup LOW ADMIT_LOW_CONFIDENCE

The poles:
- **DEFLATE acts:** an undeclared bounded-code MEDIUM slim launch gets `CCR_WORK_UNIT`, pointing at a declaration file (`{"class": "bounded-code-worker", "id": <mission>}`). A `deflate_applied` ledger row is written.
- **DEFLATE does not act:**
  - when the launch already declares a unit;
  - for a LOW class (it records `would_deflate`);
  - when `CPP_CCR_DEFLATE=off` (nothing is recorded);
  - for a `--bg` launch (it records `delivered: false`).
- **DETERMINISTIC_PATH acts:** a packet line `deterministic: <script> [args]` runs the script.
  - It spends no epoch and calls no model. The runner and spawner raise if they are called.
  - On exit 0, the mission completes with the output's sha256 on the record.
- **DETERMINISTIC_PATH does not act:**
  - A packet without that line launches the model normally.
  - A failing script leaves the mission where it was, with a `deterministic_failed` row, and **never** falls back to a model.
  - A script outside the work tree, or not a .py/.sh file, is refused.
- **The real A3 `pgo-classes.json`** (no stub) classifies a code packet as bounded-code MEDIUM, which is declared, and a lookup packet as LOW, which only observes.

### Mutation drill
`vault/programs/ccr/stage3/a6/mutation_drill.py`, output in `mutation_drill.out.json`:
- Each mutation runs in its own `mktemp` copy of `tools/` + `vault/config/` + the A3 `pgo-classes.json`.
- Every mutation is killed, each by its own gate. The unmutated control copy is green.

| mutation | suite | failing gates |
|---|---|---|
| control (unmutated) | 13/13 | -- |
| enforce at LOW (`_ccr_enforceable` -> True) | 12/13 | ENFORCE-LOW-OBSERVES |
| DEFLATE ignores confidence | 11/13 | DEFLATE-LOW-OBSERVES, A3-MODELS-LOOKUP-LOW |
| deterministic path skipped | 11/13 | DET-RUNS-NO-MODEL, DET-FAIL-NO-FALLBACK |
| outside-tree script allowed | 12/13 | DET-OUTSIDE-TREE-REFUSED |
| failing script completes the mission | 12/13 | DET-FAIL-NO-FALLBACK |
| unit env not delivered to the spawn | 11/13 | DEFLATE-DECLARES-UNIT, A3-MODELS-BOUNDED-CODE-MEDIUM |

The first drill run went red on 3 gates for every mutation, including the control. The cause was in the copy, not the code: the `slim-t2` floor `requires` `vault/config/slim-critical-settings.json`, and the copy did not include it. Without it the route ESCALATEd. The drill now copies all of `vault/config`.

### Regression (the existing gsd_mission suites, A6 tree vs HEAD 3665d157)
These pass with A6:
- `test_gsd_mission.py` MC_PASS=230/230
- admission 43/43
- baseline 21/21
- capsule_v2 73/73
- ccr_contract 5/5
- chain 11/11
- cost_hold 23/23
- envelope 67/67
- freshness 18/18
- goal_control 27/27
- owner_hold 32/32
- protocol 11/11
- quota_relogin 7/7
- surface 6/6

Three suites are red **identically at HEAD 3665d157**, before A6. They ran in a detached worktree of HEAD and gave the same failing lines, so A6 did not cause them:
- `cwd_align` 15/16 (V-MCA-SUPERVISE-ORDER)
- `legacy_characterization` 24/33 (`shadow_breakeven` new rows, s_cards capsule bytes 7828B -> 7912B)
- `sleep` 5/6 (V-SLEEP-ONE-ROW-PER-HOLD, auth_expired)

## 3. DEFLATE intervention: a real undeclared launch, priced against its own project's history (laptop projections)
I surveyed 154 projected sessions (`a6/survey.py` -> `a6/sessions.json`), keyed on the receipt's `start.unit`:
- 76 non-declared sessions open at a first-call context of 60K or more.
- The 2 declared sessions (`bounded-code-worker`: 8c3d8a8e, fa1e65cd) open at **18,077-18,308**.

The chosen launch is **9cdf4fbb**:
- non-interactive, `unit: null`, opus, 2026-10-12T01:39Z;
- Madzia project (KobiiSports-Resort);
- first-call context **75,550**.

Its own project's lean unit workers (0bdd6fe2, bf6d4b07, f03c1c84) opened at 18,137 / 17,235 / 19,100, median **18,137**.

One session was excluded: 8dd034fb (74,115, haiku) was the V1 attempt-1 OFF canary, a deliberate arm and not a natural launch.

9cdf4fbb has no mission record in `missions.json`. It is a receipt session, so its class is not in the A3 corpus. The counterfactual assumes it would be classified bounded-code, like that project's unit workers. That is the only class where DEFLATE acts.

`a6/deflate_counterfactual.py` -> `a6/deflate_counterfactual.json`:
- D = 75,550 - 18,137 = **57,413 tokens removed from each of the 13 calls**.
- Weighted pricing:
  - Call 1 is priced at its own mix: 16,027 cache_read + 59,521 cache_creation, so 1.006 per context token.
  - Later calls are priced at cache_read (0.1).
  - Output is left unchanged.

| 9cdf4fbb (13 calls) | before (as run, undeclared) | after (DEFLATE: unit declared) | saved |
|---|---:|---:|---:|
| processed | 1,233,784 | 487,415 | **746,369 (60.5 %)** |
| weighted | 255,548.2 | 128,893.1 | **126,655.1 (49.6 %)** |

This is a counterfactual on a past launch, not a re-run. It assumes the declared floor would hold for this session's work. That assumption is backed only by the same project's unit workers, which opened at 17.2-19.1K and ran 23-31 calls to a last context of 65-99K.

## 4. DETERMINISTIC_PATH, real run (Linux plane GEX44, host 2.1.296)
The obligation is one of this programme's checks: re-measure Stage 3 units A2-A5 processed tokens from their run files.
- Script: `a6/remeasure.py`. It applies the same rule as drive.sh `spent()`: assistant lines, first usage per message id, input + cache_read + cache_creation + output.
- `a6/det_route.py` routes it through `gsd_mission` in an isolated mission store:
  1. create
  2. packet `deterministic: vault/programs/ccr/stage3/a6/remeasure.py <data> A2 A3 A4 A5`
  3. `admit_route` (ADMISSIBLE)
  4. `launch_worker`, with a runner and spawner that raise `AssertionError` on any model launch.

Run 2026-10-14 (store `ccr-s3-data/a6-det-state-r3`, output `a6/det_route.r3.out.json`; attempt 2's identical run is `a6/det_route.out.json`):

| field | value |
|---|---|
| admission | ADMISSIBLE |
| rc | 0 |
| **model_calls** | **0** (no jobs/ or sessions/ dir created in the store; the raising runner/spawner were never called) |
| mission state | COMPLETED, epoch 1 (no epoch claimed) |
| stdout | `{"A2": 4302121, "A3": 1678774, "A4": 6352270, "A5": 2012075}` |
| stdout sha256 | f6c3f228d428ef407ab9b7ce4bc31e6426cd831a85f6f15cef929e7218aa30df (same in both runs) |

### Correctness
| unit | earlier measured (packet) | deterministic output | equal |
|---|---:|---:|---|
| A2 | 4,302,121 | 4,302,121 | yes |
| A3 | 1,678,774 | 1,678,774 | yes |
| A4 | 6,352,270 | 6,352,270 | yes |
| A5 | 2,012,075 | 2,012,075 | yes |

Before and after for this obligation, as routed through `gsd_mission`:
- **Before A6:** a packet mission always launched a worker. That costs at least one slim floor (13,507 per call, `slim-t2` in `route-floors.json`) and, normally, several calls.
- **After A6:** the cheaper path answered with **0 model calls and 0 processed tokens**, and every value matches exactly.

## 5. Verdict
- **DETERMINISTIC_PATH ran for real.** It made 0 model calls and its output equals the earlier measured values (4/4).
- **DEFLATE is wired and tested from both poles.** It acts only on bounded-code (MEDIUM). On the real undeclared launch 9cdf4fbb it would have saved 746,369 processed (60.5 %) and 126,655 weighted (49.6 %). That number is a counterfactual from laptop projections, not a measured re-run.
- Enforcement of the W1 contract is still opt-in (`CPP_CCR_ADMISSION=enforce`). Where it is on, it refuses only at MEDIUM or HIGH.
