---
covers: [global-prefix-floor, context-rent, ctx-rent-x, floor-decomposition, claude-md-compile-out, resident-context-admission]
status: AWAITING_OWNER_APPROVAL
date: 2026-11-02
plane: laptop DESKTOP-PMT5BS8, branch feature/knowledge-acquisition @ 98504a8d
supersedes: none (extends vault/programs/ctx-rent-x; does not open a new programme)
---
# Global Prefix Floor (GPF): plan (recovery copy; the inline chat plan is authoritative)

## Reality scan (sources)
- Owner already exists: ctx-rent-x (cb877667, 3c42b965). done_gate.py today: 20 PASS / 1 FAIL (CR-31 dirty tree) / 11 UNKNOWN of 32.
- Skill/agent/MCP listing virtualisation is already LIVE: CCR_MAIN_CANARY default-on, release 0.1.0-265d3d55. L5: call-1 93,139 -> 72,343 (-22.3%, N=4/arm). L6: processed -27.8%, 6/6 correct, 0 page faults.
- Context Performance CI already exists: tools/test_floor_regression_gate (71/71). CCR owns ContextImage/PGO (ccr-v2..v5 plans, tools/ccr_pgo.py).
- This session's call-1: cache_read 27,527 + cache_create 58,116 = 85,645 (including a ~12K-token pasted prompt), which puts the floor near ~72K. MEASURED total; split ESTIMATE.
- Resident CPP text files: 63,474 bytes, ~17.6K tok ESTIMATE (bytes/3.6). PP CLAUDE.md 23.2 KB, ~/.claude/CLAUDE.md 19.3 KB, ~/CLAUDE.md 6.0 KB, rules 12.2 KB, MEMORY 2.8 KB.
- Laptop estate 10-25..11-01: floor_rent 3.86G of 7.47G processed (51.7%). top-level mean floor 90-128K across stale releases (estate-laptop-w0.json).
- Waiting share 1.3% of calls (CR-20 shadow), so call admission for waits is low ROI. S9 Lane A already makes waiting zero-budget.
- Falsified premises: the "60K mystery" and "164K->93-104K" numbers are stale; skill metadata is already names-only; Context Perf CI is not missing.

## Work units (EXECUTION mode; ULTRA not needed, because no ownership fork was found)
W0 floor decomposition: 6 arms x N=3 single-variable ablation on the live release, with the l5 driver (haiku, "reply OK").
   Arms: full | -CLAUDE.md chain | -rules | -memory | -SessionStart injections | -MCP. Residual = Claude Code system + built-in tools (provider floor).
   Output: vault/programs/ctx-rent-x/floor-decomposition.json. Ceiling 5M.
W1 resident doctrine compile-out (largest CPP-controlled block if W0 confirms): classify every block of the 3 CLAUDE.md files + rules.
   Move activation-criteria prose to the skills that already exist. Replace the HR mirror with the digest router (machinery already exists).
   Drop duplicates/superseded. Backups first (HR-001). Measure with the floor_diet contract (N=4/arm) plus the L6 quality arm. Ceiling 12M.
W2 close the ctx-rent-x laptop-plane UNKNOWNs on this plane: Phase 4 successor smoke (CR-11,14,15,16,29) and Phase 5 Safe-to-Forget (CR-09,10,13). Ceiling 15M.
W3 Resident Context Admission: extend floor_regression_gate with per-surface byte/token budgets for the CLAUDE.md chain, rules and memory,
   so a W1 saving cannot silently re-inflate. Add a CBR row separating availability from residency. Ceiling 4M.
Deferred, gated on W0/W1 numbers: dependency graph, ContextImage compiler, PGO/Policy Regret, call admission beyond waits. Owners: CCR v5 / cognitive-economy.

## Gates
Extend ctx-rent-x/done_gate.py: CR-33 decomposition record; CR-34 W1 delta N=4 spread<1%; CR-35 quality non-inferior (L6 6/6);
CR-36 budget pinned in floor_regression_gate; plus CR-09..16, 29 resolved. Exit 0 only if no FAIL and no in-scope UNKNOWN.

## Budget (processed tokens; bottom-up)
W0 3-5M | W1 6-12M | W2 8-15M | W3 2-4M | closeout 3M. Lower 22M, P50 30M, P80 38M, P95 50M.
Authority: stage 1 = 8M (W0 + first W1 delta); stage 2 = +32M (40M total) on a measured W1 delta. Max 12 cycles / 24 h.
Early value: by 8M, either the decomposition plus one measured call-1 delta, or METHOD_PIVOT. Breaker: 2 intervals with no committed measurement -> halt.
NPV (ESTIMATE): -6K tok/call x ~35K top-level calls/week ~= 210M/week (mostly cache reads). Break-even ~2K calls (<1 day).
