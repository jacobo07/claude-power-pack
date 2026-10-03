---
phase: 06-compile-out-lineage
verified: 2026-10-03T21:00:00Z
status: passed
score: 2/2 roadmap success criteria + 3/3 plans (at least one must-have per plan driven to the other answer by the verifier) verified (SC-G)
covered_files:
  - .planning/workstreams/skill-capability/REQUIREMENTS.md
  - .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-01-PLAN.md
  - .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-01-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-02-PLAN.md
  - .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-02-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-03-PLAN.md
  - .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-03-SUMMARY.md
  - tools/card_lineage.py
  - tools/test_card_lineage.py
  - tools/skill_coverage.py
  - tools/skill_mirror_drift.py
  - hooks/doctrine_cards.js
  - hooks/destructive_doctrine_card.js
  - vault/programs/skill-capability/card_source_digests.json
  - vault/programs/skill-capability/evidence/G-lineage.md
  - vault/programs/skill-capability/evidence/H-drift.md
  - vault/programs/skill-capability/ledger.json
  - vault/programs/skill-capability/owner-bundle.md
covered_digest: "v1:sha256:8caa3c98b70b559c50eeb45d954fe1f03dce69cfce3b30f80f3513ff29179b22"
behavior_unverified: 0
overrides_applied: 0
verifier: gsd-verifier subagent, host gex44, worktree sc-run, HEAD c1f6c6f9
---

# Phase 6: Compile-out lineage - Verification

**Goal:** Compiled-out cards carry source lineage, and a source change without re-derivation fails a gate.
**Requirements:** SC-G. **Host:** gex44 (python3). **HEAD:** c1f6c6f9 (after the 8/8 review fixes). **Re-verification:** No.

## Roadmap success criteria

| # | Criterion | Evidence | Verdict |
|---|-----------|----------|---------|
| 1 | Lineage field and gate, driven from both poles | Both cards end on a `// COMPILED-FROM:` trailer whose sha256 and commit the verifier recomputed independently with git. Live gate PASS. In a temp clone the verifier changed the source and re-recorded H only, and G read FAIL on SOURCE-CURRENT alone. Re-deriving the trailer and re-recording H made it PASS again (D1) | PASS |
| 2 | `--pillar G` PASS | `timeout 1900 python3 tools/test_skill_capability_program.py --pillar G` rc=0 `CEP_PILLAR_G=PASS`. The harness re-runs the gate argv. With state.G's prg pin zeroed in the clone it reads `CEP_PILLAR_G=FAIL` (L4) | PASS |

## Observable truths (plan must-haves)

| # | Plan | Truth | Status | Evidence |
|---|------|-------|--------|----------|
| 1 | 06-01 | Each card ends with a COMPILED-FROM trailer (skill, source, LF sha256 of the committed SKILL.md, the last commit that changed it) | VERIFIED | `tail -n 4` on both hooks. The sha matches `git show HEAD:... \| tr -d '\r' \| sha256sum` and the commit matches `git log -1 HEAD -- path` |
| 2 | 06-01 | The population is discovered, never listed, with a floor of 2 | VERIFIED | D5: an unregistered committed `hooks/new_card.js` raised population to 3 and the verdict to FAIL |
| 3 | 06-01 | All 10 clauses must PASS. An absent trailer is UNMEASURED, never PASS. A git failure is INCONCLUSIVE | VERIFIED | D6 (absent trailer -> UNMEASURED, FAIL). D3 (5 stubbed subcommands -> INCONCLUSIVE, no exception; real drift plus git failure stays FAIL) |
| 4 | 06-01 | The judge reads committed blobs only | VERIFIED | D4: uncommitted source edit plus untracked card -> PASS [] |
| 5 | 06-01 | It reuses smd and sc and adds no second comparator. H stays green | VERIFIED | Gates SKD 16/16 and SKC 17/17 match phase 4's verified counts. `--pillar D` and `--pillar H` PASS |
| 6 | 06-01 | `card_lineage.py` prints PASS population=2 | VERIFIED | `CARD_LINEAGE PASS population=2 head=c1f6c6f9`, rc=0 |
| 7 | 06-02 | The gate is driven from both poles, the drills reproduce exact fail sets, the core frozen-rule drill exists, and CR-01 multi-skill is covered | VERIFIED | `CLG_PASS=40/40`. Independent D1 and D2 (a second skill named without a trailer -> SKILL=FAIL) |
| 8 | 06-02 | Every clause is load-bearing | VERIFIED | The verifier's own mutant forced c_skill to always PASS. The gate read rc=1 `CLG_PASS=36/40`, with MULTI-SKILL-UNLINEAGED, SKILL-MISMATCH, EVERY-CLAUSE and EVIDENCE-CURRENT red. Restored |
| 9 | 06-02 | `G-lineage.md` is a deterministic render compared to the committed blob | VERIFIED | V-CLG-EVIDENCE-CURRENT ok, and it went red under the mutant |
| 10 | 06-03 | state.G is IMPLEMENTED_AND_VERIFIED with gate argv, prg pin, file pin, owner and commit evidence, savings [] | VERIFIED | Pins equal the LF sha256 of the HEAD blobs. The card_source_digests.json pin is the same in G and H (985aa980...). All 7 commits resolve |
| 11 | 06-03 | `frozen` equals FROZEN_AT, and the earlier pillars still PASS | VERIFIED | Python equality against ledger.json at 217d72b5. A, B, C, D, F, G, H all PASS. `--status` reports violations [] |
| 12 | 06-03 | `owner-bundle.md` has the `[G] (host: laptop)` lines | VERIFIED | Lines 13-15 (live cards, gate runtime, re-derivation duty). These are laptop owner-bundle items, not gaps |

**Score:** 12/12 truths verified, 0 behavior-unverified.

## Anti-patterns / info

- No TBD, FIXME or XXX in card_lineage.py, test_card_lineage.py, G-lineage.md or either hook.
- INFO: two figures in owner-bundle.md line 14 are stale: "23 drills" (now 32) and "at most 4.17 s" (now about 5-6 s). They are advisory text and are not pinned by the ledger.
- INFO: DISPATCHER-COVERED checks registered ⊆ population, so an unregistered card does not fail it. That card's own TRAILER clause does fail it (D5), so nothing escapes.

## Restoration

Every drill ran in `/tmp/v06clone`. Afterwards `git status` and `git diff --stat HEAD -- tools hooks skills vault/programs` are empty in the worktree. The only untracked phase file is this report. Nothing was committed.

## Confirmed facts (running log)

- HEAD c1f6c6f9 (`docs(06): code review fix report -- 8/8 findings fixed`). Workstream set to skill-capability.
- Gates (foreground, gex44, HEAD c1f6c6f9): `test_card_lineage.py` rc=0 `CLG_PASS=40/40 threshold=40/40` (40 `ok` lines); `card_lineage.py` rc=0 `CARD_LINEAGE PASS population=2 head=c1f6c6f9`, all 7 per-card clauses PASS for both cards + FLOOR/DISPATCHER-COVERED/H-RECORD-CURRENT PASS; `test_skill_drift.py` rc=0 `SKD_PASS=16/16`; `test_skill_coverage.py` rc=0 `SKC_PASS=17/17`; `test_card_precision.py` rc=0 `SCA_PASS=36/36`; `node hooks/tests/test-doctrine-cards.js` rc=0 `DOCTRINE_CARDS_PASS=37/37`; `node hooks/tests/test-destructive-doctrine-card.js` rc=0 `DDC_PASS=15/15`. D and H counts equal phase 4's verified 17/17 and 16/16, so the review fix to skill_coverage.py / skill_mirror_drift.py did not move D or H.
- Trailers checked independently of the tool: both hook files END on `// COMPILED-FROM: ...`. CW sha256=f1f52de4... equals `git show HEAD:skills/concurrent-writers-shared-tree/SKILL.md | tr -d '\r' | sha256sum`; commit=31e1e25c... equals `git log -1 --format=%H HEAD -- <that path>`. DS sha256=2985bd97... and commit=7f985799... match the same way.
- `timeout 1900 python3 tools/test_skill_capability_program.py --pillar X`: A, B, C, D, F, G, H each rc=0 `CEP_PILLAR_X=PASS` (G took 6 s; the CE harness `check_ledger` -> `Resolver.run_gate` re-runs state.G's gate argv `tools/test_card_lineage.py` when the terminal is IMPLEMENTED_AND_VERIFIED, so this PASS includes a fresh gate run). `--status` rc=0: closed [A,B,C,D,F,G,H], open [E,I,J,K,L,M,N], `"violations": []`.
- Ledger at HEAD (the worktree copy is byte-equal to HEAD): state.G terminal IMPLEMENTED_AND_VERIFIED, savings []. Evidence: gate argv `["python","tools/test_card_lineage.py"]`; prg `evidence/G-lineage.md` sha256 abe493da... equals the LF sha256 of the HEAD blob; file `card_source_digests.json` 985aa980... equals the HEAD blob and equals state.H's pin for the same file; owner `hooks/doctrine_cards.js`; 7 commits (ee645e09, 3bc41bd5, edfd59a3, 03f580c1, a179624d, a057c82f, 3e60b990), all resolve and are 06-01/06-02 commits. state.H pins (H-drift.md 2e8cdccc..., H-live-gex44.json 43831a34..., card_source_digests.json 985aa980...) all equal the LF sha256 of the HEAD blobs.
- `frozen` at HEAD equals `frozen` in ledger.json at FROZEN_AT 217d72b5944a664fbc0baa1060c04617ff10f481 (python dict equality).

## Drills driven by the verifier (temp clone /tmp/v06clone of HEAD c1f6c6f9, autocrlf=false, hooksPath=/dev/null; the worktree's tools pointed at it with `--repo`)

- D1 (06-01, frozen rule core): the clone at HEAD reads `CARD_LINEAGE PASS population=2`. Two lines were appended to `skills/concurrent-writers-shared-tree/SKILL.md` and committed, then ONLY H was re-recorded (`skill_mirror_drift.py --record-cards`, committed). H reads `--cards` rc=0, both CURRENT. G reads rc=1 `CARD_LINEAGE FAIL`, with only `hooks/doctrine_cards.js SOURCE-CURRENT=FAIL` ("at 74ce0572 is 526c785d5924, trailer says f1f52de4c311: re-derive the card"); every other clause PASS.
- D1 other pole: the trailer was replaced with the `--trailer-for concurrent-writers-shared-tree` output and committed. G then reads FAIL on `H-RECORD-CURRENT` (CARD_CHANGED), because a card edit with no H re-record is caught. After H was re-recorded and committed, G reads `CARD_LINEAGE PASS`.
- D2 (06-01 CR-01): a body line naming "the `destructive-state-authorization` skill" was inserted into doctrine_cards.js above the lineage block, H was re-recorded (3 pairs), and both were committed. G reads rc=1 FAIL with `SKILL=FAIL: card names skill(s) with no lineage trailer: ['destructive-state-authorization']`.
- D3 (06-02 git failure): `smd.git_run` was stubbed to fail one subcommand, on the green clone. merge-base -> INCONCLUSIVE {COMMIT-ANCESTOR x2}; log -> INCONCLUSIVE {COMMIT-TOUCHES x2}; cat-file -> INCONCLUSIVE {DISPATCHER-COVERED, H-RECORD-CURRENT}; ls-tree and rev-parse -> INCONCLUSIVE. No exception escaped. Red control: real drift (commit 74ce0572) plus the merge-base failure still reads FAIL, including the measured SOURCE-CURRENT.
- D4 (06-02 committed-blob-only): an uncommitted edit to `skills/destructive-state-authorization/SKILL.md` plus an untracked new card file -> PASS [].
- D5 (06-01 discovered population): a committed, unregistered `hooks/new_card.js` naming a skill without a trailer -> population=3, its 7 clauses UNMEASURED, verdict FAIL rc=1. The population is discovered, not listed.
- D6 (06-01 absent trailer): with the COMPILED-FROM line deleted from destructive_doctrine_card.js and committed, its clauses go UNMEASURED and H-RECORD-CURRENT FAIL -> verdict FAIL.
- Observation (info, not a gap): DISPATCHER-COVERED checks registered ⊆ population ("2 registered card(s), all members"). An unregistered new card does not fail it, but its own TRAILER clause does (D5).
_Verified: 2026-10-03 · Verifier: Claude (gsd-verifier)_
