---
title: CLAUDE.md auto-compaction — lightweight index, vault as source
covers: [claude-md, compaction, index, pointer, vault, linter, threshold]
tier: 2
date: 2026-07-26
status: STOP #1 delivered inline; awaiting Owner approval before execution
mode: PLAN MODE — blast radius localized to ~/.claude/CLAUDE.md + knowledge_vault/
---

# CLAUDE.md auto-compaction

## Reality scan (measured, not estimated)

`~/.claude/CLAUDE.md` = **40,275 chars, 33 sections**, 275 over the 40,000
performance warning.

Four facts that shape the plan:

1. **Two sections are 44.2% of the file** — `Parallel Subagent Limit on Windows`
   (9,628) and `Windows Bash Bridge Reliability` (8,160) = 17,788 chars. Both are
   protected by a sealed lesson (`reference_claude_md_40k_char_warning.md`:
   *never relocate Bash-Bridge/Anti-Waiting rules*). **They are excluded from this
   plan entirely.**
2. **`trim_claude_md.py` is exhausted** — `--dry-run` reclaims 0. It removes
   provenance prose only, and that was already harvested on 2026-07-04.
3. **The size linter is already live** — `hooks/claude_md_linter_stop.js`, wired
   in the Stop chain at `hook-dispatcher.js:121`, WARN 39,750 / ALERT 40,000.
   Its remedy is **dead advice**: it tells the agent to run the exhausted trimmer.
4. **The pointer pattern already exists** — 14 sections delegate via
   ``See `~/.claude/knowledge_vault/...` ``, and `claude-doctrine/` already holds
   three `*-detail.md` files. This plan extends an established convention; it
   invents nothing.

## Central architectural decision — the TRIGGER/EXPLANATION split

**A section may move only if its TRIGGER stays in CLAUDE.md and only its
EXPLANATION moves.**

- **TRIGGER** (stays): the recognition condition + the imperative + the pointer.
  What makes the agent notice the situation and act correctly.
- **EXPLANATION** (moves): rationale, incident origin, worked examples, recovery
  narratives, detail tables — everything that only matters once you are already
  in the situation AND the trigger named the file.

Why this criterion and not "move the big things": CLAUDE.md is the only text
guaranteed in context. A pointer is followed only if the agent chooses to read
it. So anything that must fire *without* the agent deciding to read anything is
unconditional and stays. Move a trigger and the rule silently stops existing —
which is `T-SDD-OS-IMPLICIT-ACTIVATION-001` all over again, in a new file.

### Hard exclusion list (never moved, any future pass)

Windows Bash Bridge · Parallel Subagent / Anti-Waiting (A)-(I) · Hard-Rules
router 4 triggers · Environment Awareness · Critical Rules · Reality Contract
core · Token Efficiency · PP Activation Criteria table.

## CLAUDE_MD_MAP — move candidates

| Section | now | keep | save | destination |
|---|---|---|---|---|
| Sovereign Baseline | 1,798 | ~420 | 1,378 | `sovereign-baseline-detail.md` |
| Anti-Overlap / Pathspec commits | 1,912 | ~620 | 1,292 | `commit-doctrine-detail.md` (exists) |
| Sovereign Standard | 1,560 | ~430 | 1,130 | `sovereign-standard-detail.md` |
| HARD RULES router (provenance + UI/design) | 2,829 | ~1,830 | 1,000 | `hard-rules-router-detail.md` |
| Anti-Antipattern / Regla 12 | 1,161 | ~380 | 781 | `anti-antipatterns.md` (exists) |
| RESUMPTION_FILE pattern | 1,132 | ~360 | 772 | `session-continuity-detail.md` |
| Context Pressure Response | 897 | ~330 | 567 | `context-pressure-detail.md` |
| Background Process Hygiene | 1,132 | ~620 | 512 | `windows-execution-detail.md` (exists) |
| ULTRA / ONESHOT Protocol | 788 | ~360 | 428 | `commands/ultra.md` (exists) |
| Reality Contract (Analytical-Log Exemption) | 787 | ~380 | 407 | `reality-contract-detail.md` |
| Knowledge Vault Protocol | 869 | ~500 | 369 | `INDEX.md` (exists) |
| Agent Teams HANDOFF | 630 | ~300 | 330 | `session-continuity-detail.md` |

**Estimated recovery ~8,970 chars → ~31,300**, i.e. under the 38,000 target with
~6,700 headroom, **without touching either protected Windows section.**

## Scopes

- **C0 (do first)** — fix the SDD-OS auto-generation defect. The hook writes a
  spec skeleton on every long prompt in a scaffolded repo; `_active_spec()` picks
  the newest spec, so the skeleton became the injected "ACTIVE PROJECT SPEC".
  Hook becomes read-only; generation moves to explicit `/cpp-sdd-os spec`.
  Delete `vault/specs/t3-preflight-git-fetch-origin-git-log-oneline-5-cat.md`.
- **C1** — move the 12 sections, one micro-commit each, measuring after every one.
- **C2** — upgrade the live Stop linter: thresholds from config (not hardcoded),
  and emit the top-N movable sections by measured size instead of pointing at the
  exhausted trimmer.
- **C3** — `PR-CLAUDE-MD-INDEX-FIRST-001` as governance + real enforcement in the
  same linter: a section over N chars with no vault pointer is named.

## Done-gate

CLAUDE.md < 38,000 (target ~31-33k) · every moved section reachable via its
pointer · linter emits specific recommendations · policy documented AND enforced
· 2 UKDL rules sealed · REMOTE_DELTA 0 0.
