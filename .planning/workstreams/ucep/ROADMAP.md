# Roadmap: UCEP — No feature ships as a naked verb

Plan of record: `vault/plans/ucep-naked-verb-2026-10-02.md` (ULTRA-PLAN; Owner answers 2026-10-02 recorded there).
Audit: `vault/plans/ucep-naked-verb-2026-10-02.audit.md` (18 gaps; each fix is injected below as `[Gn]`).

Principle: feature completeness is compiled from repo reality and accumulated maturity. Applicability precedes
inheritance; required surfaces close with evidence; non-applicable surfaces are excluded with a reason; proven
reusable maturity ratchets the baseline. UNKNOWN / UNJUDGED / DELEGATED / DEFERRED are never PASS.

## Operating constraints (every phase)

- Repo: `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`. Another session
  is live in this checkout. Prefer NEW files. Every commit is pathspec-scoped (`git commit -F <msgfile> -- <paths>`),
  made within minutes of the edit, after reading the diff hunk headers of every shared file. Never stage or commit a
  path this mission did not write. After each commit verify `git log -1 --format=%s` matches the message file.
- Git: `& 'C:\Program Files\Git\cmd\git.exe' -C <repo> ...`. Python:
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `$env:PYTHONIOENCODING='utf-8'`.
- Read-only / out of scope: `ucr-cif/construction`, `goal-spine/v1`, `modules/sdd_os/*`, every path dirty from the
  other session at phase start (re-read `git status --short` first), root `.planning/STATE.md`,
  `vault/knowledge_base/ukdl-universal.md` and `vault/audits/liveness_report.md` [G14].
- B0 and web_surface B1 generation files are byte-immutable; history is projected, never rewritten.
- KobiiCraft Core Files (`C:\Users\User\Desktop\Cursor Projects\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files`)
  and InfinityOps (`C:\Users\User\Desktop\Cursor Projects\InfinityOps`): write ONLY in a dedicated worktree on branch
  `ucep/<slice>`, scoped commits, never push, no live server, no deploy [G17]. KSR: read-only always.
- Promotions: family/archetype scope may auto-admit when the full evidence bar is met; cross-family, universal or
  constitutional scope stops at PENDING_OWNER — record it and continue.
- Enforcement REPORT-ONLY until Phase 8's gate passes. Kill switch `CPP_CAPABILITY_GATE` accepts the same tokens
  as `CPP_FAMILY_BASELINES` (`off`/`0`/`false`) via the same parse helper; it silences the envelope block and the
  Stop judge; `CPP_FAMILY_BASELINES` keeps governing `family_block` [G12].
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/` or credentials.
  A live-hook change is an OWNER STEP: write it to `vault/OWNER_QUEUE.md`-style handoff in the phase EVIDENCE [G3].
- Liveness: each new module is declared PLANNED with an owner-queue line in the SAME commit that creates it, and
  undeclared when wired. Never run `reachability.py --baseline` in this shared tree [G11].
- Oracles: narrow (the phase's own test files), bracketed by the sorted dirty-path SET before/after. Tests write to a
  hermetic HOME (pattern `tools/test_family_injection.py:79-84`); no test row reaches the production ledger [G13].
- Never ask the Owner mid-run: write the blocker into the phase EVIDENCE.md, mark the phase BLOCKED/UNJUDGED, continue.
- Every phase ends with EVIDENCE.md: commands, exit codes, observed output, Production Reality verdict
  (PROVEN / OBSERVED / UNJUDGED / BLOCKED — never upgraded).

## Phases

- [x] **Phase 1: Baseline integrity repair** - the chain is green and ratchet/gate holes are closed before new authority is built (completed 2026-10-03)
- [ ] **Phase 2: Capability subject and archetypes** - traits from repo structure (cached) + intent; archetype orthogonal to family
- [ ] **Phase 3: Promotion admission and scope contract** - every entry added after the cutover carries an admission record
- [ ] **Phase 4: Archetype maturity generations** - three archetype B0 generations on a second tower axis, admitted
- [ ] **Phase 5: Envelope compiler** - subject -> surfaces as Obligations with dispositions, reasons, consequences
- [ ] **Phase 6: Live delivery and report-only closure** - envelope beside family_block within budget; Stop judge recorded
- [ ] **Phase 7: Proving grounds and cross-context transfer** - KC + InfinityOps worktrees, KSR read-only
- [ ] **Phase 8: Falsification, live promotion, inheritance** - 12 challenges, severing drill red, admitted promotion inherited
- [ ] **Phase 9: Knowledge, metrics and handoff** - incidents, UKDL candidates, metrics with real denominators, RESUMPTION

## Phase Details

### Phase 1: Baseline integrity repair

**Goal**: The baseline chain is green and the known ratchet/gate escape routes are closed.
**Depends on**: Nothing
**Success Criteria**:

  1. `ratchet.reanchor(family, {id: new_origin}, reason, authority)` writes ONE generation per family with
     `changes[id].kind="REANCHORED"`, keeps ids, refuses unless the new origin's `verify_origin == VERIFIED` [G1].
     The 9 QUOTE_MISSING entries are re-anchored to PP `skills/<name>/SKILL.md` (or reverted with a reason if the
     rule text is gone) -> `persistent_state/B1.json`, `wii_homebrew/B1.json`.
  2. `ratchet.diff` covers `why`, `origin`, `class`, `propagation_scope`; an unanchored child is not ok; authority
     comes from an allowlist. Probe attacks H1/H2/H3b go red; their controls stay green.
  3. Donegate: N/A needs a reason from a closed vocabulary and an N/A-share cap; `test:` checks are never executed on
     any hook path and report UNJUDGED, which is counted separately from VIOLATED [G13]. Probe H5/H6 no longer pass.
  4. `test_tower_ratchet.py` and `test_baseline_generations.py` discover subjects by walking `BASELINES_DIR`
     (nested axes included) with a population floor, not a hardcoded family tuple [G9].
  5. `python tools/test_baseline_generations.py` 16/16+, `test_tower_ratchet.py`, `test_tower_donegate.py`,
     `test_family_baselines.py` all PASS; B0 and web_surface B1 sha256 unchanged (recorded before/after).
**Plans:** 5/5 plans complete
Plans:

- [x] 01-01-PLAN.md — (wave 1) LF-pin baseline generations (tracer: V-TRAT-REAL-CHAINS green) + RED harness for H1/H2/H3b
- [x] 01-02-PLAN.md — (wave 1) donegate exits: `test:` -> UNJUDGED never run, N/A closed vocabulary + 30% cap (H5/H6)
- [x] 01-03-PLAN.md — (wave 2) ratchet hardening: unanchored not ok, diff why/origin/class/scope, authority allowlist
- [x] 01-04-PLAN.md — (wave 3) `ratchet.reanchor` + CLI; re-anchor 9 entries -> persistent_state/B1, wii_homebrew/B1
- [x] 01-05-PLAN.md — (wave 4) `discover_subjects` replaces hardcoded families; phase gate; 01-EVIDENCE.md

### Phase 2: Capability subject and archetypes

**Goal**: A capability subject (traits + archetypes) resolved from repo reality first, intent second.
**Depends on**: Phase 1
**Success Criteria**:

  1. `modules/capability_runtime/archetypes.py`: traits (persistent, multi_actor, bulk, destructive, distributed,
     external_effect, scheduled, money, policy_layers, ui) and archetypes as trait conjunctions; family and archetype
     are independent outputs.
  2. Structural traits come from a cache keyed by repo root + cheap fingerprint, computed OFF the prompt path; the
     prompt path only reads it [G4]. Cache miss -> traits UNJUDGED, never absent.
  3. Intent-only traits carry fact state EXTRACTED and can yield at most CONDITIONAL, never REQUIRED [G16].
  4. `tools/test_capability_archetypes.py`: vocabulary-overlap negative control, intent-only control, trait-transition
     (ephemeral->persistent, local->distributed) recompiles differently, positive controls per archetype.
**Plans:** 5/5 plans executed
Plans:

- [x] 02-01-PLAN.md — (wave 1) tracer: off-path trait cache -> read-only reader -> WORLD_MUTATION end to end; vocabulary (ten traits, three single-segment archetypes, Strength, N/A bridge); PLANNED registry rows + Owner queue
- [x] 02-02-PLAN.md — (wave 2) single `ceiling()` [G16]: intent-only <= CONDITIONAL (EXTRACTED); bilingual verb-object intent; demoters; orthogonality + vocabulary-overlap negative control; drills
- [x] 02-03-PLAN.md — (wave 3) producer detectors: declared-dependency parsers (8 ecosystems), markers, STRONG/WEAK, entitlement (truncated/budget/unreadable/blind -> UNJUDGED); e2e positives per archetype
- [x] 02-04-PLAN.md — (wave 4) reader contract [G4]: fingerprint + evidence re-stat + age staleness, malformed refusal, key normalization, zero-walk proof, producer skip; drills; `tools/capability_traits.py` CLI
- [x] 02-05-PLAN.md — (wave 5) subject signature + modifiers (transitions recompile differently), UNJUDGED causes reachable, real-repo poles; phase gate; 02-EVIDENCE.md

### Phase 3: Promotion admission and scope contract

**Goal**: Constitutive admission is evidence-gated and enforced by the chain, not by convention.
**Depends on**: Phase 1
**Success Criteria**:

  1. `modules/tower/admission.py`: origin VERIFIED and not under a worktree or a rules stub [G15]; a runnable check or
     an explicit MANUAL do-confirm; evidence ref (commit/incident); production evidence ref; negative applicability;
     counterfactual verdict (instance/product/archetype/constitutive); status provisional.
  2. Scope is DERIVED from the write location + applicability; a declared scope narrower than the derived one is
     refused [G6]. family/archetype -> AUTO_ADMITTED; cross-family/universal/constitutive -> PENDING_OWNER.
  3. `ratchet.promote` and archetype B0 creation both require an admission record [G5]; `verify_chain` refuses any
     entry added at generation >= cutover without one (gen <= 1 grandfathered).
  4. `baselines.propagation_scope(entry, gen)` projects gen <= 1 entries as LEGACY_UNSPECIFIED; C/D gain no meaning.
  5. Tests: a bad origin, `glob:**`, a self-declared narrow scope and an unadmitted raw `write_generation` are all
     refused; a fully evidenced archetype entry is admitted (positive control).

### Phase 4: Archetype maturity generations

**Goal**: Three materially distinct archetypes carry admitted B0 maturity on a second tower axis.
**Depends on**: Phases 2, 3
**Success Criteria**:

  1. `vault/tower/archetypes/<ID>.json` definitions + `vault/tower/baselines/archetype/<ID>/B0.json` through
     admission, for WORLD_MUTATION/persistent-state (donor KC world_persistence_gate), EXTERNAL_EFFECT (donor
     InfinityOps effect-keeps-http-status, generalized), BACKGROUND_JOB (donor PP gsd sweep lease/heartbeat/bounded
     stages + KC stale-lock reclaim). Archetypes may change if evidence favours better donors; record why.
  2. Every entry: surface, consequence, origin+quote (VERIFIED, main-checkout path), check or MANUAL, negative
     applicability, propagation_scope=archetype.
  3. `verify_chain` ok for each; the discovered-subject gates (Phase 1.4) include them.

### Phase 5: Envelope compiler

**Goal**: The capability envelope is compiled as derived Obligations and closes only on evidence.
**Depends on**: Phase 4
**Success Criteria**:

  1. `modules/gsd_x/mission/envelope.py`: subject -> archetype + family entries -> causally applicable UKDL traps ->
     contract dependencies -> one `Obligation` per surface, with consequence and trait-fact evidence; considered
     surfaces it excludes are listed NOT_APPLICABLE with a reason.
  2. An explicit mapping table (REQUIRED->ACCEPTED, CONDITIONAL->CANDIDATE+condition, NOT_APPLICABLE,
     EXPLICITLY_DEFERRED->DEFERRED) and an evidence-verdict field; a passing `closure.Verdict` is built only from
     APPLIED_VERIFIED, never from DELEGATED/UNJUDGED [G8].
  3. Closure: DEFERRED with empty/unassigned owner or empty `revisit_when` is blocking [G7].
  4. Composition: a typed relation on `CapabilityContract.dependencies`, with a test that the loaded contract count
     stays 13 (`load_contracts` drops invalid files silently) [G18].
  5. Tests: naked-verb, irrelevant-surface, consequence-escalation, silent-omission, N/A gaming, deferred-forever.

### Phase 6: Live delivery and report-only closure

**Goal**: Real sessions receive the envelope and their Stop leaves an evidence row — report-only.
**Depends on**: Phase 5
**Success Criteria**:

  1. `modules/gsd_x/cli.py`: bounded envelope block beside family_block; one total ceiling, dedup by entry id across
     family and archetype blocks [G18]; the delivered sentence states exactly what runs (report-only).
  2. Budget gate: measured added latency on the UserPromptSubmit child stays under the chain deadline with
     family_block still delivered (median and p95 recorded) [G4].
  3. At UserPromptSubmit write `~/.claude/state/tower/envelopes/<sid>.json` (envelope, judged_under stamps,
     subject_root(s) — the actual subject repo, not PP, when work happens elsewhere) [G2].
  4. A Python Stop member reads it by sid, parses `NO APLICA: <reason>` from the transcript against the closed
     vocabulary, judges report-only, writes rung rows (compiled/required/closed/NA/deferred/unjudged/violated);
     bounded timeout, block:false. Registered in the CANONICAL `hooks/hook-dispatcher.js` Stop-chain [G3].
  5. Live activation needs the Owner mirror step (copy canonical dispatcher to `~/.claude/hooks/`): written as an
     Owner action in EVIDENCE.md; until done, Production Reality for the Stop leg is UNJUDGED, never PASS.
     A V-gate drives the canonical dispatcher end to end (not in-process) and shows a row.

### Phase 7: Proving grounds and cross-context transfer

**Goal**: The plane works on real code in three archetypes and transfers across projects.
**Depends on**: Phase 6
**Success Criteria**:

  1. KC worktree `ucep/world-mutation`: a real persistence/world-mutation feature compiles an envelope; required
     surfaces close via a local gate with the exact command recorded (no live server, no deploy).
  2. InfinityOps worktree `ucep/external-effect`: a real external-effect feature inherits EXTERNAL_EFFECT surfaces;
     its local gate runs.
  3. BACKGROUND_JOB exercised on a real PP scheduled job (or KC job) with its own gate.
  4. KSR read-only (absolute path recorded in EVIDENCE): a naked "add coin save" intent compiles an envelope that
     requires save integrity; current code judged VIOLATED citing the save path — transfer without mutation.
  5. Each run's envelope is captured as a fixture for Phase 8.

### Phase 8: Falsification, live promotion, inheritance

**Goal**: The mechanism is proven falsifiable and the ratchet demonstrably moves future work.
**Depends on**: Phase 7
**Success Criteria**:

  1. `tools/test_capability_envelope_adversarial.py`: the 12 challenges (naked verb, irrelevant surface, trait
     transition, archetype negative control, consequence escalation, existing maturity, silent omission, N/A gaming,
     deferred-forever, instrument positive control, compiler severing, ratchet inheritance), `*_PASS=` line.
  2. Severing drill: a PP test replays captured Phase-7 fixtures through the real inheritance path, with imports
     routed through a root env var so `tools/mutation_drill.py` mutates an isolated copy; severed -> named V-gate
     FAIL (KILLED). Registered in `vault/governance/mutation_ratchet.json` [G10].
  3. One real promotion (archetype B1) from Phase-7 evidence passes admission (AUTO_ADMITTED); a later feature
     prompt in a receiving repo gets it in its envelope unprompted; removing it from the work is flagged by closure.
  4. Blocking gate (Owner answer 4): only if positive/negative controls, mutation + severing drills, N/A-gaming tests
     and one real run with zero false activations all pass — otherwise stay report-only and record why.

### Phase 9: Knowledge, metrics and handoff

**Goal**: Product Delta and Intelligence Delta are both durable and discoverable by a fresh agent.
**Depends on**: Phase 8
**Success Criteria**:

  1. Incidents (symptom, causal chain, fix, regression proof) for every bug met; UKDL HR/PR/Trap candidates in a NEW
     file `vault/knowledge_base/ukdl-candidates-ucep.md` [G14].
  2. Metrics from the rung rows with real denominators: capability closure rate, naked-verb escape rate, archetype
     inheritance rate, false-activation rate (UNJUDGED kept separate).
  3. Liveness: every new module reachable or declared; no new orphan by name.
  4. Wiki component pages (status LIVE/PLANNED), `RESUMPTION` for the mission, final handoff block.
