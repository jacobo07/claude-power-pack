---
title: UKDL candidates -- TTB Enhanced Renderer + cu observer (TCS PC), #CROSS-PROJECT seeds
date: 2026-10-21
status: CANDIDATES -- NOT promoted; ukdl-universal.md is not edited from here (its tail is auto-appended by CEPS)
evidence: C:\Users\User\TB-PC-spike\ttb\knowledge\ukdl_seeds.md (T-GFX/PR-GFX, 2026-10-20); cu repo commits 85d5fd3 829ce33 6789a62 (gates/obs_spike.py, obs_law.py, obs_heading.py, tests/)
---

# 1. Ownership sweep
The ids `T-GFX-00*`, `PR-GFX-00*`, `T-CU-00*` and `PR-CU-00*` were searched across all of `vault/` on 2026-10-21: the only hit is this file, so no id collides. Topic owners were not searched beyond the ids.
Seeds 1-3 are carried over verbatim in substance from the project vault; 4-8 were measured on 2026-10-21.

# 2. Traps
- **T-GFX-001** #CROSS-PROJECT. Detecting a game scene by mean brightness: a bloomed intro video and the attract-mode video both pass "mean > N", so the run reported the hub while looking at something else. Fix: Pearson r of downsampled luminance against a baseline frame of the target scene (same scene with post effects 0.84-0.98, attract mode about 0, threshold 0.75), so the check can return the other answer. Evidence: `cu/gates/gfx_capture.py scene_r`; P4 landed in attract mode 3 of 3 before the fix.
- **T-GFX-002** #CROSS-PROJECT. A ReShade effect whose source texture is missing still compiles and the run exits 0; only ReShade.log carries `ERROR | Source 'X.png' ... was not found`. Fix: grep the log for `| ERROR |` after every run.
- **T-CU-003** #CROSS-PROJECT. An "atomic" write (temp file then `os.replace`) whose temp name carries only the pid collides between two threads of one process: one thread's `os.replace` consumes the other's temp file (`FileNotFoundError`). Seen when a sampler thread and the main thread both beat the same heartbeat file. Fix: pid AND thread id in the temp name. Evidence: `cu/state.py write_json`, `tests/test_state_threads.py` red (3 errors in 4 threads x 400 writes) then green.
- **T-CU-004** #CROSS-PROJECT. A failed model fit is not evidence against the model until the experiment is shown to have been free to run. Law run 1 was rejected (rms 0.463) while its last two holds moved 0.0008 and 0.0001 units: the character had hit a wall. Fix: a hold that moves less than a floor is BLOCKED = CANNOT_EVALUATE, never a rejection. When the protocol is revised after seeing the failed run, say so in the record: the next run is then a replication of a revised design, not a blind test. Evidence: `cu/gates/obs_law.py`, `evidence/gfx/obs_law_run1`.
- **T-CU-005** #CROSS-PROJECT. A tolerance derived from the same misfit it judges widens itself: with tolerance = 3 x train RMS a quadratic world passed as LAW_HOLDS in the offline test. Fix: limits fixed in advance (train RMS <= 0.05, held-out error <= max(0.10, 10% of d)) plus a fit-quality gate. Found by driving the verdict from both poles on synthetic worlds before touching the game.

# 3. Process rules
- **PR-GFX-002** #CROSS-PROJECT. A third-party shader pack without a declared licence is pinned by commit and sha256 in a lock file and fetched into a cache outside git; the lock is verified before each use and drift raises before the file is kept. Local use only; never in a release package.
- **PR-CU-001** #CROSS-PROJECT. Offsets taken from a third-party project are a hypothesis until a live spike confirms them on THIS executable: read-only sampler, a control key the game ignores, an idle baseline, a before/after screenshot as evidence independent of the memory layer, and a three-way verdict (CONFIRMED / REFUTED / CANNOT_EVALUATE) where an unreadable field is UNKNOWN, never 0. The header carries the exe sha256 and the code commit. Result: BrickBench P1 position and map-name offsets CONFIRMED on TCS (w hold 1.44 units; z control and idle 0.0).
- **PR-CU-002** #CROSS-PROJECT. When two models of a signal compete, write the predictions before the run and choose the sequence so they DISAGREE by more than the acceptance threshold on at least one step, then make the verdict require that disagreement. Heading: target model predicted `a` after `d` at F-90, rate model at F; observed -91.2, errors 0-3 deg against target and 91 deg against rate. Evidence: `cu/gates/obs_heading.py`.
