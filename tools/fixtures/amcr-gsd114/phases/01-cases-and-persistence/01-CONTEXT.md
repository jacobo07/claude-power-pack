# Phase 1: Cases and Persistence - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning
**Mode:** Smart discuss, auto-accepted (unattended mission, `mode: yolo`; no operator available to answer). Every answer below is the recommended one, grounded in the approved scope `docs/specs/remaining-scope.md` and the binding spec `docs/specs/design.md` (spec wins on conflict).

<domain>
## Phase Boundary

Durable, audited storage for the engine's output: encrypted clients, cases, documents, items, extracted field values with confirmations beside them, assignments with rule traces, per-channel results, and an audit log. Wire the existing ingest output and operator confirmations into it, run the engine on confirm, log results per item x channel and advance the round through `advanceRound`. Exercised through a service layer and CLI scripts (as `npm run ingest` already is). No UI, no letters, no assistant, no partner sync in this phase.

Requirements: CASE-01..CASE-08.
</domain>

<decisions>
## Implementation Decisions

### Encryption at rest
- Encrypt the sensitive client fields at the application layer with an authenticated cipher (random IV per value, auth tag stored with the ciphertext). The SQLite file therefore holds ciphertext only.
- Key is read from `.env.local`, loaded at the service boundary; `.env.local` is git-ignored. A missing or wrong-length key makes every sensitive read/write throw with a named reason; there is no default key and no plaintext fallback.
- An over-long reference number is rejected by validation before it reaches the encryption layer, so it is never stored in any form.
- The ciphertext envelope carries a version tag so a key rotation can be added later without a schema change.

### Schema and migrations
- Models: `Client`, `Case` (methodologyVersion, currentRound), `Document`, `Item`, `FieldValue` (channel, field, extractedValue, confidence, operatorValue, confirmedBy, confirmedAt), `Assignment` (flow, round, rule, objective, trace JSON), `Result` (item x channel outcome: resolved / still open / updated), `AuditEvent` (actor, kind, subject, payload JSON, at), `Job` (kind, status, reason, partial result, attempts).
- The extracted value is never overwritten: a confirmation is stored as `operatorValue` + `confirmedBy` beside it.
- Source files are never copied into the repository or the database; only extracted values, their confidence and a source filename/hash are stored.
- Migrations only through `prisma migrate dev --create-only` then `prisma migrate deploy`; never plain `migrate dev`, never `migrate reset`. A test proves the FTS5 sidecar and the KB tables survive the new migration.

### Service layer and engine wiring
- A plain TypeScript service module (`src/cases/`) over the existing Prisma client: `createClient`, `openCase`, `saveDocument`, `confirmFields`, `confirmDocument`, `logResults`, `advanceCaseRound`, `listAudit`. No framework; Phase 3 will call it from route handlers.
- `confirmDocument` refuses unless the document is fully read and every flagged field has a confirmation; it then calls the existing engine `assignInitial` and stores each assignment with its rule trace. The engine is never started on a partly read document (existing project decision).
- `logResults` records a result per item x channel and, when a round is complete, calls `advanceRound` from `src/engine` and persists the new assignments and the case's `currentRound`. A known unruled case stays a flag on the item; persistence never decides it.
- CLI scripts under `src/cases/cli.ts` (`npm run case ...`) are the Phase 1 operator surface.

### Audit log and failed jobs
- One append-only `AuditEvent` table is the audit log. Every confirm, assignment and result writes an event in the same transaction as the change. Phase 2 writes approve and reopen into this same table via the same `recordAudit` helper.
- Extraction and generation work is wrapped in a `Job` row: on failure it is saved as `failed` with its reason, keeps its partial results, and a `retry` creates a new attempt against the same job. With no model API key on the machine, retry paths are tested against a boundary fake of the model client; the opt-in live test states why it skipped. No production code fakes a model call.

### Testing and gates
- Keep the existing tests and `tsc --noEmit` green. New tests: AAA pattern, each rule has a refusing test and a passing control (over-long reference refused / valid accepted; unconfirmed flag blocks confirm / confirmed passes; ciphertext check reads the raw SQLite file).
- Test DBs come from the existing `tests/db/fresh-db.ts` helper. Only the redacted fixture `tests/fixtures/sample-1/` is used; no real data is committed.

### Claude's Discretion
File layout inside `src/cases/`, exact column types, index choices, and zod schema shapes at the service boundary.
</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/engine/` (`assignInitial`, `advanceRound`, `resolveRules`, `projectPlan`, `diffFields`, traces) - pure TS, consumed as-is.
- `src/ingest/` (`pipeline.ts`, `review.ts`, `normalize.ts`, `schema.ts`) - produces the extracted values, confidence and flags to persist; `review.ts` holds the operator-confirmation shape.
- `src/db/client.ts` Prisma + better-sqlite3 adapter; `tests/db/fresh-db.ts` for isolated test databases.
- `tests/fixtures/sample-1/extracted.json` redacted golden fixture.

### Established Patterns
- ESM TypeScript strict, Vitest, zod at boundaries, exact-pinned dependencies, CLI entry points run via `tsx`.
- Migrations in `prisma/migrations/` with an FTS5 sidecar migration that plain `migrate dev` would treat as drift.

### Integration Points
- New Prisma models extend `prisma/schema.prisma`; generated client in `src/generated/prisma/`.
- `src/ingest/pipeline.ts` output feeds `saveDocument`; `src/engine/index.ts` is called from `confirmDocument` and `advanceCaseRound`.
</code_context>

<specifics>
## Specific Ideas

Windows environment: npm via `node.exe ...npm-cli.js`, git via `C:\Program Files\Git\cmd\git.exe`, vitest via `.\node_modules\.bin\vitest.cmd run` (use `--reporter=default` when a log line is the evidence). Work happens in a linked worktree on a feature branch (node_modules is a junction to the main checkout's).
</specifics>

<deferred>
## Deferred Ideas

- Key rotation tooling for the encryption key (envelope is versioned to allow it later).
- Multi-user actors in the audit log (single operator in phase 1; `actor` is a string).
</deferred>
