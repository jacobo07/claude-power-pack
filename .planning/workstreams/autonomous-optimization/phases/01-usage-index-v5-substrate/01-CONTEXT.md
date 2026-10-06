# Phase 1: usage_index v5 substrate - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss). ROADMAP marks this phase PLAN mode: the plan
must state the schema and migration design before the first code edit.

<domain>
## Phase Boundary

Execution history is ingested once per content identity into queryable structured state (ROADMAP Phase 1, IC-gen2
pillar O). Success criteria, verbatim from ROADMAP:

1. Schema v5 adds tool events (tool, input hash, path, result bytes), cwd, project/workstream attribution (mixed
   allowed), realpath + content identity. Migration is incremental: no re-read of files already ingested.
2. Negative controls go red when they should: mixed-project session attributed to both; two distinct histories not
   merged; junction alias counted once; `_archived` handled by declared rule; parser failure surfaced, never a
   silent zero; empty population refuses a verdict.
3. Population parity against the frozen KME-L denominator (102 sessions / 34,871 calls / cache_read
   11,549,646,300) on the GEX44 copy, with dedup reconciled to the unit.
4. Refresh cost measured (wall, bytes) for a cold build and for a delta.

The frozen pillar O rule in `vault/programs/incremental-cognition/gen2/ledger.json` is the closing contract; it
names the owners `tools/usage_index.py` (schema v4 today, `SCHEMA_VERSION = 4`) and `tools/tis_observed.py`
(`store_identity`, line ~349) and requires the v4 -> v5 migration to re-read zero already-ingested files, MEASURED.

</domain>

<decisions>
## Implementation Decisions

### Locked by the approved plan and the frozen gen2 ledger
- EXTEND `tools/usage_index.py` (schema v5) and reuse `tools/tis_observed.py::store_identity` for realpath + content
  identity. No new database, no new top-level module (HR-NOVELTY-001 record from Phase 0 = EXTEND_EXISTING_OWNER).
- Corpus on this plane = the Owner-authorized COPY `/home/kobii/kme-corpus/projects` (9.6 GB, frozen 2026-10-05,
  contains `_archived` and 3 relative symlinks recreated from laptop junctions). Pass it as the root explicitly;
  NEVER point a measurement at GEX44's own `~/.claude/projects`. Every result labelled `plane: gex44`.
- The index DB for measurements lives outside the repo and outside the corpus (e.g. under the job/mission scratch
  area); the corpus copy is read-only input.
- Parity target is the frozen KME-L denominator (102 sessions / 34,871 calls / cache_read 11,549,646,300). Any
  mismatch is reconciled to the unit (which sessions/calls differ and why), never rounded away.
- UNKNOWN / INCONCLUSIVE / UNMEASURED are never PASS. Parser failure is surfaced, never a silent zero. An empty
  population refuses a verdict.
- Never edit: CE/SC/IC-gen1 ledgers' `frozen` objects, gen2 `frozen` object, `tools/test_cognitive_economy_program.py`,
  `tools/test_skill_capability_program.py`, root `.planning/STATE.md`, `tools/gsd_mission.py`.
- Commits: explicit pathspec, one falsifiable increment each; verify `git log -1 --format=%s`.
- Phase ends with `01-EVIDENCE.md` (Product Delta + Intelligence Delta) and its gen2 ledger state rows for pillar O.

### Claude's Discretion
Table layout for tool events, attribution encoding (mixed allowed), the declared `_archived` rule, and the test
harness shape (follow existing V-gate style, e.g. `tools/test_ao_p0.py`).

</decisions>

<code_context>
## Existing Code Insights

- `tools/usage_index.py` (831 lines): SQLite index, `SCHEMA_VERSION = 4`, incremental migrations gated on
  `meta.schema_version`.
- `tools/tis_observed.py` (418 lines): `store_identity(base)` returns realpath-deduplicated store files + identity map.
- KME-L measurements: `vault/programs/incremental-cognition/measurements/*-KME-L-2026-10-05.md`; zero-rescan plan
  `vault/plans/zero-rescan-reality-scan-2026-10-05.md` (do NOT redo while dependencies are unchanged).
- Gen2 judge: `python3 tools/test_incremental_cognition_program.py --generation 2 --status|--selftest`.

</code_context>

<specifics>
## Specific Ideas

ROADMAP operating constraints apply to every phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
