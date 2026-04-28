# design-md — Google's DESIGN.md format integrated into Power Pack

This module wraps [`@google/design.md`](https://github.com/google-labs-code/design.md), Google Labs' linter and exporter for the **DESIGN.md** format — a single-file design-system spec that combines machine-readable tokens (YAML front-matter) with human-readable rationale (markdown).

When the Power Pack is installed (`install.sh` / `install.ps1`), `npm install` runs in the repo root and provisions `@google/design.md` into local `node_modules/`. A wrapper is exposed as `~/.claude/bin/design-md` so the CLI is callable from any project.

## Why DESIGN.md is the Power Pack default for web design

- **One file, source of truth.** Tokens, components, and rationale live together — no Figma sync drift, no scattered theme files.
- **Agent-native.** Coding agents read `DESIGN.md` once and have the entire visual identity in context. No "describe the design" handoff.
- **Linted.** Seven structural rules catch broken token references, contrast failures, orphaned tokens, and naming drift.
- **Exportable.** Produces Tailwind theme JSON, W3C DTCG `tokens.json`, and any custom format you need.
- **Diffable.** `design-md diff` surfaces token-level changes between versions, useful in PR review.

## Commands

```bash
design-md lint DESIGN.md                            # validate structure + run 7 rules
design-md diff DESIGN.md DESIGN-v2.md               # detect token-level changes
design-md export --format tailwind DESIGN.md        # tailwind.theme.json
design-md export --format dtcg DESIGN.md            # W3C DTCG tokens.json
design-md spec --format json                        # output the format spec (for agent prompts)
```

All commands accept file paths or stdin (`-`).

## Workflow in a Power-Pack project

1. **Bootstrap.** When starting a new web project, copy the template:
   ```bash
   cp ~/.claude/skills/claude-power-pack/modules/design-md/DESIGN.md.template ./DESIGN.md
   ```
2. **Edit.** Fill in the tokens (colors, typography, spacing, components) and the rationale prose.
3. **Lint on every change.** `design-md lint DESIGN.md` — fail-fast in pre-commit hook recommended.
4. **Export when implementing UI.** Before writing component code, the agent runs `design-md export --format <stack> DESIGN.md` and writes the result into the project's theme config (e.g. `tailwind.config.ts`).
5. **Diff in PR review.** `design-md diff main:DESIGN.md HEAD:DESIGN.md` surfaces visual-identity changes.

## Power-Pack integration points

- **Slash command**: `/cpp-design-md` — see `commands/design-md.md`.
- **Bootstrap**: When `bootstrap-new-project.md` runs in a frontend project, it offers to drop the DESIGN.md template.
- **Pre-output gate**: When the agent is about to emit frontend code (React/Vue/Svelte/HTML), it first checks for `./DESIGN.md` and reads it. If present, all generated tokens MUST resolve via `design-md export`.

## Upstream

- npm: https://www.npmjs.com/package/@google/design.md
- repo: https://github.com/google-labs-code/design.md
- license: Proprietary (Google Labs Code) — see upstream for terms. Power Pack vendors only the package reference in `package.json`; the package itself is fetched from npm at install time.
