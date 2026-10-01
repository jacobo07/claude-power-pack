---
type: improvement
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-system-prompts-leaks]
status: IN-PROGRESS
effort: S
graduated_to: CLAUDE.md (PP project, "## Compact Instructions")
---

# Add a `## Compact Instructions` section

## Evidence

- Reported Claude Code `/compact` prompt: "There may be additional summarization instructions
  provided in the included context. If so, remember to follow these instructions", with
  `## Compact Instructions` as the example ([[2026-09-30-system-prompts-leaks]], `compact.md` @ `b632b67`).
- No `CLAUDE.md` under `~/.claude` contains such a section (grep, 2026-09-30); neither does
  `C:\Users\User\CLAUDE.md`.

## Proposal

A short section (≤10 lines) in the PP project `CLAUDE.md` telling every compaction what to keep
verbatim, for example:
- the current `RESUMPTION_FILE.md` path and its next action;
- any HR-* trigger that fired this session, and any Owner bypass phrase given;
- pending Owner decisions, stated as questions;
- the wiki's last `log.md` entry, if the session worked on the wiki.

## Why it matters

PP has a record of context-pressure and `/compact` failures (Owner memory index, "Cuelgues y hooks").
This uses a lever the harness itself reportedly offers, instead of adding another hook.

## Risks

Leaked prompt; the hook may change or not exist. Verify cheaply: add the section, compact a test
session, and check the summary for the listed items.
