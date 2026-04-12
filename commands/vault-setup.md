---
name: cpp-vault-setup
description: "Extract a monolithic CLAUDE.md into an Obsidian-compatible governance vault for token-efficient on-demand rule loading"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# Vault Setup — Governance Vault Generator

Extract a monolithic CLAUDE.md into an Obsidian-compatible governance vault (`~/.claude/vault/`). Claude reads the ~300-token INDEX.md on session start and navigates via [[wikilinks]] to load only what's relevant, saving 80%+ of governance token overhead.

---

## Step 1: Identify Source

1. Check if `~/.claude/CLAUDE.md` exists (global config — primary target).
2. Also check `./CLAUDE.md` in current project (project-level config).
3. Use AskUserQuestion if both exist: **"Which CLAUDE.md should I extract into the vault? (a) Global (~/.claude/CLAUDE.md), (b) Project (./CLAUDE.md), (c) Both"**

## Step 2: Check Existing Vault

1. Check if `~/.claude/vault/INDEX.md` already exists.
2. If it exists, use AskUserQuestion: **"A governance vault already exists with {file_count} files. Do you want to: (a) Merge new content (keep existing, add missing), or (b) Full re-extract (regenerate from scratch)?"**

## Step 3: Run Extraction

```bash
python ~/.claude/skills/claude-power-pack/tools/vault_extractor.py extract <source_path> --vault ~/.claude/vault/
```

Parse the output. Report:
- Number of sections extracted
- Number of vault files created
- INDEX.md token cost
- Verification result (0% loss check)

## Step 4: Update CLAUDE.md Router

If the source CLAUDE.md was >50 lines, suggest transforming it into a Router:
- Use AskUserQuestion: **"Your CLAUDE.md is {lines} lines. Should I transform it into a lightweight Router (<50 lines) that points to the vault? The original will be backed up to CLAUDE.md.bak. (y/n)"**
- If yes: backup original, write Router version.

## Step 5: Report Results

```
Governance Vault generated successfully!
  Vault: ~/.claude/vault/
  Files: {count}
  INDEX.md: ~{tokens} tokens

How Claude uses this:
  1. On session start, Claude reads ~/.claude/vault/INDEX.md (~300 tokens)
  2. CLAUDE.md routing table tells Claude which pages to load per-task
  3. Typical session loads index + 2 pages = ~1,000 tokens (was 4,000+)

To keep it fresh: /cpp-vault-sync
To add rules: create .md in vault subdirectory, then /cpp-vault-sync
To open in Obsidian: File > Open Vault > select ~/.claude/vault/ folder
```
