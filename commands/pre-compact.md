---
name: pre-compact
description: "Bundle vault dump + handoff write + Hardware-Law ledger update before the user types /compact. Two-step honest flow — hooks cannot dispatch /compact themselves."
allowed-tools:
  - Read
  - Bash
---

# /pre-compact — Sovereign Vault Dump before context purge

Use this **before** typing `/compact`. It snapshots session intent, appends
relevant Hardware Laws to the baseline ledger, and produces a single
pointer line in `vault/sleepy/INDEX.md` that post-compact resume reads.

> **Reality:** hooks cannot trigger `/compact` for you. The harness compacts
> on its own near token limits, OR you type `/compact`. This command makes
> the moment of compaction zero-loss for the agent's resume.

---

## What this command does (in order)

1. **Pre-compact vault dump:**
   ```bash
   python ~/.claude/skills/claude-power-pack/tools/pre_compact_vault_dump.py \
     --session-id "$CLAUDE_SESSION_ID" \
     --reason manual
   ```
   Writes `vault/sleepy/sleepy_index_<ISO>.json` and appends a pointer line
   to `vault/sleepy/INDEX.md`.

2. **Hardware-Law promotion (interactive):**
   For each new validated decision in the current session, append a row to
   the ledger:
   ```bash
   python ~/.claude/skills/claude-power-pack/tools/baseline_ledger_append.py \
     --law "<one-sentence settled fact>" \
     --evidence "<comma-separated paths>" \
     --trigger pre-compact \
     --scope global
   ```
   Skip step 2 if no new laws qualify. Don't fabricate.

3. **Inform user:**
   Print the snapshot path + ledger row count, then say:
   > "Snapshot at `<path>`. Ledger now at BL-NNNN. Type `/compact` when ready."

---

## When the agent should suggest this command

- **Auto-trigger advisory:** when `gsd-context-monitor.js` injects a CONTEXT
  WARNING (≤35% remaining), the hook now also fires the dump async. The
  agent should reply with a short note: "Vault dump fired. Suggest `/pre-compact`
  to add fresh Hardware Laws, then `/compact`."
- **Manual trigger:** user mid-session feels the conversation getting heavy.

## When NOT to use

- Right after a fresh session start (nothing to vault).
- During an active in-flight tool call sequence — finish the atomic step
  first, then run `/pre-compact`.

---

## Hard rules

- **Never claim `/compact` will fire automatically.** It won't. Hooks can't
  dispatch slash commands.
- **Never invent Hardware Laws.** Only promote what was validated by an
  OVO ≥A verdict, a passing test, or explicit user confirmation.
- **The ledger is append-only.** Don't rewrite history. If a law is wrong,
  add a superseding row referencing the old `ledger_id`.

---

## Verification

After running, this should be true:
- `vault/sleepy/INDEX.md` has one new line dated today
- `vault/sleepy/sleepy_index_<ISO>.json` exists, ≥1 KB, valid JSON
- Optional: `vault/baseline_ledger.jsonl` has ≥1 new row dated today

If any of those fail, do not tell the user "saved" — say what's missing.
