# Roadmap — ctx-rent-x (v1)

Authority: `vault/plans/ctx-rent-x-2026-10-31.md` (Owner `approve ctx-rent-x only`, 2026-10-31). Read its sections 1
(Reality Scan: owners already exist — EXTEND, never create a parallel system) and 3-5 (economics, kill switches,
Production Reality) before Phase 1, then do NOT re-scan what it already states.
PLANE: laptop, live checkout `~/.claude/skills/claude-power-pack`, branch `feature/knowledge-acquisition`, shared tree with
1000+ foreign dirty files: pathspec-scoped micro-commits only, one causal delta each, never take a foreign hunk; after every
commit check `git log -1 --format=%s`. Git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PowerShell PATH). No push.
EXECUTION mode, small scopes. **Plan each phase inline in this session. Do NOT dispatch gsd-planner / gsd-phase-researcher
subagents** (m-868c1464febb: an unbounded planner burned 16.3M and wrote no plan). At most 2 bounded subagents in parallel,
each with a compiled packet (files, question, bound, output path).
Measure your own spend after each phase: `python tools/mission_spend.py session-tree --session <your sid>`; record it in
STATE.md. A phase over 2x its P50 (plan section 2) -> stop and write the one-line Owner note in STATE.md.
UNKNOWN / UNMEASURED / INCONCLUSIVE are never PASS. CACHE_HIT is not SAVED_CONTEXT. Shadow proves safety, not savings.
Every new gate gets a mutation drill that must go red. Before any CCR release: `python tools/hardrule_compile.py --class DEPLOY`.
Never touch pane 5cadebe8, the held missions, settings.json permissions, or GEX44 `~/.claude`.
Free RAM is low on this host: run suites in the foreground, in batches; a suite red below ~3000 MB free is re-run before it is believed.

## Phases

- [ ] **Phase 1: W0 Rent census + weekly measurement (early-value checkpoint)**
- [ ] **Phase 2: W1 Top-level floor diet (counterbalanced)**
- [ ] **Phase 3: W2 CCR main canary (opt-in enforce)**
- [ ] **Phase 4: W3 Successor compiler + rollover economics**
- [ ] **Phase 5: W4 Tool-output + thinking carriage in main, Safe-to-Forget**
- [ ] **Phase 6: W5 Waiting / admission classifier (shadow)**
- [ ] **Phase 7: W6 Replay + champion/challenger, X -> X-prime**
- [ ] **Phase 8: W7 UKDL, Knowledge Vault, Baseline Ratchet, dogfood, master done-gate**

## Phase Details

### Phase 1: W0 Rent census + weekly measurement
**Depends on**: nothing. P50 2.5M, ceiling 5M.
- Rerun `vault/programs/ctx-rent-obs/b2/w6_estate.py` for 2026-10-25T00:00Z..2026-11-01T00:00Z (or now) and diff against
  `estate-week.json` (10-18..10-25), by class AND by loaded CCR generation (join `tools/ccr_generation_census.py` / CCR
  start receipts by sid; a session with no receipt is UNKNOWN, never "current").
- Per-class carriage per call on real transcripts: floor, tool_result, thinking, attachments, assistant text, user text.
- Dead Context Rent, offline Belady: for each tool_result / large block, tokens carried on calls after its last reference
  (labelled APPROX upper bound; state the reference heuristic). On >= 2 of: KSR 01.1 transcript if retrievable,
  coordinator e10a9f08, one /kresume successor chain.
- `tools/ccr_release.py release` writes `source_commit` into RELEASE.json (test first, red then green).
- New `tools/test_ctx_rent.py` (V-CTXR-*) covers the census/Belady code with fixtures from real byte shapes.
- **Acceptance (early-value checkpoint):** a weekly delta table by class and generation + a Dead-Rent figure on >= 2
  transcripts, with commands. If not reached within 5M cumulative: write `METHOD_PIVOT_REQUIRED` in STATE.md and stop.

### Phase 2: W1 Top-level floor diet
**Depends on**: Phase 1. P50 6M, ceiling 12M.
- Rows 1 (agent listing), 2 (3 rules -> skills + `skill-rule-index.md`), 3 (MEMORY.md index trim), 5 (hook additionalContext
  cap 1K chars, in the hook) of `vault/programs/ctx-rent-obs/b3/PROPOSAL.md`. Backup each touched path under
  `~/.claude/backups/ctx-rent-x-<ts>/` first, with a revert script. Keep every agent a hook dispatches by name.
- Measure with frozen contracts committed before probes; counterbalanced (control twice, arm order swapped, the source
  isolated on the live path, not only in a scratch config) — the C3c/C3d confound must not recur. Haiku probes, `claude -p`.
- Ratchet the measured floor into `tools/test_floor_regression_gate.py` (down only).
- Acceptance: measured call-1 floor delta per row with N >= 2 per arm; no capability needed by a hook lost.

### Phase 3: W2 CCR main canary
**Depends on**: Phase 1. P50 8M, ceiling 16M.
- `mods/cpp-cognitive-runtime/hooks/policy.ts`: per-process opt-in `CCR_MAIN_MODE=enforce`; unset keeps `main:'shadow'`.
  Test red first. `claude plugin test mods/cpp-cognitive-runtime`, release via `tools/ccr_release.py release`, start-receipt
  smoke shows the release id and `main` mode.
- n >= 3 counterbalanced bounded Work Units, shadow vs enforce, in REAL interactive panes launched after the release
  (pywinpty driver as in the 2026-10-25 canary; driver waits for turn.complete before /exit). Same generation both arms.
- Report processed tokens, cache-weighted cost, calls, repairs, rereads, answer correctness. Decide (with numbers) whether
  enforce should become the main default; flipping the default is a Phase 8 ratchet item, not done here.

### Phase 4: W3 Successor compiler + rollover economics
**Depends on**: Phase 3. P50 7M, ceiling 14M.
- Close `vault/backlog/2026-10-27_ccr-a2-landing-remaining.md` row 5 smoke: a real `/clear` -> `/kresume` successor whose
  receipt shows `frontier.basis:"capsule"` (`CPP_ROLLOVER_STATE_DIR` = empty dir).
- Fresh-start cost: bootstrap tokens, page-ins (rereads in first N calls), time to first correct action, on >= 2 successors.
- `tools/gsd_epoch.py` breakeven: from shadow to an advisory for interactive panes at a semantic boundary
  (continue-rent x expected calls vs successor cost), reusing its inputs. Advisory only; no auto-rotation of a human pane.

### Phase 5: W4 Carriage in main + Safe-to-Forget
**Depends on**: Phase 3. P50 6M, ceiling 12M.
- Extend the CCR B5 tool-output projection and B3 thinking-carriage handling to main under `CCR_MAIN_MODE=enforce`.
- Safe-to-Forget: project only when the raw output is durable on disk with a pointer the model can page back, and no open
  obligation names it. Count page faults (re-fetch of a projected object). Mutation drill: a projection without a durable
  raw must be refused.

### Phase 6: W5 Waiting / admission (shadow)
**Depends on**: Phase 1. P50 3M, ceiling 6M.
- Classify model calls made while a unit was waiting (poll, status re-ask, sleep-check) from real transcripts; count and
  cost them. Feed the class into `tools/ccr_pgo.py` admission in shadow. No blocking.

### Phase 7: W6 Replay + champion/challenger
**Depends on**: Phases 2-5. P50 5M, ceiling 10M.
- Corpus (plan section 2): KSR-style, long repo task, cpp-gsd-long mission, successor, debugging, sparse-capability task,
  one task that genuinely needs large coherent context. Current policy vs candidate; X -> X-prime with quality metrics.
  Counterfactual replays are ESTIMATE; live arms are MEASURED. Never mix the labels.

### Phase 8: W7 Institutionalise + master done-gate
**Depends on**: all. P50 4M, ceiling 7M (closeout reserve 5M is separate).
- UKDL Hard Rules / Process Rules / Traps only where evidence supports them; Knowledge Vault incidents (Error -> Immunity).
- Baseline Ratchet per plan section 7, through the existing baseline machinery (`tools/baseline_ledger_append.py`).
- Dogfood: repeat a comparable bounded unit on the new path; compare with this mission's Phase 1 own-spend rows.
- `vault/programs/ctx-rent-x/done_gate.py`: 32 conditions of the Owner contract, each a receipt with a measured value or a
  justified UNKNOWN; exit 0 only when all required pass. Then run every command of plan section 8; all exit 0.
- Final handoff block per the Owner contract, written to `vault/programs/ctx-rent-x/HANDOFF.md`.
