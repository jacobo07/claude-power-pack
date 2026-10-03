# Roadmap: Incremental Cognition Program (incremental-cognition workstream)

Plan of record: `vault/plans/incremental-cognition-program-2026-10-03.md` (Owner APPROVED 2026-10-03).
Ledger (authority): `vault/programs/incremental-cognition/ledger.json`, pre-registration frozen at `FROZEN_AT`.
Audit: `vault/audits/incremental-cognition-phase4-audit.md` (EXECUTE-WITH-FIXES, G1-G10, dispositions in the plan).
Done-gate: `python tools/test_incremental_cognition_program.py --final` (exit 0 = program DONE).

Mission terms: incremental-cognition, context-rent, institutional-memoization, invalidation, cognitive-compiler,
baseline-ratchet.

Principle: a delta program over cognitive-economy (CE) and skill-capability (SC). CONSUME their verdicts, BUILD
only an unowned material gap or a correctness repair. UNKNOWN / INCONCLUSIVE / UNMEASURED are never PASS; an
upper bound is never a realized saving; a deterministic replay is never behavioral evidence.

## Operating constraints (every phase)

- Shared checkout `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`, many
  peer panes and missions. Commit by explicit pathspec ONLY files this program created or the single owned hunk
  of a correctness repair; verify `git log -1 --format=%s` after each commit. Never reset, clean, restore, stash,
  amend, rebase or force. Never push.
- Never edit: `tools/test_cognitive_economy_program.py`, `tools/test_skill_capability_program.py`, CE/SC ledgers,
  `vault/knowledge_base/ukdl-universal.md`, root `.planning/STATE.md`, anything under `~/.claude/` without an
  Owner-bundle line (HR-001).
- `tools/gsd_mission.py` is LIVE-LOADED by the production sweep (saving it deploys it) and capsule-v2 (spec
  `vault/specs/mission-capsule-rollover.md` T6) will wire into `supervise`. Pillar A edits it ONLY: (1) in a
  scratch copy first, (2) as one minimal hunk around `align_cwd` / `CWD_ALIGN_BLOCKING`, (3) with
  `test_gsd_mission.py`, `test_gsd_epoch.py`, `test_gsd_mission_cwd_align.py` and the legacy golden green,
  (4) copied in only at >= 4 GB free RAM (unblocking relaunches CE and ucep workers at once, audit G6).
- Program-owned paths: `vault/programs/incremental-cognition/**`, `.planning/workstreams/incremental-cognition/**`,
  `tools/test_incremental_cognition_program.py`, `wiki/tools/kme_*.py`, and NEW files a phase creates there.
- The ledger `frozen` object is immutable. Phases write only `state.<P>`, `reviews`, `deltas`.
- Closing a pillar: `state.<P>` = `{terminal, reason, evidence[], savings[]}` with the CE verifier's evidence kinds;
  file evidence carries LF sha256; MERGED/DEFERRED need `owner` + a committed `handoffs/<P>.md` naming `[<P>]` and
  the owner; pillars in `frozen.consumes` also need `owner_ledger` evidence `{ref, commit, pillar, terminal}` at a
  commit reachable from HEAD (R2). Then `python tools/test_incremental_cognition_program.py --pillar <P>` PASS.
- Never ask the Owner mid-run: one line tagged `[<P>]` in `vault/programs/incremental-cognition/owner-bundle.md`,
  terminal AUTHORIZATION_BOUND with `owner_decision` evidence; continue with other phases.
- Every phase commits EVIDENCE.md (with Product Delta and Intelligence Delta) and its ledger rows before ending,
  so no_progress can see it (audit G8). Budget per epoch: 12 cycles / 24 h.

## Run plane: GEX44 (Owner decision 2026-10-03)

The mission runs on GEX44 in its own clone (`~/missions/incremental-cognition`), not in the laptop's shared
checkout: the laptop's free RAM swung 0.6-8 GB during arming. Read every constraint above with that in mind:

- **The clone is not shared and not live.** Editing `tools/gsd_mission.py` in it deploys nothing (GEX44's sweep
  loads its own install). B and C still edit it in one minimal hunk each, red test first; they reach the laptop's
  live file only by an Owner-run fetch + deploy at >= 4 GB free (audit G6) -- record that as a `[B]`/`[C]` line in
  the owner bundle. Never push; the Owner fetches `mission/incremental-cognition-run` back.
- **Pillar A is code-complete on the laptop** (d2505df6: 16/16 cwd_align, 7 mutants killed). Its PRG (a real held
  mission relays in the laptop's live sweep) is laptop-plane: owner-bundle line `[A]`, do not re-implement A.
- **KME-L is laptop-plane.** D, E, F, G, I and L measure the laptop's transcripts, which are not on GEX44. Never
  substitute GEX44's corpus for KME-L: measure the KME-G share where the frozen rule names KME-G, build the
  measuring tool and its tests here, and record the KME-L run as one `[<P>]` owner-bundle line with the exact
  command. The pillar stays open (no terminal) until that run lands.
- **K's reference floor is laptop-plane.** Build and test the gate here (positive control on a seeded rise);
  the committed reference must come from the laptop install -> `[K]` owner-bundle line.
- **Anything reading `~/.claude/` judges GEX44's install**, not the laptop's: label such evidence `plane: gex44`.
- **Laptop-independent work:** B (GEX44 preflight is native here), C, H, J, M (CE/SC ledgers in the repo), N.

## Phases

- [ ] **Phase 1: Mission relay in a shared checkout** - pillar A (correctness repair, red test first).
  CODE-COMPLETE d2505df6 (criteria 1-3 met); only criterion 4 (PRG, laptop-plane) remains -> owner bundle `[A]`;
  start the GEX44 run at Phase 2.
- [ ] **Phase 2: Persistent failures and remote integrity** - pillars C, B
- [ ] **Phase 3: KME corpus measurements** - pillars D, E, F, G, H, I (measured on frozen KME-L / KME-G)
- [ ] **Phase 4: Cognitive cost regression gate** - pillar K
- [ ] **Phase 5: Offline replay and owner bundle** - pillar L; owner bundle for quota / global edits / re-login
- [ ] **Phase 6: Consume owners and close** - pillars J, M (R2 after CE/SC land on HEAD); N closeout; deltas

## Phase Details

### Phase 1: Mission relay in a shared checkout

**Goal**: a mission whose worker entered its own worktree keeps relaying when peers commit to the main checkout.
**Depends on**: nothing.
**Success criteria**:

1. A red test reproduces the measured hold (cwd and work_dir both ahead of their merge-base) before the fix.
2. The Brand #001 shape (a worker that never worked in the worktree) STAYS blocked (V-MCA-DIVERGED unchanged).
3. A scratch-repo drill relays three times while main advances between relays, with no lost commit and no
   destructive git; a mutation drill (the new status forced back to blocking) turns it red.
4. PRG: a real held mission relays in the live sweep after deployment (at >= 4 GB free).

### Phase 2: Persistent failures and remote integrity

**Goal**: an authorization-class failure parks a mission instead of relaunching; a GEX44 launch proves its
environment first.
**Depends on**: Phase 1 (same file, sequential hunks).
**Success criteria**:

1. Red test of the 137-relaunch shape (worker dies on `Login expired` before any API call) -> fix -> green.
2. GEX44 a5/a7: rules version, hook health and interpreters checked by a repeatable preflight; broken hooks and
   stale rules repaired by a deploy script; re-login recorded in the owner bundle, never bypassed.
**Plans:** 4 plans (sequential waves 1-4)

Plans:
**Wave 1**

- [ ] 02-01-PLAN.md — C: 137-relaunch shape red through supervise; auth fallback parks without the breaker (C's one gsd_mission hunk); re-login releases a quarantine

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 02-02-PLAN.md — B: read-only GEX44 env preflight (auth, rules version, hooks, interpreters; READY/NOT_READY/UNMEASURABLE); evidence on a5/a7

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 02-03-PLAN.md — B+C: one pre-launch gate (B's one gsd_mission hunk): renewals inherit a quarantine; declared planes refuse on measured NOT_READY

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 02-04-PLAN.md — B: repeatable git deploy for envs (dry-run default, locked, backed up); C.md/B.md evidence; [B]/[C] owner-bundle lines

### Phase 3: KME corpus measurements

**Goal**: each measured pillar gets a terminal by its frozen rule on KME-L / KME-G.
**Depends on**: nothing (read-only on transcripts).
**Success criteria**: per pillar one measurement file naming its denominator and `command:`; materiality applied
exactly; a second workload sampled for any pillar that clears 3 %.

### Phase 4: Cognitive cost regression gate

**Goal**: a material rise in startup floor by layer is visible in review.
**Depends on**: nothing.
**Success criteria**: gate green on today's floor, red on a seeded rise (positive control), layer and scope reported.

### Phase 5: Offline replay and owner bundle

**Goal**: offline replay ranks the live experiments; every Owner item is in one bundle.
**Depends on**: Phase 3.

### Phase 6: Consume owners and close

**Goal**: J and M closed by R2 against CE/SC ledgers on HEAD; UKDL 3-level and CBR reviews; deltas; done-gate.
**Depends on**: CE and SC landing their ledger commits on this line of history.
