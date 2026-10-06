---
phase: 01-usage-index-v5-substrate
plan: 03
subsystem: usage_index
tags: [usage-index, schema-v5, effective-timestamps, cwd, kme-pattern, user-hits, attribution, mixed-sessions, mutation-drill]
requires: [01-02]
provides:
  - "effective timestamp per v5 row (own, else last seen in the file, else NULL -> files.first_ts at query time); files.first_ts/last_ts persisted across passes; call_files.ts follows the rule"
  - "file_cwds: each distinct recorded cwd with first_off and first_ts, from the single read pass"
  - "PATTERN_SOURCES / _load_patterns: patterns registry loaded from wiki/tools/kme_token_audit.py KME_RE (never copied); meta pattern_set, files.pat_ver, refresh key pattern_error"
  - "tool_events.pat_hits (champion serialization) and user_hits (champion human-text guards)"
  - "_attribute / attribution(): file_attribution (kind project|workstream|bucket, role home|touched) from a registry DISCOVERED from launch cwds; mixed sessions allowed; order independent; recompute opens nothing; meta attr_registry, attr_version (ATTR_VERSION = 1)"
affects: [01-04, 01-05, 01-06]
tech-stack:
  added: []
  patterns: ["pattern compiled object read off the champion's module at ingest", "attribution as a pure function of stored rows with a registry-hash recompute trigger", "in-process and source-text mutants driven from the gate file"]
key-files:
  created: []
  modified:
    - tools/usage_index.py
    - tools/test_usage_index_v5.py
key-decisions:
  - "spawns.result_head (v3 column, 200 chars of a spawn result): KEPT as is. Not dropped (v4 data), not widened, no new treatment: it is a bounded pre-existing v3/v4 field read by the spawn-outcome consumers. Pinned by V-UX5-RESULT-HEAD-BOUND (a 5000-char result stores exactly RESULT_HEAD=200 chars). Every NEW v5 table keeps hashes, sizes, normalized paths and counts only (V-UX5-NO-RAW-TEXT from 01-01)."
  - "A pattern-source failure keeps refresh status OK (the burn alarm must not become MONITOR_FAILURE because a classifier input is missing) and is typed instead: pat_ver NULL on the files of that pass, pattern_error in the refresh result and meta last_refresh_status; hits are never written as zero."
  - "files.pat_ver is the pattern_set the file's rows were ALL measured under. A grown file whose earlier rows were measured under another set (or none) while the pass uses a different one gets NULL (mixed) instead of re-tagging itself; plan 04 refuses a verdict when pat_ver != meta pattern_set."
  - "The <unattributed> bucket is stored as kind 'bucket' (name <unattributed>, role touched), not kind 'project': it is counted and visible but can never be read as a project. attribution() returns it as a separate 'unattributed' count."
  - "Filesystem roots ('/', 'C:/', '//') are not registered as project roots (a session launched at a drive root would otherwise own every absolute path)."
  - "A file with v5_from NULL (legacy, never re-read) gets NO file_attribution rows: its attribution is unknown, not zero."
  - "first_ts is set only for a file read from offset 0 (a legacy file that grows keeps NULL first_ts: the appended bytes do not hold the file's first timestamp)."
status: complete
plan_head_before: 34863cb13512992ec537ad80cdb756e7acd1e771
commits: 2
actuals:
  tokens: 14000
  tasks: 2
  commits: 2
duration: single session
completed: 2026-10-06
---

# Phase 1 Plan 03: usage_index v5 behavioural half Summary

The index now holds, per event and per instant, every feature the frozen KME-L classifier reads (effective timestamps, recorded cwds, `KME_RE` hits per tool event and per qualifying human text, all from the champion's own regex), and any session's projects and workstreams are answerable from stored rows alone: mixed sessions attributed to every project they touch, from a registry discovered from launch cwds, independent of ingest order, recomputed without opening a transcript.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Effective timestamps, recorded cwds, registered patterns and classifier features in the single pass | 20f04c9b |
| 2 | Project and workstream attribution, mixed allowed, from a discovered registry | 40badfd9 |

## Gate outputs

- `python3 tools/test_usage_index_v5.py` -> `USAGE_INDEX_V5_PASS=56/56  threshold=56/56`
- `python3 tools/test_usage_index_v5.py --drill` -> control 56/56, M1-M14 all KILLED, clean rerun 56/56, `DRILL killed=14/14` (no SURVIVED, no INVALID)
- `python3 tools/test_usage_index.py` -> `USAGE_INDEX_PASS=22/22  threshold=22/22`
- `python3 tools/test_usage_index_identity.py` -> `USAGE_INDEX_IDENTITY_PASS=11/11  threshold=11/11`
- `python3 tools/test_store_identity_consumers.py` -> `STORE_IDENTITY_CONSUMERS_PASS=12/12  threshold=12/12`
- `python3 tools/test_spawn_outcomes.py` -> `SPAWN_OUTCOMES_PASS=24/24`
- Consumers unchanged against 01-BASELINE: fanout 17/17, root_progress 11/11, spawn_policy_v2 26/26, async 12/12, goal_journey 7/7, execution_shape 14/14, displacement 16/16, kme_pillars 89/89; estate_shadow 10/11 is the pre-existing V-SHADOW-NESTED-PROJECT red.
- `grep -n PATTERN_SOURCES tools/usage_index.py` shows `wiki/tools/kme_token_audit.py`; `grep -c KobiMapEngine tools/usage_index.py` = 0; `grep -n ATTR_VERSION` shows the constant (line 806) and its meta write.

## Mutants registered

| Mutant | Kills |
|---|---|
| M10 timestamp inheritance dropped (source text: fallback to last_ts -> None) | V-UX5-TS-INHERIT |
| M11 pattern source drifts to another compiled regex (in-process patch of PATTERN_SOURCES) | V-UX5-PATTERN-SOURCE |
| M12 human-text length guard removed (source text) | V-UX5-USER-HITS-FILTER |
| M13 touched attribution rows dropped (in-process patch of `_attribution_rows`) | V-UX5-MIXED-BOTH |
| M14 segment prefix replaced by plain string prefix (in-process patch of `_under`) | V-UX5-SEGMENT-PREFIX |

## Gates added (all with a paired control that can return the other answer)

Task 1: V-UX5-TS-INHERIT (+ -ACROSS-PASSES), -CWD, -PATTERN-SOURCE, -PAT-HITS (+ -SERIALIZATION: `KME` + a non-ASCII letter differs between ensure_ascii True/False, the stored value follows the champion's False), -USER-HITS-FILTER (four raw-text-hitting controls produce no row) (+ -LIST-SHAPE), -RESULT-TEXT-PARITY (vs the champion's `text_of` on nine shapes), -PATTERN-UNAVAILABLE (+ -CONTROL), -PATTERN-DRIFT-NOT-RETAGGED, -RESULT-HEAD-BOUND.
Task 2: V-UX5-MIXED-BOTH, -MIXED-CONTROL, -UNATTRIBUTED-BUCKET (also pins an upper-cased Windows path resolving under its root), -NESTED-ROOT-STAYS-HOME (control: the same path from another root goes to the nested root, the longest match), -SEGMENT-PREFIX, -WORKSTREAM, -ATTR-ORDER-INDEPENDENT (control: the half-built states differ from the final and from each other), -ATTR-NO-OPEN (+ -CONTROL: the same spy sees the new store's file opened).

## Deviations from Plan

**1. [Plan wording] Gates written before the implementation, but not all run red first**
- Task 1 gates were run red first (37/46 with the 9 behaviour gates failing/crashing). Task 2 gates were written before `_attribute` existed but the first run was after the implementation; each is shown able to fail by mutants M13/M14 and, for order independence and no-open, by the half-built-state control and the spy control.

**2. [Rule 2 - Missing critical] pat_ver mixed-file semantics, pattern_error as typed absence, pattern drift gate**
- A grown file measured under two different pattern sets (or one without patterns) would otherwise claim one set. It now gets NULL (V-UX5-PATTERN-DRIFT-NOT-RETAGGED). Limitation: a file ingested while the pattern source was unavailable keeps pat_ver NULL until it is re-indexed (a rebuild is a plan 04/05 concern; the source is a tracked repo file so the failure is deterministic, not transient).

**3. [Plan wording] extra attribution rules** the plan left open: filesystem roots not registered, kind 'bucket' for `<unattributed>`, no rows for never-re-read legacy files (all listed under key-decisions).

**4. Commit hook:** two-file commits; no code-reviewer receipt was requested; no `--no-verify`. `vault/progress.md` (hook output) never committed. The pin command and git calls were split into plain separate commands because the sandbox refused compound ones.

## Known notes / not stubs

- Relative tool paths on a resumed pass before the first cwd line of that pass are kept relative (the running cwd is not persisted across passes) and therefore land in `<unattributed>`. Absolute paths (the normal case) are unaffected.
- `files.pat_ver` NULL after a pattern drift or an unavailable source is intentional (see decisions); plan 04 must treat NULL or != meta `pattern_set` as UNMEASURED.
- The attribution recompute on a registry change walks every file's stored rows (no transcript is opened); its wall cost on the full corpus belongs to plan 05's measurement.
- Legacy v4-migrated rows keep NULL head_sha/tail_sha/content_id and (new) NULL first_ts/pat_ver and no attribution rows until the file grows, typed unknown.
- `requirements mark-complete AO-03` reported not-found in 01-01; not fought.

## Threat Flags

None beyond the plan's register. T-01-11 (traversal strings: `_norm_path` string-only, V-UX5-ATTR-NO-OPEN spies opens), T-01-12 (fixed relative pattern source under `_PP_ROOT`, accepted), T-01-13 (pat_ver + meta pattern_set + V-UX5-PATTERN-SOURCE/-DRIFT with controls), T-01-14 (only per-pattern counts stored for user text, V-UX5-NO-RAW-TEXT) mitigated and gated.

## Blockers for the next plan

None. Handoff for plan 04: `files.first_ts` resolves an event with NULL `tool_events.ts` (`coalesce(e.ts, f.first_ts)`); `pat_hits` / `user_hits.pat_hits` are JSON `{"kme": n}` (NULL / no row when zero); a file is classifier-measured only when `files.pat_ver == meta pattern_set` and `v5_from == 0`; `attribution(con, store, session_key)` gives `{projects, workstreams, unattributed, mixed}`; the `<unattributed>` bucket is kind 'bucket'. The user-text guard constant is `USER_TEXT_MAX`; the pattern loader is `_load_patterns(con)`.

## Self-Check: PASSED

Files exist: tools/usage_index.py, tools/test_usage_index_v5.py. Commits 20f04c9b and 40badfd9 present on mission/autonomous-optimization-gen2; `commits: 2` measured from the persisted ledger (`rev-list --count 34863cb1..HEAD` before this docs commit).
