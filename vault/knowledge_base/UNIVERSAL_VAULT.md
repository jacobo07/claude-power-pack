# Universal Knowledge Vault — cross-project lesson store

**Status:** Active. Already exists. This doc names the pattern.

The "Universal Knowledge Vault" the user requested is **already operational**
under `~/.claude/knowledge_vault/`. It's a flat-file Obsidian-compatible
store that survives session compaction and is readable by any future
Claude session running on this host. This doc codifies the curation flow.

## Topology

```
~/.claude/knowledge_vault/
├── INDEX.md                         # Human + Claude entry point
├── core/                            # Always-active rules (loaded by router)
│   ├── leyes-core.md
│   ├── mistakes-global.md
│   └── protocols.md
├── errors/                          # #NEVER_AGAIN antipatterns (this session added 1)
│   ├── android-versionname-underscore-parse-error.md
│   ├── gradle-console-handle-error-windows.md
│   └── silent-index-gap-from-missing-source-scanner.md   ← MC-SA-02 added
├── execution/                       # Anti-monolith, intent-lock, vibe-coding
├── stacks/                          # Per-stack runbooks (kobiicraft-ai.md, …)
├── domain/                          # Per-domain knowledge
└── governance/                      # GAL ledger pointers
```

Per-project memory is separate at
`~/.claude/projects/<project-id>/memory/MEMORY.md` + sibling files.
The vault is the **shared** layer.

## Curation flow (the snowball)

1. **Lesson born** — a session hits an antipattern, logs it as a feedback
   memory locally.
2. **Universalize** — if the lesson applies cross-project (not specific to
   one repo), write it to `knowledge_vault/errors/<slug>.md` with YAML
   frontmatter `name`, `description`, `type: reference`, `global: true`.
3. **Seal Hardware Law** — append a row to
   `claude-power-pack/vault/baseline_ledger.jsonl` via
   `tools/baseline_ledger_append.py --law … --evidence … --trigger
   ovo-A-verdict`. The ledger is the audit-grade citation index for the
   antipattern; the vault entry is the long-form explanation.
4. **Citation contract** — future sessions cite by `BL-NNNN` and resolve
   the long form by `Read`-ing the vault entry path.

## Live receipts (this session, 2026-04-30)

Two cross-project entries added today:

- `errors/silent-index-gap-from-missing-source-scanner.md` — ledger BL-0001/BL-0002.
- (in-progress, this commit) — codification of probe-before-repair via BL-0008.

Eight Hardware Laws sealed in the ledger
(`claude-power-pack/vault/baseline_ledger.jsonl`): BL-0001..BL-0008.

## What this is NOT

- **Not a remote service.** The "universal" is per-host, not per-Anthropic-account. Sharing across machines = git push the knowledge_vault repo + git pull on peer.
- **Not auto-curated.** Nothing scrapes session logs and writes vault entries on its own. Curation is a deliberate write triggered when a session decides the lesson is universal.
- **Not infinite memory.** Vault entries should remain concise; long traces stay in `vault/audits/` and are summarized into the ledger row.

## Cross-host sync (manual today, MC-LZ-50 candidate for next session)

```bash
git -C ~/.claude/knowledge_vault add errors/<new>.md INDEX.md
git -C ~/.claude/knowledge_vault commit -m "vault: <slug>"
git -C ~/.claude/knowledge_vault push
```

Then on peer host: `git -C ~/.claude/knowledge_vault pull`. Future MC could
add a `sync_vault.py` that wraps this with ledger-row replication.

— end of doc —
