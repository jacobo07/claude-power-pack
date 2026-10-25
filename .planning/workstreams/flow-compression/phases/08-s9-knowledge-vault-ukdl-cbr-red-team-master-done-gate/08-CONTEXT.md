# Phase 8: S9 Knowledge Vault, UKDL, CBR, red team, master done-gate - Context

**Gathered:** 2026-10-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the mission: (1) turn every bug/incident recorded in STATE.md during phases 1-7 into Knowledge Vault incident entries (FC-12); (2) promote proven laws to UKDL (HR/PR/Traps) without duplicating stronger existing laws; (3) CBR only for items with a fresh-inheritance proof; (4) a red team that attacks the S1-S6 slices; (5) record the S8 work-stealing activation predicate (S8 stays DORMANT); (6) run the master done-gate over the seven mandatory milestones. No new orchestrator, no policy change, no GSD Core change (FC-10).

</domain>

<decisions>
## Implementation Decisions

### Red team scope
- **D-01:** The Owner prompt "GSD X AUTONOMOUS FLOW COMPRESSION" that defines the red team is NOT in the repo (searched vault/, .planning/, RESUMPTION_FILE, spec; only the one-line "S9 ... red team" exists). Interpretation, taken as the narrowest safe reading: the red team is adversarial attempts, run against real code in temp copies, to make each slice S1-S6 violate an FC requirement (FC-01..FC-07, FC-08) - e.g. defeat the packet-digest binding, force a false DONE without receipt, make a lapse-lease renew past the ceiling, make a blocker compile without class/unblock condition, defeat rotation-before-compaction. Each attack ends in one of: HELD (control shows the attack could succeed if the guard were off), BREACH (a finding, becomes an FC-12 incident), or UNMEASURED. — **OWNER DECISION NEEDED (recorded in STATE.md):** if the real prompt carries other red-team categories, a later pass adds them; this phase does not invent them. **Reversibility:** reversible - an added report and test file.
- **D-02:** Every attack needs a positive control (the same attack against a mutated slice with the guard removed must succeed), the Phase 5/6/7 pattern; a red-team HELD with no control that can fail is not counted.
- **D-03:** Red team runs on temp copies and read-only against the host ledger; it never writes the live ledger, OWNER_QUEUE, or settings (Phase 7 read-only proof pattern reused).

### Knowledge Vault incidents (FC-12)
- **D-04:** One incident file per distinct bug class under `vault/incidents/` in the existing format (title, class, timeline table, root cause, earliest discoverable point, repair, test, pattern), named `2026-10-2x-flow-compression-<slug>.md`. Sources are the STATE.md "Incident for/Incidents for Phase 8" sections (AMR frontmatter, S5 fixtures, S6 capital regex, S7 premise corrections, controls that did not fire). Group the ~25 bullets into classes (about 6-8 files), do not write one file per bullet.
- **D-05:** The phase-7 warnings and the W2/W3 debt are carried as an explicit "known residual" section in a closing report, with their measured figures (27,484 mission-hours ~94% unobserved; 3 of 266 incidents show a measured change; 41 unmapped supervise_error loops; epoch_compacted rows without context size; W2/W3). They are listed, not repaired (scope).
- **D-06:** Each incident must cite its test or gate id and commit hash, verified by running the command in this phase (documented capability must be executable).

### UKDL
- **D-07:** Promote only laws that are new after a grep of `vault/knowledge_base/ukdl-universal.md` and `vault/hard_rules/HARD_RULES.md`; where a stronger law exists, link to it instead of duplicating. Candidate laws: (a) phase seal not closed until GSD status advanced (frontmatter incident); (b) a negative control must be shown to fire against the real reader before it counts (S5/S6/S7); (c) a class regex is tested against the real population before it counts (S6); (d) a gate green on first run needs a mutation drill plus a no-op drill control (S6/S7); (e) inferred measurements print their basis; carried-unchanged is never reported as a gain (S7). Append as a dated UKDL PROMOTIONS section in the file's existing style. **Reversibility:** reversible.

### CBR
- **D-08:** CBR (`modules/tower` + `vault/tower/families/`) gets an entry only for an item with a fresh-inheritance proof: a fresh process that knows nothing but the committed artefact reproduces the lesson's check. If no item can be proven in this phase, CBR gets no entry and the report says so; no unproven item is promoted. Absence is reported as UNMEASURED, not as success.

### S8
- **D-09:** S8 stays DORMANT. Record the activation predicate in the spec and report: build work stealing only if a replay of the ledger shows a consumer, defined as >= 1 incident where an independent safe action existed while the critical path was blocked AND the blocker row recorded independent_work=true. Phase 7 found 0 recorded independent_work values (W3), so the predicate is false; unblocking requires the S6 `independent_work` field to accumulate real rows. **Reversibility:** reversible.

### Master done-gate
- **D-10:** `tools/test_s9_done_gate.py`, V-S9-* gates, prints `S9_PASS=n/n`. It maps each of the seven mandatory milestones (S1..S7) to evidence (existing suite pass count run live, replay report, incident files exist and cite real gates), reruns the named existing suites with their known pre-existing reds (mission_continuity 37/38 V-AMCR-ONE-RESOLVER-INVENTORY, mission_spend 44/45 V-MSPEND-HOLD-PLAN-NONE) and fails if any additional gate is red, and asserts no GSD Core file changed (git diff against the mission base). Every gate carries a named positive/negative control and a mutation drill with a no-op drill control.
- **D-11:** Milestones whose evidence is UNMEASURED or laptop-plane (S3 DEFER autopsy, S5 149 h disposal on the laptop ledger, S1 live rotation numbers) are reported with their plane and status, never as PASS by assumption.
- **D-12:** After the phase seal, assert `init.progress --ws flow-compression --raw` reports `completed_count` 8; if not, the seal is not closed (STATE incident prevention). Artefacts (PLAN, SUMMARY, VERIFICATION) come from GSD workflows with frontmatter.

### Claude's Discretion
Number and grouping of incident files, wording of UKDL laws, red-team attack list within D-01, plan split (suggested: 08-01 incidents + UKDL + CBR + S8 predicate; 08-02 red team; 08-03 master done-gate + closing report).

### Execution plane
- **D-13:** Executors cannot write the clone; use general-purpose agents in the bound worktree `.claude/worktrees/flow-compression-w`, then `git merge --ff-only worktree-flow-compression-w` in the clone. No push.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Mission
- `vault/specs/flow-compression.md` - spec, slices S1-S9, master done-gate, rollback, budget
- `.planning/workstreams/flow-compression/REQUIREMENTS.md` - FC-01..FC-12
- `.planning/workstreams/flow-compression/ROADMAP.md` - Phase 8 entry
- `.planning/workstreams/flow-compression/STATE.md` - all incident entries and carry-overs for this phase
- `.planning/workstreams/flow-compression/RESUMPTION_FILE.md`

### Prior phase evidence
- `.planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.md` and `07-VERIFICATION.md` - replay report, 5 warnings
- `.planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-CONTEXT.md` - mutant and drill pattern (D-05, D-10)

### Knowledge stores
- `vault/incidents/2026-09-16-hook-registration-identity-loss.md` - incident file format
- `vault/knowledge_base/ukdl-universal.md` - UKDL (check before promoting)
- `vault/hard_rules/HARD_RULES.md` - HR archive
- `modules/tower`, `vault/tower/families/` - CBR
- `vault/specs/agent-capability-virtualization.md` - CBR/PRG ownership notes

No Owner red-team prompt file exists in the repo (see D-01).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/flow_replay.py`, `tools/test_s7_replay.py`: read-only harness, pin, mutant/drill pattern to copy for the red team and done-gate.
- Per-slice suites (test_arm_preflight, test_s5/s6 gates, test_gsd_epoch, test_rotation_invariant, test_gsd_mission, test_mission_continuity, test_mission_recovery, test_cpp_gsd_long_routing) are the milestone evidence.

### Established Patterns
- V-<SLICE>-* gate naming with `<SLICE>_PASS=n/n`; every gate has a control that fires; mutation drills plus a no-op drill control.
- Artefacts via GSD workflows with frontmatter; commits as separate git commands, message via -F file.

### Integration Points
- `vault/incidents/`, `vault/knowledge_base/ukdl-universal.md`, `vault/tower/families/`, STATE.md/RESUMPTION_FILE.md, `init.progress`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the roadmap line; open to standard approaches within D-01..D-13.

</specifics>

<deferred>
## Deferred Ideas

- Repairing the Phase 7 warnings (unobserved mission-hours, inferred idle gap starts, unmapped supervise_error loops, epoch_compacted without context size, W2/W3) - listed in the closing report only.
- Building S8 work stealing - dormant until the D-09 predicate is true.
- Pre-existing red gates V-AMCR-ONE-RESOLVER-INVENTORY, V-MSPEND-HOLD-PLAN-NONE - not ours.

</deferred>

---

*Phase: 8-S9 Knowledge Vault, UKDL, CBR, red team, master done-gate*
*Context gathered: 2026-10-25*
