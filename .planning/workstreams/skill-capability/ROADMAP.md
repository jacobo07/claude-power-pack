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

- [x] **Phase 1: Card precision** - pillar A (completed 2026-10-03)
- [x] **Phase 2: Listing floor** - pillar B (completed 2026-10-03)
- [x] **Phase 3: Opportunity and delivery measurement** - pillar C (completed 2026-10-03)
- [x] **Phase 4: Coverage, criticality and freshness** - pillars D, H (completed 2026-10-03)
- [x] **Phase 5: Representation operations** - pillar F (completed 2026-10-03)
- [x] **Phase 6: Compile-out lineage** - pillar G (completed 2026-10-03)
- [x] **Phase 7: Contribution** - pillar E (completed 2026-10-04)
- [x] **Phase 8: Owner reconciliation and creation governance** - pillars I, J, K, L, M (completed 2026-10-04)
- [x] **Phase 9: Closeout (gex44 part)** - reviews, deltas, pre-final, LAPTOP-CLOSEOUT (completed 2026-10-04; state.N + `--final` are the laptop step, tracked in LAPTOP-CLOSEOUT.md, never a mission phase)
- [ ] **Phase 10: Gen 1 gex44 remainder** - pillar E bounded experiment on gex44 (<= 8 sessions), Q4 YAML repair of 7 skills + CWST card re-derivation, LAPTOP-CLOSEOUT refresh
- [ ] **Phase 11: Gen 2 Reality Scan and successor ledger** - 20 frontier items mapped to existing owners, gen2 ledger pre-registered and frozen, Gen 2 phases added from the scan

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

**Plans:** 3/3 plans complete

Plans:

- [x] 01-01-PLAN.md -- D-01 mtime-window provenance in the card + D-02 replay gate (5 D-CARD denies allowed, pre-session + mutant denied, 6th deny beside)
- [x] 01-02-PLAN.md -- D-03 `git exit 128` x6: stderr class per row, unborn-HEAD empty-tree fallback, capsule test hermetic + sweep
- [x] 01-03-PLAN.md -- D-04 ledger closure: prg evidence, state.A IMPLEMENTED_AND_VERIFIED, `[A]` owner-bundle line, `--pillar A` PASS

### Phase 2: Listing floor

**Goal**: Decide pillar B under its frozen rule; no third hiding attempt without a fresh-session D-LISTING measurement.
**Requirements**: SC-B
**Success Criteria**: a measurement file naming D-LISTING with its `command:`; `--pillar B` PASS.

**Plans:** 2/2 plans complete

Plans:

- [x] 02-01-PLAN.md -- D-04 verdict gate `tools/test_listing_floor_verdict.py` (recomputes K4 from the jsonl, red on a fabricated lower floor, rows pinned to 4d1cfb83) + D-01 generated D-LISTING measurement `evidence/B-listing-floor.md`
- [x] 02-02-PLAN.md -- D-01..D-03 ledger closure: state.B FALSIFIED_OR_REJECTED_BY_EVIDENCE from `--json`, upper-bound saving over D-LISTING, one `[B]` owner-bundle line (plugin-paging gateway, laptop), `--pillar B` PASS

### Phase 3: Opportunity and delivery measurement

**Goal**: One gate computes opportunity, delivery, recall and precision over a named transcript window.
**Requirements**: SC-C
**Success Criteria**: the gate is driven red once; n is reported per rate; `--pillar C` PASS.

**Plans:** 3/3 plans complete

Plans:

- [x] 03-01-PLAN.md -- D-01/D-03 gate `tools/test_skill_delivery.py` over committed fixture window F, owner row-time bounds in `tools/skill_invocations.py`, mutant drills, subprocess red run, rendered prg `evidence/C-delivery.md`
- [x] 03-02-PLAN.md -- D-02 windows: L = pinned laptop pack (selection-bound recall, invocation UNMEASURED), G = `--measure-live` recorded on gex44 into `evidence/C-window-G.json` (`--compare` reproduces it), V-SD-PLANES
- [x] 03-03-PLAN.md -- D-04 closure: state.C IMPLEMENTED_AND_VERIFIED, one `[C]` owner-bundle line, `--pillar C` PASS, A and B stay PASS

### Phase 4: Coverage, criticality and freshness

**Goal**: Every installed skill gets a coverage and criticality class (discovered, not curated); drift is gated.
**Requirements**: SC-D, SC-H
**Success Criteria**: sweep with a population floor and a positive control; drift gate red on a mutated mirror;
`--pillar D`, `--pillar H` PASS.

**Plans:** 4/4 plans complete

Plans:

- [x] 04-01-PLAN.md -- D: `tools/skill_coverage.py` + gate `tools/test_skill_coverage.py`, coverage/criticality derived from code, gex44 plane recorded in `evidence/D-live-gex44.json`, rendered `evidence/D-coverage.md`
- [x] 04-02-PLAN.md -- H: `tools/skill_mirror_drift.py` + gate `tools/test_skill_drift.py` (committed-blob, LF-normalized whole-dir compare), gex44 plane recorded in `evidence/H-live-gex44.json`, rendered `evidence/H-drift.md`
- [x] 04-03-PLAN.md -- H: card-vs-source digests `card_source_digests.json` + gate checks + wiring in `tools/router_freshness_gate.py`
- [x] 04-04-PLAN.md -- D/H closure: state.D, state.H, `[D]` + 2 `[H]` owner-bundle lines, `--pillar D/H` PASS, A/B/C stay PASS

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
`vault/programs/skill-capability/CLOSE.md`. On gex44 the phase ends at the laptop hand-off; `--final` and state.N are
the Owner's laptop step.

**Plans:** 3/3 plans executed (gex44 part verified; laptop `--final` pending, 09-VERIFICATION human_needed)

Plans:

- [x] 09-01-PLAN.md -- D-03 pre-final gate `tools/test_skill_capability_prefinal.py` (A-M PASS, N open, `--closeout`, selftest)
- [x] 09-02-PLAN.md -- D-01 reviews (ukdl.md, cbr.md) and ledger `reviews` / `deltas`
- [x] 09-03-PLAN.md -- D-02 LAPTOP-CLOSEOUT.md + D-03 record `evidence/pre-final-gex44.md`

### Phase 10: Gen 1 gex44 remainder

**Goal**: Everything of Gen 1 that gex44 can honestly close is closed: pillar E gets its bounded, pre-registered
experiment, the 7 invalid SKILL.md frontmatters are repaired or classified, and the laptop hand-off is current.
**Contract**: `vault/programs/skill-capability/gen2/OWNER-BRIEF-2026-10-05.md` (Q2, Q4, Gen 1 truthfulness) and
`vault/plans/skill-capability-gen2-2026-10-05.md` (Pillar E on GEX44, Q4). Read both before planning.
**Depends on**: Phase 9
**Requirements**: SC-E, SC-J, SC-G, SC-H
**Success Criteria**:

  1. Pillar E: a pre-registration (arms, n <= 4 per arm and <= 8 total, grade rule, decision rule, stop conditions,
     per-row environment record) is committed BEFORE the first counted session; the harness's host-path port is
     proven on a fixture dry-run first; gex44 rows are a plane of their own and are never pooled with the laptop rows
     (reported beside them). state.E ends at the terminal the pre-registered rule gives -- RESEARCH_INSUFFICIENT_EVIDENCE
     is valid -- and if it changes, the E rows of `reviews/cbr.md` and ledger `deltas` change in the same commit.
  2. Q4: each of the 7 skills is classified individually; a repair keeps the parsed description byte-identical to
     what the host reads today; an unrepaired one is recorded as legacy debt and excluded from any health or benchmark
     figure that treats it as valid. The CWST repair follows owner-bundle item 12 in the same unit (card + trailer,
     `--record-cards`, re-render G and H, move the state.G / state.H pins).
  3. `--pillar A` .. `--pillar M` PASS, `tools/test_skill_capability_prefinal.py` PASS with N open, the J gate PASS.
  4. LAPTOP-CLOSEOUT.md reflects the new state (state.N hashes follow any change of reviews/cbr.md; the pillar E
     owner-bundle item is updated to its result; the 7-skill outcome is listed for the laptop live sync).

### Phase 11: Gen 2 Reality Scan and successor ledger

**Goal**: Decide, against what actually exists, how each of the brief's 20 Gen 2 frontier items is owned
(ADOPT / EXTEND / MERGE / CONNECT / MINE / BENCHMARK / REJECT / BUILD), and pre-register Gen 2 as a versioned successor
of this same program.
**Contract**: OWNER-BRIEF "AFTER GEN 1 CLOSE", "GEN 2 DONE-GATE" and frontiers 1-20; the plan's "Gen 2" section.
**Depends on**: Phase 10
**Success Criteria**:

  1. A scan report under `vault/programs/skill-capability/gen2/` maps every frontier item to an existing owner or to a
     justified BUILD, from a DISCOVERED sweep (`/d2a-family`, `vault/audits/apir/NON_DUPLICATION_LEDGER.md`, the
     HR-NOVELTY-001 13-question proof for any BUILD), with file:line evidence. Pillar B's falsification is carried as
     negative knowledge (no retry of the same listing mechanism).
  2. One independent `oneshot-architect-auditor` pass over the mapping; its gaps are fixed or answered in the report.
  3. `vault/programs/skill-capability/gen2/ledger.json` pre-registers the Gen 2 items with predicted terminals and
     existing owners, names its lineage (Gen 1 ledger + FROZEN_AT), is frozen at a commit, and a wrapper verifier in the
     Gen 1 wrapper's pattern passes `--selftest` and `--status`.
  4. The Gen 2 execution phases are added to this roadmap from the scan (one phase per coherent wave, each naming its
     items, its evidence order -- telemetry, replay, shadow, natural experiments before fresh sessions -- and its
     gate), plus a final Gen 2 close phase whose laptop-plane proofs go to a laptop hand-off file.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Card precision | 3/3 | Complete    | 2026-10-03 |
| 2. Listing floor | 2/2 | Complete    | 2026-10-03 |
| 3. Opportunity and delivery measurement | 3/3 | Complete    | 2026-10-03 |
| 4. Coverage, criticality and freshness | 4/4 | Complete    | 2026-10-03 |
| 5. Representation operations | 3/3 | Complete    | 2026-10-03 |
| 6. Compile-out lineage | 3/3 | Complete    | 2026-10-03 |
| 7. Contribution | 2/2 | Complete    | 2026-10-04 |
| 8. Owner reconciliation and creation governance | 4/4 | Complete    | 2026-10-04 |
| 9. Closeout (gex44 part) | 3/3 | Complete    | 2026-10-04 |
| 10. Gen 1 gex44 remainder | 0/0 | Not started | - |
| 11. Gen 2 Reality Scan and successor ledger | 0/0 | Not started | - |
