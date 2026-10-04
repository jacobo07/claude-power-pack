---
phase: 04-cognitive-cost-regression-gate
verified: 2026-10-04T00:30:00Z
status: human_needed
score: 8/8 roadmap+plan truth groups verified (IC-K terminal not claimable on GEX44)
covered_files:
  - .planning/workstreams/incremental-cognition/REQUIREMENTS.md
  - tools/floor_regression_gate.py
  - tools/test_floor_regression_gate.py
  - vault/programs/incremental-cognition/evidence/K.md
  - vault/programs/incremental-cognition/floor/reference-gex44.json
  - vault/programs/incremental-cognition/owner-bundle.md
covered_digest: "v1:sha256:e7d597ab36b5bc56990af6fa7811f2cb3fe3fe6e21aa336334f2832b52821ae1"
behavior_unverified: 0
overrides_applied: 0
gaps: []
human_verification:
  - test: "Laptop run of the [K] owner-bundle item: cherry-pick, fixture suite, write floor/reference.json (option A probe or option B --session 8f983bc6), seeded --real-session control, one real --check of a later session against the committed reference (PRG)"
    expected: "FLOOR_PASS n/n on the laptop; reference.json committed; PRG check recorded in evidence/K-prg.md (WITHIN_BOUND_CHARS_ONLY or WITHIN_BOUND); then ledger state.K and IC-K are closed by the Owner/laptop run"
    why_human: "Frozen rule K needs a laptop-plane reference; GEX44 cannot produce it. IC-K must stay unticked here."
  - test: "Judge the review-fix decisions WR-01 (absent >=1,000-char layer = exit 2), WR-02 (uncorrelated hook element = unattributed), WR-03 (uncompared tokens axis = exit 2 unless --chars-only)"
    expected: "Thresholds and verdict names are what the Owner wants. Note the consequence: the reference's tokens come from a worker session with its own prompt digest, so an ordinary session is never tokens-comparable and real use will be WITHIN_BOUND_CHARS_ONLY; plain WITHIN_BOUND needs a same-prompt probe session."
    why_human: "Policy choices (fix report marks them requires-human-verification); gates cannot judge intent."
  - test: "Judgment-tier prohibitions (all flagged, NON-AUTHORITATIVE verdicts below): no exit 0 on an unmeasurable comparison; unattributable origin never filed project/harness; nothing written under ~/.claude, no real claude session; IC-K/state.K not ticked/written; reference-gex44 not presented as frozen-rule reference; no laptop command claimed run"
    expected: "Reviewer agrees with the verifier's evidence-based reading (all held in this verification)"
    why_human: "verification: judgment tier -> unverified-prohibition, human review recommended (ADR-550 D4)"
---

# Phase 4: Cognitive cost regression gate Verification Report

**Phase Goal:** a material rise in startup floor by layer is visible in review.
**Success criteria (ROADMAP):** gate green on today's floor, red on a seeded rise (positive control), layer and scope reported.
**Verified:** 2026-10-04 at HEAD f29342d0 (GEX44, python3). **Status:** human_needed. **Re-verification:** No (initial).

## Gates re-run by the verifier (not taken from SUMMARY)

| Command | Result |
|---|---|
| `python3 tools/test_floor_regression_gate.py` | `FLOOR_PASS=67/67 threshold=67/67 skipped=0 inconclusive=0` |
| `... --drill` | `DRILL-CONTROL 57/57`, `DRILL-CLEAN-AFTER-MUTANTS 57/57`, `DRILL-RESTORE sha256 096d71cc164eac46 before==after`, `DRILL killed=18/18` (M14-M18 are the review-fix mutants) |
| `python3 tools/test_incremental_cognition_program.py --selftest` | `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS` |
| `... --pillar K` | `FAIL L3 K: no terminal disposition` (expected: K open) |

The artifact sha256 values on disk (gate 096d71cc..., test 3bec0f7b..., reference-gex44 0d59e0dc...) equal those in evidence/K.md, and the gate hash equals the drill's restore hash.

## Independent behavioral checks (own commands, transcripts read-only; sha256 identical before/after)

Real transcripts: 607795c4 (interactive, ic-run) and 34f03871 (mission worker), reference = committed `reference-gex44.json`.

| Check | Observed | Status |
|---|---|---|
| Green on today's floor: `--check --reference reference-gex44.json --transcript 607795c4 --chars-only` | `FLOOR verdict=WITHIN_BOUND_CHARS_ONLY exit=0`, `SCOPE universal=+0 project=+0 harness=-59 unattributed=-4383` | VERIFIED |
| Same without `--chars-only` | exit 2 `tokens_unmeasured` (TOKENS not_comparable ref=109021 now=107351) | VERIFIED (WR-03 contract) |
| Default reference on GEX44 | exit 2 `reference_missing` (floor/reference.json absent; no laptop reference faked) | VERIFIED |
| Real red: scratch ref from 607795c4, check 34f03871 | `RISE system_prompt scope=unattributed delta=+4383 ... rules=universal_1k`, exit 1 (an appended system prompt is not filed as harness) | VERIFIED |
| Positive control, own seeding on a scratch copy of the real transcript (scratch HOME): untouched copy | exit 0, universal=+0 project=+0 | VERIFIED |
| +1,024 chars in `~/.claude/CLAUDE.md` entry | `RISE memory_global scope=universal delta=+1024 rules=universal_1k`, `SCOPE universal=+1024 project=+0`, exit 1 | VERIFIED |
| +1,024 chars in the project CLAUDE.md entry | `SCOPE universal=+0 project=+1024`, exit 0 | VERIFIED |

Layer and scope are reported on every path (`LAYER`, `RISE`, `SCOPE` lines, `--json` keys incl. detail/probe_error).

## Observable truths

| # | Truth (ROADMAP SC + plan must_haves) | Status | Evidence |
|---|---|---|---|
| 1 | SC1 green on today's floor | VERIFIED | row 1 above; V-FLOOR-REF-GEX44-GREEN PASS. Green is `WITHIN_BOUND_CHARS_ONLY`, not plain `WITHIN_BOUND` (see supersession) |
| 2 | SC2 red on seeded rise (positive control) | VERIFIED | own seeded check above + V-FLOOR-SEEDED-REAL PASS + drill kills M1-M18 |
| 3 | SC3 layer and scope reported; universal vs project distinct | VERIFIED | SCOPE line; drill M1/M2 (scope_key mutants) killed |
| 4 | 04-01: write-reference/check, exit 0/1/2, never 0 on unmeasurable; materiality rules; explanations bound + empty-reason refusal; no transcript content emitted; secret-firewall redaction | VERIFIED | gate suite 67/67 (V-FLOOR-* incl. NO-SECRET, EXPLAIN*, M4-M6 killed); real default-reference refusal exit 2 |
| 5 | 04-01 scope never guessed / system prompt parts digest-identified, unattributed | VERIFIED | real appended-prompt red (+4383 unattributed) |
| 6 | 04-02: hook/skill/agent attribution by evidence; absent cwd -> unattributed | VERIFIED (superseded in part, below) | V-FLOOR-HOOK-*, -SKILL-*, -AGENT-*, -CWD-ABSENT-UNATTRIBUTED PASS; M9-M11 killed |
| 7 | 04-03: four sources, --probe never ends in traceback/0, no real session, real GEX44 reproduction, reference-gex44 labelled gex44 and not frozen reference | VERIFIED | V-FLOOR-SOURCES-*, -PROBE-*, -NO-REAL-SESSION, -REAL-GEX44 PASS; `plane: gex44` in provenance; wiki/tools/listing_floor_probe.py and results file have no diff vs phase base |
| 8 | 04-04: [K] bundle item with exact commands, parse-proven, NOT RUNNABLE HERE stated; K.md with Product/Intelligence Delta, Status OPEN; state.K `{}`, IC-K unticked | VERIFIED | V-FLOOR-BUNDLE-ARGV-PARSES PASS; K.md read in full; ledger `state.K` = `{}`; REQUIREMENTS line 22 `[ ]`; ROADMAP Phase 4 `[ ]` |

### R2-W1 (orchestrator requirement)

`reference-gex44.json` provenance carries `window_sha256` dc6d23b90cac05e6...fd63 and `window_rows` 34 (read from the file). Both `V-FLOOR-WINDOW-APPEND-STABLE` (test line 2609) and `V-FLOOR-REAL-REFERENCE-PINNED` (line 2674) exist and PASS in the re-run; PINNED re-derives the digest from the transcript on disk (not SKIP). SATISFIED.

### Where the review-fix superseded a plan truth (all intentional, all gated)

- 04-01/04-03 "`--check` exits 0 when no material unexplained rise" and "committed reference vs 607795c4 exits 0": now exit 2 `tokens_unmeasured` unless `--chars-only` -> `WITHIN_BOUND_CHARS_ONLY` exit 0 (WR-03). A material chars rise stays exit 1 either way; a comparable tokens axis is still enforced with the flag. Roadmap SC1 "green" is met in the chars-only sense.
- 04-02 "uncorrelated element falls back to the event's registrations (project when only project registers it)": replaced by `unattributed`/`event_uncorrelated` (WR-02); stricter, consistent with the plan's own prohibition on guessing project.
- 04-01 "exit 2 on non-comparable ..." widened: window_line_unparseable (CR-01) and layer_absent:<layer> (WR-01) are new exit-2 reasons.
- 04-03 reference regenerated twice (CR-02 hook source = `hook:<sha256[:16]>[:basename]`, WR-02); window pin, rows 34, total_chars 207245, tokens unchanged; reference holds no `node `/CLAUDE_PLUGIN_ROOT/`--event` text (grepped).
- 04-04 expected `DRILL killed=13/13`: now 18/18. Bundle [K] item updated to the fixed tree state (`git checkout ef336ec7 -- <3 paths>`), adds `--chars-only` lines; cherry-pick shas (8 + ef336ec7) all exist as commits.
- Review fixes really applied: seven fix commits present (19792a95 ... ef336ec7); each has a named gate and CR/WR a drill mutant, all passing/killed in my re-run.

## Requirements coverage

| Req | Status | Evidence |
|---|---|---|
| IC-K | ADDRESSED, NOT SATISFIED (correct) | Gate built and proven on GEX44; ledger terminal needs laptop `floor/reference.json` + PRG (owner bundle [K]). REQUIREMENTS `[ ]` and `state.K {}` left untouched; `--pillar K` still FAIL L3. Not ticked, as instructed. No orphaned requirements for phase 4. |

## Prohibitions (judgment tier; NON-AUTHORITATIVE verifier verdicts, all flagged `unverified-prohibition - human review recommended`)

| Prohibition | Verifier reading |
|---|---|
| No exit 0 / WITHIN_BOUND on an unmeasurable comparison | Held: reference_missing, tokens_unmeasured, not_comparable, unparseable window, absent layer all exit 2 in my runs and drill M6/M16/M18 killed |
| Unattributable origin not filed project/harness | Held: real appended prompt = unattributed; uncorrelated hook = unattributed |
| No writes under ~/.claude, no transcript writes, no real claude session | Held by evidence: grep of the gate finds no write/mkdir/unlink on .claude paths; transcript sha256 unchanged; tests use stubs behind a fence; `git diff` shows no change to listing_floor_probe results; I ran no probe |
| No state.K / IC-K tick; GEX44 not presented as frozen reference | Held: verified above |
| No laptop command claimed run | Held: bundle states expected-not-measured |

## Anti-patterns

TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER grep over both tool files: none. Phase touches only 4 non-planning files (gate, test, reference-gex44, bundle, K.md); pre-existing dirty `vault/progress.md` and untracked docs/arch files are outside the phase.

## Advisory / warnings (non-blocking)

- Tokens axis is largely theoretical in real use: the committed reference's prompt digest is the worker's, so only a same-prompt probe session reaches plain `WITHIN_BOUND`; ordinary sessions yield `WITHIN_BOUND_CHARS_ONLY`. Documented in the bundle and K.md.
- Named debt (documented): `tools/` is outside the liveness scanner; after K closes nothing runs `--check` against `reference.json` except the one PRG.
- Laptop-side cherry-pick/tree-state path is unproven (not runnable here).

## Gaps Summary

No gaps. Every roadmap criterion and plan truth is verified against the code and by my own runs. Status is human_needed solely because IC-K's terminal (laptop reference + PRG) and the flagged judgment items require the Owner.

_Verified: 2026-10-04_
_Verifier: Claude (gsd-verifier)_
