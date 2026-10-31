# LAPTOP RESULTS (ctx-rent-x), plane: laptop, 2026-10-31 ~16:05 local, run by pane f432029e on branch ctx-rent-x-w0 @ a0073a50

## L1: PASS
Command: `python tools/ctx_rent.py estate --since 2026-10-25T00:00:00Z --until 2026-11-01T00:00:00Z --out vault/programs/ctx-rent-x/estate-laptop-w0.json` (rc 0)
Total: 1,287 sessions, 43,031 calls, 7,473,949,368 processed, floor_rent 3,860,620,200 (51.7 %). active_release 0.1.0-b15bfc3d.

top-level by generation (sessions, calls, processed, floor_rent -> mean floor = floor_rent/calls):

| generation | sessions | calls | processed | mean floor | processed/call |
|---|---:|---:|---:|---:|---:|
| UNKNOWN | 73 | 10,043 | 2,269,174,028 | 99.7K | 226K |
| STALE fce69916 | 203 | 8,330 | 1,533,945,422 | 111.4K | 184K |
| STALE 7df93813 | 138 | 3,414 | 545,364,180 | 101.9K | 160K |
| STALE 40f2c160 | 34 | 2,252 | 531,039,483 | 101.7K | 236K |
| STALE f79e3c46 | 14 | 1,905 | 413,503,921 | 122.5K | 217K |
| STALE c42eb4e7 | 27 | 1,841 | 437,057,407 | 114.9K | 237K |
| STALE 82c98708 | 19 | 1,631 | 284,857,949 | 106.3K | 175K |
| STALE 384b03a0 | 71 | 1,023 | 142,520,620 | 103.3K | 139K |
| CURRENT b15bfc3d | 18 | 845 | 154,275,711 | 108.3K | 183K |
| STALE c5b18294 | 7 | 41 | 5,975,872 | 114.7K | 146K |

Other classes: subagent 621 sessions / 10,147 calls / 969.8M (all UNKNOWN); worker:background 37 sessions / 1,159 calls / 171.7M; worker:slim 25 / 400 / 14.7M (UNKNOWN).

Reading (laptop plane, MEASURED): the top-level mean floor sits at ~100-122K in EVERY CCR generation, including CURRENT.
CCR generation does not move the interactive floor, consistent with `main:'shadow'`. Top-level = 84.5 % of processed
(6.32B of 7.47B). The lever is the top-level floor + main enforcement (Phases 2-3), not generation rollout.

## L2: PASS
Command: `python tools/ccr_release.py --root %TEMP%/claude/ccr-scratch-root release --impact none` (rc 0), SCRATCH root so the
live `~/.claude/ccr` was not touched (ACTIVE.json still 0.1.0-b15bfc3d, ts 09:35:04).
RELEASE.json: `{"release": "0.1.0-7b5347c5", "version": "0.1.0", "source_commit": "a0073a50bb3d05a179716a5d90cdfa120ea188ae"}`: 40-hex.
