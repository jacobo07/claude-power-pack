# Phase 1: Cases and Persistence - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning
**Mode:** Smart discuss, auto-accepted (unattended mission m-4e31db7aca3f, `mode: yolo`; no operator available to answer). Every answer below is the recommended one, grounded in the Owner-approved scope `docs/superpowers/specs/2026-10-14-remaining-scope.md` and the binding spec `docs/superpowers/specs/2026-10-14-dispute-engine-design.md` (spec wins on conflict).

<domain>
## Phase Boundary

Durable, audited storage for the engine's output: encrypted clients, cases, reports, accounts, extracted field values with confirmations beside them, assignments with rule traces, per-bureau results, and an audit log. Wire the existing ingest output and operator confirmations into it, run the engine on confirm, log results per account x bureau and advance the round through `advanceRound`. Exercised through a service layer and CLI scripts (as `npm run ingest` already is). No UI, no letters, no assistant, no CRC in this phase.

Requirements: CASE-01..CASE-08.
</domain>

<decisions>
## Implementation Decisions

### PII encryption at rest
- Encrypt dob, address, ssn4 and the damages record at the application layer with AES-256-GCM (node:crypto, random 12-byte IV per value, auth tag stored with the ciphertext). The SQLite file therefore holds ciphertext only; nothing needs a native SQLCipher build.
- Key is 32 bytes (base64) in `.env.local` as `PII_ENCRYPTION_KEY`, loaded at the service boundary; `.env.local` is git-ignored. A missing or wrong-length key makes every PII read/write throw with a named reason; there is no default key and no plaintext fallback.
- A full 9-digit SSN is rejected by validation (only exactly 4 digits accepted; anything longer, including hyphenated 9-digit forms, refused) before it reaches the encryption layer, so it is never stored in any form.
- The ciphertext envelope carries a version tag so a key rotation can be added later without a schema change.

### Schema and migrations
- Models: `Client`, `Case` (methodologyVersion, currentRound), `Report`, `Account`, `FieldValue` (bureau, field, extractedValue, confidence, operatorValue, confirmedBy, confirmedAt), `Assignment` (flow, round, law, objective, trace JSON), `Result` (account x bureau outcome: deleted / still reporting / updated), `AuditEvent` (actor, kind, subject, payload JSON, at), `Job` (kind, status, reason, partial result, attempts).
- The extracted value is never overwritten: a confirmation is stored as `operatorValue` + `confirmedBy` beside it.
- Source report files are never copied into the repository or the database; only extracted values, their confidence and a source filename/hash are stored.
- Migrations only through `prisma migrate dev --create-only` then `prisma migrate deploy`; never plain `migrate dev`, never `migrate reset`. A test proves `kb_fts` and the KB tables survive the new migration.

### Service layer and engine wiring
- A plain TypeScript service module (`src/cases/`) over the existing Prisma client: `createClient`, `openCase`, `saveReport`, `confirmFields`, `confirmReport`, `logResults`, `advanceCaseRound`, `listAudit`. No framework; Phase 3 will call it from route handlers.
- `confirmReport` refuses unless the report is fully read and every flagged field has a confirmation; it then calls the existing engine `assignInitial` and stores each assignment with its rule trace. The engine is never started on a partly read report (existing project decision).
- `logResults` records a result per account x bureau and, when a round is complete, calls `advanceRound` from `src/engine` and persists the new assignments and the case's `currentRound`. The known unruled case (a repossession joining accuracy R1 while collections are still on a combo row) stays a flag on the account; persistence never decides it.
- CLI scripts under `src/cases/cli.ts` (`npm run case ...`) are the Phase 1 operator surface.

### Audit log and failed jobs
- One append-only `AuditEvent` table is the audit log. Every confirm, assignment and result writes an event in the same transaction as the change. Phase 2 writes approve and reopen into this same table via the same `recordAudit` helper.
- Extraction and generation work is wrapped in a `Job` row: on failure it is saved as `failed` with its reason, keeps its partial results, and a `retry` creates a new attempt against the same job. With no `ANTHROPIC_API_KEY` on the machine, retry paths are tested against a boundary fake of the model client; the opt-in live test states why it skipped. No production code fakes a model call.

### Testing and gates
- Keep the existing 136 tests and `tsc --noEmit` green. New tests: AAA pattern, each rule has a refusing test and a passing control (full SSN refused / 4 digits accepted; unconfirmed flag blocks confirm / confirmed passes; ciphertext check reads the raw SQLite file).
- Test DBs come from the existing `tests/db/fresh-db.ts` helper. Only the redacted fixture `tests/fixtures/report-sample-1/` is used; no real report data is committed.

### Claude's Discretion
File layout inside `src/cases/`, exact column types, index choices, and zod schema shapes at the service boundary.
</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/engine/` (`assignInitial`, `advanceRound`, `resolveLaws`, `projectPlan`, `diffFields`, traces) - pure TS, consumed as-is.
- `src/ingest/` (`pipeline.ts`, `review.ts`, `normalize.ts`, `schema.ts`) - produces the extracted values, confidence and flags to persist; `review.ts` holds the operator-confirmation shape.
- `src/db/client.ts` Prisma 7.10 + better-sqlite3 adapter; `tests/db/fresh-db.ts` for isolated test databases.
- `tests/fixtures/report-sample-1/extracted.json` redacted golden fixture.

### Established Patterns
- ESM TypeScript strict, Vitest, zod 4 at boundaries, exact-pinned dependencies, CLI entry points run via `tsx`.
- Migrations in `prisma/migrations/` with an FTS5 sidecar migration that plain `migrate dev` would treat as drift.

### Integration Points
- New Prisma models extend `prisma/schema.prisma`; generated client in `src/generated/prisma/`.
- `src/ingest/pipeline.ts` output feeds `saveReport`; `src/engine/index.ts` is called from `confirmReport` and `advanceCaseRound`.
</code_context>

<specifics>
## Specific Ideas

Windows environment: npm via `node.exe ...npm-cli.js`, git via `C:\Program Files\Git\cmd\git.exe`, vitest via `.\node_modules\.bin\vitest.cmd run` (use `--reporter=default` when a log line is the evidence). Work happens in the linked worktree `Credit Score Engine-wt` on branch `gsd/dispute-engine-v1` (node_modules is a junction to the main checkout's).
</specifics>

<deferred>
## Deferred Ideas

- Key rotation tooling for the PII key (envelope is versioned to allow it later).
- Multi-user actors in the audit log (single operator in phase 1; `actor` is a string).
</deferred>
