# Parallel Cognitive Mesh — Master Index

> An extension of the Cognitive OS (CO-00…CO-10). Where the Cognitive OS governs the *cost*
> of one session, the Parallel Mesh governs the *coordination* of many panes on one repo so
> that concurrency multiplies **progress**, not **burn**.
>
> **Root law:** *Parallel allowed. Duplicate cognition forbidden.* N panes on the same repo are
> permitted; what is forbidden is duplicated reasoning, duplicated context-building, and
> duplicated cost. The goal is not fewer panes — it is coordinated panes: 6–10 active with the
> cognitive cost of 2–3.
>
> **Central metric (inherited from CO-01):** verifiable work finished per unit of compute cost.
> **Honesty rule (inherited from CO-10):** every mesh surface is a **file on disk polled at pane
> boundaries** — never IPC between Claude instances. No coordination is claimed that requires
> live pane-to-pane conversation.
>
> Scope approved by Owner 2026-07-01 (STOP #1): **5 NEW datasets**, the near-COVERED and
> borderline systems **deferred to backlog**, depth **inherited from the CO-family** (Owner Q-C).
> Sealed as **SCS C65**.

---

## Family tree

```
Cognitive OS (CO-00..CO-10)                    ← PARENT SYSTEM (must exist)
│
└── Parallel Cognitive Mesh (PM-01..PM-05)     ← this family (extension)
    │
    ├── STATE
    │   └── PM-01  Repo Shared Brain            (parent CO-04) — generated once, consumed by all
    │
    ├── COORDINATION
    │   ├── PM-02  Pane Intent & Collision      (parent CO-08) — RECALIBRATES the same-repo cap
    │   └── PM-03  Shared Findings Bus          (parent CO-05) — publish/consume + Redundancy Tax
    │
    ├── ECONOMICS
    │   └── PM-04  Parallel Budget Auction      (parents CO-01/02/08) — ROI + modes + Opus Singleton
    │
    └── ACCELERATION
        └── PM-05  Speculative Prefetch         (parents CO-04/05) — cheap/idle/net-positive only
```

## Dependency graph (consumer → provider)

- **PM-01** consumes CO-04 (Warm store) + CO-05 (freshness) + CO-06 (eviction); provides the
  shared repo state to PM-02 (active plans) and PM-03 (recent-findings pointer).
- **PM-02** consumes CO-08 (cap + detectors), `intent_lock.js` (soft cross-process pause), and
  PM-01 (active plans); provides scope-gated admission to the mesh and cost/ROI/model bids to PM-04.
- **PM-03** consumes CO-05 (asset store) + CO-06 (eviction) + the `cross_signal_bus` transport
  pattern; provides the consume-before-reason gate + Redundancy Tax to PM-02 (Reuse resolution).
- **PM-04** consumes CO-01 (ROI/WU) + CO-02 (governor) + CO-08 (Opus/model axis) + CO-00 (bands →
  modes) + PM-02 (bids); provides budget grants and concurrency modes to every pane.
- **PM-05** consumes CO-04 (Warm) + CO-05 (assets) + CO-03 (cheap rungs) + PM-01/PM-02 (prediction
  signal) + PM-04 (Green-only gate); provides pre-warmed cheap assets. Weakest guarantee by design.

## EXTEND vs NEW vs COVERED (vs Cognitive OS)

| ID | Dataset | Verdict | Parent / reuse |
|---|---|---|---|
| PM-01 | Repo Shared Brain | **NEW** | CO-04 Context Virtual Memory (Warm store); CO-05 freshness pattern |
| PM-02 | Pane Intent & Collision Detector | **NEW** | CO-08 detectors + `harness/intent_lock.js` |
| PM-03 | Shared Findings Bus (+ Redundancy Tax) | **NEW** | CO-05 asset registry + `autoresearch/cross_signal_bus.py` transport |
| PM-04 | Parallel Budget Auction & Concurrency Modes | **NEW** | CO-01 ROI + CO-02 governor + CO-08 same-repo (model axis) |
| PM-05 | Speculative Prefetch Engine | **NEW** | CO-04 Warm + CO-05 assets + CO-03 cheap rungs |
| — | Reasoning Deduplication Engine | **FOLDED into PM-03** | would duplicate CO-05; absorbed as the consume-before-reason gate |
| — | Cognitive Portfolio Manager | **COVERED by CO-01** | CO-01 *is* Cognitive Capital + ROI (INDEX line 86); cross-pane mechanic kept in PM-04 |
| — | Cognitive Compiler | **DEFERRED (EXTEND CO-03 + one_shot)** | `one_shot/compiler.py` + CO-03 + spec_gate already compile |
| — | Deterministic Replacement Engine | **DEFERRED (EXTEND CO-03)** | CO-03 cascade already has a "deterministic" rung |
| — | Cross Project Learning Network | **DEFERRED (PM-06 candidate)** | vault + CEPS + `cross_project_dedup` + `cross_signal_bus` xkw |

Deferred set → `vault/backlog/2026-07-01_parallel-mesh-deferred.md`.

## The CO-08 recalibration (headline, Owner-approved Q-A 2026-07-01)

CO-08's live `scheduler.py` enforces `SAME_REPO_CAP=1` (no bypass, tested 68/68) because it could
not distinguish duplicated from independent same-repo parallelism. PM-02 supplies that missing
sense (declared scope) and PM-04 bounds the spend, so the blunt count cap is **recalibrated** to:
*N same-repo panes admitted when declared scopes are disjoint AND the aggregate stays under the
CO-00/CO-02 envelope.* Fail-safe: an **undeclared** pane still gets the original blunt cap. The
live `scheduler.py` semantics change (relax same-repo cap on a passing scope-check) is the
**Owner-authorized follow-up build** these datasets specify — the datasets are the architecture;
the code change is the next EXECUTION-mode step.

## V-gates (FASE 4 done-gate) — honest scorecard

| Gate | Status | Evidence |
|---|---|---|
| V-REALITY-SCAN (no dataset duplicates a CO-0N) | ✅ PASS | 5 NEW named parents; Reasoning-Dedup folded, Portfolio dropped as COVERED, 3 EXTEND deferred |
| V-PARALLEL-ALLOWED (N same-repo panes, no blunt cap) | ✅ PASS | PM-02 recalibration contract (§I.3) + PM-04 §II.3 |
| V-DEDUP-FORBIDDEN (concrete duplicate-cognition prevention) | ✅ PASS | PM-02 Collision Detector (4 resolutions) + PM-03 Redundancy Tax + consume-before-reason gate |
| V-HONEST-IPC (Findings Bus = shared disk, not magic) | ✅ PASS | Honest-IPC clause in all 5 datasets + this index's honesty rule |
| V-NO-CODE (zero code in datasets) | ✅ PASS | measured: 0 fenced code blocks across PM-01..PM-05 (only this index's family tree) |
| V-PARENT-REFS (each dataset declares its CO-0N parent) | ✅ PASS | every dataset's blockquote + contract table names its parent |
| V-BASELINE (pytest no regression) | ✅ PASS | zero code changed — only .md added; `test_cognitive_os_build.py` 68/68 unaffected |
| V-DEPTH (≥2500 words/Part) | ⚠️ ACCEPTED DEVIATION (Owner Q-C 2026-07-01) | inherits the CO-family depth (~560–1070 words/Part); full expansion would be the burn the kernel prevents |

**7/8 strict PASS + 1 accepted deviation (V-DEPTH, Owner-ruled).** Consistent with the CO-family's
own sealed depth ruling (2026-06-30). Honest per the "no classified FAILs at done-gate" doctrine.

## Build status

| Dataset | Status | Parent |
|---|---|---|
| PM-01 Repo Shared Brain | ✅ written | CO-04 |
| PM-02 Pane Intent & Collision | ✅ written | CO-08 |
| PM-03 Shared Findings Bus | ✅ written | CO-05 |
| PM-04 Parallel Budget Auction | ✅ written | CO-01/02/08 |
| PM-05 Speculative Prefetch | ✅ written | CO-04/05 |
| SCS C65 seal | ✅ sealed (`parallel_mesh_scs_c65.md`) | — |

## The fundamental property of the whole system

> **Parallel allowed. Duplicate cognition forbidden.** Repo Shared Brain: common state, generated
> once. Findings Bus: discoveries published, consumed before reasoning. Collision Detector:
> overlap detected before execution. Redundancy Tax: work already done is blocked from repetition.
> Budget Auction: spend follows ROI, not arrival order. All of it is shared files on disk polled at
> pane boundaries — no IPC claimed, no magic promised.
