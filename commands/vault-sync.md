---
name: cpp-vault-sync
description: "Regenerate the governance vault INDEX.md and sync metadata"
allowed-tools:
  - Bash
  - Read
---

# Vault Sync — Regenerate INDEX.md

Regenerate `~/.claude/vault/INDEX.md` after editing vault files. This keeps the navigation index fresh.

## Step 1: Run Sync

```bash
python ~/.claude/skills/claude-power-pack/tools/vault_sync.py
```

## Step 2: Report

Print the sync output (file count, token cost, changes detected).

## Step 3: Check Mode (optional)

To check for changes without syncing:

```bash
python ~/.claude/skills/claude-power-pack/tools/vault_sync.py --check
```
