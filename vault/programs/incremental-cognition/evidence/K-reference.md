# Pillar K -- reference written (owner-bundle row 12, Option B) -- PRG still pending

Session c59ad762, 2026-10-05, laptop plane, HEAD 9f6e379f. Option B as authorized (no quota): the reference is the
champion-startup probe already on disk. **This file is NOT the PRG.** K stays open until `K-prg.md` holds one real
`--check` of a LATER session with the same cwd (`C:\Users\User\Apps\listing-probe\champion`). None exists on disk:
`~/.claude/projects/C--Users-User-Apps-listing-probe-champion` holds only 8f983bc6 itself.

Scope: K measures the startup floor (what the model is handed before the first turn). It does not measure the cost
of an equivalent change, and nothing here says it does.

## Reference

    python tools/floor_regression_gate.py --write-reference vault/programs/incremental-cognition/floor/reference.json --session 8f983bc6-d760-4440-938d-aeed86a548ae
    FLOOR reference written path=vault/programs/incremental-cognition/floor/reference.json total_chars=188147 tokens=87739 window_sha256=22042236b82b window_rows=25
    FLOOR verdict=REFERENCE_WRITTEN exit=0 reason=written

sha256(reference.json) = c77535d4b6c2de2e0585c456f4b5abffe85236e6ee94d372f46b3aae7958a61f
cwd of the reference = the champion probe directory, so universal layers only.

## Sanity parse (NOT a floor-held proof: the reference checked against the session it was written from)

    python tools/floor_regression_gate.py --check --session 8f983bc6-d760-4440-938d-aeed86a548ae
    FLOOR total_chars ref=188147 now=188147 delta=+0
    WINDOW ref_sha256=22042236b82b now_sha256=22042236b82b ref_rows=25 now_rows=25 same=yes
    SKILLS ref_chars=30000 now_chars=30000 ref_entries=266 now_entries=266 ref_skill_count=266 now_skill_count=266
    TOKENS status=measured ref=87739 now=87739 delta=+0
    FLOOR verdict=WITHIN_BOUND exit=0 reason=within_bound

## Injected-rise drill (isolated copies; the live reference was never written)

The rise is injected by lowering the largest universal component (memory_global, 39,809 chars) in a scratch copy
of the reference, so the unchanged session reads as a floor that rose by that many chars. Thresholds untouched.

| Case | Injected rise | Expected | Observed |
|---|---|---|---|
| rise_1500 | +1,500 universal | MATERIAL_RISE exit 1 | `RISE memory_global scope=universal delta=+1500 rules=universal_1k`, exit 1 |
| control_500 | +500 universal (< 1,000 and < 3 % of 188,147) | WITHIN_BOUND exit 0 | WITHIN_BOUND, exit 0 |
| rise_1500_explained | +1,500 with a covering explanation | WITHIN_BOUND exit 0 | `EXPLAINED ... by=75691a64`, exit 0 |

Live reference sha256 before = after = c77535d4b6c2de2e. `K_DRILL=PASS`. Script: session scratchpad `k_drill.py`.

## Fixture gate

    python tools/test_floor_regression_gate.py
    FLOOR_PASS=57/57  threshold=57/57  skipped=10  inconclusive=0   (exit 0)

## Open

PRG under Option B needs one fresh headless probe session in the champion directory, which spends one session of
quota. Row 12 authorized Option B as "no quota", so that session is not run without the Owner:

    python tools/floor_regression_gate.py --check --probe --cwd C:\Users\User\Apps\listing-probe\champion
    (if exit 2 tokens_unmeasured) ... same line with --chars-only, record the verdict as WITHIN_BOUND_CHARS_ONLY

Named debt (unchanged): no hook, CI job or `--final` run executes `--check` against this reference; after the PRG
its absence is silence, not health.
