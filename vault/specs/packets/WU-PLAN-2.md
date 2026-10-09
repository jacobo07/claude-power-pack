done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_gsdx_chain.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-PLAN-2.json

# WU-PLAN -- programme planner epoch: compile the next units from L1 and append them to the chain

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3 (W3..W8, the budget table,
tranches). You replace the resident coordinator for ONE planning epoch. Fresh worker, no Agents, no GSD commands,
never push, never Set-Location / cd. Work class: COMPILATION (read structured inputs, write packets and data).

## 0. Inputs (read only these)
- `vault/specs/gsdx-factory.RECEIPT-L1.json` and `vault/specs/gsdx-factory/l1/GRAPH.md` (the remaining work graph).
- The Master Plan sections 2-3 (grep -n "## 2\|## 3\|## 4" to find them; read those ranges only).
- `vault/specs/gsdx-factory/chain.json` (the chain the 15-minute tick `tools/gsdx_chain.py tick` executes).
- One existing packet as a template: `vault/specs/packets/WU-L1.md` (header lines, sections 0-2, budget/closeout).

## 0b. L1 limits you must correct (coordinator, 2026-10-09)
- GRAPH.md `n` and `cost` are placeholders (n = rows/6 or rows/4); never copy them. Estimate n per unit from the work it
  names (files to change, gates to write, GEX44 jobs to wait on), and say how in one line per unit.
- Open recon phases (P2 close, P3, P7 CP50, P8, P9) are one GRAPH row (U-W7). Decompose them from the recon ROADMAP
  `### Phase N` sections (read only those ranges) into units of at most 25 model calls each.
- Measured references: L1 itself = 1,804,651 + a 98,070 no-op renewal (route target 1.3M: +46%); S1 = 2,708,995 at 40
  model calls; gen3 recon phase leases 1.0-2.4M each (TRANCHE-CP50.md).

## 1. Rules for every packet you write
- Header: `done_gate:` (a command that exits 0 only when the unit is proven), `work_tree:`, `receipt:`.
- Section 0 facts must be checked by you now (a path exists, a commit is an ancestor); write nothing you did not verify.
- Never schedule edits to files another programme owns while its units run: ce-lifecycle-v3 owns gsd_mission.py,
  hooks/session_budget_guard.js, modules/provider_routing/ledger.py, tools/mission_spend.py; cost-collapse owns
  tools/route_admission.py. A unit that must touch them gets `wait` on
  `C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-INST2-receipt.md`.
- Recon-factory units: `cwd` = `C:\Users\User\Apps\recon_work\wt_keosdtk_home`, never touching its pre-existing dirty
  paths (pathspec commits only). GEX44 legs go through the factory's own GEX44 job path (as P2b did), not a new one.
  Full WSR is out of scope.
- Route per unit: envelope target = C(n)*1.3 with C(n) = n*F + g*n*(n-1)/2 (slim-t2 F=19,000 g=1,700; top F=121,000
  g=2,000), warn = 1.3x target, stop = 1.7x target, `calls` = tool calls = 1.6 x model calls; worker `calls` = n.
  If a unit's C(n) exceeds 1.5M on slim-t2, split it into epochs of at most 25 model calls.
- Every packet ends with the protected closeout: at (calls wall - 7) tool calls stop new work, commit green, write the
  receipt (PARTIAL allowed, with remaining items).

## 2. Steps
1. Write packets + routes for the next block: at most 4 units in dependency order from GRAPH.md (prefer units with no
   wait first: recon P2 close, A-G units without owned-file edits). Commit.
2. Append them to chain.json (`id`, `packet`, `route`, `receipt`, `after`, `wait`, optional `cwd`), then append one more
   unit `PLAN-<n+1>` after the block's last unit. Its packet is a copy of this file saved as `WU-PLAN-<n+1>.md` with
   the receipt line changed to `RECEIPT-PLAN-<n+1>.json` (the chain keys on packet path, so each epoch needs its own).
   Keep chain.json valid JSON.
   Run `python tools/gsdx_chain.py tick --dry-run` and paste its row into the receipt. Commit.
3. Budget check: sum of the block's route targets + goal used (from `python C:\Users\User\.claude\skills\claude-power-pack\tools\mission_spend.py goal-status --goal gsdx-factory-2`)
   must stay <= 40,000,000; if the forecast for the REST of the programme (GRAPH.md totals) makes the total exceed
   40M, write `"owner_needed": "<one sentence>"` in the receipt and append nothing beyond the current block.
4. Receipt `vault/specs/gsdx-factory.RECEIPT-PLAN-2.json`: status DONE/PARTIAL, units compiled, chain rows added, the
   dry-run row, programme forecast (lower / expected / safety) recomputed from GRAPH.md. Commit.

## 3. Budget and closeout (protected)
About 14 model calls / 24 tool calls. At 17 tool calls stop compiling, commit, write the receipt. End your final
message with `HANDOFF NOTE:` and one line.
