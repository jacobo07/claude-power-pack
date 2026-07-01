# Parallel Mesh — UKDL / Doctrine entries (sealed 2026-07-01, SCS C66)

## T-PARALLEL-MESH-COLLISION-PREFIX-001 (trap)

The PM-02 `CollisionDetector` compares declared scopes by **exact normalized
path-token intersection**. It does NOT catch directory-vs-file prefix overlap:
a pane declaring `modules/` and a pane declaring `modules/x.py` are read as
disjoint, so both are admitted even though they truly collide.

**Workaround:** declare intents at **file granularity**, not directory. A pane
that will touch a whole directory should list the specific files it will edit.
**Fix (backlog):** a prefix-aware collision rule (`a == b` OR `a` is a path-prefix
of `b`). Not built in C66 to keep `scheduler.decide` self-contained and the
sealed CO-08 diff minimal.

## PR-BRAIN-BEFORE-REPO-READ-001 (protocol)

Before reading any directory or file of a repo in a session, verify the Repo
Brain (PM-01). `RepoBrainConsumer.get_or_generate(repo, scan_fn, ...)` is the
standard entry point: it returns the existing fresh brain with NO scan, or
generates once. Only cold-read the repo when the brain is missing or stale
(new HEAD / past TTL). Trusting the brain over live source for a SPECIFIC file
is forbidden — verify that file against source (HR-PREMISE-001); the brain
accelerates orientation, never substitutes verification.

## PR-BUS-BEFORE-REASON-001 (protocol)

Before reasoning about any topic, consult the Findings Bus (PM-03).
`RedundancyTax.reason_or_reuse(repo, topic, reason_fn, ...)` is the standard
entry point for any reasoning that another pane may already have done: a hit
returns the existing finding for 0 new tokens (`reason_fn` never runs); a miss
reasons once and publishes back. A published finding is a lead until its anchor
is verified — act on a stale finding only after re-checking source.

## PR-BUDGET-GATE-SECOND-001 (protocol)

The budget gate (PM-04) is the SECOND gate, after the scope-gate (PM-02).
Order is always **scope (PM-02) → budget (PM-04) → the sealed CO-00/CO-08
wrapper enforcement**. All three are advisory and fail-open: none blocks
execution if the Owner ignores the advisory. The one hard refusal in the whole
mesh is the CO-08 blunt cap for an UNDECLARED same-repo pane — and that is the
sealed fail-safe, not a mesh addition.

## Meta

All four are consequences of the C66 live build. The traps/protocols are honest
residuals surfaced at the done-gate (per the "no classified FAILs" doctrine), not
hidden. Cross-ref: `vault/knowledge_base/parallel_mesh/parallel_mesh_scs_c66.md`.
