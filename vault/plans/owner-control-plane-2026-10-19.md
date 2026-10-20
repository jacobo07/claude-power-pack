---
covers: [owner-control-plane, providerless-capital, control-intent-router, wait-owner-capital, econ-safex-canary]
status: PROPOSED (awaiting one Owner approval)
date: 2026-10-19
---

# Owner Control Plane -- Master Plan (SDD tier T3)

Written after a bounded, read-only Reality Delta Scan. Nothing was mutated: no ledger row, no packet, no commit.
Evidence grade: E1 = read from a durable file this turn; E2 = inferred; UNVERIFIED = not read.

## 1-6. Current reality (E1 unless stated)

| Item | Finding | Source |
|---|---|---|
| Why `subelo por 70M` was blocked | `hooks/econ_admission.js` (UserPromptSubmit, critical lane, settings.json:785) blocks EVERY prompt except the verbs `econ status` / `econ detach` when the bound goal is TOMBSTONED, EXHAUSTED or "next call does not fit". Its own text says "The cap is never raised here." | hook lines 1-19, 29, 129-138 |
| When | Transcript entry `blocked_by_hook`, 2026-10-19T10:09:35Z, uuid c7b1fcb0-4c7f-48d7-a4b0-333d6ab4407c, session 5615bc94, line 890 of its transcript (under the Power Pack project dir, NOT the econ-safex project dir). "Original prompt: subelo por 70M" is stored verbatim. | transcript |
| Binding | `goal=econ-safex gen=1 source=cwd` -- the target came from cwd. | same entry |
| Programme authority | One `programme` row, seq 2, value 32,000,000, source `capital:8d5183457124:econ-safex:...`. No later programme row. The 70M was NOT applied. | goal-budget/econ-safex/spend.journal.jsonl |
| Leases | L1 cap 4.0M (exhausted seq 16). L2 cap 26.5M opened seq 20 (`econ-safex:owner:L2`, reserves closeout 600k / proof 300k / recovery 300k). Tombstones: sid c95f76dd (used 25,988,707), sid 5615bc94 (used 26,210,306). | journal seq 15-104 |
| Auto successor | seq 95 `authority_required`, succession `econ-safex:auto:L2`, need 50,000,000, executable -58,855. The auto compiler asked for 50M. Risk: that is the blind-lease trap (Law 17). C9 must check the sizing code before any wake. | journal seq 95 |
| Programme headroom | Hook text reports 1,911,450 left of 32M. | transcript |
| Stop-loss already tripped | Packet `econ-safex-programme-32m-2026-10-13` says: "a lease ends with a dirty, unsealed worktree: stop and return to the Owner". It did. The Owner's reply was the capital message. | packet stop_loss |
| Dirty residual | Worktree `C:\Users\User\Apps\pp-econ-safex`, branch `econ/safe-exhaustion`, HEAD 4ea5b45a. Seven untracked routes: `.pp-capabilities`, `docs/{arch,changelog,constitution,prd}/tools__safex_regression.py.md`, `tools/safex_regression.py`, `vault/programs/econ-safex/evidence/W1-drills/`. Classification and validation NOT yet done (E2: the four docs files and `.pp-capabilities` look GENERATED_REPRODUCIBLE; the regression tool and drills look OWNED_UNVALIDATED). | git status |
| Existing capital machinery | `modules/provider_routing/capital_authority.py`, `tools/mission_spend.py capital-apply-pending`, `hooks/owner_capital_capture.js`. Grammar: `approve [everything]`, `approve <goal> only`, `modify <goal> to N[mk]`, `revoke <goal>`. Packet is hash-bound, has an expiry and invalidators. There is NO add operation and NO Spanish. | hook lines 18-33 |
| Wiring gap | `owner_capital_capture.js` is not named in `~/.claude/settings.json`. How it is registered is UNVERIFIED (C1 checks this first). |  |
| Providerless surface today | `tools/econ_plane.py` has only `status` and `detach`. | argparse help |
| Not yet scanned | Decision Plane providerless capability, Adaptive Lease Controller code, Global Event Fabric names, Recovery WAL API, whether econ-safex is a Ralph mission, active writers in other panes. Each is a C0/C1 item, not an assumption. | |

## Root-cause matrix

| Cause | Layer | Fix |
|---|---|---|
| R1 admission lane treats "unaffordable model call" as "reject every Owner input" | econ_admission.js | classify intent before affordability |
| R2 capital grammar has no ADD, no Spanish, no deterministic clarification | capital_authority + capture hook | typed grammar |
| R3 capital leg is packet-then-approve, so a typed intent has no path | capital_authority | `owner_intent` receipt kind with CAS |
| R4 tombstone is per-sid and the only advertised exit is `/clear` | econ_admission next-step text | successor wake owned by the runtime |
| R5 target comes from cwd | goal_binding | target = explicit goal or the single open authority boundary |
| R6 programme change does not wake the frontier | ledger | `PROGRAMME_AUTHORITY_CHANGED` consumer |
| R7 automatic succession opens `min(tranche, executable - keep - carry)` (ledger.py `_auto_succeed`). The journalled `need` 50,000,000 is econ-safex's configured `tranche`, not a compiler bug. With a 102M programme the next automatic lease would be about 50M: Law 17 violated by policy. | `ledger.set_succession` | tightening a tranche is always admitted without the Owner, so C9 lowers it (or replaces it with residual-derived sizing) BEFORE the capital lands |

## Design

**Authority order.** Owner > programme > goal > generation > lease > work unit > provider call. The fence stays on MODEL_REQUIRED only.

**Router.** Extend `econ_admission.js decide()` (same critical lane, no new lane). Order: authenticate (hook stdin event, not transcript text) -> exact grammar -> bind target -> validate version -> execute via `econ_plane.py capital-intent` (spawnSync, 9 s, same pattern as `detach`) -> deterministic clarification -> only then fall through to the existing affordability block. Outcomes: TYPED_CONTROL_OPERATION, DETERMINISTIC_CLARIFICATION, MODEL_REQUIRED, INVALID, STALE, CONFLICTED. Kill switch stays `CPP_ECON_ADMISSION=off`.

**Grammar (closed set, no model).**
- ADD: `subelo por X`, `sube por X`, `incrementa X`, `suma X`, `add X`, `raise by X`, `plus X`, `increase by X` -> new = current + X.
- SET: `subelo a X`, `sube a X`, `pon el tope en X`, `set to X`, `raise to X`, `modify <goal> to X` (existing) -> new = X.
- KEEP: `mantener`, `keep`. STOP: `stop`, `para`, `cierra el goal`, `revoke <goal>` (existing).
- Units: raw integer, `K`, `M`, with `,`/`_` separators already tolerated by the existing grammar. Decimals only as `1.5M`. Reject negative, zero ADD, NaN, overflow above a stated ceiling, unit-less ambiguous values.
- Ambiguous (e.g. `subelo 70M`, `70M`): providerless choice `ADD +70M` / `SET total 70M`; no guess.
- Negation guard reused from `owner_capital_capture.js` (`NEG`).

**Receipt (`owner_intent`).** receipt id, principal, ts, goal, op, previous, delta, new, source fingerprint (sha256 of session id + prompt text + event timestamp), expected_programme (CAS), idempotency key = fingerprint, state version, result, invalidators. Written intent-first to the existing recovery WAL, then one `programme` journal row carrying `source: owner-intent:<fp>`, then the event. Replay = same key -> report APPLIED, never re-add.

**CAS.** Apply under the ledger's existing lock; require journal programme value == expected_programme. SET below `totalSettled + totalOpen` is refused. ADD while in-flight is unknown: conservative (open reservations count as spent).

**States kept apart.** Goal `WAIT_OWNER_CAPITAL` (derived from an unresolved `authority_required` row, not stored per session). Generation: `TOMBSTONED` / `SEALED`. Lease L2 `EXHAUSTED`. Programme `ACTIVE`. Owner Control `AVAILABLE`. Model execution `FENCED`.

**Wake.** Receipt -> event `PROGRAMME_AUTHORITY_CHANGED` -> consumer recomputes residual (dirty classification + proof reuse), sizes the successor lease from residual / next sealable frontier / forecast / reserves (never = delta, never = old lease), opens it, then activates through the existing mission relay (`claude --bg --resume`, card) or lifts the tombstone, whichever C9's reality check shows is already supported. Anti-entropy sweep completes any step a crash interrupted.

**Dirty residual.** Seal-first: classify the seven routes (OWNED_VALIDATED_PENDING_COMMIT / OWNED_UNVALIDATED / GENERATED_REPRODUCIBLE / FOREIGN / CONFLICTING / UNKNOWN), reuse state-bound proof receipts, run only the missing validation, commit only owned paths with pathspec, never touch FOREIGN.

**Decision / resource / stop.** Active Decision packet option tokens and a declared REC alias resolve through the same router, bound to the packet fingerprint. STOP outranks everything and is never gated by affordability. Resource acknowledgement only for an already-materialized boundary.

## Canary (C13) -- the historical 70M

- Durable: yes (transcript entry above).
- Unapplied: yes (journal has no programme row after seq 2).
- Unambiguous: yes under the "por = ADD" contract. Expected result if the ledger still reads exactly 32,000,000 at apply time: 32M + 70M = 102M.
- Promotable under current governance: NOT as-is. The capture grammar never matched it and no packet sha was displayed. The existing apply leg already re-reads Owner entries from transcripts, so promotion by fingerprint is consistent with precedent, but its authenticity is E2 (a transcript is a writable file). Plan: the new router captures live events at E1 strength; for this one historical message the control plane renders the exact typed choice `ADD +70M -> 102M` and the Owner's single reply (or the promotion by fingerprint, if Owner prefers) is the receipt. This is decided once, at C13, from the live ledger -- not from this document.
- Not applied now. Not applied before approval.

## Mode by workstream

EXECUTION: reality delta, fence audit, grammar, Spanish aliases, receipt, idempotency, event, recompile, activation, dirty residual, Decision integration, fault injection, canary, vault/UKDL/CBR. PLAN then EXECUTION: router ownership, auth/target binding, CAS/WAL, WAIT_OWNER_CAPITAL contract. ULTRA-PLAN: not needed -- no foundational conflict found; the work extends econ_admission + capital_authority.

## Token budget (estimates, tokens; confidence LOW-MEDIUM; reuse-first)

| Stage | Lower | P50 | P80 | P95 | Boundaries | Avg CWS |
|---|---|---|---|---|---|---|
| C0-C1 reality + fence audit | 0.25M | 0.5M | 0.8M | 1.25M | 3-5 | 120k |
| C2-C4 router, grammar, auth/target | 1.2M | 2.4M | 3.9M | 6.0M | 12-20 | 150k |
| C5-C6 receipt, idempotency, CAS/WAL | 0.9M | 1.8M | 3.0M | 4.6M | 8-14 | 150k |
| C7-C9 states, event, lease sizing, activation | 1.3M | 2.8M | 4.8M | 7.5M | 14-24 | 170k |
| C10-C11 dirty residual, Decision/resource | 0.6M | 1.3M | 2.2M | 3.4M | 6-12 | 150k |
| C12 fault matrix | 0.8M | 1.6M | 2.6M | 4.0M | 8-14 | 150k |
| C13-C14 canary, repeat boundary | 0.5M | 1.5M | 3.0M | 5.1M | 6-16 | 170k |
| C15 vault, FIOS, UKDL, CBR | 0.4M | 0.8M | 1.3M | 2.0M | 4-7 | 120k |
| TOTAL | 5.95M | 12.7M | 21.6M | 33.9M | | |

Proposed hard authority: 22M (about P80), checkpoint at P50. No stage was measured; the table is a forecast and will be replaced by settled numbers per stage.

## CAPEX vs OPEX

- CAPEX: building the Owner Control Plane, charged to a NEW goal `owner-control-plane` (it cannot be charged to econ-safex, which is exhausted, and must not inflate it).
- OPEX: econ-safex roadmap continuation, charged to econ-safex programme after the canary. The 70M grant belongs here.

## Micro-commits (causal, revertible, pathspec-scoped)

1 incident receipt + this plan; 2 grammar module + tests (por/a); 3 router in econ_admission; 4 principal + target binding; 5 receipt + idempotency + CAS + WAL; 6 WAIT_OWNER_CAPITAL fold; 7 event + wake consumer; 8 adaptive successor sizing; 9 dirty-residual classifier; 10 Decision/STOP paths; 11 fault matrix; 12 canary evidence; 13 vault + FIOS + UKDL + CBR.

## Done-gate

New `tools/test_owner_control.py` (V-OCP-*), every detector driven from both poles; the fault matrix from the brief; liveness (`modules/liveness/reachability.py`) clean; `test_goal_lease.py` and `test_capital_authority.py` unchanged-green; canary shows capital -> successor ACTIVE with zero clear, zero lease-open, zero second Owner message.

## Conditions for returning to the Owner

A new programme ceiling beyond the approved one, a security boundary, an irreversible action, a scope decision, a human-only dependency, or a host limit evidence cannot resolve.
