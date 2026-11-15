---
status: SPECIFIED 2026-11-16 (Owner "y", pane 4de9b293: "diagnóstico de consumo + spec de los arreglos estructurales, nada rearmado mientras")
tier: T2
covers: [autopilot-stall-fixes, progress-topup, age-aware-topup, worktree-checkpoint-discovery, hold-sha-evidence, halted-branch-continuation]
owner: vault/programs/ascension/autopilot/autopilot.py, evolve.py (live copy /home/kobii/agora/ascension-autopilot on GEX44)
---

# Ascension autopilot: generations stop on mechanisms, not on results

## Incident (measured 2026-11-15, GEX44)
Two hand un-sticks (09:38Z and 15:32Z) re-armed 8 generations. All 5 lanes were stopped again within about 40 min each
time. None of them stopped on a judged result. Each stopped on a different mechanism:

| Lane | Generation | Stopped by | Work actually done |
|---|---|---|---|
| MKW | S65M m-0831a20727ab | cost hold 9.35M/9.5M at 16:09Z, no certificate, so no top-up | 5 commits on `s65m/work` (P1-P3, frozen instrument, 3 dev functions at 100, S60M recheck: the 4 CharStrmReader fns read 100 after `configure.py`); held-out run done, `result.json` **uncommitted**, no checkpoint |
| TENNIS | S56T m-26ef670c62b6 | `older than 16.0 h`, 9 min after an Owner authority raise to 20M | top-up wasted |
| FIFA | S63F m-3b6cf7f24e50 | judge INCONCLUSIVE: the checkpoint path was absolute inside `.claude/worktrees/s63f`, unmerged; then CAPITAL_EXHAUSTED | gates absent from product (rc=2) |
| WIIPARTY | S58W (before) | the hold's `evidence` was a commit sha (`8afbd99`); `hold_checkpoint` returns it as a path, so `discover_checkpoint` parks | needed a hand merge |
| WIIPARTY | S64W | the re-plan was refused: RESEARCH_LANE_CAP 60M would be exceeded | Owner ceiling, out of scope |

**Burn diagnosis.** Command: the per-session usage sum over `~/.claude/projects/*/<session>.jsonl`.

- **S65M:** 77 API turns across 2 workers (sonnet). It processed 9,351,435 tokens: 9.0M cache read (96%), 266k cache
  creation and 81k output.
- **Other generations:** S63F, S64W, S56T and S62K had cache-read shares of 97%, 93%, 94% and 95%.
- **Turn cost:** resident context is 120-180k, so every tool call costs about 120k "processed" tokens. A 10M generation
  buys about 60-80 tool calls, roughly 20-30 min of work.
- **Phase caps:** they are written as if tokens were work. S65M's own `budget.md`: P1 cap 1.5M, used 2.8M.
- **Conclusion:** the workers are not idle. Generations do real work and are cut off before certification, which is
  always their last phase. Top-ups require a registered certificate, so the gate that would fund the certification
  phase can only open after it.

## Changes

### F1. Top-up on proven progress, inside the Owner envelope
`cost_topup` admits on `certified_since(...)` **or** on `progressed_since(product, ls, mid)`. The second is true only
when both of these hold:
- the mission's `binding.head` has at least 1 new commit on the generation branch since the generation's base, or
  since the last top-up's head;
- the gsd_mission ledger has a `cost_mark` row "progress fingerprint moved" for this mission after the last top-up.

The other conditions are unchanged:
- the envelope still needs an `owner_turn`;
- `MAX_TOPUPS` stays at 2;
- `TOPUP` stays at 6M;
- `envelope_admits` and `budget_admits` are still checked.

The ledger row is `auto_topup` with `basis: "certificate" | "progress"` and the commit range. A progress top-up can
never exceed the lane envelope, and it never raises any Owner ceiling: TOTAL, DAY, RESEARCH_LANE_CAP and GEN_CAP stay as
they are.

### F2. Age-aware top-up (Owner or auto)
**Premise to verify before coding (HR-PREMISE-001):** where `max_hours` and `created_at` live in the record, and whether
`authority --extend_hours` exists and applies to a RUNNING mission.

Before any top-up, the autopilot computes `left_h = max_hours - age`.
- If `left_h < 1.5`, it does not top up. It extends the wall when gsd_mission allows that with the same Owner turn
  (`authority --extend_hours`).
- If gsd_mission does not allow it, the lane follows F4 instead. The ledger row is `topup_skipped_age`.
- The same check goes into the hand runbook (the RESUMPTION_FILE note), so an Owner raise is never spent on a mission
  that is minutes from its wall.

### F3. Checkpoint discovery for worktree paths and sha evidence
**`hold_checkpoint`:**
- If `evidence` matches `^[0-9a-f]{7,40}$` or is not an existing path under product or worktree, use `residual`.
- If both are unusable, return "", which keeps the existing "names no evidence" park.

**`discover_checkpoint`:** an absolute path under `<product>/.claude/worktrees/<w>/` is rewritten to its path relative
to that worktree. It then goes through the existing one-branch / ff-only / clean-product rule.
- The checkpoint must be committed on that branch.
- If it is not committed, the lane parks `CHECKPOINT_UNCOMMITTED` and does not judge. Today the judge is called and
  returns INCONCLUSIVE.

### F4. A generation that halts without a checkpoint keeps its branch
**Today:** a TERMINAL mission with no checkpoint hold parks the lane, and the work on the branch is lost to the
planner.

**Change:** if the generation branch has at least 1 commit since its base, the lane re-enters once per generation (key
`continued_for = <mid>`) through a pending plan.
- The verdict is the one the generation was planned from.
- The directive is: "continue `<branch>` at `<head>`; read its budget.md and evidence first; commit what is uncommitted
  before anything new; checkpoint before 75% of authority."

A second halt without a checkpoint parks as today. A halt with 0 commits also parks as today.

### F5. The planner and worker prompts price a tool call
`planner_prompt.md` and the S-phase template state the measured cost: about 120k processed tokens per tool call at the
current resident context. Phase caps are written in tool calls and tokens (`cap 1.5M ≈ 12 calls`), and the checkpoint
phase is reserved before the experiment phases. No policy check changes. This is text only, and it is measured on the
next 3 generations, judged by the share of generations ending with a committed checkpoint.

## Out of scope (Owner decisions, listed in the report)
- RESEARCH_LANE_CAP 60M (WIIPARTY is at the cap) and the research generation cap of 10M.
- The incident-notice channel. `incident_notify_failed` happened 3 times on TENNIS; the choice between Telegram and the
  inbox is still open.
- KSR: no admissible lever, and a new method is needed.
- Reducing the resident context itself (worker model, autocompact 250k, card size). That is a separate measurement.

## Acceptance (test_autopilot.py, plus 52+ mutants killed)
- **V-AP-TOPUP-PROGRESS:** cost hold, no certificate, 2 new commits, `cost_mark` moved: one top-up with
  `basis=progress`.
- **V-AP-TOPUP-NOPROGRESS** (negative): no new commit gives no top-up and an owner_queue row.
- **V-AP-TOPUP-FP-ONLY** (negative): the fingerprint moved but there are 0 commits: no top-up.
- **V-AP-TOPUP-ENVELOPE** (negative): progress, but the envelope is exhausted: no top-up.
- **V-AP-TOPUP-AGE:** age 15 h of 16: no authority raise; extend_hours or F4, with ledger `topup_skipped_age`.
- **V-AP-HOLD-SHA:** evidence `8afbd99...` with an existing residual: the residual is judged.
- **V-AP-HOLD-SHA-NONE** (negative): sha evidence and no residual: park, no judge call.
- **V-AP-CKPT-WORKTREE:** an absolute worktree path, committed and ff-able: product fast-forwarded, then judged.
- **V-AP-CKPT-UNCOMMITTED** (negative): the file exists in the worktree but is uncommitted: park
  `CHECKPOINT_UNCOMMITTED`, no judge.
- **V-AP-HALT-CONTINUE:** HALTED, branch +5 commits: one pending plan with the continue directive, then arm.
- **V-AP-HALT-CONTINUE-ONCE** (negative): a second halt of the continuation parks.
- **V-AP-HALT-NOCOMMIT** (negative): HALTED, 0 commits: park as today.
- **Field check:** a dry run over today's state on GEX44 must:
  - name MKW F1 (it would top up: 5 commits);
  - name FIFA and TENNIS F4;
  - make no decision for WIIPARTY or KSR.

## Rollback
The live files are backed up `*.bak-<pane>-stallfix-<stamp>` before the deploy. Copy them back. No new state beyond
`ls.continued_for` and the ledger `basis` field. Both are ignored by the old code.
