---
phase: 01-baseline-integrity-repair
verified: 2026-10-03T00:00:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .gitattributes
  - .planning/workstreams/ucep/REQUIREMENTS.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-01-PLAN.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-01-SUMMARY.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-02-PLAN.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-02-SUMMARY.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-03-PLAN.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-03-SUMMARY.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-04-PLAN.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-04-SUMMARY.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-05-PLAN.md
  - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-05-SUMMARY.md
  - modules/tower/baselines.py
  - modules/tower/donegate.py
  - modules/tower/ratchet.py
  - tools/baseline_population.py
  - tools/family_baseline.py
  - tools/test_baseline_generations.py
  - tools/test_tower_ratchet.py
  - tools/test_ucep_baseline_integrity.py
  - tools/test_ucep_donegate_exits.py
  - vault/tower/baselines/persistent_state/B1.json
  - vault/tower/baselines/wii_homebrew/B1.json
covered_digest: "v1:sha256:39bce27ab68fb695af652343c871f7fed407041c8afe6ce992c9681c34f6608a"
behavior_unverified: 0
overrides_applied: 0
gaps: []
deferred:
  - truth: "authority of revert/promote/reanchor is a self-declared token (a caller can type 'Owner'); bind it to something the caller cannot type"
    addressed_in: "Phase 3 (PARTIAL match)"
    evidence: "ROADMAP Phase 3 SC3 requires admission records for ratchet.promote and archetype B0 creation, and SC2 makes cross-family/universal scope PENDING_OWNER. Neither names revert/reanchor authority, so the match is partial; see Advisory 2."
  - truth: "V-UCEP-REAL-REANCHORED pins generations == [0,1] and every active entry VERIFIED against out-of-repo absolute paths (IN-02)"
    addressed_in: "later phase, not named"
    evidence: "01-REVIEW IN-02 Deferred: revisit before the first legitimate B2 on persistent_state/wii_homebrew. No ROADMAP phase schedules a B2 on those two families, so the trigger is unlikely before Phase 8."
  - truth: "unjudged_reason maps MALFORMED / REFUSED_PATH / ERROR all to 'other' (IN-03 half)"
    addressed_in: "Phase 6"
    evidence: "01-REVIEW IN-03 Deferred: do it with the first consumer that must tell a refused path from an evaluator crash. ROADMAP Phase 6 SC4 is the first consumer (Stop judge, rung rows unjudged/violated)."
owner_review_items:
  - id: A1
    item: "authority string on persistent_state/B1.json and wii_homebrew/B1.json is the agent-typed 'Owner (UCEP-01, plan of record vault/plans/ucep-naked-verb-2026-10-02.md)'"
    verifier_decision: "accepted, disclosed assumption, not a gap (see Criterion 1)"
  - id: A2
    item: "12 NA_REASONS tokens and NA_SHARE_CAP_PERCENT = 30 are executor choices"
  - id: A3
    item: "9 origins point at the PP main checkout (a live tree on branch feature/knowledge-acquisition)"
  - id: A4
    item: ".gitattributes eol=lf pin instead of a CRLF-insensitive anchor hash"
advisory:
  - finding: "01-EVIDENCE.md is stale against HEAD 0939d27b and one of its statements is now false"
    category: other
    reason: "EVIDENCE was written at 232836ce. It records 33/33, 13/13, 16/16, 16/16 and 23/23; HEAD measures 40/40, 17/17, 18/18, 17/17 and 24/24 after the review fixes WR-02..07. Section 9 says 'no live hook path is changed', but commit 1ba16a61 changed modules/gsd_x/heartbeat.py (imported by gsd_x/cli.py, the UserPromptSubmit child). It is behaviour-preserving for a stable environment (call-time resolution of the same formula, 7/7 gates) but never exercised in a live session. Add an addendum: heartbeat.py changed, Production Reality UNJUDGED for it."
    evidence_status: "git diff 07f04424..HEAD -- modules/gsd_x/heartbeat.py; 01-EVIDENCE.md section 9"
  - finding: "WR-01 deferral target (Phase 3) only partly covers the residual"
    category: security
    reason: "Phase 3 admission records gate promote and archetype B0 creation. revert and reanchor authority (the operations used for the two real B1 files) is still a typed string after Phase 3 as written. Name an owner for it (a Phase 3 plan line or a UKDL candidate in Phase 9)."
    evidence_status: "ROADMAP Phase 3 SC1-SC5; ratchet.py lines 73-86"
---

# Phase 1: Baseline integrity repair - Verification Report

**Phase Goal:** The baseline chain is green and the known ratchet/gate escape routes are closed.
**Requirement:** UCEP-01 (declared in all five PLAN frontmatters, present in REQUIREMENTS.md mapped to Phase 1; no orphaned requirement).
**Verified:** HEAD 0939d27b, base 07f04424, worktree `...\.claude\worktrees\ucep`, branch `ucep/mission`.
**Status:** passed
**Re-verification:** No, initial verification.

All numbers below were produced by the verifier at HEAD 0939d27b, with `CLAUDE_STATE_DIR` on a temp dir (and a temp HOME for the second batch), not copied from SUMMARY or EVIDENCE.

## Suite re-run (verifier's own, every rc=0)

| suite | result line |
|---|---|
| test_baseline_generations | BASELINE_GENERATIONS_PASS=18/18 |
| test_tower_ratchet | TOWER_RATCHET_PASS=21/21 |
| test_tower_donegate | TOWER_DONEGATE_PASS=10/10 |
| test_family_baselines | FAMILY_BASELINES_PASS=20/20 |
| test_ucep_baseline_integrity | UCEP_BASELINE_INTEGRITY_PASS=40/40 |
| test_ucep_donegate_exits | UCEP_DONEGATE_EXITS_PASS=17/17 |
| test_tower_select / checks / capsule / inheritance | 15/15, 23/23, 16/16, 17/17 |
| test_family_injection / test_tower_o4 / test_gsd_x_heartbeat_path | 24/24, 7/7, 7/7 |

Zero `  FAIL` lines across the 13 logs. After the runs, `git status --porcelain -- vault modules tools` shows only ` M vault/progress.md`, which was already dirty before any run (not this mission's file).

## Falsification of the instruments (could they have returned the other answer?)

The verifier copied `modules/ tools/ vault/tower` to a temp dir, replaced `ratchet.py`, `baselines.py`, `donegate.py` with their 07f04424 versions, and ran the two new harnesses:

- `test_ucep_baseline_integrity.py` at base code: rc=1. FAIL: V-UCEP-H1-RAW, H1-API, H2-WHY, H2-ORIGIN, H2-CLASS, H2-SCOPE, H3B, H3B-DELETE-B0, H3B-GAP, H3B-PARENT-FIELD, ALLOWLIST, CLI-UNANCHORED, REANCHOR-*. PASS (controls): H1-RAW-CONTROL, H1-API-CONTROL, H2-CONTROL, H3B-CONTROL-TAMPER, H3B-ROOT-CONTROL. The attacks are real on the old code and the controls are green on both, so the gates discriminate.
- `test_ucep_donegate_exits.py` at base donegate: rc=1, `UCEP_DONEGATE_EXITS_PASS=8/17`. FAIL: H6-TEST-UNJUDGED (verdict DELEGATED, would_block False), REPORT-COUNTS, H5-FREE-TEXT (NOT_APPLICABLE, would_block False), H5-OVER-CAP, H5-NO-REASON, WR03/WR04 gates. V-UCEP-H6-NOT-EXECUTED passes on both because base never ran tests either; it has a working positive control (V-UCEP-H6-MARKER-CONTROL: running the file by hand writes the marker).
- The original probe `wiki/tools/cbr_probe.py`, functions called at HEAD: H1 ok=False, H2 ok=False, H3b ok=False (tampered=[2] unanchored=[1]), H5 would_block=True, H6 verdict=UNJUDGED would_block=True. `promote_cases` raises RatchetRefusal on `authority 'x'`, so the script aborts at P4 as EVIDENCE says. That abort is the closed H1 hole, not a regression.

No vacuous gate found in the Phase 1 contract. Limits are listed at the end.

## Criterion 1: `ratchet.reanchor` and the 9 QUOTE_MISSING entries - VERIFIED

- `modules/tower/ratchet.py:342-368` `reanchor(family, new_origins, reason, authority, root)` delegates to `plan_reanchor` (269-339) and calls `bl.write_generation` once. Refusals are collected into one `RatchetRefusal` (all-or-nothing; gate V-UCEP-REANCHOR-ALL-OR-NOTHING passes). It keeps ids and order (only `origin` is replaced, `entries = [new_entries.get(e["id"], e) ...]`), records `changes[id] = {kind: REANCHORED, reason, authority, from, to}`, and refuses when `bl.verify_origin(candidate) != VERIFIED` (lines 328-332), plus changed or empty quote, relative path, `/.claude/worktrees/` path, no-op, unknown or reverted id, bad authority.
- Real data, verifier's own read: B0 verdicts were persistent_state `{VERIFIED:7, QUOTE_MISSING:8}` and wii_homebrew `{VERIFIED:14, QUOTE_MISSING:1}`, which is exactly the 9. Latest generations are `{VERIFIED:15}` for both. Both chains `[0,1]`, `verify_chain.ok == True`, `parent_sha256` equals the current sha256 of B0. B1 differs from B0 in the `origin` field only (8 entries and 1 entry), ids identical, one generation per family. All 9 `changes[id].kind == "REANCHORED"`; new files are `...\claude-power-pack\skills\<skill>\SKILL.md` in the main checkout, tracked in git there (`ls-files --error-unmatch` ok) and present in the worktree HEAD.
- Authority string (A1). Decision: **accepted, disclosed assumption, not a gap.** Reasons: (1) ROADMAP SC1 itself orders these writes, and the plan of record carries the Owner's approval of 2026-10-02, so the string's content ("plan of record ...") is a truthful pointer rather than a claim that the Owner typed the command; (2) the contract in SC2 asks for an allowlist, which is implemented, and `ratchet.py:73-86` states the real residual (self-declared token; root of trust is repo history plus the Owner reviewing the commit); (3) both generations are append-only and supersedable by a later reanchor or revert; (4) EVIDENCE section 6 labels it an Owner-review item and not an Owner confirmation. The Owner still has the standing right to reject it; that is recorded in `owner_review_items`, and it is not an unmet must-have. Strict alternative: if the orchestrator wants the Owner's personal ack before closing, treat A1 as human_needed.
- A3 note (not a gap): the origin path is a live tree on `feature/knowledge-acquisition`, as the B0 origins in `~/.claude/rules` and the CavEX paths already were. `verify_chain` does not read origins; only the citations gate does.

## Criterion 2: `ratchet.diff` coverage, unanchored child, allowlist, H1/H2/H3b - VERIFIED

- `diff` (ratchet.py:134-161) compares requirement, check (WEAKENED / CHECK_CHANGED), `why` (WHY_CHANGED), origin file+line+quote (REANCHORED), `class` (CLASS_CHANGED), `propagation_scope` (SCOPE_CHANGED, absent equals absent), plus WITHDRAWN and REVERTED. `_recorded` needs the kind, a non-empty reason and `is_authorized(authority)`.
- `ChainReport.ok` is `not regressions and not tampered and not unanchored` (180-182); a child without `parent_sha256` is appended to `unanchored`. WR-02 closes the missing-root variant: `verify_chain` (190-216) records MISSING_ROOT when the lowest generation is not 0, GAP for non-consecutive numbers, PARENT_MISMATCH when `parent != predecessor`. Gates V-UCEP-H3B-DELETE-B0 / -GAP / -PARENT-FIELD with V-UCEP-H3B-ROOT-CONTROL pass at HEAD and fail at base (above).
- Allowlist: `AUTHORITIES = ("Owner",)` in code, first-token match, case-sensitive; refuses `x`, blank, None, `owner`, `Ownerx`, `Owner's cat`, `Bot Owner`; accepts the real B1 `promoted_by` form (V-UCEP-ALLOWLIST).
- **WR-01 deferral to Phase 3: legitimate as a Phase 1 deferral, imprecise as to its target.** Phase 1 SC2 asks for "authority comes from an allowlist", which is met. The residual (a caller can type "Owner") is honestly disclosed at `ratchet.py:77-85` and the fix needs a design the plan did not scope (a capability or admission record). But Phase 3 SC3 covers only `promote` and archetype B0 creation, not `revert` or `reanchor`, so the deferral names a home that only partly fits. Recorded as Advisory 2, not a gap.

## Criterion 3: donegate exits - VERIFIED (module level; hook path UNJUDGED)

- `donegate.py`: `NA_REASONS` is a closed 12-token tuple with no deferral token; `parse_na_reason` partitions on ":" and matches the head exactly; `NA_SHARE_CAP_PERCENT = 30`, `na_cap = (30*n)//100`, and over the cap every claim is voided to UNJUDGED `na-over-cap`. Real families admit 4, 4, 5 and 4 claims (15, 15, 17, 15 entries).
- `test:` is never executed anywhere: `modules/tower` contains no `subprocess`, `os.system`, `os.popen`, `exec`, `eval`, `runpy`, `importlib`, `__import__`, `os.spawn` or `os.exec` (verifier grep: no matches); `checks.py` for `test:` does `os.path.isfile` only (lines 152-154) and is byte-unchanged since base; `donegate.judge` has no caller under `modules/` (grep of `donegate` and `.evaluate(` found only the `tower/donegate.py`, `tower/select.py`, `tower/ratchet.py` imports and a comment in `gsd_x/cli.py`). `judge` remaps `kind == "test" and outcome == DELEGATED` to UNJUDGED `test-not-run`. `counts` keeps `unjudged`, `unjudged_tests` and `violated` apart; `registry:` stays DELEGATED (V-UCEP-REGISTRY-STILL-DELEGATED).
- H5 and H6 no longer pass: probe H5 would_block=True, H6 verdict=UNJUDGED would_block=True; harness red at base, green at HEAD.
- Post-review hardening beyond the contract also verified green: WR-03 (`would_block` includes the chain), WR-04 (N/A over a failing check is flagged `na_masked_violation`, deliberately not blocking; disclosed).
- Production reality for this criterion is module level only. No hook path calls `donegate.judge` until Phase 6, so enforcement is not exercised; EVIDENCE says UNJUDGED and the verifier agrees.

## Criterion 4: discovery with a population floor, no hardcoded family tuple - VERIFIED

- A search for `kobiicraft_mode|persistent_state|wii_homebrew|FAMILIES` in `tools/test_tower_ratchet.py` and `tools/test_baseline_generations.py` finds no family name at all. Both real-tree gates call `bl.discover_report()` (os.walk over `BASELINES_DIR` read at call time, nested axes by relative path, symlinked and unreadable directories reported and raised on).
- Floors: `len(subjects) >= 4` (both) and `len(real) >= 60` (citations gate), plus WR-05 cross-checks from `tools/baseline_population.py` against the family registry, a glob, the git index and a raw-JSON active-entry count (62).
- Verifier drills on a temp copy: planting `archetype/PLANTED` with a missing-file origin makes `V-BGEN-REAL-B0-CITATIONS-HOLD` FAIL naming `('archetype/PLANTED','planted-1'): FILE_MISSING` (population 63); planting a nested subject with a wrong `parent_sha256` makes `V-TRAT-REAL-CHAINS` FAIL naming `archetype/PLANTED tampered [1]`; dropping `kobiicraft_mode` fails both gates (population 47, `cross_check.missing.families`). The nested axis is reached and the floor is a real lower bound.

## Criterion 5: listed suites and immutability - VERIFIED

- The four named suites pass at HEAD (table above): 18/18 (16/16+ required), 21/21, 10/10, 20/20.
- sha256 of the five pre-existing generation files, on disk, equals the blob at 07f04424 and the blob at HEAD, before and after the verifier's runs:

| file | sha256 |
|---|---|
| kobiicraft_mode/B0.json | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 |
| persistent_state/B0.json | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 |
| web_surface/B0.json | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 |
| web_surface/B1.json | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 |
| wii_homebrew/B0.json | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd |

All equal the EVIDENCE section 4 table.
- `git log 07f04424..HEAD -- vault/tower/baselines` lists only `994fe560` and `694f5a24`; `git diff --name-status 07f04424..HEAD -- vault/tower/baselines` is exactly `A persistent_state/B1.json`, `A wii_homebrew/B1.json`. `git ls-files --eol`: all 7 generation files `i/lf w/lf attr/text eol=lf`.

## Requirements coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| UCEP-01 | 01-01..01-05 (all five declare it) | SATISFIED | Criteria 1-5 above; REQUIREMENTS.md row maps it to Phase 1; no other ID maps to Phase 1 |

## Anti-patterns, scope and liveness

- No debt-marker comments (the three standard debt tokens) in any file changed by the phase (search over modules/tower, heartbeat.py, tools, .gitattributes: none).
- Read-only `reachability.gate()` at HEAD: ok=False, 63 offenders, 486 rows (the orchestrator's measurement reproduced); dirty-path SET before and after equal. The gsd_x/goal, gsd_x/mission, tower/donegate and tower/ratchet offenders are pre-existing and the phase added no module under `modules/`.
- Out-of-contract change: `modules/gsd_x/heartbeat.py` (review fix WR-07), behaviour-preserving; see Advisory 1.

## Production Reality

EVIDENCE section 9 never says PROVEN; the highest word is OBSERVED, for repo-local changes on an unmerged branch, and the donegate hook path and live `family_block` stamp are UNJUDGED. The verifier agrees and adds heartbeat.py as UNJUDGED in live sessions. No upgrade beyond OBSERVED is warranted.

## Known limits (not Phase 1 gaps)

- The N/A tokens cannot be checked against the entry (a `no-money` claim over a money rule passes within the 30% cap); only the cap bounds abuse.
- A forger who recomputes `parent_sha256` after hollowing is undetectable at file level; repo history is the root of trust.
- Floors equal today's population (4 / 60), so alone they pass by coincidence; the cross-check is what bites. The git route is reported `unavailable` rather than failing when git is absent.
- `V-UCEP-REAL-REANCHORED` and the citations gate read absolute paths outside the repo; they FAIL (not INCONCLUSIVE) on another host (IN-02 deferred).
- 14 MOVED citations remain tolerated (outside the 9-entry bound).
- Verifier ran only this phase's suites, not the whole workspace suite; the sorted dirty set was equal before and after.

## Gaps Summary

No gaps. All five roadmap success criteria are met by code and data present at HEAD, and the instruments for each were driven from the failing side. Two advisories (stale EVIDENCE.md, partial fit of the WR-01 deferral) and four Owner-review items (A1-A4) are recorded and do not change the status.

---

_Verified: 2026-10-03_
_Verifier: Claude (gsd-verifier)_
