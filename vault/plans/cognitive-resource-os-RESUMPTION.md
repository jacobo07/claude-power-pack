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

## 2b. Owner decisions pending
- hooks/kobiiclaw-autoresearch.js (Stop, registered at dispatcher:174) has been INERT since TUA-X renamed
  TUAX_UGC_SYSTEM -> CW_UGC_SYSTEM: its fallback path is dead, so every turn skips silently. Fixing the path
  REVIVES a per-turn `knowledge_engine.py inject <cwd>` that writes AKOS_KNOWLEDGE_BRIEF.md into every open
  repo (incl. trees other panes commit in) with a 5 s budget. Revive, retire, or move to SessionStart? Not
  changed. /knowledge (manual) was repointed; `domains` verified, `query` run, inject/brief not executed here.

## 3. Active decisions
- Estimates and observations never mix; every figure names its source.
- Pricing: never hardcode a dated filename; never invent a price (read the live page).
- Phase 4 (Ralph holes in tools/gsd_mission.py) goes LAST in P1-P4: the live writer edits that file.

## 4. Next three actions
1. DEFERRED by Owner 2026-09-27 ("why spend? better wait for the limit to come back"): run it on subscription
   quota after the usage limit resets, never as paid spend. Then: diagnose the cross-session prefix miss — two
   back-to-back `claude -p` runs in one dir, identical prompt, then two with `--strict-mcp-config` + empty MCP
   config; compare first-call cache_read. Worker argv is in tools/gsd_mission.py (LIVE writer there).
   $ figures in this file are API-rate EQUIVALENTS of usage, not charges.
2. BLOCKED (same-file collision): model-routing refresh touches tools/tco_compact_gate.py + tools/test_tco.py,
   dirty in another pane that is writing a SECOND transcript reader (V-TCO-MEASURED-*). Messaged the
   "Context rent architecture..." session to import tools/tis_observed.py instead. Resume once they commit.
3. BLOCKED (same-file collision): P2 needs modules/gsd_x/mission/closure.py, dirty in another pane (+ untracked
   coverage.py). Free alternative: CONNECT done_gate/artifact_done_gate (orphan, NOT a duplicate — plan corrected).
Owner clarified 2026-09-28: ONLY the paid experiment is off; free work continues. Model-calling runs
(A/B, ablation) wait for subscription quota.
- `6aa3bb6` modules/token-optimizer/prefix_inventory.py: unconditional prefix ~102k tok est. (rules 56.8k,
  CLAUDE.md 21.4k, agents 11.0k, skills 7.9k, MEMORY 4.0k); harness/tools/MCP/plugins declared NOT counted.
- P3 protocol predeclared: vault/plans/cognitive-resource-os-P3-ablation-protocol.md (pre-flight P0 = run an
  arm without rules and without touching global config/credentials; unresolved -> STOP, do not improvise).
- A peer session moved every rule's incident evidence to knowledge_vault/rules-evidence/ (rules ~267->216 KB).
  Three+ transcript parsers now agree on dedupe (peer 8c39c27); consolidating them to one owner is open debt.

## 5. Start instruction
Run the coherence anchor. `git log --oneline -8` and confirm the three commits. Then action 1.
