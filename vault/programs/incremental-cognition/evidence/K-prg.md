# Pillar K -- PRG: one real --check against the committed reference

Session c59ad762, 2026-10-05, laptop plane, base 6ca4a867. Owner authorized the one quota-spending probe session
("y", 2026-10-05). Reference: `vault/programs/incremental-cognition/floor/reference.json` (default `--reference`),
sha256 c77535d4b6c2de2e0585c456f4b5abffe85236e6ee94d372f46b3aae7958a61f, written from champion session 8f983bc6
(2026-10-03). Same cwd, same kind (headless probe), same probe prompt.

## Command, output, exit code

    python tools/floor_regression_gate.py --check --probe --cwd C:\Users\User\Apps\listing-probe\champion
    SOURCE probe session=fa7e93cb-3737-4712-809e-ade44eafd54b
    PROBE exe=C:\Users\User\.local\bin\claude.exe session=fa7e93cb-3737-4712-809e-ade44eafd54b label=floor-gate-20261005T203946Z cost_usd=0.542805
    FLOOR total_chars ref=188147 now=169893 delta=-18254
    WINDOW ref_sha256=22042236b82b now_sha256=2a4c0ba49935 ref_rows=25 now_rows=25 same=no
    LAYER hook_context:SessionStart:SessionStart scope=unattributed ref=0 now=6436 delta=+6436
    LAYER hook_context:UserPromptSubmit:UserPromptSubmit scope=unattributed ref=2073 now=2460 delta=+387
    LAYER other:deferred_tools_delta scope=unattributed ref=5116 now=8494 delta=+3378
    LAYER other:session_context scope=harness ref=304 now=300 delta=-4
    LAYER rules scope=universal ref=63625 now=35605 delta=-28020
    LAYER skill_listing scope=universal ref=24507 now=24499 delta=-8
    LAYER system_prompt scope=unattributed ref=6998 now=6575 delta=-423
    RISE hook_context:SessionStart:SessionStart scope=unattributed delta=+6436 unit=chars rules=layer_3pct,universal_1k
    RISE other:deferred_tools_delta scope=unattributed delta=+3378 unit=chars rules=universal_1k
    SCOPE universal=-28028 project=+0 harness=-4 unattributed=+9778
    SKILLS ref_chars=30000 now_chars=29992 ref_entries=266 now_entries=297 ref_skill_count=266 now_skill_count=297
    TOKENS status=measured ref=87739 now=83115 delta=-4624
    FLOOR verdict=MATERIAL_RISE exit=1 reason=material_rise

Exit code 1. The tokens axis WAS compared (prompt digests equal), so `--chars-only` was not needed and not run.

## Reading

- The gate worked: two unexplained rises, each over a frozen materiality line, both in `unattributed` scope.
  1. `hook_context:SessionStart` 0 -> 6,436 chars: a SessionStart hook now injects context that the 2026-10-03
     reference did not have. Its producing hook was not correlated (unattributed), so the gate cannot name it.
  2. `other:deferred_tools_delta` 5,116 -> 8,494 chars: more deferred tools are announced at startup.
- At the same time the floor FELL overall: rules -28,020 chars (the 2026-09-29..10-05 rule-to-skill moves), total
  -18,254 chars, first-call tokens -4,624 (87,739 -> 83,115, -5.3 %). A net fall does not cancel a per-layer rise;
  the gate judges per (layer, scope), by design.
- Per owner-bundle row 12, a RISE here is the gate working, not a failure of the step. Resolution is the Owner's:
  either explain both rows in `reference.json` `explanations` (layer, scope, unit, delta_bound, reason, commit), or
  re-baseline with `--write-reference ... --replace` from this session. Nothing was explained or replaced here, and
  no threshold was changed.
- The probe appended its row to the tracked `wiki/tools/listing_floor_probe.results.jsonl`; it is committed with this
  file (the probe's documented behaviour).

Scope: this measures the startup floor, not the cost of an equivalent change.
