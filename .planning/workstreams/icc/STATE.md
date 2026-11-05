---
gsd_state_version: "1.0"
milestone: v1
status: ready
stopped_at: Roadmap created by the arming pane
last_updated: "2026-11-05T00:00:00.000Z"
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
milestone_name: icc
workstream: icc
created: 2026-11-05
current_phase: 1
current_phase_name: Phase 1 (see ROADMAP.md)
last_activity_desc: Owner approved `y go ICC`; mission armed
---

# Project State

Authority: `ROADMAP.md` + `REQUIREMENTS.md` here, and `vault/plans/icc-state-centric-2026-11-05.md`.
Budget: authority 60M processed tokens + 3 top-ups of 10M; hard ceiling 90M; closeout reserve 4M.
Arming pane bcf0a0bc (interactive, PP root) did the Reality Scan and plan inline.

Measured at arm (laptop, request plane): call-1 71,883 tokens (floor_regression_gate --check --session bcf0a0bc).
Recorded plane (transcript chars): deferred_tools_delta 45,603; skill_listing 29,988; memory_project 28,817;
agent_listing 27,068; mcp_instructions 8,975; SessionStart hook 8,229; rules 8,239; memory_global 7,871; system_prompt 7,937.
Deferred MCP names: vercel 241 (8,237 chars), rea 207 (6,355), github 41, artifacts 32, Gmail 30, gex44-browser 25.

## Spend log
(one row per phase: phase, session id, processed tokens, command)

## Notes
- 2026-11-05 epoch2: Phase 1 partial. DONE: floor gate refuses ambiguous newest-by-mtime (f78e2b5f); A1 probes (vault/programs/icc/floor-request-plane.{json,md}): -p control 78,179 / CCR off +41 (canary no effect in -p, UNMEASURED there) / no-MCP -3,560. PENDING in Phase 1: COMPAT-miss SessionStart line, GEX44 items (any GEX44 ~/.claude write = OWNER_STEPS).
- DECISION: A1 run in -p (cheap, pinned) as the plan specifies; interactive-pane canary effect needs a pty probe (phase5_smoke.py driver) - deferred to Phase 2 shadow receipts.
- 2026-11-05 epoch3: COMPAT-miss SessionStart line DONE (hooks/ccr_compat_line.js + hub wiring 13b; test hooks/tests/test-ccr-compat-line.js both poles, mutation red->green). Reprobe tool does not exist: message names the manual COMPAT edit + ccr_release.py release. REMAINING Phase 1: GEX44 read-only items (dangling pointers, resident budget file, -13,786 attribution) + request-plane table md already committed.
- DECISION (epoch3): no live hub smoke on a real incompatible host (none available); unit poles are the evidence; labelled UNMEASURED live.
- 2026-11-05 epoch3: PHASE 1 COMPLETE (early-value table: vault/programs/icc/floor-request-plane.md; GEX44 budget: vault/programs/icc/gex44-resident-budget.md; -13,786 attribution UNMEASURABLE by construction (gate refuses cross-plane compare); GEX44 pointer fix -> OWNER_STEPS.md). Supervisor-measured spend ~4.7M processed cumulative (Phase 1 ceiling 6M, met). Next: Phase 2 (W1 CCR deferred-name collapse).
- 2026-11-05 epoch3: Phase 2 STARTED. DONE: collapseDeferredNames + deferredNamesMode (policy.ts), wired in register.ts prompt.attachment (kill switch CCR_DEFERRED_NAMES=0, default SHADOW receipts, 'enforce' explicit). 39/39 mod tests pass (claude plugin test mods/cpp-cognitive-runtime), mutation (drop saving guard) red. NOT YET: pp-code-reviewer pass, release via ccr_release.py (shadow release first), n=10 ON/OFF quality bench, elasticity bench. Open risk: attachment text format assumed one name per line (matches this session's rendering); verify against shadow receipts before enforce.
- 2026-11-05 epoch4: pp-code-reviewer on e5e21afe = APPROVE with notes (0 crit/high). Tests re-run 39/39. M1 (shadow gated by canary): canary is enforce for interactive sessions, off for headless/-p (policy.test.ts:393-396), so shadow receipts DO accumulate in interactive panes; headless not measured - accepted, no change. M2 (added vs removed names merged in one block): must check real attachment format via shadow receipts before CCR_DEFERRED_NAMES=enforce; collapse per section if removals can appear. Low: shadow receipt `out`=original, collapsed size in `lean`.
- DECISION (epoch4): did NOT run `ccr_release.py release` - HR-2 requires a same-commit smoke of the new build and none was run; a release changes the Owner's live sessions (outward-facing). OWNER DECISION NEEDED: run the shadow release + HR-2 smoke (`python tools/ccr_release.py release`, then smoke) and let shadow receipts accumulate; enforce stays off until M2 is checked. Phase 2 is code-complete but not released; remaining phases 3-7 not started this epoch.
- DECISION (epoch4): Phase 3 = DEFERRED-FOREIGN-WRITER. Its gate is `git status -- CLAUDE.md` clean; the main checkout shows ` M CLAUDE.md` (foreign edit not landed). Skipped per roadmap. NEXT runnable: Phase 4 (W3 model-call accounting; extend tools/cognitive_admission.py / mission_spend.py, no new meter).
- epoch4 Phase 4 scouting: existing meter = tools/mission_spend.py (processed_tokens, session_tree_report, programme_spend); zero-model close path to extend = tools/gsd_mission.py ~line 3973 (`state=COMPLETED, deterministic=res`) and 6006/6266 (mission_completed). Phase 4 is T2 (multi-file, persistence): write the spec (PRD+AC+rollback, covers: [model-call-accounting, zero-model-fraction]) BEFORE the first edit.
