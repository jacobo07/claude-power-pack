# Backlog — UEK Phase 13: E4 self-host canary (UEK-8, OPEX on goal ccr) (2026-10-25)

Source: claude-power-pack coordinator pane, Owner "add phase 13 to claude power pack's backlog" (2026-10-25).
Nothing runs. Not funded: the goal-uek packets (t1-t4) excluded it on purpose.

## State at entry

- UEK Phases 6-12 and 14 are sealed and landed in branch `ccr/v5` (worktree `.claude/worktrees/ccr-v5`), last landing
  `0d912f69` (Phase 14). Local commits, not pushed. Goal `uek` settled 76,096,861 of 79,100,000.
- ccr chain `vault/programs/ccr/v5/chain.json` is still PARKED. Its parked_reason: the single admission reader refuses E4b2
  (route RECOMPILE 3,580,388 > 3,500,000; thin to one top-level worker, no agents, <=26 calls).
- Plan: `vault/plans/ccr-v5-uek-master-plan-2026-10-23.md` (in ccr/v5). Roadmap text lives in the GEX44 clone
  `~/missions/uek/.claude/worktrees/uek-phase8/.planning/ROADMAP.md` (branch mission/uek-p8).

## Success criteria (ROADMAP Phase 13, verbatim in substance)

1. E4b2 arms only through all admissions. While laptop RAM < 4.5 GB on two samples, the honest result is WAIT_RESOURCE.
2. E4c2 arms only with feasibility, authority and discriminative-power receipts (Static Feasibility first).
3. Atoms are appended through `uek.append`; the E4 verdict comes from `closure.json` only (no false E4 completion).

## Why it is laptop work

It arms E4b2/E4c2 on the laptop's ccr chain (PP-CcrChain-Tick). A GEX44 worker cannot reach ccr/v5, the chain tick or the
goal ledger. Measured free RAM on 2026-10-25: about 3.4 GB, under the 4.5 GB floor.

## To start it (in order)

1. Owner decision: fund it as OPEX on goal `ccr` (packet `approve ccr only`); it is not covered by any uek packet.
2. Thin the E4b2 route under the admission limit (one top-level worker, no agents, <=26 calls), then unpark chain.json.
3. Measure RAM twice >= 4.5 GB before arming E4b2; otherwise record WAIT_RESOURCE and stop.
4. Do not create E5-E17 directories. Writing obligation.contract rows into `vault/programs/ccr/v5/evidence.jsonl` needs the
   Phase 6 gate (pins that ledger at two rows) updated deliberately in the same commit.
