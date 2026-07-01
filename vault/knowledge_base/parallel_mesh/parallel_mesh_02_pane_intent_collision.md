# Parallel Mesh — PM-02 — Pane Intent Declaration & Collision Detector

> The dataset that makes the mesh's founding promise enforceable. CO-08 today refuses a
> second hot pane on the same repo (`SAME_REPO_CAP=1`, no bypass) because it could not tell
> *duplicated* parallel work from *independent* parallel work — so it blocked both. PM-02
> gives the kernel that missing sense: every pane **declares its intent before it executes**,
> and a Collision Detector reads those declarations to distinguish overlap from independence.
> With that sense, the blunt cap is replaced by a precise one — **N same-repo panes allowed
> when their declared scopes do not collide.** This is the *recalibration of CO-08*, not a
> new silo: parallel allowed, duplicate cognition forbidden.
>
> EXTEND, not NEW: builds on CO-08's detectors (`repo_coordinator.coordinate` /
> `parallel_burn`) and the `harness/intent_lock.js` concurrency lock (worktree+PID+ts).
> PM-02 upgrades detection from *size-and-time* ("two big prompts close together") to
> *declared-scope* ("these two panes both intend to edit `router.py`"). Honest (CO-10):
> declarations are **files on disk read at pane boundaries**, not a cross-instance lock server.

---

## Part I — The Intent Declaration

### I.1 What a pane declares, before it acts

Before a pane executes a substantial prompt, it emits an **intent declaration** — a small,
structured record read by every other pane's Collision Detector. It states, at minimum:

- **Objective** — the one-line goal of this unit of work.
- **Scope** — the files, directories, or modules this pane intends to touch.
- **Mode** — EXECUTION vs ULTRA-PLAN vs review/index (the concurrency-mode axis of PM-04).
- **Expected cost** — the projected output-token / Work-Unit spend (feeds CO-00/CO-02).
- **Expected ROI** — the value class of the work (feeds PM-04's auction).
- **Requested model** — the model the pane wants (arbitrated by CO-03 / PM-04's Opus Singleton).
- **Dependencies** — the plans, findings, or other panes this work waits on.

The declaration is cheap to write and cheap to read — it is the *contract* a pane offers the
mesh, the same way a One-Shot contract (`compile_contract`) states scope + done-gate before
an L/XL task. It is not a plan; it is the *header* of a plan, sized for other panes to scan.

### I.2 Why declaration precedes execution

The ordering is the whole point. CO-08's blunt cap fires at *launch* because that is the only
moment it has information; it has no view of *what* the new pane will do, so it must assume the
worst (a same-repo re-derivation) and block. A declaration moves the decision from "how many
panes" to "what will each pane do" — the axis on which duplication actually lives. Two panes on
the same repo editing disjoint subsystems are high-value parallelism; two panes both rebuilding
the same subsystem's context are the 48h burn. Only a declared scope separates them, and only a
declaration *before* execution lets the mesh act before the tokens are spent rather than after.

### I.3 The CO-08 recalibration contract (Owner-approved 2026-07-01)

PM-02 replaces CO-08's `SAME_REPO_CAP=1` blunt refusal with a **scope-gated admission**:

- A new same-repo hot pane is **admitted** when its declared scope does **not** collide with
  any active pane's declared scope, **and** the aggregate projection stays within the
  CO-00/CO-02 envelope (the summed-envelope check CO-08 already enforces is retained).
- A new same-repo pane whose scope **collides** is not silently blocked — it is routed to a
  **resolution** (Part II): fuse, split, demote-to-reviewer, or reuse.
- **Fail-safe to the blunt cap:** a pane that provides **no declaration** cannot be
  scope-checked, so CO-08's original `SAME_REPO_CAP=1` applies to it unchanged. The mesh only
  relaxes the cap in exchange for a declaration; an undeclared pane gets exactly today's
  refusal. This makes the recalibration strictly safe — it can only *widen* admission for
  panes that give the kernel enough information to prove non-overlap.

The global `HOT_CAP` and the summed-envelope ceiling are **unchanged**; only the same-repo
dimension is refined from count to scope. The "no bypass, only satisfaction" property of the
cap survives: a colliding pane is satisfied by resolution, never by a silencing flag.

---

## Part II — The Collision Detector and its resolutions

### II.1 Detecting collision by declared scope

The Collision Detector reads the active declarations (from the Repo Shared Brain's active-plans
section, PM-01, and the on-disk declaration files) and computes scope overlap: shared files,
shared modules, or a declared dependency that names another pane's in-flight output. Overlap is
graded — **hard** (both intend to *write* the same file), **soft** (one writes, one reads the
same file → a producer/consumer ordering, not a true conflict), **none** (disjoint scopes). This
is a strict upgrade over `parallel_burn`, which can only see that two prompts are large and
recent, not *what* they touch. The detector runs at the honest boundaries — launch and
turn-start — the same points PM-01 checks freshness.

### II.2 The four resolutions

On a **hard** collision, the mesh does not block; it resolves, preferring the highest-ROI
outcome:

- **Fuse** — the two intents are the same work; merge them into one pane and cancel the
  duplicate before it spends a token. The canonical duplicate-cognition kill.
- **Split** — the intents overlap partially; partition the scope so each pane owns a disjoint
  slice, converting a collision into legitimate parallelism.
- **Demote to reviewer** — one pane proceeds as the author; the other is re-tasked to *review /
  verify / index* the first's output (a different, non-duplicative role) rather than
  re-authoring it. Parallelism preserved, duplication removed.
- **Reuse** — if one pane's declared output already exists (in the Findings Bus, PM-03, or as a
  CO-05 asset), the second reuses it directly and drops the redundant work — the Redundancy Tax
  of PM-03 applied at declaration time.

A **soft** collision resolves to an **ordering** (the producer runs first or its output is
reserved) rather than a merge — a producer/consumer pair is valid parallelism, just sequenced.

### II.3 Honest limits of a file-based detector

PM-02 is precise about what it cannot do (CO-10). Detection is only as good as the declarations,
and declarations are read at boundaries, not enforced by a live lock — so two panes can both
declare, pass the check at their respective turn-starts, and *then* diverge from their
declarations mid-turn. Two guards bound this: (1) the `intent_lock.js` worktree+PID lock provides
a **soft real-time pause** on the narrow case of two processes touching the same working tree
concurrently — the one host-level lock that does act between processes; (2) **declaration drift**
(a pane doing work outside its declared scope) is caught post-hoc by the HR-ONESHOT-002 scope-
deviation check (>40% of touched files outside declared scope → surfaced). The mesh does not
claim to prevent all collision in real time; it claims to prevent *declared* collision at
boundaries and to *detect* drift after. That honest split is the guarantee.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Undeclared pane escapes the detector.** A pane launched without a declaration cannot be
  scope-checked. Detection + response: it simply gets CO-08's blunt `SAME_REPO_CAP=1` (the
  fail-safe), and is flagged as un-declared exactly as CO-08 flags an un-gated pane — never
  silently admitted.
- **False overlap starves legitimate parallelism.** Two independent scopes flagged as colliding
  → productive parallel work blocked. Detection: post-hoc WU/MTok on "collided" pairs that were
  actually disjoint → loosen the overlap grading. A starving detector shows as *foregone*
  high-ROI parallel work, which is measurable.
- **Stale declaration.** A pane finished but its declaration lingers, causing phantom
  collisions. Detection: declarations carry the same recency anchor as CO-08's "hot" definition
  (a real turn within the window); a declaration whose pane is no longer hot is expired by CO-06.
- **Declaration drift.** A pane declares scope X and edits Y. Detection: HR-ONESHOT-002 fidelity
  check post-hoc; the drift is surfaced to the Owner, and the pane's future declarations are
  trusted less (the detector weights a repeatedly-drifting pane's declaration down).

### III.2 Rollback protocol

PM-02 degrades to CO-08's exact current behavior. (1) Demote the scope-gate to the blunt
`SAME_REPO_CAP=1` for **all** panes (not just undeclared ones) — instant return to today's
sealed cap. (2) Disable resolutions — a collision reverts to a plain refusal (the CO-08
baseline). (3) Keep declarations as *advisory metadata* in the Brain without gating on them. The
fail-safe direction is **toward the blunt cap, never toward unrestricted parallelism**: a broken
detector must not admit colliding panes; it must fall back to the conservative count cap. Because
the recalibration only ever *widened* admission in exchange for proof-of-non-overlap, removing it
can only *tighten*, never break.

### III.3 Integration contract

- **CO-08 (parent)** — PM-02 refines CO-08's same-repo dimension from count to declared scope;
  the global cap, summed envelope, and no-bypass property are inherited unchanged. The live
  `scheduler.py` semantics change (relaxing same-repo cap on a passing scope-check) is the
  Owner-authorized follow-up build this dataset specifies.
- **`harness/intent_lock.js`** — the one real cross-process guard: a worktree+PID soft-pause for
  the concurrent-same-tree case.
- **PM-01** — declarations live in / are indexed by the Brain's active-plans section.
- **PM-03** — the Reuse resolution is the Redundancy Tax applied at declaration time.
- **PM-04** — declared cost/ROI/model feed the Budget Auction and the Opus Singleton arbitration.
- **CO-00 / CO-02** — the summed-envelope check gates admission alongside the scope check.
- **`/kclaude`** — the declaration is emitted at launch; the primary honest coordination point.
- **`/compact` / `/kclear`** — `/kclear` retires the pane's declaration (its work ended); a
  `/compact` preserves it (same work continues). **`/loop`** — a loop declares once at entry; its
  scope is fixed for the loop's life so it does not re-collide every iteration.

### III.4 Anti-patterns (forbidden)

- **Executing substantial same-repo work without declaring.** Undeclared work gets the blunt cap
  and is flagged; declaration is the price of relaxed admission.
- **Blocking a collision instead of resolving it.** The mesh fuses/splits/demotes/reuses; a plain
  refuse is the rollback state, not the operating state.
- **Trusting a declaration as a real-time lock.** It is boundary-read; drift is caught post-hoc,
  and the only live guard is `intent_lock`'s narrow same-tree pause (CO-10).
- **Relaxing the cap for an undeclared pane.** The recalibration widens admission *only* in
  exchange for a declaration; no declaration → no relaxation.
- **Silently absorbing declaration drift.** Drift is surfaced (HR-ONESHOT-002) and lowers future
  trust in that pane's declarations.

---

### PM-02 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| N same-repo panes admitted when declared scopes are disjoint AND aggregate is under envelope | Each pane declares intent | Admission of an undeclared pane beyond CO-08's blunt cap |
| A declared collision is resolved (fuse / split / demote-to-reviewer / reuse), never plain-blocked | Both panes declared | Real-time prevention of undeclared or mid-turn-drifted collision |
| Undeclared or detector-broken → fail-safe to CO-08 `SAME_REPO_CAP=1` | Always | Unrestricted same-repo parallelism |
| Declaration drift caught post-hoc (HR-ONESHOT-002) and lowers future declaration trust | Always | Prevention of the first drift in real time |
| Rollback restores CO-08's sealed blunt cap with no loss | On misbehavior | — |

**Guarantee level (honest):** rung-3 at the launch boundary (the scope-gate admits/refuses in
kclaude) + rung-2 turn-start advisory + one narrow rung-4 cross-process guard (`intent_lock`
worktree+PID pause). Declarations are **files on disk polled at boundaries**, not a lock server;
mid-turn drift is detected, not prevented. This is the sense CO-08 lacked — the reason it had to
block same-repo parallelism wholesale. Parent: **CO-08**. *Sealed under SCS C65.*
