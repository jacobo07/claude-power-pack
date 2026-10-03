---
phase: 01-card-precision
plan: 01
subsystem: hooks/doctrine-card
tags: [doctrine-card, concurrent-writers, provenance, replay-gate]
requires: []
provides:
  - "mtime-window provenance in the commit card (reason mtime-in-own-shell-window, ledger field unknown_reasons)"
  - "pillar A replay gate tools/test_card_precision.py (SCA_PASS=27/27 on gex44)"
affects: [hooks/doctrine_cards.js]
tech-stack:
  added: []
  patterns: ["real card as child process + real scratch git repos + transcripts rebuilt from real tool-call windows", "mutant pole by body replacement of one named function"]
key-files:
  created:
    - tools/test_card_precision.py
    - vault/programs/skill-capability/card_evidence_pack.json
    - vault/programs/skill-capability/card_replay_spec.json
  modified:
    - hooks/doctrine_cards.js
    - hooks/tests/test-doctrine-cards.js
decisions:
  - "Window rule lives in one declaration (ownShellWindowHit) so the gate's mutant replaces exactly that body"
  - "Only 3a05f288 is a measured mtime; the other four replays are placed inside the writer window and labelled placed in spec and gate output"
  - "The 6th deny (4615e1d1) is reported beside D-CARD with class rollover-predecessor-lines, not folded into the /5 counts"
requirements: [SC-A]
metrics:
  duration: "about 12 min wall clock (start not captured; estimated from first scratch file at 16:29Z host clock)"
  completed: 2026-10-03
status: complete
actuals:
  tokens: 8743    # chars/4 over the authored diff; the verbatim 265049-byte pack copy (about 66k) is excluded
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count f1e80a0e..HEAD at SUMMARY write
plan_head_before: f1e80a0e0ec82001cc9fbe9b6914e3428d6cb127
---

# Phase 1 Plan 01: Card precision Summary

Mtime-window provenance in the commit card: a foreign-hunk file whose mtime lies inside one of this session's shell tool-call windows (1 s slack) and after its last own Edit/Write is classed unknown, and all 5 frozen D-CARD false denies replay as allowed through the real card while a pre-session hunk and arm C stay denied.

## Observed gate output (host kobicraft-gex44, node 18, python3, git 2.43; GEX44 is not the laptop's live install)

`python3 tools/test_card_precision.py` -> rc 0, `SCA_PASS=27/27`. Key lines, verbatim:

```
ok   V-SCA-FIXTURE-SHA: sha256=dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05
ok   V-SCA-SPEC-MEASURED-ONLY-3a05f288: measured=['3a05f288'] placed=['300ac3a1', '4a7ee8bc', '5b36b02f-1', '5b36b02f-2']
ok   V-SCA-SPEC-WRITER-IDS-REAL: every writer id and window equals the pack's call
ok   V-SCA-REPLAY-ALLOWED-3a05f288: mtime=measured decision=unknown denied=False reasons={...census.json: 'mtime-in-own-shell-window'}
ok   V-SCA-MUTANT-APPLIED: declarations=1 differs=True
ok   V-SCA-6TH-DENY-STAYS-DENIED-4615e1d1: mtime=placed denied=True decision=deny-card class=rollover-predecessor-lines
D-CARD frozen_denies=5 replayed_allowed=5/5 presession_denied=5/5 mutant_denied=5/5 | beside: 4615e1d1 (after freeze) denied=True class=rollover-predecessor-lines
ok   V-SCA-NODE-DOCTRINE-CARDS: rc=0 last='DOCTRINE_CARDS_PASS=30/30'
ok   V-SCA-ARM-C: doctrine-cards output contains PASS V-DC-JUDGED-COMMIT-NOT-A-WRITE
ok   V-SCA-NODE-DESTRUCTIVE-CARD: rc=0 last='DDC_PASS=15/15'
SCA_PASS=27/27
```

All 5 `V-SCA-REPLAY-ALLOWED-*`, 5 `V-SCA-PRESESSION-DENIED-*` and 5 `V-SCA-MUTANT-DENIES-*` printed `ok`. `node hooks/tests/test-doctrine-cards.js` -> `DOCTRINE_CARDS_PASS=30/30` (was 25/25 before this plan; cases 1-10 untouched, `git diff --stat` shows insertions only). `node hooks/tests/test-destructive-doctrine-card.js` -> `DDC_PASS=15/15`.

## Task log

### Task 1 (tracer) - commit 4e9cf4d4
- Window rule in `hooks/doctrine_cards.js`: `ownership()` returns `windows` and `lastOwnEdit` (tool_result rows are regex-prefiltered by known tool_use id before JSON.parse); `judge(diff, own, mtimeOf)` is pure when `mtimeOf` is absent; `main()` builds `mtimeOf` lazily (one bounded `rev-parse --show-toplevel`, only on the foreign-with-windows path); `ownership` exported; header states the aperture.
- Fixture copied with `cp`, LF sha256 `dacfdf5a...0c05`; credential scan over the 7 HR-SECRET CRITICAL shapes: 0 hits (every pattern 0).
- Tracer feedback gate: the plan's `<verify>` was re-run end to end before expanding (rc 0, SCA_PASS=4/4, DOCTRINE_CARDS_PASS=25/25), then Task 2.

### Task 2 - commit e32fd6d3
- 4 more replay entries, 4615e1d1 under `beside`, mutant pole, spec-integrity checks (writer ids and windows must equal the pack's own call; placed mtime must lie inside the writer window; measured only for 3a05f288).

### Task 3 (tdd) - commit 48c46acc
- Node case block 11: V-DC-MTIME-IN-SHELL-WINDOW, -PRE-SESSION, -BEFORE-LAST-OWN-EDIT, -WINDOW-OPEN, -SLACK (end+0.9 s unknown, end+1.5 s denied); gate runs both node suites and asserts arm C by name.
- Red observation: the cases were written, then run against a scratch copy of the card with `ownShellWindowHit`'s body replaced by `return false` (never the tracked file): `FAIL V-DC-MTIME-IN-SHELL-WINDOW: denied=true decision=deny-card reasons={}`, `FAIL V-DC-MTIME-SLACK: end+0.9s: deny-card; end+1.5s: deny-card`, `DOCTRINE_CARDS_PASS=28/30`. The other three new cases stay PASS against the mutant because they are the foreign-stays-foreign pole.

## Evidence-pack flags (read before quoting the replay as reproduction)

1. The pack truncates every tool-call `command` to 300 chars. Replay transcripts therefore carry truncated commands. The card's shell-write-target branch (`shellTargets`) saw only those 300 chars; the live denies were produced from the full text. The replays hold only on the assumption that the full commands did not name the file as a write target, which the live decisions (deny-card, not unknown) also imply.
2. 4a7ee8bc: the phase context names `ledger_write.py` as the writer. The pack's 300 chars for that call (14:23:51.562Z-14:24:04.907Z) show `WriteAllText` of `spec_*.json` under the job tmp dir and do not contain `ledger_write.py`. The window times match the context exactly; the identification of the writer script is not confirmable from the pack. Recorded in the spec note. No window was adjusted.
3. 5b36b02f-1: the 300 chars (13:26:38.207Z-13:27:00.341Z) end at the `oxlint` call, so `oxfmt` is not visible in this window. Window times match the context exactly. Recorded in the spec note.
4. All other writer windows match the CONTEXT: 300ac3a1 12:13:52-12:14:04Z (gsd-tools roadmap.update-plan-progress, full text visible), 3a05f288 13:39:24-13:40:45.729Z (trust_figures_census.py), 5b36b02f-2 13:50:01-13:50:27Z (oxlint then oxfmt visible). Last own Edit of force-reload spec 13:23:49.956Z and of terminal-input-probes.ts 13:49:53.167Z match the context.
5. The measured mtime for 3a05f288 was stored as 1791034845084.3274 by the spec generator; it is the same IEEE double as the plan's 1791034845084.3275 (Python `==` True).
6. Hunks are synthetic (3 invented lines per file); the pack is content-free. Names, session ids, timestamps and windows are real.
7. mtime provenance: measured = 3a05f288 only. placed = 300ac3a1, 5b36b02f-1, 5b36b02f-2, 4a7ee8bc (midpoint of the writer window) and the beside entry 4615e1d1 (end of its own last Edit, 14:42:07.480Z, so the window rule cannot allow it: not a shell window and not after its own last edit).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] tool_result prefilter regex too strict**
- **Found during:** Task 1 first gate run (replay denied, 0 windows).
- **Issue:** `/"tool_use_id":"([^"]+)"/` required no whitespace after the colon; the first version of the gate wrote python's default `", "`-spaced JSON, so no shell window ever closed.
- **Fix:** card regex now `"tool_use_id"\s*:\s*"..."`; gate writes compact JSON like the harness. Diagnosed by calling `ownership()` on the rebuilt transcript before touching any predicate.
- **Files modified:** hooks/doctrine_cards.js, tools/test_card_precision.py
- **Commit:** 4e9cf4d4 (fixed before the task commit)

### Plan-directed host adaptations (not behavioral deviations)
- Pre-commit HEAD assertion: the branch is `mission/skill-capability-run` in a worktree, which is outside the `agent-*` allow-list; the orchestrator resolved isolation to `none` and directed work in this tree, so commits were made here (not on main). Commits were pathspec-scoped; `git log -1 --format=%s` matched after each.
- The plan's per-task fixture claim "placed mtime" for 5b36b02f-1 etc. is by construction inside the writer window; `V-SCA-SPEC-MTIME-INSIDE-WRITER-WINDOW` pins it.

## Known Stubs

None. No placeholder values flow to any surface. (`.planning/` out-of-scope dirt `.gsd/`, `milestone.lock`, `state.json` was present before this plan and was not touched.)

## Threat Flags

None. The card gained one extra bounded `git rev-parse --show-toplevel` spawn and a `fs.statSync` of a path produced by `git diff` output joined to the git toplevel; no new network endpoint, auth path or schema. T-01-01..05 dispositions held: T-01-04 (gate never names the live ledger dir: `grep claude/state/doctrine-cards tools/test_card_precision.py` printed nothing, rc 1), T-01-03 (credential scan 0 hits).

## Self-Check

## Self-Check: PASSED

All 5 files present on disk (`ls -l`), commits 4e9cf4d4, e32fd6d3, 48c46acc in `git log --oneline -4`.
