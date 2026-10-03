# Phase 8 plan check (gsd-plan-checker, 2026-10-04, worktree sc-run, HEAD cdd40074)

Findings appended as confirmed. Severity BLOCKER / WARNING / INFO.

## Structural
- frontmatter.validate --schema plan: valid on 08-01..08-04. verify.plan-structure: valid, all tasks have files/action/verify/done.

## Premise 1: modules/capability_runtime/retirement.py -- CONFIRMED
- Exists; `main` exposes `--json` (retirement.py:461) and `--record` (:457, writes via record_evaluation only when set,
  :467-468); `_audit_frontmatter` at :93; `probe_liveness_reachability` (:160) imports `modules.liveness.reachability.gate`
  and calls it with NO root (:171). 13 contracts in vault/capability_runtime/contracts. 08-03 DH-01 is accurate.

## Premise 2: quick_validate.py accepts `metadata:` -- CONFIRMED (no repo copy exists)
- No quick_validate.py tracked in the repo. Five copies under ~/.claude, THREE distinct contents (sha prefixes 5b1b51ae
  minimal owner copy; f6531597 x3 synced; 67cf5703 official plugin). Official plugin :42 and synced :84
  `ALLOWED_PROPERTIES = {name, description, license, allowed-tools, metadata, compatibility}`; minimal owner copy has no
  whitelist. `metadata:` nesting is accepted by all. DJ-01 holds.

## Other premises (HR-PREMISE-001) -- all CONFIRMED
- tools/skill_coverage.py: CARD_TOKEN:65, DISPATCHER_REL:43, lf:71, registered_hooks:101, discover_cards:134 (read_disk kw),
  opportunity_adapters:165, coverage:185 (evidence `hook:line (...)` + `file:line`, so DJ-03 "file part before first `:`" works),
  COVERAGE_CLASSES:49, KIND_LINE:67, CAP_LINE:68.
- tools/skill_mirror_drift.py: lf_bytes:68, git_run:76, resolve_commit:93, tracked_paths:114, BATCH_FAILURES:284,
  is_git_failure:288, REPO:61, `vgm` = verify_global_mirrors (batch_blobs at tools/verify_global_mirrors.py:178), --record-cards.
- modules/skill_router/skill_index.py:123 `_FM_RE` as quoted. card_lineage.py --trailer-for:552; test_card_lineage.py and
  test_skill_drift.py and test_skill_coverage.py all have --write-evidence. hooks/tests/test-doctrine-cards.js,
  test-destructive-doctrine-card.js, tools/test_card_precision.py, test_cdio_mobile.py, router_freshness_gate.py exist.
- 24 tracked skills/*/SKILL.md, 24 distinct dirs; 08-02 files_modified lists exactly that set.
- CE verifier: REQUIRED_KINDS:70, DEFERRAL_PROSE:86, lf_sha256:90, _path expands `~`:130, handoff_landed:148, run_gate
  sys.executable:163, L4 owner/handoff rules:272-296, CEP_PILLAR_ output:536; wrapper rebinds HANDOFF_DIR at
  tools/test_skill_capability_program.py:42. All frozen owners of I-M exist. Ledger state lines I..N are the null shape (107-112).
- Pins: card_source_digests.json on G(105)+H(106), H-drift.md on H, G-lineage.md on G, D-coverage.md on D(102): matches DD-05.
- estimate-check --calibrated: 75k/85k/80k/55k all under 100k budget, confidence low (0 samples).

## WARNING 1 -- 08-03 I measurement is not "committed blobs only"
- 08-03-PLAN.md:27 and :173-175 run `python3 <tmp>/modules/liveness/reachability.py --json` inside a `git archive` export.
  reachability.py:42 sets `_PP_ROOT` from `__file__`, so in the export `_is_installed_root(root)` (:100-112) is TRUE and
  `live_seeds` (:297-303) merges gex44 `~/.claude/{hooks,commands,agents,settings.json,CLAUDE.md}` as seeds. Same for
  retirement.py's probe (:171, `gate()` with no root). The candidate list therefore depends on the gex44 live install, not
  only on committed blobs, and differs per host.
- Required property: every I figure names the plane(s) it read; either the live tree is excluded or it is labelled.
- Fix: call `gate(Path(export))` in-process from the worktree module (root != _PP_ROOT -> no live seeds), or run the
  export copy with `HOME=<empty tmp>`; record which in the handoff and SUMMARY.

## WARNING 2 -- phase-7 fixer concurrency on ledger.json / owner-bundle.md / E-contribution.md
- The fixer edits ledger state.E and owner-bundle [E] (07-REVIEW-FIX.md is untracked in this worktree). Line-level, phase 8
  does not write E: 08-02 T3 moves pins on G/H(/D) lines only; 08-04 writes I-M lines and appends I-M bundle lines.
  But pathspec commits are file-granular: 08-02 T3 (08-02-PLAN.md:186-193) and 08-04 (both commits) `git commit -- ledger.json
  [owner-bundle.md]` would sweep an uncommitted fixer hunk in the same file, and both appends land at the same EOF region of
  owner-bundle.md. 08-04 T1 has a porcelain-empty precondition (08-04-PLAN.md:88); 08-02 T3 and 08-03 T2 do not.
- 08-03 T2 quotes E-contribution.md deltas into handoffs/M.md (:183-184); if the fixer changes E after, M.md is stale prose
  (its sha pin still matches, `--check` compares claims only, DH-05) -> a committed handoff misquoting E.
- `--pillar A..H` regression in 08-02 T3 and A..M in 08-04 T3 include E, which can be red for phase-7 reasons.
- Required property: phase 8 writes to ledger.json / owner-bundle.md and reads E evidence only after the phase-7 fix is
  committed, with `git status --porcelain -- vault/programs/skill-capability tools/test_contribution_verdict.py` empty.
- Fix: add that precondition to 08-02 T3 and 08-03 T2 (as 08-04 T1 already has), or make 08-02/08-03 depend on the 07 fix commit.

## WARNING 3 -- 08-02 scope: 32 files_modified (08-02-PLAN.md:7-39), over the 15-file threshold
- Mitigated (24 edits are one scripted insertion, add-only diff checked), but Task 1 also reads 40 lines of 24 files and
  runs 17 test files twice. Consider moving the G/H re-derivation (Task 2-3) to its own plan if context runs hot.

## INFO 1 -- quick_validate variants: 3 distinct contents, not 2 (08-02-PLAN.md:132-133)
- sha prefixes 5b1b51ae (owner, no whitelist), f6531597 (3 synced copies, whitelist), 67cf5703 (official plugin, whitelist).
  The dedup-by-sha discovery handles it; only the plan-time figure is off.

## INFO 2 -- task type `tracer` (08-01:119, 08-02:120, 08-03:125, 08-04:80) is outside auto/checkpoint/tdd
- verify.plan-structure accepts it and each has files/action/verify/done; confirm the executor treats it as `auto`.

## INFO 3 -- same-wave 08-01 / 08-03 undeclared coupling (Dimension 3b)
- Both add top-level tools/*.py, which enter each other's apertures (sc.opportunity_adapters population for J/D; the K/M
  added-file sweep). Both plans guard it (DJ-06, DH-03: no `KIND =`/`CAPABILITY =` line, no marker hits), so no race on
  outcome; noting the edge so it stays declared.

## Not found
- No requirement gap (SC-I..M each claimed), no dependency cycle (08-01,08-03 w1; 08-02 w2 <- 08-01; 08-04 w3 <- 08-02,08-03),
  no CONTEXT contradiction or deferred-idea creep, no CE-file / live ~/.claude / repo CLAUDE.md / frozen edit planned,
  ledger closure via one-line replacement with frozen asserted against 217d72b5, every absence has a positive control and
  UNMEASURED on dead control / zero population, git failure -> INCONCLUSIVE drilled with PATH=/nonexistent.

## Verdict: ISSUES FOUND -- 0 blockers, 3 warnings, 3 info
