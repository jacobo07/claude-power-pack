---
name: claude-power-pack
description: "Universal AI execution framework — tiered loading, zero-issue delivery, self-healing"
---

# Claude Power Pack v8.0

Universal AI execution framework. Project-agnostic. Tiered loading.

**ALWAYS read** `./parts/core.md` and `./parts/execution.md` — these contain all always-active rules.

## Token Budget

| Tier | When | Load |
|------|------|------|
| LIGHT | Fix, lookup, single file | core.md only (~1000 tok) |
| STANDARD | Feature, 1-5 files | core + execution (~1600 tok) |
| DEEP | Architecture, 5+ files | core + execution + relevant sleepy |
| FORENSIC | Production risk, prior failures | all parts |

**Never load all files. Match task to tier first.**

## Sleepy Parts (load ONLY when triggered)

| Trigger | Part | File |
|---------|------|------|
| React, Next.js, Vue, CSS, frontend | F: Frontend | `parts/sleepy/frontend.md` |
| /autoresearch, competitive research | G: Autoresearch | `parts/sleepy/autoresearch.md` |
| token audit, compress, dedup, optimize | C+H+R: Token Tools | `parts/sleepy/token-tools.md` |
| load ExecutionOS, governance overlay | I: ExecutionOS | `parts/sleepy/executionos.md` |
| daemon, dispatch, omnicapture, infra, VPS | O+P+S+V+X: Infra | `parts/sleepy/infrastructure.md` |
| agent governance, AGT, OWASP ASI | W: Agent Gov | `parts/sleepy/agent-governance.md` |
| zero-crash, TTY, sandbox, process isolation | ZC: Zero-Crash | `parts/sleepy/zero-crash.md` |
| reverse engineer, video analysis, YouTube, competitor, SOTA | VRE: Video-RE | `parts/sleepy/video-re.md` |
| knowledge graph, graphify, obsidian, vault | KG: Knowledge Graph | `parts/sleepy/knowledge-graph.md` |
| governance vault, leyes, mistakes, gates, vault sync | GV: Governance Vault | `parts/sleepy/governance-vault.md` |

## Quick Reference

| Trigger | Action | Source |
|---------|--------|--------|
| (every activation) | PART A0: Scan $PWD, detect manifests, populate context | core.md A0 |
| (every task) | OBSERVE→PLAN→EXECUTE→VERIFY→HARDEN | core.md A |
| (>1 file) | STOP after PLAN, wait approval | core.md B |
| "done"/"complete" | Zero-issue gate: compile+test+E2E | core.md D |
| (on correction) | RCA: HALT→TRACE→HEAL→FIX | execution.md K |
| (new system) | Challenge→Reverse-engineer→Decompose→Tooling | execution.md N |
| (new backend) | Elixir-First if >=2 criteria match | execution.md T |
| (>10 files) | Micro-batch, checkpoint, pause | execution.md U |
| `!kclear` | Dump memory+task, clean restart | execution.md M |
| "token audit" | Load sleepy/token-tools.md | on demand |
| "runtime check" | Load sleepy/infrastructure.md | on demand |
| `/cpp-customclaw create [name]` | Scan project, generate custom daemon | commands/customclaw.md |
| `/cpp-vault-sync` | Regenerate vault INDEX.md and sync metadata | commands/vault-sync.md |
| `/cpp-vault-setup` | Extract CLAUDE.md into governance vault | commands/vault-setup.md |
| `/cpp-design-md` | Lint/diff/export DESIGN.md (Google Labs design-system spec). Power-Pack default for web design. | commands/design-md.md |

## SkillBank Index

Full catalog of slash commands, modules, sleepy parts, and tools — 1-line Process/Rules/Output per entry: [`./SKILLBANK.md`](./SKILLBANK.md).

## Austerity Rule (Token Shield)

Before Explore agents or bulk-reads in this repo, check `./_audit_cache/source_map.json` first:

```bash
python tools/audit_cache.py --project . --check-all        # report changed vs unchanged
python tools/audit_cache.py --project . --summary <path>   # cached 1-line summary (no full file read)
```

If a file's SHA matches the cache, prefer the cached summary. Only raw-read on hash mismatch, missing cache entry, or explicit deep-refactor request. See `./_audit_cache/semantic_tags.json` for module-purpose tags.
