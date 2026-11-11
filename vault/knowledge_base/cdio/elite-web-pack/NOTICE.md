# NOTICE — CDIO Elite Web Experience Agent Pack v1.0.0 (absorbed 2026-11-12)

**Origin.** `CDIO_Elite_Web_Experience_Agent_Pack_v1.0.0.zip` supplied by the Owner (Downloads), release date
2026-11-11, language es. Zip SHA-256 `F8C6381D0F6A8479DB4585212C5F27207901C715B6092E5A1875C2E1622AE54E`.
Every archived file here matches the pack's own `SHA256SUMS.txt` (0 mismatches, checked at copy time).

**Owner instruction (2026-11-12):** "mete esto dentro de CDIO ... añadele memoria persistente a cada agente y haz DRX
sobre cada tema". Choices made by the Owner: 9 new linked agents; all 9 DRX runs now, sequential; memory on all 12.

## Where each part went (REUSE / EXTEND / BUILD)

| Pack part | Disposition | Location |
|---|---|---|
| 9 specialists A–I (`04_claude_code_ready`) | BUILD, one per role, from the assembled version only (the pack forbids installing both forms) | `~/.claude/agents/cdio-<slug>.md` |
| Their source `SYSTEM.md` + `ROLE.md` (`01_agents`) | archived as source of truth for future edits | `01_agents/` here |
| `CDIO_SYSTEM_OVERLAY.md`, `CDIO_ROLE_PROMPT.md` | NOT applied over cdio-core (pack says never overwrite the canonical CDIO); routing EXTENDED into cdio-core as a "Specialist bench" table | `~/.claude/agents/cdio-core.md` |
| Protocols, templates, MYTILUS case, integration docs | archived reference | `02_PROTOCOLS/`, `03_TEMPLATES/`, `05_EXAMPLE_MYTILUS/`, `06_INTEGRATION/` |
| `DESIGN.template.md` | schema reference only; DESIGN.md keeps its existing authority (CDICF, `tools/design_gate.py`) | — |

Changes added by the integration to each specialist (generator: the build script used in the session, logic recorded
here): frontmatter `model: sonnet` (was `inherit`; HR-COST), `memory: user`, an "Anclaje en el CDIO" block binding it
to its CDIO datasets, to cdio-reviewer as the only gate, to cdio-standards-librarian for new criteria, to its DRX
report, and a memory protocol (read at start, one-fact-per-file at end, writes limited to its memory dir except G).

## Persistent memory

`memory: user` (documented Claude Code subagent field; values user|project|local) → `~/.claude/agent-memory/<agent>/`,
first 200 lines / 25 KB of `MEMORY.md` auto-loaded. Enabling it grants Read/Write/Edit, so read-only agents carry an
explicit instruction that their only write surface is their memory dir. It has no effect if auto memory is disabled.
Backups of the 3 pre-existing agents before edit: `~/.claude/backups/cdio-agents-20261112/`.

## DRX

Queue: `vault/research/cdio_elite/run_drx_cdio_elite.py` (depth 2, breadth 3, Sonnet 5.5), output
`vault/research/cdio_elite/drx-out/<letter>_<slug>/`, a topic counts only with its `DONE.json`. It shares the global
DRX lock with the DRX yield experiment and the CostaLuz queue, waits it out, never forces it.

## Not verified by this absorption

- Live delegation from cdio-core to a specialist in a FRESH session (agent definitions load at session start).
- The pack's fresh-agent missions (MYTILUS + a non-restaurant site) have not been run.
- Pack claims about Agent Teams are the pack author's, unverified here.
