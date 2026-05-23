# Universal Knowledge / Documentation / Lessons — cross-reference ledger

This file is the "ukdl-universal" reference index — each row points
at a sealed lesson, learning, or session note that is broadly
applicable across PP-shipped projects and not specific to one repo.

Entries are append-only; never remove a row. If a lesson is
superseded, append the superseding row referring back to the older.

## Auto-Testing Skill (Quality Gate) — 2026-05-23

| Ref | File | Why it matters |
|---|---|---|
| UKDL-AT-01 | `vault/specs/auto-testing-gate.md` | Authoritative contract for the Quality Gate skill: architecture, verdict shapes, 30 s budget, ceiling-honest posture, Mirror-Sync-Direction. |
| UKDL-AT-02 | `vault/plans/auto-testing-skill-2026-05-23.md` | 23-Paso ULTRA plan + status log with empirical numbers for each gate. |
| UKDL-AT-03 | `vault/knowledge_base/session_lessons.md` (rows L1-L6 dated 2026-05-23) | Iteration findings from real empirical runs: Python-by-convention rule (twice tightened), pytest filename validity, PowerShell here-string tokenization, regex var-in-PowerShell coverage. |
| UKDL-AT-04 | `knowledge_vault/core/apex-completion-standard.md` — "Testing Gate Axis (sealed 2026-05-23)" section | 5 required components + 5-check DONE-gate for the axis. PP source + `~/.claude/knowledge_vault/core/...` live mirror byte-identical (sha256 63bdfca46f83e8cd). |
| UKDL-AT-05 | `vault/lessons/windows-argv-limit-stdin-fix.md` (sister to deep-research) | claude.exe -p user message via STDIN. The Auto-Testing LLM bridge inherits this vaccine. |
| UKDL-AT-06 | `vault/lessons/stop-hook-subprocess-recursion.md` (sister to deep-research) | CLAUDEPP_AUTOTEST_RUNNING=1 sentinel pattern. The hook checks this as its first statement; same family as CLAUDEPP_DEEPRESEARCH_RUNNING. |

## Cross-axis pattern: sleepy auto-spawn + ceiling-honest gates

Three PP axes now share the same architectural shape (sealed
2026-05-23):

- **Research Axis** (`cpp-deep-research`): Stop hook intent regex +
  detached `cmd.exe /c start "" /B python ...` spawn + recursion
  guard env var. CEILING when web search + no API keys produce
  zero URLs.
- **Testing Gate Axis** (`auto-test-gate`): PreToolUse hook command
  regex (PRIMARY + LOOSE) + subprocess spawn of
  `python auto_test.py --gate` + recursion guard env var. CEILING
  when no build manifest OR framework binary missing.
- **Session-Safety Axis** (`session-file-guard`): PreToolUse hook
  protects .jsonl files from harmful tool calls; SessionStart hook
  recovers stub sessions.

Common pattern (sealed as PP doctrine): every "smart" hook is
fail-OPEN, has a recursion-guard env-var, has a Mirror-Sync-Direction
consolidator in `settings_merger.py`, and ships with a 5-check
DONE-gate in `apex-completion-standard.md`.

## Cross-references to forbidden runtimes

- `memory/feedback_no_n8n_ever.md` — n8n is forbidden as a runtime.
  Reference workflows extracted only for prompt + algorithm
  reverse-engineering. Same ban extends to Zapier/Make.com/Pipedream
  by implication.


## Production Branch Standard — 2026-05-23

| Ref | File | Why it matters |
|---|---|---|
| UKDL-PB-01 | `knowledge_vault/core/apex-completion-standard.md` "Production Branch Standard" section | Three hard preconditions for `feat/* -> main`: verify_spp 7/7, manual conflict resolution, post-merge verify_full_install 0. |
| UKDL-PB-02 | `.gitattributes` (repo root) | 5 ledgers configured for `merge=union` (session_lessons.md, governance_vaccines.md, verdicts.jsonl, vendor/NOTICE.md, SSOT.md). Cherry-pick onto main BEFORE the merge so the union driver activates. |
| UKDL-PB-03 | `vault/knowledge_base/session_lessons.md` "Branch hygiene: 177-commit feat branch" row | 4 lessons: merge frequency <=2 weeks; union driver from day 1; cherry-pick .gitattributes onto main first; Reality Contract = commits + tests pass, not just merge commit. |
| UKDL-PB-04 | `vault/lessons/bash-heredoc-bom-clobber.md` | Companion pattern: Python read_bytes + write_bytes is the safe append for BOM-prefixed markdown files. Used to recover the L1-L6 rows when the union merge couldn't reconcile divergent file structures. |
