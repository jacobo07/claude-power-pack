# Roadmap: Skill / Capability Program (skill-capability workstream)

Plan of record: `vault/plans/skill-capability-program-2026-10-03.md` (Owner APPROVED 2026-10-03, boundaries 1-4).
Ledger (the program's authority): `vault/programs/skill-capability/ledger.json`, pre-registration frozen at the
commit named in `vault/programs/skill-capability/FROZEN_AT`.
Done-gate: `python tools/test_skill_capability_program.py --final` (exit 0 = program DONE). It wraps
`tools/test_cognitive_economy_program.py` (clauses L1-L9) and adds R1 (retained global settings).

DAG (plan): P0 -> A -> B -> C -> (D || H) -> F -> G -> E -> (I, J, K, L, M) -> N.

Principle: availability without residency, proven by need-time delivery. A falsified lever is a successful
result. UNKNOWN, INCONCLUSIVE and UNMEASURED are never PASS. An upper bound is never a realized saving.

## Operating constraints (every phase)

- Shared checkout `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`, peer
  panes and two peer missions (`ucep`, `cognitive-economy`). Commit by explicit pathspec ONLY files this program
  created or owns; after each commit verify `git log -1 --format=%s`. Never reset, clean, restore, stash, amend or
  force. Push only under Owner boundary 4 (no foreign commits interleaving).
- Never edit (read only): `tools/test_cognitive_economy_program.py`, `vault/programs/cognitive-economy/**`,
  `tools/rollover.py`, `tools/gsd_mission.py`, `tools/usage_index.py`, `modules/cognitive_os/*`,
  `vault/knowledge_base/ukdl-universal.md` (UKDL candidates go to this program's own candidates file).
- Global edits under `~/.claude/` (HR-001, Owner boundary 3): snapshot first, shortest window, restore; prefer a
  per-run `--settings` file. Anything kept must be declared in ledger `retained.settings` (R1 checks it at --final).
- Sessions (Owner boundary 2): listing family 8 of 12 left; <= 10 new sessions for contribution/delivery benchmarks.
  Count every fresh session against D-SESSIONS in the phase EVIDENCE.md.
- RAM (Owner boundary 1): the mission is armed only at >= 4 GB free; below that, work in-pane.
- The ledger's `frozen` object is immutable. Phases write only `state.<pillar>`, `retained`, `reviews`, `deltas`.
- Closing a pillar: `state.<P>` = `{terminal, reason, evidence[], savings[]}` with the kinds the CE verifier
  requires; file evidence carries `sha256` of LF-normalized bytes; MERGED/DEFERRED need a frozen `owner` plus a
  committed handoff `vault/programs/skill-capability/handoffs/<P>.md` naming `[<P>]` and the owner path;
  measurements name a frozen denominator (`D-LISTING`, `D-CARD`, `D-SESSIONS`, `D-W7`) and carry a `command:` line.
  Then `python tools/test_skill_capability_program.py --pillar <P>` must print PASS.
- Never ask the Owner mid-run: Owner items go to `vault/programs/skill-capability/owner-bundle.md`, one line tagged
  `[<P>]`; that pillar is AUTHORIZATION_BOUND with an `owner_decision` evidence.

## Host plane: this run executes on GEX44 (Owner "do it in GEX44", 2026-10-03)

- Clone `/home/kobii/missions/skill-capability`, branch `mission/skill-capability`, origin = the bare repo
  `/home/kobii/repos/claude-power-pack.git`. Push ONLY `mission/skill-capability` to that origin; never GitHub,
  never another branch. The Owner fetches it back to the laptop.
- GEX44 is NOT the laptop's live install. Its `~/.claude/` (settings, hooks, skills, transcripts) is a different
  plane: never edit it, and never report a GEX44 reading as the laptop's. Every measurement names its host
  (`host: gex44` or `host: laptop`). A claim that needs the laptop plane (live hook sync of
  `hooks/doctrine_cards.js` to `~/.claude/hooks/`, a fresh laptop session listing, laptop transcripts beyond the
  pack, R1 retained-settings at `--final`) goes to `vault/programs/skill-capability/owner-bundle.md` tagged `[<P>]`.
- Pillar N (closeout) and the `--final` run are laptop-only: R1 reads the settings file of the host it runs on.
  On GEX44, finish at "every pillar except N terminal, `--pillar <P>` PASS for each"; N stays open by design.
- Laptop evidence shipped for pillar A, content-free (paths, timestamps, hunk headers, redacted truncated shell
  commands; no file content): `/home/kobii/missions/skill-capability-data/card_evidence_pack.json` (20 card-ledger
  rows, 7 sessions; built by `card_evidence_pack.py` beside it). Copy what a gate needs into
  `vault/programs/skill-capability/` as a fixture and cite it with sha256.
- Pillar A leads measured at hand-off (verify, do not trust): (1) D-CARD froze 5 denies; the live ledger now holds
  6 (`4615e1d1`, Orca-X, after the freeze); report it beside the frozen figure, never fold it in. (2) 3 of the 6
  `git exit 128` rows carry session `abcd1234`, the fixture id of `hooks/tests/test-capsule-mutation-guard.js`:
  a test invoking the card without `DOCTRINE_CARDS_STATE_DIR` would write test rows into the live ledger.
  (3) the other 3 are session `fce2689e`, cwd `C:\Users\User\Apps\io-mnb-w0`: a different checkout.
- Model calls: subscription quota only, this mission's own work. No paid API, no new credentials.

## Phases

- [ ] **Phase 1: Card precision** - pillar A
- [ ] **Phase 2: Listing floor** - pillar B
- [ ] **Phase 3: Opportunity and delivery measurement** - pillar C
- [ ] **Phase 4: Coverage, criticality and freshness** - pillars D, H
- [ ] **Phase 5: Representation operations** - pillar F
- [ ] **Phase 6: Compile-out lineage** - pillar G
- [ ] **Phase 7: Contribution** - pillar E
- [ ] **Phase 8: Owner reconciliation and creation governance** - pillars I, J, K, L, M
- [ ] **Phase 9: Closeout** - pillar N; reviews, deltas, done-gate

## Phase Details

### Phase 1: Card precision

**Goal**: The commit card stops denying the session's own tool-mediated writes without letting a foreign hunk through.
**Requirements**: SC-A
**Success Criteria**:

  1. `hooks/doctrine_cards.js` classifies a file whose mtime lies inside one of this session's shell tool-call
     windows after its last own edit as `unknown` (allowed), never `foreign`.
  2. A gate replays the five D-CARD denies as allowed AND a pre-session foreign hunk (arm C shape) as denied;
     existing card tests and the destructive card suite stay green.
  3. The `git exit 128` x6 class is reproduced and named (cause + fix or explicit fail-open reason).
  4. `--pillar A` PASS.

**Plans:** 2/3 plans executed (waves 1 -> 2 -> 3, sequential: shared `hooks/doctrine_cards.js` / `tools/test_card_precision.py`)

Plans:

- [x] 01-01-PLAN.md -- D-01 mtime-window provenance in the card + D-02 replay gate (5 D-CARD denies allowed, pre-session + mutant denied, 6th deny beside)
- [x] 01-02-PLAN.md -- D-03 `git exit 128` x6: stderr class per row, unborn-HEAD empty-tree fallback, capsule test hermetic + sweep
- [ ] 01-03-PLAN.md -- D-04 ledger closure: prg evidence, state.A IMPLEMENTED_AND_VERIFIED, `[A]` owner-bundle line, `--pillar A` PASS

### Phase 2: Listing floor

**Goal**: Decide pillar B under its frozen rule; no third hiding attempt without a fresh-session D-LISTING measurement.
**Requirements**: SC-B
**Success Criteria**: a measurement file naming D-LISTING with its `command:`; `--pillar B` PASS.

### Phase 3: Opportunity and delivery measurement

**Goal**: One gate computes opportunity, delivery, recall and precision over a named transcript window.
**Requirements**: SC-C
**Success Criteria**: the gate is driven red once; n is reported per rate; `--pillar C` PASS.

### Phase 4: Coverage, criticality and freshness

**Goal**: Every installed skill gets a coverage and criticality class (discovered, not curated); drift is gated.
**Requirements**: SC-D, SC-H
**Success Criteria**: sweep with a population floor and a positive control; drift gate red on a mutated mirror;
`--pillar D`, `--pillar H` PASS.

### Phase 5: Representation operations

**Goal**: Apply disclosure / fission / fusion / inline / dedup only where measured to help.
**Requirements**: SC-F
**Success Criteria**: each applied operation carries before/after D-LISTING and a recall check; `--pillar F` PASS.

### Phase 6: Compile-out lineage

**Goal**: Compiled-out cards carry source lineage, and a source change without re-derivation fails a gate.
**Requirements**: SC-G
**Success Criteria**: lineage field + gate driven from both poles; `--pillar G` PASS.

### Phase 7: Contribution

**Goal**: Measure whether delivered capability changed outcomes, inside the D-SESSIONS budget.
**Requirements**: SC-E
**Success Criteria**: paired arms, n stated, budget consumption recorded; `--pillar E` PASS.

### Phase 8: Owner reconciliation and creation governance

**Goal**: Close I, K, L, M by verified handoffs to their owners; land the J creation gate.
**Requirements**: SC-I, SC-J, SC-K, SC-L, SC-M
**Success Criteria**: one committed handoff per merged/deferred pillar; J gate refuses an undeclared skill and
admits a declared one; each `--pillar` PASS.

### Phase 9: Closeout

**Goal**: Reviews, deltas, retained-settings declaration and the done-gate.
**Requirements**: SC-N
**Success Criteria**: `reviews.ukdl` / `reviews.cbr` files exist; deltas filled; `retained.settings` matches live
settings; `python tools/test_skill_capability_program.py --final` exits 0, output pasted in
`vault/programs/skill-capability/CLOSE.md`.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Card precision | 2/3 | In Progress|  |
| 2. Listing floor | 0/0 | Not started | - |
| 3. Opportunity and delivery measurement | 0/0 | Not started | - |
| 4. Coverage, criticality and freshness | 0/0 | Not started | - |
| 5. Representation operations | 0/0 | Not started | - |
| 6. Compile-out lineage | 0/0 | Not started | - |
| 7. Contribution | 0/0 | Not started | - |
| 8. Owner reconciliation and creation governance | 0/0 | Not started | - |
| 9. Closeout | 0/0 | Not started | - |
