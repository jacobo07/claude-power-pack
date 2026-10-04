---
phase: 05-offline-replay-and-owner-bundle
verified: 2026-10-04T02:30:00Z
status: human_needed
score: 15/15 must-haves verified
behavior_unverified: 0
overrides_applied: 0
plane: gex44 (instrument, gates, scratch-clone sync replay); laptop (KME-L run, quota decision: Owner)
head_verified: 561eb249 (083efdc7 plus a STATE.md-only docs commit; no code differs)
requirement: IC-L addressed, NOT satisfied (ledger terminal needs the KME-L ranking file and/or the Owner decision; state.L = {}, IC-L stays unticked)
human_verification:
  - "[L] KME-L ranking (owner bundle row 10, [L]#1): on the laptop run `python wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root C:\\Users\\User\\.claude\\projects` after the Laptop code sync and the Phase 3 population proof, commit the printed L-KME-L file; and the live champion/challenger quota decision (row 11, [L]#2) in the Owner's own words as evidence/L-owner-decision.md. IC-L closes only through these."
  - "Phase 5 review-fix judgement (owner bundle row to add): accept or amend the identity and policy decisions the gates cannot judge: CR-01/WR-01/WR-02 R4 identity rule (bundle under any spelling, byte copy, mission-written file refused; exemption by the literal L-owner-decision*.md name), WR-03 R3-L cross-check of front matter against the json block, WR-04 terminal only at rollover growth 100000, WR-06 retries and rereads keyed per thread, IN-01 dense ranks for equal figures (05-REVIEW-FIX.md marks them requires human verification)"
  - "Phase 5 judgment-tier prohibitions (owner bundle row to add): confirm the IC-L prohibitions held (no number for an UNMEASURED candidate, no figure presented as a saving, no ledger/IC-L/claude-session/~/.claude write, smoke never presented as KME-L, no Owner decision invented, no laptop run claimed); verifier verdicts below are non-authoritative LLM-judge verdicts"
---

# Phase 5: Offline replay and owner bundle -- Verification Report

**Phase goal:** offline replay ranks the live experiments; every Owner item is in one bundle.
**Verified:** 2026-10-04 (GEX44, Linux, python3). **Mode:** initial (no previous VERIFICATION). **Status: human_needed.**
No gap blocks the goal on this plane. What is left is the laptop-plane KME-L run and the Owner's quota decision (both
already in the bundle) plus two judgement items the gates cannot make.

## Gates re-run by the verifier (foreground, this worktree, HEAD 561eb249; code identical to 083efdc7)

| Command | Result |
|---|---|
| `python3 tools/test_kme_replay.py` | `KMER_PASS=45/45 skipped=0 inconclusive=0` |
| `python3 tools/test_kme_replay.py --drill` | `DRILL killed=19/19`, `DRILL-CLEAN-AFTER-MUTANTS 42/42` |
| `python3 tools/test_kme_pillars.py` | `KMEP_PASS=89/89` (and `--drill` `killed=20/20`, 84/84 clean) |
| `python3 tools/test_floor_regression_gate.py` | `FLOOR_PASS=67/67` |
| `python3 tools/test_incremental_cognition_program.py --pillar L` | `FAIL L3 L: no terminal disposition`, exit 1 (expected) |
| `python3 tools/test_incremental_cognition_program.py --selftest` | `ICP_SELFTEST=PASS` |
| Smoke reproduced independently (`--out-dir /tmp`, same command as the committed file) | ranking section byte-identical to `measurements/L-KME-G-2026-10-04.md` |
| Laptop code sync replayed literally in a scratch clone at `18e928af` (fetch from this worktree) | fetched tip `561eb249`, ancestor of pin `f3cdc79b` exit 0, status empty, checkout 0, commit 0; the four suites exit 0: `KMEP 89/89`, `KMER 44/44 skipped=1`, `FLOOR 67/67`, `ICP_SELFTEST=PASS` |

## Observable truths (derived from the four plans' must_haves; the ROADMAP lists only the goal)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | `kme_replay.py rank` scans once through `kme_pillars`' run context and ranks three candidates on one weighted denominator, as upper bounds, highest first | VERIFIED | `rank_result` reuses `kp._prepare/_resolve/_match`; one `denominator_for`; smoke ranking late_rollover 8,773,728.0 > retries 2,520.633 > rereads 0.0, shares over 54,899,558.8; V-KMER-RANK-ORDER, -ONE-DENOMINATOR green; independent rerun identical |
| 2 | identical_rereads is the Phase 3 E observer, not a fork | VERIFIED | `RereadObserver(kp.EObserver)`; V-KMER-REREADS-EQUALS-E green. Superseded form: WR-06 splits state per thread (identical to E when no inline sidechain lines) and WR-05 rounds the entry figure, so the plan's literal "equals `weighted_interval[1]`" now reads "equals it rounded to 6 decimals" |
| 3 | An unobserved candidate is UNMEASURED with a named reason, never a number (0 included); an observed candidate with no events is a ranked measured zero | VERIFIED | `candidate_status`, `split_ranking`; V-KMER-UNMEASURED-NEVER-ZERO green; rereads 0.0 is ranked (events 0 shown), kill by drill |
| 4 | Contract: exit 0 / 3 / 2, deterministic ties, drifted population or unlocated cutoff makes all UNMEASURED | VERIFIED | `main` returns `EXIT_UNMEASURED` iff unranked; V-KMER-RANK-TIE-DETERMINISTIC, -CLI-USAGE, -UNTIL-AUTO green. SUPERSEDED by IN-01: ties keep candidate order but share one dense rank (4,4,4 -> 1,1,1) and stdout labels `upper_bound_share=` |
| 5 | Every ranked entry is an upper bound (`saving_status upper_bound`, `displacement unknown`) read against 3 % on the bound | VERIFIED | `rank_result` sets both on every entry; V-KMER-UPPER-ONLY. SUPERSEDED by WR-05: entries carry only `upper_bound_weighted` / `upper_bound_share` (6 decimals); `weighted_lo` / `weighted_interval` no longer emitted (they bounded nothing) |
| 6 | `terminal_evidence` true only for a KME-L primary, exact population, committed frozen source, nothing unranked | VERIFIED | `terminal_ok`; V-KMER-TERMINAL-EVIDENCE. EXTENDED by WR-04: also requires `rollover_growth == 100000` (V-KMER-ROLLOVER-GROWTH-PINNED; at G=1e9 the file is primary but not terminal) |
| 7 | KME-G smoke committed: plane gex44, role smoke, terminal_evidence false, population exact, exact `command:`; source trees unchanged | VERIFIED | front matter of `L-KME-G-2026-10-04.md` (13 sessions, 1322 calls, all deltas 0, frozen_source sha 38493644...); my rerun read the same roots read-only (V-KMER-READ-ONLY green) |
| 8 | No transcript content, secret or raw read path in the file or stdout; no write into a scanned corpus or `~/.claude/**` | VERIFIED | V-KMER-NO-SECRET, -NO-RAW-PATHS (IN-02 digests `path_sha256_12`), -READ-ONLY, -OUT-DIR-INSIDE-ROOT, -NO-OVERWRITE green. Committed file holds `top_paths: []` and only sanitiser signatures (`git show`, `git log`, `ExitWorktree`); the two `/home/kobii` hits are the recorded `--root` arguments. Residual (named by the fixer): `cmd_signature` from Phase 3 can keep a path token as a command's second word |
| 9 | `kme_pillars.py` changed only by the additive `observer_factories` keyword | VERIFIED | `git diff 6af1b5e5~1 HEAD -- wiki/tools/kme_pillars.py` = 5 changed lines, all the keyword; suite 89/89, drill 20/20 |
| 10 | Done-gate wrapper covers L: R3-L refuses smoke, forged and inconsistent ranking files; R4 refuses the owner bundle as an `owner_decision` | VERIFIED | `kmer_ranking_problems` run by me on a hand-typed file: refused (`no kmer-json block`); selftest `V-ICP-R3-L-RANKING-CHECKED` (15 forgeries), `-CONSISTENT-ACCEPTED`, `-GROWTH-PINNED`, `V-ICP-R4-IDENTITY` (19 poles) green; mutants killed. SUPERSEDED/HARDENED: R4 is now identity (samefile, spelled tail, drive/case fold, byte copy, mission-written files), not the plan's normalised-path compare (CR-01, WR-01, WR-02); R3-L now cross-checks front matter against the json block (WR-03) |
| 11 | Bundle `## Phase 5` has NOT RUNNABLE HERE and two `[L]` items; the command parses with kme_replay's own parser | VERIFIED | bundle lines 397-429; V-KMER-BUNDLE-ARGV-PARSES green (1 line parsed, controls bad 2/2, good 0/0) |
| 12 | `## Laptop code sync` guarded and proven; Phase 3 / Phase 4 correction lines inserted; bundle insert-only | VERIFIED | replay above (all four suites exit 0 at the tip); `Phase 5 correction` paragraphs at bundle lines 189 and 305; `git diff --numstat 6af1b5e5~1 HEAD` = +129 / -0. Counts quoted inside the bundle are stale, see Warnings |
| 13 | Summary table (24 rows) covers every `[X]` item, the sync step, every pending UAT test (01..05) and UAT-less human_verification; the gate discovers, never lists, and can go red | VERIFIED (with a blind spot, W2) | In a scratch clone at HEAD: delete row 14 -> `FAIL ... missing row for [B]#1`; add a `[Z]` item with no row -> `FAIL ... missing row for [Z]#1`; alter a command only in the table -> `FAIL ... unknown command in row 10`; add a pending `### 4.` UAT test -> `FAIL V-KMER-BUNDLE-SUMMARY-UAT ... missing row for UAT 04#4`; restored -> 45/45 |
| 14 | `evidence/L.md` has the frozen rule, models and thresholds, commands with outputs, bundle consolidation, liveness, shas, Product Delta, Intelligence Delta, named debts, `Status: OPEN` | VERIFIED | all sections present; all six LF sha256 values recomputed and match the current files; figures match the smoke |
| 15 | Ledger `state.L` stays `{}`, IC-L stays unticked, `--pillar L` exit 1, no `L-owner-decision` file, no invented decision | VERIFIED | `ledger.json` state.L = `{}`, last touched at the P0 freeze `18e928af`; REQUIREMENTS.md line 23 `[ ]`; `--pillar L` exit 1; no decision file in `evidence/`; every SUMMARY has `requirements-completed: []` |

**Score:** 15/15 truths verified; 0 present-but-behavior-unverified. IC-L is accounted for, not satisfied (see below).

## IC-L requirement handling

IC-L ("replay ranks live experiments; live runs need quota") is satisfied only by its ledger terminal. On GEX44 no
terminal can exist: the KME-L corpus is laptop-plane, and no Owner decision was recorded. The instrument is built, tested
from both poles and smoke-run (KME-G, role smoke); the KME-L run and the quota decision are bundle rows 10 and 11. IC-L
correctly stays unticked; `requirements.mark-complete` was not called.

## Where review fixes superseded plan truths (judged in their light)

- 05-01 ranked-entry shape: `weighted_lo` / `weighted_interval` removed (WR-05); rank numbers dense, order unchanged (IN-01).
- 05-01 retries/rereads "per transcript file": now per thread inside a file; parallel identical tool uses are not a retry (WR-06). Residency of an inline-sidechain event still counts the whole file, so it is an upper figure; the committed corpus has 0 such sessions so the smoke is unchanged.
- 05-02 terminal rule: adds the rollover growth pin (WR-04).
- 05-03 R3-L and R4: R3-L now cross-checks front matter against the json block and the candidate id set (WR-03); R4 became identity-based (CR-01, WR-01, WR-02). Original poles still pass.
- Ranking file no longer carries raw read paths (IN-02); L docstrings say which L terminals need a ranking file (IN-03, executed by `V-ICP-R3-L-NEEDS-RANKING-TABLE`).
All ten fixes are present in the code at HEAD and each has its named gate and mutant in the green suites above.

## Warnings (non-blocking; none makes a truth FAILED)

- **W1 stale counts in the bundle.** `## Laptop code sync` still says `KMER_PASS=39/39`, then (Phase 5 update) `40/40 skipped=1` at the freeze and `41/41` on the worktree. The replay now gives `44/44 skipped=1` in a freeze clone and `45/45` in the worktree (the review fixes added gates 42-45). The exit codes, the guard and the paths are right; a laptop Owner comparing counts will see a mismatch. Not gate-checked. Fix: insert one line in the sync section with the current counts (insert-only).
- **W2 blind spot in the VER discovery of V-KMER-BUNDLE-SUMMARY-UAT.** `ver_entries` stops at the first line of a `human_verification` item that is not `- ...`, so the canonical multi-key list (`- test:` / `expected:` / `why_human:`) yields only `VER NN#1` (verified: a three-entry file returns `['VER 05#1']`). Today it is harmless (phase 1 uses one string per entry; phases 2-4 have a UAT, and VER is ignored then). Entries 2..n of a multi-key VERIFICATION would escape the "every Owner item has a row" gate. This file uses one string per entry on purpose, so it is fully counted. Recommended: fix `ver_entries` to count items with nested keys.
- **W3 gate consequence of this file.** With `status: human_needed` and no 05-UAT.md, `V-KMER-BUNDLE-SUMMARY-UAT` will demand rows `VER 05#1`, `VER 05#2`, `VER 05#3` in the bundle summary (or, if a 05-UAT.md is generated from these items, rows for its pending tests). VER 05#1 can be cited by the existing rows 10 and 11; VER 05#2 and #3 need new rows (cf. rows 23 and 24 for phase 4). This is the gate working as designed; the orchestrator should insert the rows (insert-only) with the same commit as this file, or KMER goes 44/45.
- **W4 one Owner-decision-shaped line outside the bundle.** STATE.md "Session Continuity" ends with "obligation 5 -- arm gsd_mission.py arm --workstream incremental-cognition (12/24h), needs Owner go on WHERE (local RAM swings 0.6-8 GB; GEX44 own clone is the alternative)". It is an older session paragraph (this run already executes on GEX44) and likely moot, but nothing says so and it is not a bundle row. The Owner should confirm it is resolved or the orchestrator should delete the stale paragraph. UNCERTAIN, not a gap.
- **W5 named debt carried (from 05-REVIEW-FIX.md, accepted as stated).** The D..I terminal gate trusts self-asserted front matter (the WR-03 weakness is closed for L only); `L-owner-decision*.md` exemption is by name, so a mission-written file given that name is accepted; the Windows spellings of R4 are proven as strings on Linux only.

## Prohibitions (judgment-tier, non-authoritative LLM-judge verdicts; unverified-prohibition, human review recommended)

| IC-L prohibition | Verdict | Basis |
|---|---|---|
| no number (0 included) for a missing/partly observed candidate | held | `candidate_status` / `split_ranking`; gate and drill M-mutants killed |
| no figure presented as a saving | held | `saving_status upper_bound`, `displacement unknown`; WR-05 removed the misleading low side |
| only the additive `observer_factories` change to kme_pillars; no ledger / IC-L / claude session / `~/.claude` write | held | diff of 5 lines; ledger untouched since `18e928af`; no session started by this verification either |
| KME-G smoke never presented as KME-L or terminal | held | role smoke, terminal false, bundle quotes it "smoke, plane gex44, never terminal" |
| no unmeasured candidate ranked; one denominator for all | held | single `denominator_for`; V-KMER-ONE-DENOMINATOR |
| no write into scanned corpora, no transcript content emitted | held | V-KMER-READ-ONLY, -NO-SECRET, -NO-RAW-PATHS |
| no Owner decision recorded or invented; no laptop run claimed | held | no `L-owner-decision` file; bundle says NOT RUNNABLE HERE; evidence says proven to parse / GEX44 scratch clone only |
| no summary row without a source, no item without a row, no table command not verbatim in the body | held | gate poles above |
| insert-only bundle; no live-loaded file in the sync paths | held | 0 removed lines; sync paths are tool, test, measurement, bundle and FROZEN_AT files only |

## Anti-patterns

No `TBD` / `FIXME` / `XXX` found in the phase's files (`wiki/tools/kme_replay.py`, `tools/test_kme_replay.py`,
`tools/test_incremental_cognition_program.py`) by the standard scan; no stubs on the data path (ranking figures trace to
real transcript scans and reproduce on rerun).

## Human verification required

1. **KME-L ranking and the quota decision** (bundle rows 10 and 11): laptop plane; needed to give IC-L its terminal. Expected: `L-KME-L-<date>.md` with all three candidates measured (or UNMEASURED with reasons) and population `exact`; the Owner's decision in their own words as `evidence/L-owner-decision.md`. Why human: the corpus and the quota decision are not on GEX44.
2. **Review-fix judgement** (CR-01, WR-01..04, WR-06, IN-01): accept or amend the identity rules, the growth pin and the dense-rank reading. Why human: they are decisions about what counts as the Owner's answer and as terminal evidence; the gates prove the code does what was decided, not that it was the right decision.
3. **Judgment-tier prohibition confirmation:** accept or reject the verdicts in the table above. Why human: judge verdicts are non-authoritative.

## Gaps Summary

None blocking. Phase 5 delivers an instrument that ranks the three live experiments from offline transcripts as upper
bounds on one named denominator (smoke on KME-G reproduced here), a done-gate that will not let a hand-written file or the
bundle itself stand in for the KME-L ranking or the Owner's decision, and one bundle whose summary table is covered by a
gate that turns red (demonstrated four ways) when an item or pending check lacks a row. IC-L stays open by design.

---

_Verified: 2026-10-04_
_Verifier: Claude (gsd-verifier)_
