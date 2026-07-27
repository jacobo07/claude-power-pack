---
title: CRPF Option A — Repair Wiring: per-module disposition
date: 2026-07-27
status: COMPLETE (Option A). Option B' (CO-13 / CO-14) not started.
decision: Owner ruled "A luego B'" — no CRPF family, no 22 doctrinal Parts, no standalone
  reconciliation family. Residency residue ships inside cognitive_os.
audit: vault/plans/crpf-2026-07-27.md (STOP #1)
instrument_commit: a91328c
---

# Option A — Repair Wiring

Thirteen residency modules were reported WIRED-BUT-SILENT. This file records, per module,
why it was silent, who should invoke it, and what blocks activation — with evidence.

## Headline: the instrument was wrong before the modules were

Ten enabled scheduled tasks run PP scripts on a timer. `reachability.py` scanned hooks,
commands, agents, `CLAUDE.md` and `SKILL.md` — never the Task Scheduler. Its own
`SCHEDULED` exemption class existed because someone knew this, and the workaround was
hand-declaration: `PR-COVERAGE-BY-CONSTRUCTION-001` reproduced *inside the instrument
built to end it*. Seventh measured instance.

Repaired in `a91328c` (`scheduled_task_seeds`, locale-independent XML, enabled-only,
fail-open, both test poles). **Measured: REACHABLE 171 → 180, zero regressions.**

A second real bug surfaced with it: `live_seeds` merged the live install's ~110 hooks,
commands and agents into a scan of *any* root, so three of this module's own V-gates had
been failing silently since the hook-registration filter landed. Verified pre-existing by
executing the committed copy at HEAD. Production output is unchanged; the suite went
8/11 → **11/11, hermetic ×3**.

## Per-module disposition

| # | Module | Why SILENT | Who should invoke it | Blocker | Verdict |
|---|---|---|---|---|---|
| 1 | `cognitive_os/hibernate_runner` | instrument blind to the Task Scheduler | task **PP-Hibernation** → `hibernation_daemon.ps1` → `tools/run_hibernation.py` | none — it was never silent | **LIVE** (was misclassified PLANNED) |
| 2 | `cognitive_os/context` | not composed into any live authority | `process_governor.py` (LIVE) — the CO-00 band estimate belongs beside its session-age advisory | composition is an architecture decision: which authority owns the ceiling, and at which rung it may block | **PLANNED** — owner: CO-00 composition |
| 3 | `cognitive_os/governor` | same | `process_governor.py` — DOWNGRADE-over-REFUSE is an envelope verdict | needs #2 first: a governor with no ceiling reading has nothing to govern | **PLANNED** — blocked on #2 |
| 4 | `cognitive_os/economics` | same | `co_12_telemetry` (LIVE) — CO-12's own index says its readiness score ties to CO-01 WU/MTok | the WU ledger is sparse until gates accrue; wiring it now yields a low-confidence metric that reads as fact | **PLANNED** — owner: CO-01 ledger density |
| 5 | `cognitive_os/loop_budget` | same | the `/loop` iteration boundary | no live surface owns that boundary today | **PLANNED** |
| 6 | `cognitive_os/guarantee_ledger` | same | a reporting surface (`/liveness`-adjacent) | classification is only useful beside claims to classify — needs #4 | **PLANNED** — blocked on #4 |
| 7 | `cognitive_os/memory` | same | `tools/jit_skill_loader.py` (LIVE) — CO-04's own docstring calls itself an EXTEND of it | see the seam below: the loader already does this work under its own names | **PLANNED** — owner: CO-04 adapter |
| 8 | `cognitive_os/gc` | same | `memory.py` — CO-04 is the mechanism, CO-06 the policy | needs #7; eviction with no tier inventory has nothing to score | **PLANNED** — blocked on #7 |
| 9 | `cognitive_os/rehydration` | invoked by hand, not by code | the rehydrate path in `hibernate_runner`; today only `vault/patches/hibernation/INSTALL.md` §4 names it, as an Owner-run identity gate | verified: `kclaude.ps1` does not reference it | **PLANNED** — owner: rehydrate-path composition |
| 10-13 | `parallel_mesh/pm_01_brain`, `pm_02_intent`, `pm_04_auction`, `pm_05_prefetch` | no mesh runtime | a mesh driver | `pm_03_bus` is LIVE only because `cdio/bus_bridge` reuses it **as a store**; nothing runs the mesh itself. Prefetch (PM-05) additionally requires PM-04's pressure mode and PM-02's intent declaration, neither of which has a producer | **PLANNED** — owner: mesh runtime decision |

**One of thirteen was a measurement error. Twelve are honest, blocked, dependency-ordered
debt** — and the order matters: #2→#3, #4→#6, #7→#8. Wiring any of them alone produces a
consumer with no producer, which is the defect this pass exists to remove, not add.

## R3 — the premise was wrong, in a useful way

STOP #1 recorded: *"`eviction_score` reads `last_ref_turn` and `hot_since_turn`; no surface
writes them."* Half right. The **observations are written continuously in production**:

- `tools/jit_skill_loader.py` `_telemetry()` → `vault/telemetry/jit_usage_<sid>.jsonl`.
  Measured: **384 files, 339,197 bytes**, newest written today. Each row carries
  `{module, tier, bytes, budget, ts, session_id}`.
- `_save_state()` → `~/.claude/state/jit-injected-<sid>.json`, **495 files**, the
  per-session resident set, with `if m in state: continue` as a live residency check.

`tier` is CO-04's `depth`. `bytes` is `size_tokens`. `ts` is `last_ref_turn`. The resident
set is the working set. **The producer exists and runs on every prompt; it simply does not
know CO-06 exists.** What is missing is an adapter between two vocabularies for the same
physics — not an instrument.

This is CLAE's own thesis applied to itself: the residual was already computed and
discarded. Recorded, not built — an adapter feeding a `gc` that no live surface calls
would be a write with no reader, the opposite orphan. It belongs in Option B', where it
turns R4 from `HYPOTHESIS` into a measurable claim over data already on disk.

## /liveness before and after

| | before | after |
|---|---|---|
| REACHABLE | 171 | **180** |
| standing debt (`known_orphans`) | 10 | **9** |
| hand-written exemptions | 134 | **126** |
| `test_reachability.py` | 8/11 | **11/11** ×3 |

Eight exemptions were deleted rather than added: seven `sqi` modules had been hand-declared
`SCHEDULED` (someone knew, and wrote it down instead of measuring it) and are now *proven*
reachable, so the declarations are gone and the gate is re-armed for them.

## Out of scope, reported not absorbed

`dataset_first/transduction` and `decision_review/epistemic_algebra` are gate offenders and
were offenders before this pass. Both are CPCSC Tier-B modules with test-only consumers —
the same PLANNED class as the CO-0x set. They are not residency modules; disposition is the
Owner's call.

## IGEF

`PENDING_AUDIT`. Admitted by the same asserted-absence standard as CRPF, in the same
document, against the same recalled denominator. Not started. The PASO −1 sweep must run
first, with a denominator discovered from `modules/` and `vault/knowledge_base/` rather
than recalled — including `cognitive_os`, DAIF and Parallel Mesh.
