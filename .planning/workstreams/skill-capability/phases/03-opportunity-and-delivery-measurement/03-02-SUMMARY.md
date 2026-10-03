---
phase: 03-opportunity-and-delivery-measurement
plan: 02
subsystem: pillar-C-delivery-measurement
tags: [delivery, recall, precision, windows, planes, pillar-C]
status: complete
requirements: [SC-C]
key-files:
  modified:
    - tools/test_skill_delivery.py
    - vault/programs/skill-capability/evidence/C-delivery.md
  created:
    - vault/programs/skill-capability/evidence/C-window-G.json
commits: 2
plan_head_before: 0261ea8efb591718b9beef31c21e083b1dd5a4bc
actuals:
  tasks: 2
  commits: 2
---

# Phase 3 Plan 02: windows L and G, live path, planes gate Summary

The 03-01 gate now carries window L (the pinned laptop pack, precision over frozen D-CARD, selection-bound recall), window G (a recorded gex44 measurement with opportunity UNMEASURED), a tested `--measure-live` / `--compare` path, and a planes clause that refuses any line mixing windows.

## Commits

- `e90bb823` feat(03-02): C -- window L (laptop pack) precision over D-CARD, selection-bound recall (Task 1, tracer)
- `d1bed167` feat(03-02): C -- window G recorded on gex44, live path proven on fixture, planes gate (Task 2)

## Gate

Verbatim last line: `SD_PASS=36/36` (exit 0, `python3 tools/test_skill_delivery.py`). No FAIL and no INCONCLUSIVE line.

## Window L (plane laptop, n stated)

Pack `card_evidence_pack.json`, LF sha256 `dacfdf5aa8afb0a5...` matches PACK_SHA256. 20 of 140 ledger rows; by decision deny-card 6, pass-after-card 8, unknown 6.
- opportunities 6, delivery measured 6, delivered 6 (by card 6, invocation-only 0).
- card_and_invocation `UNMEASURED` (the pack ships 9 nameless Skill tool calls, so the invocation channel is UNMEASURED, never 0 and never 9).
- recall `6/6 = 1.000 (n=6)`, labelled `selection-bound` (the builder picks no undelivered opportunity rows). Population recall `UNMEASURED on host gex44`.
- precision (card channel) `0/5 = 0.000 (n=5)`, labels from frozen D-CARD (live_denies 5, true_positives 0); the 6th deny `4615e1d1` is reported beside D-CARD, never folded in. judgement unknown (git exit 128) 6 beside, never counted. pass-after-card 8.

## Window G (plane gex44, recorded)

- `$END` = `2026-10-03T18:05:00Z` (taken as now minus 2 minutes, see deviations), days 7, start `2026-09-26T18:05:00Z`, root `~/.claude/projects` (literal, A-2), host `kobicraft-gex44`.
- Measure command: `python3 tools/test_skill_delivery.py --measure-live --window G --root '~/.claude/projects' --days 7 --end 2026-10-03T18:05:00Z --out vault/programs/skill-capability/evidence/C-window-G.json` -> `wrote ...`, rc 0.
- Compare (same arguments, `--compare`): `compare: identical`, rc 0 (run twice: after the record and after the commits).
- Figures: invocations model 31, typed 23 (n = 23 sessions with calls; unknown_rows 0, untimed_rows 0); 189 files scanned (informational). Only 4 skills were invoked, all gsd-*: gsd-autonomous (model 3, typed 23), gsd-code-review 5, gsd-execute-phase 12, gsd-plan-phase 11. The capability `concurrent-writers-shared-tree`: model 0, typed 0 (measured). card ledger ABSENT, opportunities `UNMEASURED`, recall and precision null.
- Record is content-free (no sessionId / uuid / message keys; checked `False`).

## Verification of other clauses

V-SD-LIVE-PATH reproduces window F through `measure_live` on the fixture materialised as a fake root plus ledger (recall `4/6 = 0.667 (n=6)`, opportunities 8). V-SD-PLANES ok; `--measure-live` without `--end` exits 2 and writes nothing. New drills each ok: L-UNLABELLED-AS-FALSE, L-INVOCATION-ZERO, L-DCARD-TP, L-EMPTY-WINDOW, TS-DROP, G-OPPORTUNITY-ZERO, PLANE-SUM (plus L-CLEAN control). All 03-01 drills still ok.

## Deviations from Plan

**1. [A-1] unparseable card ts.** `compute_window` now marks a row with an unparseable `ts` as delivery UNMEASURED for any decision (including deny-card, whose card delivery would otherwise be observable independent of ts), counts it in `unparseable_ts`, keeps it as an opportunity. Clause V-SD-TS-UNPARSEABLE (also pins fixture ts to the pack's 24-char ISO shape) and drill M-TS-DROP added. The live path keeps ledger rows whose ts is unparseable instead of bounding them out, so they print UNMEASURED rather than vanish. Window F figures unchanged.

**2. [A-2/A-3]** G record stores the literal `~/.claude/projects` (passed quoted so the shell does not expand it; `measure_live` expands internally). utf-8 reads and `newline="\n"` writes throughout.

**3. [Tracer lines] tag prefix.** Task 1 rendered tagged lines as `- [L] ...`, which failed the plan's `^\[L\] ` acceptance (grep count 0 at the Task 1 commit). Task 2 changed all F/L/G lines to start with `[X] ` and V-SD-PLANES now enforces it. Task 1's committed render therefore differs from Task 2's.

**4. `$END` taken 2 minutes before now** (plan: now truncated to the minute) so that this running session's own transcript rows cannot be mid-flush at measure time; the record names its `end` either way.

**5. Host string** is `kobicraft-gex44` (gethostname); the clause requires `gex44` as a substring.

## Findings

- Window G shows zero invocations of the capability in 7 days of gex44 transcripts. That is an invocation count, not a recall: gex44 has no card ledger so opportunity is UNMEASURED.

## Known Stubs

None. `files_scanned` is informational by design and excluded from `--compare`.

## Threat Flags

None. Window G record is counts and skill names only.

## Self-Check: PASSED

Files found: tools/test_skill_delivery.py, vault/programs/skill-capability/evidence/C-delivery.md, vault/programs/skill-capability/evidence/C-window-G.json. Commits e90bb823 and d1bed167 present in `git log`; `git rev-list --count 0261ea8e..HEAD` printed 2 before this SUMMARY commit.
