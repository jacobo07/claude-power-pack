---
phase: 06-compile-out-lineage
plan: 01
subsystem: skill-capability pillar G (compile-out lineage)
status: complete
tags: [lineage, compile-out, pillar-G, card, gate]
requires: [phase 4 review fixes WR-04/05/06 (committed_card_pairs, is_git_failure, tracked_paths)]
provides: [tools/card_lineage.py judge/fail_set/CLAUSES/population/trailer_for/parse_trailer, lineage trailers on both cards]
affects: [pillar H record + render + state.H pins, 06-02 drills, 06-03 G closure]
tech-stack:
  added: []
  patterns: [committed-blob-only judge, discovered population, clause table looked up at call time]
key-files:
  created: [tools/card_lineage.py]
  modified: [hooks/doctrine_cards.js, hooks/destructive_doctrine_card.js, vault/programs/skill-capability/card_source_digests.json, vault/programs/skill-capability/evidence/H-drift.md, vault/programs/skill-capability/ledger.json]
decisions:
  - "Render H-drift.md only after the record is committed (committed-blob reader); needed one extra commit"
  - "No DG-05 in-place card edits: both card texts are faithful to their current SKILL.md"
metrics:
  duration: "~6 min wall (20:40:46Z - 20:46:41Z)"
  completed: 2026-10-03
plan_head_before: df391c072f8952832c5baeee0e0aacc25c502c74
actuals:
  tokens: 8000
  tasks: 2
  commits: 4
---

# Phase 6 Plan 01: card lineage tool, card trailers and state.H re-pin Summary

Both compiled-out cards now end with a `COMPILED-FROM` trailer that names the skill, source path, LF sha256 and source
commit. `tools/card_lineage.py` finds the cards in the committed tree and judges them with 10 clauses, using committed
blobs only. It reuses pillar H's functions (`committed_card_pairs`, `card_source_state`, `card_drift`, `card_verdict`,
`tracked_paths`, `is_git_failure`) and `sc.CARD_TOKEN`. H's record and render were re-derived and the two state.H pins
were moved. Live result: `CARD_LINEAGE PASS population=2`.

PRE06 = `df391c072f8952832c5baeee0e0aacc25c502c74`

## Commits

| # | sha | subject |
|---|-----|---------|
| 1 | ee645e09 | feat(06-01): G -- card_lineage judge and lineage trailers on both compiled-out cards |
| 2 | 3bc41bd5 | feat(06-01): H -- card record re-derived after the lineage trailers; H-drift.md re-rendered |
| 2b | edfd59a3 | fix(06-01): H -- H-drift.md rendered from the committed record (deviation 1) |
| 3 | 03f580c1 | feat(06-01): G -- card lineage trailers; H record re-derived and its two pins moved |

## Trailer lines (verbatim, last line of each card)

hooks/doctrine_cards.js:
```
// COMPILED-FROM: skill=concurrent-writers-shared-tree source=skills/concurrent-writers-shared-tree/SKILL.md sha256=f1f52de4c3115d0aafc39d69c67a2e1ae7936ae63b26ecc9263d89f1150e57c0 commit=31e1e25ca20bdf1266aa48c832312ef983d5d1eb
```
hooks/destructive_doctrine_card.js:
```
// COMPILED-FROM: skill=destructive-state-authorization source=skills/destructive-state-authorization/SKILL.md sha256=2985bd97002abf0589a95080a7d29b447b7a703df9ccd319494dba45701cd0de commit=7f985799916ce6e12cbdc6e2495c47065366c14b
```
`--trailer-for` returned exactly the plan-time values for both skills. Each trailer is preceded by the two `// LINEAGE
(skill-capability pillar G): ...` comment lines. No line contains a backtick (`tail -n 3 | grep -c` gives 0), and
`node --check` passes on both hooks.

## DG-05 faithfulness (re-read of each SKILL.md against its card)

- **concurrent-writers-shared-tree -> `card()` in hooks/doctrine_cards.js:** the card says a pathspec names a file
  and not your hunks, so commit only your own lines through `git apply --cached` and leave the other lines untouched.
  This matches section 1 of the skill (commit isolation is file-granular; the non-interactive repair filters the diff
  to your own hunks and applies it to the index). The skill does not contradict "never stash, reset or checkout them
  away". No edit.
- **destructive-state-authorization -> `CARD` in hooks/destructive_doctrine_card.js:** the five questions match the
  skill's core rules. Q1 is content identity, not mtime/size/ids ("Choose the identity from the EFFECT"). Q2 is never
  destroying state nobody looked at. Q3 is recoverability. Q4 is per-item re-authorization and truthful batch reporting
  ("Batch operations: authorize per item"). Q5 is "refusal is not failure". No edit.

## Gate runs (last lines, gex44, foreground)

Before commit 1 (working tree holds the trailers):
- `node hooks/tests/test-doctrine-cards.js`: `DOCTRINE_CARDS_PASS=37/37` rc=0
- `node hooks/tests/test-destructive-doctrine-card.js`: `DDC_PASS=15/15` rc=0
- `python3 tools/test_card_precision.py`: `SCA_PASS=36/36` rc=0
- `python3 tools/test_skill_delivery.py`: `SD_PASS=53/53` rc=0
- `python3 tools/test_skill_coverage.py`: `SKC_PASS=16/17` rc=1. The one non-ok clause was `V-SKC-EVIDENCE-CURRENT`,
  INCONCLUSIVE with "render sources differ from HEAD": the committed-blob rule applies until the edit is committed.
  After commit 1 it was `SKC_PASS=17/17` rc=0 with V-SKC-EVIDENCE-CURRENT ok.
- Red pole before the trailers: `CARD_LINEAGE FAIL population=2 head=df391c07`. Both cards were
  TRAILER=UNMEASURED ("trailer absent") and the other six clauses were UNMEASURED ("no trailer"). The three gate
  clauses were PASS.

Final, at HEAD 03f580c1:
- `python3 tools/test_skill_drift.py`: `SKD_PASS=16/16` rc=0
- `python3 tools/test_skill_coverage.py`: `SKC_PASS=17/17` rc=0, `ok V-SKC-EVIDENCE-CURRENT`
- `node hooks/tests/test-doctrine-cards.js`: `DOCTRINE_CARDS_PASS=37/37`; `node hooks/tests/test-destructive-doctrine-card.js`: `DDC_PASS=15/15`; `python3 tools/test_card_precision.py`: `SCA_PASS=36/36`
- `python3 tools/test_skill_capability_program.py --pillar X` (timeout 1900): A, B, C, D, F and H each printed
  `CEP_PILLAR_<X>=PASS` with rc=0.
- Negative control for the re-pin: `ce.check_ledger` on the pre-re-pin ledger blob (HEAD~1) for H returned two L4
  failures ("sha256 changed since it was cited" for H-drift.md and card_source_digests.json). The pin check can go red.

`python3 tools/card_lineage.py` (text output at HEAD):
```
hooks/destructive_doctrine_card.js skill=destructive-state-authorization TRAILER=PASS SKILL=PASS SOURCE-PATH=PASS SOURCE-CURRENT=PASS COMMIT-ANCESTOR=PASS COMMIT-TOUCHES=PASS COMMIT-DIGEST=PASS
hooks/doctrine_cards.js skill=concurrent-writers-shared-tree TRAILER=PASS SKILL=PASS SOURCE-PATH=PASS SOURCE-CURRENT=PASS COMMIT-ANCESTOR=PASS COMMIT-TOUCHES=PASS COMMIT-DIGEST=PASS
FLOOR=PASS (population=2)
DISPATCHER-COVERED=PASS (2 registered card(s), all members)
H-RECORD-CURRENT=PASS (2 pair(s) CURRENT)
CARD_LINEAGE PASS population=2 head=03f580c1
```
`--json`: verdict PASS, population holds both card paths, and all 17 outcomes (7 x 2 cards + 3 gate clauses) are PASS.
`PATH=/nonexistent /usr/bin/python3 tools/card_lineage.py` gave rc=1 and printed `CARD_LINEAGE INCONCLUSIVE population=0
head=none reason=HEAD not resolvable: git not found: git executable not found on PATH or known Windows locations`, with
no Traceback.

## Acceptance checks

- Hooks diff vs PRE06: `git diff` rc=0, removed lines 0 (append only).
- D-coverage refs before and after (`hooks/destructive_doctrine_card.js:61`, `hooks/doctrine_cards.js:428`,
  `hooks/hook-dispatcher.js:427`, `:433`): `cmp` rc=0. Both card-hook cited lines are byte-equal at PRE06 and HEAD.
- In tools/card_lineage.py: there is no hashlib import. Every reuse name appears at least once (card_drift 1,
  card_source_state 2, committed_card_pairs 1, tracked_paths 1, is_git_failure 2, sc.CARD_TOKEN 2). The only
  `git-batch-*` literals are `git-batch-empty` and `git-batch-missing`. No quoted card path appears.
- Ledger diff: exactly `-  "H"` / `+  "H"`. `IMPLEMENTED_AND_VERIFIED 9` both before and after (N_PRE=9). frozen equals
  its FROZEN_AT copy (True).

## state.H pins (old -> new)

| ref | old sha256 | new sha256 |
|---|---|---|
| vault/programs/skill-capability/evidence/H-drift.md | 8d0ec0548710b6f9f36810efd3da766e626a41aa51d9100bbd7e02064622ce86 | 2e8cdccc72f76e7789b685082e028cb03d38c7e710e9440583022ebd91d2fa82 |
| vault/programs/skill-capability/card_source_digests.json | cdce72618407c85edda52e3c26f60cb2a4739ecd80fa6df6d351687fc79ada31 | 985aa98060ce510af28623274d2f757e8033198cffdeb122395fb9f5611f93d8 |

The record moved both `card_sha256` values (the trailer append). Both `source_sha256` values stayed the same, and
`recorded_at_commit` changed from 0a2ab9ea to ee645e09.

## Shipped API (for 06-02)

`judge(repo=smd.REPO, ref="HEAD") -> {verdict, head, reason, population, cards:[{card, trailer, clauses}], gate}`,
`fail_set(result)`, `CLAUSES` (10 entries, looked up at call time, signature `(ctx, member=None, trailer=None)`, where
`member` is `{"card": rel, "text": lf_text}`), `population(repo, sha, tracked) -> (members | None, reason)` (called
through the module global, so it can be wrapped), `trailer_for(repo, skill, ref="HEAD")`, `parse_trailer(text)`,
`LINEAGE_MARKER`, `CARD_CLAUSES`, `GATE_CLAUSES`. CLI: `--repo`, `--ref`, `--json`, `--trailer-for` (exit 2 for a bad
skill name, 1 for a refused trailer). Names are as the plan specified.

## Deviations from Plan

1. **[Rule 1 - Bug] H-drift.md render taken before the record was committed.** Task 1 says to run `--record-cards`,
   then `--write-evidence`, then commit both. The phase-4 WR-04 reader renders the record from its committed blob, and
   at that moment the record was still uncommitted. The render therefore said "Record unreadable (uncommitted: ...)",
   and commit 2 (3bc41bd5) carried that render. After commit 2, `test_skill_drift.py` gave `SKD_PASS=15/16`
   (V-SKD-EVIDENCE-CURRENT FAIL). Fix: re-ran `--write-evidence` with the record committed and committed only H-drift.md
   as edfd59a3 (no amend). SKD went to 16/16. Future re-records need this order: record, commit the record, render,
   commit the render.
2. **Branch allow-list.** The executor's per-commit worktree check expects `agent-*` branch names. This worktree is on
   `mission/skill-capability-run`, which the orchestrator named and earlier phases committed on. `git.base-branch
   --is-protected` returned false, so commits went ahead there.

## Out of scope / deferred

- `python3 modules/liveness/reachability.py` exits 1 on pre-existing ORPHAN debt under modules/ (for example
  tower/donegate and tower/ratchet). tools/card_lineage.py is not in its population or its output. Wiring the tool as G
  gate evidence is 06-03's job (the G closure). Not fixed here.
- I-02 from the plan check (state.H's reason text saying "16/16 clauses") belongs to phase 4 and was not touched.

## Known Stubs

None.

## Threat Flags

None. The tool is read-only, has no network access and writes no files. The hook change is comment-only.

## Self-Check: PASSED

- tools/card_lineage.py, both hooks (trailer last line), card_source_digests.json, H-drift.md and ledger.json exist,
  and each is committed.
- ee645e09, 3bc41bd5, edfd59a3 and 03f580c1 are all present in `git log`.
