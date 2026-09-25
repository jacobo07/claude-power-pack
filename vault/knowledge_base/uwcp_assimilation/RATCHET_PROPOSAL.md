# Constitutive Baseline proposal -- `distributed_correctness` (PROPOSED, not promoted)

Status: PROPOSED 2026-09-25. Promotion is the Owner's, owed after UWCP Golden 01 reaches
REMOTE_REALITY (plan §7 X8; Owner answer Q5). Until then nothing below binds any project.

## Applicability predicate
Applies to a component that holds STATE which can RACE (two writers), REPLAY (a retried or late
message) or SPLIT (two holders of one authority): leases, locks, queues, epoch chains, spend or
quota ledgers, schedulers, distributed state, deployment coordination.
Does not apply to: stateless code, single-writer local files with no concurrent reader that acts,
documents, UI. A Markdown file needs no model.

## What completion requires when it applies
1. A named authority for every mutation, and a fence (monotonic generation) checked by every
   resource the component guards -- HR-FENCE-AT-RESOURCE-001.
2. UNKNOWN kept as its own answer end to end -- HR-UNKNOWN-NEVER-LICENSES-001.
3. Deadlines persisted as absolute values by their authority -- HR-CLOCK-OWNER-RESTART-001.
4. Where the concurrency core is finite: a TLA+ model whose target config passes with every action
   exercised, and whose predicted-defect configs fail on the named property AND mechanism
   (template: vault/specs/tla/UWCP.tla + tools/test_uwcp_tla.py).
5. A history check over independent sources (template: modules/history_check).
6. A mutation drill per guard, every restore SHA-256 verified (template: tools/lane_r_mutate.py).
7. Each claim labelled with its evidence class, never promoted across classes
   (modules/done_gate/strength_ladder.assess_evidence_class).

## Evidence that this is worth the ceremony (collected, not argued)
- The model found a defect path the author did not predict (Expire without stop evidence).
- Mutation drills and first runs found 11 blind spots across 7 gates (lease 4, history 1, trace 1,
  routing 1, bench 2, evidence class 1, corpus 1) (the lock-race blindness twice,
  a stale-fence case never presented, a tolerance wider than its error, a scanner seeing itself).
- Four independent systems (etcd, Temporal, Hazelcast, Redlock) converge on requirement 1.

## Supersession
A later version must not remove a requirement without a recorded reason and a replacement check.
