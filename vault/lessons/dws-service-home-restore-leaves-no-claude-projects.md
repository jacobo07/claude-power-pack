---
title: A live leg on a service account must leave its home as it found it
tier: execution
date: 2026-10-18
source: Orca repo docs/dws/live-2026-10-18-row-70-resume-evidence.md (r70r4) and live-2026-10-18-row-59-model-turn-evidence.md (36876b70e7)
status: LESSON -- UKDL entry T-LIVE-LEG-MUST-RESTORE-THE-SERVICE-HOME-001
---

# A live leg on a service account must leave its home as it found it

## Evidence
- r70r4: past the trust dialog, the answer left a project entry in the service account's ~/.claude.json. svc-restore never touched that file, so the entry survived the run; it was removed by hand.
- The harness now removes only the leg's own projects keys (no byte restore: the serve keeps its login in that file) and reports HWF_CLAUDE_PROJECTS; the driver compares it.
- Passing runs print HWF_CLAUDE_PROJECTS=0, SVC_HOME_RESTORED=True, WITNESS_UNCHANGED=True, REMAINING=0, PROC_COUNT=0 (rows 59 and 70).

## Lesson
Backup and restore must cover every file the leg can write, not the files the harness knows about. Prove it with a counter the driver reads (here the project-key count), and restore by removing what the leg added when the file also holds state the host owns.