# Phase 1: Usage truth plane - Research

**Researched:** 2026-10-10
**Domain:** Deterministic token/spend measurement from Claude Code transcripts (Python stdlib, zero model calls), mission-hold display surfaces, provider quota (429) detection, sourced API price table
**Confidence:** HIGH (every number below was measured this session on the real transcripts; the only MEDIUM item is the price page, which is a first-party page fetched today)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None. CONTEXT.md has no locked decisions: "All implementation choices are at Claude's discretion -- discuss phase was skipped per user setting."

### Claude's Discretion
"All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions. Extend `tools/mission_spend.py` / `tools/usage_index.py` (no new owner). Gate: `tools/test_evc_usage_truth.py`."

### Deferred Ideas (OUT OF SCOPE)
"None — discuss phase skipped."

(Out of Phase 1 by ROADMAP ordering, not by CONTEXT: JS session-budget-guard undercount = Phase 5; estimator clamp = Phase 3; 24 h process TTL = Phase 6; live landing = Phase 9.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVC-01 | Live usage truth with freshness watermark; stale spend never shown as current; subagents included | Canonical dedupe rule (last copy per (message.id, requestId), cross-file max) reproduces all three baselines to <0.02 %; single statement renderer for 5 hold-echo surfaces; liveness injection |
| EVC-02 | Three economies: processed, API-equivalent (sourced prices, else UNKNOWN), cognitive composition (Phases 1, 2) | Phase 1 owns the first two: per-category token split + per-category USD from a dated, sourced price file; cognitive composition is Phase 2 |
| EVC-03 | Quota awareness (429 / weekly limit, reset horizon) | Real 429 row shape captured verbatim (structured `quotaLimits.resetsAt` epoch, `apiErrorStatus` 429); single-pass extraction via `calls_from(on_line=...)` |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Directives extracted from the global `~/.claude/CLAUDE.md`, `C:\Users\User\CLAUDE.md` and the worktree `CLAUDE.md`; research below does not contradict any of them.

- **Reality Contract:** zero placeholders, mocks, stub returns or empty `except:` in shipped code. Every new function is wired end to end this phase (renderer wired into all echo surfaces, quota extraction wired into the reader).
- **Liveness Standard:** a new module must be reachable from a hook/command/agent/tool or declared in `vault/liveness/reachability_registry.json`. Phase 1 adds NO new module (extend `mission_spend.py` / `usage_index.py`), so the only new file is the gate `tools/test_evc_usage_truth.py` (a tool-invoked gate, same class as `tools/test_mission_spend.py`).
- **HR-PREMISE-001:** every file/function named in a plan must be verified in this repo; this document cites line numbers read this session. Planner: re-verify with `assert_premises` for anything added later.
- **Gate convention (PP testing rules):** AAA, `V-<DOMAIN>-<NAME>` gate names, final `*_PASS=n/m` line, paired controls (a refusal needs a control in which the instrument fires), exit 0/1. `INCONCLUSIVE` must never count as PASS (memory: `feedback_inconclusive_counted_as_pass`).
- **Windows host:** run Python via the PowerShell tool with `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'` and absolute paths; never `python ... | head` through Bash; git via `& 'C:\Program Files\Git\cmd\git.exe'`; Edit calls on the same file strictly sequential; Read/Grep batches of at most 4; an `Agent` dispatch alone in its batch.
- **Secrets:** HR-SECRET-002 - any text echoed from transcripts (429 reply text) goes through the redactor before logging; the 429 text is host-written but the rule is unconditional.
- **Shared tree:** the worktree is `evc/e2`; commit pathspec-scoped and verify `git log -1 --format='%s'` after committing. Attribution line for commits: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **No new owner, no new package:** CONTEXT.md discretion note.
- **ROADMAP operating constraints (Phase 1 budget):** deflation disposition SHRINK, 3M budget.

## Summary

The defect is two separate things that look like one. (1) **Wrong number:** `mission_spend._file_tokens` keeps the FIRST copy of each `message.id` in a transcript, but Claude Code writes a streamed message several times with growing `output_tokens` (fixture proof: `json: line("m1", "r1", 1, 5) + line("m1", "r1", 1, 50)          # streamed: 5 then 50`, `tools/test_usage_index.py:63`). First-copy therefore undercounts by 0.8 - 1.0 % on the three baseline missions. (2) **No freshness/liveness:** the cost-breaker freezes a number into prose (`owner_hold.reason`, `set_at`) at trip time and every later surface re-prints that prose as if current. On `m-cd548e5d2ada` the hold says 367,997,576 while the true final total is 371,042,313, the worker's last real call was 06:24:51Z, the host-written 429 reply is 06:25:34Z, and the hold was set 08:11:13Z. So the figure was not merely stale; it was also short, and nothing said whether a worker could still add to it.

The repository already contains the correct rule and the correct plumbing: `tis_observed.calls_from` (last copy per `(message.id, requestId)`, synthetic skipped, incremental, `on_line` hook that sees every parsed line) and `usage_index` (`calls` table with `ON CONFLICT(k) DO UPDATE ... max(...)` cross-file dedupe, dated pricing, `quota` table). Applying exactly that rule to a mission's attributed files reproduces the roadmap baselines to within 0.02 %: **371,042,313 / 58,401,057 / 245,821,099** against 371.0M / 58.4M / 245.8M. Phase 1 is therefore a consolidation: one reader (in `mission_spend.py`, built on `calls_from`), one statement renderer, one priced-category view (in `usage_index.py` plus a new dated price file), and one quota-event extractor riding the same pass. No package, no new module, no model call.

Two traps are load-bearing. **Do not change `_file_tokens` or `session_tokens`:** `tools/test_session_budget_guard.py:242` pins the JS guard to `ms._file_tokens` and `ms.session_tokens` (`V-SBG-REAL-PARITY`); that undercount is Phase 5's problem and Phase 1 must record it as named debt, not fix it half-way. And **the price file lacks the model the missions actually ran on:** `vault/pricing/anthropic_2026-09.json` has no `claude-sonnet-5-5` row, so it falls back to `claude-sonnet-5`, whose cache-read rate is $0.20/MTok while the official page lists Sonnet 5.5 at $0.10/MTok (cache hits are 0.05x input for 5.5 per the page footnote). 350.9M of the 371.0M tokens of the largest baseline are cache reads, so the fallback roughly doubles the dominant cost line for Sonnet. A new `anthropic_2026-10.json` carrying the exact row is part of this phase.

**Primary recommendation:** Add `usage_truth(...)` to `tools/mission_spend.py` on top of `tis_observed.calls_from` (last-copy per file, cross-file max-merge, `created_at` since-filter kept), make `processed_tokens` a thin int projection of it, add one pure `spend_statement()/format_statement()` pair used by every hold-echo surface, add `usage_index.price_breakdown()` plus `vault/pricing/anthropic_2026-10.json`, extract 429 events in the same pass, and prove it all in `tools/test_evc_usage_truth.py` with hermetic fixtures plus a typed-NOT_OBSERVED live-baseline gate.

## Architectural Responsibility Map

This is a local CLI/daemon estate (no browser/CDN tier). Tiers are mapped to the repo's actual layers.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Transcript parsing + dedupe + categories | Measurement library (`tools/tis_observed.py` `calls_from`) | `tools/usage_index.py` (SQLite index) | Already owns the reference identity rule; the index is the cached twin |
| Per-session / per-mission-tree aggregation, watermark, data age | Spend module (`tools/mission_spend.py`) | - | Context says extend it; owns `mission_sessions`, `_attributed`, `mission_dirs` (attribution) |
| Worker liveness verdict | Mission runtime (`tools/gsd_mission.py` `liveness`, `host_sessions`) | - | Only owner of host-session semantics; `mission_spend` must receive the verdict injected (lazy-import cycle already exists the other way) |
| "measured X as of T" statement text | Spend module (pure functions) | Surfaces call it | One renderer prevents five divergent echoes |
| Hold storage (structured spend snapshot) | Mission runtime (`set_owner_hold`, record JSON) | - | Hold record is the persistence boundary; prose stays only as legacy fallback |
| Hold/status display | `gsd_mission.plan_next`, `renewal_refusal`, status CLI, `mission_surface.classify` | `mission_steward` (reads only the flag) | These are the surfaces that echo the frozen prose |
| API-equivalent pricing | `tools/usage_index.py` (`price_for`, new `price_breakdown`) | `vault/pricing/anthropic_YYYY-MM.json` via `tools/pricing_source.py` | Existing sourced, dated price owner |
| Quota (429) event detection | Spend module reader (same pass, `on_line`) | `usage_index.quota` table (account-wide, global) | Per-worker attribution needs the attributed file set, which the spend module owns |
| Gate | `tools/test_evc_usage_truth.py` | - | Named in CONTEXT.md and ROADMAP criterion 5 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `re`, `os`, `pathlib`, `sqlite3`, `datetime`, `zoneinfo`) | CPython 3.12.10 | Everything in the phase | Whole `tools/` tree is stdlib-only; verified `Python 3.12.10` and that `zoneinfo.ZoneInfo('Europe/Madrid')` resolves on this host [VERIFIED: probe run this session] |
| `tools/tis_observed.py` | in-repo | Canonical per-file call identity (`calls_from`, `SYNTHETIC_MODEL`) | Already documented as "Same filters and identity as _calls_in"; reproduces the baselines |
| `tools/usage_index.py` | schema v4 | Dated pricing, `price_for`, `quota` table | Existing price/quota owner; CONTEXT.md names it |
| `tools/mission_spend.py` | in-repo | Attribution + reader home | CONTEXT.md names it |
| `tools/pricing_source.py` | in-repo | `current_pricing_path()` newest dated file | Existing resolver; "never hardcode a dated filename" |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tools/gsd_long_run.py` (`find_transcript`, `_tail_rows`, `last_assistant_text`) | in-repo | Locate/tail a worker transcript | Legacy quota text path (`quota_hold_from_transcript`); keep, do not duplicate |
| `tools/provider_breaker.py` | in-repo | Host-written `<synthetic>` reply classification | The park/relaunch decision stays there; Phase 1 only REPORTS quota events |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reader over transcript files (cached by size/mtime) | Reader over the `usage_index` `calls` table | The table dedupes globally by key and records only the first file for a shared key, so per-mission file attribution can mis-assign a shared message; also depends on index freshness (`STALE_AFTER_S` 7200). Use files; use the index only as a cross-check path in the gate |
| Parse the reset time from reply prose (`RESETS_RE` + `ZoneInfo`) | Read structured `quotaLimits.resetsAt` | Prose parsing needs a tz database and silently falls back to host-local time when the zone is unknown (`quota_reset_at`, `gsd_mission.py:3978-3980`). Use the epoch; keep prose only as fallback |

**Installation:** none. `pip`/`npm` untouched.

**Version verification:** no packages are added. Runtime verified: `Python 3.12.10`.

## Package Legitimacy Audit

No external packages are installed by this phase. Nothing to audit. **Packages removed due to [SLOP] verdict:** none. **Packages flagged [SUS]:** none. The planner must not introduce a dependency (e.g. a tz or pricing library); stdlib only.

## Architecture Patterns

### System Architecture Diagram

```
 transcripts (~/.claude/projects/<enc-cwd>[--claude-worktrees-*]/<sid>.jsonl
              and <sid>/subagents/agent-*.jsonl)
        |                                   record JSON (~/.claude/state/gsd-mission-<id>.json)
        |  mission_dirs() + _attributed()     |   owner.session_id, ledger-named workers, pending.bg_id
        v                                     v
  attributed file set  <------------  mission_sessions(rec)
        |
        |  ONE PASS per file (size/mtime cache):
        |  tis_observed.calls_from(path, on_line=collect_events)
        |     |-- calls: last copy per (message.id, requestId), synthetic skipped
        |     `-- on_line: rows with quotaLimits / isApiErrorMessage (429)  ---> quota events
        v
  cross-file merge by key (per-column max)  --> per-session + per-tree totals
        |        {input, cache_write, cache_read, output, processed, calls,
        |         last_call_ts, files_mtime_max, measured_at, by_model, subagent_tokens}
        |
        +--> usage_index.price_breakdown(by_model + cw TTL split, prices)  --> USD per category | UNKNOWN
        |
        +--> spend_statement(truth, worker_verdicts, now)  <--- liveness() per attributed worker
        |                                                        (verdict injected, host_sessions() once)
        v
  format_statement()  ->  "measured X as of T (age A); worker LIVE -> total current UNKNOWN, >= X"
        |
        +--> plan_next hold branch (gsd_mission.py:544) and settle reasons (:534, :543)
        +--> renewal_refusal (:2169)
        +--> mission_surface.classify (:35)
        +--> status CLI rows / --surface (:4389-4397)
        +--> hold CLI echo (:4346)
        `--> set_owner_hold(): stores structured snapshot, prose only as legacy fallback
```

### Recommended Project Structure
```
tools/
  mission_spend.py        # + usage_truth(), spend_statement(), format_statement(), quota_events()
                          #   processed_tokens() becomes int projection; _file_tokens/session_tokens UNTOUCHED
  usage_index.py          # + price_breakdown()  (per-category USD, None-on-unpriced)
  gsd_mission.py          # set_owner_hold(measured=...), plan_next/renewal_refusal/status use format_statement
  mission_surface.py      # classify() uses the same renderer
  test_evc_usage_truth.py # NEW gate (V-EVC-*)
vault/pricing/
  anthropic_2026-10.json  # NEW dated price file, retrieval 2026-10-10, Sonnet 5.5 exact row
```

### Pattern 1: Canonical call identity (reuse, do not reinvent)
**What:** last copy per `(message.id, requestId)` within a file; across files, per-column max; `<synthetic>` skipped; identity-less calls keyed by byte offset.
**When to use:** every spend figure.
**Example:**
```python
# Source: tools/tis_observed.py:162-170 (read this session)
if msg.get("model") == SYNTHETIC_MODEL:
    continue
key = (msg.get("id"), obj.get("requestId"))
if key == (None, None):
    key = ("off", start)
...
calls[key] = {"model": msg.get("model") or "", "usage": msg["usage"],
              "ts": obj.get("timestamp"), "key": key}
```
Cross-file merge to copy from the index [VERIFIED: tools/usage_index.py:475-478]: `"INSERT INTO calls(k,file,ts,model,...) VALUES(...) ON CONFLICT(k) DO UPDATE SET ts=excluded.ts, inp=max(inp,excluded.inp), cw=max(cw,excluded.cw), ..."`.

### Pattern 2: Inject the world, keep the function pure
`liveness(owner, sessions, pid_alive=lr._pid_alive)` (`gsd_mission.py:444`), `judge(rec, spent, fp)` (`mission_spend.py:219`), `_cost_breaker(rec, now, measure=None, fingerprint=None)` (`gsd_mission.py:1383`) all take their effects as parameters. `spend_statement(truth, verdicts, now)` must do the same: `mission_spend` must not import `gsd_mission` at module level (`mission_spend.lineage_members` already lazy-imports it the other way, `mission_spend.py:169`).

### Pattern 3: Statement semantics (closed set, no free prose)
Inputs: `truth` (processed, watermark), `verdicts` (one `(verdict, evidence)` per attributed worker), `now`.

| Worker verdicts | Printed form |
|-----------------|--------------|
| any `ALIVE` | `measured X as of T (age A); worker LIVE -> total current UNKNOWN, >= X` |
| any `BLOCKED` (waiting on a human) or `UNKNOWN`, none ALIVE | `measured X as of T (age A); worker liveness UNKNOWN -> total current UNKNOWN, >= X` (BLOCKED can resume; it is not a death) |
| all `DEAD` | `measured X as of T (age A); no live worker -> X is final as of last call L` |
| no attributable session / no transcript dir | `spend UNKNOWN (not measurable)` - never 0 |
| legacy hold with prose only | `recorded at <set_at> (age A): <prose>; not re-measured` |

Verdict constants are values, not names: `LIVE = "ALIVE"`, `DEAD = "DEAD"`, `UNKNOWN = "UNKNOWN"`, `WAITING_HUMAN = "BLOCKED"` [VERIFIED: tools/gsd_mission.py:88-91 `LIVE = "ALIVE"` / `DEAD = "DEAD"` / `UNKNOWN = "UNKNOWN"` / `WAITING_HUMAN = "BLOCKED"`]. A background worker the host does not list is `UNKNOWN`, never DEAD [VERIFIED: gsd_mission.py:481-482 `if owner.get("kind") == "background": return UNKNOWN, "background worker not listed by host (host owns its restarts)"`].

### Pattern 4: One pass, two products
`calls_from(path, offset, on_line)` calls `on_line(obj, start_offset)` for every parsed JSON object before the usage filter [VERIFIED: tis_observed.py:157-158]. Collect quota events there; do not re-read the file.

### Anti-Patterns to Avoid
- **Printing `owner_hold.reason` through an f-string** (5 sites, listed below). Every one is a frozen-figure leak; route all through the renderer, and add a source-scan gate that fails if a new `owner_hold.get('reason')` interpolation appears outside the renderer.
- **Fixing the number in `_file_tokens` in place.** Breaks `V-SBG-REAL-PARITY` and silently changes the JS guard contract (Phase 5).
- **Deleting a hold to "refresh" it.** The hold is the breaker's state; the renderer reads live data, it never mutates the record.
- **Treating "worker not listed" as dead.** Documented host auto-restart (`gsd_mission.py:455-459`).
- **Using `window()`'s cache-write TTL fallback silently.** Unsplit writes are priced at the 1h rate by design (`usage_index.py:564-566`); report `ttl_assumed` as an attribute instead of hiding it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-call dedupe identity | Another `seen` set keyed by `message.id` alone | `tis_observed.calls_from` + index-style max-merge | First-copy undercounts 0.8 - 1.0 % (measured); the index agrees with `calls_from` (pinned `V-UIX-PARSE-AGREES`) |
| Partial-line safety | Own line splitter | `calls_from` end-offset logic (`if not raw.endswith(b"\n"): break`) | A line still being written is never half-read (`V-UIX-PARTIAL-LINE`) |
| Reset time from reply prose | New regex + tz math | `quotaLimits.resetsAt` epoch; `gsd_mission.quota_reset_at` only as fallback | Structured, tz-free; the prose path has a documented silent local-time fallback |
| Price lookup / family fallback | New model-name matcher | `usage_index.price_for` (`exact` / `family:<id>` / `unpriced`) | Existing typed result; unpriced is counted, never 0 |
| Newest price file | Hardcoded filename | `pricing_source.current_pricing_path()` | Hardcoded `2026-05` hid a 3x Opus error for four months (module docstring) |
| Liveness | `os.kill`/pid probing | `gsd_mission.liveness(owner, sessions)` with one `host_sessions()` call per pass | Host owns restarts; `claude agents --json --all` is the source of truth |
| Hermetic test state | Writing to the real `~/.claude/state` | `GSD_LONG_RUN_STATE_DIR`, `GSD_LONG_RUN_PROJECTS_DIR`, `CPP_CLAUDE_EXE=__no_such_claude_in_tests__` as in `test_mission_spend.py:22-26` | Never launches a real worker |

**Key insight:** every primitive exists. The phase's value is making ONE composition authoritative and deleting the divergent echoes, not adding capability.

## Runtime State Inventory

Not a rename/refactor phase, but it changes how an existing persisted field is rendered, so the hold-record question needs an explicit answer.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Mission records `~/.claude/state/gsd-mission-<id>.json` hold `owner_hold = {"reason": <prose with frozen figure>, "set_at": <epoch>}`. Example: `m-cd548e5d2ada`, `set_at` 1791619873.887 (2026-10-10T08:11:13Z), reason carries `367,997,576`. No `measured` field exists | Code edit: `set_owner_hold(..., measured=)` stores a structured snapshot for NEW holds. No data migration: legacy holds render via the "recorded at ... not re-measured" branch |
| Live service config | None - no external service holds the string | None - verified: figure lives only in the record JSON and the ledger |
| OS-registered state | Supervisor sweep (5-minute pass) calls `plan_next`/`_cost_breaker`; it re-imports the changed code on its next pass; no task embeds the figure | None; sweep health is read through `sweep_health()` |
| Secrets/env vars | None involved | None |
| Build artifacts | None (pure Python, no egg-info) | None |

**Canonical question answered:** after the code is updated, the only thing still carrying the old frozen string is the existing hold record JSON files and their ledger rows; the renderer must handle them (legacy branch), and the ledger rows are history and are never rewritten.

## Common Pitfalls

### Pitfall 1: First-copy dedupe passes every existing test and is still wrong
**What goes wrong:** the reader reproduces `V-MSPEND-EXACT-SUM` (fixture duplicates are byte-identical) and undercounts real transcripts.
**Why it happens:** real streamed duplicates differ (5 then 50 output tokens); the repo fixture in `test_mission_spend.py:67-68` uses identical copies.
**How to avoid:** the gate fixture MUST contain a streamed pair with different usage (copy `test_usage_index.py:63`) and assert the LAST copy wins, with a control showing the first-copy rule gives the smaller number.
**Warning signs:** a new reader that matches `processed_tokens` exactly on real data - it should differ by 0.8 - 1.0 %.

### Pitfall 2: "Reproduces within 1 %" is satisfied by the BROKEN reader
**What goes wrong:** current `processed_tokens` returns 367,997,576 / 57,900,034 / 243,471,065 = -0.82 % / -0.86 % / -0.96 %, inside the 1 % band by a hair, so criterion 1 can be "passed" by doing nothing, and a 0.04 % regression would flip it.
**How to avoid:** the gate asserts the exact rule (±0.05 % on the live baselines, exact on fixtures), not just the 1 % band.

### Pitfall 3: Changing `_file_tokens` / `session_tokens` breaks the guard parity gate
**What goes wrong:** `tools/test_session_budget_guard.py:140-145` and `:242` pin JS == Python == `_file_tokens`.
**How to avoid:** leave both untouched; add a named-debt line (guard undercount, Phase 5) and a gate that asserts the divergence is the KNOWN streaming difference (new reader >= `_file_tokens`, equal when no duplicate differs).

### Pitfall 4: Data age is not the last call's age
**What goes wrong:** "age" computed from the last call timestamp makes a finished mission look stale forever, and a fresh read of a dead mission look old.
**How to avoid:** carry three separate times: `measured_at` (when the reader ran), `last_call_ts` (newest call in scope), `files_mtime_max` (newest transcript write). Statement prints `T = measured_at`, `A = now - measured_at`; `last_call_ts` is shown for DEAD.

### Pitfall 5: Cache keys must include `since`
`processed_tokens` caches `{size, mtime, since, tokens}` per file and checks `since` (`mission_spend.py:147`). The new per-file cache must store the per-key tuples, not just a sum, or the cross-file max-merge cannot be redone; keep the `since` guard, and keep the `created_at` filter (the `old` row in `test_mission_spend.py:71` must still be excluded).

### Pitfall 6: The 429 reply is `<synthetic>` with all-zero usage
The row is excluded from spend by design, so a reader that only walks usage rows will never see it. Quota detection must read it through `on_line`, keyed on `isApiErrorMessage`/`apiErrorStatus`/`quotaLimits`, not on usage.

### Pitfall 7: Quota is account-wide, workers are not
A weekly-limit 429 on one worker says every worker on that account is refused. Per-worker detection is what the reader can prove; "account blocked" is an inference. `launch-accounts.json` (`_record_launch_account`, `gsd_mission.py:4036`) records which account launched a worker; use it only to label, and report feasibility UNKNOWN unless measured.

### Pitfall 8: A new dated price file changes every consumer
`current_pricing_path()` picks the newest month. `tis_report.py`, `budget_monitor.py`, `verify_full_install.py` and `usage_index.load_prices` all resolve through it. The new file must carry every model row of `anthropic_2026-09.json` (`V-PRICESRC-OPUS47-NOT-OPUS4-RATE` and `V-PRICESRC-WRITE-MULTIPLIERS` run against the CURRENT file, `test_pricing_source.py:49-60`).

### Pitfall 9: Slow cold read
Cold read of the 29-file, 371 M mission took 9.1 s (3.9 s and 0.6 s for the other two). The supervisor pass runs every 5 minutes and the status CLI calls it per mission. Keep the size/mtime cache, and never call the reader inside a render loop.

## Code Examples

### 1. Reader skeleton (extend `mission_spend.py`)
```python
# Source: composition of tools/mission_spend.py:75-154 (attribution) and tools/tis_observed.py:124-171
# Verified by probe 2026-10-10: reproduces 371,042,313 / 58,401,057 / 245,821,099.
def usage_truth(rec, root=None, cache=None, sessions=None, now=None):
    root = root or projects_root()
    dirs = _mission_dirs_both_planes(rec, root)          # work_dir AND cwd, as processed_tokens does
    ids, prefixes = sessions if sessions is not None else mission_sessions(rec)
    if not dirs or (not ids and not prefixes):
        return None                                       # UNKNOWN, never zero
    since = _since_iso(rec)                               # created_at filter kept
    merged, quota, newest_mtime = {}, [], 0.0
    for d in dirs:
        for p in d.rglob("*.jsonl"):
            if not _attributed(p, d, ids, prefixes):
                continue
            per_file = _read_file_once(p, since, cache)   # calls_from(p, 0, on_line=collect) cached by (size, mtime, since)
            for key, tup, model, ts in per_file["calls"]:
                old = merged.get(key)
                merged[key] = (tup, model, ts) if old is None else (
                    tuple(max(a, b) for a, b in zip(old[0], tup)), old[1], max(old[2] or "", ts or ""))
            quota.extend(per_file["quota"])
            newest_mtime = max(newest_mtime, per_file["mtime"])
    ...
```

### 2. The real 429 row (what the extractor must recognise)
Captured verbatim from the `m-cd548e5d2ada` worker transcript, line at 2026-10-10T06:25:34.656Z [VERIFIED: probe run this session on `ec66dcff-213f-4945-a764-a24cd13c1f2b.jsonl`]:
```
type = 'assistant'          model = '<synthetic>'      isApiErrorMessage = True
error = 'rate_limit'        apiError = 'usage_limit_reached'      apiErrorStatus = 429
apiErrorParams = {'rate_limit_info': {'status': 'rejected', 'resetsAt': 1791856800, 'rateLimitType': 'seven_day',
                  'overageStatus': 'rejected', 'overageDisabledReason': 'org_level_disabled', 'isUsingOverage': False}}
quotaLimits = {'status': 'rejected', 'resetsAt': 1791856800, 'unifiedRateLimitFallbackAvailable': False,
               'rateLimitType': 'seven_day', 'overageStatus': 'rejected',
               'overageDisabledReason': 'org_level_disabled', 'isUsingOverage': False}
message text = "You've hit your weekly limit · resets Oct 13, 4am (Europe/Madrid)"
message.usage = all zeros
```
`resetsAt` 1791856800 = 2026-10-13T04:00:00+02:00 = 02:00:00Z [VERIFIED: zoneinfo decode this session], matching the prose. Existing index code already reads the same sibling field: `usage_index.py:367-371` (`if isinstance(o.get("quotaLimits"), dict): ... q.get("rateLimitType"), q.get("status"), _epoch(q.get("resetsAt")), q.get("overageDisabledReason")`).

Event record to emit per worker: `{file, session, ts, http_status, type, status, resets_at, overage_reason}`. Feasibility rule: `status == "rejected"` and `resets_at > now` -> `rejected until <iso> (measured at <ts>)`, current feasibility still UNKNOWN unless a real call with `ts` later than the event exists in the attributed set (then `superseded: a call succeeded after the rejection`); `resets_at <= now` -> `reset horizon passed; current quota UNKNOWN (not re-measured)`.

### 3. Per-category USD (extend `usage_index.py`)
```python
# Source: tools/usage_index.py:524-536 (price_for) and :557-569 (window arithmetic), per-category split
def price_breakdown(rows, prices):
    """rows: iterable of (model, inp, cw5, cw1, cw_unsplit, cr, out). Returns
    {"usd": {"input","cache_write","cache_read","output","total"} | None, "unpriced_calls": n,
     "unpriced_models": [...], "fallbacks": {...}, "ttl_assumed_tokens": n}.
    Any unpriced call makes the affected categories None (UNKNOWN) and total a lower bound field, never 0."""
```

### 4. Price file row to add (official page, fetched 2026-10-10)
Page rows [CITED: platform.claude.com/docs/en/about-claude/pricing, fetched 2026-10-10]: `| Claude Sonnet 5.5 | $2 / MTok | $2.50 / MTok | $4 / MTok | $0.10 / MTok<sup>2</sup> | $10 / MTok |`, footnote 2: "Cache hits and refreshes on Claude Opus 5.5 and Claude Sonnet 5.5 are priced at 0.05x the base input price." Existing Opus 5.5 row in the 2026-09 file (`input 4.0, output 20.0, cache_write_5m 5.0, cache_write_1h 8.0, cache_read 0.2`) agrees with the page row `| Claude Opus 5.5 | $4 / MTok | $5 / MTok | $8 / MTok | $0.20 / MTok | $20 / MTok |`.
```json
"claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_write_5m": 2.5, "cache_write_1h": 4.0, "cache_read": 0.1}
```
Set `source_url` "https://platform.claude.com/docs/en/about-claude/pricing" and `fetched_iso` "2026-10-10T00:00:00Z" in the new file.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| First copy per `message.id` per file (`_file_tokens`) | Last copy per `(message.id, requestId)`, cross-file max (`tis_observed`, `usage_index`) | Index v2 era (C1, 2026-10-02) | +0.8 - 1.0 % on the baselines; the breaker still uses the old rule |
| Frozen prose in `owner_hold.reason` | Structured snapshot + render-time statement | This phase | Removes the stale-as-current class |
| Family-fallback price for Sonnet 5.5 (`claude-sonnet-5`, cache read $0.20) | Exact row ($0.10) | Page lists it today; file dated 2026-09-27 lacks it | Halves the dominant Sonnet cost line |
| Reset time from prose + tz db | `quotaLimits.resetsAt` epoch | Field present on the 2026-10-10 row | No tz fallback hazard |

**Deprecated/outdated:** `vault/pricing/anthropic_2026-05.json` (3x Opus error; kept as history). Haiku 5.5 is priced by prompt size on the page ("for prompts up to 100,000 tokens" $0.10/$0.125/$0.20/$0.01/$0.50, "for prompts over 100,000 tokens" $0.50/$0.625/$1/$0.05/$2.50); the price schema has no tier, so leave `claude-haiku-5-5` ABSENT (UNKNOWN) rather than invent a flat rate.

## Measured Evidence (baselines, this session)

All three missions, rule M = last copy per `(id, requestId)` per file, per-column max across files, no cross-file duplicate keys found (0 on all three).

| Mission | Files (subagent) | Calls | First-copy `processed_tokens` | Rule M | Roadmap | Rule M vs roadmap | First-copy vs roadmap |
|---------|------------------|-------|-------------------------------|--------|---------|-------------------|----------------------|
| m-cd548e5d2ada (intent/order, owner `ec66dcff...`, RUNNING record, background) | 29 | 2,292 | 367,997,576 | 371,042,313 | 371.0M | +0.01 % | -0.81 % |
| m-5709490db84c (Clock A new, owner `e0cd1dbb...`, BLOCKED) | 11 | 387 | 57,900,034 | 58,401,057 | 58.4M | +0.00 % | -0.86 % |
| m-f24648f187c5 (Clock A old, owner `be97307b...`, HALTED) | 38 | 1,547 | 243,471,065 | 245,821,099 | 245.8M | +0.01 % | -0.95 % |

Category split (input / cache_write / cache_read / output) with Rule M [VERIFIED: probe 7]:
- m-cd548e5d2ada: 4,588 / 16,770,445 / 350,875,974 / 3,391,306; subagent tokens 339,041,879; by model: claude-sonnet-5-5 221,124,203, claude-opus-5-5 149,918,110.
- m-5709490db84c: 774 / 3,312,725 / 54,513,942 / 573,616; subagent 45,419,140; claude-sonnet-5-5 58,401,057.
- m-f24648f187c5: 3,094 / 14,205,782 / 228,941,739 / 2,670,484; subagent 203,059,504; claude-sonnet-5-5 245,821,099.

Subagent transcripts are 91 %, 78 % and 83 % of these totals - "subagents included" is not a footnote, it is most of the money. Last real call timestamps: intent/order 2026-10-10T06:24:51Z, Clock A new 2026-10-10T10:02:39Z, Clock A old 2026-10-10T00:40:01Z [VERIFIED: probe 2, earlier in this session].

## Hold-echo surfaces to route through the renderer

[VERIFIED by Grep of non-test tools this session]:
1. `tools/gsd_mission.py:544` - `return {"action": "none", "reason": f"owner hold: {hold.get('reason')}"}`
2. `tools/gsd_mission.py:533-534` and `:542-543` - settle reasons echo `(hold: {str(hold.get('reason'))[:200]})`
3. `tools/gsd_mission.py:2168-2169` - `renewal_refusal`: `return f"owner hold: {rec['owner_hold'].get('reason')}"`
4. `tools/mission_surface.py:35` - `return out(COLD, f"owner hold: {(rec['owner_hold'] or {}).get('reason')}")`
5. `tools/gsd_mission.py:4346` (`hold` CLI) and the status CLI rows (`:4389-4397`), which carry `plan_next`'s reason
Write side: `set_owner_hold` stores `reason=f"owner hold: {reason[:300]}"` and `owner_hold={"reason": reason[:1000], "set_at": now}` (`gsd_mission.py:1287-1288`); the breaker call site is `set_owner_hold(mid, verdict["trip"], now=now)` (`:1407`), and `judge` builds the prose with the figure (`mission_spend.py:227-228`). Only existing tests touching the text: `tools/test_gsd_mission_owner_hold.py` lines 116 and 169 (as `set_owner_hold` inputs, not output pins).
Not an echo: `mission_steward.py:226` and `gsd_mission.py:3531` read only the boolean.

Design: add `measured: dict | None` to `set_owner_hold` and store `owner_hold["measured"] = {processed, categories, measured_at, last_call_ts, workers}` when the caller (cost breaker) has it. `judge` keeps returning prose for the ledger/reason, but the displayed text comes from the renderer. Keep `plan_next` pure: it already takes `sessions`, so it can compute liveness; the renderer receives the verdicts as a parameter.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The first-copy undercount is caused by streamed rows that grow `output_tokens` (mechanism). The delta and the streamed-pair fixture are verified; that the real files' deltas are all in `output_tokens` was not separately measured | Summary, Pitfall 1 | Low: the rule works regardless; only the explanation would change |
| A2 | Switching `processed_tokens` to the new rule raises the breaker's measured spend by ~1 % (trips slightly earlier) and no existing gate pins the old value | Architecture (`processed_tokens` projection) | Medium: a gate or a live envelope tuned to the old number would shift. Planner should grep for numeric pins before switching; tests found stub `processed_tokens` (`test_gsd_mission_envelope.py:248`, `test_mission_lineage.py:57`, `test_mission_spend.py:159`), so they are unaffected |
| A3 | `claude agents --json --all` can be called once per pass in the status/supervise path without a new latency problem (existing code already does) | Pattern 3 | Low |
| A4 | Haiku 5.5 should stay unpriced rather than getting a flat rate | State of the Art | Low-medium: if Haiku 5.5 is used in the estate its USD reads UNKNOWN; owner may prefer a tiered schema |
| A5 | The worker of `m-cd548e5d2ada` was no longer running at hold time (08:11Z) because its last row is 06:25:34Z; host liveness was NOT queried this session, so its present liveness is UNKNOWN | Summary | None for the plan; stated so the statement is not over-claimed |
| A6 | The pricing page content is current as of 2026-10-10 and the missing `claude-sonnet-5-5` row in the 2026-09 file reflects a page change after 2026-09-27, not an omission; either way the exact row is on the page today | Standard Stack / Code Example 4 | Low |

## Open Questions

1. **Should `processed_tokens` (breaker) adopt the new rule now, or only the displays?**
   - Known: "one reader" is criterion 1; two numbers for one mission (367.99M in the hold, 371.04M in status) would violate its spirit. The breaker threshold shifts by ~1 %.
   - Unclear: whether any live envelope is calibrated to the old figure.
   - Recommendation: adopt now (single reader), record the ~1 % shift in the plan, and keep `_file_tokens`/`session_tokens` untouched for guard parity (Phase 5 debt, named).
2. **Where does the structured hold snapshot live for holds set by non-breaker callers** (`hold` CLI, `gsd_mission.py:2544`, `:3630`)?
   - Recommendation: `measured` is optional; absent -> legacy "not re-measured" branch. Do not measure inside `set_owner_hold` (adds a transcript scan to every park).
3. **Feasibility for quota beyond "UNKNOWN"?** ROADMAP says UNKNOWN unless measured. Measurable only by a successful later call in an attributed transcript. Recommendation: implement that single positive rule and nothing else.
4. **Haiku 5.5 tiered pricing** - add a `tiers` schema or leave unpriced? Recommendation: leave unpriced this phase (open for the Owner).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | yes | 3.12.10 | - |
| `zoneinfo` + tz data | Legacy prose reset fallback only | yes (`Europe/Madrid` resolves) | stdlib | Structured `resetsAt` epoch needs no tz |
| `claude` CLI (`claude agents --json --all`) | Liveness verdicts in the live path | not probed this session | - | `host_sessions()` returns None -> every owner UNKNOWN (typed, never "no sessions"); tests set `CPP_CLAUDE_EXE` to a nonexistent path |
| Real transcripts of the three baseline missions | Live baseline gate | yes on this host | - | Gate prints typed `NOT_OBSERVED` and does not count it as PASS |
| Network (price page) | Refreshing the price file | yes (fetched today) | - | Dated file already committed; gate reads the file, never the network |
| PowerShell tool | Windows run discipline | not available in this research run (Bash with the bridge-guard marker was used for python probes) | - | Planner: run gates via PowerShell with absolute interpreter path |

**Missing dependencies with no fallback:** none.

## Validation Architecture

(`.planning/config.json` has no `workflow.nyquist_validation` key, so it is treated as enabled; it contains only `hooks` thresholds and `workflow.skip_discuss`.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain-Python gate scripts (`check(gate, cond, ev)` printing `PASS`/`FAIL V-...`, final `*_PASS=n/m`, exit 0/1) - the repo convention, no pytest |
| Config file | none - each gate sets its own temp env (`test_mission_spend.py:22-26`) |
| Quick run command | `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_evc_usage_truth.py` |
| Full suite command | the quick command plus `tools\test_mission_spend.py`, `tools\test_usage_index.py`, `tools\test_pricing_source.py`, `tools\test_session_budget_guard.py`, `tools\test_gsd_mission_owner_hold.py`, `tools\test_gsd_mission_envelope.py`, `tools\test_mission_lineage.py` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVC-01 | Streamed duplicate: LAST copy wins; control: first-copy rule is smaller (`V-EVC-STREAM-LAST`, `-CONTROL`) | unit (fixture) | `python tools\test_evc_usage_truth.py` | Wave 0 (new) |
| EVC-01 | Subagent file counted; per-session vs per-tree totals differ by exactly the subagent tokens (`V-EVC-SUBAGENT-IN-TREE`) | unit | same | Wave 0 |
| EVC-01 | Synthetic row excluded; cross-file duplicate key merged by per-column max; identity-less call counted once | unit | same | Wave 0 |
| EVC-01 | Four categories + call count + `last_call_ts` + `measured_at` + `files_mtime_max` present and sum to processed (`V-EVC-CATEGORIES-SUM`) | unit | same | Wave 0 |
| EVC-01 | UNKNOWN is not zero: no dir / no attributable session -> None (`V-EVC-UNKNOWN-NOT-ZERO`, paired control) | unit | same | Wave 0 |
| EVC-01 | Index twin agrees: reader == `usage_index.window` totals on the same fixture (`V-EVC-EQ-INDEX`) | integration | same | Wave 0 |
| EVC-01 | Live baselines within 0.05 % of 371.0M / 58.4M / 245.8M (`V-EVC-BASELINE-*`); absent transcripts -> `NOT_OBSERVED`, excluded from the pass count | live (non-hermetic) | same | Wave 0 |
| EVC-01 | Statement: ALIVE -> text contains `worker LIVE -> total current UNKNOWN, >= X`; UNKNOWN verdict -> liveness-UNKNOWN text; all DEAD -> final text; stale branch driven RED then GREEN (`V-EVC-STATEMENT-*`) | unit | same | Wave 0 |
| EVC-01 | Legacy prose-only hold renders `recorded at ... not re-measured`, never as current (`V-EVC-LEGACY-HOLD`) | unit | same | Wave 0 |
| EVC-01 | All 5 echo surfaces use the renderer: static scan finds no `owner_hold...get('reason')` interpolation outside it, plus a behavioural call of each surface (`V-EVC-SURFACES-ONE-RENDERER`) | static + behavioural | same | Wave 0 |
| EVC-01 | Breaker path stores `owner_hold["measured"]` on trip and ledger text unchanged for old consumers (`V-EVC-HOLD-SNAPSHOT`) | integration (hermetic mission via `gm.create`) | same | Wave 0 |
| EVC-02 | Exact price row for `claude-sonnet-5-5` in the CURRENT file; `source_url` and `fetched_iso` present (`V-EVC-PRICE-SOURCED`) | unit | same | Wave 0 |
| EVC-02 | Per-category USD sums to total; unknown model -> category None and unpriced count, never 0; control with all priced (`V-EVC-PRICE-UNKNOWN`) | unit | same | Wave 0 |
| EVC-03 | Verbatim 429 row fixture -> event with `resets_at` epoch, worker attribution, `http_status` 429; control: ordinary row yields none; auth `<synthetic>` reply is not a quota event | unit | same | Wave 0 |
| EVC-03 | Feasibility: rejected+future reset -> `UNKNOWN` current; later successful call -> `superseded`; reset passed -> `UNKNOWN (not re-measured)` | unit | same | Wave 0 |
| Regression | Guard parity unchanged | existing gate | `python tools\test_session_budget_guard.py` | yes |
| Regression | Pricing source tests on the NEW current file | existing gate | `python tools\test_pricing_source.py` | yes |

### Sampling Rate
- **Per task commit:** `python tools\test_evc_usage_truth.py` (hermetic part runs in seconds; the live baselines are the only slow part, about 14 s cold).
- **Per wave merge:** quick command + `test_mission_spend.py`, `test_usage_index.py`, `test_pricing_source.py`, `test_gsd_mission_owner_hold.py`.
- **Phase gate:** full suite above green, then mutation drill, before `/gsd-verify-work`.

### Mutation drill (instrument can return the other answer)
Using `GSD_MISSION_DRILL_DIR` holding mutated copies of `mission_spend.py` / `gsd_mission.py` (convention at `test_mission_spend.py:8,28-29`; import `mission_spend` before `gsd_mission` as in lines 30-34): (a) revert to first-copy -> `V-EVC-STREAM-LAST` and the baseline gates must go red; (b) make the renderer print the bare figure -> `V-EVC-STATEMENT-ALIVE` red; (c) make an unpriced model cost 0 -> `V-EVC-PRICE-UNKNOWN` red; (d) drop the quota `on_line` collection -> the 429 gate red; (e) re-introduce the f-string at one echo site -> `V-EVC-SURFACES-ONE-RENDERER` red. Run mutants from an isolated copy, never against the live-loaded file (memory: `feedback_mutation_drill_on_live_loaded_file`).

### Wave 0 Gaps
- [ ] `tools/test_evc_usage_truth.py` - covers EVC-01/02/03 (new, hermetic temp dirs; copy `check()`/`_row()` helpers from `test_mission_spend.py:41-57`)
- [ ] `vault/pricing/anthropic_2026-10.json` - must exist before the price gate can be green; all rows of the 2026-09 file + `claude-sonnet-5-5`
- [ ] No framework install needed

## Security Domain

(`.planning/config.json` has no `security_enforcement` key -> enabled.)

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | - (no auth surface; the credential file is never read by this phase) |
| V3 Session Management | no | - (session ids are labels here, not credentials) |
| V4 Access Control | no | Local single-user estate |
| V5 Input Validation | yes | Transcripts are untrusted data: `json.loads` per line with `except ValueError: continue`, type-check every field (`isinstance(..., dict)`), cast token fields with `int(...)` guarded as in `usage_index`/`tis_observed`; session ids validated by `_SID_RE` (`^[A-Za-z0-9._-]{1,128}$`, `mission_spend.py:251`) before use in paths |
| V6 Cryptography | no | - |
| V12 Files/Resources | yes | Atomic write (`tmp` + `os.replace`) for any record or cache file written; never follow a transcript-supplied path |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Hostile content in a transcript line (huge line, wrong types, injection text in a reply) | Tampering / DoS | Per-line parse isolation, type checks, no `eval`, print only numbers and fixed templates; never echo reply text unredacted (HR-SECRET-002) |
| A spend figure presented as current when it is not | Repudiation / Spoofing of state | The renderer's closed statement set with watermark and age |
| Path traversal via session id in `<sid>/subagents/` attribution | Tampering | `_attributed` compares names, not joins untrusted strings; keep `_SID_RE` for any new path construction |
| Provider-quota text parsed with a regex on long input | DoS (ReDoS) | Prefer structured fields; keep `RESETS_RE` bounded input (`[:200]` already used by `quota_hold`) |

## Sources

### Primary (HIGH confidence)
- In-repo reads this session: `tools/mission_spend.py:1-340`, `tools/gsd_mission.py:88-91, 400-545, 1265-1424, 2160-2174, 3525-3533, 3950-4220, 4370-4414`, `tools/mission_surface.py:1-65`, `tools/tis_observed.py:120-250`, `tools/usage_index.py:51-86, 108-171, 362-371, 475-478, 515-600, 670-715`, `tools/pricing_source.py`, `tools/test_pricing_source.py:20-67`, `tools/test_usage_index.py:1-135`, `tools/test_mission_spend.py:22-91`, `tools/mission_steward.py:215-240`, `vault/pricing/anthropic_2026-09.json`.
- Measured: probes 2-7 on the three real missions and the `ec66dcff-...` worker transcript (scratch scripts in the user temp dir, not deliverables).
- `.planning/workstreams/evc/ROADMAP.md` Phase 1 (lines 88-99), `REQUIREMENTS.md` EVC-01..03, `01-CONTEXT.md`.

### Secondary (MEDIUM confidence)
- [CITED: https://platform.claude.com/docs/en/about-claude/pricing] fetched 2026-10-10 via WebFetch (first-party; model rows and footnotes quoted above). The page is the source named in the repo's own price file (`source_url`).

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependency; every primitive read in source
- Architecture: HIGH for the reader, renderer and pricing; MEDIUM for the exact `processed_tokens` migration (A2) and the hold-snapshot shape (Open Question 2)
- Pitfalls: HIGH - each was measured or read from a pinning test

**Research date:** 2026-10-10
**Valid until:** 2026-10-24 for the price table (fast-moving; re-fetch before the price file is cut); the code findings hold until `mission_spend.py`/`gsd_mission.py` change on `evc/main`.

## RESEARCH COMPLETE
