---
name: cpp-autoupdate
description: Toggle automatic update checking for Claude Power Pack on session start
allowed-tools:
  - Bash
  - Read
---

# Claude Power Pack — Auto-Update Toggle

Enable or disable automatic update checking on session start.

## Process

### 1. Check current state
```bash
ls ~/.claude/skills/claude-power-pack/.autoupdate 2>/dev/null && echo "ENABLED" || echo "DISABLED"
```

### 2. Toggle

**If currently DISABLED → Enable:**
```bash
touch ~/.claude/skills/claude-power-pack/.autoupdate
```
Report: "Auto-update enabled. On each session start, Claude Power Pack will silently check for updates and notify you if a new version is available. No updates will be installed without your confirmation — use `/cpp-update` to install."

**If currently ENABLED → Disable:**
```bash
rm ~/.claude/skills/claude-power-pack/.autoupdate
```
Report: "Auto-update disabled. Run `/cpp-update` manually to check for updates."

## Session Start Behavior (when enabled)

When `.autoupdate` marker exists, on session start:

1. Run silently: `cd ~/.claude/skills/claude-power-pack && git fetch origin 2>/dev/null`
2. Compare: `cat VERSION` vs `git show origin/main:VERSION 2>/dev/null`
3. If different → display ONE line: "Claude Power Pack update available (v{LOCAL} → v{REMOTE}). Run `/cpp-update` to install."
4. If same → say nothing, zero noise.

This check adds ~1 second to session start. No code is changed automatically — only notification.
