# Roadmap: Context Rent in one pane (ctx-same-pane workstream)

Contract of record: `vault/plans/context-rent-same-pane-2026-10-10.md` (commit `06d25261`, Owner "y" 2026-10-10).
It is binding: slices, done-gates, external limitations and budget come from it. Read sections 1-5 before any phase.

Principle: same-pane epoch rotation is ALREADY LIVE (292 auto `/clear` in 14 d). Do NOT rebuild it. Extend the
existing owners: `tools/rollover.py`, `tools/rollover_econ.py`, `tools/rollover_replay.py`, `hooks/rollover_wall.js`,
`modules/zero-crash/hooks/context-watchdog.py`, `tools/session_autopsy.py`, `tools/tis_observed.py`.
UNKNOWN, INCONCLUSIVE and UNMEASURED are never PASS. Missing attribution is not zero rent.

## Operating constraints (every phase)

- Goal `ctx-same-pane`, cap 16,000,000, bound to this worktree. HARD STOP: reaching it is a STOP: write the receipt
  `vault/programs/ctx-same-pane/RECEIPT.md` and end. Never raise a cap, never declare or rebind a goal.
- Keep tool calls small: host RAM is low. One command per call, results into files, read the file.
- Windows: git via `& 'C:\Program Files\Git\cmd\git.exe' -C <path>`; python via
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`. Prefer the PowerShell tool over Bash.
- Own paths: this worktree only. Read-only: `C:\Users\User\Apps\pp-ctx-rent` (never edit it), every other worktree,
  `~/.claude/state/**` (read ledgers, never write them except through the tools under test).
- Commit by explicit pathspec, verify `git log -1 --format=%s` after each commit. Never push, reset, clean, stash,
  amend or force. One causal change per commit; every behaviour change ships with a red-path V-gate + a control.
- Kill switches only DISABLE. The 45 % wall (`ADVISORY_PCT`) is never removed.
- LIVE INSTALL (self-hosting): after a phase's gates pass, install its commits into the live repo
  `C:\Users\User\.claude\skills\claude-power-pack` (branch feature/knowledge-acquisition) ONLY by
  `git -C <live> cherry-pick -x <sha>` when every path the commit touches is clean in live
  (`git -C <live> status --porcelain -- <paths>` empty). If a path is dirty or the action is denied: do not route
  around it; add one line to `vault/programs/ctx-same-pane/OWNER.md` (sha, paths, why) and continue.
- Never ask the Owner mid-run. Owner items go to `vault/programs/ctx-same-pane/OWNER.md` as one line each.
- Durable output: append confirmed facts to `vault/programs/ctx-same-pane/LOG.md` AS YOU GO.
- Real canaries spend subscription quota: bound each one (number of calls stated before it runs).

## Phases

- [ ] **Phase 1: S0 ctx-rent S2 repair** - apply/port the half-edit, finish H1, 4 suites, 4 red-path gates, replay OLD vs NEW prior
- [ ] **Phase 2: S1 rent attribution** - per-call breakdown by source + static floor census on real transcripts
- [ ] **Phase 3: S2 economic trigger** - custody-safe boundary + calibrated growth gate + thrash guard, replay-proven
- [ ] **Phase 4: S3 pane-advice extinction** - Stop-chain detector turns economic fresh-pane advice into a /kclear ask
- [ ] **Phase 5: S4 zero-model status** - probe UserPromptSubmit block; deterministic status projection or recorded limitation
- [ ] **Phase 6: S5 floor reduction** - remove only attributed, mechanically-enforced floor items, each with a test
- [ ] **Phase 7: S6 canaries + Production Reality** - long-pane multi-epoch, status, decision, crash matrix, cross-domain
- [ ] **Phase 8: S7 knowledge + CBR + closeout** - KV entry, FIOS, UKDL HR/PR/traps (deduped), CBR ratchet, liveness, receipt

## Phase Details

### Phase 1: S0 ctx-rent S2 repair
**Goal**: The PROTOCOL rehydration basis lands correctly. Input: `vault/programs/ctx-same-pane/S0-ctx-rent-s2-halfedit.patch`
(diff of pp-ctx-rent vs 0f8713fe) and `C:\Users\User\Apps\pp-ctx-rent\vault\plans\ctx-rent-RESUMPTION.md` +
`ctx-rent-s2-recovery.md` (read-only). The patch's base may differ from this tree: port by hand if `git apply` fails.
**Depends on**: Nothing
**Success Criteria**:
  1. The three missing H1 lines are in; `tools/test_rollover_replay.py`, `test_rollover.py`, `test_rollover_active_path.py`, `test_rollover_economic.py` pass (outputs committed to `vault/programs/ctx-same-pane/s0/`).
  2. New gates V-RR-CERTIFY-DETECT (controls: refused, --help, echo), V-RR-PROTOCOL-NOT-WORK (mutation goes red), V-RR-NO-CERTIFY-NOT-ZERO, V-ROLLOVER-PROTOCOL-BASIS pass, each with its red branch driven.
  3. Replay receipt `vault/receipts/ctx-rent-s2-replay.json`: OLD UPPER_BOUND_P50 vs NEW PROTOCOL_P90 (+ p50 sensitivity), counts, transition matrix, predicted rotation p50/p90, `no_certify_call`; the 150K-gate decision recorded per the recovery plan's rule.

### Phase 2: S1 rent attribution
**Goal**: Explain why a call processed what it did. Extend `tools/session_autopsy.py` (no new module unless no owner fits).
**Depends on**: Phase 1
**Success Criteria**:
  1. Per call: floor vs growth; growth split into tool_result / assistant / user / injected additionalContext (by hook where the transcript names it), totals reconcile with usage within a stated tolerance, unattributable = UNKNOWN (never 0).
  2. Static floor census: byte/token-estimate of global + project CLAUDE.md, `~/.claude/rules/**`, MEMORY.md, skill listing, agent listing, SessionStart/UserPromptSubmit injections; host-owned remainder reported as host floor.
  3. Run on >= 5 real transcripts (one per kind: long interactive pane, mission worker, successor after /kresume, fresh small pane, non-PP repo); report committed `vault/programs/ctx-same-pane/s1/attribution.md`. Gate V-AUTOPSY-ATTRIB-* with a positive control.

### Phase 3: S2 economic trigger
**Goal**: Rotation fires at the economic point, not at 450K.
**Depends on**: Phase 1, Phase 2
**Success Criteria**:
  1. `rollover.at_boundary` replaced by a custody-safe boundary (no own uncommitted writes outside the capsule repo, no pending children; peers' dirt ignored). Gate drives both poles; the 449-class refusal is reproduced red on the old predicate.
  2. Growth gate calibrated from the Phase 1 replay (target ~floor+150K); thrash guard = minimum calls per epoch from measured C. Replay over the 14-day ledger shows predicted rotation p50 and rotations/day before vs after; no thrash.
  3. Installed live (see constraints) behind `CPP_ROLLOVER_ECONOMIC`; first live `rollover_kclear_asked` from the new path observed in the ledger, or recorded as OWED with reason.

### Phase 4: S3 pane-advice extinction
**Goal**: "Open a fresh pane" given for context economics becomes an automatic in-place rotation.
**Depends on**: Phase 3
**Success Criteria**:
  1. A Stop-chain detector (closer-guard family, fail-open, kill switch `CPP_PANE_ADVICE_GUARD=off`) recognises the advice (EN/ES) and sets the existing self-seal ask; legitimate mentions (quoting, docs, a different repo) are controls that stay green.
  2. Its liveness is proven by driving the registered hook on a real payload (the event reaches it), not by rc. FIOS class OWNER_FORCED_PANE_ROTATION registered.
  3. Memory `feedback_coordinator_pane_is_the_overrun` amendment text proposed in OWNER.md (memory lives under ~/.claude: proposal only).

### Phase 5: S4 zero-model status
**Goal**: Pure status questions cost ~0 model tokens.
**Depends on**: Phase 2
**Success Criteria**:
  1. One bounded probe (record the host version) of whether a UserPromptSubmit `decision:block` + reason is shown to the Owner and no model call happens (verify by transcript usage). Result committed.
  2. If yes: deterministic fail-open keyword sentinel for status queries (EN/ES; advisory questions pass through) renders Program State Projection (missions via gsd_mission status, goals via mission_spend goal-status, rollover state, HEAD/dirty); kill switch `CPP_STATUS_FASTPATH=off`; gates for both poles. If no: EXTERNAL_LIMITATION entry + cheapest fallback documented; no success claimed.

### Phase 6: S5 floor reduction
**Goal**: Shrink the per-call floor using Phase 2 attribution only.
**Depends on**: Phase 2
**Success Criteria**:
  1. Each removal names its attributed size and the mechanism that still enforces it, with a test proving enforcement survives.
  2. Anything under `~/.claude` (rules, CLAUDE.md, settings) is a PROPOSAL in OWNER.md with measured savings, never edited by the worker.
  3. Measured floor before/after on a fresh session (transcript call #1), or UNMEASURED with reason.

### Phase 7: S6 canaries + Production Reality
**Goal**: Host traces prove the claims. Every number from transcript usage, never object sizes.
**Depends on**: Phase 3, Phase 4, Phase 5
**Success Criteria**:
  1. Long-pane canary: a real pane crosses >= 3 epochs via the live path; per epoch: resident at rotation, successor first-call context, tokens to first useful action, exam result. Bounded call count stated beforehand.
  2. Status canary (if Phase 5 shipped): >= 5 status prompts in a large pane, model tokens ~0 by transcript.
  3. Crash during rotation at 4 points + duplicate dispatch converge (reuse existing fault-matrix tests; add the interactive cases missing).
  4. Cross-domain: one non-PP repo pane, or GEX44 tmux route, measured. Results in `vault/programs/ctx-same-pane/s6/PRODUCTION_REALITY.md` with reality level per claim.

### Phase 8: S7 knowledge + CBR + closeout
**Goal**: Lock it in and close honestly.
**Depends on**: Phase 7
**Success Criteria**:
  1. KV/UKDL entries (HR/PR/trap candidates deduped against `vault/knowledge_base/ukdl-universal.md`), FIOS classes, CBR ratchet entry; `python modules/liveness/reachability.py` exit 0 for new modules.
  2. RECEIPT.md answers the plan's final meta-analysis and the 18 done-gates, each PASS / EXTERNAL_LIMITATION (with fallback + test) / OWED with reason. Handoff block per the contract.
