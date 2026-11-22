---
phase: 05-bi-15-35-on-the-cli-path
plan: 01
status: complete
completed: 2026-11-21
---
# 05-01 Summary: BI-15..35 on the CLI path

Commits: see `git log --grep "package stage"`.

`modules/ccf/creative_checks.py` gained the `package` stage: brand_color (BI-20), export_profile (BI-22/23), design_tokens (BI-25),
application_preview (BI-15), language_coverage (BI-19), logo_lens (BI-28), similarity (BI-29), benchmark (BI-31),
independent_review (BI-35), typed_parts (BI-17), trace (BI-18), release_manifest (BI-26). `cli.cmd_package` calls it before any
write. Report by default, `enforce` opt-in per check, absent = UNASSESSED, enforce+absent blocks. File inputs are project-relative only.
Gate `tools/test_bcap2_cli15.py` (in done_gate). Residuals: see STATE.md Phase 5.
