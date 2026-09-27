# Cognitive Resource OS — RESUMPTION

Read this and continue with zero prior context. Update after every sealed unit.

## 1. Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Plan of record: `vault/plans/cognitive-resource-os-2026-09-27.md` (Owner APPROVED 2026-09-27, incl. consent
to relocate `~/.claude/rules` content in P3 ONLY after an ablation shows non-inferior quality, one reversible
commit per move). Thesis: the gap is orphans + overlaps, not missing concepts — CONNECT/MERGE/EXTEND, 0 mega-systems.
Another writer is LIVE in this tree (touches gsd_mission.py, knowledge_acquisition). Commit by explicit pathspec only.

## 2. Sealed
- `9fa1017` tools/tis_observed.py — real usage from transcripts (dedupe by message.id+requestId; synthetic excluded;
  subagents attributed; MEASURED / MEASURED_ZERO / UNMEASURED). Baseline: 97 sessions, median startup context
  168,631 tok, 13,858 calls, startup prefix ≈ 50% of all context (call-weighted ESTIMATE).
- `48bbbb7` /cost-autopsy → `tis_report.py --observed`; project key = non-alnum→'-'; empty dir = UNMEASURED exit 2.
- `383cb37` pricing: anthropic_2026-09.json (read live 2026-09-27); 2026-05 file priced opus-4-7 at Opus 4 rate (3x);
  tools/pricing_source.py resolves newest dated file for tis_report / budget_monitor / verify_full_install.
- `ca69a04` budget_monitor runway from OBSERVED sdk-cli spend (entrypoint split); estimate kept as source=estimate.
- (this commit) tis_observed: first_call_cache_read + startup_shared_share_median; UKDL
  `vault/knowledge_base/ukdl-cognitive-resource-os.md` (1 HR, 3 PR, 4 T).
MEASURED 2026-09-27 (7d): programmatic $90.06 / 272 calls / 62 sessions; 79.9% = 1h cache writes; median 1 call
per session; first-call shared prefix 1.9% sdk-cli, 16.4% cli. Hypothesis (unmeasured): tool list varies with MCP.
Coherence anchor: `python tools/test_tis_observed.py` 25/25, `test_pricing_source.py` 5/5,
`test_budget_monitor_observed.py` 7/7. test_tco V-BASELINE-INTACT INCONCLUSIVE (full pytest >180s, host ~630 MB free).

## 3. Active decisions
- Estimates and observations never mix; every figure names its source.
- Pricing: never hardcode a dated filename; never invent a price (read the live page).
- Phase 4 (Ralph holes in tools/gsd_mission.py) goes LAST in P1-P4: the live writer edits that file.

## 4. Next three actions
1. Diagnose the cross-session prefix miss (highest $ lever): an A/B of two back-to-back `claude -p` runs in one
   dir, identical prompt, then with `--strict-mcp-config` + empty MCP config; compare first-call cache_read.
   Worker argv is in tools/gsd_mission.py (LIVE writer there) — measure first, change later, coordinate.
2. vault/config/model-routing.json: stale claude-*-4 ids; test_tco V-ROUTE pins claude-opus-4-7 — refresh with tests.
3. P2: connect done_gate/strength_ladder + prg_assess to gsd_x/mission/closure (replace self-declared string).

## 5. Start instruction
Run the coherence anchor. `git log --oneline -8` and confirm the three commits. Then action 1.
