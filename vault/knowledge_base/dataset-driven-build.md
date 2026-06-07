# Dataset-Driven Build -- vault without module is documentation (SCS C41)

## SCS C41 -- Dataset-Driven-Build: a vault file without a module is documentation, not a feature (sealed 2026-06-07, BL-BUILD-EVERYTHING-001)

**Standard.** A system defined in an ingested dataset is not "built"
until a Python/JS module + an empirical done-gate prove it runs. A
`vault/` markdown file with no implementing module is documentation, not
a feature. AND its converse, equally binding: **do not build what already
exists.** Before building a dataset-named system, inventory the live
`modules/` tree -- if a module already implements it, compose/extend it;
never ship a redundant duplicate.

**The build-everything inventory (FASE -1) found ~14 proposed systems;
~8 already existed or thinly overlapped.** Building "everything"
literally would have duplicated `rollback`, `cost_collapse`,
`secret_firewall`/`secret_rotation_advisor`, `monitoring`/
`pp_health_report`, `arch-decision`, `one_shot`, `output_contracts`, and
`cpc_os`. That is a Reality-Contract / SCS C28 violation, not progress.

**Built (the genuine gaps, all `tools/test_build_everything.py` 9/9 x 3
hermetic):**
- A1 `modules/sdd_os/prd_generator.py` (`/prd-generate`) -- composes
  `spec_gate.classify_tier`; emits the tier's PRD scaffold (Tier 0
  mini-spec -> Tier 3 full strategic set).
- B2 `modules/setup_os/backlog_generator.py` (`/setup-backlog`) -- bridges
  `roi_analyzer` recommendations into `backlog_autopilot.what_now`; each
  item carries a done-gate; secret firewall pinned P0.
- B3 `modules/setup_os/drift_detector.py` (`/setup-drift`) -- repo-CONFIG
  drift (profile fields + config-file hashes); the gap `monitoring`
  (service health) does not cover.

**Deliberately NOT built (documented, not silently skipped):**
- EXISTS/overlap: A2->arch-decision, A3->one_shot, A5->output_contracts
  (is_done_for_tier), B1->secure_installer rollback_recipe + modules/
  rollback, B4->cost_collapse, B5->secret_firewall+rotation_advisor,
  B7->pp_health_report+monitoring, Parts XI-XIV->cpc_os.
- HIGH-RISK: A6 regression_guard (auto-generated tests = test theater),
  B6 cross_project_sync (global ~/.claude = HR-001 Owner-side).
- EPICS: PP Parts XIX-XXIII (Sovereign Governance/Control-Plane/Fleet/
  Execution/Assurance) -- each a multi-sprint build, not a one-module gap.

**No-duplication is gate-enforced:** `V-COMPOSE-NO-DUP` asserts the new
modules reuse the canonical `classify_tier` / `what_now` / `scan` objects
(identity check), not re-implementations.

Cross-ref C28 (read source / compose), C39 (SDD-OS), C40 (Setup OS),
HR-001 (Owner-side global config). Companion: the FASE -1 MASTER BUILD
INVENTORY is the audit trail for what existed vs what was new.

Sealed BL-BUILD-EVERYTHING-001 2026-06-07.
