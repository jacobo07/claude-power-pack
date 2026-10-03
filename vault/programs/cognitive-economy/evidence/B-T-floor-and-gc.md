# [B] [T] Resident floor and institutional GC -- evidence

Both pillars end AUTHORIZATION_BOUND by their frozen rules: every remaining action edits `~/.claude/` (rules,
settings) or deletes code, and that is the Owner's. The campaign measured, proposed, and did neither.

## [B] Resident context floor

Frozen rule: "each rules->skills move needs an Owner y per move (CCP RESUMPTION s4); the campaign batches the
remaining moves into P5 and never executes one".

command: a PowerShell listing of `~/.claude/rules/**/*.md` with byte size, plus whether the body says "moved to a
skill" (2026-10-03, read only).

- 23 rule files. 10 are already stubs (moved to a skill, 592-914 B each), and 13 are still resident in full.
- The 13 total **56,861 B**: technical-failure-to-product-state 6,932; scoped-side-effect-authority 6,602;
  generated-content-needs-an-evidence-gate 6,284; effect-authority-across-transports 6,106;
  human-facing-external-effects 5,520; documented-capability-must-be-executable 5,045;
  validation-planes-do-not-transfer 3,656; capability-preserving-compaction 3,335; state-lifetime-and-incarnation
  3,137; post-effect-resource-truth 3,126; durable-exit-transaction 2,830; python/testing 2,516;
  common/code-review 1,772.
- The bytes are a ceiling on what moves could take out of the per-call prefix, not a saving. The moves made so far
  carry their own ablation (P3 REPORT, owner `cognitive-resource-os` phase 06); the moves of 2026-09-30 carry none,
  as their stubs say. Each further move needs the same kind of evidence and an Owner yes.

## [T] Institutional GC

Frozen rule: "liveness sweep + retire proposals; settings.json and skill removal need Owner".

command: `python vault/programs/cognitive-economy/measure/t_sweep.py --json vault/programs/cognitive-economy/measure/t_sweep_out.json`
(zero model calls; imports `modules/liveness/reachability.gate()`, never edits it). The skills half runs on the
D-W7 window.

Modules: 490 units, 310 REACHABLE and 180 ORPHAN. 64 are gate offenders (unreachable, undeclared, not standing debt):

| disposition | count | meaning |
|---|---|---|
| ACTIVE | 47 | committed within 14 days, or never committed: being built, never proposed |
| DORMANT_TESTED | 14 | older, and a test file imports it: declare (LIBRARY / PLANNED) or wire it |
| PACKAGE_INTERNAL | 3 | `knowledge_acquisition/__init__`, `engine3`, `session`: imported relatively by package siblings |
| RETIRE_CANDIDATE | 0 | none |

The 14 DORMANT_TESTED: cognitive_os/hibernate_runner, craif/oier, dataset_first/transduction,
done_gate/architectural_truth, fable_distillation/fd_04_acceleration, knowledge_acquisition/{boundary,
corpus_parser, queues, raw_vault, routing, runlock, store}, session_resilience/snapshot_versioning, sqi/ratchet.
Eight of them, plus the three PACKAGE_INTERNAL, belong to `modules/knowledge_acquisition`. That package is the
subject of the shared checkout's current branch `feature/knowledge-acquisition`, so its owner decides whether to
wire or declare it.

How the matcher was controlled (each run recorded):

- Run 1 read tests in tools/ only, and it proposed a package that has five tests under tests/. The aperture was
  widened to tools/, tests/ and module-local test_*.py.
- Run 2 still filed `from modules.pkg import mod` users as untested. The fix added per-file matching of the package
  path plus the basename. Controls: one-line and multi-line positives True; another package and a non-import both
  False.
- Run 3 proposed 3 modules, and every one was imported by a sibling. The fix added PACKAGE_INTERNAL. Controls:
  engine3 and session True; liveness/reachability (no sibling imports it) False.

Skills: 165 installed under `~/.claude/skills`, of which 23 were invoked in D-W7 and 142 were not. One week is a
thin window, so "not invoked in D-W7" is not a retirement verdict. Skill residency is the C owners' (handoff C).

## Product Delta / Intelligence Delta

- Product: zero modules are proposed for deletion. The sweep would have proposed 3 modules in use, and an
  uncontrolled run 1 would have proposed a tested package.
- Intelligence: an orphan sweep's retirement list is only as good as its usage matcher. Three successive matcher
  holes each produced false retirement proposals; see ukdl-candidates UC-02.
