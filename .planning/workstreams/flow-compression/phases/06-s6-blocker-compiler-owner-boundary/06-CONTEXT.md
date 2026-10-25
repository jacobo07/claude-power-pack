# Phase 6: S6 Blocker compiler + Owner boundary - Context

**Gathered:** 2026-10-24
**Status:** Ready for planning (auto mode: recommended defaults chosen, no Owner input)

<domain>
## Phase Boundary

Every `mission_blocked` (and Owner-hold / OWNER_BOUNDARY park) carries three typed fields: a blocker class from a
taxonomy derived from the real ledger, a machine-readable unblock condition, and an `independent_work` flag saying
whether the mission could proceed on other safe work. Foreseeable Owner decisions are listed once at arm time
(batched) instead of discovered one by one in live workers. No authority expansion; no new state machine (FC-08, FC-06, FC-10).

Out of scope: replay/champion-challenger (Phase 7), work stealing (S8, dormant), KV/UKDL (Phase 8).
</domain>

<decisions>
## Implementation Decisions

### Taxonomy
- **D-01:** Derive classes from the host ledger by a read-only census of existing `mission_blocked`, `blocked_intent`, `owner_hold`, `cost_hold` and AMR OWNER_BOUNDARY rows (reasons + hold kinds), not from imagination. The census output and the class-to-evidence table are committed as an artifact; a class with zero observed rows is allowed only if it is already a named hold kind in code. Unclassifiable rows map to `UNKNOWN`, which is never treated as "independent work available".
- **D-02:** Build on `tools/blocked_intent.py` (COMMAND/DECISION/RESOURCE/HOST_GATE/UNKNOWN) and the existing hold kinds (`resume_not_certified`, `seal_refused`, cost hold, capital exhausted, owner_hold). The compiler is a pure function in a new module `tools/blocker_compiler.py` that maps (reason, hold, blocked_intent, record) to `{class, unblock_condition, independent_work, owner_required}`. blocked_intent stays as one input, not replaced.
- **D-03:** `unblock_condition` is structured (`{kind, ...}` e.g. owner_act with the exact command, host_gate, resource_supplied, time/cause delta), never prose only; a human sentence rides beside it.

### Independent-work flag
- **D-04:** `independent_work` is true only on positive evidence: the ROADMAP/STATE shows a next runnable unit not depending on the blocked item, inside the existing authority. Absent or unreadable evidence yields `false` with reason `unmeasured` (absent is not true, absent is not zero). The compiler reports; it never launches anything itself.
- **D-05:** When `independent_work` is true the supervisor path may continue with that unit using existing launch/admission gates only; no new launch path.

### Emission
- **D-06:** Every site that writes `event="mission_blocked"` (gsd_mission.py around the capsule_blocked, capsule_seal_refused and surface_blocked branches) goes through one helper that attaches the compiled fields to the transition row and the ledger. A guard test greps all `mission_blocked` writers and fails if any bypasses the helper (no hand-curated list: discovered by search).
- **D-07:** Kill switch `CPP_BLOCKER_COMPILE=off` restores the old row shape; existing consumers must tolerate extra fields.

### Owner boundary batching
- **D-08:** At `arm`/`arm_preflight`, compile a "foreseeable Owner decisions" list from the spec/ROADMAP/STATE (capital top-ups, deploy/push authorization, branch protections, known Owner-only gates) and write it once as a single batched record plus one Owner-queue entry, not N parked missions. Decisions already answered by a recorded directive are omitted.
- **D-09:** RESOLVE_BY_POLICY applies only when an explicit written policy covers the decision (matching rule id recorded on the row); otherwise the item stays an Owner decision. No authority, capital, push, deploy or protection is ever expanded by the compiler (FC-06). `python -m modules.autonomy_gate classify` is the reference classifier for the Owner-only set; the compiler must agree with it on the control cases.

### Proof
- **D-10:** `tools/test_s6_blockers.py` with V-S6-* gates, printing `S6_PASS=n/n`: positive and negative control per class, UNKNOWN reachable, independent_work false on unmeasured, writer-discovery guard, batching idempotent (second arm adds nothing), policy-resolution refused without a rule, and mutants (drop-class, always-independent, expand-authority) that must go red. Each negative control must be shown to fire against the real reader first (Phase 5 incident).
- **D-11:** Existing suites stay green (`test_gsd_mission`, `test_blocked_intent`, `test_owner_boundary_delivery`, `test_s5_reconcile`, `test_gsd_epoch`). Run with `CPP_RESOURCE_ADMISSION=off`.

### Claude's Discretion
Class names, module layout inside tools/, exact record field spellings, census script shape.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Mission and requirements
- `vault/specs/flow-compression.md` - S6 line, acceptance, rollback, budget
- `.planning/workstreams/flow-compression/ROADMAP.md` - Phase 6 definition
- `.planning/workstreams/flow-compression/REQUIREMENTS.md` - FC-06, FC-08, FC-10, FC-12
- `.planning/workstreams/flow-compression/STATE.md` - incidents carried to Phase 8; plane decision (bound worktree, ff-merge into clone, no push)
- `.planning/workstreams/flow-compression/phases/05/05-01-PLAN.md` - plan shape and gate conventions to copy

### Code
- `tools/blocked_intent.py` - existing typed ask (A2)
- `tools/gsd_mission.py` - `mission_blocked` writers, `arm_preflight` (~5927), `arm` (~5984), `arm_chain`; AMR section (~2504)
- `tools/mission_recovery.py` - OWNER_BOUNDARY state and hold handling (~33-448)
- `tools/test_blocked_intent.py`, `tools/test_owner_boundary_delivery.py`, `tools/test_s5_reconcile.py` - test conventions
- `modules/autonomy_gate` - Owner-decision classifier
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `blocked_intent.classify/intent`: seed of the taxonomy and the ANSWER_STANDING path.
- `mission_recovery` OWNER_BOUNDARY and `TERMINAL_RECOVERY_STATES`: the Owner-boundary vocabulary.
- `arm_preflight`: the single arm-time hook for batching foreseeable decisions.

### Established Patterns
- Pure decision function + one effectful call site + env kill switch + V-* gate file with mutants (S2-S5).
- Provenance in ledger rows; read-only reconcilers; `unmeasured` kept apart from zero.

### Integration Points
- Each `transition(... event="mission_blocked" ...)` call; `surface_blocked`; Owner-queue writer used by arm.
</code_context>

<specifics>
No specific requirements beyond FC-08: class, unblock condition, independent-work flag on every BLOCKED.
</specifics>

<deferred>
## Deferred Ideas

- Replaying historical blocks through the compiler to measure avoidable idle: Phase 7.
- Work stealing across independent units: S8, dormant until Phase 7 shows a consumer.
</deferred>

---

*Phase: 6-S6 Blocker compiler + Owner boundary*
*Context gathered: 2026-10-24*
