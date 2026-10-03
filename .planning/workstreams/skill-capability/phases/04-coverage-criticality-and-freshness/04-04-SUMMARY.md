---
phase: 04-coverage-criticality-and-freshness
plan: 04
subsystem: skill-capability program ledger (pillars D, H)
tags: [ledger, pillar-closure, evidence, pillar-D, pillar-H]
requires: [04-01, 04-02, 04-03]
provides:
  - ledger state.D IMPLEMENTED_AND_VERIFIED (gate tools/test_skill_coverage.py + prg D-coverage.md)
  - ledger state.H IMPLEMENTED_AND_VERIFIED (gate tools/test_skill_drift.py + prg H-drift.md)
  - owner-bundle [D] x1, [H] x2 (host: laptop)
key-files:
  modified:
    - vault/programs/skill-capability/ledger.json
    - vault/programs/skill-capability/owner-bundle.md
decisions:
  - "D and H closed by textual replacement of exactly their two state lines (same method as phase 1 for A)"
  - "Task 1 tracer and task 2 land in one commit, as the plan's task 2 specifies (ledger + bundle + this SUMMARY)"
  - "Workstream STATE.md is updated after the plan commit in a separate docs(state) commit, on the orchestrator's instruction (the plan text says the orchestrator owns STATE.md)"
status: complete
plan_head_before: b9adc10a1acbdfc5713cbf109d49fe42cc16b236
commits: 1
actuals:
  tokens: 6000
  tasks: 2
  commits: 1
metrics:
  completed: 2026-10-03
---

# Phase 4 Plan 04: close pillars D and H in the ledger Summary

Pillars D (coverage + criticality) and H (freshness / drift) are IMPLEMENTED_AND_VERIFIED in
`vault/programs/skill-capability/ledger.json`, with gate + prg evidence the verifier re-runs and accepts on gex44; A, B and
C still pass. The Owner bundle carries one `[D]` and two `[H]` laptop-plane lines.

`commits: 1` is the plan commit that contains this file (it is written before that commit, so the count is the
planned single commit; re-measure with `git rev-list --count b9adc10a..<plan commit>`).

## Task 1 (tracer): state.D and state.H

Preconditions (foreground, gex44): `python3 tools/test_skill_coverage.py` -> `SKC_PASS=15/15` rc 0, `ok V-SKC-EVIDENCE-CURRENT`;
`python3 tools/test_skill_drift.py` -> `SKD_PASS=13/13` rc 0, `ok V-SKD-EVIDENCE-CURRENT`; `git status --porcelain` of the
pinned evidence, the four tools and `card_source_digests.json` empty.

Script `/home/kobii/.claude/jobs/88cfe52b/tmp/04-04-ledger.py` (frozen == FROZEN_AT copy before and after, D/H empty
precondition, `ce.lf_sha256` pins, `ce.DEFERRAL_PROSE` check, other state entries equal to the pre-edit read, line-by-line
byte identity outside the two lines): `OK lines changed: [102, 106]`.

Evidence lists as written:

    D [{"kind": "gate", "argv": ["python", "tools/test_skill_coverage.py"]}, {"kind": "prg", "ref": "vault/programs/skill-capability/evidence/D-coverage.md", "sha256": "f46e7b1270b119266310abbe98302413d11b68d5eebc2efa84776a10666ab05f"}, {"kind": "file", "ref": "vault/programs/skill-capability/evidence/D-live-gex44.json", "sha256": "319fd8e55cdac062238e64c50bd70262758092aeb2ed72227fdee923255f615a"}, {"kind": "owner", "ref": "tools/skill_invocations.py"}, {"kind": "commit", "ref": "1ad9ee71"}, {"kind": "commit", "ref": "8313c340"}]
    H [{"kind": "gate", "argv": ["python", "tools/test_skill_drift.py"]}, {"kind": "prg", "ref": "vault/programs/skill-capability/evidence/H-drift.md", "sha256": "5eae42e6963e13ca6e5af1d8c273c13f573f7790355a652a3a802cb958dafbbd"}, {"kind": "file", "ref": "vault/programs/skill-capability/evidence/H-live-gex44.json", "sha256": "43831a34843e21aa2c07d00b1c025411a71b9a849f08bc8cd44428152708ee6f"}, {"kind": "file", "ref": "vault/programs/skill-capability/card_source_digests.json", "sha256": "cdce72618407c85edda52e3c26f60cb2a4739ecd80fa6df6d351687fc79ada31"}, {"kind": "owner", "ref": "tools/router_freshness_gate.py"}, {"kind": "commit", "ref": "97ded664"}, {"kind": "commit", "ref": "a94256e6"}, {"kind": "commit", "ref": "06dae4b0"}, {"kind": "commit", "ref": "a98f883c"}]

Reasons: D names repo plane 24 (opportunity_detector 1, card 1, none 22; high 0 / medium 4 / low 20), gex44 plane 185
(1 / 1 / 183; high 11 / medium 5 / low 169), 9 high-with-coverage-none on gex44, the two positive controls and four drills,
the 10/15 mutated-dispatcher red run. H names IDENTICAL 13 (eol_only 10) / DRIFT 1 / ABSENT_LIVE 10 / INCONCLUSIVE 0, the
android-reverse-engineering DRIFT (4 `.ps1` absent live), the raw-byte 4/10/10 vs LF 13/1/10 reconciliation, 2 card/source
pairs CURRENT with both poles driven, and the router gate's `V-ROUTER-SKILL-DRIFT` (max 0.054 s, FAIL on gex44 for the
android drift). Both reasons name host gex44 and leave the laptop plane to the Owner bundle. All figures copied from the
04-01 / 04-02 / 04-03 SUMMARYs.

Acceptance checks: frozen equality `True`; `git diff -U0` rc=0, 4 state markers, exactly `-  "D"`, `+  "D"`, `-  "H"`,
`+  "H"`; both terminals IMPLEMENTED_AND_VERIFIED with argv `['python', 'tools/test_skill_coverage.py']` and
`['python', 'tools/test_skill_drift.py']`.

Red drill (could the verifier say FAIL? `/home/kobii/.claude/jobs/88cfe52b/tmp/04-04-drill.py`, in-memory ledger copies,
real Resolver, file on disk untouched):

    D unmutated: [] gate calls: [(('python', 'tools/test_skill_coverage.py'), 0)]
    D prg sha mutant: ['L4 D: prg file vault/programs/skill-capability/evidence/D-coverage.md sha256 changed since it was cited']
    D deferral mutant: ["L7 D: reason defers in prose: 'later'"]
    D gate rc mutant: ['L5 D: gate python tools/test_skill_coverage.py --no-such-flag rc 2: ...']
    H unmutated: [] gate calls: [(('python', 'tools/test_skill_drift.py'), 0)]
    H prg sha mutant: ['L4 H: prg file vault/programs/skill-capability/evidence/H-drift.md sha256 changed since it was cited']
    H deferral mutant: ["L7 H: reason defers in prose: 'later'"]
    H gate rc mutant: ['L5 H: gate python tools/test_skill_coverage.py --no-such-flag rc 2: ...']

So each PASS below is a gate that actually ran (one call, rc 0) plus pins that would have failed if changed.

## Task 2: owner bundle and regression

Appended (append only; `git diff -U0` removed lines 0): one `[D] (host: laptop)` line (laptop plane recording, re-render,
move the state.D prg pin, add `D-live-laptop.json` as file evidence; real only after the pillar A live-hook sync) and two
`[H] (host: laptop)` lines (laptop `--live` / `--measure-live --host laptop` / re-render / move pins; fetch precondition on
repo_commit `97ded664c314857fb32f88576a41529380d060e7` read from `H-live-gex44.json`; gex44 DRIFT set and ABSENT_LIVE 10
left unrepaired for the Owner; the router gate's three new red paths, the `verify_spp.py` router row, the measured cost
0.054 s vs bound 3.0 s, and the `--record-cards` obligation after any card or source edit). Counts: `^\[D\]` 1, `^\[H\]` 2.
state.C is terminal (IMPLEMENTED_AND_VERIFIED), so `--pillar C` was run.

Verifier, verbatim output (each run `timeout 1900`, foreground, gex44, rc 0; the whole output of each run is this one line):

    $ python3 tools/test_skill_capability_program.py --pillar A
    CEP_PILLAR_A=PASS
    $ python3 tools/test_skill_capability_program.py --pillar B
    CEP_PILLAR_B=PASS
    $ python3 tools/test_skill_capability_program.py --pillar C
    CEP_PILLAR_C=PASS
    $ python3 tools/test_skill_capability_program.py --pillar D
    CEP_PILLAR_D=PASS
    $ python3 tools/test_skill_capability_program.py --pillar H
    CEP_PILLAR_H=PASS

D and H were run twice: once after task 1 (both PASS) and once after the bundle edit (both PASS, unchanged).
`--status`: closed A, B, C, D, H; open E, F, G, I-N; `"violations": []`.

## Deviations from Plan

1. [Rule 1 - own typo] The first append of the `[H]` fetch-precondition line carried `97ded6643c...` (an extra digit,
   carried over from the 04-02 SUMMARY's abbreviated `97ded6643...`). Fixed in the same uncommitted edit to the value
   read from `H-live-gex44.json`; `git cat-file -t` on it prints `commit`.
2. Per-task commits: the plan's task 1 has no commit step and task 2 commits ledger + bundle + SUMMARY together under the
   planned subject, so there is one plan commit, not two.
3. STATE.md: the plan says not to edit it; the orchestrator's instruction for this run asks for a minimal update through
   gsd-tools. Done after the plan commit, in its own commit, so `HEAD~1` (not HEAD) is the 3-file plan commit if the
   STATE commit lands. See the run report for whether the gsd-tools state commands worked.
4. One stray one-byte file I created by mistake inside the worktree (`.claude/jobs-tmp-placeholder`) was deleted at once
   after a content check; it was never staged.

## Known Stubs / Threat Flags

None. Only the D and H ledger lines and appended bundle lines changed; no CE file, no `frozen` byte, no gex44 `~/.claude`
file was edited (T-04-14..17 mitigated as planned).

## Self-Check: PASSED

ledger.json and owner-bundle.md modified as above; every cited commit (1ad9ee71, 8313c340, 97ded664, a94256e6, 06dae4b0,
a98f883c) is an ancestor of HEAD; every cited file exists and matches its pin (the verifier's L4 is green for D and H).
