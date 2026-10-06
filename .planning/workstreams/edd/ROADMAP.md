# Roadmap: GSD X Expectation-Driven Development (GEX44 workstream `edd`)

Binding contract: `.planning/workstreams/edd/source/MISSION_PROMPT.md` (Founder's verbatim mission, 2026-10-06).
Design input (NOT repository truth): `source/DATASET_EDD_1.md`. Iteration standard: `source/iteracion-avanzada-universal.txt`.
KobiiCraft evidence is NOT committed (it is another repo's source): `/home/kobii/missions/edd-stage/skyparty_pre_6f389020.tar.gz`,
`skyparty_post_83deab2f.tar.gz`, `skyparty_timeline.txt` -- absolute paths, read-only; wherever this file says `source/skyparty_*`
it means that directory. Extract into a scratch dir outside the repo, never into the tree.
Resume point: `.planning/workstreams/edd/RESUMPTION_FILE.md` -- read it FIRST in every session, update it after every sealed unit.

North star: DONE = evidence-backed convergence between intent, expected reality and observed reality, not "tasks complete".
EDD EXTENDS GSD X; it never builds a parallel Goal engine, obligation runtime, baseline system or verifier.

## Laptop pre-scan (2026-10-06, verified by reading code, extend in Phase 1)

| Mission concept | Existing owner | Status |
|---|---|---|
| Derived expectation (unstated, consequence-bearing requirement) | `modules/gsd_x/mission/obligation.py` (`operator`, `parents`, `consequence`, `evidence`, `closure_condition`; CANDIDATE/ACCEPTED/NOT_APPLICABLE/REJECTED/DEFERRED/SATISFIED/STALE) | IMPLEMENTED UNDER ANOTHER NAME |
| Materiality gate ("candidate is not authority") | same file | IMPLEMENTED |
| Proof oracle + closure that can say no | `modules/gsd_x/mission/closure.py` (`Verdict` with gate, exit, tree_hash, gate_pin; ALLOWED/REFUSED/UNJUDGEABLE) | IMPLEMENTED |
| Defect invalidation | `STALE` + `invalidated_by` | PARTIAL (representable; trigger from a defect unverified) |
| Goal spine / convergence | `modules/gsd_x/goal/*` | EXISTS, untraced |
| `modules/knowledge_acquisition/expectation.py` | corpus question evidence-kind classifier | NOT EDD -- do not build on it |

Hypothesis to verify, not assume: the gap is generative OPERATORS (semantic conservation families) feeding the
existing obligation pipeline, plus new closure-blocking classes (Self-Evolution Debt, Decision Frontier, Reference Frontier).

## Founder decisions already taken (persist as decision provenance in Phase 1)

- D-01 (2026-10-06): execution runs on GEX44, not the laptop (laptop at 4% free RAM).
- D-02 (2026-10-06): promotion scope -- proven operators become the GSD X DEFAULT, auto-inherited by every GSD X Goal.
  Promotion to the UNIVERSAL baseline (`~/.claude/CLAUDE.md`, UKDL HARD RULE, `~/.claude/rules/`) waits for the Founder's
  explicit y: write it as a PROPOSED Decision Packet, never apply it.

## Operating constraints (every phase)

- Clone `~/missions/edd`, branch `mission/edd`. Commit by explicit pathspec, micro-commits, causal messages. The commits
  ARE the hand-back (laptop fetches the branch). Never push to main. Never touch `/home/kobii/.claude/skills/claude-power-pack`
  (live install) or any other mission directory.
- Peer branches also edit `modules/gsd_x` (worktrees gsd-x, goal-spine, ucr-cif on the laptop). Prefer NEW files and small,
  additive edits to existing gsd_x files so the hand-back merges; never reformat or move existing gsd_x code.
- `tools/gsd_mission.py` and the Ralph supervisor are peer-owned: read, never edit.
- Model calls only on this host's subscription quota. If `ANTHROPIC_API_KEY` is set, STOP that phase, record BLOCKED.
- Never edit `~/.claude/settings.json`, `~/.claude/rules/`, `~/.claude/CLAUDE.md` or credentials. Items that need the
  laptop's install or the KobiiCraft live server are marked LAPTOP-ONLY / BLOCKED_BY_EXTERNAL_CONDITION, and every
  independent lane continues.
- Founder questions: the Founder is NOT reachable mid-run. A genuinely Founder-owned decision is written as a Decision
  Packet (decision, scope, evidence gathered, recommendation, alternatives + consequences, blocking?) into
  `.planning/workstreams/edd/DECISION_FRONTIER.md`; a BLOCKING one marks only its lane BLOCKED_BY_HUMAN_AUTHORITY.
  Engineering-resolvable questions are never escalated. This file is itself the first consumer of the Decision Frontier.
- Corpus partition (evaluation-corpus-governance): `source/skyparty_post_*`, the dataset's descriptions of what the Founder
  discovered, and `source/skyparty_timeline.txt` are the ANSWER side. The blind-replay INPUT is `source/skyparty_pre_6f389020.tar.gz`
  plus pre-incident intent only. Derivation code must never read the answer side. The worker that writes the operators has
  read the answers, so blind replay alone cannot prove generalisation: novel holdouts (renamed, cross-domain) are authored
  and SEALED (hash committed) BEFORE operator work begins, and contamination is stated beside every replay number.
- Report only measured results with the command that produced them. UNKNOWN / INCONCLUSIVE / BLOCKED are never PASS.
- Two identical failures of one call shape = pivot. Do not end a turn waiting; at the wall commit, update
  RESUMPTION_FILE.md, end with `HANDOFF NOTE:`.

## Phases

- [ ] **Phase 1: Reality scan + ownership matrix + spec** - every dataset concept classified against traced producers/consumers; spec with `covers:`
- [ ] **Phase 2: Gold sets + benchmark before operators** - SkyParty gold set, sealed cross-domain holdouts, negative controls, baseline score of today's machinery
- [ ] **Phase 3: Goal world model + conservation operators** - smallest repo-native semantic model; operators emit obligations through the existing pipeline; blind replay + mutation
- [ ] **Phase 4: Self-Evolution Debt + defect propagation** - defect -> product+factory obligations, Earliest Preventable Point, STALE propagation, closure refuses NEVER_CONSIDERED
- [ ] **Phase 5: Decision Frontier + Reference Frontier** - closure-blocking classes, Decision Packets persisted and recompiled, reference dispositions
- [ ] **Phase 6: Transfer + baseline ratchet + knowledge** - cross-domain proof, GSD X default inheritance, UKDL 3 levels, Knowledge Vault incidents
- [ ] **Phase 7: Done gate + meta-analysis + handoff** - every required closure judged, regression intact, final handoff

## Phase Details

### Phase 1: Reality scan + ownership matrix + spec
**Goal**: Replace the laptop pre-scan with a traced ownership matrix and a binding spec.
**Depends on**: Nothing
**Requirements**: EDD-01
**Success Criteria**:
  1. `.planning/workstreams/edd/OWNERSHIP_MATRIX.md` classifies every dataset concept as ALREADY IMPLEMENTED / UNDER ANOTHER
     NAME / PARTIAL / DOCUMENTED ONLY / DATASET ONLY / REGISTERED-UNREACHABLE / REACHABLE-NOT-COMPLETION-EFFECTIVE / NEW, each
     with file:line of the producer AND consumer it traced (gsd_x mission+goal, UCR-CIF / Constitutive Baseline Ratchet,
     Production Reality, sleepless_qa, mutation ratchet, UKDL, Knowledge Vault, D2A, hard_rules, liveness).
  2. Every NEW row passes the HR-NOVELTY-001 13-question proof or is reclassified.
  3. `vault/specs/edd.md` exists with `covers: [edd, expectation-driven-development, semantic-conservation, self-evolution-debt, decision-frontier, reference-frontier]`,
     PRD + architecture + acceptance criteria + rollback, and records conflicts between the iteration standard, CLAUDE.md, UKDL and the mission.
  4. D-01/D-02 persisted as decision provenance in the canonical decision owner the scan finds (not only in this file).

### Phase 2: Gold sets + benchmark before operators
**Goal**: Measure today's machinery before changing it, with sets it cannot have been tuned on.
**Depends on**: Phase 1
**Requirements**: EDD-02
**Success Criteria**:
  1. SkyParty gold set (answer side): the expectation escapes (pregame containment, void/elimination continuation, spectator
     state, state-owned controls/projection, return-state restoration, first-release protection boundary, cleanup, second-run
     cleanliness, reconnect/restart, player-observable truth) each with source evidence and Earliest Preventable Point.
  2. >= 3 non-Minecraft holdout domains (e.g. payment/checkout, background job, SaaS onboarding) + >= 1 renamed-Minecraft
     holdout, plus negative controls (Founder intent overrides common expectation, non-applicable lifecycle, intentionally
     persistent temporary state, rejected reference advantage, evidence-answerable question that must NOT reach Founder).
     Holdout files hashed and the hashes committed BEFORE any Phase 3 commit.
  3. A V-EDD-BENCH runner reports separately: material recall, critical recall, precision, false-obligation rate,
     Founder-escalation precision. Today's machinery scored and recorded as the BEFORE baseline.

### Phase 3: Goal world model + conservation operators
**Goal**: Sparse intent -> expected semantic model -> derived obligations through the EXISTING obligation pipeline.
**Depends on**: Phase 2
**Requirements**: EDD-03
**Success Criteria**:
  1. Smallest repo-native model (actors, states, transitions, ownership, temporary states, projections, termination,
     restoration) built only where applicable; no universal megagraph.
  2. Conservation operators (purpose, authority, ownership, projection, temporal boundary, termination, restoration,
     cardinality/exactly-once) emit `Obligation`s with consequence + provenance; materiality gate still dispositions them.
  3. Producer -> consumer -> closure demonstrated end to end: an ACCEPTED derived obligation without proof makes closure
     REFUSE; a passing Verdict closes it. Semantic Preservation: a material parent contract that is silently dropped is detected.
  4. Blind replay on `skyparty_pre` reported with contamination stated; holdouts + negative controls scored vs Phase 2 BEFORE.
  5. Mutation drill per operator (`tools/mutation_drill.py` style, isolated copy): disabling it turns its benchmark subset red; restoring turns it green.
  6. `python modules/liveness/reachability.py` exit 0 for every new module.

### Phase 4: Self-Evolution Debt + defect propagation
**Goal**: A validated defect cannot close as merely "fixed".
**Depends on**: Phase 3
**Requirements**: EDD-04
**Success Criteria**:
  1. A defect record yields a PRODUCT obligation and a FACTORY obligation with Earliest Preventable Point; closure refuses
     a factory obligation with no disposition (NEVER_CONSIDERED is not terminal).
  2. Impact analysis marks only causally affected SATISFIED obligations STALE; a test proves an unaffected one stays SATISFIED.
  3. Forward immunity: a capability revision recompiles the active goal's remaining obligations; revision activation is an
     explicit boundary and the candidate is evaluated on holdouts it was not derived from (no self-approval).
  4. Every defect found during this mission is run through this path (dogfood) and recorded.

### Phase 5: Decision Frontier + Reference Frontier
**Goal**: Unresolved Founder-owned decisions and material reference deficits block closure; answers recompile the goal.
**Depends on**: Phase 3
**Requirements**: EDD-05
**Success Criteria**:
  1. Decision Packets are a persisted class; a blocking open packet makes closure refuse; an answer with provenance and scope
     recompiles affected obligations and invalidates stale certificates; non-blocking optional items defer explicitly.
  2. An engineering-resolvable unknown is routed to evidence, not the Founder (negative control green).
  3. Reference dispositions (MATCHED / SURPASSED / SUPERSEDED / NOT_APPLICABLE / REJECTED_WITH_REASON / BLOCKED); NOT_CONSIDERED
     on a material advantage refuses closure; SURPASSED requires a named oracle.

### Phase 6: Transfer + baseline ratchet + knowledge
**Goal**: Proven learning reaches future goals automatically, at the narrowest correct scope.
**Depends on**: Phases 4, 5
**Requirements**: EDD-06
**Success Criteria**:
  1. Operators that pass >= 3 non-Minecraft holdouts become the GSD X default: a NEW goal created after the change inherits
     them without being told (test proves it); operators failing transfer stay family-scoped.
  2. Constitutive Baseline Ratchet disposition recorded per learning (provenance, scope, version, negative controls).
  3. UKDL: Hard Rules / Process Rules / Traps distilled (no raw prose, no duplicates); Knowledge Vault incident entries for
     every defect found. Universal promotions written as PROPOSED Decision Packets only (D-02).

### Phase 7: Done gate + meta-analysis + handoff
**Goal**: Judge every required closure with observed evidence.
**Depends on**: Phase 6
**Requirements**: EDD-07
**Success Criteria**:
  1. Each closure in MISSION_PROMPT.md "DONE GATE -- REQUIRED CLOSURES" has a verdict with its command/evidence; Production
     Reality for the KobiiCraft live server is LAPTOP-ONLY and stated as such, never as PASS.
  2. Existing gsd_x tests and every touched suite pass (output to a log; summary + failing lines recorded).
  3. Meta-analysis fed into owning systems; FINAL HANDOFF section of MISSION_PROMPT.md written to
     `.planning/workstreams/edd/HANDOFF.md`; RESUMPTION_FILE.md final.
