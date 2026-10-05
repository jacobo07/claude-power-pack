# Roadmap: E1 resident-rule ablation (cognitive-economy-e1 workstream)

Contract of record: `vault/programs/cognitive-economy/e1/ADDENDUM-E1.md` (committed `bc70934b`, before any run).
It is binding and immutable for this run: gates, design, stopping contract and decision table come from it,
never from judgement during the run. Packet: `vault/programs/cognitive-economy/post-reset-packet.json`.
Preflight gate 1 evidence: `vault/programs/cognitive-economy/measure/e1_mechanical_{laptop,gex44}.json`.

Principle: verified quality outranks token reduction. A ceiling is "no loss observed", never "no effect".
UNKNOWN, INCONCLUSIVE and UNMEASURED are never PASS.

## Operating constraints (every phase)

- Host GEX44. CLI for every counted session: `/home/kobii/.local/bin/claude` (2.1.289); `/usr/local/bin/claude`
  (2.1.113) cannot use the model and must never be used. Model `claude-opus-5-5`.
- Own paths only: `vault/programs/cognitive-economy/e1/**` and `.planning/workstreams/cognitive-economy-e1/**`.
  Read-only: everything else, including `.planning/workstreams/cognitive-resource-os/**` (the P3 harness and its
  task banks are another workstream's: copy what you need, never edit them), `tools/gsd_mission.py`,
  `vault/programs/cognitive-economy/ledger.json`, and anything under `~/.claude/`. Never write `~/.claude`.
- Commit by explicit pathspec, and verify `git log -1 --format=%s` after each commit. Never push, reset, clean,
  stash, amend or force.
- Durable output: commit results after EVERY counted pair, so a crash or rotation loses at most one pair.
- Spend: the counted runs follow ADDENDUM-E1's stopping contract, enforced by code (phase 2), not by
  attention. Never exceed 17,000,000 summed counted context. Reaching it is a STOP, never a request to go on.
- Never ask the Owner mid-run. Anything needing the Owner goes into `e1/OWNER.md` as one line; continue.

## Phases

- [x] **Phase 1: Judgement task bank for 11 rules** - one task per rule, validated without model calls, frozen (completed 2026-10-05)
- [x] **Phase 2: E1 runner with the stopping contract as tested code** - GEX44 port of the P3 judgement path (completed 2026-10-05)
- [ ] **Phase 3: Counted runs** - pairs in contract order until a stop condition
- [ ] **Phase 4: Report** - per-rule decisions, measured tokens, limits; no ~/.claude change

## Phase Details

### Phase 1: Judgement task bank for 11 rules

**Goal**: One judgement task for each of the 11 rules ADDENDUM-E1 names (all 13 packet rules except
technical-failure-to-product-state and scoped-side-effect-authority), in the shape of
`.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/ADDENDUM-R2.md` and its `judgement-r2`
bank: a stub module with `...` bodies and a docstring naming the caller and what the result drives, the prompt
"implement them", and a hidden grader copied in only after the session.
**Depends on**: Nothing
**Requirements**: E1-BANK
**Success Criteria** (what must be TRUE):

  1. Every task's judgement checks test the decision its rule governs, and its rule is named in the bank index.
  2. Validation with no model calls: each selftest is OK, and a naive solution fails ONLY its judgement
     checks. The log is committed beside the bank.
  3. No grader is reachable from a session's working tree. Proven by listing the run tree a session would see.
  4. The bank is frozen by one commit whose hash is recorded in `e1/BANK_FROZEN_AT`.

**Plans:** 5/5 plans complete

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — tracer: driver `_e1_common.py`, POSIX `validate_bank.py`, its V-E1BANK tests, index builder; gceg + eaat tasks validated in fresh BASE worktrees (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — hfee, dcme, vpdt judgement tasks (wave 2)
- [x] 01-03-PLAN.md — cpc, slai, pert judgement tasks (wave 2)
- [x] 01-04-PLAN.md — det, pyt, cr judgement tasks (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-05-PLAN.md — move bank-draft/ to bank/, freeze-check, index.json, VALIDATE-E1 11/11 log, single freeze commit, BANK_FROZEN_AT (wave 3)

**Cross-cutting constraints:**

- `validate_bank.py validate --only <id>` prints VALIDATE-E1 1/1 for each, with bank_in_tree=none and worktree_removed=True
- Every judgement check in these files tests the decision its rule governs, recorded in JUDGES

### Phase 2: E1 runner with the stopping contract as tested code

**Goal**: `vault/programs/cognitive-economy/e1/e1_runner.py`, a POSIX port of the P3 runner's judgement path
(fresh worktree at the frozen bank commit, prepare, one headless session per run, grade, metrics from the
transcript). Arm B = `--settings {"claudeMdExcludes": [the 13 absolute paths under /home/kobii/.claude/rules]}`.
**Depends on**: Phase 1
**Requirements**: E1-RUNNER
**Success Criteria** (what must be TRUE):

  1. Every stopping-contract clause is code: order by rule bytes, alternation, one pair per rule, the rerun-once
     validity rule, per-rule decision, harm stop (4 losses in the first 8 valid pairs), spend stop (17M summed
     counted context), and the gate-1 positive control on the first pair (B at least 15,000 below A).
  2. A test with a fake session drives every stop branch red and green. No model calls.
  3. Before the first counted run, the runner re-checks the 13 LF sha256 pins against the packet and refuses
     on any mismatch.

**Plans:** 4/4 plans complete

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — tracer: one counted run of J-gceg_product_page end to end with a fake CLI process (worktree at BASE, scrub + stub, red precondition, session argv, grade, transcript metrics, validity); e1_contract.py validity/spend; no-model guard (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — stopping contract as pure code: order, alternation, decision table, positive control, harm, spend, replay/next_action state machine, pair and stop records (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — preflight refusals: pins, CLI path/version, bank drift vs BANK_FROZEN_AT, freeze_check, BASE, index order, results; `preflight` subcommand (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-04-PLAN.md — durable campaign loop: drive, reconcile, commit per pair, resume; `plan` and `run` subcommands; E1_PASS=60/60 (wave 4)

**Cross-cutting constraints:**

- Plans are sequential: all four write `vault/programs/cognitive-economy/e1/test_e1_runner.py` (one phase gate, `E1_PASS=n/n`)
- No model call in any test; `e1_runner.py run` is never invoked in Phase 2 (only `plan` and `preflight` from a shell)

### Phase 3: Counted runs

**Goal**: Run `e1_runner.py run` to its contract stop. Results go to `e1/results.jsonl`, one commit per pair.
**Depends on**: Phase 2
**Requirements**: E1-RUNS
**Success Criteria** (what must be TRUE):

  1. Every counted run is recorded with validity, grade, first-call context, total context and output tokens.
  2. The run ended on a contract condition (all 11 decided, harm stop, spend stop or positive-control stop), and
     that condition is named in the last record.

### Phase 4: Report

**Goal**: `e1/REPORT.md`: one decision per rule (relocation candidate / stays / no information), with the R2
decisions for technical-failure and scoped-side-effect carried in by reference. Also counted spend, measured
first-call delta, a bank-access audit of the transcripts (as in P3 REPORT R2), and the limits stated in
ADDENDUM-E1.
**Depends on**: Phase 3
**Requirements**: E1-REPORT
**Success Criteria** (what must be TRUE):

  1. Each decision cites its pair's run ids. No decision uses tokens as a tie-break.
  2. The report proposes the move list for the Owner and changes nothing under `~/.claude`.
