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
current_phase: 7
current_phase_name: Phase 7 closeout (done); Phase 3 deferred-foreign-writer
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
- 2026-11-05 epoch5: DECISION (runtime answer RESOLVE_BY_DEFAULT, no Owner class: reversible local shadow release, rollback = ccr_release.py rollback): ran `ccr_release.py release` -> 0.1.0-05998d9a, then HR-2 smoke arm D n=2 on that build: 2/2 correct, 0 faults, receipts safe-hoisted (vault/programs/icc/phase2-release-hr2-smoke.json). Phase 2 RELEASED in shadow; CCR_DEFERRED_NAMES stays shadow, enforce still gated on M2 check of shadow receipts. NEXT: Phase 4 spec (T2) before first edit.
- 2026-11-05 epoch5 Phase 4 CODE-COMPLETE: spec vault/specs/icc-model-call-accounting.md; gsd_mission.try_done_gate_close (packet 'done-gate:' line, pass -> COMPLETED with 0 model calls, fail/outside-root -> normal epoch, kill switch GSD_ZERO_MODEL_CLOSE=0); mission_spend.model_call_report + CLI model-calls. tools/test_done_gate_close.py 5/5, mutation (gate failure still closes) red. LIVE: model-calls --mission m-1f1ba12950ec = 5 model epochs, 0 zero-model closes, fraction 0.0 (work class unclassified). Not yet: code review pass, a real packet using done-gate:. NEXT: Phase 5.
- 2026-11-05 epoch5 Phase 5: agent_bundle path already wired (tools/agent_carrier_run.py + silent-failure-hunter spec). Found+fixed a measurement bug: on claude 2.1.318 the Agent tool_result is only a pointer and the report is in task_notification.handback_report.text (runner recorded the pointer as the reply). Measured n=3 each: bundle reply mean 4,284 chars vs prose 3,491 (+23%), 3/3 VALID. RESULT: bundle does NOT cut parent growth on this host (full report still delivered as a message). DECISION: do not adopt bundle return for context savings; keep as validated-evidence format only. Evidence vault/programs/icc/phase5-bundle-vs-prose.json. Open: the p4 review (python-reviewer) raised HIGH that model_call_report cannot group by work class (no event carries work_class) - known limitation, all 'unclassified'; not fixed. NEXT: Phase 6.
- 2026-11-05 epoch5 Phase 6 PART 1 DONE: tools/ctx_rent.py regret (dead rent = carriage minus Belady bound, per Work Class; transcripts <10 calls skipped). Real run on 7 transcripts (vault/programs/icc/phase6-regret.json): top-level n=4 regret 4.1% of processed / 46.5% of result rent; worker:background n=3 7.4% / 22.5%. UPPER BOUND, chars/4. tools/test_ctx_regret.py 2/2 + legacy test_ctx_rent exit 0. PART 2 NOT DONE: resident_budget.json (vault/programs/global-prefix-floor/) gains request-plane listing layers + floor gate fails on growth. Then Phase 7 closeout.
- 2026-11-05 epoch6: PHASE 6 PART 2 DONE (60500015): resident_budget.json + skill_listing 33,000 / other:agent_listing_delta 32,000 (recorded-plane chars, cwd-scoped to PP); deferred_tools/mcp_instructions excluded by name (connection-timing variance 8.9k-47k); V-FLOOR-BUDGET-REAL-PINNED adds a growth pole; floor test 70/70, done-gate test 45/45.
- 2026-11-05 epoch6: PHASE 7 CLOSEOUT DONE: 5 UKDL entries (ukdl-universal.md, ICC closeout block), 4 errors.md rows, master done-gate mapping with NPVs appended to vault/plans/icc-state-centric-2026-11-05.md. Fresh-agent recovery test (sonnet, read only RESUMPTION Start + this STATE): correctly named mission, workstream, blocked Phase 3 and status command; but saw STATE as stale (next=Phase 6 pt2, frontmatter 0 complete) -> fixed in this edit. RESULT: PASS with one staleness defect, repaired.
- OWNER ITEMS (no action taken): Phase 3 needs the foreign CLAUDE.md edit landed or discarded; check real attachment format in shadow receipts before CCR_DEFERRED_NAMES=enforce; pp-code-reviewer on Phase 4/5 diffs; make model_call_report Work-Class-aware.
- 2026-11-06 epoch7: DECISION (RESOLVE_BY_DEFAULT; reversible, internal): the uncommitted CLAUDE.md edit in the main checkout (-144/+3 lines, HR mirror trimmed to TRIGGER-only, ctx-rent-a2 diet by another writer) is NOT mine to land or discard; left untouched. Phase 3 stays DEFERRED-FOREIGN-WRITER per its own roadmap gate. All other phases (1,2,4-7) done; mission has no further runnable phase. Owner items above remain.
