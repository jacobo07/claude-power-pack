# WU-T0A -- CCR boundary CWS: reality delta on host 2.1.302 (supersedes the scan half of WU-T0.md)

Goal `ccr-vm` (institutional CAPEX). Packet `capital-packet-ccr-vm` (sha256 ba3d4f55ccad25593381b2bfa00d57ba75a6c1b2f3dacfb86eeeaa4267521192), ceiling 3.5M, stop and write the receipt at 3.0M.
Plan: `vault/plans/ccr-boundary-cws-plan-2026-10-17.md` (read it first; it is the approved contract). Prior state to EXTEND, not redo: `vault/plans/ccr-hypervisor-master-plan-2026-10-16.md` (matrix, owner map, Epoch Zero), `ccr-v4-boundary-cost-2026-10-12.md`, v5 plan in `.claude/worktrees/ccr-v5`.
Run in THIS fresh small-context worker. Never read pane 85b7c296. Mode EXECUTION. Budget this half: P50 1.0M, hard 1.8M, <= 40 tool calls. Then continue straight into `WU-T0B.md` in the same session.

## Forbidden in T0
Code changes in `mods/`, `modules/`, `tools/`; any release, settings.json edit, push; any capital request; any Tennis state change; reading prior transcripts except via a script that prints totals only.

## Tasks
1. Host and CCR: `claude --version`; `~/.claude/ccr/ACTIVE.json`; `policy.ts:8` COMPAT; current share of CCR session-start receipts with `compatible=false` over the last 24h (script, totals only; state the window).
2. Mod capability matrix on 2.1.302: for each surface in plan section 3, class DIRECT_ENFORCEMENT / REWRITE / FILTER / OBSERVE / HOST_FALLBACK / PROTECTED_BY_HOST / UNAVAILABLE / UNKNOWN, each with a file:line or probe output. Diff against the 2.1.296 matrix; mark every row "carried from 2.1.296, not re-probed" if not probed. Read generated types, not memory.
3. Caller/economic coverage: for interactive pane, bg worker, slim worker, subagent, planner/reviewer, successor, closeout: which admission runs BEFORE a call (file:line) and which only after.
4. Owner map. Classify PRODUCTION / PARTIAL / SHADOW / SPEC_ONLY / DUPLICATED / UNREACHABLE / HOST_LIMITED / SUPERSEDED / MISSING for: CCR, UCVM, UTVM, SSM, UCWSM (these names had 0 hits in modules|tools|mods; search vault/ and specs too, report the real owner or SPEC_ONLY), `modules/cognitive_os/*`, economic kernel, boundary reservation, Mission Cost Tree, Estate Controller, Technical Capital Allocator, tool/skill/memory linkers, proof graph. Decide: ONE owner for Boundary Context Compilation, or STOP and report a conflict (ULTRA-PLAN trigger).
5. WU-T0 gap: confirm which WU-T0 tasks T0A/T0B cover and which remain (Tennis forensics classification stays in T0B only as ONE flamegraph).

## Output (path-scoped commit, vault/ only)
`vault/programs/ccr-vm/T0A-reality.md` (matrix, coverage table, owner map, owner decision), then `vault/programs/ccr-vm/WU-T0A-receipt.md` with spend (processed tokens) and every claim labelled MEASURED / READ / UNVERIFIED.
Verify `git log -1 --format=%s` after the commit.
