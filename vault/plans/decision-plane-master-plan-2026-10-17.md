---
covers: [decision-plane, owner-decision, decision-b, capital-option-compiler, tb-full-wakeup, forecast-drift]
status: PROPOSED (2026-10-17). Reality Delta Scan only; nothing implemented, no mission touched, no mirror.
---
# Decision Plane + Decision B self-hosting: Master Plan

## 1-4 Reality (measured this scan unless marked)
- decide: `a18250f0` is HEAD of feature/knowledge-acquisition; `510b647b` is its ancestor. `deliver_decision` stores {id,text,supersedes} on the mission, renders `DECISION id: text` directive lines, stops + resumes a live background owner. Tests: V-DECIDE x12, 102/102 (run earlier this session). It is TEXT-ONLY: no options, no parameters, no receipt hash, no event, no consumer index, no remote delivery.
- GEX44 PP install = `30fdbf0f`; its `gsd_mission.py` CLI lists {arm,session-start,handoff,directive,hold,release,envelope,supervise,status}: no `decide`, and it also lacks bind/obligation. "Mirror decide by hand" is a symptom of install drift.
- Decision B: the only durable representation found is PROSE in the worker's STATE.md ("OWNER DECISION NEEDED (TB-FULL, 2026-10-17, W0 reforecast)", /home/kobii/missions/tb-m2) plus chat. The handoff holds the id, not the contract. Class: DANGLING_DECISION_REFERENCE. Hidden parameter in option A: the new ceiling. A and C were never exclusive (capital vs cost-per-unit policy).
- Mission m-7e268fc1a6d9 is listed by the GEX44 host; m-80fd126a23cc is the held/terminal predecessor. Worker d0ad56cd liveness and the mission record's `decisions` field were NOT read (my record read returned nothing; I did not repeat that shape). Status: UNKNOWN until D0.
- Economics as reported by the worker (source unverified): ceiling 120M, mission total 11.17M at W0 seal, runway ~108.8M = ~72 units at 1.5M, unit cost 1.0-2.1M, breaker estimate 60M / trip 2.0x.

## 5 Forecast semantics (never mixed)
90M lower scenario | 196M central scenario (no evidence it is P50) | 320M upper scenario | 120M hard authority | 11.17M observed actual (source unverified) | 60M original estimate (soft target, breaker base) | 2.0x trip = breaker threshold. No TB P50/P80/P95 exists in the tree; OCA supports p50/p80/p95 tiers for capital packets, but nothing fed them. Drift: 196/60 = 3.27x.

## 6 Owner map
| Capability | Owner | State |
|---|---|---|
| Decision primitive | gsd_mission.deliver_decision | PARTIAL, landed |
| Owner capital apply | modules/provider_routing/capital_authority.py (OCA: typed-transcript proof, sha-bound, idempotent, BOUND..APPLIED) | PRODUCTION; reuse |
| Owner Escalation Gate / blocked typing | gsd_mission.py:621,838 + tools/mission_policy | PARTIAL in HEAD; `967988aa`,`b0ae1165` (replace a worker that ends on a policy-answerable question) NOT ancestors of HEAD |
| Authority = breaker trip | econ/mission-authority `02976b60` | NOT in HEAD |
| Phase lease / in-turn gate | `4752ce43` | in HEAD |
| Event fabric / remote wakeup | none found by an 11-pattern grep; absence NOT proven | UNKNOWN, D0 |
Writers: 1191 dirty paths, 1 foreign staged file (vault/plans/d12b-progress-2026-10-14.md), ~90 worktrees. Untouched.

## 7 Root causes
RC1 decision lives in prose (STATE.md/handoff). RC2 options authored as free text, no closure gate. RC3 orthogonal dimensions fused into A/B/C. RC4 capital packet never compiled though OCA exists. RC5 delivery = CLI text onto a lagging install. RC6 wake = model/CLI relay. RC7 forecast drift not institutionalized. Owner Turn Amplification on this boundary so far: 2 turns / 1 irreducible = 2.0.

## 8-30 Design (thin: one module + wiring; reuse OCA, deliver_decision, mission_policy)
- Registry: append-only `decisions.jsonl` per mission dir; independent of pane/session/worker/STATE.md.
- Object: id, goal, mission, unit, class, status (OPEN, READY_FOR_OWNER, RESOLVED, SUPERSEDED, INVALIDATED, EXPIRED), question, evidence handles + fingerprint, dimensions[], options[] with param schemas, recommendation (separate field, never authority), consumers, wake policy, invalidators, freshness.
- Classes: CAPITAL, SCOPE, PRODUCT, SECURITY, IRREVERSIBLE, EXTERNAL, RISK. Decision B = composite: CAPITAL (ceiling), SCOPE (unchanged), EFFICIENCY (continue optimization, default-on).
- Completeness compiler + Closure Gate: an option is selectable only if applying it needs no further parameter; else it stays internal. Gate question: "if selected now, can the system apply and continue?"
- Capital Option Compiler: from settled, reserved, remaining obligations, per-unit costs, reserves, breaker; emits OCA-compatible packets. Forecast Quality Gate: no quantile is invented; scenarios are labelled scenarios.
- Receipt: typed, hashed, append-only: option, parameters, ceiling, scope, efficiency, evidence fingerprint, consumers. Text is a view.
- Short input: option token -> receipt with no model; ambiguous -> list valid tokens.
- `decide` evolves: create / show / resolve / supersede / apply; legacy `--text` kept.
- Event + remote: OWNER_DECISION_COMMITTED written to the shared decision store; GEX44 supervise pass consumes it idempotently (receipt sha) and applies + wakes locally. Transport chosen by measurement in D5 (VPS dispatcher job channel vs git ref push to the ssh://gex44 bare repo). The one-time sync of GEX44 PP to HEAD is a normal software deploy, not decision-time mirroring; it trips the DEPLOY hard rules (read `hardrule_compile.py --class DEPLOY` first).
- Wake: Actionable Frontier recompute -> WAKE_EXISTING_EXECUTOR | PREPARE_SUCCESSOR | WAIT_*. A dead worker gets a successor compiled from mission state; the decision is never lost.
- Capital apply through OCA (bound to packet sha, idempotent per (sha, goal)); the model never edits ledgers. Raising the ceiling keeps breakers, adds a reforecast trigger.
- Idempotency: replay of a receipt = no second apply, no second wake. Staleness: evidence fingerprint changed before answer -> INVALIDATED, new packet.
- Forecast drift incident: record 3.27x; attribute only from measured causes: prefix re-read per call (~73k/call), 4/7 failed continuations (fixed `705218e0`), bootstrap-only epochs (0.9M), Work-Class estimate error. Others are hypotheses until D7 measures them. Feed Work-Class costs to the allocator.

## 31-35 Decision B canary and TB-FULL
Create the object from the STATE.md prose (read-only), compile options, show once, receive one token, OCA apply, event, wake, continue the frontier (Phases 17-19, critical path to the checkpoint). Efficiency stays on: capital never waives it. Reprofile after ~6 optimized units. The 26 Oct checkpoint is represented as a scheduler condition, not model memory (verify it is still the canonical date; the repo plan `79359618` dates checkpoints to 25 Dec).

## 32 Decision B: complete executable options (raise-capital branch)
Common to all: scope UNCHANGED; efficiency policy CONTINUE_OPTIMIZATION (on); breakers stay; auto-reforecast packet at the earlier of 6 optimized units or 60M settled; spend never targets the ceiling.
| Token | New hard ceiling | Increment | Basis | Reserve over the basis | Runway after 11.17M |
|---|---|---|---|---|---|
| R-200 | 200M | +80M | central scenario 196M | 4M (2%, thin) | 188.8M |
| R-320 | 320M | +200M | upper scenario 320M | 0 over the upper scenario | 308.8M |
| R-REFC | 120M (unchanged) | 0 | reforecast first | n/a | 108.8M (~72 units at 1.5M, worker keeps running) |
Recommendation (not authority): R-200. You chose to raise; 200M funds the central scenario and the trigger re-prices it with measured data. R-REFC loses nothing in time because the runway covers ~72 units.
Caveat: no quantiles exist, so none of these is a P80 or P95 ceiling.

## 36-37 Modes and commits
EXECUTION: D0, D1 (Registry), D4, D6, D9, D10, D11. PLAN then EXECUTION: D2, D3, D5, D7. No ULTRA-PLAN: ownership is clear (OCA owns capital apply, deliver_decision owns consumption). Micro-commits: incident evidence; registry+object; completeness+closure; capital compiler; receipt+short input; decide CLI; event emitter+consumer index; GEX44 consumer; OCA apply; idempotency+staleness; forecast drift; Decision B migration; TB wake; UKDL/FIOS/CBR. Each pathspec-scoped, verified with `git log -1 --format=%s`.

## 38-40 Budget (processed tokens, M). These are my judgment estimates, not measured quantiles; confidence LOW-MEDIUM; unit costs are unmeasured until D0
| Stage | Sem. LB | Lower | P50 | P80 | P95 | Hard | Boundaries | Avg CWS |
|---|---|---|---|---|---|---|---|---|
| D0 reality + B reconstruction + owner map | 0.3 | 0.5 | 0.8 | 1.2 | 2.0 | 2.5 | 6-10 | 90k |
| D1 registry + object | 0.4 | 0.6 | 1.0 | 1.6 | 2.5 | 3.0 | 8-12 | 90k |
| D2 completeness + closure | 0.3 | 0.5 | 0.8 | 1.3 | 2.0 | 2.5 | 6-10 | 90k |
| D3 capital option compiler | 0.5 | 0.7 | 1.2 | 1.9 | 3.0 | 3.5 | 10-14 | 95k |
| D4 receipt + short input | 0.3 | 0.4 | 0.7 | 1.1 | 1.7 | 2.0 | 5-8 | 85k |
| D5 event router + remote consumer | 0.6 | 0.9 | 1.6 | 2.6 | 4.0 | 4.5 | 12-18 | 100k |
| D6 OCA authority apply | 0.3 | 0.5 | 0.8 | 1.3 | 2.0 | 2.5 | 6-10 | 90k |
| D7 forecast drift + Work-Class feedback | 0.3 | 0.5 | 0.8 | 1.3 | 2.0 | 2.5 | 6-10 | 90k |
| D8 fault-injection suite | 0.6 | 0.9 | 1.5 | 2.4 | 3.6 | 4.0 | 10-16 | 95k |
| D9 Decision B canary | 0.4 | 0.6 | 1.0 | 1.6 | 2.5 | 3.0 | 8-12 | 90k |
| D11 vault/FIOS/UKDL/CBR | 0.3 | 0.5 | 0.8 | 1.3 | 2.0 | 2.5 | 5-8 | 85k |
| CAPEX total | 4.3 | 6.6 | 11.0 | 17.6 | 27.3 | 32.5 | | |
OPEX (D10, TB-FULL continuation) is booked against the TB programme, not here. Requested CAPEX authority: 20M hard ceiling (P80 + margin), stop-loss at 2x P50 = 22M never reached by construction. D1+D2+D4 are one module; expect the realized P50 below the table.

## 41-43 Approval and return conditions
Packet hashes: none exist yet. Before the canary D3 compiles the OCA packet and records its sha256; a selection given now is recorded as intent bound to the option terms above and becomes authority only when OCA binds it to the compiled packet. If the compiled terms differ from the table, I ask again; if the OCA grammar rejects a combined phrase, one short confirm is needed.
Return to Owner only for: a new ceiling beyond the selection, a security boundary, an irreversible action, a scope or product choice, an external dependency, a host limit evidence cannot resolve, or the DEPLOY rule demanding an Owner phrase for the GEX44 sync.
