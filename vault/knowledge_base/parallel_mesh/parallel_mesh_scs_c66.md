# SCS C66 — Parallel-Mesh-Active

**Sealed:** 2026-07-01. **Mode:** EXECUTION (faithful implementation of the SCS C65
architecture). **Successor to:** SCS C65 (the Parallel Mesh architecture family).
**Parent economy:** Cognitive OS (SCS C61 arch / SCS C62 live). **Next free SCS:** C67.
**Commits:** `092585e` PM-02, `6321a92` PM-03, `16637ef` PM-01, `bfd844c` PM-04,
`<this>` PM-05 + seal. REMOTE_DELTA 0 0 throughout.

## What was sealed

The 5 Parallel Mesh datasets (SCS C65, architecture) are now **live, tested code**
under `modules/parallel_mesh/`, built in five bounded anti-burn sprints (each tested +
committed + pushed — practicing the kernel's own thesis, not one mega-turn).

| Dataset | Module | Live behavior | Honest level (CO-10) |
|---|---|---|---|
| PM-02 | `pm_02_intent.py` | scope-gate recalibrates CO-08: declared panes admitted by non-overlap; undeclared keep the blunt `SAME_REPO_CAP=1` | WRAPPER (advisory) + sealed fail-safe |
| PM-03 | `pm_03_bus.py` | append-only JSONL bus; `reason_or_reuse` returns a hit for 0 new tokens; identity dedup | HOOK (consult-before-reason) |
| PM-01 | `pm_01_brain.py` | repo briefing generated once, consumed by all; stale on new HEAD or TTL | WARM-tier cache (CO-04) |
| PM-04 | `pm_04_auction.py` | Green/Yellow/Red/Black from real `cost_gate` burn; Opus Singleton; ROI auction | HOOK advisory (never blocks) |
| PM-05 | `pm_05_prefetch.py` | cheap-only + idle-only + net-positive-gated speculative prefetch | rung-1/2 (weakest by design) |

## The recalibration (Owner-approved, delivered)

CO-08's live `scheduler.decide()` was **extended, not replaced**: two optional params
(`declared`, `hot_scopes`). `declared=None` reproduces the exact sealed C62 behavior
(68/68 preserved). A declared pane whose scope does not collide with same-repo
incumbents is admitted — N same-repo panes, gated by scope instead of a blunt count.
Undeclared panes keep `SAME_REPO_CAP=1`. This is the founding promise made real:
*parallel allowed, duplicate cognition forbidden.*

## Done-gate — empirical, honest

- `tools/test_parallel_mesh.py` = **26/26 PASS, hermetic (verified 3× re-runnable,
  exit 0 each)**: 6 PM-02 + 5 PM-03 + 4 PM-01(+coexistence) + 6 PM-04 + 5 PM-05.
- `tools/test_cognitive_os_build.py` = **68/68** unchanged — the sealed CO-family has
  no regression (scheduler extended backward-compatibly, verified every sprint).
- **V-NO-CODE** applies to datasets only; the modules are code by design (this is the
  C62-style live-code seal, not an architecture seal).

## CONTRATO DE REALIDAD — 5/5

1. `scheduler.decide()` admits 2+ same-repo panes when they declare disjoint scope;
   undeclared → blunt cap (V-PM02-INTENT-ALLOWED + V-SCHEDULER-FAILSAFE).
2. A pane consulting the bus on a known topic reuses the finding for 0 new tokens —
   `reason_fn` never runs (V-PM03-REDUNDANCY-TAX).
3. 3 panes on one repo trigger exactly 1 repo scan; the other 2 consume the brain
   (V-PM01-BRAIN-GENERATED-ONCE).
4. The concurrency mode is derived from `cost_gate`'s REAL burn, silent on no data,
   never a fabricated number (V-PM04-READS-REAL-BURN).
5. Prefetch runs ONLY green+idle+cheap+net-positive; a hot pane → fail-stop
   (V-PM05-IDLE-ONLY + V-PM05-RUNS-WHEN-IDLE).

## Honest residuals (CO-10 — surfaced, never hidden)

- **Collision is exact path-token intersection** — dir-vs-file prefix overlap not caught
  (`vault/lessons/parallel-mesh-ukdl.md` T-PARALLEL-MESH-COLLISION-PREFIX-001). Declare
  at file granularity.
- **All gates are advisory** — PM-02 scope-gate refuses at the wrapper boundary, but
  PM-03/04 are HOOK-level; a pane that never consults the bus/brain is not covered
  (flagged like CO-08's un-gated pane, never silently claimed governed).
- **Hub wiring is Owner-side** — the SessionStart/Stop shell-outs are documented in
  `modules/parallel_mesh/hub_wiring_instructions.md`, not auto-edited into the live
  hook (HR-001). Until wired, the modules are invocable but not auto-injected.
- **"Idle" is a coarse proxy** (no hot session in the window) — a pane could activate
  the next second; bounded by cheap-only + net-positive so a wrong read is cheap waste.

## Lineage

C61 = CO architecture, C62 = CO live code, C65 = Mesh architecture, **C66 = Mesh live
code**. The mesh is the coordination layer over the Cognitive OS economy: CO governs
one session's cost; the mesh coordinates N panes so parallelism multiplies progress,
not burn. Next free SCS = **C67**.
