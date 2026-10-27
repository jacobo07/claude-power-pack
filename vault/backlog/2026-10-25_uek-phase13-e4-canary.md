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

## State 2026-10-26: steps 1-2 done, waiting only on RAM (Owner "añade todo al backlog para cuando tenga RAM", 2026-10-27)

Owner 2026-10-26: "approve" (go for Phase 13), then "1" (Phase 13 before CCR-NEXT and CCN). Landed in `ccr/v5`, local, not
pushed: `17defeee` (a retired failed-arm stub is not an attempt) and `b6bfc54a` (chain unparked).

- chain.json: `parked: false` with `unparked_reason`; `yield_root` = CCR-NEXT `m-c60b6defbe97` (55M) and CCN
  `m-b85fa1eacc8c` (25M). They yield the tree only while held and never launched; released, they take it back.
- Envelope 330M -> 723M = the programme ceiling (`mission_spend.py programme-status --goal ccr`). Sync, not new capital.
- route-E4b2 ADMISSIBLE (need 3,458,564 <= 3,500,000). Failed-arm stub `m-50183b34f0eb` retired (never launched).
- Dry tick on the real chain: `arm E4b2`. Live ticks 10:11 and 10:21: `ram_hold free_gb=1.7`
  (`~/.claude/state/ccr-chain-tick.log`).
- Suites at landing: CHAIN 41/41, UEK 54/54, UEK_LEDGER 69/69, UEK_AUTH 35/35, SUPERSEDE 22/22.

## What runs by itself once RAM is free

PP-CcrChain-Tick (every 10 min) runs python only at >= 4 GB free, and arms E4b2 only at >= 4.5 GB on two samples
(else `wait_resource`). No Owner action is needed beyond freeing RAM (close idle panes / claude sessions; /clear and
/compact do not release claude.exe memory).

## Pending, in order (when RAM allows)

1. Watch the first E4b2 arm: `~/.claude/state/gsdx-chain.jsonl` and the mission's receipt `WU-E4b2-receipt.md`.
2. When E4b2 writes rows into `vault/programs/ccr/v5/evidence.jsonl`, update the Phase 6 two-row pin
   (`tools/test_uek_safety.py`) deliberately, in the same commit that records those rows.
3. E4c2 arms after E4b2 only with Static Feasibility, authority and discriminative-power receipts. E4 verdict from
   `closure.json` only.
4. After E4c2 ends: release CCR-NEXT and CCN (no release task exists: PP-CCRNext-Start / PP-CCN-Start were never created).
   Their 80M of authority exceeds goal ccr's current window remaining (40.2M on 2026-10-26), so a window/capital
   check comes before release.
5. ccr/v5 commits stay local; pushing is an Owner decision.
