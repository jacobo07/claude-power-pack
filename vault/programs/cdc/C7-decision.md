# C7 decision -- Cognitive CI

Tool: `tools/cognitive_ci.py` (`--measure`, `--certify`, `--check`). Deterministic, no model call. Kill switch `CPP_COG_CI=off`.
Fails OPEN on its own error (reported `INSTRUMENT_ERROR`); a measured regression is never open.

## Benchmark bank (all computed from a repo root, so a fixture can stand in)
| metric | class | blast |
|---|---|---|
| floor.claude_md_bytes, floor.rules_bytes, floor.hook_context_bytes, floor.skill_listing_bytes, floor.agent_listing_bytes | size | ALWAYS_ON |
| capsule.bytes, capsule.bootstrap_bytes (fixed inputs) | size | PER_ROTATION |
| admission.floor.<profile> (route-floors.json) | size | PER_SPAWN |
| ctc.candidate_tokens, ctc.p95_tokens (fixed 5-claim graph) | size | PER_SPAWN |
| status.model_call_sites, wait.resident_sites | count, must be 0 | ZERO |
| admission.latency_ms (min of 20) | latency | PER_SPAWN |

## Noise model
`--certify` measures 3 runs. noise = max - min per metric. size/count metrics are deterministic (noise 0). Latency is
noisy: tolerance = max(5 x baseline, baseline + 50 ms), because a scheduler hiccup must not block a landing.

## Thresholds (confidence by blast radius)
- ALWAYS_ON: any growth > 0.5 % (min 64 bytes) is a regression. Paid by every session.
- PER_ROTATION / PER_SPAWN: growth > 5 %.
- ZERO: any value > 0 is a regression, no budget entry can excuse it.
- Lower is never a regression.
A regression is RED unless `cognitive-budget-changes.json` has an entry for the metric with `allowed_max >= value`,
non-empty `reason` and `owner`. Re-certify after a justified entry merges.

## Metamorphic V-gates (fixed-work metrics must not move)
+50 unrelated skills, +1000 history rows, +100 dormant goals, +500 unrelated test files -> every non-floor.* metric
equal within noise. Sensitivity control: the +50 skills DO grow floor.skill_listing_bytes (the instrument sees it).

## Landing
`land_worktree.py` runs the check on the rebased worktree before tests/ff-only; RED -> `COGNITIVE_REGRESSION`, nothing
lands. `--cog-ci off` / `CPP_COG_CI=off` skips. Missing baseline -> open with `NO_BASELINE` in the receipt.

## Limits
hook_context_bytes counts additionalContext literals statically; dynamic hook output is NOT measured (NOT_PROVEN).
status/wait checks are static call-site scans of named entry points, not a runtime trace.
