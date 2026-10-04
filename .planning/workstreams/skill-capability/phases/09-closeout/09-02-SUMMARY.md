---
phase: 09-closeout
plan: 02
subsystem: skill-capability program closeout
status: complete
tags: [closeout, reviews, ukdl, cbr, deltas, ledger, pillar-N, gex44]
requires: [09-01 (tools/test_skill_capability_prefinal.py at HEAD)]
provides:
  - vault/programs/skill-capability/reviews/ukdl.md (ledger reviews.ukdl.file, CE L8)
  - vault/programs/skill-capability/reviews/cbr.md (ledger reviews.cbr.file, CE L8)
  - ledger deltas.product (14) and deltas.intelligence (15)
affects: [09-03 (LAPTOP-CLOSEOUT.md and the gex44 record are now the only missing gate inputs)]
tech-stack:
  added: []
  patterns: [two-line text replacement of the ledger with byte-identity, FROZEN_AT, retained and state assertions; pre-check with the gate's own check_* functions before commit]
key-files:
  created: [vault/programs/skill-capability/reviews/ukdl.md, vault/programs/skill-capability/reviews/cbr.md]
  modified: [vault/programs/skill-capability/ledger.json]
decisions:
  - "12 UKDL candidates (the six D-01 traps as UKDL-SC-01..06, then six more), kept in the program's own file; ukdl-universal.md was never opened"
  - "IN-04 is recorded as an intelligence delta on pillar J: a known limit, not a failure"
  - "Pillar N appears in deltas too (the pre-final check; the stale CE pin) besides the required A..M"
metrics:
  duration: ~6 min
  completed: 2026-10-04
plan_head_before: c13cec897dc8699ee909cba5c93d07b22b48577f
actuals:
  tokens: 6900    # chars/4 over the realized diff c13cec89..f33d4a72 (27595 chars)
  tasks: 2
  commits: 3      # git rev-list --count c13cec89..HEAD once this SUMMARY lands: 2 task commits + 1 docs
---

# Phase 9 Plan 02: closeout reviews and deltas Summary

The program's CE L8 inputs now exist and are committed: 12 sourced UKDL candidates in `reviews/ukdl.md`, a 14-row case-based review in `reviews/cbr.md`, and ledger `reviews` + `deltas` (14 product, 15 intelligence, every pillar A..N named). Only the two `reviews`/`deltas` lines of the ledger changed. On HEAD f33d4a72 the gex44 pre-final gate's only failures are the three V-PF-CLOSEOUT-* checks, which 09-03 owns.

Host: gex44 (kobicraft-gex44), worktree sc-run, branch mission/skill-capability-run. BASE c13cec897dc8699ee909cba5c93d07b22b48577f. Not pushed.

## Commits
- `9653c922` docs(09-02): UKDL candidates learned in the skill-capability run (CE L8). Touches only reviews/ukdl.md.
- `f33d4a72` docs(09-02): case-based review and ledger reviews/deltas (CE L8). Touches only reviews/cbr.md and ledger.json.
- the docs(09-02) summary commit carrying this file.

`git log -1 --format=%s` and `--name-only` were checked after each commit. `git diff --name-only c13cec89 f33d4a72` lists exactly the three program files.

## UKDL candidates (reviews/ukdl.md)
| id | title | source |
|---|---|---|
| 01 | git options placed after `--` are read as pathspecs | 01-REVIEW.md:62, hooks/doctrine_cards.js |
| 02 | a verdict must depend on every provenance clause it prints beside | 02-REVIEW.md:34, 03-REVIEW.md:82 |
| 03 | zero, empty or absent input is UNMEASURED, never a reading | 02-REVIEW.md:46, 04-REVIEW.md:46 |
| 04 | a row without a usable timestamp is UNMEASURED, not "not delivered" | 03-01-PLAN.md:379 (A-1, checker W1), 03-REVIEW.md:63 |
| 05 | a gate re-run on another machine must read only committed blobs | 04-REVIEW.md:131 |
| 06 | files written by hooks must not ride a program commit | STATE.md:58 |
| 07 | a dismissal in rendered prose must use the gate's own verdict rule | 07-REVIEW.md:53, tools/test_contribution_verdict.py |
| 08 | a normalisation drill must go red when the normalisation is removed | 04-REVIEW.md:96, tools/test_skill_drift.py |
| 09 | a key added after a block-scalar value can be swallowed by a hand-rolled reader | 08-REVIEW.md:164, tools/skill_creation_gate.py, modules/skill_router/skill_index.py |
| 10 | a pin on "not landed yet" goes stale the moment its subject lands | STATE.md:48, tools/test_skill_capability_program.py |
| 11 | an isolation sentinel can go stale between dispatches | STATE.md:61 |
| 12 | a push refused by a hook is an Owner decision, not something to retry | STATE.md:57 |

## CBR surprise column, in brief
A: a sixth deny after the freeze, reported beside D-CARD; three git-128 rows came from a test fixture. B: K4 cut 205 listing chars while startup tokens rose +2105; the first verdict function ignored DENOM-MATCH. C: recall 4/7 on window F; the untimed-row rule cut both ways. D: 9 gex44 skills are high criticality with coverage none, 0 in the repo plane. E: the regrade left an authoritative effect of 0; CR-01 showed the C-fixed 2/2 is separable in 8 sessions (Owner decision). F: one dedup group, saving UNMEASURED; the upper-bound gap was closed and re-verified 18/18. G: population of 2 cards; a second named skill escaped G until CR-01 was fixed. H: the one DRIFT is 4 .ps1 scripts that a SKILL.md-only compare cannot see. I: 75 vs 64 offenders is a plane difference. J: the validator whitelist forced `metadata:` nesting, which met the block-scalar reader; IN-04. K: the no-router sweep hit 0 with live controls. L: absent by name only. M: both savings are unmeasured upper bounds. N: open on gex44 by design.

## Deltas
- product: 14 entries, pillars A, B, C, D, E, F, G, H, J, I, K, L, M, N.
- intelligence: 15 entries, pillars A, B, C, D, E, F, G, H, I, J (2, including IN-04), K, L, M, N.
- Every evidence path exists at HEAD. No change text matches `ce.DEFERRAL_PROSE`.
- IN-04 entry (pillar J): 7 of the 24 repo SKILL.md frontmatters were invalid YAML before phase 8 and were not rewritten, by phase-scope decision. Evidence: 08-REVIEW-FIX.md and 08-REVIEW.md.

## Ledger edit guards (/tmp/0902_ledger_edit.py)
The script asserted that the working-tree ledger equals HEAD, that exactly one `"reviews"` line and one `"deltas"` line exist and equal the originals, and that the prefix and suffix lines are byte-identical. It also asserted that `frozen` equals the copy at FROZEN_AT 217d72b5, that `retained`, `state` and every other key equal HEAD, that state.N is `{terminal: None, evidence: [], savings: []}`, and that the gate's own `check_deltas` and `check_cbr` return []. Acceptance: the ledger diff has 2 removed lines, and `grep -c IN-04 ledger.json` = 1.

## Gate (HEAD f33d4a72)
`timeout 1200 python3 tools/test_skill_capability_prefinal.py` exited with rc=1:
```
  ok   V-PF-COMMITTED (program dir and tools/ clean in the working tree)
  ok   V-PF-L8 (check_ledger(final, gates not re-run) == ['L3 N: no terminal disposition'])
  ok   V-PF-UKDL (vault/programs/skill-capability/reviews/ukdl.md entries, fields and sources hold)
  ok   V-PF-CBR (14 rows A..N match the ledger, evidence exists)
  ok   V-PF-DELTAS (product 14, intelligence 15, A..M named)
  FAIL V-PF-CLOSEOUT-BUNDLE: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md missing at HEAD
  FAIL V-PF-CLOSEOUT-DECISIONS: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md missing at HEAD
  FAIL V-PF-CLOSEOUT-COMMANDS: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md missing at HEAD
  ok   V-PF-LEDGER-INVARIANT (all keys but state/reviews/deltas and state.N equal the FROZEN_AT ledger)
  ok   V-PF-UKDL-UNTOUCHED (no commit since the freeze touches vault/knowledge_base/ukdl-universal.md)
  ok   V-PF-NO-FINAL (run_wrapper(['--final']) raised ValueError; no process started)
  ok   V-PF-SELFTEST (SCP_SELFTEST=PASS rc 0, 0.3s)
  ok   V-PF-STATUS (open ['N'], closed A..M, violations [])
  ok   V-PF-PILLARS (--pillar A..M each rc 0 CEP_PILLAR_<P>=PASS, 23.4s)
  ok   V-PF-N-OPEN (--pillar N rc 1, CEP_PILLAR_N=FAIL on exactly 'L3 N: no terminal disposition')
  ok   V-PF-DIRTY-SET-STABLE (dirty set unchanged while the wrapper ran)
PF_TERMINAL=A,B,C,D,E,F,G,H,I,J,K,L,M
PF_OPEN=N (expected: state.N and --final are laptop-only)
PF_PASS=13/16
PF_FAILED=V-PF-CLOSEOUT-BUNDLE,V-PF-CLOSEOUT-DECISIONS,V-PF-CLOSEOUT-COMMANDS
PF_VERDICT=FAIL
```
This is the expected state. Direct runs of `python3 tools/test_skill_capability_program.py --pillar <P>` for A..M on HEAD f33d4a72 each gave rc 0 and `CEP_PILLAR_<P>=PASS`, 13 of 13.

## Deviations from Plan
1. **[Unattended choice] Pillar N appears in the deltas** (one product entry and one intelligence entry), besides the A..M coverage the gate requires. The plan's product list named N (`tools/test_skill_capability_prefinal.py`). The intelligence entry records the stale CE pin that the plan listed.
2. **[Unattended choice] UKDL entries tag their pillar.** The run-level traps (UKDL-SC-06, 10, 11 and 12) carry `[N]`, because they belong to the program's closeout and governance, not to a measurement pillar.
3. **[Unattended choice] Executor branch-namespace rule.** The generic executor protocol restricts worktree commits to `agent-*` / `worktree-agent-*` branches. The caller explicitly bound this run to branch `mission/skill-capability-run` in worktree sc-run. That branch is not protected (`main` is the default), so its HEAD was asserted before each commit and the caller's binding governed.
4. **[Rule 1 - accuracy] Two delta texts were corrected before the write.** These were the G lineage claim (now quotes the verdict PASS over 10 clauses, as read from G-lineage.md) and the A capsule-guard claim (names `unwrapCall`, verified at hooks/capsule_mutation_guard.js:71). No commit was needed for this, because both corrections happened before the ledger write.

The hook-generated `docs/{arch,changelog,constitution,prd}/*`, `.gsd/` and `vault/progress.md` were left untracked or unstaged. They were never committed and never deleted. STATE.md and ROADMAP.md were not updated, per the caller's instruction.

## Known limits (not failures)
- IN-04 (7 of 24 SKILL.md frontmatters were invalid YAML before phase 8) is recorded as a delta.
- Pillar E's session-spend decision and the mirror-red live sync are open Owner items, not failures of this plan.
- N stays open on gex44 by design. state.N, `--final` and the push belong to the laptop.

## Known Stubs
None.

## Threat Flags
None. These changes are review text and ledger data only.

## Self-Check: PASSED
- FOUND at HEAD: vault/programs/skill-capability/reviews/ukdl.md, vault/programs/skill-capability/reviews/cbr.md, vault/programs/skill-capability/ledger.json (reviews/deltas filled)
- FOUND: 9653c922, f33d4a72 (`git log`)
