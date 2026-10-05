# Pillar K -- resident rent of hook-injected context (deterministic, no model call)

Session c59ad762, 2026-10-05, HEAD 5d82174c. Instrument: `k_rent_scan.py` (this directory), read-only over the 40
newest top-level transcripts >= 200,000 bytes under `~/.claude/projects` (all projects), 297 real user prompts.

    python vault/programs/incremental-cognition/evidence/k_rent_scan.py --n 40
    TOTAL hook_additional_context chars=929987 per_session=23249 per_prompt=3131

## Reading the unit

The chars below are paid once when injected, then carried in context by every later model call of the session
until /clear or compaction. Lifetime rent of one injection ~= chars x calls remaining after it, so a per-prompt
injection compounds (k prompts -> ~k^2/2 carry), a SessionStart one is carried for the whole session. This scan
measures the first factor exactly; the second is an estimate from call counts, not computed here.

## Top rows (chars_per_occurrence x occurrences over 40 sessions)

| Event | Producer marker | chars/occ | occ | sessions | Owner | Note |
|---|---|---|---|---|---|---|
| SessionStart | `<EXTREMELY_IMPORTANT>` superpowers | 3,405 | 53 | 40 | plugin | every session; not CPP code |
| SessionStart | `[OWNER_QUEUE]` (+ the learning-sentinel rule sections that follow it) | 5,639 | 22 | 14 | CPP hub | split is by `[Tag]` line, so this row includes the 2,985 rule stubs + 1,046 pointer |
| UserPromptSubmit | `ExecutionOS Lite tier FORENSIC` (+ family baselines) | 3,003 | 40 | 20 | CPP | per prompt |
| UserPromptSubmit | `Tower baseline -- lessons` | 2,560 | 35 | 23 | CPP | per prompt; self-labelled "unverified, NOT ranked by relevance" |
| PreToolUse | `[Woz]` advisories | 148 | 315 | 36 | CPP | per tool call |
| SessionStart | `Compound Learnings STUCK auto-invoke` | 3,955 | 9 | 8 | CPP | |
| UserPromptSubmit | `POWER PACK ACTIVE reminder` | 2,073 | 16 | 15 | CPP | first prompt |
| PreToolUse | Cross-project baseline / Graph-First / SKILL ADVISOR | 332-702 | 42-85 | 27-39 | CPP | per tool call, advisory |
| SessionStart | `[AutoResearch VPS]` | 488 | 22 | 14 | CPP hub | mostly "no notable signals" |
| SessionStart | `[recovery]` | 607 | 13 | 6 | CPP hub | |

Full table: rerun the command (41 rows).

## Consequences for K

- Recurring hook context is ~23 k chars per session on top of the ~170 k startup floor, and it is **not** in the
  floor gate's startup window except for its first SessionStart / first UserPromptSubmit occurrence. K governs the
  startup window; per-prompt and per-tool injections are an uncovered rent class (named debt, handed to the
  microkernel brief with the rest of steps 11-18).
- The K-local slice acts on what the probe measured (the hub sections). The per-prompt classes are listed here so the
  ordering by rent is evidence, not taste: by occurrence x size the per-prompt FORENSIC/Tower injections outrank every
  hub section except OWNER_QUEUE.
