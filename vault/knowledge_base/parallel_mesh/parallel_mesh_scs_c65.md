# SCS C65 — Parallel-Cognitive-Mesh-by-default

**Sealed:** 2026-07-01. **Mode:** ULTRA-PLAN (architecture only — no code, mirroring SCS C61).
**Parent system:** Cognitive OS (SCS C61 architecture / SCS C62 live code). **Next free SCS:** C66.

## The rule

**Parallel-Cognitive-Mesh-by-default:** N parallel panes of the same repo are **permitted**. What
is forbidden is **duplicated reasoning**. The goal is not fewer panes — it is coordinated panes:
6–10 active with the cognitive cost of 2–3 well-coordinated sessions.

- **Repo Shared Brain (PM-01):** common repo state, generated **once**, consumed by every pane
  before it reasons. Parent CO-04.
- **Pane Intent & Collision (PM-02):** every pane **declares** scope/cost/ROI/model **before**
  executing; the Collision Detector resolves overlap (fuse / split / demote-to-reviewer / reuse)
  before a token is spent. **Recalibrates CO-08's blunt `SAME_REPO_CAP=1`** into a scope-gate.
  Parent CO-08.
- **Shared Findings Bus (PM-03):** discoveries **published**, **consumed before reasoning**; the
  **Redundancy Tax** stops work already done. Absorbs the Reasoning-Dedup mechanism (folding it in,
  rather than duplicating CO-05, is the root law applied to the mesh's own design). Parent CO-05.
- **Parallel Budget Auction (PM-04):** shared budget granted by **ROI, not arrival order**;
  concurrency **modes** Green/Yellow/Red/Black scale spend to aggregate CO-00 pressure; **Opus
  Singleton** keeps ≤1 Opus-heavy pane per repo. Parents CO-01/CO-02/CO-08.
- **Speculative Prefetch (PM-05):** pre-warm **cheap**, **idle-only**, **net-positive** assets
  ahead of predicted need; a wrong guess is bounded cheap waste, never a burn. Parents CO-04/CO-05.

## The CO-08 recalibration (Owner-approved Q-A)

The founding conflict, surfaced at STOP #1 and ruled by the Owner: CO-08's live `scheduler.py`
hard-refuses a 2nd same-repo hot pane because it could not tell duplicated from independent
parallelism. The mesh does not delete that concern — it **replaces the blunt count cap with a
precise scope+budget gate** (PM-02 + PM-04). Undeclared panes keep the blunt cap (fail-safe). The
`scheduler.py` code change is an Owner-authorized follow-up EXECUTION step (backlog).

## Honest guarantee (CO-10 inherited)

Every mesh coordination surface is a **shared file on disk polled at pane boundaries** (launch /
turn-start / close) — **never IPC between Claude instances**. The Brain, the Bus, the declarations,
and the auction are files read at boundaries; the only real cross-process guard is
`intent_lock.js`'s narrow worktree+PID soft-pause. No coordination requiring live pane-to-pane
conversation is claimed anywhere. The latency (a finding published by one pane is seen by another
only at that other's next boundary) is stated, not hidden.

## Done-gate — honest scorecard

- **7/8 strict V-gate PASS + 1 accepted deviation** (V-DEPTH, Owner Q-C: inherit CO-family depth
  ~560–1070 words/Part; full 2500/Part would be the burn the kernel prevents). See
  `PARALLEL_MESH_INDEX.md` V-gates table.
- **V-NO-CODE:** 0 fenced code blocks across PM-01…PM-05 (only the index's family-tree diagram).
- **V-REALITY-SCAN:** no dataset duplicates a CO-0N — 5 NEW with named parents; Reasoning-Dedup
  folded into PM-03, Portfolio Manager dropped as COVERED-by-CO-01, three EXTEND items deferred.
- **V-BASELINE:** zero code changed (only `.md` added); `test_cognitive_os_build.py` 68/68
  unaffected — no regression surface.

## Scope (Owner-approved at STOP #1, 2026-07-01)

- **Q-A → Recalibrate** CO-08 to mesh-gated N panes.
- **Q-B → 5 NEW datasets** (PM-01…PM-05); Cognitive Compiler / Deterministic Replacement /
  Cross-Project Learning / Portfolio Manager deferred → `vault/backlog/2026-07-01_parallel-mesh-deferred.md`.
- **Q-C → Inherit CO-family depth.**

## Lineage

CO-00…CO-10 (Cognitive OS) is the parent economy kernel. The Parallel Mesh (PM-01…PM-05) is the
coordination layer on top: the Cognitive OS governs one session's cost; the Mesh governs many
panes' coordination so parallelism multiplies progress, not burn. C61 = CO architecture, C62 = CO
live code, **C65 = Mesh architecture**. Mesh live code (a `modules/parallel_mesh/`) remains a
deferred follow-up, mirroring the C61→C62 progression.
