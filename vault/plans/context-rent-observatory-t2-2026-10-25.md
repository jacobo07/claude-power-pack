---
covers: [ctx-rent-obs-t2, context-rent-observatory, worker-boot-floor, cr-o5-cws, cr-o6-estate-rent, c2-contract]
status: AWAITING OWNER APPROVAL (2026-10-25). Nothing armed, no authority moved, no worker launched.
mode: EXECUTION (W5-W7). No ULTRA-PLAN.
parent: vault/plans/context-rent-observatory-2026-10-25.md (tranche 1, sections 7-8)
---

# Context Rent Observatory, tranche 2

## 0. Verdict
- Tranche 1 did not reach its saturation stop: C1 came out REFUTED (direction holds, 76.8% against a claimed 67%), so
  the claim is not certified and the Observatory continues (tranche 1 plan section 8).
- Tranche 2 takes the two "high ROI next" rows of tranche 1 section 7 and nothing else:
  1. **W5** the mission-worker boot floor, measured from transcripts that already exist, then one frozen contract (C2)
     on a single removable source;
  2. **W6** Projected Estate Rent: floors x session counts over one measured week.
- The "PLAN first" and "speculative" rows of section 7 stay deferred.

## 1. Facts this plan rests on (read 2026-10-25)
| fact | source |
|---|---|
| mission-worker boot floor 100-215K per call | tranche 1 plan section 7 |
| laptop interactive call-1 floor 106,769 (36d35fab); 147,977 (5cadebe8) | `ctx-rent-obs/b1/slice-b-census.laptop.json` (e2dc477a) |
| GEX44 call-1 floor 67,568 / 67,561 / 67,561; not comparable with the laptop | `ctx-rent-obs/B1.md` |
| `tools/context_floor_census.py` takes transcripts or session ids, `--json` | its argparse, lines 303-306 |
| `tools/floor_regression_gate.py --probe [--cwd]` runs a fresh headless probe | its argparse, lines 1272-1292 |
| tranche 1 spent 8,874,921 against P80 6.7M (1.32x) and a 7,000,000 ceiling | `ctx-rent-obs/STATUS.md` LEDGER moves |
| ccr-vm WU-T0B is written and has never run (no receipt, no T0B commit beyond the plan and route) | `git log --all --grep T0B`; `vault/programs/ccr-vm/` |

## 2. Boundary with ccr-vm T0B (no double measurement)
- T0B task 1 measures HARD_HOST_FLOOR against CPP_ADDED_FLOOR on a **bare headless call**. Tranche 2 does not.
- T0B tasks 2 (reclamation experiments) and 4 (flamegraph) stay with T0B. Tranche 2 does not.
- W5 measures only the **mission-worker** boot: the worker prompt, its card, its first tool call.
- If T0B lands first, W5 cites its HARD_HOST_FLOOR as the lower bound. Otherwise W5's lower bound is UNKNOWN, not zero.

## 3. Work units (fresh Sonnet worker, laptop plane; pathspec commits under `vault/programs/ctx-rent-obs/` only)

### W5a Worker boot census (no model probes)
1. Pick N >= 5 mission-worker transcripts on the laptop from the last 14 days, from at least 2 missions. List the
   selection rule and the session ids before measuring.
2. Run `context_floor_census.py <sids> --json b2/worker-boot-census.json`.
3. Per source: chars, tokens, and whether the worker read or used it before its first tool call (from the transcript).
4. Output `B2.md`: the worker boot floor with its spread, and the largest source unused before the first tool call.

### W5b C2: one frozen reduction contract
1. Commit `contracts/C2.json` FIRST: the source named by W5a, the existing mechanism that removes it (an env knob or
   flag that already exists; **no settings.json edit, no new code**), the instrument, the pass rule (worker still
   reaches its first tool call with the card read) and the frozen band for the saving.
2. If no existing mechanism removes that source: verdict UNMEASURABLE, stop W5b, spend nothing more.
3. Otherwise run 2 matched pairs through `floor_regression_gate.py --probe --cwd <worker cwd>` with the worker prompt.
4. Verdict CERTIFIED / REFUTED / UNMEASURABLE in a commit after the contract commit.

### W6 Projected Estate Rent (no model probes)
1. Count laptop sessions per class (interactive pane, mission worker, subagent) over one measured week, from transcripts.
2. Multiply by the class floor (B1 laptop for panes, B2 for workers). State which numbers are measured and which are
   carried from another class.
3. Output `ESTATE.md`: weekly floor rent per class and in total, each figure with the command that produced it.

### W7 Receipt
`STATUS.md` tranche 2 section and RESUMPTION update; book the worker's spend on `ctx-rent-obs` by `goal-settle`
(UTC cut or without `--measured`, never a local-time `since_iso`).

## 4. Done-gates
- **W5a:** `B2.md` with N >= 5 and its spread; selection rule committed before the census ran.
- **W5b:** a verdict row whose contract commit precedes its data commit, or UNMEASURABLE with the reason.
- **W6:** `ESTATE.md` where every figure names its command.

## 5. Budget (processed input incl. cache reads; Sonnet worker floor ~70-110K/call)
| unit | lower bound | P50 | P80 | P95 |
|---|---:|---:|---:|---:|
| W5a census | 0.3M | 0.6M | 0.9M | 1.2M |
| W5b C2 (4 probes ~0.2-0.45M each) | 0.0M | 1.2M | 1.8M | 2.4M |
| W6 estate rent | 0.3M | 0.5M | 0.8M | 1.1M |
| W7 receipt + meta | 0.2M | 0.4M | 0.5M | 0.7M |
| **total** | **0.8M** | **2.7M** | **4.0M** | **5.4M** |

- **Lineage correction:** tranche 1 ran 1.32x over its P80. 4.0M x 1.32 = 5.3M, inside P95.
- **HARD AUTHORITY asked:** 4,000,000 for tranche 2 (P80). The ctx-rent-obs programme would become
  8,874,921 settled + 4,000,000 = **12,874,921**. That also covers the 1,874,921 overdraft of tranche 1.
- **Stop-loss:** a unit over 2x its P80; 3 epochs without a commit; C2 edited after data was read.
- **Saturation stop:** if W5a finds no source above 10K unused before the first tool call, skip W5b and record it.
- **Payback:** UNKNOWN by construction. W6 is what turns floors into a weekly figure the Owner can rank levers by.

## 6. Owner boundaries
- Capital: `approve ctx-rent-obs only` on a packet for 12,874,921, or `goal-programme --goal ctx-rent-obs --value
  12874921 --owner` typed in a real terminal. Nothing launches before that.
- No settings, hooks or code change in this tranche; any reduction found becomes a proposal, not an edit.
