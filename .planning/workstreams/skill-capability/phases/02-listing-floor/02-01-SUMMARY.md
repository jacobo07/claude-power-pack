---
phase: 02-listing-floor
plan: 01
subsystem: listing-floor
tags: [listing-floor, measurement, verdict-gate, pillar-B]
requirements: [SC-B]
status: complete
commits: 3
plan_head_before: bbbdf3d9ee8f4a245ba8fac2cebf6561b15bb297
actuals:
  tokens: 14000
  tasks: 3
  commits: 3
---

# Phase 2 Plan 01: Listing floor verdict gate Summary

**Pillar B verdict gate recomputes the K4 listing-floor falsification from the committed probe rows and renders the D-LISTING measurement file the ledger will cite (verdict FALSIFIED, K4 startup tokens +2105, listing 205 chars under the cap).**

## Task 1 (tracer) -- commit cea69a71

- `tools/test_listing_floor_verdict.py` created: K4 arms selected by label, V-LF-SOURCES / V-LF-TOKENS /
  V-LF-CAP, `--jsonl`, `--write-evidence`.
- Evidence rendered to `vault/programs/skill-capability/evidence/B-listing-floor.md` (2567 chars, LF).
- Verbatim run: `ok V-LF-TOKENS ... (delta +2105)`, `ok V-LF-CAP ... gap 205 chars (0.68% of cap), band 300`,
  `LF_PASS=3/3`, rc=0. `command:` count 6, D-LISTING count 2, `<not recorded in the row>` count 4, no CRLF.
- Real CE contract one-off (`ce._check_evidence("B", measurement, ...)`) printed `[]`.
- Note: the plan-head ledger file for #3968 was created after the first commit (from `cea69a71^`), same value.

## Task 2 (red drills) -- commit 9552b49d

RED run (drill harness added before V-LF-DENOM-MATCH / V-LF-EVIDENCE-CURRENT existed), verbatim:

```
    drill clean: V-LF-SOURCES ok <-- WRONG          (clean case needs DENOM-MATCH ok, clause absent)
    drill tokens-lowered: V-LF-TOKENS FAIL
    drill chars-lowered: V-LF-CAP FAIL
    drill chars-at-band-edge: V-LF-CAP ok
    drill listing-unmeasured: V-LF-SOURCES INCONCLUSIVE
    drill duplicate-champion-row: V-LF-SOURCES INCONCLUSIVE
    drill challenger-tokens-changed: V-LF-DENOM-MATCH MISSING <-- WRONG
    drill evidence-digit-changed: V-LF-EVIDENCE-CURRENT MISSING <-- WRONG
rc=1
```

GREEN after adding the clauses: `V-LF-DRILLS ok 9 drills`, `LF_PASS=6/6`, rc=0 (clean, 7 verdict mutants incl.
band edge, evidence clean + one-digit mutant).

Subprocess red drills (files under /tmp, committed jsonl untouched, `git diff --quiet` rc 0):

```
floor (tokens 80000, chars 20000) rc=1
  ok   V-LF-SOURCES ...
  FAIL V-LF-TOKENS challenger startup_tokens 80000 vs champion 87739 (delta -7739): ...
  FAIL V-LF-CAP challenger listing chars 20000, cap 30000, gap 10000 chars (33.33% of cap), band 300: ...
  FAIL V-LF-DENOM-MATCH ...
  LF_PASS=1/4
tokens-only (85000) rc=1
  ok   V-LF-SOURCES ...
  FAIL V-LF-TOKENS challenger startup_tokens 85000 vs champion 87739 (delta -2739): ...
  ok   V-LF-CAP challenger listing chars 29795, cap 30000, gap 205 chars (0.68% of cap), band 300: still cap-bound
  FAIL V-LF-DENOM-MATCH ...
  LF_PASS=2/4
```

## Task 3 (provenance, pin, aperture, --json) -- commit 84a2d891ef599fa9ac077ad1674be820149f741e

Verbatim final line of the default run (host gex44, rc=0): `LF_PASS=11/11`.
Clauses: V-LF-SOURCES, TOKENS, CAP, DENOM-MATCH, C6 (134 overrides, 29991 -> 30002, commit d9072185),
ROWS-AT-K4 (K4 blob 4d1cfb83), ENTRIES-APERTURE (4 lines -> 3 keys, control 3 -> 3), BOUNDS (9000 / 4000,
noise +-1500), CITED, EVIDENCE-CURRENT, DRILLS (21 drills, all died by their own clause, append stability and
both A-1 wording branches pinned).
`--json` verdict: `FALSIFIED`; commits k4 `4d1cfb83d974...`, c6 `d9072185ca27...`.
Evidence file: K4 blob LF sha256 `74c5514c6049b3e74de9a679d37972762862f0c37964b8f4b0f57875318a7635`; every
`22 -> 50` / `87 -> 103` / `179 -> 32` line carries `not used by the verdict`; CE `_check_evidence` one-off
prints `[]` on the final render. The committed jsonl is untouched; `git show --name-only` of the commit lists
only the two plan files and nothing under `modules/` or `wiki/`.

## Deviations from Plan

- **[Rule 2 - gap] two extra clauses:** V-LF-BOUNDS and V-LF-CITED were added so the bound/noise parse and the
  located sources of the three non-derivable figures fail INCONCLUSIVE rather than silently defaulting
  (plan: "missing text gives INCONCLUSIVE, never a default"). They count in `LF_PASS`.
- **[Choice] wording boundary (A-1):** delta == noise (1500) is worded "no saving shown (delta inside noise)";
  only delta > noise says "rose by N, above the stated noise". A negative delta says "fell by N ... not a saving
  without a repeat". A-1 and A-2 applied; the Commands heading is the A-2 text.
- **[Process] commit shape:** three commits (one per task, each pathspec-limited to the two plan files) instead
  of one at Task 3, so a timeout could not cost the earlier tasks. `--drills` was added as a developer entrance.
- **[Process] plan-head ledger** (`gsd-plan-head-before-02-01`) was created after the first commit, from
  `cea69a71^`; the measured commit count is 3.
- `FRESH_SESSIONS_THIS_PHASE = 0` is a declared constant (a statement about this phase, D-02), not a measurement.

## Known Stubs

None.

## Threat Flags

None. No network, auth or schema surface; the script reads committed files and runs git read-only.

## Commits

- cea69a71 feat(02-01): B -- listing floor verdict tracer, jsonl to rendered D-LISTING measurement
- 9552b49d feat(02-01): B -- listing floor gate red drills, denominator match, stale-evidence check
- 84a2d891 feat(02-01): B -- listing floor provenance sections, K4 row pin, entries aperture, --json

## Self-Check: PASSED

Files exist (script, evidence); the three commit hashes resolve; the default run is 11/11.

