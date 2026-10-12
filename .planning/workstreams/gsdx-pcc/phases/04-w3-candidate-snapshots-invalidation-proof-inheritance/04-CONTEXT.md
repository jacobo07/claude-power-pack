# Phase 4: W3 Candidate snapshots, invalidation, proof inheritance - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Mode:** Auto (UNATTENDED, WU-P4; discuss skipped; every gray area decided here with a one-line reason)
**Mission:** m-84c6e0072a10 follow-on (packet WU-P4, Owner "aprobar 75M" 2026-10-12)

<domain>
## Phase Boundary

ROADMAP Phase 4: proofs bind to candidate snapshots by causal fingerprint; inheritance is explicit (`proof.inherited`
event) and never applies to fresh-required evidence; UNKNOWN impact forces FULL. Requirements D01 D10 D11 D12 D13 D14
D20 D23 D24 D39 D45 R02, plus R12 (DENOMINATOR assigns it to Phase 4). Depends on Phase 3.

Must not regress: `GSDX_PCC_REPLAY_PASS=28/28`, `GSDX_PCC_SEMANTICS_PASS=48/48` (Phase 2), `GSDX_FRONTIER_PASS=40/40`
(Phase 3), the 12 pre-existing goal suites. `judge.py` is NOT touched (S9: VALIDATE is Phase 5), so closure stays
necessary-not-sufficient and every inherited claim is still replayed by the judge.

Out of scope: Phase 5+, the root milestone, the main checkout, `~/.claude`, any push, any live store write.

D25 / D26 (executed speculation, racing): DENOMINATOR.md assigns them to Phase **3** (column "3"); the rows' note says
"executed ... closed by Phase 4" but the ROADMAP Phase 4 requirement list omits them. Packet rule: Phase 4 work only
if the DENOMINATOR assigns it. Decision: **left OPEN, not built**; stated in the receipt. Reason: nothing in the sweep
dispatches cognitive hypotheses, so executing speculation would be scaffold with no consumer (Reality Contract).
Candidate snapshots (this phase) are the substrate racing needs, which is recorded as the unblock.
</domain>

<decisions>
## Implementation Decisions

### Candidate snapshot (D23, R02) -- on git objects, no copy store
- New pure-ish module `modules/gsd_x/goal/candidate.py`: `snapshot(root, paths)` builds a tree object with a
  **temporary index** (`GIT_INDEX_FILE` in a temp dir, `git add -A -- <paths>`, `git write-tree`), then deletes the
  temp index. The tree oid is the candidate; objects live in the repo's own object database. No worktree, ref or
  branch is touched. Reason: spec D23 "BUILD on git objects"; a parallel copy store is forbidden by the packet.
- The candidate id stays a `tree_id`-shaped string for legacy callers (S1). The snapshot adds `snap:<oid>` only inside
  the new `candidate.promoted` event; no legacy field changes meaning.
- Not a git repo, git failing, or any path outside the root -> `snapshot` returns `unknown:` (never raises), so
  every consumer falls to the whole-tree/FULL path (S1, S4, Unknown Escalates).
- `candidate.promoted` (frozen row, owner phase 4) lands as code in `proof.py` with a real projection
  (`ledger.promoted`) and the frozen-table row moves to the landed table in the same commit, with the V-PCC-VOCAB
  gate updated to read both tables. Reason: S7 says a type must be declared before use; Reality Contract bars a
  constant with no projection, and `ledger.promoted` is consumed by drift detection below.

### Causal binding and the producer (D12, D13)
- `proof.produced` is appended in `sweep._apply_verdicts` immediately after a **successful** `cv.satisfy`, never
  before and never when satisfy refused. Reason: S3 "only from the gate receipt path"; a produced proof for a refused
  verdict would be a certificate for nothing.
- Payload (additive keys beyond the five required): `premises` {claim, revision, gate_pin, fingerprint, environment,
  policy}, `freshness_class`, `env_deps`, `contract_hash`. Binding = `proof.binding(tree, fingerprint)`: `causal`
  scheme only when the effective contract declares `causal_paths` AND the fingerprint is not `unknown:`; otherwise
  the whole-tree binding (S1). A certificate id is `cert:<claim_id>:<seq>`.
- **Candidate changes under verification**: the gate provider already returns `tree_before` (at dispatch) and
  `tree_after` (at harvest) in the receipt. `proof.produced` is written ONLY when they are equal AND the causal
  fingerprint taken at dispatch equals the one taken at harvest. A mismatch writes **no** certificate and appends a
  `proof.invalidated` for any live certificate of that claim, reason "candidate moved under verification". The legacy
  `obligation.satisfied` path is NOT changed (a test-writing gate may legitimately dirty the tree; refusing there
  would change legacy output, D43). Reason: the new axis may be stricter than the old one; the old one stays byte-equal.

### Inheritance (D01, D14, D45) -- reconciler is the only producer
- New module `modules/gsd_x/goal/inherit.py`:
  - `observe_current(root, state, obligation, contract)` -> current premise values (impure: reads the worktree; called
    only by the sweep, never by `decide`).
  - `plan(state, candidate, current, now)` -> pure: per claim `{action: INHERIT | INVALIDATE | RUN, reason}`.
  - `apply(log, state, plan, actor)` -> appends `proof.inherited` / `proof.invalidated` through `append_pcc`.
- The sweep runs observe -> plan -> apply **before** `decide_now`, only when `inheritance_enabled()`. Reason: keeps
  `decide`/`Context` signatures unchanged (V-PCC-DECIDE-SIG pins the field tuples, test_gsd_x_goal_pcc_replay.py:878).
- **Consumption stays pure**: `goal_closure(state, tree, open_epochs=None, inherited=frozenset())` and
  `reconcile._needs_a_gate_here` gain an `inherited` argument computed by `inherit.inherited_ids(state, tree)`. With
  no PCC events or the switch off the set is empty, so every legacy output is identical (replay suite is the proof).
- `inherited_ids` re-derives from the log every premise the log can supply (claim_id from the current obligation,
  revision, gate pin, policy constant, freshness class) and takes only fingerprint and environment from the
  reconciler's recorded observation. A `proof.inherited` event whose recorded premises disagree with the log-derived
  ones is ignored (state UNKNOWN). Reason: S3 "the event is a claim"; pure code cannot read the worktree, and the
  judge still replays everything in this phase.
- **FRESH_REQUIRED, UNKNOWN freshness, `inheritability: never` (the legacy default), REALITY plane, any risk tag:
  never inherited** (D14, D39). The legacy one-element contract is `never`, so an obligation with no typed
  contract is never inherited: Phase 4 changes behaviour only for claims that opt in through `obligation.contract`.
  Reason: opt-in keeps the scheduled sweep behaviour-identical on merge.
- Fresh proof islands (D39): `inherit.fresh_islands(state)` = claims forced to run (FRESH_REQUIRED / REALITY / risk
  tags); the solver output lists them and the sweep never skips one.

### Minimal sufficient verification (D20)
- `inherit.verification_set(state, candidate, current, now)` -> `{"run": [...], "inherit": [...], "full": bool,
  "reasons": {...}}`. Rule: a claim is skipped only if its state is INHERITED (or FRESH at this tree); every other
  state (STALE, UNKNOWN, no certificate, no contract, switch off) RUNS. `full` is true when any run claim has an
  `unknown:` fingerprint or no declared `causal_paths`, i.e. the impact of the change on it could not be mapped.
  Reason: UNKNOWN -> FULL; the solver can only remove work with positive evidence.
- The sweep reports the set; the existing `_needs_a_gate_here` path consumes the same decision through
  `inherited_ids`, so there is one source of truth (no second scheduler).

### Proof algebra (D11) -- minimal, with the honest limit
- `proof.combine_states(op, states, k=None)` for AND / OR / SEQ / QUORUM over element states
  {FRESH, INHERITED, other}: UNKNOWN or STALE never satisfies; OR with only unknown elements -> UNKNOWN; SEQ stops at
  the first non-satisfied element; QUORUM needs k satisfied. Pure, with truth-table gates.
- `freshness_class` for `combine != AND` stays UNKNOWN (V-PCC-CONTRACT-COMBINE-UNKNOWN is pinned), so a non-AND claim
  is always run in full. Per-element execution needs element-level receipts from a multi-command gate provider that
  does not exist. D11 is therefore dispositioned **PARTIAL** (algebra built and gated, consumed by the solver's
  `reasons`, element-level execution open for Phase 5/7), not DONE.

### R12 (unknown: tree equality) -- RED first
- `convergence.goal_closure` (line 350) and `reconcile._needs_a_gate_here` (line 115) compare tree strings with `!=`.
  Fix: a tree id that starts with `unknown:` never counts as equal to anything, including itself. RED: a log whose
  verdict tree and the candidate are both `unknown:not-a-git-tree` closes today; after the fix it blocks and the gate
  is re-run. This is a deliberate legacy-behaviour change, owned by DENOMINATOR R12 and Phase 2 STATE decision 3.

### Continuous verification (D24)
- Phase 4 lands the substrate only: `candidate.drift(promoted_event, current_snapshot)` and the
  candidate-moved-under-verification rule. A watcher that re-verifies on every promoted candidate and its measured
  benefit belong to Phase 9. D24 stays OPEN in DENOMINATOR with the Phase 4 part noted.

### Kill switches and engine identity
- `GSDX_PROOF_INHERITANCE` (existing, S10) gates the sweep's observe/plan/apply and `inherited_ids`. Off = legacy.
  Production of `proof.produced` is also gated by it, so off means no new event is ever written.
- New `.py` files under `goal/` change `engine_identity` (S14 G17): `record-gates` is not re-run from this worktree.
- Liveness: `candidate.py` and `inherit.py` are imported by `sweep.py` in the same commit that creates them
  (wired, not declared).

### RED list (verbatim; each driven red, then green, then mutation-drilled)
- false reuse after a relevant change
- UNKNOWN treated as clean
- fresh-required proof inherited
- omitted proof without an INHERITED event
- candidate changes under verification
(plus R12: two `unknown:` trees compared equal)

### Claude's discretion
Gate names (V-INH-*, V-CAND-*), log file names, which extra mutants beyond the RED list. Suites:
`tools/test_gsd_x_goal_invalidation.py` (summary `GSDX_INVALIDATION_PASS`, the ROADMAP-named suite) and
`tools/test_gsd_x_goal_certificate.py` (`GSDX_CERTIFICATE_PASS`).
</decisions>

<canonical_refs>
- `vault/specs/gsdx-proof-conserving-convergence.md` S1 S2 S3 S4 S5 S6 S7 S10 S12 S14
- `modules/gsd_x/goal/{proof,git_state,convergence,reconcile,sweep,frontier}.py`, `providers/gate.py:143,187`
- Phase 2: `02-VERIFICATION.md`; Phase 3: `03-VERIFICATION.md`
- dataset sections 9-14, 18, 21-23, 38, 44 (open only those)
</canonical_refs>
