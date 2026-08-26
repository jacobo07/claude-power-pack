---
spec_id: SPEC-KACQ-001
title: Durable External Knowledge Acquisition
status: APPROVED
tier: 3
approved_by: Owner
approved_on: 2026-08-26
covers:
  - knowledge-acquisition
  - external-knowledge-interface
  - prompt-corpus-registry
  - durable-job-ledger
  - playwright-session-manager
  - immutable-raw-response-vault
  - eva-consultoria-adapter
  - acquisition-priority-scheduler
---

# SPEC-KACQ-001 — Durable External Knowledge Acquisition

## 1. Problem

A corpus of 2,200 questions must be asked, one at a time, of an authenticated
third-party chat knowledge interface (EVA, Consultoria.io), over an estimated
30-70 hours of wall time. Today this is a manual loop: read question, paste,
send, wait, check it finished, copy, save, next.

The naive automation of that loop is a script that loses everything when the
browser crashes on hour 19. The requirement is not a script. The requirement is
a capability that survives process death, reboot, session expiry and DOM
change, never loses a captured answer, never re-asks an answered question, and
never silently promotes a vendor's opinion into institutional truth.

## 2. Reality Scan verdict (what already exists — do not rebuild)

Verified by reading implementations, not docstrings.

| Capability | Owner | Disposition |
|---|---|---|
| Playwright executor + `Dumper` ABC | `sleepless_qa/dumpers/{base,web}.py` | Subclass the ABC; new sibling adapter |
| Claim extraction | `deep-research/research_engines.py:712-736,920-969` | REUSE |
| Confidence (non-self-certifying) | `research_engines.py:684-706`, `fable_distillation/epistemic_ladder.py:88-117` | REUSE |
| Contradiction detection (per-run) | `research_engines.py:989-1153` | REUSE, extend to standing |
| Frontier question generation | `frontier_intelligence/unknown_unknown_generator.py:97-142` | REUSE, add enforced stop |
| Human escalation + idempotency | `owner_queue/owner_queue.py:74-77,165-192` | REUSE |
| Promotion gates | `dataset_first/manifest.py:75-113`, `hard_rules/writer.py:186-235` | REUSE |
| Secret redaction | `secret_firewall/detector.py:33-60` | REUSE |
| Pacing / throttle | `osa/throttle.py:120-162` | REUSE |
| Response completion gate | `done_gate/` (D2A: 95% owned) | EXTEND parent |

D2A family run (12 proposed): 1 FOLD, 3 KEEP, 8 DEFER. DEFER is read as
UNKNOWN, never as new; direct file:line evidence above overrides the score in
both directions.

### Genuine residue — this module builds only these

1. Persistent, addressable prompt registry (frontier_intelligence regenerates
   per-run; nothing survives as a queryable corpus with family + status).
2. Authenticated persistent browser session. `WebDumper` calls `new_context()`
   with no `storage_state` and hardcodes `headless=True`. Hard blocker.
3. Durable job ledger with a real state machine. `owner_queue` is a binary
   pending/done fold. `session_resilience` solves IDE-window topology.
4. Immutable raw artifact store. `deep_research` fetches raw HTML and derives
   markdown, then persists **neither** — only the synthesis. For an
   unrepeatable multi-day acquisition this is the highest-severity gap found.

## 3. Ownership

`claude-power-pack/modules/knowledge_acquisition/`. Not TUA-X: every reuse
target lives in the pack, the capability must serve future interfaces, and
`capability_runtime` is where a write-surface capability gets its contract,
rollback and kill switch. EVA is one adapter, not the system's name.

## 4. Corpus ground truth (measured 2026-08-26)

| File | Prompts | Already answered | Bare |
|---|---|---|---|
| `EVA_PRE_200_Six_Figure_First_30_Day_Launch_Reverse_Engineering.md` | 200 (`SF30-001`..`SF30-200`) | 17 | 183 |
| `EVA_2000_Prompts_CommonWealth_Ops_Brand_001.md` | 2,000 (`1.`..`2000.`) | 8 | 1,992 |

Total 2,200. **25 answers already captured** — these import as `COMPLETE`, not
`PENDING`. Requirement G (never re-ask a completed prompt) is live on day one.

### Parsing hazard (must not be solved naively)

In the main file the prompt marker `N.` at line start also matches numbered
list items **inside EVA's answers**: a raw scan yields 2,011 matches for 2,000
prompts, and the surplus ids repeat (`1, 2, 3, 1, 1, 2, 3, 5`). A parser that
trusts the regex silently fragments answers and mis-assigns provenance across
a 2,200-item corpus. Disambiguation is mandatory and must be asserted, not
assumed: prompt ordinals are strictly monotonic from 1 with no repeats, and
the parsed count must equal the declared corpus size or ingestion fails
closed.

## 5. Contracts

### 5.1 `KnowledgeInterface` adapter

Subclasses the existing `sleepless_qa.dumpers.base.Dumper` ABC
(`launch/trigger/capture/teardown`) so future interfaces plug in without
touching the engine. Differs from `WebDumper` in three required ways:
persistent `storage_state`, durable (non-`mkdtemp`) evidence directory, and a
long-lived browser context reused across N prompts rather than relaunching
Chromium per prompt.

### 5.2 Storage

SQLite (WAL) at `vault/knowledge_acquisition/kacq.db`, with isolated FTS5
sidecars for prompt and response text — own tables and triggers, never a
shared FTS table (Apex mandate BL-0068). Chosen over JSONL because 2,200
mutable rows with a state machine need transactional status updates; the
append-log pattern in `owner_queue` does not give that.

Raw vault: content-addressed, write-once, at
`vault/knowledge_acquisition/raw/<sha256[:2]>/<sha256>.md`. Never overwritten.
Every derived artifact records the extractor version that produced it, so any
derivation is re-runnable from raw.

### 5.3 Job state machine

`PENDING -> RUNNING -> {COMPLETE | FAILED | NEEDS_HUMAN}`, with
`FAILED -> PENDING` on bounded retry and `NEEDS_HUMAN -> PENDING` on operator
release. Illegal transitions are refused, not logged and ignored. Every
transition appends to an audit event table.

### 5.4 Delivery guarantee — stated honestly

**At-least-once with idempotent reconciliation. Not exactly-once.** Send and
persist cannot share a transaction across a browser boundary. Reconciliation:
before sending prompt P, inspect the live thread for an existing answer to P;
a would-be duplicate send becomes a detected already-answered. The CLI and
docs state this guarantee in these terms. Any claim of exactly-once is a spec
violation.

### 5.5 Security

No credentials in source, ever. Session bootstrap is a human-driven login into
a persisted `storage_state` file, which is git-ignored and never logged. All
log and evidence output passes `secret_firewall` redaction. On any access
control — login wall, CAPTCHA, rate limit — the system pauses durably and
reports what human action is needed. No evasion of any access control is in
scope, now or later.

## 6. Phasing and done-gates

| Phase | Deliverable | Done-gate (empirical, observed output) |
|---|---|---|
| 0 | Corpus parser, identity, registry, FTS5 | 2,200 parsed, 25 imported COMPLETE, ids stable across two runs, count assertion fails closed on drift |
| 1 | Ledger, state machine, resume, retry+backoff | `kill -9` mid-run then restart: no loss, no repeat, illegal transitions refused |
| 2 | Session manager + EVA adapter | Manual login persists; second process reuses session; expiry produces durable pause |
| 3 | Completion/integrity gate + raw vault | Real response captured; raw immutable; truncation and wrong-answer detected |
| 4 | Production Reality vertical slice, 5-10 real prompts | Real answers on disk with provenance; live crash + resume demonstrated |

Phases 5+ (extraction, standing contradiction detection, frontier recursion
with an enforced computed stopping criterion, promotion) are DEFERRED by Owner
decision. The contracts above leave the seams; no rewrite is required to add
them.

## 7. Explicit non-goals

Second knowledge graph. UI. Any access-control evasion. Automatic promotion of
a vendor answer to institutional truth — candidates stop at the validation
queue and require Owner adjudication through the existing gates.

## 8. Acceptance

Done requires every phase gate above to have produced observed output, the
guarantee in 5.4 stated accurately in shipped docs, zero secrets in tracked
files, and a clean pathspec-scoped commit history. "Should work" is not
evidence.
