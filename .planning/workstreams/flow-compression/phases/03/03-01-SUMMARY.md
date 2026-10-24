# Summary 03-01
Landed hold backoff, EOL/BOM-normalised packet digest (legacy raw digests accepted), residual no-overwrite (`.residual-N.md`).
Tests: test_s3_admission 11/11; test_gsd_mission 234/234 (V-MC-GSD-BLOCK-CLEARS-ON-OK now probes past next_check; new V-S3-BACKOFF-SKIPS-ASK-INSIDE-WINDOW); test_mission_steward 26/26 (V-STEWARD-RESIDUAL-NO-STACK expectation intentionally changed to the new path + V-S3-RESIDUAL-NEVER-OVERWRITES-ADMITTED); admission 43/43, goal_control 27/27, arm_preflight 16/16, arm_worker_guard 6/6.
