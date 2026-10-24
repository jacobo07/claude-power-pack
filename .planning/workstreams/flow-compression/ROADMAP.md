# Roadmap — flow-compression (v1)

Read `REQUIREMENTS.md`, then `vault/specs/flow-compression.md` (contracts, acceptance, budget) and
`vault/plans/flow-compression-ownership-map.md` (who owns what; do NOT re-scan what it already states).
Work happens in the worktree `.claude/worktrees/flow-compression` (branch `gsd/flow-compression`). The live system
runs from the main checkout `C:\Users\User\.claude\skills\claude-power-pack` (branch feature/knowledge-acquisition,
shared with other panes): land each sealed phase there with a pathspec-scoped commit of exactly your files, after
backing up each live file, and verify `git log -1 --format=%s`.
Each phase ends with: tests run (foreground, bounded, `CPP_RESOURCE_ADMISSION=off` only inside test runs when host RAM
< 3000 MB), micro-commit(s), `STATE.md` + `RESUMPTION_FILE.md` (this dir) updated with measured spend.
UNKNOWN / INCONCLUSIVE are never PASS. Every new gate gets a mutation drill that must go red.

## Phases

- [ ] **Phase 1: S1 Rotation invariant — Production Reality**
- [ ] **Phase 2: S2 Arm preflight**
- [ ] **Phase 3: S3 Admission refusal loop + packet identity**
- [ ] **Phase 4: S4 Economic lease (variance is not a stop)**
- [ ] **Phase 5: S5 Terminal reconciliation**
- [ ] **Phase 6: S6 Blocker compiler + Owner boundary**
- [ ] **Phase 7: S7 Historical replay + champion/challenger**
- [ ] **Phase 8: S9 Knowledge Vault, UKDL, CBR, red team, master done-gate**

## Phase Details

### Phase 1: S1 Rotation invariant — Production Reality
**Depends on**: Nothing (code landed by the arming pane)
- Observe THIS mission's own epochs: `python tools/gsd_epoch.py epochs --mission <id>` and ledger rows
  `baseline_invariant_repaired` / `epoch_compacted` (`rotation_verdict`) / `launch_cause` CONTEXT_ROTATION.
- Measure rehydration cost (fresh launch -> first commit or .planning change, tokens and wall) vs a compaction
  cycle (tokens to next verified delta after compact_boundary) on comparable work; report champion/challenger.
- Acceptance: >= 1 real CONTEXT_ROTATION with trigger wall or economic_ceiling and state intact, numbers with source.
  If rotation loses economically, say so and propose the threshold change with evidence (do not hide it).

### Phase 2: S2 Arm preflight
**Depends on**: Phase 1
- One `arm_preflight()` in gsd_mission reusing gsd_status, mission_launch_gate.refusal, rollover custody,
  resource_admission, apply_rotation_invariant, authority presence; wire it into `arm` and `arm_chain`.
- Safe deterministic repair only when unambiguous; otherwise refuse naming the cause. Idempotent.
- Replay historical NO_PHASES / custody / low-memory / COPIA cases: prevented, moved earlier, legitimate.

### Phase 3: S3 Admission refusal loop + packet identity
**Depends on**: Phase 2
- Identical launch refusal with no causal delta -> backoff hold naming the unblock condition.
- Normalised packet digest (EOL/BOM); `mission_steward._r1` writes a new path, never the admitted file.
- DEFER autopsy on the 8 missions: false-defer rate.

### Phase 4: S4 Economic lease (variance is not a stop)
**Depends on**: Phase 3
- In `mission_spend.judge`: variance trip with verified semantic delta and remaining authority -> recompile.
- Semantic top-up renewal (fingerprint, never commit count), idempotent by seq; class calibration.
- Controls: productive mission crosses variance; nonproductive/runaway still stops; ceiling authoritative.

### Phase 5: S5 Terminal reconciliation
**Depends on**: Phase 4
- Dispose the 149 h (successor check). Close epochs on slim/supersede terminals in `gsd_epoch.epochs`.
- One receipt resolver; reconciler outcomes with positive, continuation and ambiguous controls; no false DONE.

### Phase 6: S6 Blocker compiler + Owner boundary
**Depends on**: Phase 5
- Taxonomy derived from the ledger; mission_blocked carries class, unblock condition, independent-work flag.
- Foreseeable Owner decisions batched at arm; no authority expansion.

### Phase 7: S7 Historical replay + champion/challenger
**Depends on**: Phase 6
- Replay harness over the ledger via plan_next() seams; champion vs challenger for S2-S6; mutants must fail.
- Report: mission-hours vs wall-clock vs critical path; avoidable idle before/after.

### Phase 8: S9 Knowledge Vault, UKDL, CBR, red team, master done-gate
**Depends on**: Phase 7
- KV incident per bug found; UKDL HR/PR/Traps without duplicating stronger laws; CBR only for proven items with
  fresh-inheritance proof; red team per the Owner prompt; S8 work-stealing activation predicate recorded.
