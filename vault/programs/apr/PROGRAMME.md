# Autonomous Programme Recovery (APR) -- common brief for every unit worker

Owner approval: inline plan "y", 2026-10-11, coordinator pane (goal `apr`, cap 20,000,000; EWC `max_residuals 2` +
`acceptance` blocks; install into the live checkout branch feature/knowledge-acquisition).
`chain.json` here is ticked by the zero-model task PP-AprChain-Tick. No orchestrator exists above you. Your packet
names what is yours. Spend for the whole programme is goal `apr`; the coordinator pane is outside it.

## The defect this programme removes
EWC unit E2 finished its work (commit 25f83975, 56/56) and wrote a receipt with no `Status:` line. The chain read
UNREADABLE, `max_residuals 0` made that `stopped_without_done`, and the chain sat until a human added the line
(`vault/programs/ewc/KNOWLEDGE.md` K5). A recoverable, internal, evidence-derivable fault needed the Owner.

Root cause (measured, APR-1): three receipt parsers disagreed. `gsd_mission._receipt_present` called a Status-less
receipt present (mission COMPLETED, halt-continue skipped); `gsdx_chain.receipt_status` called it UNREADABLE (unit
not done). Nobody owned the unit. Second cause: the chain's only completion evidence is model-authored text; a unit
in `chain.json` carries no acceptance contract the runtime could check.

## Already done (APR-1, live at 741479f3) -- read before changing anything
- `tools/receipt_judge.py`: the ONE reading of a receipt. `receipt_status`, `is_closed` (explicit verdict),
  `is_done`, `NOT_CLOSED`. gsdx_chain, gsd_mission (`_receipt_present`, `receipt_complete`, the slim-finish reason)
  and mission_steward R1 all call it. Never add a fourth parser: extend this module.
- A worker that ends with an unclosed receipt is now HALTED "receipt not closed (status X)" and gets the existing
  bounded halt-continue renewal (`HALT_CONTINUE_MAX_RENEWAL` 2) -- the K5 case recovers without the Owner.
- Gates: `tools/test_receipt_judge.py`, `tools/test_halt_continues.py` (V-APR-K5-*), `tools/test_mission_steward.py`.

## Target (what the remaining units add; EXTEND, no new engine)
1. Machine seal: optional per-unit `acceptance` in chain.json; a zero-model finalizer runs it and writes
   `<receipt>.seal.json` (provenance: sealer, receipt sha256, gate rc+tail, commits). The chain trusts the seal over
   prose. A worker DONE whose declared gates fail is FALSE_DONE: refused, never advanced, residual instead.
2. Residuals, not halts: a recovery-class table with attempt budgets; the same failure twice with no new evidence
   changes strategy (route rung) and, with none left, records an explicit HUMAN_GATE row with the evidence.
3. Event-driven advance: the sweep's terminal transition of a packet mission ticks the owning chain at once; the
   10-min tick stays as a repairing watchdog. One per-goal tick lock; exactly one next-unit arm under any race.
4. Bounded silence + health: `gsdx_chain.py status` answers "is it working" without transcript forensics; an ACTIVE
   programme with no live mission and no recorded reason past the window triggers recovery or a visible alert.
5. Budget reforecast from measured unit spend before each arm; explicit `pause_budget` instead of a silent overrun.

## Paths
- Work tree (your cwd): `C:\Users\User\Apps\wt_apr` (branch apr/self-closing). All code commits go here. Never
  write code into the live checkout except in APR-4 (install).
- Programme files + receipts: `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\apr\` (live checkout).
  Other panes commit there too: pathspec commits only. The EWC programme runs in parallel (`C:\Users\User\Apps\wt_ewc`,
  goal ewc): never touch its tree; its chain.json is changed only by APR-4.
- `tools/gsdx_chain.py`, `tools/gsd_mission.py`, `tools/mission_steward.py` are LOADED LIVE from the live checkout by
  the sweep and every chain tick. Your edits in wt_apr are inert until APR-4 installs them. That is deliberate.

## Session loop
1. Tests first (RED, and show it red against the old code), then code. Pathspec micro-commits ending with
   `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. Never `git add -A`. Git via
   `& 'C:\Program Files\Git\cmd\git.exe' -C <path>`; never Set-Location into another goal's root.
2. Close: overwrite `WU-<id>-receipt.md` beside your packet. Line 1 `# <id> receipt`, line 2 `Status: DONE`, then
   commits, PROVEN / NOT_PROVEN per claim with the command and its counts, calls used, what the next unit must know
   (<= 8 lines). Commit it (live checkout, pathspec). (After APR-1 a receipt without a closing Status is a fault and
   your mission is renewed to finish it -- write the line.)
3. Unit too big (stop starting new work at 85 % of your calls): commit what is done, INSERT a continuation unit into
   `chain.json` right after yours (id `<id>b`, `after` = your id, packet `WU-<id>b.md` with the exact remaining steps,
   route = route-S.json), then receipt `Status: DONE`; commit all three together. Never write PARTIAL.
4. Blocked on something only the Owner can do: receipt `Status: BLOCKED_HUMAN` with the exact command/action. Only:
   writes the classifier denies (~/.claude/hooks, settings.json), capital, credentials, push.
5. Before ending a session, list your open obligations; if one is agent-owned and actionable, do it.

## Hard constraints
- Windows: git/python via the PowerShell tool with absolute paths (`C:\Users\User\AppData\Local\Programs\Python\
  Python312\python.exe`). No Bash for git/python. Background commands SOLO in their batch.
- Backward compatibility is a gate: every live chain (ewc, tennis-rf, cp50, ctx-rent ...) loads the same code. A chain
  or unit without the new fields behaves exactly as before; prove it with a test, not a sentence.
- No `/gsd-autonomous`, no EnterWorktree, no push, no cap change. Agent spawns only where your packet allows (APR-4).
- Every guard ships with a test that drives its red branch and a positive control; mutation drills through
  `tools/mutation_drill.py` only (never mutate a live-loaded file in place).
- Iterate with `C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` at each
  failure (read once per session).
- Every bug found: an entry in `vault/programs/apr/KNOWLEDGE.md` (symptom, trigger, root cause, impact, fix,
  prevention, proof, epistemic status). APR-6 promotes candidates.
