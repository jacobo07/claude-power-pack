# Cognitive Resource OS — plan of record (2026-09-27)

Status: AWAITING OWNER APPROVAL. Nothing below is implemented.
Scratch evidence: session scratchpad reality_A.md / reality_B.md (scout reports, key claims re-verified in main thread).

## Mode
- Outer: /cpp-gsd-long (Ralph mission) after approval. ULTRA-PLAN used for Phase 0 only (this document).
- EXECUTION MODE from P1 onward; PLAN MODE only for P4 fencing design and P3 ablation design.

## Reality (measured, 2026-09-27)
- HEAD 6a17b3a on feature/knowledge-acquisition; ~20 files dirty from another live writer (not ours; never staged).
- Startup payload OBSERVED: first model call of a recent session = 157,256 cache-creation tokens (transcript usage field).
- Always-loaded instruction files: 356 KB ≈ 94k tokens (bytes/3.8 ESTIMATE); ~/.claude/rules = ~267 KB, none path-scoped.
- `paths:` frontmatter documented for PROJECT rules (code.claude.com/docs/en/memory.md); user-level: NOT DOCUMENTED.
- TIS (tools/tis.py) logs chars/4 estimate of JIT injection (jit_skill_loader.py:1153-1162), not model usage. Real usage exists in 96 transcripts.
- vault/config/model-routing.json routes to claude-*-4 ids only (stale).
- Ralph (tools/gsd_mission.py): epoch+CAS, 3-state liveness, card, GSD ALL_COMPLETE convergence. Holes H1-H11; H1 verified (last_progress_at written once as None, :184).
- Goal Engine (modules/gsd_x/goal/*) complete design, ORPHAN (no hook/command/ps1 caller — verified in repo hooks/commands/tools ps1).
- UCR/CIF/UBC/CBR/Context ROI/Baseline Cache/Construction Memory/Memory Capability Compiler: concept names only (vault/knowledge_base/ucr_cif/); prior D2A audit exists; Owner A/B/C ruling OPEN there.
- Overlaps: model routers 7 · completion gates 6 · contract/spec owners 6 · ratchets 4 · epoch/lease 4 · reapers 4 · supervisors 3 · FTS5 stores 5.
- Documented-not-executed: prg_assess/strength_ladder, premise_verifier.assert_premises, token_autopsy, ukdl_queue, side_effect_ledger, modules/lease.
- 95-token-reduction doc: NOT FOUND in Downloads (home-wide search timed out → unlocated, not absent).

## Governing decision (HR-NOVELTY-001)
The prompt names ~20 control-plane components. Measured reality: the estate's gap is ORPHANS and OVERLAPS, not missing concepts.
Verdict: 0 new mega-systems. CONNECT orphans, MERGE overlaps, EXTEND owners; NEW only for 3 primitives with no owner
(usage-observed ledger reader, progress detector, resume exam) — each justified inline, each inside an existing module.

## D2A
| Capability | Decision | Owner |
|---|---|---|
| Resource ledger | EXTEND | tools/tis.py: add `observed` source from transcript usage; relabel chars/4 as `estimate` |
| Model routing | MERGE 7→1 | modules/cost_collapse/router.py canonical; refresh ids; others delegate; shadow first |
| Completion claim verifier | MERGE | output_contracts/validator (live) absorbs artifact_done_gate (PLANNED, delete) |
| PRG | CONNECT | strength_ladder/prg_assess → gsd_x/mission/closure replaces self-declared string |
| Evidence freshness | EXTEND | receipts keyed to HEAD + dependency path hashes inside output_contracts |
| Instruction economics | NEW harness inside rule_compiler (effect_harness/counterfactual exist) | ablation over frozen tasks |
| Durable execution | EXTEND | gsd_mission.py: H1 progress, H3 freshness on arm, H4 resume exam, H9, H10 retire v2 sweep |
| Write fencing | CONNECT | modules/lease/store.py (fenced, unused) → mission epoch; checked at commit |
| Convergence | CONNECT (shadow) | gsd_x/goal/judge consulted beside ALL_COMPLETE |
| Tool I/O firewall | EXTEND | RTK (live) + persisted raw artifact locator |
| Repo intelligence | CONNECT | harness LSP symbol-first; audit_cache stays; no new index |
| Memory reuse / negative cache | EXTEND | graphify writeback + session_delta, with freshness fields |
| Agent foundry / gym / counterfactual | DEFER to shadow experiments | keos_qwen ledger + rule_compiler/counterfactual |
| Baseline ratchet | EXTEND | modules/tower (CBR slice) receives certified items only |

## Phases (dependency order)
P0 Baseline freeze — measure startup/turn/agent tokens over 96 transcripts; freeze 8-12 representative replay tasks + quality floor.
P1 Measurement — observed usage ledger; model id refresh; token_autopsy wire-or-delete. Slice: per-session report from real usage.
P2 Evidence — PRG connected to closure; freshness receipts; merged completion verifier. Slice: stale green refused after source change.
P3 Instruction economics — ablation harness; candidate relocation of domain rules to path-scoped project rules/skills (Owner consent: global files). Slice: startup tokens before/after with non-inferior replay.
P4 Durable execution — H1/H3/H4/H9/H10, fencing via modules/lease, goal judge in shadow. Slice: a real 2-epoch crossing + fenced stale worker.
P5 Context/tool I/O + memory reuse — raw-output locator, symbol-first advisory, negative-decision cache with invalidation.
P6 Routing — merged router in shadow, worker --model recommendation logged, one controlled comparison.
P7 Agents/gym/science — shadow only; go/no-go on P1-P2 trustworthiness.
P8 Crystallization — tower/CBR promotion, UKDL 3-level, liveness baseline, retire merged duplicates.

## Done gates (each phase)
Tests (narrow, change-scoped) · /liveness exit 0 · PRG state named (PROVEN / PARTIALLY PROVEN / LIVE_UNVERIFIED / BLOCKED) · mutation drill on each new guard · measured before/after with quality floor · UKDL entries.

## Risks
Live concurrent writer (pathspec commits, never stage their files) · host RAM starvation (1.1 GB free measured by scout) · ~/.claude writes blocked by classifier (HR-001) · full-tree mirror .claude/worktrees/gsd-x (stale copies) · replay quality floor may be too expensive to run often.

## First action after approval
Extend tools/tis.py with an observed-usage reader over transcripts + test; produce the P0 baseline report.
