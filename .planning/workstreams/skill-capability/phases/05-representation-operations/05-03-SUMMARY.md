---
phase: 05-representation-operations
plan: 03
subsystem: skill-capability / pillar F
status: complete
tags: [ledger, closure, owner-bundle, pillar-F]
requires: [05-01 (sweep + F-sweep-gex44.json, feat ec706ab8), 05-02 (operation ledger + F-representation.md, feat e4947f62)]
provides: [ledger state.F terminal IMPLEMENTED_AND_VERIFIED, owner-bundle [F] lines]
affects: [program --final (F no longer open)]
tech-stack:
  added: []
  patterns: [one-line ledger replacement with ndiff assertion, figures copied from the gate's --json, committed-blob LF sha256 pins]
key-files:
  created: []
  modified:
    - vault/programs/skill-capability/ledger.json
    - vault/programs/skill-capability/owner-bundle.md
decisions:
  - "state.F = IMPLEMENTED_AND_VERIFIED (D-01/D-03); savings [] because the only candidate group sits on the gex44 plane and D-LISTING is the laptop listing"
  - "The dedup group managing-sleepy-skills + sleepy-skills is recorded as an OWNER decision on gex44; no operation applied, saving UNMEASURED and possibly 0"
  - "The laptop [F] line names the LISTING_HOSTS host-string precondition (05-02 dev 7) and --compare timing (05-01 dev 2) instead of changing the gate"
metrics:
  duration: ~12 min
  completed: 2026-10-03
estimate:
  tokens: 45000
  tasks: 2
actuals:
  tokens: 9000
  tasks: 2
  commits: 1
plan_head_before: 9845ed020d96b246a6fb5941916691c7aa91b6d5
---

# Phase 5 Plan 03: pillar F ledger closure Summary

Pillar F is closed in the program ledger. `state.F` is now IMPLEMENTED_AND_VERIFIED, and the CE verifier accepts it on gex44 by re-running `tools/test_skill_representation.py` (15/15). Only the `"F":` line of ledger.json changed. Two `[F]` Owner lines were appended to the bundle: the laptop procedure, and the gex44 dedup group as an Owner decision.

## Figures (read at execution time, HEAD 9845ed02, from the gate's `--json` and printed output)

- Precondition: `python3 tools/test_skill_representation.py` returned rc=0 with `SR_PASS=15/15`. `vault/programs/skill-capability/` and `tools/` were clean.
- Sweep `F-sweep-gex44.json` at repo_commit 01f4182a:
  - repo plane: 24 skills of 24 entries
  - gex44 plane: 161 skills of 186 entries (no_skill_md 24, non_dir 1)
  - drift_excluded: 14
- 1 group: `managing-sleepy-skills` + `sleepy-skills`.
  - SKILL.md bodies are identical: body_sha 01e535170bf2…
  - Both declare fm name `managing-sleepy-skills`, and managing-sleepy-skills ⊆ sleepy-skills.
  - Laptop status in all 4 rows: `UNMEASURED (not in watch set)`. entries_upper_bound 1.
- `V-FO-ENTRIES 0 operations applied`; `V-FO-DRILLS 21 drills (2 positive controls)`.
- D-LISTING startup tokens: 87739 before, 89844 after. D-SESSIONS: 8 of 12. Both come from the frozen denominators in the ledger.

## state.F as written

- Evidence: gate `["python","tools/test_skill_representation.py"]`
- prg `evidence/F-representation.md`: sha256 1ca8386fe6ea…
- file `evidence/F-sweep-gex44.json`: sha256 8b17edc5081b…
- file `f-operations.json`: sha256 a19b06cf0570…
- owners `modules/skill_router/skill_index.py` and `vault/plans/skill-virtualization-k-slice-2026-10-03.md`
- commits `ec706ab8` and `e4947f62`
- savings `[]`

Every sha256 is CE `lf_sha256` of the working file. Before pinning, the script asserted that this equals the LF sha256 of the `HEAD:` blob and that the path is clean.

The reason paragraph was built inside the script from those figures. It cites D-01 and D-03. It was checked against `DEFERRAL_PROSE` (no match) and ends with "Observed on host gex44; this pillar claims no saving."

The script, `/tmp/f0503_close.py` (not committed), asserted the following:
- exactly one `  "F": ` line, holding `terminal: null` before the edit;
- the ndiff has exactly 1 removed line and 1 added line;
- the trailing comma is kept;
- parsed `state.F` equals the built object;
- `frozen` equals its copy at FROZEN_AT 217d72b5 (sort_keys dump);
- every other state entry equals its pre-edit parse.

## Tasks

| # | Task | Commit |
|---|---|---|
| 1 | Tracer: state.F from `--json`, owner `[F]` lines, `--pillar F` PASS | 03cd4730 (single plan commit; Task 2 commits both files) |
| 2 | Regression of terminal pillars, `--status`, pathspec commit | 03cd4730 |

Tracer gate check (auto): before any expansion, `--pillar F` returned rc=0 with `CEP_PILLAR_F=PASS`. `git diff --numstat` gave `1 1 ledger.json` and `2 0 owner-bundle.md`. The owner-bundle diff showed `grep -c '^+\[F\]'` = 2 and `grep -c '^-[^-]'` = 0.

L5 is proven to actually run (instrument check). An in-process `ce.check_ledger(..., only=['F'])` with a counting Resolver made 1 gate call (`['python','tools/test_skill_representation.py']`) and returned `[]` on the real gate. When the resolver forced rc 1, it returned `['L5 F: gate python tools/test_skill_representation.py rc 1: forced']`. The 0.34 s `--pillar F` wall time matches the gate's own 0.26 s.

## Gate results (foreground, timeout 1900, after commit 03cd4730)

```
A rc=0 CEP_PILLAR_A=PASS
B rc=0 CEP_PILLAR_B=PASS
C rc=0 CEP_PILLAR_C=PASS
D rc=0 CEP_PILLAR_D=PASS
F rc=0 CEP_PILLAR_F=PASS
H rc=0 CEP_PILLAR_H=PASS
--status rc=0: open ['E','G','I','J','K','L','M','N'] closed ['A','B','C','D','F','H'] violations []
python3 tools/test_skill_representation.py: SR_PASS=15/15 (rc 0)
```

The same six PASS lines and `--status` violations `[]` were also observed before the commit.

## Commit

- `03cd4730 docs(05-03): F -- close pillar F in the ledger with gate + prg evidence on gex44`. `git log -1 --format=%s` matches the subject.
- `git show --stat` lists exactly ledger.json (1+/1-) and owner-bundle.md (2+). Nothing was deleted.
- Afterwards, `git status --porcelain -- vault/programs/skill-capability/` is empty.
- It was committed by pathspec with `-F` from `/home/kobii/.claude/jobs/88cfe52b/tmp/msg-0503.txt`. The branch is `mission/skill-capability-run`, which is not protected (`git.base-branch --is-protected` = false). Nothing was pushed.

## Owner bundle `[F]` lines (summary)

- `[F] (host: laptop)`: covers the following.
  - The laptop sweep `--measure-live --host laptop --out evidence/F-sweep-laptop.json` plus a commit.
  - `--compare` is timing-sensitive: the live `claude-power-pack` hook logs move `dir_digest` (05-01 dev 2).
  - The operation procedure: two fresh listing-family sessions (8 of 12) with `listing_floor_probe.py` under new labels, two delivery windows, then one `f-operations.json` entry.
  - The LISTING_HOSTS precondition (05-02 dev 7). V-FO-RECALL accepts only host `laptop`. `test_skill_delivery.py --measure-live` records `socket.gethostname()` and has no `--host` flag (C-window-G.json records `kobicraft-gex44`). So the laptop windows are refused until `LISTING_HOSTS` is edited on purpose in its own commit. Window host fields must never be hand-edited.
  - The only recall-measurable skill today is `concurrent-writers-shared-tree`.
  - Upper bound per group is distinct names - 1 entries. The cap refills, so the saving may be 0.
  - The terminal does not depend on this line.
- `[F] (host: gex44)`: the managing-sleepy-skills / sleepy-skills group, recorded as an OWNER decision with no operation applied.
  - Identical body, shared fm name, subset relation.
  - Upper bound 1 entry on gex44. This is not a D-LISTING figure: the saving is UNMEASURED and may be 0.
  - This run never edits `~/.claude`. The `--compare` caveat is repeated here.
  - The terminal does not depend on this line.

## Deviations from Plan

1. **Some figures come from the gate's printed output, not from `--json`.** The `--json` output carries no drill count, clause count, operation count, `skill_md_identical` or member frontmatter names. The script took these from the same HEAD's printed gate run (`SR_PASS=15/15`, `V-FO-DRILLS 21 drills (2 positive controls)`, `V-FO-ENTRIES 0 operations applied`) and from the committed `HEAD:` blob of F-sweep-gex44.json, and asserted each before using it. "19 refusals" is 21 minus the 2 positive controls, as 05-02 recorded.
2. **The owner lines cover three items the orchestrator asked for beyond the plan text:** 05-02 dev 7 (host string), 05-01 dev 2 (`--compare` timing) and the dedup group as an OWNER item. They are still exactly two `[F]` lines, which keeps the acceptance `grep -c '^+\[F\]'` = 2. The safest option was applied: no gate edit, and no operation.
3. **Single commit for Tasks 1 and 2**, as the plan's Task 2 instruction and acceptance (`git show --stat HEAD` = 2 files) require.
4. **This file was written incrementally** while the work ran, then replaced with this final text.

## Known Stubs

None. `savings: []` is deliberate and stated in the reason: no plane-matched figure exists.

## Threat Flags

None. These are data-only edits to two ledger files.

## Self-Check: PASSED

- FOUND vault/programs/skill-capability/ledger.json (state.F terminal) and owner-bundle.md (2 `[F]` lines)
- FOUND commit 03cd4730 (`git rev-list --count 9845ed02..HEAD` = 1)
