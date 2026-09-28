# Phase 05 EVIDENCE -- Seal and hand back (GEX44)

This phase makes no model call and edits two vault files and this directory only.

## 0. Pre-checks

head_before: 9528d2d5b072b46313ef96a32c83131ae5193554
branch: mission/cognitive-resource-os-gex44
base_commit: cd4e436
measured_at_utc: 2026-09-28T15:30:32Z
model_calls: 0
ff_precheck_rc: 0
status_before:
```
## mission/cognitive-resource-os-gex44
 M .planning/workstreams/cognitive-resource-os/STATE.md
?? .planning/active-workstream
?? .planning/workstreams/cognitive-resource-os/config.json
?? .planning/workstreams/cognitive-resource-os/milestone.lock
?? .planning/workstreams/cognitive-resource-os/state.json
```

Both `05-01-PLAN.md` and `05-CONTEXT.md` are already tracked (committed in `9528d2d`), so this task's commit
pathspec needs no extra untracked phase file.

## 1. Inputs

p1_evidence: .planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md
p1_verdict_line: phase_verdict: BLOCKED
p1_verification: gaps_found
p1_review: absent
p1_next: Re-run plan 01-02 from Task 1 once the Owner approves the pinned pytest 9.1.1 / pluggy 1.6.0 / iniconfig 2.3.0 install.

p2_evidence: .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md
p2_verdict_line: phase_verdict: MEASURED
p2_verification: passed
p2_review: issues_found, fix_status all_fixed, fixes ad22dcd add48ee 71beaf0 35479c8 350fb84
p2_next: Phase 4 reuses tis_observed's first-call fields for its A/B; Phase 5 relabels RESUMPTION/UKDL laptop figures by host and folds instrument_gaps in as follow-ups.

p3_evidence: .planning/workstreams/cognitive-resource-os/phases/03-p3-pre-flight-p0/EVIDENCE.md
p3_verdict_line: p0_verdict: PASS (--settings {"claudeMdExcludes":["/home/kobii/.claude/rules/instrument-before-claim.md","/home/kobii/.claude/rules/destructive-state-authorization.md","/home/kobii/.claude/rules/real-context-reachability.md"]})
p3_verification: passed
p3_review: absent
p3_next: Phase 5 carries p0_verdict, version_scope and host_applicability into RESUMPTION and UKDL; the P1 A/A and every counted run wait for subscription quota and the Owner.

p4_evidence: .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md
p4_verdict_line: verdict: UNJUDGED (similar-reuse-variance-not-observed)
p4_verification: passed
p4_review: issues_found (critical 1, warning 2, info 1), no fixes block; orchestrator disposition records CR-01/WR-01/WR-02 open, fix required under a new runner sha before any reuse of ab_runner.py
p4_next: Record UNJUDGED in RESUMPTION/UKDL as judged (not BLOCKED); a rerun needs the MCP surface to actually change between run 1 and run 2 to exercise R5-R7 at all.

p4_gate_verification: WRITE
p4_gate_review_cr01: WRITE

## 2. RESUMPTION changes

resumption_sections_added: 1a, 2c, 2d, 2e, 4a
resumption_relabelled_lines: 13 lines carrying a laptop-figure anchor got "(laptop)" beside the figure (section 2's
  sealed bullets and MEASURED/coherence-anchor lines, section 2a's Ralph bullet, and the three former section-4
  bullets now folded into section 2), plus the section 2d/2e prose that quotes the 1.9%/16.4% laptop figures for
  comparison.
resumption_moved: the three sealed bullets (`6aa3bb6` prefix_inventory, P3 protocol predeclared, peer rules-evidence
  move) moved from the old section 4 to the end of section 2; the two "Owner clarified 2026-09-28" lines moved to
  the end of section 3; the old section 4 items 1-3 moved verbatim to the new section 4a.
next_actions_rule: (a) close a requirement this run left unsatisfied, then (b) work that a PASS verdict unblocked
  on the programme's main line, then (c) an open hypothesis whose next step costs zero model calls.
next_actions: 1. CRO-01 Owner review + re-run 01-02. 2. P3 pre-flight on the laptop's own claude, then P1 A/A on
  quota. 3. Prefix-miss follow-up from the laptop's own transcripts (zero-call step first).
phase4_action3_variant: standard (04-VERIFICATION.md status read as `passed` at execution time, not gaps_found).
