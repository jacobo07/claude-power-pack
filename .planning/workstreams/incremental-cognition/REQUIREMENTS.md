# Requirements: Incremental Cognition Program (incremental-cognition workstream)

Each requirement is satisfied when its pillar's ledger entry reaches a terminal that
`python tools/test_incremental_cognition_program.py --pillar <P>` prints PASS for. The pillar's frozen rule
(ledger `frozen.pillars`) decides WHICH terminal; this file does not.

Mission terms: incremental-cognition, context-rent, institutional-memoization, invalidation, cognitive-compiler,
baseline-ratchet.

## v1 Requirements

- [ ] **IC-A**: Mission relay in a shared checkout -- held missions relay without losing worktree commits.
- [ ] **IC-B**: Remote environment integrity -- GEX44 preflight; rules and hooks repaired by a repeatable deploy.
- [ ] **IC-C**: Persistent-failure retry classification -- auth-expired parks, never relaunches unchanged.
- [ ] **IC-D**: Silent-success hooks -- per-call additional-context rent measured; slice only if material.
- [ ] **IC-E**: Large-source read virtualization -- identical-version rereads replayed on KME-L.
- [ ] **IC-F**: GSD operational projection -- workflow-doc residency measured; handed to the GSD owner.
- [ ] **IC-G**: Derived / negative cognition reuse -- re-tested falsifications counted; one slice only if earned.
- [ ] **IC-H**: Proof reuse / singleflight / CCSE -- CE P, G consumed; KME verification share checked.
- [ ] **IC-I**: Startup floor and subagent bootstrap -- subagent floor measured, handed to CE B / SC B.
- [ ] **IC-J**: Context lifetime / rollover / zero-transcript -- CE D, E, I consumed (R2).
- [ ] **IC-K**: Cognitive cost regression -- floor gate by layer with a positive control.
- [ ] **IC-L**: Offline replay / lower bound / regret -- replay ranks live experiments; live runs need quota.
- [ ] **IC-M**: Optimizer, experiments, routing, events, reality model -- dispositions via CE Q, N, O, M (R2).
- [ ] **IC-N**: Closeout -- UKDL three levels, CBR, baseline, vault, institutional GC.

## Traceability

Checked by clause X2 of `tools/test_incremental_cognition_program.py`: the row of every closed pillar names its ledger
terminal, so "Complete" cannot hide how the obligation closed.

| Req | Pillar | Status |
|---|---|---|
| IC-A | Mission relay in a shared checkout | Pending |
| IC-B | Remote environment integrity | Pending |
| IC-C | Persistent-failure retry classification | Pending |
| IC-D | Silent-success hooks | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| IC-E | Large-source read virtualization | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| IC-F | GSD operational projection | Complete -- MERGED_INTO_EXISTING_OWNER |
| IC-G | Derived / negative cognition reuse | Complete -- RESEARCH_INSUFFICIENT_EVIDENCE |
| IC-H | Proof reuse / singleflight / CCSE | Complete -- RESEARCH_INSUFFICIENT_EVIDENCE |
| IC-I | Startup floor and subagent bootstrap | Pending |
| IC-J | Context lifetime / rollover / zero-transcript | Pending |
| IC-K | Cognitive cost regression | Pending |
| IC-L | Offline replay / lower bound / regret | Complete -- RESEARCH_INSUFFICIENT_EVIDENCE |
| IC-M | Optimizer, experiments, routing, events, reality model | Pending |
| IC-N | Closeout | Pending |
