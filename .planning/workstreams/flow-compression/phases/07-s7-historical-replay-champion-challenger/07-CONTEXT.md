# Phase 7: S7 Historical replay + champion/challenger - Context

**Gathered:** 2026-10-24
**Status:** Ready for planning (auto mode: recommended defaults chosen, no Owner input)

<domain>
## Phase Boundary

A read-only replay harness runs the recorded host ledger through the real `plan_next()` seam (and the S2-S6 pure
decision functions) twice: once with the pre-flow-compression policy (champion) and once with the S2-S6 policy
(challenger). It reports which historical failures the challenger prevented, moved earlier, or left as legitimate
stops, and fails when a mutant policy is not caught. It also reports mission-hours vs wall-clock vs critical-path
wall-clock, and avoidable idle before and after (FC-09, FC-11, FC-01). No new state machine, no policy change
without replay evidence, no GSD Core change (FC-10).

Out of scope: work stealing S8 (dormant; this phase only records whether replay shows a consumer for the activation
predicate), KV/UKDL/CBR/red team (Phase 8).
</domain>

<decisions>
## Implementation Decisions

### Harness shape
- **D-01:** New module `tools/flow_replay.py` (read-only, never writes the host ledger, mission records or queue). It reads
  `/home/kobii/.claude/state/gsd-autorun-ledger.jsonl` (path overridable) and reconstructs, per mission, the record
  fields `plan_next(rec, now, sessions, pid_alive=..., blocked_probe=...)` needs, calling the real function with injected
  `pid_alive`/`blocked_probe` so replay is pure. Seam = `plan_next`; no forked copy of the policy (same rule as `rollover_replay.py`).
- **D-02:** Each policy is a named toggle set over the existing kill switches (`CPP_ARM_PREFLIGHT`, `CPP_CCR_ADMISSION`, `CPP_MISSION_BOUNDED_RENEWAL`/`CPP_MISSION_RENEW`, `CPP_TERMINAL_RECONCILE`, `CPP_BLOCKER_COMPILE`, `CPP_ROTATION_INVARIANT`). Champion = all off, challenger = all on, applied by an env scope inside the harness, restored after. No new switch is added.
- **D-03:** Every replayed incident gets a verdict from a closed set: `PREVENTED`, `MOVED_EARLIER` (detected earlier with measured delta), `LEGITIMATE_STOP` (policy still stops, with reason), `UNCHANGED`, `UNMEASURED` (insufficient ledger evidence; never counted as prevented).
- **D-04:** The incident corpus is discovered from the ledger by event type (`mission_blocked`, `admission_refused` loops, `cost_hold`, `capital_exhausted`, terminal-without-receipt, `epoch_compacted`), not curated; the Phase 6 census (`phases/06-s6-blocker-compiler-owner-boundary/06-CENSUS.md`) and the 149 h terminal case from S5 are cross-checks, not the source. The ledger is live, so the report records row count and a content hash at read time.

### Mutants
- **D-05:** The four mandatory mutants (always-admit, never-rotate, always-renew, terminal-without-proof) plus drop-blocker-class and expand-authority are applied as challenger variants. A mutant must change the replay verdict set (more FC-06 breaches or lost prevention) or the gate is red; a mutant that replays identical to the challenger is a harness defect, reported, not ignored. A no-op drill control (as in Phase 6) proves the drills can fail.
- **D-06:** FC-06 invariants are replay assertions: the challenger never exceeds the Owner capital ceiling, never admits against a different packet digest, never reports DONE without `receipt_judge` closure, never weakens branch/push protections. A breach is a hard fail, independent of any speed gain.

### Time accounting
- **D-07:** The report separates three numbers per window: summed mission-hours (sum of mission active intervals), wall-clock (first launch to last event), and critical-path wall-clock (longest chain of dependent units from ROADMAP/ledger order, not concurrent panes). Avoidable idle = intervals where no worker ran while a runnable, authorized next unit existed (evidence: `plan_next` would have returned launch/recover), before vs after. Missing interval evidence is `unmeasured`, never zero.
- **D-08:** Outputs: machine JSON plus a markdown report committed under the phase directory, each number carrying the command and ledger hash that produced it.

### S8 predicate
- **D-09:** The report ends with one recorded sentence on whether replay found any case where independent work existed and was left idle (a work-stealing consumer). Zero found means S8 stays dormant with the evidence; it is not built here.

### Proof
- **D-10:** `tools/test_s7_replay.py`, V-S7-* gates, prints `S7_PASS=n/n`: harness read-only (ledger sha256 before/after), real `plan_next` is the seam (grep + monkeypatch probe), champion differs from challenger on at least one real incident, each verdict class reachable with a positive control and a named neighbour, UNMEASURED reachable, mutants red, no-op drill control fires, three time numbers distinct on a constructed case and never conflated, FC-06 assertions fire on a seeded breach. Each negative control is first shown to fire against the real reader (Phase 5/6 incident pattern).
- **D-11:** Existing suites stay green (`test_gsd_mission`, `test_s5_reconcile`, `test_s6_blockers`, `test_gsd_epoch`, `test_rotation_invariant`); `mission_spend` 44/45 and `mission_continuity` 37/38 are known prior failures. Run foreground, bounded, with `CPP_RESOURCE_ADMISSION=off`.
- **D-12:** Open debt carried from Phase 6 verification: W2 (`compile_blocker` not strictly pure) and W3 (`mission_blocked` ledger row lacks `unblock_condition`); the replay must not depend on either and must say so if it does. Fix only if replay shows they distort a verdict; otherwise leave to Phase 8.

### Claude's Discretion
Module layout, report formatting, window boundaries for time accounting, JSON field spellings.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `vault/specs/flow-compression.md` - S7 line, acceptance, rollback, budget
- `.planning/workstreams/flow-compression/ROADMAP.md` - Phase 7 definition
- `.planning/workstreams/flow-compression/REQUIREMENTS.md` - FC-01, FC-06, FC-09, FC-10, FC-11, FC-12
- `.planning/workstreams/flow-compression/STATE.md` - incidents carried to Phase 8; plane decision (commit in bound worktree, ff-merge into clone, no push)
- `.planning/workstreams/flow-compression/phases/06-s6-blocker-compiler-owner-boundary/06-CONTEXT.md`, `06-CENSUS.md`, `06-VERIFICATION.md` - prior decisions, ledger census, W2/W3 warnings
- `.planning/workstreams/flow-compression/phases/05/05-01-PLAN.md` - plan shape and gate conventions
- `tools/gsd_mission.py` - `plan_next` (~599), kill switches, AMR section
- `tools/rollover_replay.py` - read-only replay precedent (single policy seam, no fork)
- `tools/replay_harness.py` - existing adversarial replay conventions
- `tools/test_s6_blockers.py` - V-gate, mutation-drill and no-op-control conventions
- `/home/kobii/.claude/state/gsd-autorun-ledger.jsonl` - the replayed ledger (live; hash at read)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `plan_next`: pure except injected `pid_alive`/`blocked_probe`; the replay seam.
- `rollover_replay.py`: pattern for measured-input replay with explicit evidence classes.
- S6 `MUTANT_FOR` map and no-op drill control: reuse the drill structure.

### Established Patterns
- Pure decision function + env kill switch + V-* gate file with mutants (S2-S6); `unmeasured` kept apart from zero.

### Integration Points
- Ledger reader -> record reconstruction -> `plan_next` under two env scopes -> verdict classifier -> report.
</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the Owner prompt - open to standard approaches.
</specifics>

<deferred>
## Deferred Ideas

- S8 work stealing build (only if D-09 finds a consumer).
- Fixing W2/W3 unless replay shows distortion (Phase 8).
</deferred>

---

*Phase: 7-S7 Historical replay + champion/challenger*
*Context gathered: 2026-10-24*
