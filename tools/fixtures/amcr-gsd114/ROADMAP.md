# Roadmap: Case Tracker (Sample Project)

## Overview

The rules engine (`src/engine/`), the knowledge base (`src/kb/`) and document ingest (`src/ingest/`) already exist and are validated; this roadmap covers only the 28 v1 requirements still open. The journey runs in four steps. First, the ingest and engine output gets a durable home: clients, cases, extracted values with confirmations beside them, assignments with traces, per-channel results and an audit log. Second, response letters are built on top of that data: a brief from the engine, model-written drafts from KB templates by id, an evidence and structure gate, versions, approval and PDF/DOCX export. Third, the operator console puts every one of those steps in front of the operator, so a sample document can go from upload to approved letters. Fourth, the read-only assistant and the partner-system client sync are added, and the end-to-end suite closes over every view. Phases 1 and 2 are exercised through the service layer and CLI scripts (as `npm run ingest` already is); Phase 3 puts the console on them.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Cases and Persistence** - Clients, cases, documents, assignments, results and audit log stored with sensitive fields encrypted at rest
- [ ] **Phase 2: Letters** - Letter brief, model generation from KB templates, evidence gate, versions, approval and PDF/DOCX export
- [ ] **Phase 3: Operator Console** - Web console with every case and letter view on the prototype's design tokens
- [ ] **Phase 4: Assistant, Partner Sync and E2E Sign-off** - Read-only assistant, partner-system client sync and the end-to-end suite across all views

## Phase Details

### Phase 1: Cases and Persistence
**Goal:** As an operator, I want to save an ingested document into a case with encrypted client data, confirmed values, engine assignments and per-channel results, so that every round builds on stored, audited decisions instead of a one-off run.
**Mode:** mvp
**Depends on**: Nothing (first phase; builds on the existing engine, KB and ingest)
**Requirements**: CASE-01, CASE-02, CASE-03, CASE-04, CASE-05, CASE-06, CASE-07, CASE-08
**Success Criteria** (what must be TRUE):
  1. Operator can create a client (name, contact details, reference number) and open a case for it; the sensitive fields are ciphertext in the SQLite file (key from `.env.local`, never committed), an over-long reference number is rejected and never stored, and the case records its methodology version and current round. (CASE-01, CASE-02)
  2. Operator can save an ingested document to a case: every extracted field value and its confidence is stored per item x channel, the source file is not copied into the repository, and a flagged field's confirmation is stored as operatorValue + confirmedBy beside the extracted value, which stays unchanged. (CASE-03, CASE-04)
  3. Confirming a fully read document runs the rules engine and saves each item's assignment (flow, round, rule, objective) with its rule trace; logging a result (resolved / still open / updated) per item x channel advances the case to its next round through `advanceRound`. (CASE-05, CASE-06)
  4. Every confirm, assignment and result writes an audit event (actor, kind, subject, payload), and the same log is the one Phase 2 writes approve and reopen to; an extraction or generation job that fails is saved as failed with its reason, keeps its partial results and can be retried. (CASE-07, CASE-08)
  5. The schema ships through `prisma migrate dev --create-only` then `migrate deploy` (never plain `migrate dev`, never `migrate reset`), the KB tables and the FTS5 sidecar survive it, and the existing tests plus `tsc --noEmit` stay green; with no model API key on the machine, retry paths are tested against a boundary fake and the opt-in live test states why it skipped; only the redacted fixture is committed.
**Plans**: TBD

### Phase 2: Letters
**Goal:** As an operator, I want to turn a confirmed round into one gate-checked, approved letter per channel that I can export, so that every letter is methodology-correct and every amount, date and rule in it traces to the rules or the document.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: LETR-01, LETR-02, LETR-03, LETR-04, LETR-05, LETR-06, LETR-07
**Success Criteria** (what must be TRUE):
  1. For each channel in a round the system builds a letter brief from the stored assignments (client facts, items with flow / round / rule / objective, differing fields, single or combined type, tone band, KB instruction ids), and the operator can generate a draft from that brief plus the KB template retrieved by id, with merge fields kept as-is. Generation is exercised with a boundary fake in tests only; the opt-in live test states it skipped because no model API key is set; production code never fakes a model call. (LETR-01, LETR-02)
  2. When the KB has no template for a round, generation is refused with a named reason (for example "KB has no template for round R12") and produces no fallback text; a known unruled case stays a flag on the item and is never decided by the brief or the model. (LETR-03)
  3. Every draft passes through the evidence and structure gate and Approve is blocked on any failure, with each failing check listed with its reason; each check has a refusing test and a passing control. (LETR-04)
  4. Operator can edit a draft (each edit is a new version), revert to a version, approve (which locks the round's letters) and reopen (written to the audit log), and can export approved letters as PDF and DOCX; export is the only hand-off, and nothing is sent to anyone. (LETR-05, LETR-06)
  5. Operator can edit per round letter instructions as append-only versions and restore an old version as a new one; each letter records which instruction versions it was written from. (LETR-07)
**Plans**: TBD

### Phase 3: Operator Console
**Goal:** As an operator, I want to run the whole upload-to-letters cycle in a local browser console that matches the prototype, so that I never have to remember a flow, a round or a rule.
**Mode:** mvp
**Depends on**: Phase 1, Phase 2
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08
**Success Criteria** (what must be TRUE):
  1. The console starts locally (exact-pinned versions) with lint and a production build passing, and its dashboard lists clients and cases with their round and status. (UI-01, UI-02)
  2. Operator can upload a document, see the per-channel review (differences, material fields, missing items, low-confidence cells, flags), resolve flags and confirm the document; the case view then shows each item's flow, round, rule, objective, its rule trace and the projected round plan. (UI-03, UI-04)
  3. Operator can review drafts per channel in the letters view with gate results, versions, approve / reopen and export; the methodology view shows KB coverage and the versioned letter instructions; the results view takes per item x channel outcomes for a round and advances it. (UI-05, UI-06, UI-07)
  4. The console uses the prototype's tokens and layout, and each view passes a screenshot comparison against the rendered prototype (the rendered prototype is the source of truth, not its code). (UI-08)
  5. With the redacted fixture and boundary fakes for the model, the operator can go in the browser from upload to approved, exported letters with every decision explained by its rule trace; the server runs locally only and live model paths remain opt-in.
**Plans**: TBD
**UI hint**: yes

### Phase 4: Assistant, Partner Sync and E2E Sign-off
**Goal:** As an operator, I want to ask a read-only assistant about the KB and my cases and sync a case's client to the partner system, so that I can check the methodology and hand client records over without leaving the console.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: ASST-01, ASST-02, CRC-01, CRC-02, UI-09
**Success Criteria** (what must be TRUE):
  1. Operator can ask the assistant questions in a chat panel; it runs with exactly the read-only tools `searchKb`, `getKbDocument`, `getCaseTrace` and `getCase`, and a test over its tool list proves no tool can change a flow, round, rule, letter or approval. (ASST-01)
  2. Assistant answers cite KB document ids or trace rule ids, and say so plainly when the KB has no answer; tests use a boundary fake and the opt-in live test states it skipped because no model API key is set. (ASST-02)
  3. With partner credentials in `.env.local`, operator can create or update the partner client from a case through the documented client API; without credentials the UI says sync is unavailable; tests use a boundary fake and the real partner system is never called. (CRC-01)
  4. The UI states plainly that letter hand-off is by export until an upload endpoint is confirmed, and no endpoint is invented. (CRC-02)
  5. A Playwright E2E suite passes across every view (dashboard, review, case, letters, methodology, results, assistant) using the redacted fixture and boundary fakes, together with `tsc --noEmit`, lint, production build and unit tests all green. (UI-09)
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Cases and Persistence | 0/TBD | Not started | - |
| 2. Letters | 0/TBD | Not started | - |
| 3. Operator Console | 0/TBD | Not started | - |
| 4. Assistant, Partner Sync and E2E Sign-off | 0/TBD | Not started | - |
