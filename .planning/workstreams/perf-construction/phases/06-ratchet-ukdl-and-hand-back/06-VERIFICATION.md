---
phase: 06-ratchet-ukdl-and-hand-back
verified: 2026-11-23T15:00:00Z
status: passed
verdict: passed_with_unknowns  # GSD routes only passed|gaps_found|human_needed; unknowns below stay open
score: 3/3 roadmap success criteria verified on GEX44 (laptop items, scheduler existence, and the s9 red-team UNJUDGED)
verified_head: 027c0fa4
covered_files:
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-01-PLAN.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-01-SUMMARY.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-02-PLAN.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-02-SUMMARY.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-03-PLAN.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-03-SUMMARY.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/HANDOFF.md"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/handoff_check.py"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/inherit_check.py"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/ratchet_connect.py"
  - ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/ukdl_candidate_check.py"
  - "vault/knowledge_base/candidates/perf-construction-20261123.md"
  - "vault/tower/candidates/perf_construction.md"
covered_digest: "v1:sha256:5062d197b592e8ce583477f936d8c194645815ff1eb683a6c851190ce1ca0528"
behavior_unverified: 0
gaps: []
unknowns:
  - "LAPTOP-ONLY: all 12 LP items (LP-01 to LP-12) are UNJUDGED; zero are laptop-judged. How long creation takes on the laptop, which is the Owner's complaint, is UNKNOWN and nothing in the campaign observes it. HANDOFF line 1 says exactly that"
  - "Inheritance is partial by the phase's own measurement: the Phase 3 censoring proof (MX4) and the Phase 5 FLAG_WEAKENED proof (MX5) are defended by no standing gate, only by their own suites that nobody runs on a schedule that anyone found. I re-derived MX4 myself (see Spot-checks). Whether anything schedules the bench-gate row of tools/verify_spp.py is UNKNOWN. Owner decision (11) is open, pick 'leave unwired'"
  - "The five-mutants matrix is one mutant per owner, a spot check; it does not show that every condition in those owners is defended, and the other manifest suites (a5_u6, arm_preflight, gsd_mission_*, hook_boundary) have no mutant at all"
  - "Ratchet is CONNECTED_SCRATCH, live BLOCKED (three ordered reasons). That satisfies 'connected to the real owner, or BLOCKED with reason' only in its BLOCKED-for-live half; no live generation exists, so nothing is actually ratcheted in the Constitutive Baseline store yet. Owner decision (12) is open"
  - "The 'improvement' evidence of the four PROMOTABLE Tower entries is the pass count of each mechanism's own gate suite before and after the fix (24/28 to 28/28, 48/53 to 53/53, 5/9 to 9/9, 41 to 59 gates), not any latency change. The candidate note says so; a promotion would ratchet 'the gate caught the missing behaviour', not a speed gain"
  - "ukdl_candidate_check.py verifies that a cited path exists and the block shape, not what a cited line says. I re-read the cited file:line pointers by hand and they say what the blocks claim (see Truth 1), but that is a one-time reading, not a standing check"
  - "tools/test_s9_redteam.py (111/114) was not run (814 s, forbidden for this verification); UNJUDGED, no clean control run exists. Pre-existing debt, unchanged by name: 56 reachability offenders, tools/test_git_invocation.py 6/7"
human_verification: []
---

# Phase 6: Ratchet, UKDL and hand-back - Verification Report

**Phase goal:** What was proven is inherited; what was not is said plainly.
**Plane:** GEX44 (kobicraft-gex44, Linux, Python 3.12, stdlib only). Every number below was observed by me on this host in this session. The laptop was not measured and nothing here is a laptop result.
**Re-verification:** No, initial verification. Head 027c0fa4 (plans 06-01, 06-02, 06-03 merged). Phase base for the diffs below: 8a699c27 (Phase 5 verification), plus the stated mission bases 4fa606d7 and a0e12830.
**Status: passed_with_unknowns.** The three roadmap success criteria hold on evidence I re-observed. Nothing failed. The unknowns above are not counted as passes.

Method: re-ran every phase-local checker (selftests, `check`, `connect`, `classify`, `manifest`, `matrix --verify-record`), diffed the tree against the three bases, read both candidate files and re-read each cited file:line pointer, scanned the Phase 6 files for laptop numbers and absolute paths, and planted one throw-away mutant (MX4) in a `git archive` copy under /tmp (the repo was not mutated; the copy was removed). SUMMARY.md, 06-EVIDENCE.md and STATE.md were used only to know where to look. `PH` below means `.planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back`.

## Observable Truths (ROADMAP Phase 6 success criteria)

| # | Truth | Status | Evidence (re-observed) |
|---|-------|--------|------------------------|
| 1 | UKDL candidates (HR/PR/Trap) appended to a candidate file, no shared aggregate edited; each with evidence and scope | VERIFIED | `vault/knowledge_base/candidates/perf-construction-20261123.md` exists (new file, 68 lines) with five blocks, each carrying id, kind, statement, evidence pointers, measured, plane, scope (`#CROSS-PROJECT` or `#PP-LOCAL`), an ownership-sweep line and status `CANDIDATE - NOT PROMOTED`. `ukdl_candidate_check.py selftest` = `UKDL_SELFTEST=10/10` (includes a mutant control: with the plane check disabled the missing-plane block is accepted), `check` on the file = `UKDL_CHECK=5/5`. No aggregate edited: `git diff --name-status 8a699c27 HEAD` outside `.planning/` lists exactly two files, both new (`vault/knowledge_base/candidates/perf-construction-20261123.md`, `vault/tower/candidates/perf_construction.md`); `git diff --stat 8a699c27 HEAD -- hooks tools modules vault/config vault/tower/baselines vault/tower/families vault/hard_rules governance wiki vault/knowledge_base/ukdl-universal.md vault/knowledge_base/session_lessons.md vault/benchmarks vault/liveness` is empty. I re-read the cited pointers: `tools/bench_all.py:117-120` (P03 comment), `:55`, `modules/capability_runtime/construction_metrology.py:61` (`CENSORED_STATES`), `vault/knowledge_base/ukdl-universal.md:7608` (`HR-INTENT-FIDELITY-IS-DONE-CRITERION-001`), `skills/real-context-reachability/SKILL.md:228` ("Absent is not zero"), `skills/develop-here-prove-there/SKILL.md:14` (plane doctrine), `02-CONTEXT.md:18` (nine and six bench sites), `02-01-T3.red.txt:35` (24/28) and `green.txt:34` (28/28), `04-02-mutants.txt:29` and `:38` (the window-kept and forged-GREEN messages), `03-03-live.txt:13` (`TTFMC N_total=218 measured=18 censored=5`), `session_resilience_05...:188` ("unknown is not green"), `05-02-SUMMARY.md:31` and `:85`, `tools/test_hook_critical_path.py:177`: each says what the block claims. Honesty of kind: only one candidate is drafted as NEW; four are one-line EXTEND_EXISTING_OWNER pointers naming the existing owner with the sweep patterns and hit counts; no HR is claimed; one candidate was dropped for lack of a measured cost and the file says why. |
| 2 | Ratchet entry connected to the real owner from Phase 1, or BLOCKED with reason | VERIFIED (CONNECTED_SCRATCH; live BLOCKED) | Phase 1 names `modules/tower/ratchet.py` as the Constitutive Baseline Ratchet owner (`01-VERIFICATION.md:29`, `01-02-SUMMARY.md:22`); the file exists. `ratchet_connect.py selftest` = `RATCHET_SELFTEST=12/12`, including the owner's refusal poles driven from its own code (missing negative control, same-run reuse, empty authority), tamper detection, regression detection, a mutant control (with `evidence_problems` disabled the empty-control entry is accepted, so the instrument can say no), and `V-RAT-SCRATCH-ROOT` (live root, a path inside it and a symlink to it exit 2). My own run of `ratchet_connect.py connect --entries ratchet-entries.json`: `RATCHET_STATUS=CONNECTED_SCRATCH LIVE=BLOCKED generations=4 chain_ok=True promotable=4/5`; four entries `origin=VERIFIED check=PASS evidence=ok`, the plane entry `NOT_PROMOTABLE evidence=missing: improvement, negative_controls, before, after` (not rounded up); `LIVE_TREE_CLEAN=yes`; `git status --short vault/tower vault/knowledge_base` empty and the `vault/tower/baselines` + `families` index hash identical before and after. BLOCKED reasons, in order: no family reaches this work (I re-ran `classify`: `CLASSIFY_NO_FAMILY=4/4 CONTROL_REACHED=web_surface`, so the instrument can say yes), a live promotion needs an Owner authority the unattended run does not have, one mission is not a second independent domain (precedent `ecommerce_storefront.md`). `vault/tower/candidates/perf_construction.md` lists five entries with their status and the owner-side promotion commands. |
| 3 | HANDOFF.md: owner summary, engineering handoff, laptop-only checklist, known unknowns, exact next task | VERIFIED | `handoff_check.py selftest` = `HANDOFF_SELFTEST=13/13` (mutant control: with the number comparison disabled the same wrong INVENTORY lines are accepted). `handoff_check.py check HANDOFF.md` = `HANDOFF_CHECK=PASS`: first line, five sections in order (Owner summary, Engineering handoff, Laptop-only checklist, Known unknowns, Exact next task), INVENTORY line and prose counts equal the recomputed inventory (unknowns 4,6,6,8,7; lp=12; owner_decisions=13), 12 LP rows equal the phase-file set, no forbidden claim, every backticked path exists and none is absolute, one task, one command, one record, one falsifier. First line of the file, by `od -c`: `Creation speed on the laptop: UNKNOWN` plus a newline, nothing else. Exact next task is LP-05 with one command; `tools/construction_metrology_report.py --help` confirms the flags it uses (`--root --max-files --max-bytes --seed`) exist. |

**Score:** 3/3 criteria verified; 0 present-but-behavior-unverified truths.

### Cross-cutting facts re-observed

| Fact | Result |
|------|--------|
| No shared UKDL aggregate edited | confirmed: empty diff on `ukdl-universal.md`, `session_lessons.md`, `vault/hard_rules`, `governance`, `wiki` since 8a699c27 |
| `hooks/` unchanged | `git diff --stat 4fa606d7 HEAD -- hooks/` empty and `git diff --stat a0e12830 HEAD -- hooks/` empty |
| Live Tower baselines/families unchanged | `git diff --stat 4fa606d7 HEAD -- vault/tower/baselines vault/tower/families` empty |
| tools, modules, vault/config unchanged by Phase 6 | `git diff 8a699c27 HEAD` on them is empty (the 18-path campaign diff against a0e12830 is Phase 2-5 work plus the two Phase 6 candidate files, matching the HANDOFF list: 12 tools/modules files, 2 config JSONs, 1 liveness registry, 1 spec, 2 candidate files) |
| Ledger and resource-floors hashes | `cef10a59...` and `54a5f2af...` SAME before/after the manifest run (phase tool, and `handoff_check.py tree`) |
| HANDOFF first line literal | yes (see Truth 3) |
| No laptop number anywhere | grep of HANDOFF, 06-EVIDENCE, 06-INHERITANCE and both candidate files for a number near "laptop", for `1563`, `275 MB`, `28 claude`: empty. LP laptop-value slots are all `UNJUDGED`; the meta-analysis states 0 of 12 laptop-judged |
| 12 LP items present | 12 distinct `LP-nn` in HANDOFF; every row's source pointer (`file:line`) resolves to the LP-nn text in the Phase 1-5 evidence files (re-read all 12); no `NEW:` record path exists in the tree |
| No absolute home path | grep for the host home path and the Windows user path in Phase 6 md, py, records and both candidate files hits only two detector patterns inside `inherit_check.py:609` and `handoff_check.py:674` |
| No TBD/FIXME/XXX | grep over Phase 6 .py, .md and both candidate files: empty |

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `PH/inherit_check.py` | manifest + mutant matrix, closed verdict set | VERIFIED | 638 lines; `INHERIT_SELFTEST=9/9`; manifest re-run below |
| `PH/06-INHERITANCE.md` | inheritance map | VERIFIED | `matrix --verify-record` returns `MATRIX_RECORD_OK verdicts=MX1:ENFORCED,MX2:ENFORCED,MX3:ENFORCED,MX4:OWN_SUITE_ONLY,MX5:OWN_SUITE_ONLY`; the map's table equals the record |
| `PH/ratchet_connect.py`, `PH/ratchet-entries.json` | scratch connection to the real owner | VERIFIED | 555 lines; 12/12; `connect` re-run |
| `PH/ukdl_candidate_check.py` | candidate shape check | VERIFIED | 284 lines; 10/10 and 5/5 |
| `PH/handoff_check.py` | HANDOFF inventory and check | VERIFIED | 739 lines; 13/13; `check` PASS |
| `PH/HANDOFF.md` | five-section hand-back | VERIFIED | 99 lines |
| `vault/knowledge_base/candidates/perf-construction-20261123.md` | UKDL candidates | VERIFIED | new, append-only, 5 blocks |
| `vault/tower/candidates/perf_construction.md` | Tower candidate note | VERIFIED | new, 54 lines, 5 entries (4 promotable-under-Owner, 1 not) |
| `PH/records/*` | recorded runs | VERIFIED | 15 record files; the matrix record is parsed by the tool; manifest and `connect` numbers I re-ran equal them |

## Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `ratchet_connect.py` | `modules/tower/ratchet.py` (`promote_with_evidence`, `verify_chain`), `baselines.py`, `checks.py` | real import on a scratch root refused when it resolves into `vault/tower/baselines` | WIRED (connect run prints 4 generations, chain_ok=True) |
| `ratchet_connect.py classify` | `modules.tower.families.classify_prompt` | real call, with a positive control prompt | WIRED |
| `inherit_check.py manifest` | Phase 2-5 standing gates | subprocess with process-group timeout, count compared to the recorded marker | WIRED (14 judged) |
| `inherit_check.py matrix` | `tools/test_bench_gate.py` + owning suites on a scratch copy | one mutant per owner after a passing control | WIRED (record verified; MX4 independently reproduced) |
| `handoff_check.py` | phase VERIFICATION `unknowns:` lists, LP ids of the EVIDENCE files, STATE.md decisions, `git diff --name-only a0e12830 <head>` | inventory recomputed, not typed | WIRED (`check` PASS) |
| Tower candidate note | `ratchet-entries.json` and records | entries identical in the `connect` output | WIRED |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| HANDOFF INVENTORY | unknowns, lp, owner_decisions, changed_files | phase files and `git diff` | yes: today the inventory reads changed_files=184 at head 027c0fa41986; the document pins head=823d46157ea2 and its 179, and `check` accepts that because it recomputes at the stated head | FLOWING (see Anti-Patterns: stale-by-design count) |
| Tower entry evidence | before/after, negative control rc, reuse pointer | existing record files via `ratchet_connect.py fill` | yes, re-derived on each `connect` | FLOWING |
| Manifest rows | observed marker count | live suite output | yes (53/53, 24/24, 17/17, 17/17, 21/21, 38/38, 134/134, 7/7) | FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Inheritance checker | `python3 -I PH/inherit_check.py selftest` | `INHERIT_SELFTEST=9/9`, rc 0 | PASS |
| Ratchet connector | `python3 -I PH/ratchet_connect.py selftest` | `RATCHET_SELFTEST=12/12`, rc 0 | PASS |
| UKDL checker | `python3 -I PH/ukdl_candidate_check.py selftest` and `check <candidate file>` | `UKDL_SELFTEST=10/10`; `UKDL_CHECK=5/5` | PASS |
| HANDOFF checker | `python3 -I PH/handoff_check.py selftest`, `check PH/HANDOFF.md` | `HANDOFF_SELFTEST=13/13`; `HANDOFF_CHECK=PASS` | PASS |
| Ratchet connection | `python3 -I PH/ratchet_connect.py connect --entries PH/ratchet-entries.json` | `CONNECTED_SCRATCH LIVE=BLOCKED generations=4 chain_ok=True promotable=4/5`, `LIVE_TREE_CLEAN=yes`, rc 0 | PASS |
| No family reaches the work | `python3 -I PH/ratchet_connect.py classify` | `CLASSIFY_NO_FAMILY=4/4 CONTROL_REACHED=web_surface` | PASS |
| Standing gates of Phases 2-5 | `python3 -I PH/inherit_check.py manifest` | `INHERIT_JUDGED=14/15`, `INHERIT_PASS=14/14`, `SKIPPED=1`, `NOT_JUDGED=0`; markers 53/53, 24/24, 17/17, 17/17, 21/21, 38/38, 134/134, 7/7; git_invocation 6/7 and reachability 56 offenders both BASELINE_MATCH (not PASS); s9_redteam SKIPPED_BY_POLICY | PASS (14 judged, none failed) |
| Matrix record | `python3 -I PH/inherit_check.py matrix --verify-record PH/records/06-01-T3.matrix.txt` | `MATRIX_RECORD_OK` with the five verdicts above | PASS |
| My own mutant, MX4 (not the phase's run) | `git archive HEAD` subset to /tmp, `CENSORED_STATES` with `"FAILED"` removed; `test_bench_gate.py` then `test_construction_metrology.py` | control: `BENCH_GATE_PASS=24/24`, `METRO_PASS=38/38`. Mutant: standing gate still `24/24` (not caught); metrology suite fails `V-METRO-CONTRACT-MATCHES-CODE`, `V-METRO-STATE-FAILED`, `V-METRO-POLE-FAILED`, `V-METRO-ONLY-MEASURED-IN-VALUES`. So "Phase 3 is OWN_SUITE_ONLY" is true; repo not mutated | PASS |
| Tree check at today's tree | `python3 -I PH/handoff_check.py tree PH/records/06-03-T3.final-gates.txt` | `tools_modules_hooks_vault_config_clean PASS`, both hashes SAME, but `whole_tree_only_allowed_paths FAIL` (outside: the uncommitted `ROADMAP.md` edit and the untracked `.claude/worktrees/` of the orchestrator), line `HANDOFF_TREE=FAIL 1` | NOT A PHASE DEFECT: those paths are the orchestrator's live edits made after 06-03; the committed record `06-03-T3.tree.txt` is the phase's own observation. Recorded so it is neither read as a pass nor hidden |
| s9 red-team | not run (forbidden for this verification) | UNJUDGED | SKIPPED |

## Probe Execution

No phase-declared `probe-*.sh`. SKIPPED.

## Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
|-------------|--------|-------------|--------|----------|
| PERF-06 | 06-01, 06-02, 06-03 | ratchet connection, UKDL candidates, hand-back | SATISFIED on GEX44 | truths 1-3; scratch-only ratchet and laptop items UNJUDGED |

No orphaned requirement IDs mapped to Phase 6 in REQUIREMENTS.md (PERF-06 only).

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (Phase 6 files) | - | TBD / FIXME / XXX grep | none | empty |
| `vault/tower/candidates/perf_construction.md` | entry 4 | `perf_construction-unchanged-gate-text-is-not-shown` is labelled PROMOTABLE_UNDER_OWNER_AUTHORITY while its own row admits it is the weakest ("an executor interpretation of a gap in the G4 wording, no real pair with drifting gate text was recorded"), and the sibling UKDL file DROPPED the same idea for "no measured cost" | Warning | HANDOFF and 06-EVIDENCE say "four of five promotable"; that is true to the owner's `evidence_problems` (which checks the shape of the evidence) but overstates how ready entry 4 is. An Owner promoting all four would ratchet a rule the phase itself did not trust. Disclosed in the row, not in HANDOFF section 1 item 8 |
| `PH/HANDOFF.md` | INVENTORY line | `changed_files=179 head=823d46157ea2` is stale against HEAD (184 at 027c0fa41986) | Info | by design (pinned to the stated head so the commit adding the document does not move its own count) and stated in the document; `check` recomputes at that head |
| `PH/ukdl_candidate_check.py` | - | path-exists check, not line-content check | Info | disclosed; I re-read the pointers by hand and they hold |

## Human Verification Required

None blocking on this host. The 12 laptop items are listed as unknowns with a procedure, record path and falsifier each, not as items waiting for a human on GEX44.

## Gaps Summary

No gaps. The phase delivers an inheritance proof that is measured and says where it fails (two of five proofs defended only by their own suite, which I reproduced for one), a ratchet connection that runs the real owner on a scratch root and says why live is blocked, five UKDL candidates in an append-only file with no aggregate touched, and a HANDOFF whose first line and every count I could re-derive hold. What it does not deliver, and says so: any laptop observation (0 of 12 laptop-judged), a live ratchet generation, a standing gate for Phases 3 and 5, and a clean s9 red-team control. The one soft spot is the overstated "four promotable" (entry 4 is weak by its own admission), recorded above as a Warning, not a gap, because the candidate note discloses it.

---

_Verified: 2026-11-23_
_Verifier: Claude (gsd-verifier)_
