---
phase: 04-coverage-criticality-and-freshness
plan: 03
subsystem: pillar H freshness / drift (card vs source, router gate wiring)
tags: [drift, card-source, router, pillar-H, gate]
requires: [04-01, 04-02]
provides: [card_source_digests.json, skill_mirror_drift card functions, V-ROUTER-SKILL-DRIFT]
key-files:
  created: [vault/programs/skill-capability/card_source_digests.json]
  modified: [tools/skill_mirror_drift.py, tools/test_skill_drift.py, vault/programs/skill-capability/evidence/H-drift.md, tools/router_freshness_gate.py, tools/test_router_freshness_gate.py]
status: complete
plan_head_before: 0a2ab9eaafcfcd7f915d2d0908c53b240bbde2de
commits: 2
actuals:
  tasks: 2
  commits: 2
---

# Phase 4 Plan 03: pillar H card-vs-source digests and router gate wiring Summary

Card/source pairs are discovered from the dispatcher (never listed), pinned as LF sha256 pairs in a committed record, driven red and green in a temp repo, and the frozen owner `tools/router_freshness_gate.py` now prints `V-ROUTER-SKILL-DRIFT` through `skill_mirror_drift.live_report`.

## Commits (own; a foreign docs(state) commit 650387c7 landed between them and is not mine)

- `06dae4b0` feat(04-03): H -- card vs source digest record, both poles
- `a98f883c` feat(04-03): H -- router freshness gate reaches the skills drift check

## Task 1: card vs source

- `skill_mirror_drift.py`: `card_pairs` (via `skill_coverage.discover_cards`, de-duplicated by (hook, skill), source `skills/<skill>/SKILL.md`), `card_source_state` (one `batch_blobs` at a resolved commit, `_norm_sha`; git failure gives INCONCLUSIVE with `git not found`), `card_drift` (CURRENT / SOURCE_CHANGED / CARD_CHANGED / RECORD_STALE both ways / UNTRACKED / INCONCLUSIVE), `card_verdict`, `load_card_record` (CRLF->LF first), `record_cards`; CLI `--record-cards` and `--cards`.
- Record `vault/programs/skill-capability/card_source_digests.json`, schema `card-source-digests/1`, recorded_at_commit `0a2ab9eaafcfcd7f915d2d0908c53b240bbde2de`, 2 pairs: `concurrent-writers-shared-tree` <- `hooks/doctrine_cards.js`; `destructive-state-authorization` <- `hooks/destructive_doctrine_card.js`.
- Gate additions: V-SKD-CARD-SOURCE-CURRENT, -POLES (unchanged CURRENT; committed source edit SOURCE_CHANGED; re-record CURRENT; committed card edit CARD_CHANGED; second registered card RECORD_STALE; unregistered recorded card RECORD_STALE), -CRLF, -GIT-FAILURE. `render()` gained a "Card vs source" section; `H-drift.md` re-rendered (one currency check, 04-02's `evidence_current`).
- `python3 tools/test_skill_drift.py` verbatim last line: before `SKD_PASS=9/9`, after `SKD_PASS=13/13`, exit 0.
- Out-of-gate drill: record copied to /tmp/04-03-rec.json, one digit of the first `source_sha256` changed, `card_drift` on it gave `[('concurrent-writers-shared-tree', 'SOURCE_CHANGED'), ('destructive-state-authorization', 'CURRENT')]`.
- `grep -cE '"(hooks/doctrine_cards.js|hooks/destructive_doctrine_card.js)"' tools/skill_mirror_drift.py` prints 0.
- CE contract one-off `_check_evidence("H", prg ...)` on `H-drift.md`: `[]`; no CR bytes.

## Task 2: router gate wiring

- `router_freshness_gate.py`: `live_skills_root` (install shape `<x>/.claude/skills`, else `~/.claude/skills`) and `skill_drift_check(repo_root, live_root=None)` returning PASS / FAIL / UNMEASURED; imports `skill_mirror_drift` inside the function, passes `repo_root` (the checkout judged) to `live_report`; any exception or INCONCLUSIVE is FAIL with its reason. `run()` calls it after V-ROUTER-CANONICAL and before the router-absent return; FAIL adds `V-ROUTER-SKILL-DRIFT` to failures, UNMEASURED neither passes nor fails. Docstring extended by one paragraph naming the host plane.
- gex44 line: `V-ROUTER-SKILL-DRIFT FAIL       24 repo skills vs ~/.claude/skills: IDENTICAL 13, DRIFT 1, INCONCLUSIVE 0, ABSENT_LIVE 10 (reported, not drift)` then `android-reverse-engineering: DRIFT missing_live=[4 .ps1 scripts]`, then `V-ROUTER-LINKS      FAIL  router absent`.
- Router test file, before: `ROUTER_GATE_TESTS=7/8  threshold=8/8`, only `FAIL  V-RFG-CLEAN  live repo does not pass`. After: `ROUTER_GATE_TESTS=10/11  threshold=11/11`, the same single FAIL; the three new tests PASS (V-RFG-SKILL-DRIFT-GREEN, -RED, -UNMEASURED). The threshold line is computed, so no pre-existing line was edited: `git diff -U0` of the test file against the pre-edit HEAD has 0 removed lines.
- Other gates: `test_skill_drift.py` SKD_PASS=13/13, `test_skill_coverage.py` SKC_PASS=15/15.
- git unavailable (`PATH=/nonexistent /usr/bin/python3 ... skill_drift_check`): `('FAIL', ['INCONCLUSIVE: git not found: git executable not found on PATH or known Windows locations'])`, rc=0, 0 Traceback lines.

## Runtime vs bounds (gex44)

| measure | measured | bound |
|---|---|---|
| `skill_drift_check(REPO)` 3 runs | 0.054 s, 0.027 s, 0.031 s (max 0.054 s) | <= 3.0 s |
| `test_router_freshness_gate.py` before (3 runs) | 0.03 s, 0.04 s, 0.03 s (rc 1, V-RFG-CLEAN) | baseline |
| `test_router_freshness_gate.py` after (3 runs) | 0.10 s, 0.10 s, 0.11 s | delta <= 5.0 s (delta about 0.07 s) |
| verify_spp row `memory-router-freshness` timeout | 120 s (tools/verify_spp.py ~line 646) | n/a |
| mirror-parity row budget (verify_global_mirrors docstring) | 15 s | all well inside |

## Notes for later plans

- `run()` defaults to `REPO_ROOT`, the canonical main checkout, so on gex44 the router gate judges the blobs of `/home/kobii/missions/skill-capability`, not this worktree; `skill_drift_check(repo)` takes the checkout explicitly.
- For the `[H]` owner-bundle line (04-04): on the laptop the router gate can newly go red three ways: live DRIFT, git missing, import or read error. The line reads the host's live tree, so a verdict names its host plane.
- `card_pairs` reads the working-tree dispatcher and hooks while digests come from HEAD blobs; commit card and source edits before `--record-cards` (same rule as the record's `rule` field).

## Deviations from Plan

None - plan executed as written. Two small choices: `card_drift` returns per-pair rows plus a separate `card_verdict` helper (the plan did not fix the return shape), and `--cards` was added to the CLI beside `--record-cards`.

## Known Stubs

None.

## Threat Flags

None. The router gate reads the live skills directory and never writes; temp-dir tests write only under their own temp root (T-04-13).

## Self-Check: PASSED

Both commits exist (06dae4b0, a98f883c); the record, tools and tests exist; all gates above re-run green after the last commit.
