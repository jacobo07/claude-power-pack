---
phase: 08-owner-reconciliation-and-creation-governance
plan: 04
status: complete
subsystem: skill-capability program ledger, closure of pillars I-M
tags: [closure, ledger, owner-bundle, pillar-I, pillar-J, pillar-K, pillar-L, pillar-M]
requires: [08-01 J gate, 08-02 declarations and J evidence, 08-03 handoffs I/K/L/M]
provides: [state.I/J/K/L/M terminals in vault/programs/skill-capability/ledger.json, owner-bundle [I] [J] [J] [K] [L] [M]]
affects: [phase 9 (pillar N is the only open pillar; --status open=[N])]
tech-stack:
  added: []
  patterns: [one-line state replacement with frozen asserted against FROZEN_AT and every other line byte-compared, append-only owner bundle, record -> commit -> gate]
key-files:
  created: []
  modified: [vault/programs/skill-capability/ledger.json, vault/programs/skill-capability/owner-bundle.md]
decisions:
  - "J commit evidence = the four J commits (08-01 b989cb75; 08-02 007f1d86 declarations, 93c004b5 J evidence, 18076627 fixture fix); the G/H re-derivation commits of 08-02 are G/H evidence, not J"
  - "K row count: gex44 report re-read at execution printed rows 0 with a signals.jsonl now present (08-03 measured the file absent); recorded as UNMEASURED (no card ledger on gex44), never as zero opportunities"
  - "The [J] sync line states the measured 14 live copies + 10 ABSENT_LIVE rather than the plan's '24 live skill copies' (only 14 exist live on gex44)"
metrics:
  duration: ~20min
  completed: 2026-10-04
plan_head_before: 737706270a591bc5e3aca54a5dbbff1698503cb1
commits: 2
actuals:
  tokens: 4300
  tasks: 3
  commits: 2
---

# Phase 8 Plan 04: ledger closure of pillars I-M Summary

Pillars I, K and M are MERGED_INTO_EXISTING_OWNER and L is DEFERRED_STRONGER_OWNER, each on its frozen owner and a
committed, sha-pinned handoff from 08-03. J is IMPLEMENTED_AND_VERIFIED on its gate `tools/test_skill_creation_gate.py`
(SCG_PASS=32/32) and its rendered evidence. Six Owner-reserved items were appended to the owner bundle, and
`--pillar A` through `--pillar M` each print PASS on gex44. `--status` shows only N open.

## Commits

`commits: 2` = `git rev-list --count 73770627..HEAD` before this SUMMARY's commit. Both are this plan's.

| Task | Commit | Subject |
|---|---|---|
| 1 (tracer) | 844ea42a | docs(08-04): pillar L deferred to cognitive-economy on its committed handoff |
| 2 | 7d00f0ec | docs(08-04): pillars I, K, M merged into their owners, J implemented on its gate |
| 3 | - | no edit (regression only) |

C0 = 73770627 (before commit 1), C2 = 7d00f0ec. `git log -1 --format=%s` matched each subject. Both commits used the
pathspec `ledger.json owner-bundle.md` only.

## The five state lines

| Pillar | Terminal | Evidence |
|---|---|---|
| I | MERGED_INTO_EXISTING_OWNER | owner `modules/liveness/reachability.py`; handoff `handoffs/I.md` sha256 51cc310a90d642051062ebaa4bac7e08e122908639f196237731556770ee7728 |
| J | IMPLEMENTED_AND_VERIFIED | gate `["python", "tools/test_skill_creation_gate.py"]`; prg `evidence/J-creation-gate.md` sha256 9a81387fb6b3e28b587aed8eb8fdc7d5e3843388f8e1dc4f6866c11081c9f7d2; owner `~/.claude/skills/skill-creator/SKILL.md`; commits b989cb75, 007f1d86, 93c004b5, 18076627 (each `merge-base --is-ancestor` rc 0) |
| K | MERGED_INTO_EXISTING_OWNER | owner `modules/capability_runtime/agent_spec.py`; handoff `handoffs/K.md` sha256 37e79c08b5eb1df8bdec3c4ba536d1e4c03c773a87493f7d899d0a418f6a204b |
| L | DEFERRED_STRONGER_OWNER | owner `modules/cognitive_os/co_12_telemetry.py`; handoff `handoffs/L.md` sha256 14db77a12501e8bfa60192999396ec729ad637081189c3f36962d2fd1c96a516 |
| M | MERGED_INTO_EXISTING_OWNER | owner `tools/usage_index.py`; handoff `handoffs/M.md` sha256 e1471686fa6999913d292e721343681dba633d6e5dc37beff8f818dac0ce940e |

All five have `savings: []`. Each reason cites its D-NN (D-01 for I/K/L/M, D-02 for J). Figures were re-read at execution
from the 08-01..08-03 SUMMARYs, the committed handoffs and fresh runs: `skill_handoffs.py --check` (all four PASS at
73770627), `test_skill_creation_gate.py` (32/32, 4.5 s) and `skill_opportunity_signals.py report` (rows 0). The script
`/tmp/08-04-close.py` asserted, before writing, that `frozen` equals its copy at 217d72b5, that the old line is exactly
the null shape, that `ce.DEFERRAL_PROSE` finds no match in the reason, that owner refs are frozen owner strings and that
commit refs are ancestors. After writing it re-read the file: line count unchanged, only the target line(s) changed,
state.N null. In Task 2 it also asserted that the state.L line from commit 1 was byte-unchanged.

## The six owner-bundle lines (appended after [E], append only)

- [L] (host: laptop): point the CE mission at handoffs/L.md. Adjudicate `vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md:63`
  (quoted verbatim, EXISTS_AND_COMPLETE) against the absence measured by name (0 of 4294 paths, 0 code lines). The aperture
  is by name only; the two other lines are named.
- [I] (host: laptop): point CE pillar T at handoffs/I.md: 83 module candidates (export plane, empty HOME; 75 vs 64
  offenders by plane), 13 retirement verdicts and 155 skill candidates. A candidate is not a deletion verdict; nothing was
  deleted.
- [J] (host: laptop): skill-creator (not edited) should emit the `metadata:` declaration. The validator finding is cited
  (`ALLOWED_PROPERTIES` whitelist at plugin :42 / synced :84; 0 of 72 outcomes changed).
- [J] (host: laptop and gex44): sync the live skill copies. DD-03 reds as measured: CDIO_MOBILE 6/6 -> 5/6 (V-CDIO-MOBILE-MIRRORS
  drift=['SKILL.md']); `--live` 13/1/10 -> 0/14/10; laptop V-ROUTER-SKILL-DRIFT 14-skill drift turns the verify_spp router row red.
- [K] (host: laptop): run `skill_opportunity_signals.py report` for the laptop CO-12 count. The gex44 value as measured is
  rows 0 and UNMEASURED, because there is no card ledger.
- [M] (host: laptop): read handoffs/M.md. Cost figures come only from usage_index windows. The two adjudicated
  cost-marker hits are named (`tools/skill_dedup_sweep.py:324`, `tools/test_card_precision.py:330`).

The [E] line and state.E were not touched. `grep -c '^\[E\]' owner-bundle.md` returns 1.
`python3 tools/test_contribution_verdict.py` returns rc 0, `verdict: NOT_SEPARABLE`, `CT_PASS=14/14`.

## Task outputs (verbatim)

- Task 1: `CEP_PILLAR_L=PASS` (rc 0). Control before Task 2: `--pillar I` returned `FAIL L3 I: no terminal disposition`
  and `CEP_PILLAR_I=FAIL`, which shows the verifier judges the line.
- Task 2: `CEP_PILLAR_I=PASS`, `CEP_PILLAR_J=PASS` (5 s, L5 runs the gate), `CEP_PILLAR_K=PASS`, `CEP_PILLAR_M=PASS`.
  Acceptance results:
  - `git diff -U0 C0 C2 -- ledger.json` returns rc=0, and its tags are exactly `-/+` for I, J, K, L, M.
  - The bundle diff returns rc=0 with 0 removed lines. Its added tags are [I] [J] [J] [K] [L] [M].
  - The terminals are `['MERGED_INTO_EXISTING_OWNER', 'IMPLEMENTED_AND_VERIFIED', 'MERGED_INTO_EXISTING_OWNER',
    'DEFERRED_STRONGER_OWNER', 'MERGED_INTO_EXISTING_OWNER']` and N is `{'terminal': None, 'evidence': [], 'savings': []}`.
- Task 3: thirteen `--pillar` tails, each rc 0, at 7d00f0ec on gex44:

```
A rc=0 6s CEP_PILLAR_A=PASS
B rc=0 0s CEP_PILLAR_B=PASS
C rc=0 0s CEP_PILLAR_C=PASS
D rc=0 1s CEP_PILLAR_D=PASS
E rc=0 0s CEP_PILLAR_E=PASS
F rc=0 1s CEP_PILLAR_F=PASS
G rc=0 8s CEP_PILLAR_G=PASS
H rc=0 1s CEP_PILLAR_H=PASS
I rc=0 0s CEP_PILLAR_I=PASS
J rc=0 4s CEP_PILLAR_J=PASS
K rc=0 0s CEP_PILLAR_K=PASS
L rc=0 0s CEP_PILLAR_L=PASS
M rc=0 0s CEP_PILLAR_M=PASS
```

  The output files contain no FAIL line. `skill_handoffs.py --check` printed `SKILL_HANDOFFS PASS pillars=4` (rc 0).
  `test_skill_creation_gate.py` printed `SCG_PASS=32/32`. `--status` printed `open ["N"]`, `closed A..M` and
  `violations []` (rc 0).

## Deviations from Plan

1. **Bundle append by script, not the Edit tool.** The plan names the Edit tool. The same `/tmp/08-04-close.py` appended
   the lines and asserted that the old bytes are an exact prefix of the new file, which proves append-only more strictly
   than an Edit. The diff check (0 removed lines) confirms it.
2. **"24 live skill copies" stated as measured.** On gex44, 14 repo skills have a live copy and 10 are ABSENT_LIVE. The
   [J] sync line says that instead of 24.
3. **K's CO-12 host state moved since 08-03.** When 08-03 measured, `signals.jsonl` was absent ("file present: False").
   At execution it was present, 288 bytes, created 2026-10-04 00:55 by a process outside this run, with 0
   `capability_opportunity` rows. state.K and [K] record this as UNMEASURED; it is not a count of opportunities.
   `--check` still passes.
4. **Branch.** As for 08-01..08-03, I committed on `mission/skill-capability-run`, not `agent-*`, per the orchestrator.

STATE.md, ROADMAP.md and REQUIREMENTS.md were not updated, because the orchestrator owns them. No docs/* stubs, .gsd/,
vault/progress.md, 07-VERIFICATION.md, ~/.claude, CE file, `frozen`, state.E or [E] line was touched.

## Known Stubs

None. The changes are data only (ledger lines and bundle lines).

## Threat Flags

None. T-08-13..T-08-16 were mitigated as planned: one replacement per line with frozen and byte checks, sha256 from
`ce.lf_sha256` at write time, owner refs asserted to be frozen strings, and Owner items as bundle lines only.

## Self-Check: PASSED

- FOUND: commits 844ea42a and 7d00f0ec in `git log 73770627..HEAD`.
- FOUND: vault/programs/skill-capability/ledger.json state I-M closed (verified by `--pillar I..M` and `--status`).
- FOUND: six appended bundle lines (bundle diff tags [I] [J] [J] [K] [L] [M]).
