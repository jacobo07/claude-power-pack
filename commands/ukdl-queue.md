---
name: ukdl-queue
description: Review the FD flywheel's UKDL candidate queue -- the hard-rule/trap candidates captured from landed commits in every repo. Shows pending counts estate-wide, lists one repo's candidates, and records promote / reject / under-review decisions. Promotion is refused unless the rule already exists as a heading in ukdl-universal.md; nothing is ever promoted automatically.
---

# /ukdl-queue -- UKDL candidate review

The flywheel (`modules/fable_distillation/fd_07_flywheel.py`) writes one candidate ledger per repo
under `~/.claude/state/fable_distillation/`. Without a reviewer the queue is write-only
(T-UKDL-CANDIDATES-WRITE-ONLY-001): on 2026-10-09 it held 409 candidates in 65 ledgers and had
recorded 3 decisions ever.

## Run
```
python -m modules.fable_distillation.ukdl_queue --summary                     # pending per repo
python -m modules.fable_distillation.ukdl_queue --pending --repo <repo-root>  # one repo's queue
```
Run from `~/.claude/skills/claude-power-pack`.

## Decide
1. Write the rule into `vault/knowledge_base/ukdl-universal.md` as a `### <ID>` heading first.
2. `--promote <fingerprint> --rule-id <ID> --repo <repo>` (refused if the heading does not exist).
3. Or `--reject <fingerprint> --reason "<why>"` (a rejection with no reason is refused), or
   `--under-review <fingerprint>`.

Candidates are commit-derived claims, not validated knowledge (HR-ACQ-NO-AUTOPROMOTION-001 applies
in spirit): never batch-promote; each promotion needs a written rule behind it.
