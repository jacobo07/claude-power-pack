# Phase 1 EVIDENCE: Context-rent attribution

Date: 2026-10-15. Zero model calls spent reproducing known numbers: everything below is read from existing transcripts.

## Commands and results
- `python -I tools/test_ccr_rent_ledger.py` -> `RENT_PASS=11/11`, exit 0 (OBSERVED: ran here).
- `python tools/ccr_rent_ledger.py json --dir <~/.claude/projects/...KobiiCraft-Core-Files> --out vault/programs/ccr/stage4/p1/ledger.json`
  -> 268 sessions with a model call, 158 with call-1 ctx >= 150,000 (p50 196,313; min 151,998; max 258,653).
- Calibration (pooled OLS, all 268): k = 0.2585 tokens/byte, c0 = 66,432, R2 = 0.716. The split below is a FIT, not a count.

## Ledger, session nearest the measured 206,186 floor (ctx 206,190) and p50 (196,313)
| category | tokens (nearest) | share | p50 tokens | class (ccr_anatomy) | driver axis |
|---|---:|---:|---:|---|---|
| rules (23 files in ~/.claude/rules) | 67,033 | 32.5 % | 66,809 | REDUCIBLE | PROJECT |
| constitution (user + project CLAUDE.md) | 19,790 | 9.6 % | 19,790 | REDUCIBLE | PROJECT |
| memory (AutoMem MEMORY.md) | 4,926 | 2.4 % | 4,547 | ELIMINABLE | PROJECT |
| agent listing | 12,832 | 6.2 % | 12,832 | ELIMINABLE | PROJECT |
| skills listing | 4,029 | 2.0 % | 3,797 | ELIMINABLE | PROJECT |
| deferred tools + MCP instructions | 2,298 | 1.1 % | 2,238 | PAGEABLE / ELIMINABLE | PROJECT |
| hook injections | 3,259 | 1.6 % | 1,534 | REDUCIBLE | EPOCH |
| first user message (epoch packet) | 11,486 | 5.6 % | 14,627 | IRREDUCIBLE | EPOCH |
| system prompt snapshot | 2,724 | 1.3 % | 2,724 | REDUCIBLE | HOST |
| environment/model/session | 428 | 0.2 % | 430 | IRREDUCIBLE | HOST |
| other attachments | 129 | 0.1 % | 130 | UNKNOWN | EPOCH |
| **tool schemas + framing (residual, unsplit)** | **77,256** | **37.5 %** | 66,855 | REDUCIBLE by analogy only | HOST |

## Project age vs epoch age (early third vs late third of sessions by first timestamp; bytes)
- Project-age drivers that drifted: rules +49,276 B (about +12.7K tokens), agent listing +11,383 B (+2.9K); constitution +2,196 B; memory -1,481 B; skills +134 B.
  Total project-age drift between thirds is about 16K tokens of a ~200K floor (OBSERVED, replay of the corpus as it exists).
- Epoch-age driver: the first user message. Late-third p10..p90 = 145 .. 100,410 B (about 0 .. 26K tokens): a Ralph handoff packet is the epoch's own rent.
- The static bulk (rules + constitution + residual) is present in every session regardless of epoch work.

## Gate G1 (host-fixed share of the Lobby floor against 70 %)
- IRREDUCIBLE + HOST_LIMITED categories: 5.8 % of the floor (nearest) / 7.7 % (p50); with UNKNOWN-class rows 5.8 % / 7.7 %.
- Worst case, counting the whole unsplit tool-schema residual as host-fixed: 43.3 % / 41.8 %.
- **G1 is NOT triggered under either bound (both below 70 %).** Phase 6 is not shrunk to receipts-only; the saving does not move to Phase 8 on this evidence.

## What this means for later phases (OBSERVED, not promised)
- About 60 % of the floor (rules 32 %, constitution 10 %, agent listing 6 %, skills 2 %, memory 2 %, hooks, MCP) is project configuration the host
  re-sends each epoch and that ccr_anatomy already grades REDUCIBLE/ELIMINABLE on PP work units. Carrying that grading to Lobby is a hypothesis
  to test in Phase 10, not a result here.
- The largest single unknown is the 77K residual. A2 removed only 4,114 tokens of tool schemas in a small probe; whether 77K is controllable at Lobby scale is UNJUDGED.

## Production Reality verdict
| claim | grade |
|---|---|
| Ledger module + V-RENT gates work (11/11, poles driven) | PROVEN (ran here, exit 0) |
| Per-category byte attribution of the first call on 158 real sessions | OBSERVED (bytes measured from transcripts; transcripts omit tool schemas) |
| Token split per category | OBSERVED (pooled fit, R2 0.716; per-category error not bounded per session) |
| G1 not triggered | OBSERVED (holds under the worst-case bound, so insensitive to the fit) |
| Reducibility of rules/constitution/agent listing at Lobby scale | UNJUDGED (analogy from V1 on PP; needs a Lobby parity run) |
| Tool-schema residual composition (77K) | UNJUDGED (no receipt carries tool-schema bytes; needs a probe) |
| Live Lobby epoch measured after a CCR launch | BLOCKED to Phase 10 (needs authority check) |

Known limits: the corpus is this laptop's Core Files directory (interactive plus Ralph). The `nearest` row is one session; the p50 row takes
per-category medians, so its rows do not sum to a single real session. A session whose transcript lacks attachment records would under-count bytes.