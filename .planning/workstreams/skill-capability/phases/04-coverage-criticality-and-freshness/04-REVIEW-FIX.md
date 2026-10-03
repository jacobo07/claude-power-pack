---
phase: 04-coverage-criticality-and-freshness
fixed_at: 2026-10-03
review_path: .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-REVIEW.md
iteration: 1
findings_in_scope: 13
fixed: 13
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Summary:** 13 in scope (CR-01, WR-01..08, IN-01..04), 13 handled, 0 skipped. WR-01 and WR-07 were handled as
directed: no behaviour change, the gap made attributable (WR-01) or stated as a measured limit in the evidence
(WR-07).

Host gex44, worktree sc-run, python3. Every fix was driven red first (a clause or mutant that failed on the
pre-fix code), then green. Verification ran in this worktree (`.claude/worktrees/sc-run`), not the main checkout.

## CR-01: absent or empty live root reads PASS

**Status:** fixed
**Commit:** f51fef33
**Files:** tools/router_freshness_gate.py, tools/skill_mirror_drift.py, tools/test_router_freshness_gate.py, tools/test_skill_drift.py
**Red:** new V-RFG-SKILL-DRIFT-NO-LIVE on the old code: `absent=PASS`, `empty=PASS`. New V-SKD-NO-LIVE-ROOT:
`absent --live rc=0, absent --json rc=0, empty --live rc=0, empty --json rc=0`, no UNMEASURED line.
**Green:** router line UNMEASURED for an absent root and for zero IDENTICAL+DRIFT; `live_report` INCONCLUSIVE for an
absent root and carries `compared`; `--live`/`--json` exit 1 with an `UNMEASURED` line on zero compared;
`--measure-live` refuses to record a zero-compared plane. Identical-copy controls still PASS / exit 0.

## WR-02: CRLF drills over JSON records cannot go red

**Status:** fixed
**Commit:** 028591bb
**Files:** tools/test_skill_drift.py, tools/test_skill_coverage.py
**Red:** mutant `smd.lf_bytes = identity` + `vgm._norm_sha = raw sha256` left the old V-SKD-CARD-SOURCE-CRLF `ok`.
**Green:** V-SKD-CARD-SOURCE-CRLF now records card + source LF in a temp repo, recommits them as CRLF blobs
(autocrlf=false): CURRENT through the LF digest, raw sha256 of the CRLF blob differs from the record, CRLF source edit
SOURCE_CHANGED. The same mutant now FAILs it. V-SKD-RECORD-DRILL lost its JSON CRLF control (could not go red).
V-SKC-RECORDING-CRLF now claims parse robustness only and names V-SKC-EVIDENCE-DRILL (raw-bytes compare of the
rendered .md) as the gate's CR-significant pole; it asserts that CR is insignificant to the JSON parse.

## WR-03: symlinked live subdirectory invisible

**Status:** fixed
**Commit:** e1f4a7e0
**Files:** tools/skill_mirror_drift.py, tools/test_skill_drift.py, evidence/H-drift.md, ledger.json (state.H H-drift.md pin)
**Red:** V-SKD-POLE-DRIFT mutant "extra symlinked dir" read `('IDENTICAL', [], [], [])`.
**Green:** a symlinked directory is an entry hashed by its link text (never descended, never omitted):
`('DRIFT', [], ['extra'], [])`. gex44 mirrored skills hold no symlinks (checked), so H-live-gex44.json is unchanged;
the H-drift.md Method line changed, re-rendered, H-drift.md re-pinned `5eae42e6...` -> `8d0ec054...`.

## WR-05: cat-file failures labelled UNTRACKED / DRIFT

**Status:** fixed
**Commit:** 8dbb0e64
**Files:** tools/skill_mirror_drift.py, tools/test_skill_drift.py
**Red:** V-SKD-CARD-SOURCE-GIT-FAILURE extended with a monkeypatched `batch_blobs`: `git-batch-rc128` (all pairs),
`truncated` / `badheader` / `ambiguous` (one pair) read `DRIFT`.
**Green:** `BATCH_FAILURES` covers every failure reason `batch_blobs` emits -> pair INCONCLUSIVE; `card_verdict` is
INCONCLUSIVE when every non-CURRENT row is INCONCLUSIVE; `--record-cards` refuses. Control `git-batch-missing` stays
UNTRACKED.

## WR-06: ls-tree not -z

**Status:** fixed
**Commit:** a326aa64
**Files:** tools/skill_mirror_drift.py, tools/test_skill_drift.py
**Red:** V-SKD-POLE-IDENTICAL extended with `réf.md` and skill dir `été`, identical live copy: old code
`('DRIFT', ['réf.md'])` and no row for `été`.
**Green:** local `tracked_paths` runs `ls-tree -r -z --name-only` (NUL split, surrogateescape) and returns the git
reason on failure; the dead quoted-path guard is removed. Both rows IDENTICAL; gex44 `--live` counts unchanged.

## WR-08: live plane counts directories without SKILL.md

**Status:** fixed
**Commit:** 4201575b
**Files:** tools/skill_coverage.py, tools/test_skill_coverage.py, evidence/D-live-gex44.json, evidence/D-coverage.md,
ledger.json (state.D pins for both)
**Red:** new V-SKC-LIVE-SKILL-DEFINITION (synthetic home) read `(['container', 'parked', 'real'], 3, 2, None,
['parked'])`: a stub naming a non-skill gave it an evidence item.
**Green:** both planes require SKILL.md; the rest are reported by name in `non_skill_dirs` and rendered, never
classified. gex44 re-recorded (`python3 tools/skill_coverage.py --measure-live --host gex44`, 2026-10-03T19:13:14Z):
skill_dirs 185 -> 161, non_skill_dirs 24, the 12 evidence items identical to the old recording. gex44 plane: coverage
none 183 -> 159; criticality high 11, medium 5, low 169 -> 145; high+none 9 (unchanged). Re-pinned D-coverage.md
`f46e7b12...` -> `b9673d64...`, D-live-gex44.json `319fd8e5...` -> `442578e8...`.

## WR-04: records and evidence read from the working tree

**Status:** fixed
**Commit:** b65dda45
**Files:** tools/skill_mirror_drift.py, tools/skill_coverage.py, tools/test_skill_drift.py, tools/test_skill_coverage.py
**Red:** new V-SKD-COMMITTED-RECORDS and V-SKC-COMMITTED-RECORDS (temp repos) read an edited recording, an untracked
recording and a re-rendered uncommitted evidence file as if committed. V-SKD-CARD-SOURCE-POLES "re-recorded, not
committed" read `a:CURRENT`; "second card registered, not committed" read `b:UNTRACKED` (discovery from the working
tree, hashing from blobs).
**Green:** `smd.committed_bytes` (`git cat-file blob HEAD:<rel>`, the same object `git show HEAD:<rel>` prints): a git
failure, or a working-tree copy missing / different after LF normalization, returns an `uncommitted ...` reason and
nothing is read. The card record, H and D recording discovery (tracked at HEAD; an untracked working-tree recording is
reported as uncommitted) and both EVIDENCE-CURRENT clauses read through it (INCONCLUSIVE on a reason). Card pairs are
discovered from the committed dispatcher + hook blobs at the digests' commit (`discover_cards(read_disk=False)`). D
EVIDENCE-CURRENT is also INCONCLUSIVE while a render source differs from HEAD (driven with a faked `git status`, and
with a git failure). Consequence for operators: `--write-evidence` / `--record-cards` / `--measure-live` read
INCONCLUSIVE until committed (observed during WR-07). No evidence render changed; no pin moved.
**Stated limit:** D's classification sources (dispatcher, hooks, adapters, CLAUDE.md, HARD_RULES.md, heat map) are
still read from the working tree; they are only checked to be clean against HEAD, not read as blobs.

## WR-01: V-RFG-CLEAN red, two causes

**Status:** handled as directed (no behaviour change)
**Commit:** 6b2cee62
**Files:** tools/test_router_freshness_gate.py
V-RFG-CLEAN still runs the real router and the host's real `~/.claude/skills` and still FAILs on gex44. Its diagnostic
now names every failing sub-check:
`V-ROUTER-SKILL-DRIFT: 24 repo skills vs ~/.claude/skills: IDENTICAL 13, DRIFT 1, INCONCLUSIVE 0, ABSENT_LIVE 10;
V-ROUTER-LINKS: router absent`. Attribution: `router absent` is the pre-existing `router_path()` layout issue on this
non-install clone (not phase 4); V-ROUTER-SKILL-DRIFT is real gex44 drift (android-reverse-engineering missing 4 `.ps1`
scripts live), kept honest and not masked. Host red pole: `python3 tools/skill_mirror_drift.py --live` exit 1.

## WR-07: `./x.js` registrations invisible to the coverage sweep

**Status:** handled as directed (stated limit, no behaviour change)
**Commit:** 187b6952
**Files:** tools/test_skill_coverage.py, evidence/D-coverage.md, ledger.json (state.D D-coverage.md pin)
D-coverage.md now renders a measured limit line counted from the independent `script:` marker: 33 CHAIN_MAP
`script:` lines in the `./<file>` form are not parsed; 26 resolve to a file under `hooks/`, 0 of those emit a deny and
name a backticked skill; 7 have no file under `hooks/` in this checkout and cannot be judged (named in the line).
V-SKC-REGISTRATIONS still does not reconcile that count (stated in the line). D-coverage.md re-pinned
`b9673d64...` -> `a23854ef...`.

## IN-01: V-SKC-CLASS-TOTAL tautology

**Status:** fixed. **Commit:** 30d38e43. The clause also runs its check on an invented-class mutant and a
dropped-row mutant and FAILs unless both are caught; with the check disabled it reads FAIL (driven).

## IN-02: `--compare` misses vanished rows, raises on malformed recordings

**Status:** fixed. **Commit:** a42b2935. Red: new V-SKD-COMPARE read `rc=0, moved 0` for a vanished row and
AttributeError / KeyError for a JSON list / row without status. Green: vanished rows are MOVED, malformed recordings
print INCONCLUSIVE, exit 1; unchanged control exits 0. gex44 `--compare H-live-gex44.json`: `moved 0`.

## IN-03: router git-failure branch had no clause

**Status:** fixed. **Commit:** a7827168. New V-RFG-SKILL-DRIFT-GIT-FAILURE (git missing -> FAIL with
`INCONCLUSIVE: git not found`, git-present control PASS); driven red with the monkeypatch removed.

## IN-04: nits

**Status:** fixed. **Commit:** c3331947. The `destructive-state-authorization` lookup in V-SKC-CRITICALITY-RULE is a
FAIL line instead of a KeyError (driven with the row removed); the `evidence_current` docstring now says it returns a
bool.

## Ledger

Only sha values in state.D / state.H changed (no commit refs added; the format does not require them; `frozen` and
every other state entry byte-identical):
- state.H H-drift.md `5eae42e6...` -> `8d0ec054...` (e1f4a7e0)
- state.D D-live-gex44.json `319fd8e5...` -> `442578e8...` (4201575b)
- state.D D-coverage.md `f46e7b12...` -> `b9673d64...` (4201575b) -> `a23854ef...` (187b6952)
- unchanged: H-live-gex44.json, card_source_digests.json

**Stale prose left for the ledger owner (not edited, per the "sha only" instruction):** state.D.reason still says
"15/15 clauses", "185 skill dirs ... none 183; criticality high 11, medium 5, low 169" and "drops it to 10/15"; the gate
is now 17/17 and the gex44 plane 161 skills, none 159, high 11, medium 5, low 145 (high+none still 9). state.H.reason
still says "13/13 clauses"; the gate is now 16/16.

## Verification (ran in the worktree `.claude/worktrees/sc-run`, host gex44, python3)

- `python3 tools/test_skill_capability_program.py --pillar X`: A, B, C, D, H each `CEP_PILLAR_X=PASS`
- `python3 tools/test_skill_coverage.py`: `SKC_PASS=17/17`
- `python3 tools/test_skill_drift.py`: `SKD_PASS=16/16`
- `python3 tools/test_router_freshness_gate.py`: `ROUTER_GATE_TESTS=12/13`, the one FAIL is V-RFG-CLEAN, attributed
  above (pre-existing router layout + real gex44 drift)
- `python3 tools/skill_mirror_drift.py --live`: exit 1 (DRIFT 1, the real android drift); `--cards`: both CURRENT, exit 0

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
