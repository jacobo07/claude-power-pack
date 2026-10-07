# U6a receipt -- launch-time baseline resolver
Packet sha256 20e148228610 verified. Branch ce/presence. Commit subject: "feat(ce-presence): U6a baseline resolver".

Callers: worker_argv <- launch_worker (--bg path) and _launch_slim (reached only from launch_worker).
launch_worker <- supervise (relay/replace, ~l.2950) and arm/start (~l.3060). Every launch goes through
launch_worker, where resolve_baseline runs once, before the claim. Other hits are tests only.

Code (tools/gsd_mission.py): resolve_baseline, work_class, baseline_mode (CPP_CE_BASELINE shadow|enforce|off,
default shadow), baseline_legacy_verdict, LEGACY_REASONS (safe_deopt accepts ":<trigger>"). Fields ride the
launch_claimed transition (model, autocompact, continue_max_tokens, baseline). Ledger rows: baseline_resolved,
would_refuse_legacy, launch_refused_baseline (enforce; refused before any epoch is spent).
Policy (vault/config/mission-budget-defaults.json): baseline_version "1"; baseline_classes
COMPILED_UNIT/GSD_RESUME/OTHER = model sonnet, autocompact 250k, continue_max_tokens 250000.
Built-in fallback is identical (src builtin). Old two keys untouched.
Evidence: sonnet + autocompact 250k = gen3/packets/T1.md and T3.md (C23 used 300k).
continue_max_tokens: DEVIATION -- no measured value found in the repo (C23b-PROGRESS only notes the setter;
gsd_epoch default is 300_000). I set 250000 = the compaction line. Revisit when measured.

Tests (exit): test_gsd_mission_baseline 0 (19 pass), test_gsd_mission_envelope 0, test_gsd_mission_admission 0,
test_gsd_epoch 0, test_gsd_mission 1 -- single FAIL V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED, same on HEAD's
gsd_mission.py (run through GSD_MISSION_DRILL_DIR): pre-existing, not fixed.
Mutants, both red: (a) resolver call deleted -> 4 FAIL then a crash; (b) builtin model sonnet->opus -> 4 FAIL.

Not done (later units): renewal/relay re-resolution, /kresume baseline block, compiled-grammar arm for SCAN.
Bug caught: first draft wrote baseline into records under `off` (identity test after a reassigned rec); fixed with a flag.
