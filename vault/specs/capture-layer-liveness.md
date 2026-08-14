---
title: Capture-layer liveness — make automatic failure documentation actually record
date: 2026-08-14
tier: T2
status: DELIVERED 2026-08-14 — Owner approved full scope ("Arreglo + puerta + los otros 3 sumideros"). All acceptance gates observed green ×3 runs.
covers: [ceps, ceps_capture, bug_hunter_ceps_bridge, mistake_ingest, bug_hunter_learning, never_again, capture_liveness, error_documentation]
origin: Owner directive 2026-08-14 "hay que reforzar el tema de documentar automáticamente todo tipo de fallo, error, bug"
---

# Spec — capture-layer liveness

## Objective

Every failure the session observes lands in a durable corpus, and a gate fails
when producers fire but records do not land.

## Problem, measured (2026-08-14)

The automatic failure-documentation layer is fully wired in `settings.json` and
has recorded **nothing organic in ~80 days**.

| Sink | Last organic write | Days silent | Producer state |
|---|---|---|---|
| `vault/ceps/events.jsonl` | 2026-05-26 (seed only, 9 rows) | 80 | hook fired **63×** |
| `vault/knowledge_base/errors.md` | 2026-05-23 | 83 | hook wired |
| `knowledge_vault/02_Doctrine/LEARNINGS/` | never — **directory absent** | ∞ | hook wired |
| `vault/osa/never_again_log.jsonl` | 2026-06-03 | 72 | manual only |

`vault/pp_agents/throttle/pp-ceps-analyst_bash-error.json` records
`fire_count: 63`, `last_fire: 2026-08-10`. **63 fires, 0 records.**

### Producer audit — the four silences are not one failure

Reading each producer's trigger corrected the framing. Three of the four
sinks are silent **by design**; only one is broken, and it is the only
automatic observer the repo has.

| Producer | Trigger | Verdict |
|---|---|---|
| `bug-hunter-ceps-bridge` | any Bash failure output | **BROKEN** — D1 + D2 |
| `mistake-ingest` | a human editing `mistakes-registry.md` | **MANUAL** — a registry mirror, not an observer. Correct to be silent. |
| `bug-hunter-learning` | fail→pass on Bash test runners, InfinityOps holding only | **SCOPED** — a deliberate no-op outside that holding. |
| `never-again` | `pp-never-again` agent on Owner request | **MANUAL** — no automatic producer exists. |

So the true finding is sharper than "four dead sinks": **the repo has exactly
one automatic failure observer, it was discarding everything, and it only
watched the tool the doctrine forbids.** Treating the manual and scoped
producers as dead would make the gate cry wolf on every run until nobody
read it, so the gate classifies by trigger and exempts them by name.

## Defects

### D1 — producer/validator contract mismatch, silently swallowed

`hooks/bug-hunter-ceps-bridge.js:118` calls `record_error(..., scope='session')`.
`tools/ceps.py:296` validates `scope in ("project", "global")` → returns `None`.

Evidence: `~/.claude/logs/ceps.log` holds **60 lines** of
`record_error: invalid scope=session`. The diagnostic existed for 80 days and no
gate read it. Reproduced this session: `scope="project"` → dict,
`scope="session"` → `None`.

Two nested fail-open handlers hide it — the hook discards the subprocess
exception, and `record_error` returns `None` on any internal exception.
Fail-open is correct; **fail-silent is not**.

### D2 — capture surface is Bash-only on a Bash-forbidden host

The hook returns early unless `tool_name === 'Bash'`. Global `CLAUDE.md` mandates
the **PowerShell** tool for python/pytest/pip/git/npm and bans Bash for
FS mutation. The dominant execution surface is uninstrumented, and the single
most-documented failure class in `MEMORY.md` — the
`[Tool result missing due to internal error]` sentinel on Read/Edit/Write — has
no capture path at all.

### D3 — signatures too specific → recurrence never accrues

`_normalize_root_cause` (ceps.py:145) lowercases, strips punctuation, collapses
whitespace. It does **not** strip the variable tokens that make two sightings of
one mechanism look distinct: absolute paths, line numbers, hex ids, pids,
timestamps, ports. So `pattern_signature` is near-unique per occurrence →
`occurrences` stays 1 → `compute_confidence` stays 0.3 → `promote_to_global`
(≥2 projects) and the cascade map (≥2 co-occurrences) can never fire.

This was already observed on 2026-05-29 and filed in `never_again_log.jsonl` as
benign bootstrap ("cascade map size grows naturally over sessions"). It was
never re-measured. 80 days later the count is unchanged.

### D4 — no liveness gate on the capture layer itself

Nothing measures whether the error corpus grew. A dead pipeline and a clean
session are indistinguishable. This is the systemic defect: the layer whose job
is to notice failures could not notice its own.

## Scope

**In**
- `hooks/bug-hunter-ceps-bridge.js` — scope arg, tool surface, category routing
- `tools/ceps.py` — `_normalize_root_cause`, rejection ledger
- `tools/capture_liveness.py` — NEW gate
- `vault/ceps/rejections.jsonl` — NEW durable rejection ledger
- `tools/verify_spp.py` — register the gate row

**Out**
- Rewriting CEPS storage, FTS5 schema, or the taxonomy
- `learning-sentinel.js` / compound-learnings (separate lane, separate spec)
- Any new corpus, dataset family, or institutional system (HR-NOVELTY-001)
- Retroactively reconstructing the 80 lost days

## Design

1. **D1** — hook passes `scope='project'`. `record_error` appends every rejection
   to `vault/ceps/rejections.jsonl` (`{ts, reason, category, subsystem, caller}`)
   before returning `None`. Fail-open keeps the user path alive; the ledger keeps
   the loss visible.
2. **D2** — capture on `Bash` **and** `PowerShell`; add a `harness` category for
   the internal-error sentinel; route category by pattern
   (`Traceback|Error:` → `tooling`, `Permission denied` → `env`,
   `FAILED|assert` → `regression`, sentinel → `harness`) instead of the current
   hardcoded `'tooling'`.
3. **D3** — `_normalize_root_cause` additionally masks: absolute paths →
   `<path>`, `line \d+` → `line <n>`, `0x[0-9a-f]+` → `<hex>`, bare integers ≥3
   digits → `<n>`, ISO timestamps → `<ts>`. Existing 9 seeded ids are
   grandfathered; no re-hash migration.
4. **D4** — `tools/capture_liveness.py` compares, over a 7-day window, each
   producer's fire count against its sink's record count and **exits 1** when
   `fires > 0 and records == 0`. Absolute divergence, never a ratio
   (`feedback_never_gate_on_a_ratio`). Registered in `verify_spp` as
   `capture-liveness`.

## Acceptance

- `V-CAPTURE-01` — a forced Bash error produces a **new line** in
  `events.jsonl` within the same turn (observed, not inferred).
- `V-CAPTURE-02` — a forced PowerShell error produces a new line.
- `V-CAPTURE-03` — the same mechanism seen twice with different paths/line
  numbers yields **one** `pattern_signature` with `occurrences == 2`.
- `V-CAPTURE-04` — a deliberately invalid `record_error` call appends to
  `rejections.jsonl` and returns `None`.
- `V-CAPTURE-05` — `python tools/capture_liveness.py` exits **1** against the
  pre-fix state (63 fires / 0 records) and **0** after.
- `python tools/verify_spp.py` stays green.

## D5 — found during the build, not in the original spec

The throttle check ran **before** `record_error`. Its purpose is to spare the
Owner a repeated advisory, but placed ahead of the recorder it also dropped the
event. A collection gate sitting in front of the collector discards the very
data it exists to keep — the same shape as
`feedback_collection_gate_drops_live_pane`, where an escape hatch placed after
a filter was unreachable. Capture now happens first; the throttle governs only
the advisory.

## Evidence (observed 2026-08-14, not inferred)

`python tools/test_capture_liveness.py` → **13/13**, three consecutive runs,
each ending `PASS V-CAPTURE-08: corpus restored byte-identical`.

| Gate | Observed |
|---|---|
| V-CAPTURE-01 | Bash traceback → `tooling/bash:python` recorded |
| V-CAPTURE-02 | PowerShell pytest failure → `regression/powershell:python.exe` |
| V-CAPTURE-03 | 3 mechanism pairs converged to one signature each |
| V-CAPTURE-03b | unrelated mechanisms stayed distinct (no over-masking) |
| V-CAPTURE-04 | invalid call → `None` **and** a rejection-ledger row |
| V-CAPTURE-05 | replayed 63-fires/0-records → `FIRES-WITHOUT-RECORDS`, exit 1 |
| V-CAPTURE-05c | unwired producer → `UNWIRED`, exit 1 (zero fires cannot pass) |
| V-CAPTURE-06 | harness sentinel on `Read` → `integration/harness:read` |
| V-CAPTURE-07 | clean `git status` output recorded nothing |

Regression: `test_ceps_edge_cases` 6/6, `test_ceps_closed_loop` 10/10,
`test_ceps_full_cycle` PASS — the signature change broke no existing suite.
`verify_spp --row capture-gates` and `--row capture-liveness` both STRICT PASS.

## Follow-up, not done here

- The sealed rule belongs in `vault/knowledge_base/ukdl-universal.md`, which
  currently carries another pane's uncommitted work; appending would package
  their changes under this commit. To be sealed once that tree is clean.
- `never-again` has no automatic producer. Giving it one is a separate spec —
  its entries are Owner-authored judgements, not observations, and
  auto-generating them would dilute the corpus.

## Rollback

Each item is one file. Revert order D4 → D3 → D2 → D1; the gate is additive and
removing it restores current behaviour exactly.
