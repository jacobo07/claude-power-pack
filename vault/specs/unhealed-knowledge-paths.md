---
title: Unhealed knowledge paths — the half-fix, the reader-less sink, and three stale records
date: 2026-09-04
tier: T2
status: DELIVERED 2026-09-04 — three commits, all gates observed green. Producer
        registration remains Owner-side under HR-001 (§6).
covers: [graphify_deferred, graphify_unhealed, writeback_verdict, ceps_corrections,
         from_stop_hook, ceps_drafts, owner_correction_capture, capture_liveness_correction]
origin: Owner 2026-09-04 — a mission to close the institutional-memory lifecycle,
        reduced to its measured residue after the reality scan found the
        architecture already owned.
---

# Spec — unhealed knowledge paths

## 1. What the scan actually found

The brief asked to extend `UKR`, `Knowledge Sovereignty Fabric`, `ICAF` and
`UCR-CIF` as canonical owners. Measured against `vault/plans/seip-corpus-2026-08-04.md`
§37-43, the first three own **zero** lines of this estate: they do not exist and
were shelved on purpose (`ukr-runtime-2026-07-30.md`: *6 of 6 mega-systems owned*).
`vault/audits/apir/NON_DUPLICATION_LEDGER.md` is BINDING and routes the mission's
other responsibilities — learning ascension, cognitive sovereignty, knowledge
runtime, liveness, governance, failure genome — to `EXISTS_AND_WIRED` owners
across 19 DO-NOT-BUILD rows.

So the honest residue was small, and it is what this spec delivers. **No new
system, no new corpus, no sixteenth majority-owned proposal.**

The estate's real constraint is not capability. `vault/plans/STOP_LEDGER.md`
carries **13 OPEN STOP #1s** awaiting an Owner ruling, including the UCR-CIF
A/B/C decision that blocks its Phase 6. That queue, not a missing memory layer,
is what bounds this repo.

## 2. Defect A — a fix applied to half its domain

`modules/graphify/indexer.py::deferred_repos()` filtered `verdict != "deferred"`.
`session_writeback` emits **two** verdicts meaning "this repo's graph trails its
sources": `deferred` (skipped for size) and `error` (the index raised,
`session_writeback.py:87` and `:92`). Commit `442f3bf` made the first
recoverable and left the second terminal.

An errored repo was therefore filtered out of the debt set, `--repair` could
never reach it, and nothing else healed it. A size deferral at least advertised
itself as temporary; an exception was silent. **That made a Stop-hook fault the
one permanent knowledge-loss path in the capture layer** — precisely the
correctness dependency a hook may not carry.

Measured honestly: `writeback.log` holds 2,248 rows — `deferred` 1390,
`indexed` 858, **`error` 0**. The path has never fired, so this recovers no lost
knowledge today; it closes a latent path on a reachable branch.

## 3. Defect B — a caller-less writer feeding a reader-less sink

`from_stop_hook()` is the only mechanism in this estate that notices **the Owner
correcting the agent** (`no, actually` · `that's wrong` · `revert` · `no es así`).
It is distinct from `conversation_quality_audit.py`'s same-named regex, which
matches the *assistant* correcting *itself* — different voice, different object,
not a duplicate.

State on 2026-09-04: no caller anywhere; documented reader `/ceps-confirm`
absent; `/ceps` absent from the 73 PP commands and from `~/.claude/commands`;
`vault/ceps/drafts/` absent from disk. It had provably never run — while the
PostToolUse advisory printed `-> Run /ceps query` on every captured error,
naming a command nobody could run.

This is the **inverse** of the estate's documented trap. The known shape is a
writer without a reader. This was a caller-less writer AND a reader-less sink,
which is why no liveness gate ever fired on it: `capture_liveness.py` compares
fires against records, and there were **no fires** to compare.

## 4. What was NOT built, and why

An anchor-diff staleness detector for graphify. `trust: "stale"` is dead
vocabulary — nothing sets or compares it — but `writeback()` calls a **full**
`index_repo` on every Stop for any repo under the cap, so the graph already
reconstructs itself from durable sources each session. Anchor-diffing would be
machinery the architecture obviates. The only real exposure is the capped repos,
and `--deferred --repair` now covers both their verdicts.

Also not built: any parallel memory runtime, registry, fabric or kernel.

## 5. Corrections to records this session disproved

Recorded because a spec that quietly rewrites its own founding numbers is worth
less than one that shows them moving.

| record | said | measured 2026-09-04 |
|---|---|---|
| `capture-layer-liveness.md` D8 | the CEPS bridge is inert until `settings.json`'s `"matcher": "Bash"` widens | **CLOSED.** The bridge now runs under a *matcher-less* dispatcher entry (`settings.json:218-226` → `hook-dispatcher.js:302`) and reaches every tool. Observed live: a PowerShell failure recorded `ceps_5d28a90f4498a814` during this session |
| `capture-layer-liveness.md` §"known gap" | this repo holds **zero** `memory/sessions/session_*.md` | false — `session_2026-05-21_1505.md` exists |
| `memory-audit-2026-08-09.md` | STOP #1 open; R1 (8 broken vault links) and R4 (router freshness gate) pending | both **shipped**: MEMORY.md carries the corrected `../../../` prefix and links `tools/router_freshness_gate.py`. `STOP_LEDGER` still reads OPEN — family-token drift, the known false negative |

## 6. Owner-side, not done here (HR-001)

`hooks/ceps_correction_stop.js` must be registered in `hooks/hook-dispatcher.js`
`CHAIN_MAP['Stop-chain']` and the dispatcher copied canonical → live. Until then
the producer does not fire and the reader has an empty pending set — an honest
degraded state, not a broken one. Queued in `vault/OWNER_QUEUE.md`.

## 7. Rules to seal (UKDL debt — see §9)

- `T-HALF-APPLIED-FIX-001` — when a fix makes one member of an enumeration
  recoverable, enumerate the siblings. `442f3bf` freed `deferred` and left
  `error` terminal for as long as the function existed. The remaining member is
  invisible precisely because the fix's own commit message reads as complete.
- `T-CALLERLESS-WRITER-READERLESS-SINK-001` — a writer with no caller feeding a
  sink with no reader is invisible to every fires-vs-records liveness gate,
  because zero fires cannot diverge from zero records. Liveness gates detect a
  **broken** pipeline, never an **unbuilt** one. Audit for functions with no
  caller separately from producers with no consumer.
- `T-USER-ROLE-IS-NOT-THE-HUMAN-001` — in a Claude Code transcript
  `type: "user"` covers tool results, system reminders, hook output and
  slash-command stdout. Any detector reading user turns must filter them or it
  will manufacture signal out of the harness talking to itself.
- `PR-ASSERT-IDENTITY-BY-NAME-001` — assert an identity field by its NAME, never
  the containing dict's truthiness. `confirm_draft` read `event["event_id"]`
  where `record_error` emits `id`; the event was created correctly the whole
  time while the back-link was stamped `None`. A truthiness check on the event
  would have passed.
- `T-SKIP-LINE-CONFLATES-TWO-CAUSES-001` — a log line that cannot distinguish an
  unparsed input from a legitimately empty result will be read as the benign
  one. `SKIP (no owner turns in tail)` meant a BOM-broken payload, and looked
  identical to a clean session.

## 8. Evidence (observed, not inferred)

| gate | observed |
|---|---|
| `tools/test_graphify_deferred.py` | **10/10**, exit 0 — 3 gates added incl. a negative control |
| positive control | `_UNHEALED` narrowed to `("deferred",)` → errored repo yields `debt=[]`, gate RED; with the fix, GREEN |
| `tools/test_ceps_corrections.py` | **9/9**, exit 0, **twice**; `vault/ceps/drafts` still absent and `events.jsonl` still 163 lines after both runs |
| `hooks/_tests/test-ceps-correction-stop.js` | **8/8**, `node --check` clean; six of eight are negative controls |
| CEPS regression | `test_ceps_edge_cases`, `_closed_loop`, `_full_cycle`, `_admission` all exit 0 |
| `verify_spp --row ceps-corrections` | STRICT PASS |
| live end-to-end | real transcript → hook → `dispatched turns=1`, system-reminder excluded → real draft `2c81d7a348e8` → `ceps.py drafts` listed it → `dismiss` retired it → pending 0. Artifacts removed; corpus byte-unchanged |
| live debt | 3 repos, all `deferred`, each now labelled with its verdict |

## 9. Debt left standing, deliberately

The rules in §7 belong in `vault/knowledge_base/ukdl-universal.md`, which
carries **64 uncommitted insertions from another pane**. Appending would package
their work under this commit. Same call the 2026-08-14 pass made for the same
reason; the rules live here until that tree is clean.

## 10. Rollback

Three independent commits, each one file group. Reverting the graphify commit
restores the previous filter exactly; reverting either CEPS commit leaves the
other harmless (a reader with no producer has an empty set; a producer with no
reader is what existed before).
