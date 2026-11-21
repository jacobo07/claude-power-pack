# Roadmap: bcap2b (BCAP-2 campaign B — absorb everything BCAP-2 left PARTIALLY_PROVEN)

Owner 2026-11-21 (laptop pane 6e2df121): "go ahead, en mision", budget **200M + 3x50M**, plane GEX44.
Authority: `vault/plans/bcap-2-absorption-2026-11-19.md` (its binding laws, especially law 4 = what CLOSED means), then
`vault/programs/bcap-2/HANDOFF.md` and `.planning/workstreams/bcap2/STATE.md` (every residual named there is this
campaign's input). Each phase's spec is its backlog file in `vault/backlog/`. Campaign A already built every gate
`tools/test_bcap2_*.py`, `vault/programs/bcap-2/done_gate.py`, `modules/ccf/creative_checks.py` (BI-08..14 on the CLI
path, report-first) and `modules/sqi/floor_guard.py`: extend them, never rebuild them.

PLANE: **GEX44**. You run in `~/missions/bcap2b/.claude/worktrees/bcap2b`, branch `mission/bcap-2b-run`. Never call
EnterWorktree. Commit with the repo-local identity, one causal delta per commit. Do NOT push. Use Bash (Linux), python3.
**Never touch GEX44's live `~/.claude` or `~/.claude/skills/claude-power-pack`** (agora-mission-sweep runs that tree), and
never edit `~/missions/bcap2` (campaign A, read-only). Laptop-plane items (browser-real checks, Synsation videos, anything
that reads the laptop's `~/.claude`) go to `vault/programs/bcap-2/LAPTOP_STEPS.md`, numbered, copy-pasteable,
BLOCKED-ON-LAPTOP; then continue.

EXECUTION mode. Plan each phase inline. Do NOT dispatch gsd-planner or gsd-phase-researcher. At most 2 bounded subagents.
Each phase: Reality Scan of the named owners first (one discriminating experiment) -> REUSE/EXTEND/CONNECT/DECLINE row in
the item's `REUSE_LEDGER.md` -> minimal implementation in the existing owner -> its `tools/test_bcap2_<item>.py` driven
from both poles (seeded failure caught, clean case passes) -> liveness (`python3 modules/liveness/reachability.py`: wire or
declare every new module; never `--baseline` other packages' orphans) -> ledger row with exit-0 evidence -> backlog Status
line + `vault/plans/deferred-backlog.md` row with the closing commit. After each phase record spend
(`python3 tools/mission_spend.py session-tree --session <sid>` or UNMEASURED) and a 5-line meta-analysis in STATE.md.
UNKNOWN or UNMEASURED is never PASS. Two materially identical failures = pivot the method. At a phase ceiling: commit what
is proven, keep the item PARTIALLY_PROVEN with named residuals, move on.

Windows lessons that also bite here: never write `<sha>^` in a shell string (use `<sha>~1`); decode subprocess output as
UTF-8 explicitly. Network reads are read-only: pin every upstream at a commit sha with its licence before using it;
principles only where the licence forbids code. No paid provider/API calls (fake providers in tests). Never publish, send,
push, deploy or activate anything; Ruflo stays HOLD (activation is the Owner's).

## Phases

- [x] **Phase 1: Upstream fetch pass.** One batched, read-only pass for Phases 1, 2, 3, 7, 8: pin commit + licence for
  every upstream named in their ledgers; turn each HYPOTHESIS/UNVERIFIED row into READ (with the file:line read) or
  DECLINE (with the reason). Includes AGSK's 34 HYPOTHESIS + 7 UNVERIFIED rows and Phase 8 `live_verified` for the 21
  resources. Ceiling 30M.
- [x] **Phase 2: Phase 8 remaining workstreams.** Spec `2026-10-30_cdio-21-design-resources-universal-absorption.md`.
  Close what STATE.md names open: C01/C02, D01/D02/D04, E/F/G/H rest, the 23 undriven V-D21 scenarios as poles, capability
  denominators measured not UNKNOWN. Put `tools/test_bcap2_d21_bc.py` into done_gate (it is not yet). Ceiling 50M.
- [x] **Phase 3: BI-27 / BI-30 page-level reads.** DesignHub 148e8c3f (MIT) source and the Impeccable b49177d3
  (Apache-2.0) detector: read, decide port vs principle per licence, implement in modules/ccf or modules/cdio. Ceiling 20M.
- [x] **Phase 4: BI-24 illustrated brand book PDF.** Extend the existing kit PDF path in modules/ccf (residual: the PDF
  embeds a hash, not the image). Render toolchain installed in a scratch venv outside the repo; real PDF bytes checked
  (page count, embedded image present), both poles. Ceiling 25M.
- [x] **Phase 5: BI-15..35 on the CLI path.** Same rule as slice A (`vault/specs/bcap2-activation.md`): absent is
  UNASSESSED never FAIL, report by default, enforce opt-in per check via `config["creative_checks"]`; extend
  creative_checks.run, do not add a second runner. Includes BI-16 cross-platform + CCF adapter. AC1 of that spec must stay
  true (existing CCF suites byte-for-byte). Ceiling 30M.
- [x] **Phase 6: CDIO SaaS style 3.** Spec `2026-10-02_cdio-modern-saas-styles.md`; the Owner confirmed option (b) for
  style 3 (session_lessons 2026-11-20 "style-3 (b) confirmed"). All three styles selectable and scored. Ceiling 15M.
- [x] **Phase 7: Ruflo residuals runnable on GEX44.** Inside the existing sandbox `/home/kobii/ruflo-sandbox-bcap2` only:
  runtime advisory verification, dist identity, `npm audit` recorded in the ledger. Activation stays refused. Ceiling 15M.
- [ ] **Phase 8: Closeout.** done_gate aggregates every gate incl. the new ones; per-item verdict by plan law 4 (ACTIVATED
  only with execution evidence on the real path); `vault/programs/bcap-2/HANDOFF-B.md` with per-item verdict and the
  laptop-only residuals listed. Ceiling 10M.

## Phase Details

### Phase 1: Upstream fetch pass
**Goal**: no HYPOTHESIS row left unread or undeclined. Requirement BCAP2B-01. Depends on nothing.

### Phase 2: Phase 8 remaining workstreams
**Goal**: BCAP2-08 closed per law 4, or named residuals only from the laptop plane. Requirement BCAP2B-02. Depends on 1.

### Phase 3: BI-27 / BI-30 page-level reads
**Goal**: both items closed or declined with reason. Requirement BCAP2B-03. Depends on 1.

### Phase 4: BI-24 illustrated brand book PDF
**Goal**: a real PDF with real embedded images from the CCF package path. Requirement BCAP2B-04. Depends on nothing.

### Phase 5: BI-15..35 on the CLI path
**Goal**: every built BI module reachable from modules/ccf/cli.py, report-first. Requirement BCAP2B-05. Depends on 3, 4.

### Phase 6: CDIO SaaS style 3
**Goal**: BCAP2-06 closed per law 4. Requirement BCAP2B-06. Depends on nothing.

### Phase 7: Ruflo residuals runnable on GEX44
**Goal**: every GEX44-runnable Ruflo residual measured; HOLD kept. Requirement BCAP2B-07. Depends on nothing.

### Phase 8: Closeout
**Goal**: done_gate PASS with the new gates; honest per-item verdicts. Requirement BCAP2B-08. Depends on 1-7.
