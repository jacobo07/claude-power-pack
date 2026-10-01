---
type: improvement
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-karpathy-llm-wiki]
status: DISCUSSING
effort: M
graduated_to:
---

# Measure whether sessions consult PP's knowledge stores

## Question

Do PP sessions actually read the knowledge PP stores, or rebuild context from scratch each time?
Applies the three-part test from [[compounding-vs-rederived-knowledge]] (written / read / kept current).

## Known stores (existence verified, consultation NOT measured)

Status column = does the path exist at `8574446`; says nothing about whether anything reads it.

| store | path @ `8574446` | exists |
|---|---|---|
| Portfolio learnings | `knowledge/PORTFOLIO_LEARNINGS.md` | yes |
| UKDL rule corpus | `vault/knowledge_base/ukdl-universal.md` | yes |
| Knowledge graph | `_knowledge_graph/` | yes |
| Audit cache builder | `tools/audit_cache.py` | yes |
| Cached-summary hook | `hooks/gatekeeper-semantic.js` | yes |

Other stores live outside this repo (`~/.claude/knowledge_vault/`, per-project `memory/`) and are not
yet listed here. (unsourced — inventory incomplete)

## Measurement — 2026-09-30 (run 1)

Instrument: `wiki/tools/store_consult.py 30 560`. Counts agent tool calls whose path/command mentions
each store: `read` = Read/Grep/Glob, `write` = Write/Edit, `shell` = Bash/PowerShell (ambiguous — may be
either). Window: 30 days, 3015 transcripts (all projects, subagent transcripts included), 246,755
tool calls, full scan (no timeout).

| store | read | write | shell | sessions reading |
|---|---:|---:|---:|---:|
| `ukdl-universal.md` | 713 | 215 | 1263 | 172 |
| `resumption_file.md` (any repo) | 488 | 691 | 541 | 173 |
| other `/memory/` files | 1258 | 1470 | 191 | 438 |
| `MEMORY.md` | 245 | 734 | 265 | 120 |
| `~/.claude/knowledge_vault` | 298 | 161 | 208 | 114 |
| `HARD-RULES-DIGEST.md` | 49 | 0 | 15 | 46 |
| `_knowledge_graph/` | 3 | 0 | 17 | 3 |
| `_audit_cache/source_map.json` | 0 | 0 | 21 | 0 |
| `knowledge/PORTFOLIO_LEARNINGS.md` | 2 | 1 | 2 | 1 |
| control: `wiki/` (written this session) | 0 | 24 | 0 | 0 |

Control fired: this session's own wiki writes were counted, so zero is a result the instrument can
return from a real signal, not a blind spot.

### Aperture — what this cannot see

- **Hook reads.** Hooks run outside the transcript. `_audit_cache/source_map.json` is designed to be
  consumed by `hooks/gatekeeper-semantic.js` (@ `8574446`), so 0 agent reads says nothing about it.
- **Injected context.** `MEMORY.md` and CLAUDE.md-linked content arrive via system-reminders, not tool
  calls. Writes > reads for `MEMORY.md` is expected, not a failure of test 2.
- **Shell column** mixes reads, writes and tool invocations; not attributed.

### Readings

- Clearly consulted: UKDL, knowledge_vault, per-project memory, RESUMPTION_FILE.
- Interpretation: **`knowledge/PORTFOLIO_LEARNINGS.md` is effectively an archive** — 2 reads, 1 write
  in 30 days across 3015 transcripts. The hook-read caveat does not apply: a grep of every
  `*.js/*.py/*.json/*.ps1` under `~/.claude` (2026-09-30) finds the name only in caches and session
  records (lazarus, graphify state, sleepy index, source_map), never in hook or tool code. Fails tests 1 and 2 of
  [[compounding-vs-rederived-knowledge]], despite PP's CLAUDE.md making writing to it a
  "standing obligation".
- `_knowledge_graph/`: 3 direct reads; 17 shell mentions probably tool invocations. Unresolved —
  needs a check of what reads it through tools.
- `_audit_cache/source_map.json`: unresolved — measure the hook's own log instead of transcripts.

## Next steps

1. Decide PORTFOLIO_LEARNINGS' fate — recommendation on [[portfolio-learnings]].
2. Measure `_audit_cache` and `_knowledge_graph` consumption from hook / tool logs.
