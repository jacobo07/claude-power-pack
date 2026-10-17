# Roadmap — experiment-admission (v1)

Read `REQUIREMENTS.md`, then `vault/specs/experiment-admission.md` (contracts, acceptance, budget).
Each phase ends with: tests run (foreground, bounded), pathspec-scoped micro-commit(s) in the worktree
`.claude/worktrees/experiment-admission`, `STATE.md` + `RESUMPTION_FILE.md` (this dir) updated with measured spend.
UNKNOWN / INCONCLUSIVE are never PASS. Prefer Sonnet subagents for build work; at most 2 in parallel.

## Phases

- [ ] **Phase 1: W1 Incident corpus**
- [ ] **Phase 2: W2a Premise ledger**
- [ ] **Phase 3: W2b Experiment admission + taxonomy + verdict authority**
- [ ] **Phase 4: W2c Breakers**
- [ ] **Phase 5: W2d Enforcement (TB lint, tb_local, capsule)**
- [ ] **Phase 6: W3 Historical replay**
- [ ] **Phase 7: W4 Spawn-contract archaeology + P39 canary**
- [ ] **Phase 8: W5 Cross-domain + negative control**
- [ ] **Phase 9: W6 Mutation drills**
- [ ] **Phase 10: W7 Knowledge, CBR, Construction Return**
- [ ] **Phase 11: W8 Red team + master done-gate**

## Phase Details

### Phase 1: W1 Incident corpus
**Depends on**: Nothing
- Build `vault/knowledge_base/experiment_admission/incident_tb_p25_p38.json` (one record per probe P25..P38 incl. P31b/P31c)
  from durable sources only (goal file, TB PREREG/RESULT docs, ledger). Fields:
  belief/target, premises with status at the time and the falsifying probe, instrument and its qualification,
  control and whether it was matched, PASS observable and whether the baseline could satisfy it, verdict,
  new precondition, measured cost with its source line (else UNKNOWN), fault classes.
- Measure the P31c-P38 coordinator cost from the session transcripts (`mission_spend` dedupe), or mark it UNKNOWN with the reason.
- Acceptance: every record cites a source line or commit; no invented number.

### Phase 2: W2a Premise ledger
**Depends on**: Phase 1
- Extend `modules/gsd_x/goal/evidence.py`: PROVEN/UNPROVEN/FALSIFIED/STALE/NA, evidence ref, invalidation, `depends_on`,
  stale closure propagation, and a FALSIFIED premise cannot be cited without new evidence. Keep existing callers green.
- Tests: V-PREM-* (positive, negative, stale closure, falsified reuse refused).

### Phase 3: W2b Experiment admission + taxonomy + verdict authority
**Depends on**: Phase 2
- New pure module (domain-free) per spec contract 2; reuse `strength_ladder` vocabulary and `applicability` block reasons.
- Proportionality: cost class decides which checks are mandatory; trivial deterministic + proven owner = NOT_REQUIRED.
- Kill switch `CPP_EXPERIMENT_ADMISSION=off`. Tests: V-EXA-*, each check driven from both poles.

### Phase 4: W2c Breakers
**Depends on**: Phase 3
- Extend `epoch.py` info_key/HYPOTHESES with causal-delta kinds; precondition-discovery breaker (cost-derived threshold)
  -> `planning_gate` escalation to BOUNDED_PLAN; instrument-failure breaker (no identical retry). Tests: V-BRK-*.

### Phase 5: W2d Enforcement (TB lint, tb_local, capsule)
**Depends on**: Phase 4
- TB repo (GEX44 writer clone, pathspec commits): `prereg_lint` calls PP admission (PP path via env or sibling path,
  fail-closed when unreadable for slot runs) and writes a receipt bound to the disc sha256. `probe_keys` reads post-dict
  assignments. `tb_local.cmd_run` refuses without a matching CLEAN receipt. The capsule run template binds `TB_DOLPHIN_LOG=1`.
  Refresh the capsule invalidator shas. Keep `test_prereg_lint` and `test_tb_local` green and add red cases.

### Phase 6: W3 Historical replay
**Depends on**: Phase 5
- Run admission over the corpus. Report per probe ADMIT/DOWNGRADE/REFUSE with reasons, the breaker trip point and
  P31c leverage rank. Savings graded MEASURED / LOWER-BOUND / PLAUSIBLE / UNKNOWN in `vault/audits/experiment-admission-replay-2026-10.md`.

### Phase 7: W4 Spawn-contract archaeology + P39 canary
**Depends on**: Phase 6
- Static comparison of every stock womprat spawn (level, state, primitive, locator form, script and where it lives, set,
  registration, gating pickup) vs the hub door line. Produce a contract table and live hypotheses, and derive P39 as the
  cheapest discriminating experiment.
- P39 through lint + admission + `tb_local` on ONE slot (ledger AUTHORIZED/CONSUMED, reconcile). A deliberately bad
  variant (identical retry or baseline-satisfiable observable) must be refused before any slot is spent.
- Frame verdicts by the coordinator at full resolution vs the matched control (P37/P38 frames).

### Phase 8: W5 Cross-domain + negative control
**Depends on**: Phase 7
- Two non-game historical cases from repo evidence (candidates: KSR Caddie PS_PLAYING flag vs scene transition; PP hook
  dispatcher fail-open / event never reached). Encode each as an admission input; show what admission would have
  required. A trivial deterministic edit returns NOT_REQUIRED.

### Phase 9: W6 Mutation drills
**Depends on**: Phase 8
- 8 mutants from spec acceptance; each must turn a named test red (use `tools/mutation_drill.py` if it applies; never mutate live-loaded files in place).

### Phase 10: W7 Knowledge, CBR, Construction Return
**Depends on**: Phase 9
- UKDL HR/PR/Trap entries (check for duplicates first), promote T-OBSERVABLE-NOT-DISCRIMINATING-001 from SHADOW,
  Knowledge Vault incident, CBR promotion scoped by transfer evidence, Construction Return, liveness reachability for the new module.

### Phase 11: W8 Red team + master done-gate
**Depends on**: Phase 10
- `oneshot-architect-auditor` with the 17 attack questions (spec). Fix material findings. Run every test suite named in
  the phases, record actual spend vs budget, write the session-close meta-analysis, then push the branch.
