---
title: CRPF — Phase 0 overlap audit (STOP #2, blocking)
date: 2026-07-27
status: STOP_2_PENDING_OWNER — no CRPF architecture designed, per instruction
charter: vault/knowledge_base/COMPENDIUM_CHARTER.md (CRPF = 2nd family, Parts I–XXII, unbuilt)
pillar: Colibrì (R-003), read in full from the extracted RE corpus
---

# CRPF overlap audit — the charter's boundary omits the actual owner

## Verdict

**CRPF as chartered is ~80 % already owned by `cognitive_os` (CO-00…CO-10),
which is both SEALED (SCS C61) and LIVE (SCS C62).** Measured this session:
`tools/test_cognitive_os_build.py` → `COGNITIVE_OS_BUILD_PASS=68/68`, exit 0.
Not a spec — running code wired into `kclaude.ps1`.

## The charter's five claims, tested against the estate

`COMPENDIUM_CHARTER.md` states: *"`executionos-lite` tiers the task; nothing
tiers the assets. There is no heat model, no promotion/demotion policy, no
prefetch discipline, no admission control contract, and no declared degradation
order under pressure."*

| Charter claim | Reality | Verdict |
|---|---|---|
| "no heat model" | CO-04 `memory.py`: `TIER_RANK` / `TIER_CONTEXT_COST` / `TIER_TRUST` + `_KIND_TIER` mapping 20 asset kinds to HOT/WARM/COLD/EXTERNAL home tiers | **FALSE** |
| "no promotion/demotion policy" | CO-04 Part II is titled *Paging: Promotion and Demotion*; `DEPTHS = (discovery, summary, full)` page-in ladder, lossless page-out. CO-06 `gc.py` scores eviction by recency + relevance + aging, with `PROTECTED_KINDS` pinned | **FALSE** |
| "no prefetch discipline" | CO-04 III.4 forbids speculative promotion; promotion requires proven need. A prohibition *is* a discipline | **FALSE as stated** (see the one real gap below) |
| "no admission control contract" | CO-00 = 60 % ceiling, projective admission, 45–55 % action band. CO-02 `governor.py` nested envelope, DOWNGRADE-over-REFUSE. CO-08 `scheduler.py` hard hot-session cap, rung-3 block in kclaude | **FALSE** |
| "no declared degradation order" | CO-06 `_BAND_THRESHOLD = {AMBER: 12.0, RED: 6.0, BREACH: 4.0}` — graduated eviction declared numerically, by band | **FALSE (partial residue, below)** |

## Root cause — the same enrollment defect, sixth measured instance

The charter's CRPF boundary names three non-owners: `cost_collapse` (model
routing), `graphify` GK-06 (context packs), `memory-engine` (hot/cold split).
It never names `cognitive_os` — the family that actually owns the territory.

The boundary was **curated from what someone remembered, not discovered from
what exists** (`PR-COVERAGE-BY-CONSTRUCTION-001`). A component absent from the
denominator cannot be scored as overlap; absence read as a gap. Prior instances:
CPP-ACI audit denominator · Liveness Ledger · D2A `FAMILY_REGISTRY` ·
`corpus_roi.py` `CORPUS_REGISTRY` · CPP-IAS `SYSTEM_REGISTRY`. This is the sixth.

## Colibrì's 11 universal abstractions, audited by mechanism

| # | Colibrì abstraction | Existing owner | Verdict |
|---|---|---|---|
| 1 | Cognitive Tiering | CO-04 (cost-axis tiers, live in `memory.py`) | REUSE. Colibrì tiers by *scope lifetime* (constitutional→assistant→project→mission), CO-04 by *retrieval cost*. The scope axis is a thin EXTEND, not a family |
| 2 | Resource Envelope Planning | `one_shot/compiler.py` (budget), CO-00 (context projection), `cost_collapse` (model tier), `spec_gate` | PARTIAL — the parts exist, a single read-only pre-mission envelope object does not. Natural home is **E4** (`contract_fabric` + `one_shot` + `karimo-harness`, "unified mission manifest"), already chartered |
| 3 | Capability Doctor | `liveness/reachability.py`, `liveness_ledger.py`, `/liveness`, `setup_os/scanner.py`, SQI-03 environment qualification, CRAIF-02 activation simulation | REUSE. Residue = the stable-ID/severity/remediation/exit-code *contract shape* as a universal |
| 4 | Honest Admission Control | CO-08 hard cap (rung-3 block), CO-09 loop/subagent admission + kill switch, CO-02 governor | REUSE. "Concurrency claims must match state isolation" is a **Hard Rule candidate**, not a family |
| 5 | Context Slot Isolation | `pane_map`, session ids, `repo_coordinator`, worktree isolation, `PP_PANE_SID` | Already routed to the approved **KSF Authorized State** family (G-KSF-5, namespace sovereignty) |
| 6 | Warm Continuation (canonical ≠ cache) | CO-07 `hibernation.py`, `rehydration.py`, Lazarus, snapshots; **E2** already chartered to extend `session_resilience` | REUSE + E2. "Cache as Memory" is a **Trap candidate** |
| 7 | Cognitive Heat Map (value-weighted) | CO-06 scores recency + relevance + aging; relevance is binary. `recall_roi`, `corpus_roi.py`, IAS C1 portfolio hold the value signals | EXTEND CO-06 — wire value into heat rather than build a second heat engine |
| 8 | **Predictive Prefetch** | **Nothing.** CO-04 III.4 explicitly forbids speculative promotion as an anti-pattern | **GENUINE GAP — and a doctrinal conflict.** Colibrì proposes prefetch *with* a harmless-failure guardrail; CO-04 bans it outright. Cannot be built silently; requires an explicit reconciliation of a sealed anti-pattern |
| 9 | Semantic Preservation Under Pressure | CO-02 DOWNGRADE-over-REFUSE + CO-06 band thresholds cover the *behaviour* | **PARTIAL GAP.** The ordered 8-step ladder (concurrency → prefetch → cache → latency → sequential → cheaper model w/ approval → reduce scope → block) plus the NEVER list (omit checks, retire security, invent evidence, alter scope silently) does not exist as one declared contract. Strong **Hard Rule candidate** |
| 10 | Small Trusted Kernel | Architectural principle; PP carries 71 modules | REFERENCE only |
| 11 | Platform Compatibility Boundary | The entire Windows Bash-bridge doctrine + `wrapper/` adapters | REUSE (heavily owned) |

**Score: 7 REUSE · 2 PARTIAL · 1 GENUINE (conflicting) · 1 REFERENCE.**

## What a 22-Part CRPF would actually be

Roughly 17 Parts restating CO-00/02/04/06/07/08/09 in new vocabulary, plus
~5 Parts of real content. Renaming an existing capability does not make it new —
Colibrì's own Duplicate-to-Advantage section says exactly this (source line ~373:
*"Changing the name of an existing capability does not make it new"*), and its
own D2A map scores Context hygiene as **EXTEND**, Memory hierarchy as **EXTEND**,
Model router as **REFERENCE / CONNECT**, and Predictive loading as
*"NEW CANDIDATE — only if not covered by existing context systems."*

The pillar audited itself correctly. The charter did not carry that verdict
through, because its boundary never enumerated `cognitive_os`.

## Recommendation

Do **not** found CRPF as a 22-Part family. Ship the residue as two CO-family
extensions, which is where the estate's own convention puts it (CO-11 and CO-12
were added the same way, after a reality scan found 7/9 proposals already covered):

- **CO-13 — Degradation Order & Semantic Preservation Contract.** The ordered
  ladder + the NEVER list, as a declared contract consumed by CO-02's governor.
  Absorbs Colibrì #9, #4 (Hard Rule), #3 (doctor contract shape).
- **CO-14 — Value-Weighted Heat & Bounded Predictive Prefetch.** Wires ROI/value
  into CO-06's relevance signal, and reconciles the prefetch conflict explicitly:
  either lift CO-04's III.4 ban under a harmless-failure guardrail, or affirm the
  ban and record why. Absorbs Colibrì #7, #8, #1 (scope axis).

Everything else routes to owners already chartered: #2 → E4, #5 → KSF
Authorized State, #6 → E2, #10/#11 → reference.

Charter impact: CRPF is struck as a NEW family; construction order becomes
**IGEF → E1…E5 → KSF**, with CO-13/CO-14 sequenced against `cognitive_os`.
The charter is sealed and a concurrent pane may be reading it — this file does
not amend it. Amendment is the Owner's call at STOP #2.

## Not asserted

CO-11 (Output Budget Governor) remains GAP-REAL and unbuilt; it is untouched by
this audit. The `omniram-sentinel` module is empty (0 files), so **host** RAM/disk
pressure — as distinct from context-token pressure — is genuinely ungoverned.
That is a real surface, but it is not what the charter assigned CRPF, and it is
not proposed here without Owner direction.
