# Strategic Gap Audit -- 2026-07-10 (frontier session, declared objective)

Objective (PP_SESSION_OBJECTIVE, verbatim intent): discover the structural gaps,
blindspots, and missing leverage points across the ecosystem; for each, design a
permanent system that closes the gap and works WITHOUT the frontier model.

SESSION_ZERO: `vault/sessions/SESSION_ZERO_2026-07-10T162015Z.md`.
Every finding below is grounded in evidence PROBED THIS SESSION (not recited from
memory): CO-12 corpus read, scheduled-task health run, PM-03 bus state listed.

---

## Meta-finding (the theme underneath all five)

The ecosystem is excellent at **construction-time verification** (V-gates, hermetic
x3, done-gates, Reality Contract) and structurally blind at **post-ship runtime
liveness and value measurement**. Every gap below is one instance of the same
missing loop: *ship -> is it alive? -> is it earning?* Nothing closes that loop
today; each instance gets discovered ad-hoc, sessions later, as a fresh lesson.

---

## D1 -- The Activation Gap is a CLASS with no monitor: Liveness Ledger

**Evidence (>=8 sealed lessons share one shape, plus 2 probed today):**
- T-HOOK-DISPATCHER-DRIFT-001 marked RECURRING (canonical vs live dispatcher; hit
  FD family, then FIOS this same week).
- PM-03 findings bus: probed today -- `~/.claude/state/parallel_mesh/findings_bus_*.jsonl`
  written by 3 repos (last writes Jul 4/8/9), zero consumers. Written-never-read.
- G2/G4/G5 orphaned by the Recovery Control Plane (C83).
- Memory lessons: orphan-module (imports-but-nobody-calls), orphan-field
  (consumer-without-producer), write-without-read, built!=wired dispatcher swallow,
  pp-sessions .vsix "verify installed, not more code".

**Blindspot:** a V-gate proves code works WHEN INVOKED; nothing proves anything
invokes it. Liveness is never audited, so inert components look identical to live
ones until a failure exposes them.

**Permanent system -- Liveness Ledger (deterministic, no model):**
- `vault/liveness/registry.json`: every shipped component declares its liveness
  contract: `{id, producer_path, activation_surface (dispatcher entry | scheduled
  task | env flag | extension), evidence_probe (file mtime<max_age | CO-12 signal
  kind | live-vs-canonical hash), consumer}`.
- `tools/liveness_audit.py`: runs all probes, emits verdict per row: LIVE /
  WIRED-BUT-SILENT / ORPHANED / DRIFTED. Pure fs + hash + jsonl-grep checks.
- Surfaces: daily scheduled task writing `vault/liveness/LIVENESS.md` + a
  SessionStart advisory line (count of non-LIVE rows).
- Done-gate amendment: shipping a new wired component REQUIRES a registry row
  (same class of rule as "new hook requires Copy-Item doc").
- Dispatcher drift becomes ONE registry row (hash canonical vs `~/.claude/hooks/`),
  retiring the recurring trap as a monitored invariant.

**First move (S):** registry schema + auditor + 5 seed rows (dispatcher hash,
PM-03 consumer, FIOS stop signal, FD-07 flywheel signal, kclaude preflight).

## D2 -- The flywheel compounds in exactly ONE repo

**Evidence (CO-12 corpus, probed today):** 48 `fios_token_irr` signals; PP shows
7 assets / FDI 0.714; KobiiCraft and TUA-X frontier panes emit **0 assets, FDI 0**
every Stop. UKDL lessons are per-repo; the FD-07 ledger exists only in PP.

**Blindspot:** the highest-leverage machinery (frontier flywheel, lesson sealing)
covers ~1 of 8+ active repos. Frontier tokens spent where most product work
happens (KobiiCraft, TUA-X, InfinityOps) leave NO portable deposit -- 100%
frontier dependence exactly where spend is highest. A CRITICAL transversal lesson
sealed in one repo does not stop the same bug in the next.

**Permanent system -- Federated ledger + lesson propagation:**
- FD-07/FIOS ledger path becomes per-repo with a global aggregate:
  `~/.claude/state/fd_ledger/<repo-slug>.jsonl`; token_irr reads the repo's own
  ledger (deposits become possible everywhere), IRR aggregates globally.
- `tools/ukdl_propagate.py` (scheduled or Stop-tail): UKDL entries tagged
  CRITICAL + transversal are mirrored, hash-verified (same pattern as rules/
  mirrors), into each subscribed repo's `vault/knowledge_base/ukdl-universal.md`
  under an `## IMPORTED (global)` section. One-way, append-only, fail-open.

**First move (S/M):** repo-slug ledger in token_irr + fd_07 (backward-compatible:
PP keeps its ledger); propagation tool with a 2-repo pilot (KobiiCraft, TUA-X).

## D3 -- Knowledge base: write-optimized, never GC'd, read-ROI-blind

**Evidence:** MEMORY.md hit its byte ceiling this week (21 B margin); 46k-record
vault; 819 graph coordinates; JIT injected a 13.4 KB rollback-skill spec into THIS
strategy prompt (relevance mismatch, observed today); historic gatekeeper 40 KB/Read.
No surface records whether an injected lesson ever changed behavior.

**Blindspot:** injection cost is paid on every prompt; prevention value is never
measured. Dead knowledge is indistinguishable from load-bearing knowledge, so
nothing can be retired safely -- the KB and its token tax grow monotonically.

**Permanent system -- Recall-ROI instrumentation:**
- Every injection surface (JIT loader, gatekeeper-semantic, graph advisories,
  memory recall) appends a CO-12 signal `kb_injection {lesson_id, surface, bytes}`.
- Monthly deterministic report joins injections x CEPS error-recurrence:
  lessons injected N+ times whose origin error class never recurred AND never
  triggered a pivot -> RETIRE-candidate list (Owner-gated, never auto-deleted).
- Mismatch detector: injected-spec vs prompt-domain disagreement logged (today's
  rollback-spec-into-strategy-prompt is the seed case).
- This retires MEMORY.md byte-trimming as a recurring manual chore: eviction
  becomes evidence-based.

**First move (S):** add the `kb_injection` emit to jit_skill_loader.py +
gatekeeper (2 producers), then the report tool once ~2 weeks of corpus exists.

## D4 -- Owner-side residuals have no queue

**Evidence:** PM-03 consumer wiring pending since C70 (6+ days, invisible);
Copy-Item last-miles for FD then FIOS the same week; .vsix verification; Task
Scheduler registrations; today's 2 FAILING miners + 6 ungated HIGH_FREQ tasks --
all scattered across vault/plans/, memory files, and session-end emissions.

**Blindspot:** HR-001 makes Owner-actions structural, but they are tracked
nowhere as a set. Built->live latency is unbounded and invisible.

**Permanent system -- OWNER_QUEUE:**
- `vault/owner_queue/QUEUE.md`: machine-appended rows `{id, date, one-line action,
  EXACT command, unblocks}`. Agents append at ship time instead of burying the
  command inside a plan doc.
- SessionStart advisory: `Owner queue: N pending, oldest X days`.
- Composition with D1: the Liveness Ledger DETECTS (row went LIVE) and
  auto-clears the queue entry -- the Owner never manually bookkeeps completion.

**First move (S):** queue file + appender helper + SessionStart line; backfill
the 4 currently-known pending items.

## D5 -- Idle-fire automation burns 24/7, failures normalized

**Evidence (probed today, `tools/scheduled_task_health.py`):** 14 tasks: 2 FAILING
on every run (PP-Miner-V2, PP-Sovereign-Miner, exit 1), 6 HIGH_FREQ (120-480 s)
firing regardless of whether ANY session is live (RAM-trim, network daemon,
hibernation, kickbacks guard, pane-map, playwright watchdog).

**Permanent system:** shared `session_active` guard (newest transcript INTERNAL
timestamp < 15 min -- per the pane_map-mtime-forges-liveness lesson, never file
mtime) prepended to the 6 HIGH_FREQ tasks; miners diagnosed once -> repair or
disable. The health checker itself becomes a D1 registry row so silent failure
can never re-normalize.

**First move (S):** guard script + edit 6 task definitions (Owner-side
registration -> D4 queue entry); one manual miner run to read the real exit.

---

## Priority and composition

Leverage order: **D1 > D2 > D3 > D4 > D5.** D1 is the class-closer (every future
build inherits it); D2 multiplies the existing flywheel across the whole
ecosystem; D3 converts the KB from a growing tax into a measured asset; D4+D5 are
small hygiene systems that D1 supervises. D1+D4 compose (detect->prescribe->
auto-clear); D2+D3 both ride CO-12 as the single instrument (no new accountants).

All five are deterministic code + scheduled/SessionStart surfaces -- they run
without a frontier model, per the objective's "works without you" constraint.
Proposal only: nothing above was built this session (D2A doctrine: propose,
Owner-gates the build).
