---
phase: 02-gex44-observed-baseline
reviewed: 2026-09-28T13:20:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py
findings:
  blocker: 0
  warning: 5
  total: 5
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-28T13:20:00Z
**Depth:** standard (traced call chains into tools/tis_observed.py, tools/budget_monitor.py,
tools/tis_report.py, tools/pricing_source.py; ran `--selftest`; cross-checked field-level
arithmetic against the committed EVIDENCE.md run)
**Files Reviewed:** 1
**Status:** issues_found

## Summary

`by_entrypoint.py` was read in full alongside the four tools it composes. `python3
by_entrypoint.py --selftest` was run and passes `BYEP_SELFTEST_PASS=9/9`, exit 0, confirming
S1-S9 (grouping, shared-share, 7-day window + 1h-write share, budget_monitor reconcile, CLI
reconcile, the MISMATCH negative pole, own-dir exclusion, unpriced-model handling, and the
privacy check against `json.dumps(result)`) all genuinely exercise the code paths they claim
to, not just import successfully.

No BLOCKER was found: no reported figure in the committed EVIDENCE.md traces to an arithmetic
error in this file, dedupe and pricing are fully delegated to `tis_observed`/`budget_monitor`
(never reimplemented), the median/reconciliation helpers are correct on inspection and by
selftest, and the file's own stdout/JSON output never carries a path, session id, or
transcript text (grep for secret/debug patterns is clean; S9 verifies this at runtime).

Five WARNINGs were found, all about robustness/design gaps that could produce a wrong or
silently-uncaught figure under conditions not present in the current corpus — none of them are
demonstrated to have produced a wrong number in the committed run, but each is a real gap
worth closing before this reproducer is relied on across hosts/runs where the conditions do
occur (a longer-running corpus scan, a subagent transcript missing an `entrypoint` line, etc.).

## Warnings

### WR-01: R5/R6 do not share the "now" reference used to build cutoff_ts, breaking the "one in-process snapshot" premise for those two checks specifically

**File:** `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py:277,386-394`
**Issue:** `measure()` computes `cutoff_ts = now_ts - bm.BURN_WINDOW_DAYS * 86400` once, from the
`now_ts` parameter, and every group in `_by_entrypoint_trailing_7d` (including the sdk-cli group
used for R5/R6) is filtered against that fixed `cutoff_ts`. But `reconcile["R5"]`/`R6` compare
those group totals against `bm._aggregate_observed(bm.BURN_WINDOW_DAYS, pricing,
project_dirs=dirs)` (line 386), and `_aggregate_observed` (tools/budget_monitor.py:210) computes
its own cutoff via a **fresh** `_utc_now().timestamp()` call, not the `now_ts`/`cutoff_ts` this
file already has. `measure()` does substantial I/O between computing `cutoff_ts` (line 276) and
calling `_aggregate_observed` (line 386) — two full `T.scan`/`T.iter_calls` passes over every
project dir, for `scope_all` and `scope_excl`. On a host where transcripts are being actively
appended (this host, per EVIDENCE.md's own note that `calls` read 559 in Task 1 and 591 a few
minutes later in Task 2), any call landing in the gap between the two "now" readings could be
included in one side of R5/R6 and excluded from the other, producing a MISMATCH that is not a
concurrent-writer artifact but an artifact of the reproducer's own two different clocks. This is
a safe failure mode (it surfaces as MISMATCH, triggering the documented rerun/INCONCLUSIVE path,
never a silently-wrong figure) but it means an R5/R6 MISMATCH cannot be reliably distinguished
from a genuine `budget_monitor` arithmetic defect (Defect-procedure case b) without manually
checking whether the drift is clock-induced.
**Fix:** Either accept `now_ts` as an optional parameter on a wrapper around
`_aggregate_observed`'s cutoff (not possible without touching `tools/budget_monitor.py`, which is
out of this phase's scope per the Defect procedure), or record the elapsed wall-clock time between
computing `cutoff_ts` and calling `_aggregate_observed` in the `reconcile` block so a future
MISMATCH can be attributed to clock drift rather than triaged as a possible tool defect.

### WR-02: No R1-R6 check covers the trailing-7d "cli" (or any non-sdk-cli) call population — an entrypoint-less subagent transcript would silently understate cli/sdk-cli 7-day figures with no MISMATCH raised

**File:** `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py:171-179,321-322`
**Issue:** `_by_entrypoint_trailing_7d` groups every call by `c.get("entrypoint") or "unknown"`
(line 177). A subagent transcript's own `entrypoint` value comes from `_calls_in` reading that
subagent file's own lines (tools/tis_observed.py:101-102) — it is not inherited from the parent
session's `SessionUsage.entrypoint`. If a subagent transcript ever lacks an `entrypoint` line (or
carries a different one), its calls fall into an `"unknown"` 7-day bucket instead of `"cli"`/
`"sdk-cli"`. None of R1-R6 would catch this: R1-R3 are all-time-only (session-grouped, unaffected
by per-call subagent entrypoint), R4 only checks native sessions/calls (main-session-only, so
also unaffected), and R5/R6 only check the `sdk-cli` trailing-7d group, never `cli` or the sum
across all trailing-7d groups. `multi_entrypoint_files` (line 322, `_entrypoints_in_file`) only
flags files with **more than one** distinct entrypoint value — a file with **zero** entrypoint
lines passes that check silently. On the current corpus this is verified not to be happening
(EVIDENCE.md section 2b: cli `calls` (all-time, main-only) 588 + `subagent_calls` 1429 = 2017 =
cli `calls_7d` exactly, and sdk-cli 3 + 0 = 3 = sdk-cli `calls_7d` exactly, so every subagent
call the run touched was in fact attributed to its parent's entrypoint), but nothing in the code
asserts this invariant, and a future run on a corpus where it doesn't hold would produce
understated cli/sdk-cli 7-day figures without EVIDENCE.md's `reconcile:` line ever going MISMATCH.
**Fix:** Add a reconciliation entry (or an `assumption_checks` counter) that sums trailing-7d
`calls` across every group in `by_entrypoint` (including `"unknown"`) and compares it against
`len(list(T.iter_calls(dirs, modified_since=cutoff_ts)))` filtered by the same ts rule — a
divergence would mean calls are being silently dropped into an unreported/uncompared bucket.

### WR-03: Dead branch in `_by_entrypoint_trailing_7d` — `if usd is None` can never be true

**File:** `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py:216-225`
**Issue:**
```python
prices = models.get(model)
if pricing_ok and prices:
    usd, _assumed = T.cost_usd(usage, prices)
    if usd is None:
        unpriced_calls += 1
        ...
```
`tools/tis_observed.py:160-161` shows `cost_usd` returns `(None, False)` **only** when `not
prices` is true. This branch is only reached when `prices` (== `models.get(model)`) is already
truthy, so `T.cost_usd(usage, prices)` can never return `None` here — the `if usd is None:` arm
is unreachable. It doesn't cause a wrong figure (the `else` arm always fires instead), but it
misrepresents `cost_usd`'s actual contract to a future reader/maintainer and could mask a real
regression if `cost_usd`'s contract ever changes to return `None` for other reasons (e.g. a
malformed price row) without this branch being noticed as newly-reachable-but-untested.
**Fix:** Remove the dead `if usd is None` branch, or replace it with an explicit comment noting
`cost_usd` cannot return `None` here given the guard, and add a defensive
`assert usd is not None` if the intent is to catch a future contract change loudly instead of
silently mis-summing.

### WR-04: Repo-root check executes as an import-time side effect, not gated on `__main__`

**File:** `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py:32-40`
**Issue:**
```python
if not (ROOT / "tools" / "tis_observed.py").is_file():
    print(json.dumps({"state": "UNMEASURED", "reason": "repo root not found"}))
    sys.exit(2)

sys.path.insert(0, str(ROOT / "tools"))
import tis_observed as T  # noqa: E402
...
```
This block runs unconditionally at module import time (there is no `if __name__ ==
"__main__":` guard around it), so simply `import by_entrypoint` from another script/REPL — not
just running it as a CLI — will print to stdout and call `sys.exit(2)` if the repo layout ever
changes relative to this file. It is currently harmless because nothing else imports this
module, but it is a latent trap for reuse (e.g. Phase 4's stated plan to reuse this composition)
and is inconsistent with `measure()` being documented as "a pure function of its inputs" a few
lines later — the surrounding module is not import-safe.
**Fix:** Move the existence check and `sys.path` mutation into a `_ensure_tools_importable()`
function called from `main()`/`selftest()` (or guard the whole prelude with
`if __name__ == "__main__" or True` intent made explicit), so importing the module for its
`measure()` function (as Phase 4 intends) doesn't risk an unexpected `sys.exit`.

### WR-05: `measure()` stitches together many independent, non-atomic reads of the same live corpus — the "one in-process snapshot" is several sequential snapshots

**File:** `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py:272-406`
**Issue:** A single `measure()` call performs, in order: `T.iter_calls(dirs)` for `all_calls`
(line 296); `T.iter_calls(dirs)` again for `win_calls` (implicit re-derivation from `all_calls`,
fine) but then `_build_scope(dirs, ...)` for `scope_all` calls `T.scan(scope_dirs)` (one full
re-read) followed by `T.iter_calls(dirs, modified_since=cutoff)` (another full re-read) inside
`_by_entrypoint_trailing_7d`; `_build_scope(excl_dirs, ...)` for `scope_excl` repeats both reads
a third and fourth time; `tis_report.main(["--observed", "--all-projects"])` for R4 triggers a
fifth independent `T.scan`; and `bm._aggregate_observed(..., project_dirs=dirs)` for R5/R6
triggers a sixth independent `T.iter_calls`. None of these six-plus passes share a snapshot or a
lock — each simply re-opens and re-reads every `*.jsonl` file under `dirs` at whatever moment it
runs. EVIDENCE.md's own text acknowledges the general phenomenon between Task 1 and Task 2 (two
separate process invocations, "calls" read 559 then 591), but the same risk exists **within one
`by_entrypoint.py` invocation** since transcripts are actively written on this host throughout a
single run. The `reconcile` MATCH/MISMATCH + 3x-rerun protocol (external to this file, in the
calling plan) is the only mitigation; the code itself provides no way to distinguish "reconciled
because genuinely consistent" from "reconciled because six near-simultaneous reads happened to
land the same way this time."
**Fix:** Out of scope to fully fix without a corpus-level snapshot mechanism (e.g. hardlinking
the transcript tree, or reading each file's bytes once and passing the parsed structure to every
consumer instead of re-invoking `T.scan`/`T.iter_calls` per section). At minimum, document this
explicitly in the module docstring (currently only implied by the Task 2 EVIDENCE.md prose, not
stated in the code) so a future maintainer building on `measure()` doesn't assume its six read
passes are atomic.

---

_Reviewed: 2026-09-28T13:20:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
