---
phase: 04-prefix-cache-miss-a-b
reviewed: 2026-09-28T14:55:21Z
depth: deep
files_reviewed: 1
files_reviewed_list:
  - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py
findings:
  critical: 1
  warning: 2
  info: 1
  total: 4
status: issues_found
---

# Phase 04 (prefix-cache-miss-a-b): Code Review Report

**Reviewed:** 2026-09-28T14:55:21Z
**Depth:** deep (full read + cross-file trace into `tools/tis_observed.py`, `modules/secret_firewall/redactor.py`; selftest, readout and evidence-lines executed read-only)
**Files Reviewed:** 1 (`ab_runner.py`; `EVIDENCE.md` and `raw/ab-live.json` read as supporting evidence, not as reviewable source)
**Status:** issues_found

## Summary

`ab_runner.py` was reviewed for: transcript lookup by session id, first-call selection, cache_read/cache_creation
extraction via `tis_observed`, reuse-ratio math, the TTL rule, validity rules VR1-VR7, verdict rules R1-R8
(reachability and ordering), and the safety properties (never more than 4 model calls, env scrubbing/blocking, no
credentials-file reads, no writes under `~/.claude`, no raw transcript text in output).

Commands run (all read-only, no `claude -p`, no `--live`):
- `python3 ab_runner.py --selftest` → `ABRUN_SELFTEST_PASS=14/14  threshold=14/14` (all 14 cases pass, including the
  full fake-claude `live()` run S11 and the guard matrix S12/S13).
- `python3 ab_runner.py --readout raw/ab-live.json` → `READOUT: MATCH` (no `--write`, file untouched).
- `python3 ab_runner.py --evidence-lines raw/ab-live.json` → reproduced the same figures recorded in `EVIDENCE.md`.
- Manual recomputation of `gap_run2 = s_B2 - s_A2 = 0.999638 - 0.999658 = -2e-05` and the R8
  `similar-reuse-variance-not-observed` classification against `RULES` confirms the recorded verdict for the one
  live run this phase actually made is correct.
- Two isolated, non-networked Python probes (run outside the phase dir, never touching `raw/ab-live.json`) were used
  to prove CR-01 and WR-02 below by direct function call; both are cited with reproduction steps.

The transcript-lookup, first-call-selection, cache extraction, reuse-ratio math, TTL rule, VR1-VR6 and R1-R8 verdict
logic were all traced against the pre-registered design in `04-01-PLAN.md` and found correct, including boundary
cases (`gap` exactly at ±0.1/0.3, `M1`/`M2`/`vA` UNKNOWN branches, `run_validity`'s dependence on `ref_model` /
`prev_run`). No path launches more than the fixed 4 `claude -p` processes (`RUN_ORDER` is a 4-tuple, iterated once,
no retry/replacement logic), no code path reads `~/.claude/.credentials.json` (only `claude auth status --json` is
invoked, filtered to an explicit key allowlist), and no writes occur outside `SCRATCH_ROOT` (`/tmp/...`) or the
caller-supplied `--out` path. `parse_init`/`launch`/`evidence_lines` correctly drop reply/result text; this was also
confirmed structurally in the recorded `raw/ab-live.json` (no `result`/`text`/`content`/`message`/`stdout`/`email`
key anywhere in the tree) and by selftest S11's `bad_keys` assertion.

One BLOCKER was found in the environment-blocking guard itself (`env_check`), which is the literal mechanism this
phase relies on to guarantee it never runs on API-key billing. Two WARNINGs were found: a data-integrity gap in the
`--readout --write` recovery path, and an uncaught-exception risk in the VR7/TTL gap math on malformed timestamps.

## Critical Issues

### CR-01: `env_check()`'s ANTHROPIC_*/BLOCKING_ENV detection is value-truthy, not presence-based — an empty-but-set var silently bypasses the G1 launch guard and reaches the subprocess environment

**File:** `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py:104-105`

**Issue:** The pre-registered design (`04-01-PLAN.md`, "Environment" section) and the function's own inline comment
require blocking on the *presence* of an `ANTHROPIC_*` or `BLOCKING_ENV` name: "ANY BLOCKING_ENV name blocks on its
own, even with no ANTHROPIC_* name present." The implementation instead filters on the env var's *value* being
truthy:

```python
anthropic_names = sorted(k for k in environ if k.startswith("ANTHROPIC_") and environ.get(k))
blocking_names = sorted(k for k in BLOCKING_ENV if environ.get(k))
```

If `ANTHROPIC_API_KEY` (or any `BLOCKING_ENV` name, e.g. `CLAUDE_CONFIG_DIR`) is present in the environment but set
to an empty string — a realistic state left behind by a `.env` template, an `export ANTHROPIC_API_KEY=` line, or a
wrapper script — `environ.get(k)` returns `""`, which is falsy, so the name is silently dropped from both
`anthropic_env_names` and `blocking_env_names`. `blocked` (`bool(anthropic_env_names) or bool(blocking_env_names)`)
is then `False`, `--env-check` exits `0` instead of `3`, and `live()`'s G1 guard does **not** refuse.

Worse, for `ANTHROPIC_API_KEY` specifically, `scrubbed_env()` never removes it in the first place (it only strips
names starting with `CLAUDE`, never `ANTHROPIC_*`):

```python
def scrubbed_env(environ: dict) -> dict:
    if env_check(environ)["blocked"]:
        raise ValueError(...)
    return {k: v for k, v in environ.items() if not k.startswith("CLAUDE")}
```

so an empty-but-present `ANTHROPIC_API_KEY` flows straight through into the environment used to launch all 4
`claude -p` subprocesses (the sole safety gate protecting the phase's core invariant, "ANTHROPIC_API_KEY UNSET
throughout (subscription claudeAiOauth only)," is exactly this guard). Note the inconsistency within the same
function: `scrubbed_env_names` (line 106) correctly filters on name presence only (`k.startswith("CLAUDE") and k
not in BLOCKING_ENV`, no truthiness check), confirming the truthy filter on the other two lines is an oversight, not
a deliberate design choice. This case is not covered by selftest S2, which only exercises fully-unset vs.
non-empty-fake-string values.

**Reproduced** (isolated probe, no subprocess, no `claude` binary touched):
```
case1 ANTHROPIC_API_KEY='' -> blocked: False anthropic_env_names: [] ANTHROPIC_API_KEY field: UNSET
  scrubbed_env raised? NO. ANTHROPIC_API_KEY in scrubbed env: True value: ''
case2 CLAUDE_CONFIG_DIR='' -> blocked: False blocking_env_names: []
```

**Fix:**
```python
def env_check(environ: dict) -> dict:
    """Never includes a value -- names only."""
    anthropic_names = sorted(k for k in environ if k.startswith("ANTHROPIC_"))
    blocking_names = sorted(k for k in BLOCKING_ENV if k in environ)
    scrubbed_names = sorted(k for k in environ if k.startswith("CLAUDE") and k not in BLOCKING_ENV)
    return {
        "ANTHROPIC_API_KEY": "SET" if "ANTHROPIC_API_KEY" in environ else "UNSET",
        "anthropic_env_names": anthropic_names,
        "blocking_env_names": blocking_names,
        "scrubbed_env_names": scrubbed_names,
        "home": environ.get("HOME"),
        "blocked": bool(anthropic_names) or bool(blocking_names),
    }
```
Add a selftest case (S2) asserting `env_check({"ANTHROPIC_API_KEY": "", ...})["blocked"] is True` and the equivalent
for a `BLOCKING_ENV` name set to `""`.

## Warnings

### WR-01: `readout(..., write=True)` unconditionally forces `complete: true` even when the recovered record's `launches` count is not 4

**File:** `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py:784-792`

**Issue:** The "Readout recovery rule" in `04-01-PLAN.md` is scoped to the case where "the runner fails AFTER
launches" — i.e., all 4 `claude -p` processes already ran and only the post-processing (`assemble()`) crashed. The
code does not verify that precondition before promoting the record:

```python
if not was_complete:
    if not write:
        print("READOUT: INCOMPLETE")
        return 1
    recomputed["complete"] = True
    recomputed["completed_by"] = "readout"
    path.write_text(json.dumps(recomputed, indent=2, default=str), encoding="utf-8")
    print("READOUT: MATCH")
    return 0
```

`recomputed["complete"] = True` is set unconditionally, regardless of `recomputed["launches"]` (which `assemble()`
computed as `len(runs)` a few lines earlier, inside the same call). If `ab-live.json` was left with `complete: false`
because `live()` crashed mid-loop (e.g. after only 2 of the 4 launches), `--readout --write` on that file will mark
it `complete: true` even though only 2 launches occurred — `verdict`/`rule_fired` do correctly come out as
`UNJUDGED`/`R2` (since `verdict()` independently checks `launches != 4`), so the *verdict value* is not corrupted,
but the top-level `complete` flag — the field this exact tool and its own recovery-rule documentation treat as "all
4 runs are in" — becomes misleading provenance for a genuinely partial record.

**Reproduced** (synthetic file in `/tmp`, never touching `raw/ab-live.json`): starting from a 2-of-4-run record with
`complete: false`, `--readout /tmp/partial-ab-live.json` (no `--write`) correctly prints `READOUT: INCOMPLETE` (rc
1); `--readout /tmp/partial-ab-live.json --write` prints `READOUT: MATCH` (rc 0) and rewrites the file to
`{"runs": 2 entries, "launches": 2, "complete": true, "verdict": "UNJUDGED", "rule_fired": "R2", "completed_by":
"readout"}` — `complete: true` on a 2-launch record.

**Fix:** Gate the force-complete branch on `recomputed.get("launches") == 4` (or generally, on `not
run_validity`-style invalid launch count), and refuse (non-zero exit, no write) otherwise:
```python
if not was_complete:
    if not write:
        print("READOUT: INCOMPLETE")
        return 1
    if recomputed.get("launches") != 4:
        print(f"READOUT: REFUSED (launches={recomputed.get('launches')} != 4, "
              f"this file was never completed by live())")
        return 1
    recomputed["complete"] = True
    ...
```

### WR-02: `_vr7_ok()` / `_ttl_of()` raise an uncaught `TypeError` on a timestamp that parses but lacks a UTC offset

**File:** `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py:419` (`_vr7_ok`)
and `:626` (`_ttl_of`)

**Issue:** `_parse_iso()` only replaces a literal trailing `"Z"` before calling `datetime.fromisoformat`:
```python
def _parse_iso(ts):
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
```
If `ts` is a syntactically valid ISO-8601 string that carries no `Z` and no explicit offset (e.g.
`"2026-01-01T12:00:05"`), `fromisoformat` does **not** raise — it silently returns a naive `datetime`. `_vr7_ok`
then does `gap_s = (t2 - t1).total_seconds()` (line 419) and `_ttl_of` does the same at line 626, with no
`try/except` around the subtraction. Subtracting an aware `datetime` (the normal `...Z` case) from a naive one
raises `TypeError: can't subtract offset-naive and offset-aware datetimes`, uncaught anywhere in the call chain
(`run_validity` → `assemble` → `live`/`readout`). For `live()`, `assemble()` is only called *after* all 4 launches
have already completed, so this cannot cause extra launches, but it would crash the process before
`result["complete"]` is set to `True`, leaving a `complete: false` record that then depends on the WR-01 recovery
path (and would itself need a code fix per the plan's own recovery rule, since `rules_fingerprint` covers
`_vr7_ok`/`ttl_bound` but a bug fix here would need to keep the fingerprint byte-identical per the stated rule, or
be explicitly recorded as a `runner_post_registration_diff`).

In practice, every timestamp actually seen in the recorded evidence (`raw/ab-live.json`) and every timestamp
`tis_observed._calls_in` reads from `obj.get("timestamp")` carries a trailing `Z`, so this was not triggered by the
one live run this phase made. It is nonetheless a real, reachable, currently-untested gap in the VR7/TTL code this
task was specifically asked to check.

**Reproduced** (isolated probe, pure function call, no filesystem/network touched):
```
prev = last_call_ts="2026-01-01T12:00:00Z" (aware)
cur  = first_call.ts="2026-01-01T12:00:05" (no Z -> naive)
_vr7_ok(prev, cur) -> TypeError: can't subtract offset-naive and offset-aware datetimes
```

**Fix:** Normalize in `_parse_iso` instead of assuming every timestamp already carries a zone:
```python
def _parse_iso(ts):
    if not ts:
        return None
    try:
        d = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d
```
and add a selftest case feeding a Z-less `ts` through `_vr7_ok`/`ttl`-path to confirm it now fails the rule cleanly
(VR7 failure, or a defined bound) instead of raising.

## Info

### IN-01: `verdict()`'s final `"unclassified"` (R8) branch is unreachable dead code

**File:** `.planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py:536-546`

**Issue:** The five `gap`-range branches in `verdict()` (`abs(gap) < GAP_NULL`; `gap >= GAP_SUPPORT and s_B2 <
B2_FLOOR`; `gap >= GAP_SUPPORT and s_B2 >= B2_FLOOR and vA != "YES"`; `GAP_NULL <= gap < GAP_SUPPORT`; `gap <=
-GAP_NULL`) exhaustively partition the real line into `(-∞, -0.1] ∪ (-0.1, 0.1) ∪ [0.1, 0.3) ∪ [0.3, ∞)` (the
`gap >= GAP_SUPPORT` cases are handled earlier still, by the R5/first two R8 sub-branches above them, for the
`[0.3, ∞)` piece). Every finite `gap` value is caught by one of these, so the trailing
`return ("UNJUDGED", "unclassified", "R8")` at line 546 can never execute. Harmless as a defensive fallback (better
than a crash if the partition is ever changed and a gap is left uncovered), but worth flagging since it is untested
by S10 and, if it ever *did* fire in a real evidence file, would silently mask a logic error in the surrounding
branches rather than surfacing one.

**Fix:** No functional change required; optionally add a selftest assertion (or an `assert False, "unreachable"` in
a debug build) documenting that this branch is a deliberate belt-and-braces fallback, not a reachable rule.

---

_Reviewed: 2026-09-28T14:55:21Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Orchestrator disposition (2026-09-28)

Findings are NOT auto-fixed in this phase. `ab_runner.py` was pre-registered by sha256
(`runner_sha256: 9414fd25...`, EVIDENCE section 1, commit 740b41b) before the live window, and the
verifier's integrity check rests on `git diff 740b41b..HEAD -- ab_runner.py` being empty. Editing it now
would detach the committed evidence from the code that produced it.

- CR-01 (empty-but-set ANTHROPIC_* bypasses G1): no effect on the recorded run. Before dispatching the
  executor, the orchestrator listed this session's environment by variable NAME (not value) for
  `^(ANTHROPIC_|CLAUDE_CODE_OAUTH_TOKEN$|CLAUDE_CONFIG_DIR$|CLAUDE_CODE_USE_)` and got no match, so no such
  name existed, empty or not. Independently, all four runs' init events record `apiKeySource none`
  (EVIDENCE A1/A2/B1/B2_init, validity rule VR6), i.e. no API key reached claude.
- Status: OPEN, blocking any REUSE of ab_runner.py. Fix CR-01 (detect by name presence), WR-01, WR-02 and
  drop IN-01's dead branch in a new commit, with a new runner sha, BEFORE any further live run. The run
  directory's LIVE-LATCH already refuses a second live invocation of this copy.
