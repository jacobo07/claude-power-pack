---
phase: 06-compile-out-lineage
plan: 03
subsystem: skill-capability pillar G (ledger closure)
status: complete
tags: [ledger, pillar-closure, evidence, pillar-G]
requires: [06-01 card trailers + H re-pin, 06-02 tools/test_card_lineage.py 30/30 + G-lineage.md]
provides: [state.G IMPLEMENTED_AND_VERIFIED, owner-bundle [G] lines]
affects: [--final (G now re-runs tools/test_card_lineage.py), every future card re-record (moves the G and H pins)]
tech-stack:
  added: []
  patterns: [single-line ledger replacement with pre/post byte comparison, in-process verifier negative controls]
key-files:
  created: []
  modified: [vault/programs/skill-capability/ledger.json, vault/programs/skill-capability/owner-bundle.md]
decisions:
  - "Liveness: no registry edit. The reachability scanner reads modules/ only, the registry has no tools/ rows, and phase 6 touched nothing under modules/; a declaration for a tools/ file would be a row nothing reads"
  - "Commit evidence = the 7 task commits listed in the 06-01 and 06-02 commit tables; the docs-only SUMMARY commits are not cited"
  - "One commit for the plan, as the plan specifies (ledger + bundle + SUMMARY), so the last-commit subject check holds"
metrics:
  duration: "~4 min wall (21:00:59Z - 21:05Z)"
  completed: 2026-10-03
plan_head_before: ef38347d3d11c32a3bd4326fd4430cded34d6a8a
actuals:
  tokens: 3000   # chars/4: G ledger line 2596 B + bundle append 2257 B + this SUMMARY ~7 KB
  tasks: 2
  commits: 1
---

# Phase 6 Plan 03: pillar G ledger closure Summary

state.G is now IMPLEMENTED_AND_VERIFIED, the frozen prediction. The verifier re-runs `python tools/test_card_lineage.py`
and accepts both sha256 pins on gex44. The owner bundle gained three `[G] (host: laptop)` lines. All seven closed
pillars (A, B, C, D, F, G, H) print PASS. `--status` lists no violations.

## Preconditions (foreground, HEAD ef38347d)

- `python3 tools/test_card_lineage.py`: 30 `ok` lines, `CLG_PASS=30/30  threshold=30/30`, 4.4 s wall.
- `python3 tools/card_lineage.py`: `CARD_LINEAGE PASS population=2 head=ef38347d`.
- `git status --porcelain` on the two tools, the two cards, G-lineage.md, card_source_digests.json, ledger.json and
  owner-bundle.md was empty.
- `git branch -r --contains`: trailer commit 31e1e25c is on `origin/feature/knowledge-acquisition` and
  `origin/mission/skill-capability`. 7f985799 is on both of those, plus `origin/bench/s3b` and `origin/bench/s4`.

## Liveness (caller item)

`python3 modules/liveness/reachability.py` exited rc=1 with `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 |
gate offenders: 64`. Neither new tool can be a new entry:

- The scanner only reads `modules/`. Its own report says "`tools/` is NOT scanned".
- `git diff --stat df391c07..HEAD -- modules/` is empty.
- `modules/liveness/reachability.py` is byte-equal to its PRE06 copy.
- `vault/liveness/reachability_registry.json` has keys `known_orphans` and `modules` and lists 154 modules, none
  containing "tool". A declaration there would be a row the scanner never reads, so I made no registry edit.

`tools/card_lineage.py` is named in both live cards (`hooks/doctrine_cards.js:507`,
`hooks/destructive_doctrine_card.js:143`), which makes it a tool seed. It imports only `skill_coverage` and
`skill_mirror_drift`, both under tools/, so it adds no module. `tools/test_card_lineage.py` is reached as the state.G
gate argv. The rc=1 comes from the ORPHAN debt that already existed under modules/. None of it is ours.

## Task 1: state.G written (tracer)

The script `/tmp/06-03-close-g.py` (Write tool, run with python3) checked these before and after the edit:

- frozen equals its copy at FROZEN_AT 217d72b5.
- state.G was exactly `{terminal: null, evidence: [], savings: []}`.
- The frozen G owner is `["hooks/doctrine_cards.js"]`.
- Each pinned sha equals `ce.lf_sha256` of the working file and also the LF sha256 of its HEAD blob.
- The card_source_digests.json sha equals the state.H pin (985aa980...).
- All 7 commits are ancestors of HEAD.
- The reason does not match `ce.DEFERRAL_PROSE`.
- `ce.gate_argv_problem(argv)` is None.

The script replaced the single `  "G": ` line (line 105) and then re-checked: frozen unchanged, every other state entry
equal to its pre-edit read, the same line count, every non-G line byte-identical, and the trailing newline kept. It
printed `STATE_G_WRITTEN line 105 prg f852af7f... rec 985aa980... commits 7`.

state.G evidence list (verbatim):
```
[{"kind": "gate", "argv": ["python", "tools/test_card_lineage.py"]},
 {"kind": "prg", "ref": "vault/programs/skill-capability/evidence/G-lineage.md", "sha256": "f852af7ff6214faf3169068b34bd1cf1419b5f691ff07c8689af50b8a3a713f0"},
 {"kind": "file", "ref": "vault/programs/skill-capability/card_source_digests.json", "sha256": "985aa98060ce510af28623274d2f757e8033198cffdeb122395fb9f5611f93d8"},
 {"kind": "owner", "ref": "hooks/doctrine_cards.js"},
 {"kind": "commit", "ref": "ee645e09"}, {"kind": "commit", "ref": "3bc41bd5"}, {"kind": "commit", "ref": "edfd59a3"},
 {"kind": "commit", "ref": "03f580c1"}, {"kind": "commit", "ref": "a179624d"}, {"kind": "commit", "ref": "a057c82f"},
 {"kind": "commit", "ref": "3e60b990"}]
```
savings `[]`. The reason names host gex44, the trailer fields, both cards and their skills, the 10 clauses, the
committed-blob rule, the 23 drills with exact fail sets, the load-bearing proof and the core result. It also covers the
H re-pin in 06-01 through H's own re-derivation, the shared card_source_digests.json pin, and the laptop plane as `[G]`
items. It claims no saving.

Acceptance:
- `git diff -U0 -- ledger.json` gave rc=0. `grep -oE '^[-+]  "[A-N]"'` printed exactly `-  "G"` and `+  "G"`.
- The one-liner printed `IMPLEMENTED_AND_VERIFIED [['python', 'tools/test_card_lineage.py']] []`.
- `--pillar G` printed `CEP_PILLAR_G=PASS` with rc=0 in 3.6 s, which is about the gate's own runtime, so the gate did
  run.

Negative controls (`/tmp/06-03-negctl.py`, in-process `ce.check_ledger` on modified copies, ledger file untouched):
- live: `[]`
- gate argv changed to a failing command: `L5 G: gate python tools/card_lineage.py --no-such-flag rc 2: ...`
- prg sha256 zeroed: `L4 G: prg file .../G-lineage.md sha256 changed since it was cited`
- owner swapped to the other card: `L4 G: owner hooks/destructive_doctrine_card.js is not one of the pillar's frozen owners ['hooks/doctrine_cards.js']`

## Task 2: owner bundle and regression

I appended three `[G] (host: laptop)` lines. All the commands they cite were checked to exist (`--trailer-for`,
`--record-cards`, both `--write-evidence` flags):

1. **Live cards.** The laptop dispatcher loads the checkout's own hooks, so the trailers arrive with the branch. Any
   `~/.claude/hooks/` copies show as drifted until they are re-synced. gex44's `~/.claude/hooks/` holds neither card;
   I checked this read-only. The two trailer commits are on the two named remotes.
2. **Gate runtime.** The gate builds temp git repos and runs 23 drills. The gex44 maximum was 4.17 s (06-02 timings
   3.36 / 4.17 / 3.36 s; 4.4 s wall in this plan). The laptop runtime is not measured. CE allows 1800 s.
3. **Behaviour inherited.** This line gives the re-derivation order for either source SKILL.md, ending with both the G
   and H pin moves. Re-recording H alone does not clear G.

Acceptance:
- `git diff -U0 -- owner-bundle.md` gave rc=0.
- `grep -c '^-[^-]'` printed 0.
- The first 9815 bytes (the whole pre-edit file) match the pre-edit copy (`cmp` equal).
- `grep -c '^\[G\]'` printed 3.

Regression (foreground, `timeout 1900`, working tree holding the ledger + bundle edits):
```
rc_A=0 t=5s   CEP_PILLAR_A=PASS
rc_B=0 t=0s   CEP_PILLAR_B=PASS
rc_C=0 t=1s   CEP_PILLAR_C=PASS
rc_D=0 t=0s   CEP_PILLAR_D=PASS
rc_F=0 t=0s   CEP_PILLAR_F=PASS
rc_G=0 t=5s   CEP_PILLAR_G=PASS
rc_H=0 t=2s   CEP_PILLAR_H=PASS
```
state.E is not terminal (null), so `--pillar E` was not run. `--status` returned rc=0 with `open` E, I, J, K, L, M, N,
`closed` A, B, C, D, F, G, H, and `violations` `[]`.

## Deviations from Plan

1. **Load-bearing figure taken from the 06-02 SUMMARY, not the plan text.** The plan's reason template says "nine
   forced-pass flips + the marker-only population mutant". 06-02 measured "10 forced passes flipped their drill
   FAIL->PASS", plus two mutants run outside the gate (COMMIT-DIGEST always PASS: 23/28; worktree-reading
   SOURCE-CURRENT: 27/28). The plan says to copy figures from the SUMMARYs only, so the reason carries the measured
   figures.
2. **No liveness registry edit**, for the reasons given above. This is the safest option, because a declaration for a
   tools/ file would claim a coverage the scanner does not provide.
3. **Single commit** for both tasks, as the plan specifies. The per-task protocol was not used here, because a second
   commit would break the plan's last-commit-subject check.

## Known Stubs

None.

## Threat Flags

None. T-06-10..13 are mitigated as planned:
- frozen was asserted before and after, and CE L2 passes.
- Peer entries were compared against the pre-edit read.
- The red-gate precondition was run before writing, and CE L5 re-runs the gate (the negative control shows L5 can go red).
- The reason names gex44, and laptop items appear only as `[G]` bundle lines.

## Self-Check: PASSED

- ledger.json state.G and the three `[G]` bundle lines are present on disk.
- The 7 cited commits are ancestors of HEAD (`git merge-base --is-ancestor`, checked in the script).
- G-lineage.md and card_source_digests.json exist at their pinned LF sha256.
