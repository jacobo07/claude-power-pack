---
phase: 04-prefix-cache-miss-a-b
plan: 01
subsystem: infra
tags: [claude-code, tis_observed, cache-prefix, mcp, ab-test, subscription-quota]

# Dependency graph
requires:
  - phase: 02-gex44-observed-baseline
    provides: tools/tis_observed.py composition pattern (by_entrypoint.py's _ensure_tools_importable / WR-04 import-safe pattern), GEX44's baseline first-call shared-share figures
  - phase: 03-p3-preflight
    provides: claude 2.1.283 resolved/pinned at ~/.local/bin/claude, ~/.claude/rules confirmed absent on GEX44
provides:
  - "ab_runner.py: read-only evidence runner (env/auth pre-checks, argv, scrubbed env, one-shot --live launch, transcript lookup by session id, tis_observed-based first-call readout, VR1-VR7/M1-M2/vA/R1-R8 rules, fingerprint, readout re-derivation, evidence-lines, 14-case fake-claude selftest)"
  - "EVIDENCE.md: pre-checks, pre-registration, the four real runs, cross-arm comparison, and the CRO-04 verdict"
  - "raw/ab-live.json: the durable one-shot launch record and rerun latch"
  - "CRO-04 judged: UNJUDGED (similar-reuse-variance-not-observed), rule_fired R8, cro04 SATISFIED"
affects: [phase-05-seal-and-hand-back]

# Actuals (#2632)
actuals:
  tokens: 34734
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Read-only evidence runner composing tools/tis_observed.py (read_session/iter_calls/project_key) rather than re-implementing transcript parsing, per Phase 2's by_entrypoint.py WR-04 import-safe pattern (ROOT = parents[5], lazy _ensure_tools_importable())"
    - "One-shot live-run guard chain (G1-G8: env block, out-exists, LIVE-LATCH, arm-dir-exists, binary sha pin, runner sha/rules-fingerprint pin, oauth-only auth, pre-existing-transcript) fronting the only model-call-spending code path in the workstream"
    - "TDD RED-then-GREEN gate on a pre-registration commit: rules_fingerprint (sha256 over RULES + inspect.getsource of the rule functions) frozen and committed before the single counted --live invocation"

key-files:
  created:
    - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/ab_runner.py
    - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/EVIDENCE.md
    - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/raw/claude-help.txt
    - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/raw/static-excerpts.txt
    - .planning/workstreams/cognitive-resource-os/phases/04-prefix-cache-miss-a-b/raw/ab-live.json
  modified: []

key-decisions:
  - "Arm A's MCP tool list and server statuses were byte-identical between A1 and A2 in this single observation (vA NO) -- the tool-list-variance hypothesis was not exercised, so the verdict is UNJUDGED (similar-reuse-variance-not-observed, R8), not SUPPORTED/REFUTED. This is a legitimate, pre-registered outcome (R8 exists precisely for this case), not a plan defect."
  - "gap_run2 = s_B2 - s_A2 = -2e-05: both arms independently reached ~99.96-99.97% run-2 cache reuse regardless of MCP configuration, so no cache miss was observed to attribute to anything, including MCP variance."
  - "Global bracket (settings.json/CLAUDE.md sha256, .credentials.json stat) is byte-identical between B0 (Task 1) and B2 (Task 3 end) -- no auto-update or token refresh occurred during the live window."

requirements-completed: [CRO-04]

coverage:
  - id: D1
    description: "ab_runner.py end-to-end path proven on a fake claude with zero model calls (argv, scrubbed env, launch, init parse, transcript lookup by session id, tis_observed first-call readout)"
    requirement: "CRO-04"
    verification:
      - kind: unit
        ref: "ab_runner.py --selftest (S0-S6, ABRUN_SELFTEST_PASS=7/7)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Full runner (VR1-VR7 validity, M1/M2/vA manipulation checks, R1-R8 verdict rules, G1-G8 live guards, TTL bound, readout re-derivation) implemented via TDD and pre-registered before any counted run"
    requirement: "CRO-04"
    verification:
      - kind: unit
        ref: "ab_runner.py --selftest (S7-S13, ABRUN_SELFTEST_PASS=14/14; RED was 7/14 before implementation)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The four real subscription-quota runs (A1, A2, B1, B2) launched via one --live invocation; CRO-04 judged UNJUDGED (similar-reuse-variance-not-observed, R8), cro04 SATISFIED"
    requirement: "CRO-04"
    verification:
      - kind: other
        ref: "raw/ab-live.json + ab_runner.py --readout raw/ab-live.json -> READOUT: MATCH; tis_observed.py --sessions cross-check"
        status: pass
    human_judgment: true
    rationale: "The verdict itself (UNJUDGED vs SUPPORTED/REFUTED) is a scientific judgment about a real, non-repeatable subscription-quota observation -- automated checks confirm the numbers and the rule that produced the label, but whether that label is the right call for CRO-04's closure is for a human to accept."

duration: 26min
completed: 2026-09-28
status: complete
---

# Phase 04 Plan 01: Prefix cache-miss A/B Summary

**CRO-04 tested on GEX44 subscription quota via one `--live` invocation of 4 sequential `claude -p` runs; verdict UNJUDGED (similar-reuse-variance-not-observed, R8) because Arm A's MCP tool list did not vary between its two runs in this observation, and both arms independently reached ~99.97% run-2 cache reuse.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-09-28T14:19:56Z
- **Completed:** 2026-09-28T14:45:27Z
- **Tasks:** 3
- **Files modified:** 5 (all new)

## Accomplishments
- Built `ab_runner.py`, a read-only evidence runner composing `tools/tis_observed.py` for every transcript read, with env/auth pre-checks (`--env-check`, `--auth-check`), a one-shot `--live` launcher guarded by G1-G8, VR1-VR7 per-run validity, M1/M2/vA manipulation-and-variance checks, R1-R8 verdict rules, `rules_fingerprint`/`runner_sha256` self-hashing, `--readout` re-derivation, and `--evidence-lines` formatting -- validated end-to-end against a fake claude fixture (14/14 selftest cases).
- Froze the pre-registered design (thresholds, argv, VR/M/R rules, replacement budget 0, n=2 statement) in a committed EVIDENCE.md section 1 BEFORE any counted run, per the protocol's core rule.
- Spent the phase's entire model-call budget in one `--live` invocation: A1, A2, B1, B2 launched back-to-back on subscription quota (claudeAiOauth, no API key), all four VALID, found by pre-assigned session id, first-call cache figures read from GEX44's own transcripts via `tis_observed`, re-derived to `READOUT: MATCH`.
- Judged CRO-04: UNJUDGED (similar-reuse-variance-not-observed), rule R8 -- Arm A's MCP surface (tool list, server statuses) was identical across A1 and A2, so the tool-list-variance hypothesis under test was never exercised this run; `cro04: SATISFIED` (4 launches, complete, judged, not BLOCKED).

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer -- pre-checks + fake-claude selftest, EVIDENCE section 0** - `e3d9e1e` (feat)
2. **Task 2: Complete the runner + commit pre-registration** - `740b41b` (feat) -- TDD RED (`ABRUN_SELFTEST_PASS=7/14`) confirmed before implementation; GREEN (`14/14`) committed
3. **Task 3: The four runs -- readout, comparison, CRO-04 verdict** - `f32ea4b` (docs)

**Plan metadata:** (this commit)

_Note: TDD RED state (7/14) was run and observed but not separately committed -- the plan's protocol requires "commit only the green file"._

## Files Created/Modified
- `ab_runner.py` - Read-only evidence runner (env/auth checks, argv, scrubbed env, one-shot live launch, transcript lookup, tis_observed readout, VR/M/R rules, fingerprint, readout, evidence-lines, 14-case selftest)
- `EVIDENCE.md` - Sections 0 (pre-checks), 1 (pre-registration), 2 (the four runs), 3 (cross-arm comparison), 4 (verdict / CRO-04)
- `raw/claude-help.txt` - Verbatim installed `claude --help`
- `raw/static-excerpts.txt` - X01-X05 byte-verified excerpts of the sha-pinned binary
- `raw/ab-live.json` - The launch record, transcript readout, metrics and verdict; the durable one-shot rerun latch

## Decisions Made
- Recorded in frontmatter `key-decisions`: vA NO this run (UNJUDGED R8, not a plan defect); gap_run2 essentially zero; global bracket UNCHANGED across the live window (no auto-update, no credential rewrite).

## Deviations from Plan

None - plan executed exactly as written. All three tasks' automated checks (selftest thresholds, EVIDENCE field checks, leak/redaction scans) passed on first or second attempt; the one `replacement_budget` line was split into `replacement_budget: 0` plus a separate `replacement_budget_reason:` line so the EVIDENCE.md field check's exact-value match (`g('replacement_budget')=='0'`) would parse correctly -- a formatting fix within Task 2's own action, not a deviation from the plan's design.

## Issues Encountered

None. The single `--live` invocation completed cleanly (rc 0) inside the 1500s timeout, well under budget (`run_in_background`, ~25s wall time for all four runs).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CRO-04 is judged (not BLOCKED) with a stated why (`similar-reuse-variance-not-observed`) and `cro04: SATISFIED`.
- Phase 5 (seal-and-hand-back) should record this UNJUDGED outcome in RESUMPTION/UKDL, note that a future re-run of this harness would need the MCP surface to actually change between run 1 and run 2 (e.g. an auth-status flip or a plugin toggle) to exercise R5-R7, and that `ab_runner.py` + the `tis_observed`-based readout are now proven end-to-end against real subscription quota.
- Corpus side effect: 4 sdk-cli haiku sessions now sit under project keys `-tmp-claude-1000-cro-p04-ab-armA` and `-tmp-claude-1000-cro-p04-ab-armB`; future GEX44 baselines should exclude those two project keys.

---
*Phase: 04-prefix-cache-miss-a-b*
*Completed: 2026-09-28*

## Self-Check: PASSED

All created files (ab_runner.py, EVIDENCE.md, raw/claude-help.txt, raw/static-excerpts.txt, raw/ab-live.json, this SUMMARY) exist on disk; all three task commits (e3d9e1e, 740b41b, f32ea4b) exist in git history.
