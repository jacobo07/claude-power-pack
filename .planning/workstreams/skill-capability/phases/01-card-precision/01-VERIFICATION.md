---
phase: 01-card-precision
verified: 2026-10-03T00:00:00Z
status: passed
score: 4/4 roadmap success criteria verified (SC-A satisfied)
behavior_unverified: 0
overrides_applied: 0
advisory:
  - finding: "Window rule is not tied to the file: a peer write to the same file during one of this session's shell windows (<=120 s, after the last own edit) reads as unknown and is allowed (review WR-01, residual)"
    category: architectural
    reason: "Stated in the card header APERTURE, narrowed by MAX_WINDOW_MS=120000 and measurable via window_hits in the ledger row; not a success-criterion failure. Pinned by V-DC-MTIME-LONG-WINDOW-IGNORED but no test pins a peer write inside a short window."
    evidence_status: "documented aperture, no deterministic failing test"
---

# Phase 1: Card Precision Verification Report

**Phase Goal:** The commit card stops denying the session's own tool-mediated writes without letting a foreign hunk through.
**HEAD verified:** db19cb00 (includes the code-review fix: MAX_WINDOW_MS=120000, diff options moved before `--`)
**Host plane:** gex44 (Linux, git 2.43.0). Laptop live-hook sync is in owner-bundle.md ([A] lines 4-5) and is not a gap.
**Re-verification:** No, initial verification.

## Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | doctrine_cards.js classifies a file whose mtime lies in one of this session's shell tool-call windows after its last own edit as `unknown`, never `foreign` | VERIFIED | `hooks/doctrine_cards.js` `windowFor` + `ownShellWindowHit` + `judge` (lines ~375-410): reason `mtime-in-own-shell-window`, 1 s slack, `m > lastOwnEdit(base)`; missing stat / no timestamps / open window give no window so file stays foreign. Node suite `DOCTRINE_CARDS_PASS=37/37` includes V-DC-MTIME-IN-SHELL-WINDOW, -PRE-SESSION, -BEFORE-LAST-OWN-EDIT, -WINDOW-OPEN, -SLACK, -LONG-WINDOW-IGNORED, -WINDOW-HIT-RECORDED. |
| 2 | Gate replays the five D-CARD denies as allowed AND a pre-session foreign hunk as denied; existing card tests and destructive card suite stay green | VERIFIED | `python3 tools/test_card_precision.py` -> `SCA_PASS=36/36`; summary line `D-CARD frozen_denies=5 replayed_allowed=5/5 presession_denied=5/5 mutant_denied=5/5`. 6th deny 4615e1d1 reported beside, stays denied (`rollover-predecessor-lines`). `test-doctrine-cards.js` 37/37 (arm C `V-DC-JUDGED-COMMIT-NOT-A-WRITE` green), `test-destructive-doctrine-card.js` `DDC_PASS=15/15`, `test-capsule-mutation-guard.js` `CMG_PASS=18/18`. |
| 3 | `git exit 128` x6 class reproduced and named (cause + fix, or explicit fail-open reason) | VERIFIED | Gate output: `V-SCA-128-ROWS-SPLIT: 6 = abcd1234 x3 (index) + fce2689e x3 (only-paths)`; `V-SCA-128-CANNOT-CHDIR-abcd1234` reproduces `reason='git exit 128' basis=index git_error=cannot_chdir`, root cause = capsule-guard e2e test wrote into the live ledger, fixed by private `DOCTRINE_CARDS_STATE_DIR` (sweep + drill green). fce2689e x3: explicitly stated not recoverable from pack (`calls_in_120s_before_row=0,0,0`), per-row `git_error` classes now recorded, unborn HEAD judged against empty tree (`V-SCA-UNBORN-HEAD-JUDGED`). Honest gap: `dubious_ownership` NOT-REPRODUCED on gex44 (covered only by a synthetic-text test, labelled as such). |
| 4 | `python3 tools/test_skill_capability_program.py --pillar A` PASS | VERIFIED | Observed `CEP_PILLAR_A=PASS`. Ledger `state.A.terminal = IMPLEMENTED_AND_VERIFIED` with gate + prg evidence; prg sha256 recomputed on LF bytes = a9262884...9365 (matches ledger); evidence pack sha256 recomputed = dacfdf5a...0c05 (matches pin). |

## Note requested by orchestrator: five D-CARD replays under MAX_WINDOW_MS=120000

PASS. The cap is in the code (`const MAX_WINDOW_MS = 120000`, `windowFor` rejects `w.end - w.start > MAX_WINDOW_MS`). Writer windows in `card_replay_spec.json` are 12 s, 22 s, 27 s, 81.5 s (3a05f288, the measured one), 13 s, all under 120 s. The gate was run at HEAD db19cb00 and shows all five `V-SCA-REPLAY-ALLOWED-*` ok with reason `mtime-in-own-shell-window`, all five pre-session denied, all five mutant-denied. Review WR-02 (options after `--`) is also fixed: `git()` now puts `-U0 --no-color --no-ext-diff` before the revision/`--`.

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `hooks/doctrine_cards.js` | VERIFIED | Substantive (window rule, `classifyGitError`, empty-tree fallback), wired: main() -> judge(diff, own, mtimeOf); exports `judge, ownership, classifyGitError, MAX_WINDOW_MS`. |
| `hooks/tests/test-doctrine-cards.js` | VERIFIED | 37/37 PASS, both poles of the rule. |
| `tools/test_card_precision.py` | VERIFIED | Runs the real card as a node child with private state dir against real scratch git repos; mutant pole removes the rule body and 5/5 deny again. |
| `vault/programs/skill-capability/card_evidence_pack.json` | VERIFIED | sha256 matches pin. |
| `vault/programs/skill-capability/card_replay_spec.json` | VERIFIED | `mtime_source` measured only for 3a05f288, placed for the other four; gate asserts it. |
| `vault/programs/skill-capability/evidence/A-card-precision.md` | VERIFIED | sha matches ledger; names host gex44, 6th deny beside D-CARD, fce2689e not recoverable. |
| `hooks/tests/test-capsule-mutation-guard.js` | VERIFIED | Private `DOCTRINE_CARDS_STATE_DIR`; sweep floor=2 and drill (stripped copy flagged, unmodified not) pass. |

## Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| SC-A | 01-01, 01-02, 01-03 (all declare `requirements: [SC-A]`) | SATISFIED | All four criteria above. REQUIREMENTS.md marks SC-A `[x]` and Traceability "Phase 1 / Complete". No other requirement ID maps to Phase 1 (no orphans). |

## Anti-Patterns

Grep for TBD/FIXME/XXX over the five touched source/test files returned nothing. Savings in ledger are `upper_bound`, displacement unknown (no overclaim). No stubs found.

## Advisory (not blocking)

- WR-01 residual: a peer write to the same file inside a short (<=120 s) own shell window, after the last own edit, still reads as unknown and passes. It is stated in the card header APERTURE, bounded by the cap, and each hit is recorded (`window_hits` with mtime/window_start/window_ms) so the rate can be measured later. It does not contradict any success criterion (criterion 2's foreign case is a pre-session hunk).
- `dubious_ownership` class has no real-git reproduction on gex44 (declared NOT-REPRODUCED in gate output).
- Three of five replays use placed mtimes by construction; the gate and spec say so, so "allowed" for those four rests on the real writer windows from the pack, not on measured file mtimes.

## Human Verification

None required for phase 1. Laptop-plane live hook sync is routed to owner-bundle.md.

## Gaps Summary

No gaps. Phase goal achieved on host gex44.

_Verified: 2026-10-03_
_Verifier: Claude (gsd-verifier)_
