---
name: cpp-obsidian-setup
description: "Generate a Knowledge Graph vault from the current project for token-efficient architecture discovery"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# Obsidian Setup — Knowledge Graph Generator

Generate an Obsidian-compatible Knowledge Graph vault (`_knowledge_graph/`) from the current project's source code. Claude reads the ~400-token INDEX.md instead of scanning raw code, saving 70-80% of architecture discovery tokens.

---

## Step 1: Validate Project Root

Check that the current directory is a valid project:

1. Run `ls -la ./` to confirm directory contents.
2. Look for at least one of: `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `mix.exs`, `Makefile`, `CMakeLists.txt`, `README.md`.
3. If none found, use AskUserQuestion: **"I can't detect a project root here. Are you sure you want to generate a Knowledge Graph for this directory? (y/n)"**

## Step 2: Check Existing Vault

1. Check if `_knowledge_graph/INDEX.md` already exists.
2. If it exists, use AskUserQuestion: **"A Knowledge Graph vault already exists. Do you want to: (a) Incremental sync (fast, only re-parse changed files), or (b) Full rescan (regenerate from scratch)?"**
   - If (a): set MODE to `--sync`
   - If (b): set MODE to `` (empty — full scan)
3. If no vault exists, set MODE to `` (full scan).

## Step 3: Detect Stack and Run Generator

1. Detect languages present:
   - `*.py` files → python
   - `*.js`, `*.ts`, `*.tsx` files → javascript,typescript
   - `*.java` files → java
   - Other → generic fallback handles them
2. Run the Knowledge Graph generator:

```bash
python "$(dirname "$(find ~/.claude/skills -name kobi_graphify.py -path '*/claude-power-pack/*' 2>/dev/null | head -1)")/kobi_graphify.py" --project . $MODE
```

**Fallback** if the above fails: use Glob to find `kobi_graphify.py` under `~/.claude/skills/`, then run it with `python <path> --project . $MODE`.

3. Parse the JSON output. Report:
   - Number of nodes generated
   - INDEX.md token cost
   - Average node token cost
   - Vault path

## Step 4: Configure .gitignore

1. Check if `.gitignore` exists and contains `_knowledge_graph/`.
2. If not, append `_knowledge_graph/` to `.gitignore` (the vault is a derived artifact, not source).

## Step 5: Report Results

Print a summary:

```
Knowledge Graph generated successfully!
  Vault: ./_knowledge_graph/
  Nodes: {count}
  INDEX.md: ~{tokens} tokens
  Average node: ~{tokens} tokens

How Claude uses this:
  1. On session start, Claude reads _knowledge_graph/INDEX.md (~400 tokens)
  2. Instead of grep/glob scanning, Claude navigates via [[wikilinks]]
  3. Typical session uses index + 5 nodes = ~2,000 tokens (was 5,000-15,000)

To keep it fresh, run: /cpp-obsidian-setup (sync mode auto-detects changes)
To open in Obsidian: File > Open Vault > select _knowledge_graph/ folder
```
