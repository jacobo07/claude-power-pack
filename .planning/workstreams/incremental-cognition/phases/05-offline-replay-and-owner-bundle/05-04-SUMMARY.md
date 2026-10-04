---
phase: 05-offline-replay-and-owner-bundle
plan: 04
subsystem: owner-bundle-and-evidence
tags: [kme, pillar-L, owner-bundle, summary-table, coverage-by-discovery, evidence, scratch-replay]

requires:
  - phase: 05-offline-replay-and-owner-bundle
    provides: kme_replay rank core and contract (05-01, 05-02), [L] items and laptop code sync (05-03)
provides:
  - "owner bundle: ## Summary (every Owner item, phases 1-5), 24 rows, at the top of the file (insert only)"
  - "tools/test_kme_replay.py: bundle_items, summary_rows, uat_keys; V-KMER-BUNDLE-SUMMARY-ITEMS, V-KMER-BUNDLE-SUMMARY-UAT (coverage discovered from the bundle and the phase files, in-gate red controls)"
  - "vault/programs/incremental-cognition/evidence/L.md (Status OPEN)"
affects: [06 consume owners and close]

actuals:
  tokens: 10014
  tasks: 2
  commits: 3
plan_head_before: aca5468d
commits: 3

tech-stack:
  added: []
  patterns:
    - "a coverage gate enumerates its subjects from the artifact and from the phase files, never from a list in the test; each check is driven red by a control inside the gate"
    - "a SKIP is the answer when the files a check needs are absent, never a PASS, and the plan's own verify treats a SKIP on GEX44 as a failure"

key-files:
  created:
    - vault/programs/incremental-cognition/evidence/L.md
  modified:
    - vault/programs/incremental-cognition/owner-bundle.md
    - tools/test_kme_replay.py

key-decisions:
  - "source cell = discovered keys separated by ` ; `; the gate compares whole tokens (an item key `[X]#k \"<first three words>\"`, `sync`, `UAT NN#n`, `VER NN#k`), so a stale or unknown token is refused, not only a key-shaped one"
  - "V-KMER-BUNDLE-SUMMARY-UAT is excluded from the mutation drill's control set (it SKIPs on a checkout without the phase files, and the drill's control needs every gate to answer); it is not a mutation target"
  - "the sync section's expected-output block predates the table, so one inserted paragraph states the counts the replay and GEX44 now print (insert only, separate commit)"

requirements-completed: []   # IC-L addressed, NOT satisfied: L stays OPEN (no KME-L ranking, no Owner decision); ledger state.L is {}

coverage:
  - id: D1
    description: "the bundle opens with one table covering the code sync, every [X] item and every pending UAT / VERIFICATION human check, with exact commands taken verbatim from the item bodies"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-KMER-BUNDLE-SUMMARY-ITEMS (19 item keys incl. sync, 24 rows, 0 problems, 4 controls report), V-KMER-BUNDLE-SUMMARY-UAT (11 UAT keys, 1 VER key, 7 controls report)"
        status: pass
    human_judgment: false
  - id: D2
    description: "evidence/L.md records the frozen rule, the measures, the observed outputs, the consolidation, the liveness disposition, LF sha256 of six artifacts, Product / Intelligence Delta, named debts and Status OPEN"
    requirement: IC-L
    verification:
      - kind: integration
        ref: "rule text byte-equal to ledger.json, six sha256 lines re-computed equal, --pillar L still FAIL L3 L: no terminal disposition (exit 1), state.L {}"
        status: pass
    human_judgment: false
  - id: D3
    description: "the laptop code sync, replayed at the final HEAD in a scratch clone at the P0 freeze 18e928af, gives four suites at exit 0"
    requirement: IC-L
    verification:
      - kind: integration
        ref: "scratch replay at 003815a8 (below); clone removed"
        status: pass
    human_judgment: false

duration: 31min
completed: 2026-10-04
status: complete
---

# Phase 5 Plan 04: Owner bundle summary table, evidence/L.md, final sync replay Summary

**The owner bundle now opens with one table of every Owner action in phases 1-5 (24 rows, exact command and what closes), a pair of gates that discover the items and the pending UAT checks from the files and turn red when a row is missing or stale, and pillar L's evidence file is committed with Status OPEN.**

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 (tracer) | 4bb6eb67 | docs(incremental-cognition): owner bundle summary table -- every Owner item of phases 1-5 in one place, coverage discovered and gated |
| 1 (follow-up, deviation 1) | 4c3044b8 | docs(incremental-cognition): owner bundle -- sync expected counts after the summary gates (KMER 40/40 skipped=1 at the freeze) |
| 2 | 003815a8 | docs(incremental-cognition): L -- evidence (ranker built and smoke-run on GEX44; KME-L run and quota decision with the Owner, Status OPEN) |

`plan_head_before` aca5468d; `git rev-list --count aca5468d..HEAD` = 3 before this SUMMARY commit.

## RED record (Task 1)

Gates written first, run before the table existed:

```
FAIL V-KMER-BUNDLE-SUMMARY-ITEMS 19 item key(s) incl. sync (>= 19), 0 row(s), problems=['no summary section'], controls report: {'unknown command': False, 'removed header': True}
FAIL V-KMER-BUNDLE-SUMMARY-UAT 11 pending UAT key(s) (>= 11) and 1 VER key(s) (>= 1) each have a row, problems=['missing row for VER 01#1', 'missing row for UAT 02#1', ...]
KMER_PASS=39/41  threshold=41/41  skipped=0  inconclusive=0
```

(Two earlier first runs of the UAT gate failed on mistakes in my synthetic controls, fixed before the real RED above: the synthetic phase directory used `09-x`, outside the `0[1-5]-*` glob, and one expected key still named phase 09.) GREEN after the table:

## Gate output (final, observed on GEX44 after the last task commit)

```
KMER_PASS=41/41  threshold=41/41  skipped=0  inconclusive=0          (python3 tools/test_kme_replay.py)
PASS V-KMER-BUNDLE-SUMMARY-ITEMS 19 item key(s) incl. sync (>= 19), 24 row(s), problems=[], controls report: {'removed row': True, 'stale row': True, 'unknown command': True, 'removed header': True}
PASS V-KMER-BUNDLE-SUMMARY-UAT 11 pending UAT key(s) (>= 11) and 1 VER key(s) (>= 1) each have a row, problems=[], 7 controls report
PASS DRILL-CONTROL unmutated run: 38/38 gates green ; DRILL killed=13/13   (python3 tools/test_kme_replay.py --drill)
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0          (python3 tools/test_kme_pillars.py) ; DRILL killed=20/20 (--drill)
FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0         (python3 tools/test_floor_regression_gate.py)
CEP_SELFTEST=PASS / ICP_SELFTEST=PASS                                (python3 tools/test_incremental_cognition_program.py --selftest)
pillar_l_rc=1 ; FAIL L3 L: no terminal disposition                   (--pillar L)
```

## Final replay of the laptop code sync (GEX44 scratch clone at the P0 freeze 18e928af; nothing run on the laptop)

The `## Laptop code sync` lines were read from the committed bundle at branch tip `003815a8dfcf07a33634c1943ee03067b7f0d1f6`
and run with `git -C`, only the fetch URL replaced by the worktree path: `git fetch` exit 0; `git rev-parse FETCH_HEAD`
-> `003815a8dfcf07a33634c1943ee03067b7f0d1f6` (equals the branch tip); `git merge-base --is-ancestor f3cdc79b... FETCH_HEAD`
exit 0; `git status --short -- <paths>` printed nothing (0 bytes, exit 0); checkout and pathspec commit exit 0. The four
suites, each exit 0:

```
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
SKIP V-KMER-BUNDLE-SUMMARY-UAT phase(s) ['01', '02', '03', '04'] cited by a row have no UAT or VERIFICATION file on this checkout
KMER_PASS=40/40  threshold=40/40  skipped=1  inconclusive=0
FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0
ICP_SELFTEST=PASS
```

The replay was run at tip `4bb6eb67` first, at `4c3044b8`, and finally at `003815a8` (same results). The first run of
that script died at the last suite because my script quoted `--selftest` into the path (exit 2, a script bug, not a
suite failure); fixed and rerun. `test -d /tmp/ic-p5-04-sync` exits 1 (clone removed).

## Acceptance checks

- Summary header count 1, its line precedes `## Laptop code sync` and `## Items`; the table holds rows citing `UAT 04#2` and `[L]#2`.
- Insert only: `git diff aca5468d HEAD -- vault/programs/incremental-cognition/owner-bundle.md | grep -c '^-[^-]'` -> 0 (also 0 for each of the two bundle commits).
- L.md: one `## Product Delta`, one `## Intelligence Delta`, one `## Status: OPEN`; the frozen rule line is byte-equal to `ledger.json`; all six sha256 lines equal a fresh run; `git show --stat HEAD` for Task 2 lists only `evidence/L.md`.
- Liveness: `git diff --name-only bfe4ee4a..HEAD -- modules hooks commands agents SKILL.md CLAUDE.md vault/liveness` prints nothing; scanner on GEX44 `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | gate offenders: 64`, exit 1, pre-existing.
- `state.L` prints `{}`; `grep -c '\[x\] \*\*IC-L\*\*'` prints 0; no `L-owner-decision.md` written.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The sync section's expected-output block went stale**
- **Found during:** Task 2 (the final replay)
- **Issue:** the block under `## Laptop code sync` says `KMER_PASS=39/39 ... skipped=0`; with the two new gates the replay at the freeze prints `KMER_PASS=40/40 skipped=1` (the UAT gate SKIPs: no phase files at 18e928af) and GEX44 prints 41/41. An Owner comparing outputs would read a healthy run as a mismatch.
- **Fix:** one paragraph inserted under the block (insert only; the old lines are untouched), as its own commit `4c3044b8` so Task 2's commit lists only `evidence/L.md` as the plan requires.
- **Files modified:** vault/programs/incremental-cognition/owner-bundle.md

### Judgement calls (no rule trigger)

1. **Source cell keys are whole tokens.** The plan names key-shaped regexes; the gate splits the source cell on `;` and compares whole tokens, which also refuses any unknown token (a superset of the plan's check).
2. **Drill control set.** `V-KMER-BUNDLE-SUMMARY-UAT` is excluded from `DRILL_GATES` (it can SKIP and the drill's control requires every gate to answer; it attacks nothing the drill mutates).
3. **Row cells.** Judgement rows carry pillar labels such as `H (phase 3 UAT)` and the command `/gsd-verify-work <N>` from STATE.md "Deferred Verification"; the `[B]` env-deploy row lists all four deploy lines (a7, a5; dry-run, apply) and the `[D]` row lists the population proof and both `d` lines.
4. **Closing text.** "What closes" is quoted or closely paraphrased from the item or UAT check; the `[B]` DEBT row says nothing closes it here; the sync row says "expected, not measured there".
5. **Commit trailer.** The attribution reminder in force for this run (`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`) was used, as in 05-01..05-03, not the Opus line in the execution prompt.
6. **Tracer gate.** `<verify>` is automated-only; it was re-run end to end after the table landed (41/41) before the second task, per the tracer rule in auto-unattended mode.

No Rule 2-4 deviations. No auth gates, no package installs, no checkpoint reached. No `claude` session was started and nothing was written under `~/.claude/**` outside the job tmp dir.

## Known Stubs

None.

## Threat Flags

None. The table and L.md quote instrument output and commands already in the bundle; no new endpoint or write path.

## Pending Owner checks the table discovers (all still open)

Phase 1: VER 01#1 (the `[A]` PRG). Phase 2: UAT 02#1..#4 (`[C]` PRG, `[B]` re-login / install decision / env deploy, WR-04/06/07 semantics, WR-08 merge strategy). Phase 3: UAT 03#1..#4 (KME-L runs, H prediction check, D second workload, full review of `tools/test_kme_pillars.py`). Phase 4: UAT 04#1..#3 (laptop `[K]`, WR-01..03 policy judgement, judgment-tier prohibitions). Plus the two `[L]` items.

## Self-Check: PASSED

- FOUND: vault/programs/incremental-cognition/evidence/L.md, vault/programs/incremental-cognition/owner-bundle.md, tools/test_kme_replay.py
- FOUND commits: 4bb6eb67, 4c3044b8, 003815a8 (`git rev-list --count aca5468d..HEAD` = 3 before this SUMMARY commit)
- Gates re-run after the last task commit: KMER_PASS=41/41, DRILL killed=13/13, KMEP_PASS=89/89, FLOOR_PASS=67/67, ICP_SELFTEST=PASS, --pillar L exit 1
