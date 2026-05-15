# Governance Vaccines — Append-Only

Cross-project preventive rules synthesized from governance misses (skill-skip,
gate-bypass, ceiling violations). Distinct from `distiller_vaccines.md`
(distiller kernel gate failures). Append-only.

---

## VAC-GOV-220000 — Quality-skill skip on multi-file delivery

**Synthesized:** 2026-05-15 · ULTRA-PLAN v220000 (THE QUALITY CORONATION)
**Severity:** Critical (process) · **Status:** ACTIVE, hard-gated

### Trigger pattern

A changeset of **≥ 3 source files** is authored and declared "done" /
committed **without** `code-reviewer`, `software-best-practices`,
`python-pro`, or `kobiicraft-review` ever being invoked in the session.

Empirical origin: 26 KobiiDistillerOS Python files (~2665 LOC) shipped
across multiple sessions with **zero** quality-review skill invocations
(70-transcript `grep` of the `Skill` tool). The CLAUDE.md "code-reviewer
for 3+ files" gate and the mandatory `feedback_auto_activate_skills.md`
were both bypassed silently. This is the structural cause of the repo's
44% preventive-health baseline: high edit volume, low review gating.

### Why it happened (root cause)

Skills of **action** (`kobiicraft-dev`, `kobiicraft-execution`,
`kobiicraft-ops`) were invoked; skills of **quality control**
(`code-reviewer`, `software-best-practices`, TDD, verification) were
systematically skipped. Nothing *mechanically* prevented the skip — the
gate was advisory prose, not an enforced rail. Advisory governance under a
`bypassPermissions` ceiling degrades to "honor system", and the honor
system lost over 76 sessions.

### Prevention (how to apply)

1. **Mechanical hard gate** (Owner-ratified, ceiling v5.5):
   `~/.claude/hooks/quality-skill-gate.js` — PreToolUse on Bash. DENIES
   `git commit` when ≥3 staged source files lack a fresh quality-skill
   evidence receipt at `<repo>/.git/quality-skill-evidence.json`. Receipt
   is produced AFTER the quality skills by:
   `node ~/.claude/hooks/quality-skill-gate.js --record <files...>`.
   The skip is now *impossible to commit through*, not merely discouraged.
2. **Volume-triggered auto-activation**: when a task will touch >1 file,
   the quality skills are activated BEFORE writing code, not after — see
   reinforced `feedback_auto_activate_skills.md`.
3. **Agent-team retro-audit pattern**: 3 parallel auditor sub-agents
   (code-reviewer / python-pro / kobiicraft-review) writing findings to
   disk is the canonical way to retroactively clear an un-reviewed
   changeset without blowing orchestrator context.

### Boundaries (non-generalizing)

This hard gate required explicit Owner ratification via `AskUserQuestion`
(it breaks the sealed velocity ceiling v5.4 for ONE narrow scope). It does
NOT authorize any other agent self-elevation. Reversible by deleting the
`quality-skill-gate.js` stanza from `~/.claude/settings.json` (backup:
`settings.json.bak-v220000`).

### Evidence chain

- `CLAUDE.md` → "Governance ceiling v5.5 — Owner-ratified amendment"
- `reports/verdicts/2026-05-15_ceiling_v5.5_ratification.md`
- `docs/audit/KOBIIDISTILLER_RETRO_AUDIT_v220000.md` (+ 3 `_retro_*.md`)
- Remediation commits: `c523c8e` (A), `d1a3134` (B), `3f5e4b8` (C1+C4),
  `ad0d664` (C3), `35fa549` (C5), `9c3a479` (C6)
- `vault/audits/verdicts.jsonl` (v220000 grade row — Phase F)

### Trigger regex (for automated detection)

`commit .* (?:[^ ]+\.(py|js|ts|java|go|rs)){3,}` with no
`quality-skill-evidence.json` mtime within session window.

---

## VAC-ARCH-230000.1 — Parallel-session false-collision on shared host

**Synthesized:** 2026-05-15 · ULTRA-PLAN v230000.1 (SOVEREIGN RECONCILIATION)
**Severity:** High (process / honesty) · **Status:** ACTIVE (advisory + double-check protocol) · **2-part vaccine (detection + double-check)**

### Trigger pattern

Two Claude Code sessions for the same Owner running on the same dev host
touch the same cross-repo subsystem (e.g., KobiiDistillerOS — workspace
engine + PP kernel). Each session commits architectural work without seeing
the other's commits because neither ran `git fetch origin && git status`
at session start. Later one session reads a fragment of the other's SSOT
manifest (e.g., only the invariant title "Engine NEVER moves") and
declares a **false** Vault-First Conflict (DNA-700 mandato 8), STOPs, and
asks the Owner to choose between two architectures that were **never
actually different** — just named differently.

Empirical origin: 2026-05-15 in this repo. Parallel session named the same
architecture "DNA-11000 Rule-097 roles-not-duplicates" while my session
named it "Opt D Hybrid Kernel-Only". The "Engine NEVER moves" line in
their manifest meant *engine stays in workspace*, not *no kernel package
at PP* — they had explicitly named `kpp-distiller-kernel` in the same
manifest, three lines below. I declared STOP without reading the next
three lines. Antithesis of Anti-Antipattern rule 8 (Double-check).

### Why it happened (root cause)

1. No session-start probe of `git status` + `git log --oneline` on both
   repos surfaced the parallel work. Without that, the agent's context
   begins with a stale snapshot of HEAD.
2. The agent stopped reading SSOT manifests at the first apparent
   contradiction (a heading + invariant title) instead of reading the
   FULL content of the manifest. Manifests use prose to qualify their
   invariants; skipping the prose flips the conclusion.
3. Compaction summary tone amplified the false alarm. Once "conflict"
   was the framing, the agent built an entire 3-option fork without
   verifying the contradiction.

### Prevention (how to apply) — 2-part protocol

**Part A — Detection (session start, MANDATORY for any cross-repo work):**

```bash
# In every repo the task will touch, before reading task-specific files:
git fetch origin && git status --short && git log --oneline -10
```

If any of the recent commits are by a non-current owner email or carry an
unfamiliar phase tag, **assume a parallel session is active** and read its
SSOT manifests in full before any architectural assertion. Append the
findings to `vault/audits/parallel_session_probe.jsonl` (one row per repo).

**Part B — Double-check (before declaring any Vault-First Conflict):**

Before emitting a DNA-700 mandato 8 conflict report, re-read the **FULL**
content of every SSOT manifest cited as evidence — not just headings, not
just invariant titles. Quote at least 2 lines from EACH side, separated by
at least 5 lines of intervening content, to demonstrate the contradiction
is structural and not a misreading of a single sentence taken out of
context.

Trigger phrases that demand the double-check before STOP: "Vault-First
Conflict", "architectural collision", "parallel session contradiction",
"shared-host-parallel-session-collision".

### Boundaries (non-generalizing)

This vaccine is advisory + protocol, not a hard gate. It does NOT
authorize agent self-elevation or change permission rails. A future hard
gate could be: PreToolUse on AskUserQuestion that contains the strings
"conflict" + "parallel session" + "ratify ONE architecture" → require
proof-of-double-read receipt at `<repo>/.git/parallel-session-doublecheck.json`.

### Evidence chain

- `reports/verdicts/2026-05-15_v230000.1_seal.md` (workspace) — full seal
- `vault/audits/verdicts.jsonl` row `session=v230000.1` (line 57)
- Workspace `docs/SSOT_KOBII_DISTILLER.md` → `## v230000.1 — Owner Ratification`
- PP `SSOT.md` → `## 1.1 — v230000.1 Owner Ratification`
- Workspace memory mirror:
  `~/.claude/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/memory/feedback_parallel_session_collision_false_alarm.md`

### Trigger regex (for automated detection)

Prompt or AskUserQuestion text containing: `Vault[-\s]?First Conflict|parallel session.*contradict|architectural collision|ratify ONE architecture`
without a preceding `git fetch.+git log` in the session's Bash history.
