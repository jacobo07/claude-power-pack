# Roadmap: Cognitive Economy gen2 -- Amendment A2 (ce-a2)

Card of record: `vault/programs/cognitive-economy/gen2/AMENDMENT-A2-2026-10-07.md` (Owner-approved 2026-10-07).
State: `vault/programs/cognitive-economy/gen2/ledger.json` (blocks `obligations`, `a1`, `a2`).
Iteration lens (after Phase 1, after any falsified hypothesis, before Phase 8 promotion):
`C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt`.

## Operating constraints (every phase)

- Repo: worktree `C:\Users\User\Apps\pp-ce-a2`, branch `ce/a2`. This mission is the ONLY writer here. Never write
  the main checkout, `C:\Users\User\Apps\pp-ce-gen2` (another pane), any other worktree, or `~/.claude/`.
- Compiled grammar: each phase is executed directly by the worker in EXECUTION mode from this roadmap + the A2 card.
  No GSD discuss/research/plan sub-workflow, no Agent unless the phase states a positive-ROI reason.
- Git: `& 'C:\Program Files\Git\cmd\git.exe' -C C:\Users\User\Apps\pp-ce-a2 ...`. Python:
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `$env:PYTHONIOENCODING='utf-8'`. PowerShell
  tool for every git/python call. One msgfile per commit, verify `git log -1 --format=%s`, never push.
- Hermetic tests (state dirs redirected); RED first; guards ship with a positive control; `tools/mutation_drill.py`
  for mutation evidence; `python modules/liveness/reachability.py` exit 0 at phase end for new modules.
- Metered beats self-reported; null is never zero; a phase over 1.5x its cap stops, records the diagnosis in its
  EVIDENCE.md and changes method.
- Admission is consumed per epoch (gen3 law; a relay without it stalls, as m-595b674b8e41 shows). Before ending an
  epoch with `HANDOFF NOTE:`, re-admit the next one: `python C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py
  admit --mission m-72fba680c953 --route vault/programs/cognitive-economy/gen2/evidence/a2/route-epoch.json`;
  record its verdict in the phase EVIDENCE.md. RECOMPILE means stop: the remaining budget no longer fits.
- Never ask the Owner mid-run: write the blocker into the phase EVIDENCE.md, mark it BLOCKED, continue with the next
  unblocked phase.
- Every phase ends with `.planning/workstreams/ce-a2/phases/<NN>/EVIDENCE.md` (commands, exit codes, observed output,
  Production Reality verdict PROVEN / OBSERVED / UNJUDGED / BLOCKED, ledger fields moved, UKDL candidates), then its
  checkbox below is ticked and STATE.md updated in the same commit.

## Phases

- [ ] **Phase 1: A2-0 Gate truth**
- [ ] **Phase 2: A2-1 Metered attribution including the coordinator**
- [ ] **Phase 3: A2-2 Presence contract and baseline negotiation**
- [ ] **Phase 4: A2-3 T3 offline replay (boundary census, epoch policy, concurrency)**
- [ ] **Phase 5: A2-4 T7 prompt-rent retirement**
- [ ] **Phase 6: A2-5 Amortization-gated unfreeze**
- [ ] **Phase 7: A2-6 EDD Phase 2 self-hosting canary armed**
- [ ] **Phase 8: A2-7 UKDL, CBR and independent review**

## Phase Details

### Phase 1: A2-0 Gate truth

**Goal**: `--final` reports only genuinely open obligations, so every later phase is judged by a gate that can see.
**Depends on**: Nothing
**Requirements**: C2, C3, C15, C16
**Success Criteria** (what must be TRUE):

  1. Root cause of "check tool missing" for `tools/test_ce_t1_state.py` / `tools/test_ce_t1_lifecycle.py` found
     (source read in `tools/cep_gen2.py`), fixed red-first; C2 and C3 pass in this tree.
  2. Obligation checks run with the interpreter actually present on Windows and Linux (C15/C16 use `python3`).
  3. gen3-envelopes strike count in ledger `a1.families` set from the T1/T1b receipts with file:line evidence.
  4. Cap 0.5M processed.

### Phase 2: A2-1 Metered attribution including the coordinator

**Goal**: Program spend is measured per call, the coordinating pane included, and receipts are judged by metered calls.
**Depends on**: Phase 1
**Requirements**: C13, C16, C20
**Success Criteria** (what must be TRUE):

  1. `measure/turns.py --attribute` (A1 G3-G5: write-path + lineage attribution, message-id dedup, controls) exists
     and has a both-pole test.
  2. `check_receipt` fails a receipt whose self-reported boundary count is below the metered call count (EDD WU-1:
     3 vs 16 is the RED fixture).
  3. Ledger `a1.spent` and `a2.spent` filled with sources, or left null with the exact UNKNOWN named.
  4. Cap 3M processed.

### Phase 3: A2-2 Presence contract and baseline negotiation

**Goal**: With CPP present, a plain desired-state task gets the strongest certified baseline without being asked;
tiny tasks stay tiny.
**Depends on**: Phase 2
**Requirements**: C17, C18
**Success Criteria** (what must be TRUE):

  1. The existing gsd_x tier hook path (`modules/gsd_x/cli.py`, `capability_runtime`) and `.pp-capabilities` are
     extended, not duplicated, to resolve per-project certified capabilities; a project without evidence gets nothing
     invented. Shadow mode first; kill switch env var.
  2. Executable checks for C17 and C18 registered in the ledger and passing on CPP, one mature project and one weakly
     integrated project (read-only probes of those repos; no writes there).
  3. `floor_regression_gate` delta <= 0. Any live-hook change is an OWNER STEP in EVIDENCE.md, never applied here.
  4. Cap 4M processed.

### Phase 4: A2-3 T3 offline replay (boundary census, epoch policy, concurrency)

**Goal**: The highest lifetime-cost boundary/read/transport classes are named from history, with a shadow epoch policy.
**Depends on**: Phase 2
**Requirements**: C8, C11
**Success Criteria** (what must be TRUE):

  1. `measure/turns.py` extended (no new census) to settle the 52% "unsettled" class by sampling.
  2. Offline replay of KEEP vs DEALLOCATE, idle rebuilds and estate concurrency; host TTL recorded as host floor.
  3. Measurement receipt (kind `measurement`) with the top-3 classes by lifetime cost. Charged to the A1 cap.

### Phase 5: A2-4 T7 prompt-rent retirement

**Goal**: At least one hot mechanical instruction leaves the always-loaded prefix because machinery now enforces it.
**Depends on**: Phase 4
**Requirements**: C12, C18
**Success Criteria** (what must be TRUE):

  1. Compiler-side retirement (HARD RULES mirror or equivalent) with the enforcing mechanism cited and tested.
  2. `floor_regression_gate` shows the measured floor delta.
  3. `~/.claude/CLAUDE.md` retirements, if any, delivered as an Owner-applied diff file only.
  4. Cap 3M processed.

### Phase 6: A2-5 Amortization-gated unfreeze

**Goal**: At most one frozen tranche (T2, T4, T5, T6, T8) is unfrozen, and only by its own amortization record.
**Depends on**: Phase 4
**Requirements**: C15
**Success Criteria** (what must be TRUE):

  1. An A1-1 record (build cost, run cost, measured and forecast saving, confidence, break-even, retirement
     criterion) for each candidate, from Phase 4 evidence.
  2. Unfreeze only if break-even <= 30 days; otherwise record "nothing unfrozen" with the numbers. Both outcomes pass.

### Phase 7: A2-6 EDD Phase 2 self-hosting canary armed

**Goal**: EDD Phase 2 (first BUILD phase) is packeted and armed under the new baseline with an envelope derived from
the EDD reforecast, so C19/C20 get real evidence.
**Depends on**: Phase 3
**Requirements**: C19, C20
**Success Criteria** (what must be TRUE):

  1. Proof of Non-Work on EDD Phase 2 first (GEX44 `~/missions/edd-run` state read over ssh, read-only).
  2. Forecast including coordinator computed; if > 1.5x EDD Phase 1 end-to-end (~23.2M) the canary is HELD and the
     numbers recorded (valid outcome).
  3. Otherwise packet + dossier + envelope per `reference_gex44_mission_arming_recipe`, armed with token_estimate;
     the run itself is its own mission, judged later by C19/C20.

### Phase 8: A2-7 UKDL, CBR and independent review

**Goal**: Universal discoveries are recorded once, the baseline ratchets, and an independent review accepts A2.
**Depends on**: Phase 5, Phase 6
**Requirements**: C1, C12, C14
**Success Criteria** (what must be TRUE):

  1. UKDL candidates (duplicate-checked against `vault/knowledge_base/ukdl-universal.md`) written as a candidates file;
     entries into ukdl-universal.md only when it has no foreign uncommitted hunks.
  2. KV causal records for every bug found in A2.
  3. One read-only reviewer (pp-code-reviewer) over the A2 diff; verdict recorded.
  4. `--final` re-run; remaining OPEN obligations listed with their owners. Cap 4M processed.
</content>
</invoke>
