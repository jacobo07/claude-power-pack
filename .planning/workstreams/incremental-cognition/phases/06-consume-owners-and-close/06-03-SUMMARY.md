---
phase: 06-consume-owners-and-close
plan: 03
subsystem: testing
tags: [pillar-n, ukdl, cbr, candidates, closeout-gate, owner-bundle, python]
status: complete

requires:
  - phase: 06-consume-owners-and-close
    provides: owner-bundle Phase 6 section and summary rows 29-30 (plan 06-02)
provides:
  - "vault/programs/incremental-cognition/ukdl-candidates.md: 16 candidate learnings (6 universal, 6 domain, 4 project), each with evidence refs that resolve at HEAD"
  - "reviews/ukdl.md and reviews/cbr.md: one verdict per candidate, duplicate sweep, frozen transfer rule, Promotions recorded: none"
  - "owner bundle [N] item and summary row 31"
  - "tools/test_ic_closeout.py: eight V-ICN gates and --drill (6 mutants)"
affects: [06-04 close-out]

actuals:
  tokens: 60000     # chars/4 over the realized diff (~240 KB of text across 6 files incl. the 941-line first commit)
  tasks: 2
  commits: 2        # MEASURED: git rev-list --count 189497a8..HEAD at SUMMARY write
plan_head_before: 189497a8348d799691d719b3e2954be29af367f9
commits: 2

tech-stack:
  added: []
  patterns:
    - "candidates and reviews discovered from their own header / table grammar, never listed in the gate"
    - "every gate carries in-gate controls on synthetic text; a mutation drill proves each control can go silent"
    - "promotion made unable to be silent: a candidate id found in the UKDL or under vault/tower needs a recorded promotion at a reachable commit"

key-files:
  created:
    - vault/programs/incremental-cognition/ukdl-candidates.md
    - vault/programs/incremental-cognition/reviews/ukdl.md
    - vault/programs/incremental-cognition/reviews/cbr.md
    - tools/test_ic_closeout.py
  modified:
    - vault/programs/incremental-cognition/owner-bundle.md

key-decisions:
  - "N is addressed, NOT satisfied: no state.N, no ledger reviews or deltas (06-04), IC-N not ticked, requirements.mark-complete not called"
  - "nothing is promoted: ukdl-universal.md and vault/tower are byte-unchanged; every CBR row is filed against none and the two performance candidates are HOLD under the frozen transfer rule"
  - "domain candidates target vault/knowledge_base/ukdl-cognitive-resource-os.md (mission-scoped entries; the universal file's tail has an automated writer)"

requirements-completed: []   # IC-N addressed here, not satisfied (promotion is the Owner's)

duration: 95min
completed: 2026-10-04
---

# Phase 6 Plan 03: UKDL and CBR candidate reviews and the closeout gate Summary

**Sixteen candidate learnings of this run are written at three levels with re-read evidence, reviewed for UKDL (4 PROMOTE-PROPOSED, 11 HOLD, 1 REJECT) and CBR (none promotable), put in front of the Owner as `[N]` (row 31), and `tools/test_ic_closeout.py` makes a silent promotion, an unresolved ref, a missing verdict, an untrue review record or a CBR performance promotion without a second workload turn red.**

## Accomplishments

- `ukdl-candidates.md`: the frozen rule N verbatim, the three levels and their targets, 16 blocks `### IC-<U|D|P>-<NN> -- ` with `level`, `kind`, `proposed_id`, `target`, `statement`, `evidence` (67 refs, every one a tracked path with optional line range or a reachable commit, re-read when written).
- `reviews/ukdl.md`: reviewer = this run, `reviewed_against` the UKDL at `54128e64` with its LF sha256, one verdict row per candidate, a `## Duplicate sweep` section (one command and hit count per candidate, plus the Owner's global rules as gex44 context only), `## Promotions recorded` = none. IC-U-02 is REJECT as a duplicate of `T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001`; IC-U-04 is PROMOTE-PROPOSED as the sending-side sister of `PR-VERIFY-HANDOFF-PREMISES-001`.
- `reviews/cbr.md`: the frozen transfer rule quoted byte for byte, eight `reviewed_against` records (four families, latest generation of each), the discovered families, the `family_baseline.py` subcommands (no `promote`), the promote-caller grep quoted (the only callers of `modules/tower/ratchet.promote` are tests), every candidate filed against `none` with its reason.
- Owner bundle (insert only): the `[N]` item (promotion is the Owner's, how to write and record a promotion, the indented `python3 tools/test_ic_closeout.py`, what closes) and summary row 31.
- `tools/test_ic_closeout.py`: V-ICN-CANDIDATES-SHAPE, -EVIDENCE-RESOLVES, -REVIEW-COVERAGE, -REVIEW-AGAINST-TRUTHFUL, -DUPLICATE-CITED, -CBR-TRANSFER-RULE, -PROMOTION-NEVER-SILENT, -BUNDLE-N, with in-gate controls, `--drill` M1-M6.

## Task Commits

| Task | Commit | Subject |
| ---- | ------ | ------- |
| 1 (tracer) | 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 | docs(incremental-cognition): N -- UKDL and CBR candidate reviews (one per level), [N] item and row 31, closeout gate (06-03) |
| 2 | 06650b92 | docs(incremental-cognition): N -- full candidate set (three levels), duplicate sweep and every verdict; closeout drill (06-03) |

## Verification (observed output)

RED before the Task 1 content (gate written first, every input absent): `python3 tools/test_ic_closeout.py` -> seven `FAIL ... FileNotFoundError ... ukdl-candidates.md` / `reviews/*.md`, `FAIL V-ICN-BUNDLE-N ... 0 `- **[N]**` item(s), exactly one required`, `ICN_PASS=0/8`.

GREEN after Task 1 (MIN_PER_LEVEL = 1, three candidates): `ICN_PASS=8/8  threshold=8/8  skipped=0  inconclusive=0`; `python3 tools/test_kme_replay.py` -> `KMER_PASS=45/45`, SUMMARY-ITEMS `23 item key(s) incl. sync (>= 19), 31 row(s)`.

RED before the Task 2 content (MIN_PER_LEVEL = 3 on the Task 1 file): `FAIL V-ICN-CANDIDATES-SHAPE ... problems=['level universal has 1 candidate(s), needs 3', 'level domain has 1 candidate(s), needs 3', 'level project has 1 candidate(s), needs 3']`, `ICN_PASS=7/8`.

GREEN after Task 2:

- `python3 tools/test_ic_closeout.py` -> `ICN_PASS=8/8  threshold=8/8  skipped=0  inconclusive=0`; evidence `16 candidate(s) {'universal': 6, 'domain': 6, 'project': 4}`, `67 evidence ref(s)`, `cited duplicate id(s) ['T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001'] all found`, `recorded promotions 0`, 1,161,193 chars of the UKDL and 154,326 chars under `vault/tower/` searched.
- `python3 tools/test_ic_closeout.py --drill` -> `PASS DRILL-CONTROL 8/8`, `KILLED` M1..M6 (each by its named gate), `PASS DRILL-CLEAN-AFTER-MUTANTS 8/8`, `DRILL killed=6/6`.
- `python3 tools/test_kme_replay.py` -> `KMER_PASS=45/45`; `python3 tools/test_ic_r2_evidence.py` -> `ICR2_PASS=14/14`; `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`; `timeout 300 python3 tools/test_kme_pillars.py` -> `KMEP_PASS=89/89`; `timeout 300 python3 tools/test_floor_regression_gate.py` -> `FLOOR_PASS=67/67`.
- Owner bundle insert-only: `git diff --numstat 189497a8 HEAD -- vault/programs/incremental-cognition/owner-bundle.md` -> `19 0`; Task 1 commit alone `19 0`.
- Protected paths: the own-commit check over this plan's recorded commits prints `own 2 touching protected []` (after Task 1: `own 1 ...`); `git diff --quiet HEAD -- vault/knowledge_base vault/tower` exits 0; ledger `state.N` prints `{}`.

## Deviations from Plan

- **Seeds kept, none dropped.** Every one of the sixteen seeds was re-read at its source and holds at HEAD, so none was dropped; the wording was tightened where the first draft overclaimed (IC-U-01: the breaker-less fallback needs the host author AND an auth phrase, it does not classify "even when wording drifts").
- **Promote-caller grep.** The plan quotes the grep `grep -rn "ratchet.promote\|import promote\|ratchet import"` as proof of no caller. Run now, it prints four lines, but all belong to `intent_verified` and a CEPS helper, not `modules/tower`; `cbr.md` quotes that output verbatim and adds the sharper `rt\.promote` grep whose only hits are `tools/test_tower_ratchet.py`. The conclusion (no production caller) holds; the plan's grep alone did not demonstrate it.
- **Extra reviewed_against records.** The CBR review also records the latest generation of each family (`vault/tower/baselines/*/B*.json`), beyond the family definitions the plan requires, because the entries a family is made of live there. Both are verified by V-ICN-REVIEW-AGAINST-TRUTHFUL.
- **Message files** live under `/home/kobii/.claude/jobs/9795364c/tmp/` (repo rule), not `/tmp`; the plan's bookkeeping files (`/tmp/ic-p6-03-pb.txt`, `/tmp/ic-p6-03-commits.txt`) are in `/tmp` as the acceptance commands read them. The acceptance one-liner was run from a script file (`owncheck.py`) because the harness refuses compound `git` inside `python -c`.
- No auto-fix deviations (Rules 1-3).

## Known Stubs

None.

## Threat Flags

None. Reads git objects and committed files; writes docs and a test gate only. No candidate quotes transcript content or a credential.

## Hard prohibitions honoured

`vault/knowledge_base/ukdl-universal.md` and every other `vault/knowledge_base` file, `vault/tower/**`, `tools/baseline_ledger.py` and every CBR generation byte-unchanged; `modules/tower/ratchet.promote` and `tools/family_baseline.py` run only in read-only modes (`show`, `verify`); no ledger `state.N`, reviews or deltas; IC-N not ticked; `requirements.mark-complete` not called; no existing owner-bundle line changed or removed; STATE.md, state.json and the foreign dirty paths left uncommitted.

## Self-Check: PASSED

- FOUND: tools/test_ic_closeout.py, vault/programs/incremental-cognition/ukdl-candidates.md, reviews/ukdl.md, reviews/cbr.md, owner-bundle.md `- **[N]**` item and row 31
- FOUND commits: 54128e64, 06650b92
