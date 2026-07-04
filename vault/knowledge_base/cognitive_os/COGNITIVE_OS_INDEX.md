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

| Dataset | Status | Words |
|---|---|---|
| CO-00 Hard Context Budget Contract | ✅ written | 3218 |
| CO-01 Operating Economics | ✅ written | 2186 |
| CO-02 Economics Governor | ✅ written | 1768 |
| CO-03 Dynamic Cognitive Router | ✅ written | 1835 |
| CO-04 Context Virtual Memory | ✅ written | 1739 |
| CO-05 Zero Token Layer | ✅ written | 1696 |
| CO-06 Cognitive Garbage Collector | ✅ written | 1675 |
| CO-07 Session Hibernation | ✅ written | 1727 |
| CO-08 Parallel Session Scheduler | ✅ written | 1880 |
| CO-09 Loop & Subagent Economics | ✅ written | 1765 |
| CO-10 Enforcement Guarantee Ledger | ✅ written | 1916 |
| **Total** | **11/11 written** | **22191** |
| SCS C61 seal | ✅ sealed (`cognitive_os_scs_c61.md`) | — |

## Live implementation (SCS C62 — built 2026-06-30)

The architecture (SCS C61) is now **live code**, built in bounded waves, each tested +
committed + pushed (REMOTE_DELTA 0 0). `tools/test_cognitive_os_build.py` = **68/68
done-gates**, hermetic (re-runnable). Module = `modules/cognitive_os/`.

| Dataset | Module | What is live | Honest level (CO-10) |
|---|---|---|---|
| CO-08 | `scheduler.py` | hard hot-session cap; refuses over-cap NEW pane in kclaude | WRAPPER (rung-3 block) |
| CO-01 | `economics.py` | WU/MTok, ledger fed by real gate verdicts | HOOK (measure) |
| CO-09 | `loop_budget.py` | 7-part loop admission + kill switch + subagent routing | WRAPPER + iter-boundary |
| CO-00 | `context.py` | effective-context estimate + bands; resume advisory | WRAPPER block + HOOK warn |
| CO-03 | `router.py` | Vault→asset→deterministic→Haiku→Sonnet→Opus cascade (active) | HOOK (selection) |
| CO-05 | `registry.py` | verified-only asset registry w/ freshness; CO-03 rung-1/2 | HOOK (retrieval) |
| CO-02 | `governor.py` | nested envelope, DOWNGRADE-over-REFUSE, violation registry | WRAPPER block/downgrade |
| CO-04 | `memory.py` | HOT/WARM/COLD/EXTERNAL tiers, lossless demotion | HOOK (load discipline) |
| CO-06 | `gc.py` | eviction policy (recency/relevance/aging); never `.jsonl` | HOOK (hygiene) |
| CO-07 | `hibernation.py` | freeze/compress/store-then-destroy/restore (G4 verdict) | WRAPPER (durability) |
| CO-10 | `guarantee_ledger.py` | 5-level ladder + inflation audit + un-gated detector | classification layer |

**Wired live in `kclaude.ps1` (mirrored to `~/.claude/bin`):** CO-08 cap refusal (rung-3
block, no bypass) + CO-00 resume advisory (rung-2). All Python lives at the repo skills
path, so it is active the moment it is saved. Commits `e8279d2`→`06df80f`.

**Honest residuals (CO-10, never hidden):** enforcement is rung-3 = kclaude-launched only
(a bare `claude` escapes — `un_gated_sessions` flags it); WU ledger sparse → low-confidence
until gates accrue; `cost_gate.weekly_burn` 13.6s deferred (`vault/backlog/2026-06-30_costgate-weeklyburn-slow.md`);
CO-05 Vault/asset rungs miss on an empty registry (cascade falls to a model, today's behavior).

## V-gates (FASE 4 done-gate) — honest scorecard

| Gate | Status | Evidence |
|---|---|---|
| V-REALITY-SCAN (no dataset duplicates a PP module) | ✅ PASS | EXTEND/NEW/COVERED table; 8 EXTEND named parents, 3 NEW genuine gaps |
| V-60-PERCENT-CONTRACT (projective kill switch, not reactive) | ✅ PASS | CO-00 Part I.3 + II.3 (wrapper-maximal block) |
| V-HONEST-GUARANTEE-LEVELS (every mechanism classified) | ✅ PASS | CO-10 5-level ladder + per-mechanism table |
| V-METRIC-UNIFIED (WU/MTok tied to Production Reality Gate, not parallel) | ✅ PASS | CO-01 Part II.1 (Work Unit = Reality-Gate-certified) |
| V-NO-CODE (zero code in any dataset) | ✅ PASS | measured: 0 fenced code blocks across all 11 |
| V-ROLLBACK-PROTOCOLS (each dataset has rollback) | ✅ PASS | Part III rollback section in all 11 |
| V-INVESTIGATION-PROTOCOL (60% breach → mandatory RCA) | ✅ PASS | CO-00 III.1 + CO-02 II.2 |
| V-INTEGRATION (/loop /compact /kclear /clear + Cursor) | ✅ PASS | integration-contract section in all 11 |
| V-BASELINE (pytest no regression) | ✅ PASS (vacuous) | zero code changed — only .md added; no regression surface |
| V-DEPTH (≥2500 words/Part) | ⚠️ ACCEPTED DEVIATION (Owner-ruled 2026-06-30) | datasets 1675–3218 words total (~560–1070/Part); architecturally complete + zero-padding, below a literal 2500/Part. Owner ruled accept+seal; full expansion deferred to backlog `vault/backlog/2026-07-06_cognitive-os-vdepth-expansion.md`. |

**9/10 strict PASS + 1 accepted deviation (V-DEPTH).** Sealed as **SCS C61** at current depth
per the Owner ruling (2026-06-30): expanding to 2500/Part (~+60k words) would itself be the
low-WU/MTok burn the kernel exists to prevent. The full expansion is deferred — not dropped —
to the backlog for the week of 2026-07-06. Honest per the "no classified FAILs at done-gate"
doctrine: a waived deviation with an Owner decision and a scheduled follow-up.

---

## CO-NextGen extension — CO-12 (SCS C74, 2026-07-04)

The sealed family above is CO-00..CO-10 (SCS C61/C62); this section records later single-dataset
extensions that take the next free CO ids. The CO-NextGen Reality Scan
(`vault/plans/co-nextgen-datasets-2026-07-04.md`) found 7/9 proposed systems already COVERED,
Loop-Compression COVERED by CO-09, and **two genuine gaps** (CO-11 Output Budget Governor, CO-12
Cognitive Readiness Telemetry). Owner approved **CO-12 first** (measure-before-more-building).
CO-09/CO-10 are never reused.

| ID | Dataset | Verdict | Parent / reuse | Status |
|---|---|---|---|---|
| CO-11 | Output Budget Governor | **GAP-REAL** (approved, deferred) | `output_contracts` (quality→+economy) + CO-01 + CO-08/CO-09 | not built (Owner chose CO-12 first) |
| CO-12 | [Cognitive Readiness Telemetry](cognitive_os_12_cognitive_readiness_telemetry.md) | **GAP-REAL** | C68/C69/C70 audit family + CO-01 WU/MTok + GK-09 observatory | ✅ written |

**CO-12 in one line:** the *adoption axis* — a Cognitive Readiness Score (adoption rate over eligible
opportunities, per lever/cohort) that ties to CO-01 WU/MTok, plus the **Telemetry-Before-Claims
Contract** (no saving claim without a `(metric, source, value)` triple; else it is a hypothesis).
Metrics name their data source and read *unknown* when the instrument is pending — never a faked 0/100.

**CO-12 V-gates (`tools/test_co12_readiness_telemetry.py`, hermetic ×3):** V-REALITY-SCAN (declares
COVERED set + real parents), V-CORRECT-IDS (never claims CO-09/CO-10), V-TELEMETRY-REAL (every metric
names a concrete data source), V-PARENT-REFS, V-NO-CODE (0 code fences), V-CONTRACT (Telemetry-Before-
Claims present), V-NO-REGRESSION (C68/C69/C70 suites still green). V-DEPTH inherits the CO-family
Owner ruling (~600–1100 words/Part, architecturally complete, zero-padding).
