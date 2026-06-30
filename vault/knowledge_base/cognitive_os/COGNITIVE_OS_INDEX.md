# Cognitive Operating System — Master Index

> The PP's cognitive economy kernel. Turns scattered, reactive, advisory cost/context/
> session mechanisms into a unified economy governed by one root law.
>
> **Root law (CO-00):** effective context of any session never exceeds **60%** —
> projective, not reactive; defended from the **45–55% action band**.
> **Central metric (all datasets):** *verifiable work finished per unit of compute
> cost* (time + tokens + RAM + risk), never "tokens used".
> **Honesty rule (CO-10):** every enforcement surface is classified by the guarantee it
> can actually provide — Prompt-only → Claude-Code-hook → Wrapper → Cursor-ext →
> Host-limited. No theater.
>
> Sealed as **SCS C61**. Owner-approved scope 2026-06-30: 11 datasets, 8 EXTEND / 3 NEW,
> CO-00 framed as layered guarantee with the wrapper surface pushed maximally hard.

---

## Family tree

```
CO-00  Hard Context Budget Contract            ← ROOT LAW (inherited by all)
│
├── ECONOMY
│   ├── CO-01  Operating Economics & Cognitive Capital   (Work-Units / M-Tokens metric)
│   └── CO-02  Economics Governor & Budget Violation Registry
│
├── ROUTING
│   └── CO-03  Dynamic Cognitive Router   (Vault→asset→deterministic→Haiku→Sonnet→Opus)
│
├── MEMORY & ASSETS
│   ├── CO-04  Context Virtual Memory      (Hot / Warm / Cold / External)
│   ├── CO-05  Zero Token Layer & Cognitive Asset Registry  (+ Vault Router, Cache)
│   └── CO-06  Cognitive Garbage Collector (hygiene / eviction)
│
├── SESSION & PARALLELISM
│   ├── CO-07  Session Hibernation & Dedup  (freeze / serialize / compress / restore)
│   └── CO-08  Parallel Session Scheduler & Swarm Optimizer  (HARD hot-session cap)
│
├── LOOP & SUBAGENT
│   └── CO-09  Loop & Subagent Economics
│
└── HONESTY / ENFORCEMENT
    └── CO-10  Enforcement Guarantee Ledger  (External Automation Control Plane)
```

## Dependency graph (consumer → provider)

- **CO-00** consumes: CO-01 (cost ledger + projection calibration), CO-08 (parallel
  envelope), CO-09 (loop/subagent projections). Provides: the ceiling law + admission
  projection to **all**.
- **CO-01** provides the unified cost model + Work-Units metric to CO-00, CO-02, CO-03,
  CO-09. Consumes: `token_ground_truth`, Production Reality Gate (done-gates).
- **CO-02** consumes CO-01; provides breach/violation governance to CO-00, CO-10.
- **CO-03** consumes CO-01 (cost) + CO-04/CO-05 (can this be answered without a model?);
  provides routing decisions to every model-using operation.
- **CO-04** consumes CO-05 (assets) + CO-06 (eviction); provides tiered memory to CO-00
  (context estimate) and CO-03.
- **CO-05** provides reusable assets to CO-03, CO-04, and records every CO-00 breach RCA.
- **CO-06** consumes CO-00 bands + CO-04 tiers; provides eviction to CO-00.
- **CO-07** consumes CO-00 (when to hibernate); provides freeze/restore to CO-08.
- **CO-08** consumes CO-00 (envelope) + CO-07 (hibernation); provides the hard parallel
  cap. Root cause of the 48h burn lives here.
- **CO-09** consumes CO-00 (admission) + CO-01 (cost); provides loop/subagent budgets.
- **CO-10** consumes every dataset's guarantee claims; provides the honest classification
  + the un-gated-path flags. Cross-cutting.

## EXTEND vs NEW vs COVERED

| ID | Dataset | Verdict | Parent / reuse |
|---|---|---|---|
| CO-00 | Hard Context Budget Contract | NEW root (EXTEND) | `context-watchdog.py`, `context_monitor.py`, wrapper prelaunch |
| CO-01 | Operating Economics & Cognitive Capital | EXTEND | `token_ground_truth.py`, `cost_gate.py`, Reality Gate |
| CO-02 | Economics Governor & Violation Registry | EXTEND | `cost_gate.weekly_burn` (W5) |
| CO-03 | Dynamic Cognitive Router | EXTEND | `spec_gate.classify_tier`, `cost_collapse.route` |
| CO-04 | Context Virtual Memory | NEW (EXTEND base) | `jit_skill_loader.py` (proto Hot/Warm) |
| CO-05 | Zero Token Layer & Asset Registry | EXTEND | `vault/knowledge_base/`, `audit_cache` |
| CO-06 | Cognitive Garbage Collector | EXTEND | `auto_reset_orchestrator.py` |
| CO-07 | Session Hibernation & Dedup | EXTEND | `snapshot_versioning.py`, `restore_guard.js` |
| CO-08 | Parallel Session Scheduler & Swarm | NEW | `repo_coordinator.py` W4 (advisory→cap) |
| CO-09 | Loop & Subagent Economics | NEW | — (/loop unbounded today) |
| CO-10 | Enforcement Guarantee Ledger | NEW cross-cutting | prelaunch, restore_guard (document) |
| — | Session Dedup | COVERED | `restore_guard.js` (reused in CO-07) |
| — | Production Reality Gate | COVERED | done-gates (reused in CO-01) |
| — | Token visibility | COVERED | SCS C53 (reused in CO-01) |
| — | Context Futures Market / ROI Scoring | SKIP-LOW-ROI | folded as a section in CO-01 |

## Build status

| Dataset | Status |
|---|---|
| CO-00 | ✅ written |
| CO-01 … CO-10 | ⏳ pending (waves 2–6) |
| V-gates 10/10 ×3 | ⏳ pending (FASE 4) |
| SCS C61 seal | ⏳ pending |

## V-gates (FASE 4 done-gate, 10/10 ×3 hermetic)

V-REALITY-SCAN · V-60-PERCENT-CONTRACT · V-HONEST-GUARANTEE-LEVELS · V-METRIC-UNIFIED ·
V-DEPTH (≥2500 words/Part) · V-NO-CODE · V-ROLLBACK-PROTOCOLS · V-INVESTIGATION-PROTOCOL ·
V-INTEGRATION (/loop /compact /kclear /clear + Cursor) · V-BASELINE (pytest no regression).
