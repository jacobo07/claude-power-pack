# R2 receipt -- HARD RULES mirror floor cut (tranche context-runtime-4)

VERDICT: PASS (in-repo cut measured; live probe: PENDING)

## Compiler
`modules/hard_rules/writer.py` writes both `vault/hard_rules/HARD_RULES.md` (archive) and the
`<!-- PP-HARD-RULES-START/END -->` block of `CLAUDE.md`. It was append-only and had no filter.
I added `stub_reason(entry)`, `prune_stub_rules(path, dry_run)` and a CLI
(`python -m modules.hard_rules.writer --prune [--dry-run] [paths]`). Running the CLI regenerated
both the archive and the mirror. No generated block was edited by hand.

The archive and the mirror had already diverged before this change. HR-SECRET/CASCADE/OUTPUT/... exist only in
CLAUDE.md, and HR-REVIVAL-*/HR-PANE-MAP-* exist only in the archive. So the compiler prunes each file in
place instead of rebuilding the mirror from the archive, which would have dropped 22 real rules.

## Entries removed (from both files)
| id | reason (from `stub_reason`) |
|---|---|
| HR-002 | test entry for the auto-propose pipeline ("ZZZ") |
| HR-003 | TRIGGER derived from a heading (`Before: UKDL S+++ ...`) |
| HR-004 | TRIGGER derived from a heading; STOP is a UKDL table fragment |
| HR-005 | STOP is a sliced markdown table fragment (`|\n|---|...`) |
| HR-006 | TRIGGER derived from a heading; STOP is generic boilerplate |
| HR-007 | TRIGGER derived from a heading; STOP is generic boilerplate |

HR-001 is kept. It has a real trigger and a real STOP. All 29 named real rules are kept, and so are the
archive-only HR-REVIVAL-*, HR-PANE-MAP-* and HR-NOVELTY-001.

## Commands (repo root, Python312)
| command | exit |
|---|---|
| `python tools/test_hard_rules_mirror.py` (before prune: red pole, 4/6) | 1 |
| `python -m modules.hard_rules.writer --prune --dry-run` | 0 |
| `python -m modules.hard_rules.writer --prune` | 0 |
| `python tools/test_hard_rules_mirror.py` (after: HRM_PASS=6/6) | 0 |
| `python tools/test_hard_rules.py` (HARDRULES_PASS=14/14, baseline 233 passed) | 0 |
| `python tools/verify_hard_rules.py` (HARDRULES_PROBE=7/7) | 0 |

## Measurements (stdin python script: `git show HEAD:CLAUDE.md` vs the worktree, before the commit)
| | before | after | delta |
|---|---|---|---|
| CLAUDE.md chars | 35,804 | 33,387 | -2,417 |
| CLAUDE.md est. tokens (chars/4, estimate) | 8,951 | 8,346 | -605 |
| mirror block chars | 22,844 | 20,427 | -2,417 |
| mirror block est. tokens (chars/4, estimate) | 5,711 | 5,106 | -605 |

live probe: PENDING (not launched; its spend would not be metered in this tranche).

## Debt
- `append_hard_rule` / `bug_to_hardrule.py install` do not call `stub_reason`, so a stub could be
  re-installed. I did not gate it because test_hard_rules fixtures append heading-style rules.
  Next step: refuse stubs at install, or run `--prune` after install.
- Archive and mirror have diverged (see above). Reconciling them is out of scope here.
- `tools/test_hard_rules.py` writes side effects into the tree (`vault/knowledge_base/session_lessons.md`,
  `ukdl-universal.md`, `vault/osa/never_again_log.jsonl`, `vault/hard_rules/auto_*.md`). These are left
  uncommitted and untouched.

COMMITS: cd859053d64f0abe645cc317265c7e084a2f009a
