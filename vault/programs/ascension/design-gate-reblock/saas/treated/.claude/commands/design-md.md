---
name: cpp-design-md
description: "Lint, diff, export, or scaffold a DESIGN.md (Google Labs design-system spec). Power-Pack default for web design across all projects."
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# DESIGN.md — Google Labs design-system spec, integrated

DESIGN.md is the Power-Pack default for web/UI design across every project. One file holds the entire visual identity: tokens (YAML front-matter) + rationale (markdown prose). The agent reads it before generating any frontend code; the `design-md` CLI lints, diffs, and exports it to Tailwind / DTCG / etc.

The CLI is bundled with the Power Pack — installed via `npm install` at `install.sh` / `install.ps1` time and exposed as `~/.claude/bin/design-md`.

---

## Step 1: Parse the user's intent

Inspect the user's invocation. Match one of:

| Intent | Trigger phrases | Action |
|---|---|---|
| **Init** | "init", "scaffold", "new", "boilerplate", "start", no DESIGN.md exists in CWD | Step 2 |
| **Lint** | "lint", "validate", "check" | Step 3 |
| **Diff** | "diff", "compare", "what changed" | Step 4 |
| **Export** | "export", "tailwind", "tokens", "dtcg" | Step 5 |
| **Spec** | "spec", "format", "what does design.md look like" | Step 6 |
| **Audit** | "audit", "review", no specific verb but DESIGN.md exists | Step 3 + Step 5 (lint then export) |

If unclear, use AskUserQuestion: **"What do you want to do with DESIGN.md? (a) Init a new one, (b) Lint the existing one, (c) Diff two versions, (d) Export to Tailwind/DTCG, (e) Print the format spec"**

## Step 2: Init — scaffold a DESIGN.md

1. Check if `./DESIGN.md` already exists in the current project root.
2. If it exists: AskUserQuestion: **"DESIGN.md already exists. Overwrite, append a section, or abort?"**
3. If it does not exist (or user said overwrite):
   ```bash
   cp ~/.claude/skills/claude-power-pack/modules/design-md/DESIGN.md.template ./DESIGN.md
   ```
4. Open the file and prompt the user to fill in:
   - Project name (replaces `name: ProjectName`)
   - Brand color (replaces `colors.primary`)
   - Typography family (h1 + body)
5. Run `design-md lint ./DESIGN.md` to confirm it parses.

## Step 3: Lint

```bash
design-md lint ./DESIGN.md
```

Report:
- Pass / fail + which of the 7 rules failed
- Broken token references (e.g. `{colors.primry}` typo)
- Contrast failures (WCAG AA)
- Orphaned tokens (defined but never referenced)
- Suggestions for each violation

If lint fails, **do not proceed to export**. Fix the file first.

## Step 4: Diff

If the user gives two paths or git refs:
```bash
design-md diff ./DESIGN.md ./DESIGN-v2.md
# or git refs (the agent must materialize them first)
git show main:DESIGN.md > /tmp/old.md
git show HEAD:DESIGN.md > /tmp/new.md
design-md diff /tmp/old.md /tmp/new.md
```

Report token-level changes grouped by category (colors, typography, spacing, components). Flag breaking changes.

## Step 5: Export

Detect the target format from project context:
- `tailwind.config.{js,ts,cjs,mjs}` exists → `--format tailwind`
- `tokens.json` or DTCG-flavored config → `--format dtcg`
- Otherwise ask.

```bash
design-md export --format tailwind ./DESIGN.md > tailwind.theme.json
```

Then wire the export into the project's theme config (e.g. import the JSON into `tailwind.config.ts` under `theme.extend`). Confirm the change with the user before editing real config files.

## Step 6: Spec

```bash
design-md spec --format json
```

Use the output to seed agent context when generating components from scratch.

## Step 7: Verify

After any mutation:
1. Re-run `design-md lint ./DESIGN.md` — must pass.
2. If a frontend dev server is running, hot-reload the theme and visually confirm.
3. Commit DESIGN.md with a message referencing what changed (e.g. `design: bump primary to #0F172A, update button-primary contrast`).

---

## Why this is the Power-Pack default

- **One source of truth.** Tokens + rationale together. No Figma sync drift, no scattered theme files.
- **Agent-native.** The agent reads DESIGN.md once and has the entire visual identity in context.
- **Linted + exportable.** Catches broken refs and contrast failures; ships tokens to any stack.
- **Diffable in PR review.** `design-md diff` surfaces visual-identity changes at token granularity.

Upstream: https://github.com/google-labs-code/design.md · npm `@google/design.md`. Bundled in Power Pack via root `package.json` and installed by `install.sh` / `install.ps1`.
