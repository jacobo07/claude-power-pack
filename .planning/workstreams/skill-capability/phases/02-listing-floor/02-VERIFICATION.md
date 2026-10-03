---
phase: 02-listing-floor
verified: 2026-10-03T00:00:00Z
status: passed
score: 7/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 2: Listing floor - Verification Report

**Phase Goal:** Decide pillar B under its frozen rule; no third hiding attempt without a fresh-session D-LISTING measurement.
**Host:** GEX44 Linux, worktree sc-run, HEAD e8641d69. **Re-verification:** No.

## Observable Truths (all observed by this verifier, not taken from SUMMARY)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Measurement file names D-LISTING with `command:` | VERIFIED | `vault/programs/skill-capability/evidence/B-listing-floor.md`: `grep -c D-LISTING` = 6, `grep -c 'command:'` = 6 (probe commands for R2R1/R3/champion/challenger lines 55-58, plus the verdict script lines 59-60). Its LF sha256 recomputed = 941e7185...3dde, equal to the sha in ledger `state.B.evidence[measurement]` |
| 2 | `python3 tools/test_skill_capability_program.py --pillar B` PASS | VERIFIED | printed `CEP_PILLAR_B=PASS` |
| 3 | `--pillar A` still PASS | VERIFIED | printed `CEP_PILLAR_A=PASS`; `--selftest` printed `CEP_SELFTEST=PASS` and `SCP_SELFTEST=PASS` |
| 4 | Ledger `frozen` equals the copy at the FROZEN_AT commit | VERIFIED | FROZEN_AT = 217d72b5...; `git show 217d72b5:vault/programs/skill-capability/ledger.json` frozen == current frozen: `True`; commit is an ancestor of HEAD. Only `state.B` changed (git diff vs plan base touches ledger.json, owner-bundle.md, the script, the evidence file; nothing under modules/ or wiki/) |
| 5 | No fresh session consumed (D-SESSIONS listing family 8 of 12) | VERIFIED | frozen D-SESSIONS = `listing_family_remaining 8, total 12`; `git log 4d1cfb83..HEAD -- wiki/tools/listing_floor_probe.results.jsonl wiki/tools/listing_floor_probe.py` = 0 commits, so no new probe row and no probe change; no source file touched. The "0 consumed" statement is a declared constant plus absence of any new row, which is the strongest evidence available on this plane. |
| 6 | `python3 tools/test_listing_floor_verdict.py` LF_PASS | VERIFIED | `LF_PASS=11/11`, rc 0. Verdict from rows: challenger startup_tokens 89844 vs champion 87739 (+2105, not below), challenger chars 29795 vs cap 30000 (gap 205, 0.68%), matches frozen D-LISTING, rows equal K4-commit blob, evidence byte-equal to fresh render |
| 7 | Red drill: fabricated lower floor goes red | VERIFIED | Mutated copy `/tmp/vf_floor.jsonl` (challenger tokens 80000, chars 20000) via `--jsonl`: rc=1, `FAIL V-LF-TOKENS` (delta -7739), `FAIL V-LF-CAP` (gap 10000), `FAIL V-LF-DENOM-MATCH`, `LF_PASS=1/4`. Committed jsonl untouched (`git status wiki` clean). The tokens-only mutant and 19 further in-process drills each die by their own clause (21 drills in V-LF-DRILLS, clean case all ok, band-edge case stays ok) |

**Score:** 7/7. behavior_unverified: 0.

## Requirements Coverage

| Requirement | Source | Status | Evidence |
|-------------|--------|--------|----------|
| SC-B | 02-01-PLAN, 02-02-PLAN (`requirements: [SC-B]`) | SATISFIED | Pillar B closed in ledger as FALSIFIED_OR_REJECTED_BY_EVIDENCE with measurement + owner + 3 commit evidences; one savings entry `upper_bound`, displacement `unknown`, denominator D-LISTING (9000 tokens, minus ~4000 per gateway read, measured saving none). Third hypothesis is deferred to the laptop in a single `[B] (host: laptop)` line in owner-bundle.md (cites D-SESSIONS 8 of 12), which is a laptop-plane item and not a phase gap. No orphaned requirements. |

## Anti-Patterns

TBD/FIXME/XXX/TODO/HACK grep over `tools/test_listing_floor_verdict.py`: no hits. No stubs; the script derives every verdict figure from the jsonl, frozen ledger and git blobs.

## Gaps / Advisories

- Advisory (bookkeeping, not a goal gap): `.planning/workstreams/skill-capability/REQUIREMENTS.md` still shows SC-B `[ ]` and traceability row `Pending` (lines 12, 37). The orchestrator should flip it on phase completion.
- Untracked `.gsd/` pre-existed and is unrelated.

## Human Verification

None for this phase. The third (plugin-paging gateway) hypothesis measurement is a laptop-plane Owner item already in owner-bundle.md.

_Verified by gsd-verifier on GEX44; no source edited, nothing committed._

## Addendum (orchestrator, after review fixes 4ddd8846)

The code-review fixes (WR-01..03, IN-01/02/04) changed the rendered evidence bytes; the measurement sha256 in
state.B was re-pinned 941e7185... -> 48686286... in the same commit. Re-observed on gex44 at 4ddd8846:
`python3 tools/test_listing_floor_verdict.py` -> `LF_PASS=11/11`; `--pillar B` -> `CEP_PILLAR_B=PASS`;
`--pillar A` -> `CEP_PILLAR_A=PASS`. Verdict unchanged: FALSIFIED. Status stays passed.
