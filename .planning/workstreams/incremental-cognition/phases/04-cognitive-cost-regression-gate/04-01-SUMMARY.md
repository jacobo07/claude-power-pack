---
phase: 04-cognitive-cost-regression-gate
plan: 01
subsystem: floor-regression-gate
tags: [pillar-K, IC-K, startup-floor, scope-split, materiality, mutation-drill, window-pin]
requires: []
provides:
  - "tools/floor_regression_gate.py: ROOT, DEFAULT_REFERENCE_REL, SCHEMA floor-reference/1, LAYER_PCT, TOTAL_PCT, TOKENS_PCT, UNIVERSAL_MIN_CHARS, SCOPES, SCOPES_UNDER_1K, HARNESS_TYPES, Unmeasurable, host_plane, read_window, window_digest, classify, scope_for_instruction, scope_for_system_prompt_part, scope_key, measure, load_reference, validate_explanations, covering_explanation, is_material, compare, exit_code, render, write_reference, load_redactor, redact_obj, build_parser, main; flags --check --write-reference OUT --transcript --reference --replace --json; exit 0 within bound / 1 material unexplained rise / 2 UNMEASURABLE"
  - "tools/test_floor_regression_gate.py: Tx builder, floor_pair, run_cli (sys.executable), 26 V-FLOOR-* gates, --drill (8 mutants), --gate-path"
affects: ["04-02", "04-03", "04-04"]
tech-stack:
  added: []
  patterns: ["one seam per judgement (scope_key, scope_for_system_prompt_part, exit_code) so a drill can attack it", "unprovable origin is `unattributed`, never project or harness", "startup window pinned by window_sha256 / window_rows from ONE function (window_digest)", "every emitted string and the reference JSON pass secret_firewall.redact at string-leaf level", "UNMEASURABLE is a typed exception mapped to exit 2, never a fallthrough to 0"]
key-files:
  created: [tools/floor_regression_gate.py, tools/test_floor_regression_gate.py]
  modified: []
decisions:
  - "R2-W1 (orchestrator requirement) items 1-2 applied: provenance.window_sha256 (sha256 over the raw startup-window lines as on disk, newline-joined, every non-empty line before the first assistant row) and provenance.window_rows; one function window_digest computes both so 04-03 can reuse it; measure() exposes them, --check prints a WINDOW line and --json carries them under provenance and reference; gate V-FLOOR-WINDOW-APPEND-STABLE (rows appended after the first assistant row move nothing, a pre-assistant edit moves window_sha256). Item 3 (the real re-read against 34f03871 and the committed reference-gex44.json) is 04-03's and is not built here."
  - "RISE total is printed only when no unexplained layer_3pct finding exists: a single row at or above 3 % always implies the total rule, so the extra line would be redundant; the verdict is identical either way"
  - "load_reference also refuses (reference_invalid) a reference whose total_chars is not the sum of its components, and a malformed component; a hand edit that desyncs the total cannot make a comparison look cleaner"
  - "an unexpected exception inside main is UNMEASURABLE reason=internal_error (class name only) rather than a traceback or an exit 0"
status: complete
commits: 3
plan_head_before: 73d546152cc6edc7e9fe223ec49acf70de08c734
actuals:
  tokens: 20900
  tasks: 3
  commits: 3
metrics:
  completed: 2026-10-04
requirements: [IC-K]
requirements-completed: []
---

# Phase 4 Plan 01: floor regression gate core (pillar K) Summary

`python3 tools/floor_regression_gate.py --check --reference <ref> --transcript <jsonl>` reads a transcript's startup window, classifies each model-visible component by layer and scope, and exits 0 / 1 / 2; a seeded +1,024-char universal addition (2.05 % of a 50,000-char floor, under every 3 % rule) goes red naming `memory_global` / `universal`, while the same bytes in the repo CLAUDE.md stay green and are reported as project. **IC-K is addressed, not satisfied** (it needs the laptop reference, plan 04-04); ledger `state.K` is still `{}` and IC-K is not ticked.

**Code commits:** `7fdef637` (Task 1 tracer), `e4459393` (Task 2 rules + rule drill), `8422eb2d` (Task 3 safety). Each `git show --stat` lists only `tools/floor_regression_gate.py` and `tools/test_floor_regression_gate.py`.

## Observed results

- `python3 tools/test_floor_regression_gate.py` -> `FLOOR_PASS=26/26  threshold=26/26  skipped=0  inconclusive=0`, exit 0, 0.75 s (limit 60 s). `V-FLOOR-READ-ONLY` PASSes on GEX44 (posix; it SKIPs on nt).
- `python3 tools/test_floor_regression_gate.py --drill` -> `PASS DRILL-CONTROL 25/25`, eight `KILLED` lines (M1 scope_key universal, M2 scope_key project, M3 UNIVERSAL_MIN_CHARS 10**9, M4 validate_explanations accepts all, M5 covering ignores bound and unit, M6 exit_code maps UNMEASURABLE to 0, M7 no layer_3pct, M8 system prompt part scope harness), `PASS DRILL-CLEAN-AFTER-MUTANTS 25/25`, `PASS DRILL-RESTORE gate file sha256 1eaca4044712a8eb before == after`, `DRILL killed=8/8`.
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `ICP_SELFTEST=PASS`; ledger `state.K` prints `{}`; `from modules.secret_firewall import redact; redact('x')` prints `x`.
- Read-only real-transcript smoke (not a gate; the real gates are 04-03's): the gate measured the finished session 607795c4 (34 window rows) at total 202,803 chars, first call 107,351 tokens, and the per-layer numbers equal the plan's planning measurements exactly (memory_global 25,037; memory_project 34,478; rules 63,625; skill_listing 30,000; SessionStart hook_context 7,798; UserPromptSubmit 2,299; agent listing 27,062; system_prompt 9,447). A reference written to /tmp from it and checked against the same transcript read `WITHIN_BOUND`, `WINDOW ... same=yes`.

## RED outputs (recorded before each build)

- Task 1: the gate file did not exist: `FAIL V-FLOOR-GATE-LOADS .../tools/floor_regression_gate.py: FileNotFoundError: [Errno 2] No such file or directory`, `FLOOR_PASS=0/1`.
- Task 2 (11/18 PASS): FAIL V-FLOOR-SCOPE-REPORT (JSONDecodeError, no `--json` yet), V-FLOOR-TOTAL-3PCT (`rc=0 rises=[]`), V-FLOOR-FALL-RATCHET-HINT (JSONDecodeError), V-FLOOR-EXPLAINED-GREEN (`rc=1 ... MATERIAL_RISE`), V-FLOOR-EXPLANATION-EMPTY-REASON (`rc=1`), V-FLOOR-EXPLANATION-FIELDS (`rc=1` for every malformed entry), V-FLOOR-TOKENS-RULE (`+3.3% tokens: rc=0 rise=[]`).
- Task 3 (20/26 PASS): FAIL V-FLOOR-UNMEASURABLE-TABLE (`FileNotFoundError` on a missing reference), V-FLOOR-NOT-COMPARABLE (`rc=0` on an edited plane/cwd), V-FLOOR-WRITE-SAFETY (existing target overwritten, `~/.claude` target written), V-FLOOR-NO-MODEL-CALL (`REFERENCE_WRITTEN` on a synthetic first call), V-FLOOR-NO-SECRET (`canary found in reference`), V-FLOOR-JSON (keys `caveats provenance reference` missing). V-FLOOR-READ-ONLY and V-FLOOR-CLI-USAGE were already green (the Task 1 reader opens read-only and argparse already refused usage errors).

## Source-level scope-split drill (Task 2 acceptance)

`sha256sum tools/floor_regression_gate.py > /tmp/ic-p4-01-sha.before`; copied to `/tmp/ic-p4-01-drill/floor_regression_gate.py`; `return "universal"` inserted as the first statement of `def scope_key(` in the COPY (python `re.sub`):

```
155:def scope_key(component):
156-    """THE scope-split seam: compare attributes every delta through it."""
157-    return "universal"
158-    return component["scope"]
```

`python3 tools/test_floor_regression_gate.py --gate-path /tmp/ic-p4-01-drill/floor_regression_gate.py` exited **1** (`FLOOR_PASS=9/18` at that point in the plan, 9 gates FAIL) and printed:

```
FAIL V-FLOOR-PROJECT-LOCAL rc=1 scope=['SCOPE universal=+1024 project=+0 harness=+0 unattributed=+0'] layer=[]
FAIL V-FLOOR-SCOPE-REPORT project: scope_deltas={'harness': 0, 'project': 0, 'unattributed': 0, 'universal': 1024}
```

then `sha256sum tools/floor_regression_gate.py | diff - /tmp/ic-p4-01-sha.before` printed nothing (`SHA-DIFF-EMPTY`): the real file was never touched. (The /tmp copy was removed-and-recreated by me; the directory did not pre-exist.)

## Deviations from Plan

### Auto-fixed / decided

**1. [R2-W1 - orchestrator requirement] window pin** - applied as written: `window_sha256` and `window_rows` in provenance, computed by the single function `window_digest`, exposed by `measure()`, printed on a `WINDOW ref_sha256=.. now_sha256=.. ref_rows=.. now_rows=.. same=yes|no` line and in `--json`. Gate `V-FLOOR-WINDOW-APPEND-STABLE`: a fixture with a user row, a Stop hook_context, a `brand_new_late` attachment and a second assistant row appended after the first assistant row leaves components, layers, totals, tokens, window_sha256 and window_rows unchanged, a reference written from the base checks WITHIN_BOUND against the appended transcript with `same=yes`; the control edits the user prompt BEFORE the first assistant row and window_sha256 changes while window_rows does not. This gate lives in the Task 1 commit (window_digest is part of the tracer's reference writer). It is in the drill's control set but has no dedicated mutant, to keep the plan's `killed=8/8` figure; the control inside the gate is what lets it go red. Item 3 (real re-read against 34f03871) is left to 04-03.

**2. [Rule 3 - staging] some Task 2 gates passed on their first run** - Task 1 already built the full classification table (including digest-identified system prompt parts) and the layer_3pct / universal_1k rules, so V-FLOOR-LAYER-TABLE, -POSITIVE-UNIVERSAL, -PROJECT-LOCAL, -PROJECT-3PCT, -BOUNDARY, -SYSTEM-PROMPT-NEW-PART, -HARNESS-NOT-1K and -UNATTRIBUTED-1K were green before Task 2's build (shipping a wrong system-prompt scope in the Task 1 commit just to show a RED seemed worse). The Task 2 RED therefore covers the 7 gates listed above; the ones that were already green are attacked by drill mutants instead. V-FLOOR-EXPLANATION-BOUND was vacuously green before explanations existed, so a control (bound 1024 == delta 1024 must cover) was added inside it.

**3. [Rule 2 - output only] `RISE total` suppression** - see decisions: no verdict change.

**4. [Rule 2 - integrity] reference validation** - `reference_invalid` also covers a malformed component and a `total_chars` that is not the sum of the components (V-FLOOR-UNMEASURABLE-TABLE exercises both, plus schema and missing keys).

**5. [Rule 3 - test plumbing] run_cli sets PYTHONPATH to the repo root** - so the `--gate-path` copy under /tmp (whose own ROOT is /tmp) can still import `modules.secret_firewall`; the gate also falls back to inserting its ROOT.

**6. [Scope split] `--json`** - implemented in Task 2 (V-FLOOR-SCOPE-REPORT and V-FLOOR-FALL-RATCHET-HINT need it); Task 3 added `reference`, `provenance` and `caveats` to the 12-key document.

**7. [trailer] commit attribution** - the three commits end with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` as the dispatch's `<sequential_execution>` block directs; the session's own attribution reminder names a different model line and the dispatch instruction was followed.

### Not done here (by plan)

- Liveness (CONTEXT): the gate is reached by `tools/test_floor_regression_gate.py`; a registry declaration, the committed `plane: gex44` reference, the real-transcript gates and the evidence file `evidence/K.md` belong to 04-03 / 04-04. `modules/liveness` was not run in this plan.

## Known Stubs

None. No placeholder, mock or empty-catch code in the two files (the only `except` blocks map to typed `Unmeasurable` reasons or restore state).

## Threat Flags

None beyond the plan's register: the gate opens transcripts read-only, writes only the `--write-reference` path, refuses `~/.claude` outside the checkout, and spawns only `git --no-optional-locks rev-parse` (never `claude -p`).

## Self-Check: PASSED

- `tools/floor_regression_gate.py` and `tools/test_floor_regression_gate.py` exist; commits `7fdef637`, `e4459393`, `8422eb2d` are on `mission/incremental-cognition-run`; `git rev-list --count 73d546152cc6edc7e9fe223ec49acf70de08c734..HEAD` = 3 at the time of the last task commit.
- `grep -c 'SCHEMA = "floor-reference/1"'` = 1; `sys.executable` appears in the test file; no `["python3",` literal.
