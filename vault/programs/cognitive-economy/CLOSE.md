# Cognitive Economy Program -- close

Plan of record `vault/plans/cognitive-economy-program-2026-10-03.md` (Owner APPROVED 2026-10-03). The
pre-registration was frozen at `fa9ae2ed`. Mission `m-fdefb0fca0c0`, three epochs, branch
`cognitive-economy/autonomous-run`, worktree `.claude/worktrees/cognitive-economy`. Closed 2026-10-03.

Principle held to: waste less intelligence, never use less. A falsified lever counts as a result, and an upper
bound is never reported as a saving.

## Terminals (20 of 20)

| pillar | terminal | pre-registered | evidence |
|---|---|---|---|
| A baseline cognitive economics | IMPLEMENTED_AND_VERIFIED | = | gates/gate_baseline.py, evidence/A-prg.md |
| B resident context floor | AUTHORIZATION_BOUND | = | owner-bundle [B], evidence/B-T-floor-and-gc.md |
| C skill/agent/tool virtualization | DEFERRED_STRONGER_OWNER | = | handoffs/C.md; tool schemas 0.002 % |
| D context lifetime / dead context | MERGED_INTO_EXISTING_OWNER | = | handoffs/D.md, evidence/D-E-context-lifetime.md |
| E fresh-epoch economics | MERGED_INTO_EXISTING_OWNER | = | handoffs/E.md; ceilings 2.78 % / 0.91 % |
| F reread / materialized cognition | FALSIFIED_OR_REJECTED_BY_EVIDENCE | RESEARCH_INSUFFICIENT_EVIDENCE | 1.88 % < 3 % |
| G common subexpression elimination | FALSIFIED_OR_REJECTED_BY_EVIDENCE | = | reopening condition (F >= 3 %) not met |
| H turns per verified advancement | IMPLEMENTED_AND_VERIFIED | = | gates/gate_turns.py, evidence/H-J-turn-advancement.md |
| I one-shot work packet | MERGED_INTO_EXISTING_OWNER | = | handoffs/I.md |
| J non-convergence detection | DEFERRED_STRONGER_OWNER | RESEARCH_INSUFFICIENT_EVIDENCE | 3.51 % >= 3 %, handoffs/J.md |
| K tool output admission | FALSIFIED_OR_REJECTED_BY_EVIDENCE | = | largest dead class 2.67 % < 3 % |
| L capability compile-out | IMPLEMENTED_AND_VERIFIED | = | gates/gate_compound78.py, evidence/L-prg.md |
| M model / processor allocation | DEFERRED_STRONGER_OWNER | = | handoffs/M.md |
| N event-driven cognition | MERGED_INTO_EXISTING_OWNER | = | handoffs/N.md |
| O cognitive IR / state normalization | MERGED_INTO_EXISTING_OWNER | = | handoffs/O.md (audit G1-G4 to the Goal spine) |
| P proof reuse | FALSIFIED_OR_REJECTED_BY_EVIDENCE | = | verification 0.50 % |
| Q technical capital accounting | MERGED_INTO_EXISTING_OWNER | = | handoffs/Q.md |
| R institutionalization / UKDL | IMPLEMENTED_AND_VERIFIED | = | gates/gate_ukdl_candidates.py, evidence/R-prg.md |
| S universal baseline compiler | MERGED_INTO_EXISTING_OWNER | = | handoffs/S.md |
| T institutional GC | AUTHORIZATION_BOUND | = | owner-bundle [T], evidence/B-T-floor-and-gc.md |

18 of 20 pillars ended at their pre-registered terminal, and both misses went toward more evidence. F was predicted
unmeasurable, but the identity boundary turned out exact, so it was measured and falsified. J was predicted
unmeasurable, but the turn taxonomy measured it at 3.51 %, which clears the frozen rule, so a detector was earned
and handed to its owner.

## Before and after

command: `python tools/usage_index.py window <start> <end>`, read only.

| window | hours | calls | subagent calls | weighted (input 1, cache_read 0.1, cache_write 2, output 5) | weighted per call |
|---|---|---|---|---|---|
| D-W7 (frozen) 2026-09-26T00Z .. 10-03T00Z | 168 | 75,969 | 27,497 | 3,325,101,725 | 43,769 |
| after 2026-10-03T00Z .. 17:00Z | 17 | 7,309 | 1,736 | 284,640,174 | 38,944 |

**No difference between these two rows is attributable to the campaign.** Every campaign commit is on the unmerged
branch (`[RUN]`), and no live owner was edited, so nothing the campaign built ran in the after window. The after
window is also partial (17 h), and it contains this mission's own measurement work and the peer panes' work. It is
reported because the plan requires it, and it reads as a composition change of unknown cause, not a delta.

Every saving in the ledger, by label:

- **realized**: none.
- **upper_bound**: D economic trigger, net at most +0.19 % of D-W7, interval [-0.05, +0.19]. E mission rotation, net
  at most 2.41 %. J detector, at most 3.51 % (proposed, not built). All three have unknown displacement. Context
  crossings as a whole avoid at most 17.16 % relative to never crossing; that is rent against the wrong
  counterfactual, not a saving (UC-06).
- **unknown**: L, the compile-out of steps 7+8. It is not live, and its share of the STUCK counter was not measured.

## Meta-analysis

1. **Most proposed levers were already below materiality.** The campaign measured seven candidates; one cleared
   3 %. That is the main product of a measurement campaign: six builds that will not be made, each closed by a
   number with its denominator and command. Below the line: F 1.88, K 2.67, P 0.50, C-tools 0.002, E 2.78, and the
   D economic trigger 0.19. Above it: J 3.51.
2. **The largest open question is UNSETTLED, not waste.** 51.97 % of D-W7 calls have no observable outcome that
   classifies them. Any claim that X % of the week was wasted overreaches by that margin. A second taxonomy pass, or
   joining a test-result log, would shrink it. That work belongs to H's owner and is not in this campaign.
3. **Carriage dominates and resists identity levers.** Tool-output carriage is 25.71 % of D-W7, Read alone
   21.02 %. Exact identity re-reads (F) and dead outputs (K) inside it are each below 3 %. What remains is content
   that was read once and kept, which only shorter context lifetimes reclaim. That is D and E's ground, and those
   owners have the measured ceilings.
4. **Instruments failed in the same way, three times.** These were fixed before they could mislead: the done-gate
   selftest's stale pole, turns.py's git timeout labelled as non-convergence, and t_sweep's matcher holes, which
   proposed modules in use for deletion. All three are the doctrine's existing rule (could the instrument have
   returned the other answer?) applied late. UKDL review UC-01..03 records them, and two are rejected as already
   owned.
5. **One structural defect in a live supervisor:** gsd_mission's whole-tree progress fingerprint (audit G5). It is
   the only finding promoted toward the UKDL (`[R] UC-04`).

## Owner bundle

`vault/programs/cognitive-economy/owner-bundle.md`: `[RUN]` merge the branch, `[L]` the live compound switch,
`[B]` the remaining rule moves, `[T]` declare or wire 14 dormant modules, and `[R] UC-04` the UKDL promotion.

## Done-gate

command: `python tools/test_cognitive_economy_program.py --final` (worktree `cognitive-economy/autonomous-run`,
2026-10-03; it re-runs the four IMPLEMENTED gates A, H, L and R, and its selftest, before judging)

```
CEP_VERDICT=PASS failures=0
exit=0
```

command: `python tools/test_cognitive_economy_program.py --selftest` (tail)

```
  ok   V-CEP-SELFTEST-CLEAN (green, and the IMPLEMENTED gate was actually run once)
  ok   V-CEP-MUT-realized-without-displacement killed by L9
  ok   V-CEP-REAL-RUNNER (green rc 0, red rc 3)
  ok   V-CEP-REAL-ALLOWLIST (real script admitted, the verifier itself refused)
  ok   V-CEP-REAL-HANDOFF (frozen at newest 8b62b6ce -> False, frozen before C0 -> True, oldest 1cabd117)
CEP_SELFTEST=PASS
```

The gate passes on this branch. It passes on `feature/knowledge-acquisition` only after the `[RUN]` merge.

## 2026-10-04 rerun on `feature/knowledge-acquisition` (supersedes nothing above)

The 2026-10-03 record above describes a run that happened and is kept as written. This section adds a later run.

- `[RUN]` merge landed as `11470e92` (24 mission commits, campaign paths only).
- The first `--final` after the merge FAILED 1 clause: pillar L. `gates/gate_compound78.py` refused to run because
  the live `LEARNINGS_PENDING.md` was absent. The marker is transient (a successful `/cpp-compound` deletes it,
  the sentinel recreates it), and the live state had been rewritten at 10-04 18:45Z outside the mission.
  This was a defect in the gate's inputs. The step 7+8 module was not at fault.
- Fix `acbaabcf`: `finalize()` only unlinks the marker and never reads it. When the live marker is absent, the
  gate now judges a synthetic one and prints `marker=live|synthetic`. Observed: live PASS `marker=live`;
  synthetic PASS `marker=synthetic` (PP_MAIN pointed at a temp copy of the 235 learnings, no marker);
  synthetic `--break-rollback` FAIL `failures=1` (rollback). The red branch still fires.

command: `python tools/test_cognitive_economy_program.py --final` (`feature/knowledge-acquisition`, after `acbaabcf`)

```
CEP_VERDICT=PASS failures=0
exit=0
```

`--pillar <P>` printed `CEP_PILLAR_<P>=PASS` for all 20 pillars, and `--status` reported `open=[]`
`violations=[]`. `.planning/workstreams/cognitive-economy/REQUIREMENTS.md` checkboxes now match the ledger.
Not pushed. Owner items `[L] [B] [T] [R]` in `owner-bundle.md` are still pending.
