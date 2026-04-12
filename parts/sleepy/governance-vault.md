# Governance Vault Navigation (Part GV)

When `~/.claude/vault/INDEX.md` exists, use the vault for governance rules, leyes, mistakes, and protocols instead of loading them from CLAUDE.md.

## Navigation Protocol

1. **Read INDEX.md first** — it contains the full vault map with wikilinks (~300 tokens).
2. **Follow [[wikilinks]]** to drill into specific pages. Each page is ~200-500 tokens.
3. **Max 5 pages per task** — load only what is relevant. Never load the entire vault.
4. **Domain routing** from CLAUDE.md tells you which pages to load for which triggers.

## When to Load What

| You're about to... | Read this vault page |
|---|---|
| Write code | `vault/mistakes/mistakes-01-27.md` |
| Claim "done" | `vault/gates/completion-gates.md` |
| Touch gameplay/animation | `vault/protocols/supremacy-mode.md` |
| Change >1 file | `vault/leyes/ley-26-zero-shot-veto.md` |
| Create content/shorts | `vault/leyes/ley-36*` + `ley-37*` + `ley-38*` |
| Ship a new feature | `vault/leyes/ley-27-auto-heal.md` |
| Work on SaaS | `vault/stacks/saas-doctrine.md` |

## Sync Command

Run `/cpp-vault-sync` to regenerate INDEX.md after editing vault files.

## When to Fall Back

- Vault doesn't exist → fall back to CLAUDE.md inline rules
- Task is LIGHT tier → INDEX.md + at most 1 page
- Task is FORENSIC tier → INDEX.md + all relevant pages (still max 5)
