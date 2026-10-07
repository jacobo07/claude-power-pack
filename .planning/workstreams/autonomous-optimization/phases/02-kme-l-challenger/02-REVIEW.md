---
phase: 02-kme-l-challenger
reviewed: 2026-10-07T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - wiki/tools/kme_pillars.py
  - wiki/tools/kme_replay.py
  - wiki/tools/kme_token_audit.py
  - tools/kme_equivalence.py
  - tools/strace_io_sum.py
  - tools/test_kme_challenger.py
  - tools/test_kme_measure_tools.py
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-10-07
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Scope: the Phase 2 diff `23f5a7f1..HEAD`. That covers the access-plan, certificate, watermark and shadow code in
`kme_pillars.py`, the `select` hook in `kme_token_audit.scan_project`, the `kme_replay` wiring, the new comparator
`kme_equivalence.py`, the strace summer `strace_io_sum.py`, and their two gate files.

Each focus area was traced by hand:

- **Fallback correctness: no path found that turns an index failure into a number.** Every guard raises
  `PlanRefused`. `_resolve` (kme_pillars.py:2740) re-raises it for `challenger` and deopts for `auto`. An index answer
  other than EXACT is refused and quotes the index's own reasons (`_index_population`). The watermark closure handles
  path-spelling mismatches between the index and the disk safely: a spelling mismatch marks the session stale and it
  is read raw, or the root is refused as `root_not_indexed`. The `no_first_ts` sessions are read raw. The shadow guard
  runs before any locator probe. The backstop is the in-process population, which must be exact against the frozen
  fields. That check catches any index omission that the index's own EXACT verdict could hide. One gap remains: an
  *unexpected* exception does not deopt (WR-03). It still produces no number.
- **Exposure: no out-of-scope open found on a KME-only path.** `_scope_dirs` is the single rule for the scan, the
  watermark walk and the read-set walk. `_disk_files` and `_make_select` only call `stat`. `select` refuses a session
  before `scan_file`, so `_first_ts`, `read_subagent_meta` and the observers are never reached for a refused file. The
  locator probes inherit `ctx["access"]`, so they use the same read set. A deopt goes to the scoped tier whenever a
  filter exists. The global tier needs `--cross-project`, which `_prepare` enforces.
- **Read-only:** the index is opened `mode=ro` through `_open_index_ro`, and certificates and path logs are refused
  inside `--root`. However, neither output path is checked against the index DB itself (WR-01).
- **Secrets:** the path-log and certificate lines go through `redact`. The stderr refusal lines carry guard reasons,
  session ids and counts, never transcript text.
- **Comparator masking:** on the seven committed files it masks exactly one `measured_at`, one `command` and the H
  `commit` per file. I checked this by counting occurrences in each committed file. The patterns themselves are wider
  than documented (IN-01).
- **strace parsing:** reads are attributed from the per-call `-y` fd annotation, so a reused fd cannot be
  misattributed. Unfinished and resumed lines are paired by PID. Failed reads (`ret <= 0`) and failed opens are not
  counted. Two minor measurement caveats are in IN-03.

## Warnings

### WR-01: `certify --cert` and `--path-log` can overwrite or corrupt the usage index DB

**File:** `wiki/tools/kme_pillars.py:2390-2393, 2440` (certificate) and `wiki/tools/kme_pillars.py:2699-2705, 2511-2514` (path log)

**Issue:** The only guard on either output path is that it must not resolve inside a `--root`. Neither path is
compared with the index DB, even though the phase's read-only contract names the index DB explicitly.
- In certify, `_atomic_write(a.cert, ...)` ends with `os.replace(tmp, path)` (line 2375).
- The path log is opened with `open(lp, "a")`.

**Failure scenarios:**
- `certify ... --index-db ~/.claude/state/usage_index/index.sqlite --cert ~/.claude/state/usage_index/index.sqlite`
  (for example, a mistyped `--cert` that drops the `.kmep-cert.json` suffix) passes every guard. It reads the index,
  then atomically replaces the SQLite file with the certificate JSON. The index is destroyed.
- `--plan challenger --path-log <index-db>` appends a JSON line to the SQLite file after the run, which corrupts it
  for every later reader.
- The same applies to the `-wal`, `-shm` and `-journal` siblings.

**Fix:** In `_prepare` (path log) and `_certify` (certificate), refuse an output that resolves to the index or to one
of its siblings:
```python
def _clashes_index(out_path, index_db):
    o = os.path.realpath(out_path)
    base = os.path.realpath(index_db)
    return o in {base + s for s in ("", "-wal", "-shm", "-journal")}
# _certify, after _prepare:
if _clashes_index(a.cert, ctx["index_db"]):
    return _fail(f"--cert {a.cert} is the index DB or one of its siblings; nothing written")
# _prepare, path-log block (only when plan in challenger/auto, index_db is known there):
if path_log is not None and index_db is not None and _clashes_index(path_log, index_db): ...
```
Also add a gate row next to the `inside_ok` case of `g_certify_shadow` (`--cert` equal to `--index-db`: exit 2, DB
sha unchanged).

### WR-02: a challenger run refused by the shadow guard logs `read_set` as zero files and zero bytes after it read the whole read set

**File:** `wiki/tools/kme_pillars.py:2467-2469` (with `_resolve_scan` 2755-2763 and `_shadow_check` 2350-2366)

**Issue:** `_shadow_check` runs *after* `_measure` has opened and read every admitted transcript. On a forced
`--plan challenger`, its `PlanRefused` reaches `resolve_logged` → `report_path(..., None, exc)`. In `_path_record`,
the `refusal is not None` branch then writes a fixed record:
```python
read_set = {"basis": "planned", "sessions": 0, "files": 0, "bytes": 0, "stale": None, "no_first_ts": None}
```
`ctx["access"]["admitted"]` already holds the real files and sizes, but this branch ignores it. The path log is the
access-plan audit record, so it states that a run which read N transcripts read none. Absent is reported as zero.
That is accurate only for refusals raised before the scan (index_open … watermark).

**Failure scenario:** the index selects a session that the champion classifier rejects (the `shadow` row of
`g_deopt_logged`). The forced challenger exits 3 after reading `k1`, `k1_sub` and `n1`, and its path-log line says
`files: 0, bytes: 0`. The forced-challenger assertion in `g_deopt_logged` does not pin `read_set`, so no gate catches
this.

**Fix:** Report the admitted set whenever the scan ran, and keep `0` only for refusals before the scan:
```python
if refusal is not None:
    taken, guards, deopt = "refused", refusal.guards, {"guard": refusal.guard, "reason": refusal.reason}
    adm = (access or {}).get("admitted") or {}
    if refusal.guard == "shadow" and access:
        read_set = {"basis": "read_then_refused", "sessions": len(access["read_set"]), "files": len(adm),
                    "bytes": sum(v for v in adm.values() if v), "stale": None, "no_first_ts": None}
    else:
        read_set = {"basis": "planned", "sessions": 0, "files": 0, "bytes": 0, "stale": None, "no_first_ts": None}
```
Then assert `forced["rec"]["read_set"]["files"] > 0` in the `shadow` row of `g_deopt_logged`.

### WR-03: an unexpected exception in the index tier crashes `auto` instead of deopting, and certify's exit 1 becomes ambiguous

**File:** `wiki/tools/kme_pillars.py:2098-2117` (`_index_open`), `2124-2131` (`_index_population`), `2738-2746` (`_resolve`), `2690` (`_prepare`)

**Issue:**
- `_resolve` catches only `PlanRefused`.
- Inside the tier, only `sqlite3.Error` is converted to a refusal. Other exceptions escape:
  - `ver = int(row[0])` (line 2104) raises `ValueError` on a non-integer `schema_version`. It sits in a `try` that
    catches only `PlanRefused`, and when it raises, `con` is never closed.
  - `usage_index.population` calls `json.loads(hits)` on `pat_hits` rows, which raises `ValueError` on a malformed
    row.
  - Loading `usage_index` in `_prepare` (line 2690) can raise `ImportError` (for example, a missing
    `tis_observed` / `pricing_source`).
- Effect on `auto`: the documented contract ("challenger, deopting to scoped / global raw") breaks. The run ends in a
  traceback with exit 1 and leaves no path-log record of the failed guard.
- Effect on certify: exit 1 is already `EXIT_DISAGREE` (NOT_CERTIFIED). A crash therefore looks like a measured
  disagreement to any caller that branches on the exit code.

This fails closed (no number is produced), so it is not a blocker. It is a robustness and observability defect in
the deopt path.

**Fix:**
- Wrap the tier body so that every exception becomes a typed refusal.
- Close the connection on every path.
```python
def _index_tier(ctx):
    try:
        return _index_tier_inner(ctx)
    except PlanRefused:
        raise
    except Exception as exc:  # noqa: BLE001 -- typed, never silent
        raise PlanRefused("index_error", f"{exc.__class__.__name__}: {exc}")
```
- Do the same around the index calls in `_certify` so that exit 3 / UNMEASURED is printed instead of a traceback.
- Defer the `_usage_index()` load in `_prepare` (or catch it there) so `auto` can still deopt when the module cannot
  load.

## Info

### IN-01: comparator masks are broader than their documented locations, and no gate pins their narrowness

**File:** `tools/kme_equivalence.py:31-37`

**Issue:** The documented contract is "front-matter and JSON forms of measured_at and command, and the 40-hex commit
inside H's consumed_owner_verdicts". The patterns are wider than that:
- `^\s*"measured_at": ` and `^\s*"command": ` match the key at *any* JSON depth.
- `("commit": )("[0-9a-f]{40}")` is unanchored and applies to every pillar, not only H's `consumed_owner_verdicts`.
- The front-matter patterns `^(measured_at: )` / `^(command: )` also apply to body lines.

Today each committed file has exactly one occurrence of each (checked by count), so nothing real is hidden yet.
However, a future nested `"command"` field (for example, an H detail listing verify commands) or a second commit field
(for example, a frozen-source commit) would be masked silently. `g_equiv_volatile_masked` only proves the masks *fire*.
No gate or mutant proves they fire *only* where intended: a "mask every key named command at any depth" mutant would
survive.

**Fix:**
- Restrict the JSON patterns to the top-level indent (`^ "measured_at": ` with exactly one space, matching
  `indent=1`).
- Restrict the front-matter patterns to the `---` block.
- Anchor the commit pattern to the `consumed_owner_verdicts` object in pillar H only.
- Add a gate that inserts a nested `"command"` and a second `"commit"` into a copy and requires DIFFERENT.

### IN-02: dead `per_path` counter in the strace summer

**File:** `tools/strace_io_sum.py:152, 164`

**Issue:** `per_path` is accumulated for every read but never emitted or read.

**Fix:** Remove it, or emit it under `--list-opened`.

### IN-03: `unique_bytes` is the file size at summary time, not bytes read, and strace-escaped paths become unstattable

**File:** `tools/strace_io_sum.py:103-106, 181-190`

**Issue:**
- `unique_key` stats each opened `.jsonl` when the summary runs and adds its *current* size.
  - A file that was opened but only partly read (for example, the `_first_ts` look-ahead) counts in full.
  - On a live corpus, a file that grew between the trace and the summary counts its new size.
- strace prints non-ASCII path bytes as octal escapes. Such paths fail `os.stat` and are listed in `unstattable`
  rather than counted.

Both caveats are visible in the output (`unstattable`) or small for the GEX44 run, but the column name implies a
byte count that was read.

**Fix:** Document the column as "sum of current sizes of distinct opened files", or compute unique bytes from the
per-inode maximum read offset. Decode strace octal escapes before calling `stat`.

### IN-04: the shadow guard's "champion selected what the index did not" half is structurally unreachable

**File:** `wiki/tools/kme_pillars.py:2350-2366`

**Issue:** The 02-03 summary describes the shadow guard as also refusing when the champion selects "nothing the index
did not select". That half cannot fire:
- `_shadow_check` compares `proc - skip` with `index_selected - skip`.
- `proc` can only hold sessions the tier read, which is `read_set = index_selected | stale | no_first_ts`.
- Sessions outside the read set are registered with no lines. With a window active they are dropped by `kept == 0`.
- So `only_c` is empty by construction, apart from the windowless, project-name-only `is_kme` case.

An index omission is caught only by the in-process population being exact against the frozen fields. That check is
sound, but the guard text claims more than the code can observe.

**Fix:** Reword the docstring and summary so that the population check is named as the omission guard. Otherwise a
reader may believe two independent checks cover omissions.

### IN-05: certificate fields that are written but never verified, and selection-scope code outside the parser digest

**File:** `wiki/tools/kme_pillars.py:2431-2435` (`index.path`, `selected.digest`), `1914` (`SELECTION_NAMES`)

**Issue:**
- The certificate records `index.path` and `selected.digest`, but `_check_certificate` checks neither. A certificate
  issued against one index DB is accepted for any other `--index-db`. Per-run EXACT, watermark and shadow checks
  re-derive the selection, so this is not unsafe, but both fields read as bindings and are not.
- `SELECTION_NAMES` covers `population` / `make_keep` but not `_scope_dirs` / `scan`. Those two decide which project
  dirs (and so which sessions) enter the population. A change to them keeps old certificates valid.

**Fix:** Either check `cert["index"]["path"] == realpath(index_db)` (refusing with `certificate`), or drop the field
or rename it `informational_index_path`. Add `_scope_dirs` and `scan` to `SELECTION_NAMES`, and extend
`g_metric_coverage`'s closure roots to include them.

---

_Reviewed: 2026-10-07_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
