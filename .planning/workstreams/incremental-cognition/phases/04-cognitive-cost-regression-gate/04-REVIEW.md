---
phase: 04-cognitive-cost-regression-gate
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - tools/floor_regression_gate.py
  - tools/test_floor_regression_gate.py
findings:
  critical: 2
  warning: 3
  info: 2
  total: 7
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-04
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `tools/floor_regression_gate.py` (1170 lines) and skimmed the matching gate drills in `tools/test_floor_regression_gate.py` (2427 lines). The refusal paths (reference validation, explanation validation, write-target fence, session-id validation, probe fence, redactor-unavailable) are solid. The weaknesses sit in the reading of the transcript window and in scope attribution: the gate can say `WITHIN_BOUND exit=0` for a floor it did not fully read, and a hook element can be filed as `project` when its origin was not proved. Each finding below was reproduced with a synthetic transcript under `/tmp/rv_fl2` (scripts `exp.py`, `exp2.py`) driven through the real CLI; no source file was modified.

## Critical Issues

### CR-01: Unparseable lines inside the startup window are dropped silently; the verdict is still WITHIN_BOUND exit 0

**File:** `tools/floor_regression_gate.py:164-174` (read_window), `:603-641` (measure)
**Issue:** `read_window` turns a line that fails `json.loads` into `row = None`, appends the raw bytes to `raw_lines` (so the window hash still moves and the row count still includes it) but never adds a row and never counts it. `measure` therefore classifies a floor with that line missing, and nothing downstream reports it. A transcript whose `instructions` line is truncated (copied mid-write, `--project-dir` picking the newest still-live session, a damaged file) yields an undercounted floor. If the missing line is the one that grew, the rise is invisible. The module contract ("never 0 on anything not measured", exit-code docstring line 17) is violated.
Reproduced: reference = 100,000-char `memory_global` + listing; check transcript with the same `instructions` line cut to 50 bytes:
```
WINDOW ref_sha256=56d11cd906ef now_sha256=4a3c3a32d954 ref_rows=3 now_rows=3 same=no
LAYER memory_global scope=universal ref=100000 now=0 delta=-100000
FLOOR verdict=WITHIN_BOUND exit=0 reason=within_bound
```
`window.same=no` is printed but is informational only; the exit code is 0.
**Fix:** count unparseable (and non-dict) lines in `read_window` and refuse any in the window:
```python
bad = 0
...
except ValueError:
    row = None
if not isinstance(row, dict):
    bad += 1
...
if bad:
    raise Unmeasurable("unreadable", f"{bad} window line(s) are not JSON objects")
```
(Allow a documented tolerance only for a final partial line when no assistant row exists, and report it as `partial_window`.)

### CR-02: A written reference records raw hook command text, protected only by a regex redactor that misses common credential shapes

**File:** `tools/floor_regression_gate.py:292-296` (command_label), `:370`, `:841-878` (write_reference)
**Issue:** The `source` of every hook component is the full registered hook command (up to 200 chars; for longer ones the first 120 chars plus a digest). `write_reference` writes it into `reference.json`, a committed file (`vault/programs/incremental-cognition/floor/reference.json`). The only protection is `redact_obj`, and `modules.secret_firewall.redact` does not catch simple credential shapes. Observed directly: `redact()` returned unchanged both an unquoted `password=<16 chars>` assignment and a `token: '<16 chars>'` pair. End to end, with a hook command that carried a password-style environment assignment and a password-style flag (registered in the user's settings, with a matching hook_success row), `--write-reference` exited 0 and the written reference held the whole command line, secret-like values included, as the component `source`. A credential embedded in a hook command line (common for one-liner hooks) is persisted verbatim into a tracked file. Nothing in the comparison needs the command text; a digest is enough.
**Fix:** store only a stable non-reversible key for the source, for example the event plus `sha256(cmd)[:12]` and at most the basename of the script token; drop the 120-char prefix. Keep the basis in `scope_basis`. If readable labels are wanted, build them from an allow-list (interpreter plus script basename), never from the raw command.

## Warnings

### WR-01: A reference layer that is entirely absent from the checked floor reads as a fall, not as a comparison that could not be made

**File:** `tools/floor_regression_gate.py:967-1024` (compare), `:1018` (ratchet_hint)
**Issue:** `compare` only acts on positive deltas. A check transcript with no `instructions` attachment at all (resumed or compacted session, wrong session picked by `--project-dir`, partial transcript) produces large negative rows, `WITHIN_BOUND`, exit 0 and a `ratchet_hint`. Reproduced: reference with a 100,000-char `memory_global`; check transcript without the instructions row gives `LAYER memory_global ... delta=-100000` and `FLOOR verdict=WITHIN_BOUND exit=0`. A floor that lost its whole memory layer is far more likely a different kind of session than a 100 KB reduction, and nothing else would be verified in it.
**Fix:** refuse (exit 2, `reason=layer_missing`) when a layer holding at least 3 % of the reference total is wholly absent from the measured components, unless an explicit flag acknowledges it.

### WR-02: Hook elements with no JSON-matching producer row are filed `project` on the event alone, and plain-text hook output can never be correlated

**File:** `tools/floor_regression_gate.py:320-344` (correlate_hook), `:347-360` (_event_scope); pinned by `tools/test_floor_regression_gate.py:532-555` (g_hook_event_fallback, "project only -> project")
**Issue:** `correlate_hook` only matches a hook_success row whose stdout is a JSON document carrying the element (`json.loads(stdout)` failure leads to `continue`). A hook that prints plain text is never correlated, so attribution drops to `_event_scope`, which returns `project` whenever the project's settings register ANY hook for that event and the user's settings register none. A plugin hook (registered in neither settings file) that adds context on that event is then labelled `project`. `project` is exempt from the 1,000-char rule (`SCOPES_UNDER_1K` is universal and unattributed only), so a universal addition in the 1,000-2,999 char band, the exact band that rule exists for, passes. This contradicts the docstring statement that a component whose origin cannot be proved is `unattributed` (lines 34-35).
Reproduced: project settings register `SessionStart`, user settings register nothing, one `hook_additional_context` element of 1,500 chars with no matching producer row, 100,000-char reference:
```
LAYER hook_context:SessionStart:SessionStart:x scope=project ref=0 now=1500 delta=+1500
SCOPE universal=+0 project=+1500 ...
FLOOR verdict=WITHIN_BOUND exit=0
```
With no project registration for the event, the same element is `universal` and trips `universal_1k`.
**Fix:** treat the fallback as `unattributed` (basis `event_uncorrelated`) whenever no producing row matched, and accept plain-text stdout in `correlate_hook` (`stdout.strip() == element`). Update `g_hook_event_fallback` so "project only" expects `unattributed`.

### WR-03: Unmeasured or non-comparable token axis still ends WITHIN_BOUND exit 0; in practice the axis is rarely comparable

**File:** `tools/floor_regression_gate.py:952-960` (_tokens_axis), `:1006-1008`, `:1014`; pinned by `tools/test_floor_regression_gate.py:1229-1253` (g_no_model_call expects rc 0)
**Issue:** When the check has no model call, or the prompt digests differ, `_tokens_axis` returns `no_model_call` / `not_comparable` and no finding is produced; the verdict is `WITHIN_BOUND` with the same wording and exit code as a floor whose token axis passed. The prompt digest covers user rows and `file` attachments, so a `--project-dir` or `--session` check of any session whose first prompt differs from the reference's is `not_comparable`, which is the normal case. Tokens are the only axis that sees content the transcript does not hold (tool definitions, system prompt expansion), so "token rise exists but was not compared" is reported as green. This breaks the "never 0 on anything not measured" statement at line 17; the `TOKENS status=` line is the only signal.
**Fix:** make the verdict explicit, for example `WITHIN_BOUND_PARTIAL`, and require an explicit `--chars-only` flag to exit 0 when the token axis was not compared; otherwise exit 2 `tokens_not_comparable`.

## Info

### IN-01: A failed `--replace` write leaves a stray temp file

**File:** `tools/floor_regression_gate.py:866-870`
**Issue:** `<target>.tmp<pid>` is created, and if `fh.write` or `os.replace` raises `OSError` the `except OSError` at line 876 reports `write_failed` without removing it. The reference directory is committed, so the stray file can be staged by a broad `git add`.
**Fix:** unlink the temp file in the failure path, or create it with `tempfile.mkstemp(dir=target.parent)` and clean up in `finally`.

### IN-02: `--probe` appends to a tracked repo file, and `--json` drops the UNMEASURABLE `detail`

**File:** `tools/floor_regression_gate.py:725-726`, `:1100-1101`, `:1114-1116`
**Issue:** (a) Without `CPP_FLOOR_PROBE_RESULTS`, `--probe` appends one row to `wiki/tools/listing_floor_probe.results.jsonl`. This is acknowledged in 04-04-PLAN.md but the tool's own docstring and `--help` do not mention it, so a `--probe` user dirties a tracked file silently. (b) `JSON_KEYS` omits `detail` and `probe_error`, so `--json` output for exit 2 carries only `reason`; the named detail appears in text mode but not machine mode.
**Fix:** add one line about the results file to the module docstring and the `--probe` help text; add `"detail"` and `"probe_error"` to `JSON_KEYS`.

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
