# Roadmap: Cognitive Economy Program (cognitive-economy workstream)

Plan of record: `vault/plans/cognitive-economy-program-2026-10-03.md` (Owner APPROVED 2026-10-03, six defaults).
Ledger (the campaign's authority): `vault/programs/cognitive-economy/ledger.json`, pre-registration frozen at
`fa9ae2ed` (`FROZEN_AT`). Audit: `vault/audits/cognitive-economy-phase4-audit.md`.
Done-gate: `python tools/test_cognitive_economy_program.py --final` (exit 0 = campaign DONE).

Mission terms: cognitive-economy, context-lifetime, capability-virtualization, turn-advancement,
compile-out, baseline-ratchet.

Principle: waste less intelligence, never use less. A falsified lever is a successful result. UNKNOWN,
INCONCLUSIVE and UNMEASURED are never PASS. An upper bound is never a realized saving.

## Operating constraints (every phase)

- Shared checkout `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
  7 peer panes and a peer Ralph mission (`ucep`). Commit by explicit pathspec ONLY files this campaign
  created; after each commit verify `git log -1 --format=%s`. Never reset, clean, restore, stash, amend or
  force anything. Never push.
- Never edit (peer-owned, read only): `tools/rollover.py`, `hooks/context-watchdog.py`, `tools/gsd_mission.py`,
  `tools/gsd_epoch.py`, `tools/usage_index.py`, `tools/fanout_ledger.py`, `tools/root_progress.py`,
  `tools/compound_unattended.py`, `modules/gsd_x/goal/*`, `modules/cognitive_os/*`, root `.planning/STATE.md`,
  `vault/knowledge_base/ukdl-universal.md`, anything under `~/.claude/` (settings, hooks, rules, CLAUDE.md,
  state files other than reading). `usage_index.py` may be run with `window` only (never `refresh`/`burn`).
- Campaign-owned paths: `vault/programs/cognitive-economy/**`, `.planning/workstreams/cognitive-economy/**`,
  `tools/test_cognitive_economy_program.py`, and NEW files a phase creates under
  `vault/programs/cognitive-economy/` (measurement scripts, gates, handoffs, evidence).
- The ledger's `frozen` object is immutable (the verifier compares it with `FROZEN_AT`). Phases write only
  `state.<pillar>`, `reviews`, `deltas`.
- Closing a pillar: write `state.<P>` = `{terminal, reason, evidence[], savings[]}` using the evidence kinds the
  verifier requires (see its REQUIRED_KINDS); every file evidence carries `sha256` = sha256 of its LF-normalized
  bytes; MERGED/DEFERRED need `{"kind":"owner","ref":<a frozen owner>}` plus a handoff file
  `vault/programs/cognitive-economy/handoffs/<P>.md` that names `[<P>]` and the owner path and is COMMITTED
  (after the freeze); measurements must name a frozen denominator (`D-W7`, `anchor`, `ksr_dead_carriage`) and
  carry a `command:` line. Then `python tools/test_cognitive_economy_program.py --pillar <P>` must print PASS.
- Apply each pillar's frozen decision rule exactly; materiality is >= 3 % of D-W7 weighted. Never change a rule
  after seeing data; if a rule is unmeasurable, the terminal is RESEARCH_INSUFFICIENT_EVIDENCE with the reason.
- Never ask the Owner mid-run. Anything needing the Owner goes into
  `vault/programs/cognitive-economy/owner-bundle.md` as one line tagged `[<P>]`; the pillar's terminal is then
  AUTHORIZATION_BOUND with an `owner_decision` evidence pointing at that file. Continue with other phases.
- Model calls only for this mission's own work (Owner "spend now", this mission only). No paid API, no new
  credentials, no GEX44, no external publication.
- Every phase, measurement-only phases included, commits its EVIDENCE.md and ledger rows before it ends.
  Each phase records Product Delta and Intelligence Delta in its EVIDENCE.md.

## Phases

- [ ] **Phase 1: Baseline gate and owner reconciliation** - pillar A gate; handoffs for I, N, O, Q
- [ ] **Phase 2: Context lifetime and fresh-epoch economics** - pillars D, E measured with displacement
- [ ] **Phase 3: Turn advancement and non-convergence** - pillars H, J turn taxonomy archaeology
- [ ] **Phase 4: Re-derivation, admission, proof reuse and tool-schema residency** - pillars F, G, K, P, C(tools)
- [ ] **Phase 5: Compile-out of compound steps 7 and 8** - pillar L module proven on a temp state copy
- [ ] **Phase 6: Baseline compiler audit and institutional GC** - pillars S, T
- [ ] **Phase 7: Owner bundle, baseline-ratchet review and close** - pillars B, C, M, R; deltas; done-gate

## Phase Details

### Phase 1: Baseline gate and owner reconciliation

**Goal**: Pillar A becomes IMPLEMENTED_AND_VERIFIED through a re-runnable gate, and the pillars whose capability
already exists in a live owner (I work packet, N event-driven, O cognitive IR, Q capital accounting) are closed
by verified handoffs, not by assertion.
**Depends on**: Nothing
**Requirements**: CE-A, CE-I, CE-N, CE-O, CE-Q
**Success Criteria** (what must be TRUE):

  1. `vault/programs/cognitive-economy/gates/gate_baseline.py` exists, re-runs
     `tools/usage_index.py window` for the frozen anchor and D-W7 windows, exits 0 only if the anchor matches
     exactly and D-W7 raw figures are within 0.5 %, exits 1 otherwise, and has been driven red once (a
     perturbed expected value) with the run recorded in EVIDENCE.md.
  2. For each of I, N, O, Q the owner's capability is verified by reading or running it (cite file:line or the
     command + output), and a handoff file names the pillar, the owner path and what the owner keeps. O's handoff
     carries the audit G1-G4 finding (whole-tree verdict pin makes Goal-spine closure unreachable in a shared
     checkout) addressed to the Goal spine owner.
  3. `--pillar A`, `--pillar I`, `--pillar N`, `--pillar O`, `--pillar Q` each print PASS.
  4. A product-facing PRG for A: the gate is run from a fresh process and its stdout pasted in EVIDENCE.md.

### Phase 2: Context lifetime and fresh-epoch economics

**Goal**: Replace "savings UNMEASURED" for the live context-lifetime owners with a measured answer, separating
realized saving from displaced rehydration work.
**Depends on**: Phase 1
**Requirements**: CE-D, CE-E
**Success Criteria** (what must be TRUE):

  1. A campaign script (zero model calls) measures, for economic-rollover crossings and mission context rotations
     in the D-W7 window, the context carried before vs after and the successor's rehydration cost (first-call
     cache write + reads before its first edit), reported as an interval on D-W7 with displacement status.
  2. The KSR dead-carriage upper bound (<= 6.34 %) is compared with what the live trigger actually reclaimed, and
     the remainder is stated as upper bound, never as saving.
  3. D and E each reach a terminal by their frozen rule; any proposal to an owner is a handoff file, never an edit
     of `tools/rollover.py`, `context-watchdog.py`, `gsd_epoch.py`.
  4. Instrument controls: a positive control (a known crossing found) and a negative control (a session with no
     crossing reports none) recorded.

### Phase 3: Turn advancement and non-convergence

**Goal**: A reproducible turn-advancement taxonomy over observable state, answering how many model turns each
verified advancement costs and how many turns are coordination, bookkeeping, recovery, proof, repeat or
non-convergent.
**Depends on**: Phase 1
**Requirements**: CE-H, CE-J
**Success Criteria** (what must be TRUE):

  1. A campaign script reads `tools/usage_index.py` data and `tools/root_progress.py` output (importing, never
     editing) joined to git, classifies turns of the D-W7 window into the seven classes with the rule for each
     written down, and reports turns per commit / per green test per root, with UNSETTLED kept separate from waste.
  2. Classifier controls: hand-labelled sample of >= 30 turns with agreement reported; a shuffled-label negative
     control.
  3. H closes IMPLEMENTED_AND_VERIFIED only through a gate that re-runs the classifier on a frozen sample and
     checks its output hash; J closes by its frozen rule from H's numbers.
  4. Any optimization H suggests is judged by the 3 % rule and either becomes a handoff to its owner or is
     rejected with the number.

### Phase 4: Re-derivation, admission, proof reuse and tool-schema residency

**Goal**: Decide pillars F, G, K, P and the tool-schema half of C with measurements under their frozen rules.
**Depends on**: Phase 1
**Requirements**: CE-F, CE-G, CE-K, CE-P, CE-C
**Success Criteria** (what must be TRUE):

  1. F: identical-dependency re-reads across sibling subagents measured on D-W7 (same path + same content hash);
     G decided from F's identity evidence.
  2. K: `vault/audits/ksr_archaeology/scripts/ctx_dead.py` (or a campaign copy pointed at CPP transcripts, the
     original untouched) replicated on the CPP corpus with the same pre-registered rule.
  3. P: verification share (test/gate tool calls + their output carriage) of D-W7 measured.
  4. C(tools): MCP / tool schema residency measured against the floor and D-W7; skills and agents stay with their
     owners (skill-residency-program, K-slice, ACV) via a handoff.
  5. Every measurement file names its denominator and command; every terminal passes `--pillar`.

### Phase 5: Compile-out of compound steps 7 and 8

**Goal**: The compound-learnings pipeline that has stalled at steps 7+8 about once a day gets a correct,
campaign-owned implementation of those steps, proven against a temporary copy of its state.
**Depends on**: Phase 1
**Requirements**: CE-L
**Success Criteria** (what must be TRUE):

  1. A new module under `vault/programs/cognitive-economy/compound/` implements steps 7+8: mkdir mutex at
     `compound-learnings.json.lock`, backup, sibling tmp + rename, marker unlink, rollback on unlink failure,
     case-sensitive JSON keys.
  2. Its gate runs against a TEMP copy of `~/.claude/state/compound-learnings.json` and real learning files,
     drives a red branch (unlink failure -> rollback restores the backup byte-identically) and never touches the
     live state file (its sha256 is identical before and after the gate).
  3. The live apply and the call-site switch in `tools/compound_unattended.py` are written to the Owner bundle.
  4. `--pillar L` PASS.

### Phase 6: Baseline compiler audit and institutional GC

**Goal**: Decide whether the baseline compiler already derives completion obligations from traits (S), and run
the institutional GC sweep (T).
**Depends on**: Phase 1
**Requirements**: CE-S, CE-T
**Success Criteria** (what must be TRUE):

  1. S: `tools/baseline_ledger.py` / `tools/family_baseline.py` and their tests read and run; trait -> obligation
     derivation demonstrated on one real project or the gap named with evidence.
  2. T: `python modules/liveness/reachability.py` run; never-invoked skills and orphan modules listed with
     evidence; every retirement that needs settings or deletion goes to the Owner bundle.
  3. Each pillar passes `--pillar`.

### Phase 7: Owner bundle, baseline-ratchet review and close

**Goal**: Close the remaining pillars (B, C, M, R), finish the baseline-ratchet (UKDL 3-level + CBR) review,
record Product Delta and Intelligence Delta, and pass the done-gate.
**Depends on**: Phase 2, Phase 3, Phase 4, Phase 5, Phase 6
**Requirements**: CE-B, CE-C, CE-M, CE-R
**Success Criteria** (what must be TRUE):

  1. `vault/programs/cognitive-economy/owner-bundle.md` lists every Owner decision, one line per item, tagged
     with its pillar.
  2. `vault/programs/cognitive-economy/ukdl-candidates.md` holds every hard rule / process rule / trap candidate
     from the campaign with evidence and a promote / reject / keep-candidate verdict; CBR maturity per finding.
  3. The after-snapshot (same `usage_index window` command, a window after the campaign) is reported beside the
     before-snapshot, with every saving labelled realized / upper bound / unknown and its displacement.
  4. Ledger `reviews` and `deltas` filled; the final meta-analysis is in `vault/programs/cognitive-economy/CLOSE.md`.
  5. `python tools/test_cognitive_economy_program.py --final` exits 0, its output pasted in CLOSE.md.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline gate and owner reconciliation | 0/0 | Not started | - |
| 2. Context lifetime and fresh-epoch economics | 0/0 | Not started | - |
| 3. Turn advancement and non-convergence | 0/0 | Not started | - |
| 4. Re-derivation, admission, proof reuse and tool-schema residency | 0/0 | Not started | - |
| 5. Compile-out of compound steps 7 and 8 | 0/0 | Not started | - |
| 6. Baseline compiler audit and institutional GC | 0/0 | Not started | - |
| 7. Owner bundle, baseline-ratchet review and close | 0/0 | Not started | - |
