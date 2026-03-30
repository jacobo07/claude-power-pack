---
name: cpp-update
description: Update Claude Power Pack to the latest version from GitHub
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Claude Power Pack — Update

Update the locally installed Claude Power Pack to the latest version.

## Process

Execute these steps in order:

### 1. Detect installed version
```bash
cat ~/.claude/skills/claude-power-pack/VERSION 2>/dev/null || echo "unknown"
```
Store as `LOCAL_VERSION`.

### 2. Fetch latest from remote
```bash
cd ~/.claude/skills/claude-power-pack && git fetch origin 2>&1
```

### 3. Check remote version
```bash
cd ~/.claude/skills/claude-power-pack && git show origin/main:VERSION 2>/dev/null || echo "unknown"
```
Store as `REMOTE_VERSION`.

### 4. Compare versions
- If `LOCAL_VERSION` == `REMOTE_VERSION` → Report "Claude Power Pack is up to date (v{VERSION})." and stop.
- If different → continue to step 5.

### 5. Show changelog
```bash
cd ~/.claude/skills/claude-power-pack && git log --oneline HEAD..origin/main
```
Display the changelog to the user with a summary of what changed.

### 6. Confirm with user
Use AskUserQuestion: "Update Claude Power Pack from v{LOCAL} to v{REMOTE}? The changes above will be applied."

If user declines → stop.

### 7. Preserve local modifications
```bash
cd ~/.claude/skills/claude-power-pack && git stash 2>&1
```
Note whether stash was created (has local changes) or not (no local changes).

### 8. Pull latest
```bash
cd ~/.claude/skills/claude-power-pack && git pull origin main 2>&1
```

### 9. Reapply local modifications
Only if step 7 created a stash:
```bash
cd ~/.claude/skills/claude-power-pack && git stash pop 2>&1
```
If conflicts occur, warn the user: "Local modifications conflict with the update. Files with conflicts: {list}. Resolve manually or run `git stash drop` to discard local changes."

### 10. Confirm success
```bash
cat ~/.claude/skills/claude-power-pack/VERSION
```
Report: "Claude Power Pack updated to v{NEW_VERSION}. Restart your Claude Code session to load the new version."
