---
covers: [goal-spine, goal spine, durable goal, goal convergence, goal reconciler, execution epoch, goal revision]
status: IN-PROGRESS
tier: T3
approved: 2026-09-22 (Owner, inline ULTRA plan)
---

# Goal Spine v1 — durable Goal convergence over existing runtimes

## Objective
A Goal handed over once is owned to convergence across sessions, agents, context
resets, failures and bounded execution epochs. Completion is never declared because
one agent, one GSD milestone or one `/cpp-gsd-long` run finished.

## Scope — the only truths the spine owns
Goal intent (verbatim), identity, revision, outcome contract, declared required
obligation ids, authority, budget, lifecycle state, persisted convergence receipt.
Measured 2026-09-22: no existing Power Pack or KobiiCraft module owns any of these.

## Reused, never re-owned
| Truth | Owner |
|---|---|
| GSD phase / milestone | GSD |
| Mission Contract (called with in-process intent + obligations) | `modules/gsd_x/mission/contract.py` |
| Obligation type, lifecycle, persistence (goal-scoped namespace) | `modules/gsd_x/mission/{obligation,store}.py` |
| Closure arithmetic — **the judge** | `modules/gsd_x/mission/closure.py` |
| Evidence strength | `modules/done_gate/strength_ladder.py` |
| Epoch runtime, budget, resume, started-signal | `/cpp-gsd-long` (`tools/gsd_long_run.py`) |
| Owner decisions | `modules/owner_queue` |
| Production Reality | the project's verifier (KobiiCraft: `scripts/verify_change.py`) |

## Acceptance criteria
1. A Goal survives process restart and is reconstructed from durable state alone.
2. A whitespace-only intent edit is not a new revision; a semantic edit is.
3. A Goal cannot be declared without required obligation ids.
4. CONVERGED is reachable only from a convergence verdict computed by GSD X closure,
   and only when every declared required obligation is present and closed.
5. An empty or missing obligation store never converges a Goal.
6. BLOCKED requires a named external condition from a closed set.
7. Two writers cannot both save the same Goal version.
8. An epoch is STARTED only when the exact prepared command was submitted after it
   was prepared; a marker is never written for a session the spine does not own.
9. A retry with an unchanged structured fingerprint is refused.
10. A provider DONE without evidence satisfies nothing.

Gates: `tools/test_goal_spine.py` (`V-GOAL-*`), plus
`tools/test_gsd_x_mission_goal_scope.py` for the GSD X extension.

## Non-goals
Goal Hypervisor, Execution Colonies, Method Router marketplace, Factory Treasury,
Goal Civilization, Futures Simulator, Proof Market, Self-Play, Portfolio Intelligence,
BMAD, Superpowers-as-orchestrator, autonomous keystrokes into panes, a second GSD
lifecycle, a second evidence store, a second promotion authority.

## Rollback
Revert `modules/goal_spine/` and the goal-scope extension in GSD X's store (its
default path is unchanged, so the revert is inert for existing missions). Goal state
lives only under `~/.claude/state/goal-spine/`.

## Status
Plan of record: `~/.claude/plans/shimmying-conjuring-hanrahan.md`.
This file is updated as each stage lands.

| Stage | Commit | Evidence |
|---|---|---|
| G2 GSD X goal-scope + `o.id` crash fix | `141d1ae` | `test_gsd_x_mission_goal_scope.py` 5/5 (1/5 before); `test_gsd_x_mission.py` 17/17 unchanged |
| G1 Goal record + store | `7180d90` | `test_goal_spine.py` 15/15 |
| G3 convergence | `8b44d10` | `test_goal_spine_convergence.py` 15/15; probe 9/11 |
| G4 epochs | `2985e10` | `test_goal_spine_epoch.py` 13/13; probe 34/39 |
| Identity fix (intent in a place) | `f692404` | `test_goal_spine.py` 16/16 |
| G6 receipts | `a1a682b` | `test_goal_spine_receipt.py` 15/15; probe 16/24 |
| G5 reconciler + audit fixes | `b209776` | `test_goal_spine_reconciler.py` 27/27 (18 before); probe 41/54 pre-fix |
| P1/P3 providers + CLI | `7d96aa5` | `test_goal_spine_verify.py` 5/5, incl. the first end-to-end autonomous loop |

**Full set: 234 gates green**, including the untouched baselines `test_gsd_long_run.py`
99/99 and `test_done_strength_ladder.py` 15/15.

### Mutation record — G5, re-run against the COMMITTED reconciler
**45/59 caught** (41/54 before the audit fixes). One survivor was real and is now
pinned: `packet_delivered` defaults to `False`, and flipping that default survived —
a fail-open default on the one field the whole packet design rests on, so an action
carrying no packet could have claimed delivery (`V-RECON-NO-PACKET-NEVER-CLAIMS-DELIVERY`).
The other 13 are classified:

| Survivors | Class |
|---|---|
| `Action(frozen=)`, hash prefixes, subprocess timeout, `[:12]` in a message | EQUIVALENT — value objects and formatting |
| the re-ask loop's bounds and its `attempt == 1` text choice | EQUIVALENT — which wording is used first, not whether a packet is pending |
| `return rid, False` after five closed rows | DEFENSIVE — unreachable unless five re-asks were all closed |
| `elif e.state == CLAIMED` | EQUIVALENT — `observe_worker_start` guards the same condition itself |
| `max_epochs`, `max_epochs_per_obligation` defaults | DEFAULT VALUES — every gate passes an explicit budget; the defaults are policy, not behaviour |

### Audit record — G5 (independent adversarial audit + probe 41/54)
Five real defects the first 18 gates could not see, each now pinned:

| Finding | What it would have done |
|---|---|
| **HIGH** the claim was a version CAS, not a lease | a coordinator loading AFTER the claim passed its own CAS; two panes could run `/gsd-autonomous` in one root. Fixed with an exclusive expiring lock over load→decide→save; `store.save`/`epoch.save` also shared one temp filename |
| fingerprint hashed the whole dirty tree | in a shared checkout another pane's save minted "new information": retry refusal effectively off, and verify could spend the whole budget without the obligation ever being worked. Now revision + obligations + HEAD, plus a verify cap |
| leases began only at `claim()` | an epoch nobody claimed or executed waited for ever — WAIT every tick, no budget, no packet. Every epoch now leases from birth |
| `owner_queue.append` is idempotent across every status | a closed packet parked the Goal in AWAITING_OWNER with nothing pending. A closed row is re-asked under a fresh identity |
| CONVERGE left open epochs | nothing reconciles a CONVERGED Goal again, so a pane could keep working on finished work |

**Found by running the suites together, not alone:** `epoch_id` hashed a one-second
clock, so abandoning an unclaimed epoch and replanning within the same second minted
the same id; the save collided and escaped the tick after its side effects. A green
run and a red run differed only by whether the two calls straddled a second boundary.
Ids now carry a nonce, and `for_goal` tie-breaks on id because `prepared_at` alone is
not a total order.

**Process note:** the mutation probe rewrites its subject ON DISK per mutant, and the
auditor was reading the same file concurrently — it noticed, and its report says so.
That is this estate's own `T-A-BACKGROUND-MUTATION-RUN-IS-A-CONCURRENT-WRITER-001`,
re-created by me. Restoration was verified (270 lines, docstring and comments intact)
before anything was committed; the first restoration check was itself wrong, matching
the docstring against line 1, which is the shebang.

### Mutation record — G6
Probe first scored **14/24**. Real survivor closed: `or`→`and` on the epoch-binding
check. The receipt's own revision stamp was checked, but the EPOCH it cites was not
pinned to this Goal and revision — so an epoch prepared under revision 1 could carry
a receipt stamped revision 2 and satisfy the new target, and a foreign Goal's epoch
at the same revision could satisfy this one. Also pinned: a refusal is recorded on a
machine with no state directory. The remaining 8 survivors are EQUIVALENT: `frozen`
on two value objects, the "no gate ran" default (an empty gate yields no verdict
whatever the exit status), and hash/JSON formatting inside the receipt id and ledger.

**Finding B12 (for GSD X's owner, not changed here).** `closure.evaluate_transition`
checks that a verdict passed, not that it came from the gate the obligation names —
in GSD X `done_gate` is prose, and its own suite satisfies `done_gate="a real gate"`
with a `"pytest"` verdict. The spine therefore enforces gate identity at its own
boundary (`receipt.ingest`, gate `V-RCPT-WRONG-GATE-REFUSED`). Any other GSD X caller
remains exposed; whether `done_gate` should become an identifier is GSD X's decision.

### Mutation record — G4
Probe first scored **29/39**. Real survivors closed: a claimed session with no
findable transcript returned a bool a caller could read as "started" (the `True`
mutant survived); an ended or unclaimed epoch could report an expired lease, which
would have sent the reconciler to abandon finished work; fresh-machine directory
creation and version counting. Remaining 5, all classified:

| Survivor | Class | Why |
|---|---|---|
| epoch:60 `sort_keys` | EQUIVALENT | the fingerprint's dict literal has a fixed key order |
| epoch:61 `[:16]`→`[:17]` | EQUIVALENT | a longer prefix of the same hash is equally deterministic |
| epoch:83 `version` default | EQUIVALENT | `save` overwrites it from `expected_version` |
| epoch:130 `indent` | EQUIVALENT | JSON formatting only |
| epoch:184 `or`→`and` in the loader guard | DEFENSIVE-ONLY | `spec_from_file_location` returns a spec even for a missing file; a missing detector fails loudly in `exec_module` instead |

Design note: `/cpp-gsd-long`'s detector matches the command NAME only. What binds
a started run to THIS epoch is the claim — an act by id that unrelated pane work
cannot perform — not the command text.

### Mutation record — G3
The probe first scored **8/11**. One survivor was a REAL HOLE, worse than the mutant
that exposed it: removing `frozen=True` from `Verdict` survived because
`apply_verdict` trusted the verdict's `converged` flag. A caller flipping that flag
with `object.__setattr__` on an open verdict — digest unchanged — converged the Goal.
Fixed by recomputing the verdict at the point of effect; the token now authorises
nothing on its own. Gate `V-GOAL-CONV-TAMPERED-VERDICT-REFUSED` pins both layers.
Remaining 2 survivors (convergence:79, `sort_keys`/`ensure_ascii` inside the digest)
are EQUIVALENT: the same function computes both sides of the comparison over dicts
with a fixed insertion order.

Process note: this record was meant to land in `8b44d10`. The edit was denied (the
secret-scan hook timed out on a starved host and correctly refused to treat an
unscanned write as permitted), and the commit ran in the same batch as the edit —
a producer/consumer pair that must be sequential. It lands in the next commit.

### Mutation record — G1
Judged by the pre-existing `tools/mutation_probe.py` (auto-generated mutants), not
only by a hand-picked drill. The hand-picked drill first scored 6/6 against a suite
that the independent probe then scored **store 4/15, goal 18/24**. After closing the
real gaps: **store 11/15, goal 21/24.** Every remaining survivor is classified:

| Survivor | Class | Why |
|---|---|---|
| store:75, store:94 (`indent`, `ensure_ascii`, `sort_keys`) | EQUIVALENT | JSON formatting; the round-trip is byte-for-byte identical in meaning |
| goal:112 (`version` default 0→1) | EQUIVALENT | `store.save` overwrites `version` from `expected_version` |
| goal:104-105 (budget constants) | NOT YET REACHABLE | consumed first by the reconciler (G5), whose cap gates pin them |

Two instrument failures in this stage, both mine: a hostile-namespace gate that
counted `TypeError` as a refusal and went green 6/6 against code with no namespace
support; and a scratchpad drill that scored a CRASHED suite as a SURVIVED mutant.
